"""Japanese stone lantern prop with glTF model and lighting."""

from panda3d.core import Vec3, Vec4
from props.base_prop import BaseProp


class LanternProp(BaseProp):
    """A Japanese stone lantern prop that can be placed in the world."""

    # Model configuration
    MODEL_PATH = "assets/models/props/japanese_stone_lantern/scene.gltf"
    DEFAULT_SCALE_TARGET = ('height', 1.5)  # Scale to 1.5m tall
    FALLBACK_DIMENSIONS = (0.5, 0.5, 1.5)  # width, depth, height
    FALLBACK_COLOR = Vec4(0.6, 0.6, 0.65, 1.0)  # Stone color
    PHYSICS_HALF_EXTENTS = Vec3(0.4, 0.4, 0.75)  # Collision box
    PHYSICS_MASS = 50.0  # Stone lanterns are heavy

    def __init__(self, world, render, position, point_light_manager=None, static=True, is_ghost=False):
        """Create a Japanese stone lantern.

        Args:
            world: Bullet physics world
            render: Panda3D render node
            position: Vec3 world position
            point_light_manager: Optional PointLightManager to add light source
            static: If True, lantern is static (immovable). If False, it's dynamic
            is_ghost: If True, this is a ghost preview (don't apply final shaders/colors)
        """
        # Initialize light reference before calling parent init
        self.light = None
        
        # Call parent constructor
        super().__init__(world, render, position, point_light_manager, static, is_ghost)

        # Add light if point light manager is provided (not for ghosts)
        if point_light_manager and not is_ghost:
            self._create_light()

    def _create_light(self):
        """Create a warm light source inside the lantern."""
        if not self.point_light_manager:
            return

        # Light position: slightly above center of lantern (where the paper section glows)
        light_offset = Vec3(0, 0, 1.2)  # Adjust based on your model's proportions
        light_pos = self.position + light_offset

        # Warm orange/yellow glow (traditional paper lantern color)
        light_color = (1.0, 0.75, 0.4)  # Warm orange-yellow

        # Add the light
        self.light = self.point_light_manager.add_light(
            position=light_pos,
            color=light_color,
            radius=15.0,  # Moderate radius for ambient lighting
            intensity=3.5,  # Gentle glow
        )

        # Enable subtle flickering for a candle-like effect
        if self.light:
            self.light.set_flicker(True, speed=3.0, amount=0.08)

        print(f"Added lantern light at {light_pos}")

    def set_position(self, position):
        """Override to update light position as well."""
        super().set_position(position)
        
        # Update light position
        if self.light:
            light_offset = Vec3(0, 0, 1.2)
            self.light.position = Vec3(position) + light_offset

    def remove(self):
        """Override to remove light as well."""
        # Remove light first
        if self.light and self.point_light_manager:
            self.point_light_manager.remove_light(self.light)
            self.light = None
        
        # Call parent removal
        super().remove()

    def update(self, dt):
        """Override to sync light with physics."""
        # Call parent update
        super().update(dt)
        
        # If the lantern is dynamic and has moved, update the light position
        if not self.static and self.light and self.physics_body:
            current_pos = self.physics_body.getPos()
            light_offset = Vec3(0, 0, 0.5)  # Adjust to paper section height
            self.light.position = current_pos + light_offset
