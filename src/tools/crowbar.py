"""Crowbar tool - high-damage melee weapon for breaking structures."""

from .base import Tool, ToolType


class CrowbarTool(Tool):
    """Tool for breaking building pieces (melee weapon)."""

    def __init__(self, world, camera, building_raycaster=None):
        """Initialize crowbar tool.

        Args:
            world: Game world instance
            camera: Camera node for aiming
            building_raycaster: BuildingRaycaster for physics raycasting
        """
        super().__init__("Crowbar", ToolType.CROWBAR)
        self.world = world
        self.camera = camera
        self.building_raycaster = building_raycaster
        self.damage_per_hit = 100  # Increased for voxels
        self.swing_cooldown = 0.5  # Seconds between swings
        self.last_swing_time = 0.0
        self.current_time = 0.0
        self.max_range = 10.0  # Melee range (shorter than gun)

    def on_activate(self):
        """Called when crowbar is equipped."""
        return "Equipped: Crowbar (high damage to walls)"

    def on_primary_use(self, hit_info):
        """Swing crowbar to damage buildings.

        Args:
            hit_info: Dictionary with hit information (from terrain raycast, not used)

        Returns:
            bool: True if something was hit
        """
        # Check cooldown
        if self.current_time - self.last_swing_time < self.swing_cooldown:
            return False

        # Legacy building system
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
                        f"Crowbar HIT building at distance {physics_hit['distance']:.2f}"
                    )
                    return True
        return False

    def on_secondary_use(self, hit_info):
        """Secondary action (could be used for prying)."""
        # For now, same as primary
        return self.on_primary_use(hit_info)

    def update(self, dt):
        """Update crowbar state.

        Args:
            dt: Delta time
        """
        self.current_time += dt

    def adjust_primary_property(self, delta):
        """Adjust crowbar damage.

        Args:
            delta: Amount to adjust

        Returns:
            tuple: (property_name, new_value)
        """
        self.damage_per_hit = max(10, min(150, self.damage_per_hit + delta * 5))
        return ("Damage", self.damage_per_hit)

    def adjust_secondary_property(self, delta):
        """Adjust crowbar swing speed (cooldown).

        Args:
            delta: Amount to adjust

        Returns:
            tuple: (property_name, new_value)
        """
        self.swing_cooldown = max(0.1, min(2.0, self.swing_cooldown + delta * 10))
        return ("Cooldown", self.swing_cooldown)
