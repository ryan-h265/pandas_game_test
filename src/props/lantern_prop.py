"""Japanese stone lantern prop with glTF model and lighting."""

from panda3d.core import Vec3, Vec4
from panda3d.bullet import BulletRigidBodyNode, BulletBoxShape
from rendering.model_loader import get_model_loader


class LanternProp:
    """A Japanese stone lantern prop that can be placed in the world."""

    # Model path (relative to project root)
    MODEL_PATH = "assets/models/props/japanese_stone_lantern/scene.gltf"

    def __init__(self, world, render, position, point_light_manager=None, static=True, is_ghost=False):
        """Create a Japanese stone lantern.

        Args:
            world: Bullet physics world
            render: Panda3D render node
            position: Vec3 world position
            point_light_manager: Optional PointLightManager to add light source
            static: If True, lantern is static (immovable). If False, it's dynamic (physics-enabled)
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
        self.light = None

        # Load the model
        self._load_model()

        # Create physics body
        self._create_physics()

        # Add light if point light manager is provided (not for ghosts)
        if point_light_manager and not is_ghost:
            self._create_light()

    def _load_model(self):
        """Load the glTF model."""
        loader = get_model_loader()
        model = loader.load_gltf(self.MODEL_PATH, cache=True)

        if model is None:
            print(f"ERROR: Failed to load lantern model from {self.MODEL_PATH}")
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
        # Use flattenMedium() to preserve materials and textures (flattenStrong would destroy them)
        self.model_node.flattenMedium()

        # Now position it
        self.model_node.setPos(self.position)

        # The model is very large (scaled by 100 internally), scale it down
        # Typical lantern height should be around 1.5-2 meters
        bounds = self.model_node.getTightBounds()
        if bounds:
            min_point, max_point = bounds
            height = max_point.z - min_point.z
            # Scale to approximately 1.5 meters tall
            desired_height = 1.5
            scale_factor = desired_height / height if height > 0 else 0.01
            self.model_node.setScale(scale_factor)
            print(f"Lantern original height: {height:.2f}, scaled by {scale_factor:.4f} to {desired_height}m")

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

            print(f"Loading shader from: {vert_path}")

            gltf_shader = Shader.load(
                Shader.SL_GLSL,
                vertex=vert_path,
                fragment=frag_path
            )

            if gltf_shader:
                self.model_node.setShader(gltf_shader)
                print(f"Loaded Japanese stone lantern model with custom shader at {self.position}")
            else:
                print(f"ERROR: Failed to load glTF shader, using default rendering")
                print(f"  Vertex shader: {vert_path}")
                print(f"  Fragment shader: {frag_path}")
        else:
            print(f"Loaded ghost lantern preview at {self.position}")

    def _debug_textures(self, node, indent=0):
        """Debug helper to print texture information."""
        prefix = "  " * indent

        # Check if this node has textures
        if node.hasTexture():
            print(f"{prefix}Node: {node.getName()} - HAS TEXTURES")
            # Try to get texture attribute
            if node.hasAttrib("TextureAttrib"):
                tex_attrib = node.getAttrib("TextureAttrib")
                print(f"{prefix}  Texture attribute: {tex_attrib}")

        # Check children
        for child in node.getChildren():
            self._debug_textures(child, indent + 1)

    def _create_fallback_geometry(self):
        """Create simple fallback geometry if model fails to load."""
        from panda3d.core import GeomVertexFormat, GeomVertexData, GeomVertexWriter
        from panda3d.core import Geom, GeomTriangles, GeomNode

        # Create a simple stone-colored box as fallback
        vformat = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData("lantern_fallback", vformat, Geom.UHStatic)

        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        color = GeomVertexWriter(vdata, "color")

        # Lantern dimensions (approximate)
        width = 0.5
        depth = 0.5
        height = 1.5

        # Stone color
        stone_color = Vec4(0.6, 0.6, 0.65, 1.0)

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
                color.addData4(stone_color)

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
        node = GeomNode("lantern_fallback")
        node.addGeom(geom)

        # Attach to scene
        self.model_node = self.render.attachNewNode(node)
        self.model_node.setPos(self.position)

        print(f"Created fallback lantern geometry at {self.position}")

    def _create_physics(self):
        """Create physics body for the lantern."""
        # Approximate lantern bounding box
        # Adjust these dimensions based on your actual model size
        half_extents = Vec3(0.4, 0.4, 0.75)  # Width, depth, half-height

        # Create collision shape
        shape = BulletBoxShape(half_extents)

        # Create rigid body node
        body_node = BulletRigidBodyNode(f"lantern_{id(self)}")

        if self.static:
            # Static lantern (doesn't move)
            body_node.setMass(0)
        else:
            # Dynamic lantern (can be knocked over)
            body_node.setMass(50.0)  # Stone lanterns are heavy
            body_node.setFriction(0.8)
            body_node.setRestitution(0.1)  # Very little bounce (stone)

        body_node.addShape(shape)

        # Create node path and position it
        self.physics_body = self.render.attachNewNode(body_node)
        self.physics_body.setPos(self.position + Vec3(0, 0, half_extents.z))  # Center at midpoint

        # Add to physics world
        self.world.attachRigidBody(body_node)

        # If we have a visual model, attach it to the physics body
        if self.model_node and not self.static:
            # For dynamic objects, reparent model to physics body
            # so it moves with physics
            old_pos = self.model_node.getPos()
            self.model_node.reparentTo(self.physics_body)
            self.model_node.setPos(0, 0, -half_extents.z)  # Offset to align with ground

        print(f"Created {'static' if self.static else 'dynamic'} physics body for lantern")

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

    def get_position(self):
        """Get the current world position of the lantern.

        Returns:
            Vec3: Current position
        """
        if self.physics_body:
            return self.physics_body.getPos()
        elif self.model_node:
            return self.model_node.getPos()
        return self.position

    def set_position(self, position):
        """Set the lantern's position.

        Args:
            position: Vec3 new position
        """
        self.position = Vec3(position)

        if self.physics_body:
            self.physics_body.setPos(position)

        if self.model_node and self.static:
            self.model_node.setPos(position)

        # Update light position
        if self.light:
            light_offset = Vec3(0, 0, 1.2)
            self.light.position = Vec3(position) + light_offset

    def remove(self):
        """Remove the lantern from the scene."""
        # Remove physics body
        if self.physics_body:
            self.world.removeRigidBody(self.physics_body.node())
            self.physics_body.removeNode()
            self.physics_body = None

        # Remove visual model
        if self.model_node:
            self.model_node.removeNode()
            self.model_node = None

        # Remove light
        if self.light and self.point_light_manager:
            self.point_light_manager.remove_light(self.light)
            self.light = None

        print(f"Removed lantern at {self.position}")

    def update(self, dt):
        """Update the lantern (e.g., sync light with physics).

        Args:
            dt: Delta time since last update
        """
        # If the lantern is dynamic and has moved, update the light position
        if not self.static and self.light and self.physics_body:
            current_pos = self.physics_body.getPos()
            light_offset = Vec3(0, 0, 0.5)  # Adjust to paper section height
            self.light.position = current_pos + light_offset
