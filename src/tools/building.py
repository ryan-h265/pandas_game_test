"""Building tool - for placing structures with ghost preview."""

from .base import Tool, ToolType
from panda3d.core import Vec3, Vec4, TransparencyAttrib
from structures.simple_building import SimpleBuilding
from structures.japanese_building import JapaneseBuilding


class BuildingTool(Tool):
    """Tool for placing buildings with ghost preview controlled by mouse."""

    def __init__(self, world, camera, render, bullet_world, terrain_raycaster=None, mouse_watcher=None):
        """Initialize building tool.

        Args:
            world: Game world instance
            camera: Camera node for raycasting
            render: Panda3D render node
            bullet_world: Bullet physics world
            terrain_raycaster: TerrainRaycaster for ground placement
            mouse_watcher: MouseWatcher node for raycasting
        """
        super().__init__("Building Placer", ToolType.BUILDING)
        self.world = world
        self.camera = camera
        self.render = render
        self.bullet_world = bullet_world
        self.terrain_raycaster = terrain_raycaster
        self.mouse_watcher = mouse_watcher

        # Building type selection
        self.building_types = {
            1: {
                "name": "Simple Building",
                "class": SimpleBuilding,
                "default_width": 10.0,
                "default_depth": 10.0,
                "default_height": 8.0,
            },
            2: {
                "name": "Japanese Building",
                "class": JapaneseBuilding,
                "default_width": 12.0,
                "default_depth": 10.0,
                "default_height": 6.0,
            },
            3: {
                "name": "TODO: Building Type 3",
                "class": SimpleBuilding,  # Placeholder
                "default_width": 10.0,
                "default_depth": 10.0,
                "default_height": 8.0,
            },
            4: {
                "name": "TODO: Building Type 4",
                "class": SimpleBuilding,  # Placeholder
                "default_width": 10.0,
                "default_depth": 10.0,
                "default_height": 8.0,
            },
        }
        self.current_building_type = 1  # Start with Simple Building

        # Building parameters (adjustable)
        self.building_width = self.building_types[1]["default_width"]
        self.building_depth = self.building_types[1]["default_depth"]
        self.building_height = self.building_types[1]["default_height"]

        # Ghost building preview
        self.ghost_building = None
        self.ghost_position = Vec3(0, 0, 0)
        self.placement_valid = False

        # Settings
        self.max_placement_distance = 50.0
        self.snap_to_grid = True
        self.grid_size = 5.0  # Grid snap size

        # Track if we've already placed a building on this mouse press
        self.has_placed_this_click = False

    def on_activate(self):
        """Called when building tool is equipped."""
        self._create_ghost_building()
        building_name = self.building_types[self.current_building_type]["name"]
        return f"Equipped: {building_name} ({self.building_width}x{self.building_depth}x{self.building_height})"

    def on_deactivate(self):
        """Called when tool is switched away from."""
        super().on_deactivate()
        self._remove_ghost_building()

    def _create_ghost_building(self):
        """Create a transparent ghost preview of the building."""
        if self.ghost_building:
            self._remove_ghost_building()

        # Get the current building type class
        building_class = self.building_types[self.current_building_type]["class"]

        # Create a building as the ghost using the selected type
        self.ghost_building = building_class(
            self.bullet_world,
            self.render,
            self.ghost_position,
            width=self.building_width,
            depth=self.building_depth,
            height=self.building_height,
            name="ghost_building"
        )

        # Make all pieces transparent and greenish (valid placement color)
        for piece in self.ghost_building.pieces:
            # Set transparency
            piece.body_np.setTransparency(TransparencyAttrib.MAlpha)

            # Update color to semi-transparent green (valid placement)
            piece.body_np.setColorScale(0.2, 1.0, 0.2, 0.4)

        # Remove all pieces from physics world (ghost shouldn't collide)
        for piece in self.ghost_building.pieces:
            try:
                self.bullet_world.removeRigidBody(piece.body_np.node())
            except:
                pass  # May not be attached

    def _remove_ghost_building(self):
        """Remove the ghost building preview."""
        if self.ghost_building:
            # Remove all pieces from scene (but not from physics world, already removed)
            for piece in self.ghost_building.pieces:
                piece.body_np.removeNode()

            self.ghost_building.pieces.clear()
            self.ghost_building.piece_map.clear()
            self.ghost_building = None

    def _update_ghost_position(self, position):
        """Update the position of the ghost building.

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

        # Update all piece positions relative to base position
        for piece in self.ghost_building.pieces:
            # Calculate offset from original building position
            offset = piece.position - self.ghost_building.position
            new_pos = position + offset
            piece.body_np.setPos(new_pos)
            piece.position = new_pos

        # Update building base position
        self.ghost_building.position = position

    def _set_ghost_color(self, valid):
        """Set the ghost building color based on placement validity.

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

        for piece in self.ghost_building.pieces:
            piece.body_np.setColorScale(*color)

    def _check_placement_valid(self, position):
        """Check if placement at position is valid (not overlapping existing buildings).

        Args:
            position: Vec3 world position

        Returns:
            bool: True if placement is valid
        """
        # For now, always valid (could add collision checking later)
        # TODO: Check if position overlaps with existing buildings
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
        """Place the building at current ghost position.

        Args:
            hit_info: Dictionary with hit information (not used, we use ghost position)

        Returns:
            bool: True if building was placed
        """
        # Only place one building per mouse click
        if self.has_placed_this_click:
            return False

        if not self.ghost_building or not self.placement_valid:
            print("Cannot place building here!")
            return False

        # Create the actual building at ghost position using current building type
        building_count = len([b for b in self.world.buildings if not b.name.startswith("ghost")])
        building_class = self.building_types[self.current_building_type]["class"]
        building_type_name = self.building_types[self.current_building_type]["name"].lower().replace(" ", "_")

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

        # Mark that we've placed a building on this click
        self.has_placed_this_click = True

        print(f"Placed building at {self.ghost_position} (size: {self.building_width}x{self.building_depth}x{self.building_height})")
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

        # Recreate ghost with new dimensions
        self._remove_ghost_building()
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

        # Recreate ghost with new size
        self._remove_ghost_building()
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

        # Recreate ghost with new size
        self._remove_ghost_building()
        self._create_ghost_building()

        return ("Building Height", self.building_height)

    def on_mouse_release(self, button):
        """Called when mouse button is released - reset placement flag.

        Args:
            button: Mouse button number (1=left, 2=middle, 3=right)
        """
        if button == 1:  # Left mouse button
            self.has_placed_this_click = False

    def set_building_type(self, building_type_number):
        """Switch to a different building type.

        Args:
            building_type_number: Building type number (1-4)

        Returns:
            str: Status message
        """
        if building_type_number not in self.building_types:
            return f"Invalid building type: {building_type_number}"

        self.current_building_type = building_type_number

        # Load default dimensions for this building type
        building_info = self.building_types[building_type_number]
        self.building_width = building_info["default_width"]
        self.building_depth = building_info["default_depth"]
        self.building_height = building_info["default_height"]

        # Recreate ghost with new building type
        self._remove_ghost_building()
        self._create_ghost_building()

        return f"Selected: {building_info['name']} ({self.building_width}x{self.building_depth}x{self.building_height})"
