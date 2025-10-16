"""Japanese bar prop with glTF model."""

from panda3d.core import Vec3, Vec4
from props.base_prop import BaseProp


class JapaneseBarProp(BaseProp):
    """A Japanese bar/building prop that can be placed in the world."""

    # Model configuration
    MODEL_PATH = "assets/models/props/japanese_bar/scene.gltf"
    DEFAULT_SCALE_TARGET = ('width', 8.0)  # Scale to 8m wide
    FALLBACK_DIMENSIONS = (8.0, 6.0, 4.0)  # width, depth, height
    FALLBACK_COLOR = Vec4(0.6, 0.4, 0.2, 1.0)  # Wood color
    PHYSICS_HALF_EXTENTS = Vec3(4.0, 3.0, 2.0)  # Collision box
    PHYSICS_MASS = 500.0  # Buildings are very heavy

    def __init__(self, world, render, position, point_light_manager=None, static=True, is_ghost=False):
        """Create a Japanese bar.

        Args:
            world: Bullet physics world
            render: Panda3D render node
            position: Vec3 world position
            point_light_manager: Optional PointLightManager (not used for bar, but kept for API consistency)
            static: If True, bar is static (immovable). If False, it's dynamic
            is_ghost: If True, this is a ghost preview (don't apply final shaders/colors)
        """
        # Call parent constructor
        super().__init__(world, render, position, point_light_manager, static, is_ghost)
