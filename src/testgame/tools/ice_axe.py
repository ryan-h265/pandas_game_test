"""Ice Axe tool - versatile climbing and combat tool."""

from .base import Tool, ToolType


class IceAxeTool(Tool):
    """Tool for climbing, terrain modification, and combat."""

    def __init__(self, world, camera, building_raycaster=None, terrain_editor=None):
        """Initialize ice axe tool.

        Args:
            world: Game world instance
            camera: Camera node for aiming
            building_raycaster: BuildingRaycaster for physics raycasting
            terrain_editor: TerrainEditor for terrain modification
        """
        super().__init__("Ice Axe", ToolType.ICE_AXE)
        self.world = world
        self.camera = camera
        self.building_raycaster = building_raycaster
        self.terrain_editor = terrain_editor
        
        # Combat properties
        self.damage_per_hit = 75  # Between fist (50) and crowbar (100)
        self.swing_cooldown = 0.4  # Faster than crowbar (0.5), slower than fist
        self.last_swing_time = 0.0
        self.current_time = 0.0
        self.max_range = 8.0  # Medium range
        
        # Terrain modification properties
        self.brush_size = 2.0
        self.brush_strength = 0.3
        self.min_brush_size = 0.5
        self.max_brush_size = 8.0
        self.min_brush_strength = 0.1
        self.max_brush_strength = 1.0

    def on_activate(self):
        """Called when ice axe is equipped."""
        return "Equipped: Ice Axe (combat & terrain tool)"

    def on_primary_use(self, hit_info):
        """Primary attack - damage buildings or dig terrain.

        Args:
            hit_info: Dictionary with hit information

        Returns:
            bool: True if something was hit
        """
        # Check cooldown
        if self.current_time - self.last_swing_time < self.swing_cooldown:
            return False

        # Try building damage first (combat)
        if self.building_raycaster:
            physics_hit = self.building_raycaster.raycast_from_camera(
                self.camera, self.max_range
            )

            if physics_hit["hit"]:
                hit_pos = physics_hit["position"]
                damaged = self.world.damage_building_at_position(
                    hit_pos, damage=self.damage_per_hit
                )

                if damaged:
                    self.last_swing_time = self.current_time
                    print(
                        f"Ice Axe HIT building at distance {physics_hit['distance']:.2f}"
                    )
                    return True

        # If no building hit, try terrain modification (digging)
        if hit_info and hit_info.get("hit") and self.terrain_editor:
            hit_pos = hit_info["position"]
            
            # Dig downward with ice axe
            def dig_brush(x, z, distance_from_center):
                """Brush function for digging terrain."""
                if distance_from_center <= self.brush_size:
                    # Stronger effect at center, weaker at edges
                    strength_factor = 1.0 - (distance_from_center / self.brush_size)
                    return -self.brush_strength * strength_factor
                return 0.0

            self.terrain_editor.modify_terrain_at_position(
                hit_pos, self.brush_size, dig_brush
            )
            self.last_swing_time = self.current_time
            print(f"Ice Axe DUG terrain at {hit_pos}")
            return True

        return False

    def on_secondary_use(self, hit_info):
        """Secondary action - build up terrain (ice climbing holds).

        Args:
            hit_info: Dictionary with hit information

        Returns:
            bool: True if terrain was modified
        """
        if hit_info and hit_info.get("hit") and self.terrain_editor:
            hit_pos = hit_info["position"]
            
            # Build up terrain to create climbing holds
            def build_brush(x, z, distance_from_center):
                """Brush function for building terrain."""
                if distance_from_center <= self.brush_size * 0.7:  # Smaller build area
                    strength_factor = 1.0 - (distance_from_center / (self.brush_size * 0.7))
                    return self.brush_strength * 0.5 * strength_factor  # Gentler building
                return 0.0

            self.terrain_editor.modify_terrain_at_position(
                hit_pos, self.brush_size * 0.7, build_brush
            )
            print(f"Ice Axe BUILT terrain at {hit_pos}")
            return True

        return False

    def on_tertiary_use(self, hit_info):
        """Tertiary action - flatten terrain for stable footing.

        Args:
            hit_info: Dictionary with hit information

        Returns:
            bool: True if terrain was modified
        """
        if hit_info and hit_info.get("hit") and self.terrain_editor:
            hit_pos = hit_info["position"]
            target_height = hit_pos[1]  # Use hit point height as target
            
            # Flatten terrain around the hit point
            def flatten_brush(x, z, distance_from_center):
                """Brush function for flattening terrain."""
                if distance_from_center <= self.brush_size:
                    # Get current height at this point
                    current_height = self.terrain_editor.get_height_at_world_pos(x, z)
                    if current_height is not None:
                        height_diff = target_height - current_height
                        strength_factor = 1.0 - (distance_from_center / self.brush_size)
                        return height_diff * self.brush_strength * 0.3 * strength_factor
                return 0.0

            self.terrain_editor.modify_terrain_at_position(
                hit_pos, self.brush_size, flatten_brush
            )
            print(f"Ice Axe FLATTENED terrain at {hit_pos}")
            return True

        return False

    def update(self, dt):
        """Update ice axe state.

        Args:
            dt: Delta time
        """
        self.current_time += dt

    def adjust_primary_property(self, delta):
        """Adjust brush size with scroll wheel.

        Args:
            delta: Amount to adjust

        Returns:
            tuple: (property_name, new_value)
        """
        old_size = self.brush_size
        self.brush_size = max(
            self.min_brush_size,
            min(self.max_brush_size, self.brush_size + delta * 0.5)
        )
        
        if abs(self.brush_size - old_size) > 0.01:
            return ("Brush Size", f"{self.brush_size:.1f}")
        return None

    def adjust_secondary_property(self, delta):
        """Adjust brush strength with [ ] keys.

        Args:
            delta: Amount to adjust

        Returns:
            tuple: (property_name, new_value)
        """
        old_strength = self.brush_strength
        self.brush_strength = max(
            self.min_brush_strength,
            min(self.max_brush_strength, self.brush_strength + delta * 0.1)
        )
        
        if abs(self.brush_strength - old_strength) > 0.01:
            return ("Brush Strength", f"{self.brush_strength:.2f}")
        return None