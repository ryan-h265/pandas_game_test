"""Placement tool - for placing buildings, props, and models with ghost preview."""

from .base import Tool, ToolType
from panda3d.core import Vec3, Vec4, TransparencyAttrib
from structures.simple_building import SimpleBuilding
from structures.japanese_building import JapaneseBuilding
from props.lantern_prop import LanternProp
from props.japanese_bar_prop import JapaneseBarProp


class PlacementTool(Tool):
    """Tool for placing buildings, props, and models with ghost preview controlled by mouse."""

    def __init__(self, world, camera, render, bullet_world, terrain_raycaster=None, mouse_watcher=None, point_light_manager=None):
        """Initialize placement tool.

        Args:
            world: Game world instance
            camera: Camera node for raycasting
            render: Panda3D render node
            bullet_world: Bullet physics world
            terrain_raycaster: TerrainRaycaster for ground placement
            mouse_watcher: MouseWatcher node for raycasting
            point_light_manager: Optional PointLightManager for props with lights (e.g., lanterns)
        """
        super().__init__("Placement Tool", ToolType.BUILDING)
        self.world = world
        self.camera = camera
        self.render = render
        self.bullet_world = bullet_world
        self.terrain_raycaster = terrain_raycaster
        self.mouse_watcher = mouse_watcher
        self.point_light_manager = point_light_manager

        # Placement type selection (buildings, props, models)
        self.placement_types = {
            1: {
                "name": "Simple Building",
                "class": SimpleBuilding,
                "type": "building",  # Regular building
                "default_width": 10.0,
                "default_depth": 10.0,
                "default_height": 8.0,
            },
            2: {
                "name": "Japanese Building",
                "class": JapaneseBuilding,
                "type": "building",  # Regular building
                "default_width": 12.0,
                "default_depth": 10.0,
                "default_height": 6.0,
            },
            3: {
                "name": "Japanese Stone Lantern",
                "class": LanternProp,
                "type": "prop",  # Prop (single object, not a building)
                "default_width": 1.0,  # Not used for props, but kept for compatibility
                "default_depth": 1.0,
                "default_height": 1.5,
            },
            4: {
                "name": "Japanese Bar",
                "class": JapaneseBarProp,
                "type": "prop",  # Prop (glTF building model)
                "default_width": 8.0,  # Not used for props
                "default_depth": 6.0,
                "default_height": 4.0,
            },
        }
        self.current_placement_type = 1  # Start with Simple Building

        # Placement parameters (adjustable for buildings)
        self.building_width = self.placement_types[1]["default_width"]
        self.building_depth = self.placement_types[1]["default_depth"]
        self.building_height = self.placement_types[1]["default_height"]

        # Ghost building preview (cached per type to avoid memory leaks)
        self.ghost_buildings_cache = {}  # {building_type: ghost_building}
        self.ghost_building = None
        self.ghost_position = Vec3(0, 0, 0)
        self.placement_valid = False

        # Settings
        self.max_placement_distance = 50.0
        self.snap_to_grid = True
        self.grid_size = 5.0  # Grid snap size

        # Track if we've already placed a building on this mouse press
        self.has_placed_this_click = False

        # Prevent rapid switching causing issues
        self.is_switching_type = False

    def on_activate(self):
        """Called when building tool is equipped."""
        self._create_ghost_building()
        building_name = self.placement_types[self.current_placement_type]["name"]
        return f"Equipped: {building_name} ({self.building_width}x{self.building_depth}x{self.building_height})"

    def on_deactivate(self):
        """Called when tool is switched away from."""
        super().on_deactivate()
        self._remove_ghost_building()

    def _create_ghost_building(self):
        """Create or retrieve cached ghost preview of the building/prop."""
        # Hide current ghost if visible
        if self.ghost_building:
            self._hide_ghost_building()

        # Check if we have this building type cached
        cache_key = (self.current_placement_type, self.building_width, self.building_depth, self.building_height)

        if cache_key in self.ghost_buildings_cache:
            # Reuse cached ghost
            self.ghost_building = self.ghost_buildings_cache[cache_key]
            self._show_ghost_building()
            return

        try:
            # Get the current building type info
            building_info = self.placement_types[self.current_placement_type]
            building_class = building_info["class"]
            building_type = building_info.get("type", "building")

            # Create ghost based on type
            if building_type == "prop":
                # For props (like lanterns), create without light manager
                self.ghost_building = building_class(
                    self.bullet_world,
                    self.render,
                    self.ghost_position,
                    point_light_manager=None,  # No lights for ghost
                    static=True,
                    is_ghost=True  # Mark as ghost preview
                )

                # Make the model semi-transparent green
                if hasattr(self.ghost_building, 'model_node') and self.ghost_building.model_node:
                    self.ghost_building.model_node.setTransparency(TransparencyAttrib.MAlpha)
                    self.ghost_building.model_node.setColorScale(0.2, 1.0, 0.2, 0.4)

                # Disable collision for ghost physics body
                if hasattr(self.ghost_building, 'physics_body') and self.ghost_building.physics_body:
                    # For Bullet physics, remove from physics world temporarily
                    # Ghost props don't need collision detection
                    try:
                        self.bullet_world.removeRigidBody(self.ghost_building.physics_body.node())
                    except:
                        pass  # May not be in world yet

            else:
                # Regular building
                self.ghost_building = building_class(
                    self.bullet_world,
                    self.render,
                    self.ghost_position,
                    width=self.building_width,
                    depth=self.building_depth,
                    height=self.building_height,
                    name=f"ghost_building_{cache_key}"
                )

                # Make all pieces transparent and greenish (valid placement color)
                for piece in self.ghost_building.pieces:
                    try:
                        if piece.body_np and not piece.body_np.isEmpty():
                            # Set transparency
                            piece.body_np.setTransparency(TransparencyAttrib.MAlpha)
                            # Update color to semi-transparent green (valid placement)
                            piece.body_np.setColorScale(0.2, 1.0, 0.2, 0.4)

                            # Disable collisions for ghost pieces (remove from physics world)
                            body_node = piece.body_np.node()
                            if body_node:
                                try:
                                    self.bullet_world.removeRigidBody(body_node)
                                except:
                                    pass  # May not be in world yet
                    except Exception as e:
                        print(f"Warning: Error setting ghost piece appearance: {e}")
                        pass

            # Cache this ghost for reuse
            self.ghost_buildings_cache[cache_key] = self.ghost_building

        except Exception as e:
            print(f"Error creating ghost building/prop: {e}")
            import traceback
            traceback.print_exc()
            self.ghost_building = None

    def _hide_ghost_building(self):
        """Hide the current ghost building/prop without destroying it."""
        if self.ghost_building:
            # Check if it's a prop or a building
            if hasattr(self.ghost_building, 'pieces'):
                # Building with pieces
                for piece in self.ghost_building.pieces:
                    try:
                        if piece.body_np and not piece.body_np.isEmpty():
                            piece.body_np.hide()
                    except:
                        pass
            elif hasattr(self.ghost_building, 'model_node'):
                # Prop with model_node
                if self.ghost_building.model_node:
                    self.ghost_building.model_node.hide()

    def _show_ghost_building(self):
        """Show the current ghost building/prop."""
        if self.ghost_building:
            # Check if it's a prop or a building
            if hasattr(self.ghost_building, 'pieces'):
                # Building with pieces
                for piece in self.ghost_building.pieces:
                    try:
                        if piece.body_np and not piece.body_np.isEmpty():
                            piece.body_np.show()
                    except:
                        pass
            elif hasattr(self.ghost_building, 'model_node'):
                # Prop with model_node
                if self.ghost_building.model_node:
                    self.ghost_building.model_node.show()

    def _remove_ghost_building(self):
        """Hide the ghost building preview (keeps cache)."""
        if self.ghost_building:
            self._hide_ghost_building()
            self.ghost_building = None

    def _update_ghost_position(self, position):
        """Update the position of the ghost building/prop.

        Args:
            position: Vec3 world position
        """
        if not self.ghost_building:
            return

        # Apply grid snapping if enabled
        if self.snap_to_grid:
            position = Vec3(
                round(position.x / self.grid_size) * self.grid_size,
                round(position.y / self.grid_size) * self.grid_size,
                position.z
            )

        self.ghost_position = position

        # Update position based on type
        if hasattr(self.ghost_building, 'pieces'):
            # Building with pieces
            for piece in self.ghost_building.pieces:
                # Calculate offset from original building position
                offset = piece.position - self.ghost_building.position
                new_pos = position + offset
                piece.body_np.setPos(new_pos)
                piece.position = new_pos

            # Update building base position
            self.ghost_building.position = position

        elif hasattr(self.ghost_building, 'set_position'):
            # Prop with set_position method
            self.ghost_building.set_position(position)

    def _set_ghost_color(self, valid):
        """Set the ghost building/prop color based on placement validity.

        Args:
            valid: True for valid placement (green), False for invalid (red)
        """
        if not self.ghost_building:
            return

        self.placement_valid = valid

        if valid:
            # Green for valid placement
            color = (0.2, 1.0, 0.2, 0.4)
        else:
            # Red for invalid placement
            color = (1.0, 0.2, 0.2, 0.4)

        # Apply color based on type
        if hasattr(self.ghost_building, 'pieces'):
            # Building with pieces
            for piece in self.ghost_building.pieces:
                piece.body_np.setColorScale(*color)
        elif hasattr(self.ghost_building, 'model_node'):
            # Prop with model_node
            if self.ghost_building.model_node:
                self.ghost_building.model_node.setColorScale(*color)

    def _check_placement_valid(self, position):
        """Check if placement at position is valid (not overlapping existing buildings/props).

        Args:
            position: Vec3 world position

        Returns:
            bool: True if placement is valid
        """
        if not self.ghost_building or not self.world:
            return True

        # Get all existing buildings (excluding ghost buildings)
        existing_buildings = [b for b in self.world.buildings if not b.name.startswith("ghost")]

        # Get all existing props
        existing_props = self.world.props if hasattr(self.world, 'props') else []

        # Determine if ghost is a prop or building
        is_prop = not hasattr(self.ghost_building, 'pieces')

        if is_prop:
            # For props, use simple position-based checking with approximate size
            ghost_pos = self.ghost_position
            # Approximate prop size (adjust based on your prop)
            prop_radius = 1.5  # Radius for collision check

            # Check against existing buildings
            for building in existing_buildings:
                for piece in building.pieces:
                    piece_pos = piece.position
                    piece_size = piece.size

                    # Calculate distance from prop center to building piece
                    # Use AABB check with prop as a small box
                    ghost_min = Vec3(ghost_pos.x - prop_radius, ghost_pos.y - prop_radius, ghost_pos.z)
                    ghost_max = Vec3(ghost_pos.x + prop_radius, ghost_pos.y + prop_radius, ghost_pos.z + 2.0)

                    piece_min = Vec3(
                        piece_pos.x - piece_size.x / 2,
                        piece_pos.y - piece_size.y / 2,
                        piece_pos.z - piece_size.z / 2
                    )
                    piece_max = Vec3(
                        piece_pos.x + piece_size.x / 2,
                        piece_pos.y + piece_size.y / 2,
                        piece_pos.z + piece_size.z / 2
                    )

                    if (ghost_min.x < piece_max.x and ghost_max.x > piece_min.x and
                        ghost_min.y < piece_max.y and ghost_max.y > piece_min.y and
                        ghost_min.z < piece_max.z and ghost_max.z > piece_min.z):
                        return False

            # Check against existing props
            for prop in existing_props:
                prop_pos = prop.get_position()
                distance = (ghost_pos - prop_pos).length()
                if distance < (prop_radius * 2):  # Props too close
                    return False

        else:
            # Original building collision check
            for ghost_piece in self.ghost_building.pieces:
                ghost_pos = ghost_piece.position
                ghost_size = ghost_piece.size

                # Calculate ghost piece bounding box
                ghost_min = Vec3(
                    ghost_pos.x - ghost_size.x / 2,
                    ghost_pos.y - ghost_size.y / 2,
                    ghost_pos.z - ghost_size.z / 2
                )
                ghost_max = Vec3(
                    ghost_pos.x + ghost_size.x / 2,
                    ghost_pos.y + ghost_size.y / 2,
                    ghost_pos.z + ghost_size.z / 2
                )

                # Check against all pieces of all existing buildings
                for building in existing_buildings:
                    for piece in building.pieces:
                        piece_pos = piece.position
                        piece_size = piece.size

                        # Calculate existing piece bounding box
                        piece_min = Vec3(
                            piece_pos.x - piece_size.x / 2,
                            piece_pos.y - piece_size.y / 2,
                            piece_pos.z - piece_size.z / 2
                        )
                        piece_max = Vec3(
                            piece_pos.x + piece_size.x / 2,
                            piece_pos.y + piece_size.y / 2,
                            piece_pos.z + piece_size.z / 2
                        )

                        # Check for AABB (Axis-Aligned Bounding Box) collision
                        if (ghost_min.x < piece_max.x and ghost_max.x > piece_min.x and
                            ghost_min.y < piece_max.y and ghost_max.y > piece_min.y and
                            ghost_min.z < piece_max.z and ghost_max.z > piece_min.z):
                            # Collision detected
                            return False

                # Check against existing props
                for prop in existing_props:
                    prop_pos = prop.get_position()
                    # Simple distance check for now
                    distance = (ghost_pos - prop_pos).length()
                    if distance < 3.0:  # Props within 3 units
                        return False

        # No collisions found
        return True

    def update(self, dt):
        """Update tool state - update ghost position based on mouse.

        Args:
            dt: Delta time since last update
        """
        if not self.ghost_building:
            return

        # Raycast from camera to find ground position
        if self.terrain_raycaster and self.mouse_watcher:
            hit_info = self.terrain_raycaster.get_terrain_hit(self.mouse_watcher)

            if hit_info:
                # Update ghost position to hit point
                hit_pos = hit_info["position"]
                self._update_ghost_position(hit_pos)

                # Check if placement is valid
                valid = self._check_placement_valid(hit_pos)
                self._set_ghost_color(valid)

    def on_primary_use(self, hit_info):
        """Place the building/prop at current ghost position.

        Args:
            hit_info: Dictionary with hit information (not used, we use ghost position)

        Returns:
            bool: True if building/prop was placed
        """
        # Only place one building per mouse click
        if self.has_placed_this_click:
            return False

        if not self.ghost_building:
            print("Cannot place - no ghost preview!")
            return False

        if not self.placement_valid:
            print("Cannot place - overlapping with existing object!")
            return False

        # Get building type info
        building_info = self.placement_types[self.current_placement_type]
        building_class = building_info["class"]
        building_type = building_info.get("type", "building")
        building_type_name = building_info["name"].lower().replace(" ", "_")

        # Create the actual object at ghost position
        if building_type == "prop":
            # Create prop with light manager
            new_prop = building_class(
                self.bullet_world,
                self.render,
                self.ghost_position,
                point_light_manager=self.point_light_manager,
                static=True  # Props are static by default
            )

            # Add prop to world
            self.world.add_prop(new_prop)

            print(f"Placed {building_info['name']} at {self.ghost_position}")

        else:
            # Create regular building
            building_count = len([b for b in self.world.buildings if not b.name.startswith("ghost")])

            new_building = building_class(
                self.bullet_world,
                self.render,
                self.ghost_position,
                width=self.building_width,
                depth=self.building_depth,
                height=self.building_height,
                name=f"{building_type_name}_{building_count}"
            )

            # Add building to world
            self.world.add_building(new_building)

            print(f"Placed building at {self.ghost_position} (size: {self.building_width}x{self.building_depth}x{self.building_height})")

        # Mark that we've placed something on this click
        self.has_placed_this_click = True

        return True

    def on_secondary_use(self, hit_info):
        """Rotate the building preview.

        Args:
            hit_info: Dictionary with hit information

        Returns:
            bool: True if action was performed
        """
        # Swap width and depth to rotate 90 degrees
        self.building_width, self.building_depth = self.building_depth, self.building_width

        # Recreate ghost with new dimensions (will use cache if available)
        self._create_ghost_building()

        print(f"Rotated building (now {self.building_width}x{self.building_depth})")
        return True

    def on_tertiary_use(self, hit_info):
        """Toggle grid snapping.

        Args:
            hit_info: Dictionary with hit information

        Returns:
            bool: True if action was performed
        """
        self.snap_to_grid = not self.snap_to_grid
        print(f"Grid snapping: {'ON' if self.snap_to_grid else 'OFF'} (size: {self.grid_size})")
        return True

    def adjust_primary_property(self, delta):
        """Adjust building size (scroll wheel).

        Args:
            delta: Amount to adjust

        Returns:
            tuple: (property_name, new_value)
        """
        # Adjust width
        self.building_width = max(5.0, min(30.0, self.building_width + delta))

        # Recreate ghost with new size (will use cache if available)
        self._create_ghost_building()

        return ("Building Width", self.building_width)

    def adjust_secondary_property(self, delta):
        """Adjust building height ([ ] keys).

        Args:
            delta: Amount to adjust

        Returns:
            tuple: (property_name, new_value)
        """
        # Adjust height
        self.building_height = max(4.0, min(20.0, self.building_height + delta))

        # Recreate ghost with new size (will use cache if available)
        self._create_ghost_building()

        return ("Building Height", self.building_height)

    def on_mouse_release(self, button):
        """Called when mouse button is released - reset placement flag.

        Args:
            button: Mouse button number (1=left, 2=middle, 3=right)
        """
        if button == 1:  # Left mouse button
            self.has_placed_this_click = False

    def set_placement_type(self, placement_type_number):
        """Switch to a different placement type (building/prop/model).

        Args:
            placement_type_number: Placement type number (1-4)

        Returns:
            str: Status message
        """
        if placement_type_number not in self.placement_types:
            return f"Invalid placement type: {placement_type_number}"

        # Ignore if already this type
        if self.current_placement_type == placement_type_number:
            return f"Already selected: {self.placement_types[placement_type_number]['name']}"

        # Prevent rapid switching
        if self.is_switching_type:
            return "Switching placement type... please wait"

        self.is_switching_type = True

        try:
            self.current_placement_type = placement_type_number

            # Load default dimensions for this placement type
            placement_info = self.placement_types[placement_type_number]
            self.building_width = placement_info["default_width"]
            self.building_depth = placement_info["default_depth"]
            self.building_height = placement_info["default_height"]

            # Recreate ghost with new placement type (will use cache if available)
            self._create_ghost_building()

            return f"Selected: {placement_info['name']} ({self.building_width}x{self.building_depth}x{self.building_height})"
        finally:
            self.is_switching_type = False

    # Backward compatibility alias
    def set_building_type(self, building_type_number):
        """Legacy method name - redirects to set_placement_type."""
        return self.set_placement_type(building_type_number)
