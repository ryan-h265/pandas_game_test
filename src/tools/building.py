"""Building tool - for placing structures with ghost preview."""

from .base import Tool, ToolType
from panda3d.core import Vec3, Vec4, TransparencyAttrib
from structures.building import SimpleBuilding


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

        # Building parameters (adjustable)
        self.building_width = 10.0
        self.building_depth = 10.0
        self.building_height = 8.0

        # Ghost building preview
        self.ghost_building = None
        self.ghost_position = Vec3(0, 0, 0)
        self.placement_valid = False

        # Settings
        self.max_placement_distance = 50.0
        self.snap_to_grid = True
        self.grid_size = 5.0  # Grid snap size

    def on_activate(self):
        """Called when building tool is equipped."""
        self._create_ghost_building()
        return f"Equipped: Building Placer ({self.building_width}x{self.building_depth}x{self.building_height})"

    def on_deactivate(self):
        """Called when tool is switched away from."""
        super().on_deactivate()
        self._remove_ghost_building()

    def _create_ghost_building(self):
        """Create a transparent ghost preview of the building."""
        if self.ghost_building:
            self._remove_ghost_building()

        # Create a simple building as the ghost
        self.ghost_building = SimpleBuilding(
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
        if not self.ghost_building or not self.placement_valid:
            print("Cannot place building here!")
            return False

        # Create the actual building at ghost position
        building_count = len([b for b in self.world.buildings if not b.name.startswith("ghost")])
        new_building = SimpleBuilding(
            self.bullet_world,
            self.render,
            self.ghost_position,
            width=self.building_width,
            depth=self.building_depth,
            height=self.building_height,
            name=f"building_{building_count}"
        )

        # Add building to world
        self.world.add_building(new_building)

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
