"""Placement tool - for placing buildings, props, and models with ghost preview."""

from math import cos, sin, radians

from panda3d.core import Vec3, TransparencyAttrib, KeyboardButton
from testgame.props.lantern_prop import LanternProp
from testgame.props.japanese_bar_prop import JapaneseBarProp
from testgame.structures.simple_building import SimpleBuilding
from testgame.structures.japanese_building import JapaneseBuilding
from testgame.tools.base import Tool, ToolType


class PlacementTool(Tool):
    """Tool for placing buildings, props, and models with ghost preview controlled by mouse."""

    def __init__(
        self,
        world,
        camera,
        render,
        bullet_world,
        terrain_raycaster=None,
        mouse_watcher=None,
        point_light_manager=None,
    ):
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

        # Ghost building preview cache (stores instance + precomputed offsets)
        self.ghost_buildings_cache = {}
        self.ghost_building = None
        self.ghost_position = Vec3(0, 0, 0)
        self.placement_valid = False

        # Settings
        self.max_placement_distance = 50.0
        self.snap_to_grid = True
        self.grid_size = 5.0  # Grid snap size
        self.current_rotation_deg = 0.0
        self.rotation_step = 15.0
        self.ghost_piece_offsets = {}
        self.rotation_gesture_active = False
        self.position_locked = False
        self.rotation_gesture_origin = Vec3(0, 0, 0)

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
        self.position_locked = False
        self.rotation_gesture_active = False

        # Hide current ghost if visible
        if self.ghost_building:
            self._hide_ghost_building()

        # Check if we have this building type cached
        cache_key = (
            self.current_placement_type,
            self.building_width,
            self.building_depth,
            self.building_height,
        )

        if cache_key in self.ghost_buildings_cache:
            # Reuse cached ghost entry
            cache_entry = self.ghost_buildings_cache[cache_key]
            self.ghost_building = cache_entry.get("instance")
            self.ghost_piece_offsets = cache_entry.get("offsets", {}).copy()
            self._show_ghost_building()
            self._apply_ghost_transform()
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
                    is_ghost=True,  # Mark as ghost preview
                )

                # Make the model semi-transparent green
                if (
                    hasattr(self.ghost_building, "model_node")
                    and self.ghost_building.model_node
                ):
                    self.ghost_building.model_node.setTransparency(
                        TransparencyAttrib.MAlpha
                    )
                    self.ghost_building.model_node.setColorScale(0.2, 1.0, 0.2, 0.4)

                # Disable collision for ghost physics body
                if (
                    hasattr(self.ghost_building, "physics_body")
                    and self.ghost_building.physics_body
                ):
                    # For Bullet physics, remove from physics world temporarily
                    # Ghost props don't need collision detection
                    try:
                        self.bullet_world.removeRigidBody(
                            self.ghost_building.physics_body.node()
                        )
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
                    name=f"ghost_building_{cache_key}",
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

            # Precompute offsets for rotation
            if building_type == "prop":
                self.ghost_piece_offsets = {}
            else:
                self.ghost_piece_offsets = self._compute_piece_offsets(
                    self.ghost_building
                )

            # Cache this ghost for reuse (store both instance and offsets)
            self.ghost_buildings_cache[cache_key] = {
                "instance": self.ghost_building,
                "offsets": self.ghost_piece_offsets.copy(),
            }

            # Ensure ghost uses current transform state
            self._apply_ghost_transform()

        except Exception as e:
            print(f"Error creating ghost building/prop: {e}")
            import traceback

            traceback.print_exc()
            self.ghost_building = None

    def _hide_ghost_building(self):
        """Hide the current ghost building/prop without destroying it."""
        if self.ghost_building:
            # Check if it's a prop or a building
            if hasattr(self.ghost_building, "pieces"):
                # Building with pieces
                for piece in self.ghost_building.pieces:
                    try:
                        if piece.body_np and not piece.body_np.isEmpty():
                            piece.body_np.hide()
                    except:
                        pass
            elif hasattr(self.ghost_building, "model_node"):
                # Prop with model_node
                if self.ghost_building.model_node:
                    self.ghost_building.model_node.hide()

    def _show_ghost_building(self):
        """Show the current ghost building/prop."""
        if self.ghost_building:
            # Check if it's a prop or a building
            if hasattr(self.ghost_building, "pieces"):
                # Building with pieces
                for piece in self.ghost_building.pieces:
                    try:
                        if piece.body_np and not piece.body_np.isEmpty():
                            piece.body_np.show()
                    except:
                        pass
            elif hasattr(self.ghost_building, "model_node"):
                # Prop with model_node
                if self.ghost_building.model_node:
                    self.ghost_building.model_node.show()

    def _remove_ghost_building(self):
        """Hide the ghost building preview (keeps cache)."""
        if self.ghost_building:
            self._hide_ghost_building()
            self.ghost_building = None
            self.ghost_piece_offsets = {}
            self.position_locked = False
            self.rotation_gesture_active = False

    def _compute_piece_offsets(self, building):
        """Compute local offsets for each piece relative to building origin."""
        base_pos = Vec3(building.position)
        offsets = {}
        for piece in getattr(building, "pieces", []):
            offsets[piece.name] = piece.position - base_pos
        return offsets

    def _apply_ghost_transform(self):
        """Apply current position and rotation to ghost preview."""
        if not self.ghost_building:
            return

        # Ensure we have offsets for buildings
        if hasattr(self.ghost_building, "pieces") and not self.ghost_piece_offsets:
            self.ghost_piece_offsets = self._compute_piece_offsets(self.ghost_building)

        heading = self.current_rotation_deg
        cos_h = cos(radians(heading))
        sin_h = sin(radians(heading))
        position = Vec3(self.ghost_position)

        if hasattr(self.ghost_building, "pieces"):
            for piece in self.ghost_building.pieces:
                offset = self.ghost_piece_offsets.get(piece.name)
                if offset is None:
                    offset = piece.position - self.ghost_building.position
                    self.ghost_piece_offsets[piece.name] = offset

                rotated = Vec3(
                    offset.x * cos_h - offset.y * sin_h,
                    offset.x * sin_h + offset.y * cos_h,
                    offset.z,
                )
                world_pos = position + rotated
                if piece.body_np and not piece.body_np.isEmpty():
                    piece.body_np.setPos(world_pos)
                    piece.body_np.setHpr(heading, 0, 0)
                piece.position = world_pos

            # Update building base position
            self.ghost_building.position = Vec3(position)

        elif hasattr(self.ghost_building, "set_position"):
            # Props implement set_position and optionally set_rotation
            self.ghost_building.set_position(position)
            if hasattr(self.ghost_building, "set_rotation"):
                self.ghost_building.set_rotation(heading)
            elif hasattr(self.ghost_building, "model_node"):
                node = self.ghost_building.model_node
                if node and not node.isEmpty():
                    node.setHpr(heading, 0, 0)

    def _apply_rotation_to_building_instance(self, building, heading, pivot):
        """Apply rotation to a real building instance after placement."""
        if not building or not hasattr(building, "pieces"):
            return

        pivot_vec = Vec3(pivot)
        cos_h = cos(radians(heading))
        sin_h = sin(radians(heading))

        offsets = {
            piece.name: piece.position - pivot_vec for piece in building.pieces
        }

        for piece in building.pieces:
            offset = offsets.get(piece.name, Vec3(0, 0, 0))
            rotated = Vec3(
                offset.x * cos_h - offset.y * sin_h,
                offset.x * sin_h + offset.y * cos_h,
                offset.z,
            )
            world_pos = pivot_vec + rotated
            if piece.body_np and not piece.body_np.isEmpty():
                piece.body_np.setPos(world_pos)
                piece.body_np.setHpr(heading, 0, 0)
            piece.position = world_pos

        building.position = Vec3(pivot_vec)
        setattr(building, "rotation", heading)

    def _rotate_ghost(self, delta_degrees):
        """Adjust current rotation and update ghost transform."""
        self.current_rotation_deg = (self.current_rotation_deg + delta_degrees) % 360.0
        self._apply_ghost_transform()

    def set_rotation(self, heading_degrees):
        """Set absolute rotation for the ghost preview."""
        self.current_rotation_deg = float(heading_degrees) % 360.0
        self._apply_ghost_transform()

    def begin_rotation_gesture(self):
        """Lock ghost position while rotating via mouse drag."""
        if not self.rotation_gesture_active:
            self.rotation_gesture_active = True
            self.position_locked = True
            self.rotation_gesture_origin = Vec3(self.ghost_position)

    def end_rotation_gesture(self):
        """Release position lock after mouse rotation gesture."""
        if self.rotation_gesture_active:
            self.rotation_gesture_active = False
            self.position_locked = False
            self.rotation_gesture_origin = Vec3(0, 0, 0)
            # Reapply transform to ensure final orientation persists cleanly
            self._apply_ghost_transform()

    def _is_shift_down(self):
        """Check if shift modifier is currently held."""
        if not self.mouse_watcher:
            return False
        return self.mouse_watcher.is_button_down(KeyboardButton.shift())

    def _get_rotation_step(self):
        """Determine rotation step based on modifier keys."""
        if not self.mouse_watcher:
            return self.rotation_step

        if self.mouse_watcher.is_button_down(KeyboardButton.control()):
            return 1.0

        if self.mouse_watcher.is_button_down(KeyboardButton.alt()):
            return 45.0

        return self.rotation_step

    def _to_vec3(self, value):
        """Convert tuples, Point3, or Vec3 into a Vec3 instance."""
        if isinstance(value, Vec3):
            return Vec3(value)

        if hasattr(value, "x") and hasattr(value, "y") and hasattr(value, "z"):
            return Vec3(value.x, value.y, value.z)

        if isinstance(value, (list, tuple)) and len(value) == 3:
            return Vec3(value[0], value[1], value[2])

        # Fallback to origin if value is invalid
        return Vec3(0, 0, 0)

    def _get_node_bounds(self, node, fallback_center=None, fallback_size=None):
        """Get axis-aligned bounds for a node or fallback dimensions."""
        if node and not node.isEmpty():
            bounds = node.getTightBounds()
            if bounds:
                min_pt, max_pt = bounds
                return self._to_vec3(min_pt), self._to_vec3(max_pt)

        if fallback_center is not None and fallback_size is not None:
            fallback_size_vec = (
                fallback_size
                if isinstance(fallback_size, Vec3)
                else self._to_vec3(fallback_size)
            )
            half = Vec3(
                fallback_size_vec.x / 2.0,
                fallback_size_vec.y / 2.0,
                fallback_size_vec.z / 2.0,
            )
            center = self._to_vec3(fallback_center)
            return center - half, center + half

        return None

    def _bounds_overlap(self, a_bounds, b_bounds):
        """Check for overlap between two axis-aligned bounding boxes."""
        if not a_bounds or not b_bounds:
            return False

        a_min, a_max = a_bounds
        b_min, b_max = b_bounds

        return (
            a_min.x < b_max.x
            and a_max.x > b_min.x
            and a_min.y < b_max.y
            and a_max.y > b_min.y
            and a_min.z < b_max.z
            and a_max.z > b_min.z
        )

    def _update_ghost_position(self, position):
        """Update the position of the ghost building/prop.

        Args:
            position: Vec3 world position
        """
        if not self.ghost_building:
            return

        if self.position_locked:
            return

        # Apply grid snapping if enabled
        if self.snap_to_grid:
            position = Vec3(
                round(position.x / self.grid_size) * self.grid_size,
                round(position.y / self.grid_size) * self.grid_size,
                position.z,
            )

        self.ghost_position = position
        self._apply_ghost_transform()

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
        if hasattr(self.ghost_building, "pieces"):
            # Building with pieces
            for piece in self.ghost_building.pieces:
                piece.body_np.setColorScale(*color)
        elif hasattr(self.ghost_building, "model_node"):
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

        existing_buildings = [
            b for b in self.world.buildings if not b.name.startswith("ghost")
        ]
        existing_props = self.world.props if hasattr(self.world, "props") else []

        ghost_bounds = []

        if hasattr(self.ghost_building, "pieces"):
            for ghost_piece in self.ghost_building.pieces:
                node = ghost_piece.body_np if hasattr(ghost_piece, "body_np") else None
                bounds = self._get_node_bounds(
                    node,
                    fallback_center=ghost_piece.position,
                    fallback_size=ghost_piece.size,
                )
                if bounds:
                    ghost_bounds.append(bounds)
        else:
            prop_node = None
            if hasattr(self.ghost_building, "model_node") and self.ghost_building.model_node:
                prop_node = self.ghost_building.model_node
            elif (
                hasattr(self.ghost_building, "physics_body")
                and self.ghost_building.physics_body
            ):
                prop_node = self.ghost_building.physics_body

            fallback_size = getattr(
                self.ghost_building, "FALLBACK_DIMENSIONS", (1.0, 1.0, 1.0)
            )
            bounds = self._get_node_bounds(
                prop_node,
                fallback_center=self.ghost_position,
                fallback_size=fallback_size,
            )
            if bounds:
                ghost_bounds.append(bounds)

        if not ghost_bounds:
            return True

        for bounds in ghost_bounds:
            # Against existing buildings
            for building in existing_buildings:
                for piece in building.pieces:
                    node = piece.body_np if hasattr(piece, "body_np") else None
                    piece_bounds = self._get_node_bounds(
                        node,
                        fallback_center=piece.position,
                        fallback_size=piece.size,
                    )
                    if self._bounds_overlap(bounds, piece_bounds):
                        return False

            # Against existing props
            for prop in existing_props:
                prop_node = None
                if hasattr(prop, "model_node") and prop.model_node:
                    prop_node = prop.model_node
                elif hasattr(prop, "physics_body") and prop.physics_body:
                    prop_node = prop.physics_body

                fallback_size = getattr(prop, "FALLBACK_DIMENSIONS", (1.0, 1.0, 1.0))
                prop_bounds = self._get_node_bounds(
                    prop_node,
                    fallback_center=prop.get_position() if hasattr(prop, "get_position") else None,
                    fallback_size=fallback_size,
                )
                if self._bounds_overlap(bounds, prop_bounds):
                    return False

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
                if not self.position_locked:
                    self._update_ghost_position(hit_pos)

                # Check if placement is valid
                check_pos = (
                    self.ghost_position if self.position_locked else hit_pos
                )
                valid = self._check_placement_valid(check_pos)
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
                static=True,  # Props are static by default
            )

            # Apply current rotation before adding
            if hasattr(new_prop, "set_rotation"):
                new_prop.set_rotation(self.current_rotation_deg)

            # Add prop to world
            self.world.add_prop(new_prop)

            print(f"Placed {building_info['name']} at {self.ghost_position}")

        else:
            # Create regular building
            building_count = len(
                [b for b in self.world.buildings if not b.name.startswith("ghost")]
            )

            new_building = building_class(
                self.bullet_world,
                self.render,
                self.ghost_position,
                width=self.building_width,
                depth=self.building_depth,
                height=self.building_height,
                name=f"{building_type_name}_{building_count}",
            )

            # Add building to world
            self.world.add_building(new_building)

            # Rotate building to match preview
            self._apply_rotation_to_building_instance(
                new_building, self.current_rotation_deg, self.ghost_position
            )

            print(
                f"Placed building at {self.ghost_position} (size: {self.building_width}x{self.building_depth}x{self.building_height})"
            )

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
        if not self.ghost_building:
            return False

        step = self._get_rotation_step()
        delta = -step if self._is_shift_down() else step
        self._rotate_ghost(delta)

        direction = "counter-clockwise" if delta < 0 else "clockwise"
        print(
            f"Rotated placement {direction} to {self.current_rotation_deg:.1f} degrees"
        )
        return True

    def on_tertiary_use(self, hit_info):
        """Toggle grid snapping.

        Args:
            hit_info: Dictionary with hit information

        Returns:
            bool: True if action was performed
        """
        self.snap_to_grid = not self.snap_to_grid
        print(
            f"Grid snapping: {'ON' if self.snap_to_grid else 'OFF'} (size: {self.grid_size})"
        )
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
