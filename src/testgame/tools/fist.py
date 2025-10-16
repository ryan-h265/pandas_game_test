"""Fist tool - default melee interaction tool."""

from .base import Tool, ToolType


class FistTool(Tool):
    """Default tool - bare hands for basic interaction."""

    def __init__(self, world, camera, building_raycaster=None):
        """Initialize fist tool.

        Args:
            world: Game world instance
            camera: Camera node for aiming
            building_raycaster: BuildingRaycaster for physics raycasting
        """
        super().__init__("Fist", ToolType.FIST)
        self.world = world
        self.camera = camera
        self.building_raycaster = building_raycaster
        self.damage_per_hit = 50  # Increased for voxels
        self.max_range = 5.0  # Very short melee range

    def on_activate(self):
        """Called when fist is equipped."""
        return "Equipped: Fist (basic interaction)"

    def on_primary_use(self, hit_info):
        """Punch buildings/voxels.

        Args:
            hit_info: Dictionary with hit information (from terrain raycast, not used)

        Returns:
            bool: True if something was hit
        """
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
                    print(
                        f"Fist HIT building at distance {physics_hit['distance']:.2f}"
                    )
                    return True

        return False

    def adjust_primary_property(self, delta):
        """Adjust fist damage.

        Args:
            delta: Amount to adjust

        Returns:
            tuple: (property_name, new_value)
        """
        self.damage_per_hit = max(5, min(100, self.damage_per_hit + delta * 5))
        return ("Damage", self.damage_per_hit)

    def adjust_secondary_property(self, delta):
        """Adjust fist range.

        Args:
            delta: Amount to adjust

        Returns:
            tuple: (property_name, new_value)
        """
        self.max_range = max(2.0, min(10.0, self.max_range + delta * 10))
        return ("Range", self.max_range)
