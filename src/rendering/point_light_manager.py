"""Point light manager for dynamic lights like torches and lanterns."""

from panda3d.core import Vec3, Vec4


class PointLight:
    """Represents a single point light source."""

    def __init__(self, position, color=(1.0, 0.8, 0.5), radius=15.0, intensity=5.0):
        """Initialize a point light.

        Args:
            position: World position (Vec3)
            color: RGB color tuple (default: warm orange for torch)
            radius: Maximum radius of light effect
            intensity: Brightness multiplier
        """
        self.position = Vec3(position)
        self.color = Vec3(*color)
        self.radius = radius
        self.intensity = intensity
        self.enabled = True

        # Optional: Flickering parameters
        self.flicker_enabled = False
        self.flicker_speed = 5.0
        self.flicker_amount = 0.15
        self._flicker_time = 0.0
        self._base_intensity = intensity

    def update(self, dt):
        """Update light (for flickering animation).

        Args:
            dt: Delta time since last frame
        """
        if self.flicker_enabled:
            import math

            self._flicker_time += dt * self.flicker_speed

            # Smooth flickering using sine waves
            flicker = math.sin(self._flicker_time) * 0.5 + 0.5
            flicker += math.sin(self._flicker_time * 2.3) * 0.25
            flicker /= 1.5

            # Apply flicker to intensity
            variation = flicker * self.flicker_amount
            self.intensity = self._base_intensity * (1.0 - self.flicker_amount + variation)

    def set_flicker(self, enabled, speed=5.0, amount=0.15):
        """Enable/disable flickering effect.

        Args:
            enabled: True to enable flickering
            speed: Flicker speed multiplier
            amount: Flicker intensity variation (0.0-1.0)
        """
        self.flicker_enabled = enabled
        self.flicker_speed = speed
        self.flicker_amount = amount
        if enabled:
            self._base_intensity = self.intensity


class PointLightManager:
    """Manages dynamic point lights for the scene."""

    MAX_LIGHTS = 32  # Must match shader MAX_POINT_LIGHTS (increased from 8)

    def __init__(self):
        """Initialize the point light manager."""
        self.lights = []

    def add_light(self, position, color=(1.0, 0.8, 0.5), radius=15.0, intensity=5.0):
        """Add a new point light to the scene.

        Args:
            position: World position (Vec3 or tuple)
            color: RGB color tuple (default: warm torch color)
            radius: Maximum radius of light effect
            intensity: Brightness multiplier

        Returns:
            The created PointLight object

        Note:
            You can now add unlimited lights! The system will automatically
            select the nearest/brightest MAX_LIGHTS lights each frame.
        """
        light = PointLight(position, color, radius, intensity)
        self.lights.append(light)
        print(
            f"Added point light at {position}, color={color}, radius={radius}, intensity={intensity}"
        )
        print(f"Total lights in scene: {len(self.lights)}")
        return light

    def remove_light(self, light):
        """Remove a point light from the scene.

        Args:
            light: The PointLight object to remove
        """
        if light in self.lights:
            self.lights.remove(light)

    def clear_lights(self):
        """Remove all point lights."""
        self.lights.clear()

    def update(self, dt):
        """Update all lights (for animations like flickering).

        Args:
            dt: Delta time since last frame
        """
        for light in self.lights:
            if light.enabled:
                light.update(dt)

    def set_shader_inputs(self, node_path, camera_pos=None, max_distance=None):
        """Set shader inputs for all active lights.

        Args:
            node_path: NodePath to apply shader inputs to
            camera_pos: Optional camera position for distance culling
            max_distance: Optional maximum distance for light culling (default: auto from radius)
        """
        # Filter and sort lights
        active_lights = [light for light in self.lights if light.enabled]

        # Smart culling: Sort by distance and brightness
        if camera_pos:
            # Calculate "importance" score: closer lights and brighter lights rank higher
            def light_importance(light):
                distance = (light.position - camera_pos).length()
                # If light is beyond its radius + safety margin, it won't affect the camera
                effective_distance = max(0.1, distance - light.radius)
                # Importance = brightness / distance (inverse square-ish)
                importance = (light.intensity * light.radius) / (effective_distance * effective_distance)
                return importance

            # Sort by importance (highest first)
            active_lights.sort(key=light_importance, reverse=True)

            # Optional hard distance culling
            if max_distance:
                active_lights = [
                    light
                    for light in active_lights
                    if (light.position - camera_pos).length() < max_distance
                ]

        # Limit to max shader capacity (most important lights only)
        active_lights = active_lights[: self.MAX_LIGHTS]

        # Prepare arrays for shader
        positions = []
        colors = []
        radii = []
        intensities = []

        for light in active_lights:
            positions.append(light.position)
            colors.append(light.color)
            radii.append(light.radius)
            intensities.append(light.intensity)

        # Pad arrays to MAX_LIGHTS (some GPUs require fixed-size arrays)
        while len(positions) < self.MAX_LIGHTS:
            positions.append(Vec3(0, 0, 0))
            colors.append(Vec3(0, 0, 0))
            radii.append(0.0)
            intensities.append(0.0)

        # Set shader inputs
        node_path.setShaderInput("numPointLights", len(active_lights))

        # Convert to Vec4 arrays for Panda3D GLSL
        pos_vec4s = [Vec4(p.x, p.y, p.z, 0) for p in positions]
        color_vec4s = [Vec4(c.x, c.y, c.z, 0) for c in colors]

        # Set as uniform arrays (Panda3D way)
        node_path.setShaderInput("pointLightPositions", pos_vec4s)
        node_path.setShaderInput("pointLightColors", color_vec4s)
        node_path.setShaderInput("pointLightRadii", radii)
        node_path.setShaderInput("pointLightIntensities", intensities)

    def get_light_count(self):
        """Get the number of active lights.

        Returns:
            Number of enabled lights
        """
        return sum(1 for light in self.lights if light.enabled)

    def get_light_at_index(self, index):
        """Get a light by index.

        Args:
            index: Light index

        Returns:
            PointLight object or None
        """
        if 0 <= index < len(self.lights):
            return self.lights[index]
        return None
