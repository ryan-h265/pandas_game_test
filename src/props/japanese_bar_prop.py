"""Japanese bar prop with glTF model."""

from panda3d.core import Vec3, Vec4
from panda3d.bullet import BulletRigidBodyNode, BulletBoxShape
from rendering.model_loader import get_model_loader


class JapaneseBarProp:
    """A Japanese bar/building prop that can be placed in the world."""

    # Model path (relative to project root)
    MODEL_PATH = "assets/models/props/japanese_bar/scene.gltf"

    def __init__(self, world, render, position, point_light_manager=None, static=True, is_ghost=False):
        """Create a Japanese bar.

        Args:
            world: Bullet physics world
            render: Panda3D render node
            position: Vec3 world position
            point_light_manager: Optional PointLightManager (not used for bar, but kept for API consistency)
            static: If True, bar is static (immovable). If False, it's dynamic (physics-enabled)
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
        loader = get_model_loader()
        model = loader.load_gltf(self.MODEL_PATH, cache=True)

        if model is None:
            print(f"ERROR: Failed to load Japanese bar model from {self.MODEL_PATH}")
            print("Creating fallback placeholder geometry")
            self._create_fallback_geometry()
            return

        # Attach model to render
        # If model is a PandaNode (like ModelRoot), wrap it in a NodePath
        from panda3d.core import NodePath, PandaNode
        if isinstance(model, PandaNode):
            self.model_node = NodePath(model)
        else:
            self.model_node = model

        self.model_node.reparentTo(self.render)

        # Flatten the transform hierarchy to fix offset issues
        # Use flattenMedium() to preserve materials and textures
        self.model_node.flattenMedium()

        # Now position it
        self.model_node.setPos(self.position)

        # Scale the model to appropriate size
        # Bars are typically larger than lanterns - around 8x10 meters
        bounds = self.model_node.getTightBounds()
        if bounds:
            min_point, max_point = bounds
            # Use width for scaling (bars are wider than tall typically)
            width = max_point.x - min_point.x
            # Scale to approximately 8 meters wide
            desired_width = 8.0
            scale_factor = desired_width / width if width > 0 else 0.01
            self.model_node.setScale(scale_factor)
            print(f"Japanese bar original width: {width:.2f}, scaled by {scale_factor:.4f} to {desired_width}m")

        # Only apply final colors/shaders if this is NOT a ghost preview
        if not self.is_ghost:
            # Ensure proper color (reset any color scale that might be applied)
            self.model_node.clearColorScale()
            self.model_node.setColorScale(1, 1, 1, 1)  # Explicitly set to white

            # Clear any transparency that might have been set
            self.model_node.clearTransparency()

            # Apply custom glTF shader that supports both textures AND point lights
            from panda3d.core import Shader
            import os

            # Get absolute paths to shader files
            shader_dir = os.path.abspath("assets/shaders")
            vert_path = os.path.join(shader_dir, "gltf_model.vert")
            frag_path = os.path.join(shader_dir, "gltf_model.frag")

            gltf_shader = Shader.load(
                Shader.SL_GLSL,
                vertex=vert_path,
                fragment=frag_path
            )

            if gltf_shader:
                self.model_node.setShader(gltf_shader)
                print(f"Loaded Japanese bar model with custom shader at {self.position}")
            else:
                print(f"ERROR: Failed to load glTF shader for bar, using default rendering")
        else:
            print(f"Loaded ghost Japanese bar preview at {self.position}")

    def _create_fallback_geometry(self):
        """Create simple fallback geometry if model fails to load."""
        from panda3d.core import GeomVertexFormat, GeomVertexData, GeomVertexWriter
        from panda3d.core import Geom, GeomTriangles, GeomNode

        # Create a simple box as fallback
        vformat = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData("bar_fallback", vformat, Geom.UHStatic)

        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        color = GeomVertexWriter(vdata, "color")

        # Bar dimensions (approximate)
        width = 8.0
        depth = 6.0
        height = 4.0

        # Wood color
        wood_color = Vec4(0.6, 0.4, 0.2, 1.0)

        # Create box vertices
        half_w = width / 2
        half_d = depth / 2

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
                color.addData4(wood_color)

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
        node = GeomNode("bar_fallback")
        node.addGeom(geom)

        # Attach to scene
        self.model_node = self.render.attachNewNode(node)
        self.model_node.setPos(self.position)

        print(f"Created fallback Japanese bar geometry at {self.position}")

    def _create_physics(self):
        """Create physics body for the bar."""
        # Approximate bar bounding box (larger than lantern)
        # Adjust these dimensions based on your actual model size
        half_extents = Vec3(4.0, 3.0, 2.0)  # Width, depth, half-height

        # Create collision shape
        shape = BulletBoxShape(half_extents)

        # Create rigid body node
        body_node = BulletRigidBodyNode(f"japanese_bar_{id(self)}")

        if self.static:
            # Static bar (doesn't move)
            body_node.setMass(0)
        else:
            # Dynamic bar (can be destroyed/moved)
            body_node.setMass(500.0)  # Buildings are very heavy
            body_node.setFriction(0.8)
            body_node.setRestitution(0.1)

        body_node.addShape(shape)

        # Create node path and position it
        self.physics_body = self.render.attachNewNode(body_node)
        self.physics_body.setPos(self.position + Vec3(0, 0, half_extents.z))  # Center at midpoint

        # Add to physics world
        self.world.attachRigidBody(body_node)

        # If we have a visual model, it's already positioned separately
        print(f"Created {'static' if self.static else 'dynamic'} physics body for Japanese bar")

    def get_position(self):
        """Get the current world position of the bar.

        Returns:
            Vec3: Current position
        """
        if self.physics_body:
            return self.physics_body.getPos()
        elif self.model_node:
            return self.model_node.getPos()
        return self.position

    def set_position(self, position):
        """Set the bar's position.

        Args:
            position: Vec3 new position
        """
        self.position = Vec3(position)

        if self.physics_body:
            self.physics_body.setPos(position)

        if self.model_node and self.static:
            self.model_node.setPos(position)

    def remove(self):
        """Remove the bar from the scene."""
        # Remove physics body
        if self.physics_body:
            self.world.removeRigidBody(self.physics_body.node())
            self.physics_body.removeNode()
            self.physics_body = None

        # Remove visual model
        if self.model_node:
            self.model_node.removeNode()
            self.model_node = None

        print(f"Removed Japanese bar at {self.position}")

    def update(self, dt):
        """Update the bar (e.g., sync physics).

        Args:
            dt: Delta time since last update
        """
        # If the bar is dynamic and has moved, update position tracking
        if not self.static and self.physics_body:
            self.position = self.physics_body.getPos()
