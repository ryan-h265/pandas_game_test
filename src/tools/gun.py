"""Gun tool - ranged weapon with visual effects."""

from .base import Tool, ToolType


class GunTool(Tool):
    """Ranged weapon for shooting buildings from distance."""

    def __init__(self, world, camera, effects_manager=None, building_raycaster=None):
        """Initialize gun tool.

        Args:
            world: Game world instance
            camera: Camera node for aiming
            effects_manager: EffectsManager for visual effects
            building_raycaster: BuildingRaycaster for physics raycasting
        """
        super().__init__("Gun", ToolType.GUN)
        self.world = world
        self.camera = camera
        self.effects_manager = effects_manager
        self.building_raycaster = building_raycaster
        self.damage_per_shot = 100
        self.fire_rate = 0.3  # Seconds between shots
        self.last_shot_time = 0.0
        self.current_time = 0.0
        self.max_range = 100.0
        self.bullets_fired = 0

    def on_activate(self):
        """Called when gun is equipped."""
        return "Equipped: Gun (ranged damage)"

    def on_primary_use(self, hit_info):
        """Fire gun at target.

        Args:
            hit_info: Dictionary with hit information (from terrain raycast)

        Returns:
            bool: True if shot was fired
        """
        # Check cooldown
        if self.current_time - self.last_shot_time < self.fire_rate:
            return False

        # Get camera position in world space
        camera_pos = self.camera.getPos(self.world.render)

        # Get forward direction from camera's transformation matrix
        # This properly accounts for both heading (yaw) and pitch
        cam_mat = self.camera.getMat(self.world.render)
        forward = cam_mat.getRow3(1)  # Y-axis (forward) from transformation matrix
        forward.normalize()

        # Check if using voxel system
        hit_something = False
        end_pos = camera_pos + forward * self.max_range  # Default miss position

        # Legacy building system
        if self.building_raycaster:
            physics_hit = self.building_raycaster.raycast_from_camera(self.camera, self.max_range)

            if physics_hit["hit"]:
                end_pos = physics_hit["position"]
                hit_something = True
                damaged = self.world.damage_building_at_position(end_pos, damage=self.damage_per_shot)
                print(f"Gun HIT building at distance {physics_hit['distance']:.2f}")
        elif hit_info and hit_info.get("position"):
            end_pos = hit_info["position"]
            hit_something = True
            self.world.damage_building_at_position(end_pos, damage=self.damage_per_shot)

        # Create visual effects
        if self.effects_manager:
            # Start bullet trail offset from camera (gun barrel position)
            muzzle_pos = camera_pos + forward * 3.0  # 3 units forward from camera
            self.effects_manager.create_bullet_trail(muzzle_pos, end_pos)
            self.effects_manager.create_muzzle_flash(muzzle_pos, forward)

            # Create debug ray visualization (shows exact raycast)
            self.effects_manager.create_debug_ray(camera_pos, end_pos, hit_something)

        self.last_shot_time = self.current_time
        self.bullets_fired += 1
        return True

    def update(self, dt):
        """Update gun state.

        Args:
            dt: Delta time
        """
        self.current_time += dt

    def adjust_primary_property(self, delta):
        """Adjust gun damage.

        Args:
            delta: Amount to adjust

        Returns:
            tuple: (property_name, new_value)
        """
        self.damage_per_shot = max(10, min(200, self.damage_per_shot + delta * 5))
        return ("Damage", self.damage_per_shot)

    def adjust_secondary_property(self, delta):
        """Adjust gun fire rate.

        Args:
            delta: Amount to adjust

        Returns:
            tuple: (property_name, new_value)
        """
        self.fire_rate = max(0.1, min(2.0, self.fire_rate + delta * 10))
        return ("Fire Rate", self.fire_rate)
