"""Base class for glTF props with physics."""

from panda3d.core import Vec3, Vec4, NodePath, PandaNode
from panda3d.core import GeomVertexFormat, GeomVertexData, GeomVertexWriter
from panda3d.core import Geom, GeomTriangles, GeomNode, Shader
from panda3d.bullet import BulletRigidBodyNode, BulletBoxShape
from testgame.rendering.model_loader import get_model_loader
import os


class BaseProp:
    """Base class for placeable props with glTF models and physics.

    Subclasses should define:
        - MODEL_PATH: Path to glTF model file
        - DEFAULT_SCALE_TARGET: Tuple of ('width'|'height'|'depth', desired_meters)
        - FALLBACK_DIMENSIONS: (width, depth, height) for fallback geometry
        - FALLBACK_COLOR: Vec4 color for fallback geometry
        - PHYSICS_HALF_EXTENTS: Vec3 half extents for collision box
        - PHYSICS_MASS: Float mass (0 = static)
    """

    # Subclasses should override these
    MODEL_PATH = None
    DEFAULT_SCALE_TARGET = ("height", 1.5)  # ('dimension', meters)
    FALLBACK_DIMENSIONS = (1.0, 1.0, 1.5)  # width, depth, height
    FALLBACK_COLOR = Vec4(0.7, 0.7, 0.7, 1.0)
    PHYSICS_HALF_EXTENTS = Vec3(0.5, 0.5, 0.75)
    PHYSICS_MASS = 50.0

    def __init__(
        self,
        world,
        render,
        position,
        point_light_manager=None,
        static=True,
        is_ghost=False,
    ):
        """Create a prop.

        Args:
            world: Bullet physics world
            render: Panda3D render node
            position: Vec3 world position
            point_light_manager: Optional PointLightManager for light sources
            static: If True, prop is static (immovable). If False, it's dynamic
            is_ghost: If True, this is a ghost preview (don't apply final shaders/colors)
        """
        self.world = world
        self.render = render
        self.position = Vec3(position)
        self.point_light_manager = point_light_manager
        self.static = static
        self.is_ghost = is_ghost

        # References
        self.model_node = None
        self.physics_body = None

        # Load the model
        self._load_model()

        # Create physics body
        self._create_physics()

    def _load_model(self):
        """Load the glTF model."""
        if not self.MODEL_PATH:
            print(f"ERROR: {self.__class__.__name__} has no MODEL_PATH defined")
            self._create_fallback_geometry()
            return

        loader = get_model_loader()
        model = loader.load_gltf(self.MODEL_PATH, cache=True)

        if model is None:
            print(f"ERROR: Failed to load model from {self.MODEL_PATH}")
            print("Creating fallback placeholder geometry")
            self._create_fallback_geometry()
            return

        # Attach model to render
        if isinstance(model, PandaNode):
            self.model_node = NodePath(model)
        else:
            self.model_node = model

        self.model_node.reparentTo(self.render)

        # Flatten the transform hierarchy to fix offset issues
        self.model_node.flattenMedium()

        # Position it
        self.model_node.setPos(self.position)

        # Scale the model to appropriate size
        bounds = self.model_node.getTightBounds()
        if bounds:
            min_point, max_point = bounds
            dimension, target_size = self.DEFAULT_SCALE_TARGET

            # Get the appropriate dimension
            if dimension == "width":
                current_size = max_point.x - min_point.x
            elif dimension == "height":
                current_size = max_point.z - min_point.z
            elif dimension == "depth":
                current_size = max_point.y - min_point.y
            else:
                print(f"ERROR: Unknown scale dimension '{dimension}'")
                current_size = 1.0

            scale_factor = target_size / current_size if current_size > 0 else 0.01
            self.model_node.setScale(scale_factor)
            print(
                f"{self.__class__.__name__} original {dimension}: {current_size:.2f}, "
                f"scaled by {scale_factor:.4f} to {target_size}m"
            )

        # Only apply final colors/shaders if this is NOT a ghost preview
        if not self.is_ghost:
            # Ensure proper color
            self.model_node.clearColorScale()
            self.model_node.setColorScale(1, 1, 1, 1)
            self.model_node.clearTransparency()

            # Apply custom glTF shader
            shader_dir = os.path.abspath("assets/shaders")
            vert_path = os.path.join(shader_dir, "gltf_model.vert")
            frag_path = os.path.join(shader_dir, "gltf_model.frag")

            gltf_shader = Shader.load(
                Shader.SL_GLSL, vertex=vert_path, fragment=frag_path
            )

            if gltf_shader:
                self.model_node.setShader(gltf_shader)
                print(
                    f"Loaded {self.__class__.__name__} with custom shader at {self.position}"
                )
            else:
                print(
                    f"ERROR: Failed to load glTF shader for {self.__class__.__name__}"
                )
        else:
            print(f"Loaded ghost {self.__class__.__name__} preview at {self.position}")

    def _create_fallback_geometry(self):
        """Create simple fallback geometry if model fails to load."""
        vformat = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData(
            f"{self.__class__.__name__}_fallback", vformat, Geom.UHStatic
        )

        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        color = GeomVertexWriter(vdata, "color")

        width, depth, height = self.FALLBACK_DIMENSIONS
        half_w = width / 2
        half_d = depth / 2

        # Create box vertices
        corners = [
            Vec3(-half_w, -half_d, 0),
            Vec3(half_w, -half_d, 0),
            Vec3(half_w, half_d, 0),
            Vec3(-half_w, half_d, 0),
            Vec3(-half_w, -half_d, height),
            Vec3(half_w, -half_d, height),
            Vec3(half_w, half_d, height),
            Vec3(-half_w, half_d, height),
        ]

        faces = [
            ([0, 1, 2, 3], Vec3(0, 0, -1)),
            ([4, 5, 6, 7], Vec3(0, 0, 1)),
            ([0, 1, 5, 4], Vec3(0, -1, 0)),
            ([2, 3, 7, 6], Vec3(0, 1, 0)),
            ([0, 4, 7, 3], Vec3(-1, 0, 0)),
            ([1, 2, 6, 5], Vec3(1, 0, 0)),
        ]

        for face_indices, face_normal in faces:
            for idx in face_indices:
                vertex.addData3(corners[idx])
                normal.addData3(face_normal)
                color.addData4(self.FALLBACK_COLOR)

        # Create triangles
        tris = GeomTriangles(Geom.UHStatic)
        for face_idx in range(6):
            base = face_idx * 4
            tris.addVertices(base + 0, base + 1, base + 2)
            tris.addVertices(base + 0, base + 2, base + 3)
        tris.closePrimitive()

        # Create geom and node
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        node = GeomNode(f"{self.__class__.__name__}_fallback")
        node.addGeom(geom)

        # Attach to scene
        self.model_node = self.render.attachNewNode(node)
        self.model_node.setPos(self.position)

        print(f"Created fallback {self.__class__.__name__} geometry at {self.position}")

    def _create_physics(self):
        """Create physics body for the prop."""
        # Create collision shape
        shape = BulletBoxShape(self.PHYSICS_HALF_EXTENTS)

        # Create rigid body node
        body_node = BulletRigidBodyNode(f"{self.__class__.__name__}_{id(self)}")

        if self.static:
            body_node.setMass(0)
        else:
            body_node.setMass(self.PHYSICS_MASS)
            body_node.setFriction(0.8)
            body_node.setRestitution(0.1)

        body_node.addShape(shape)

        # Create node path and position it
        self.physics_body = self.render.attachNewNode(body_node)
        self.physics_body.setPos(
            self.position + Vec3(0, 0, self.PHYSICS_HALF_EXTENTS.z)
        )

        # Add to physics world
        self.world.attachRigidBody(body_node)

        # For dynamic objects, reparent model to physics body
        if self.model_node and not self.static:
            self.model_node.reparentTo(self.physics_body)
            self.model_node.setPos(0, 0, -self.PHYSICS_HALF_EXTENTS.z)

        print(
            f"Created {'static' if self.static else 'dynamic'} physics body for {self.__class__.__name__}"
        )

    def get_position(self):
        """Get the current world position of the prop.

        Returns:
            Vec3: Current position
        """
        if self.physics_body:
            return self.physics_body.getPos()
        elif self.model_node:
            return self.model_node.getPos()
        return self.position

    def set_position(self, position):
        """Set the prop's position.

        Args:
            position: Vec3 new position
        """
        self.position = Vec3(position)

        if self.physics_body:
            self.physics_body.setPos(position)

        if self.model_node and self.static:
            self.model_node.setPos(position)

    def remove(self):
        """Remove the prop from the scene."""
        # Remove physics body
        if self.physics_body:
            self.world.removeRigidBody(self.physics_body.node())
            self.physics_body.removeNode()
            self.physics_body = None

        # Remove visual model
        if self.model_node:
            self.model_node.removeNode()
            self.model_node = None

        print(f"Removed {self.__class__.__name__} at {self.position}")

    def update(self, dt):
        """Update the prop (e.g., sync physics).

        Args:
            dt: Delta time since last update
        """
        # If the prop is dynamic and has moved, update position tracking
        if not self.static and self.physics_body:
            self.position = self.physics_body.getPos()
