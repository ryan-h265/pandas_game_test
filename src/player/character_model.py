"""Character model for third-person view."""

import math
from panda3d.core import (
    GeomVertexFormat,
    GeomVertexData,
    GeomVertexWriter,
    Geom,
    GeomTriangles,
    GeomNode,
    Vec3,
    Vec4,
)


class CharacterModel:
    """A basic character model for third-person view."""

    def __init__(self, render, position=None):
        """Initialize the character model.

        Args:
            render: Panda3D render node
            position: Starting position Vec3
        """
        self.render = render
        self.node_path = None
        self.position = position if position else Vec3(0, 0, 0)

        # Animation state
        self.animation_time = 0.0
        self.is_moving = False
        self.is_running = False
        self.is_jumping = False

        # Store node paths for limbs (for animation)
        self.left_leg = None
        self.right_leg = None
        self.left_arm = None
        self.right_arm = None
        self.body = None
        self.head = None

        # Create the character mesh
        self._create_character_mesh()

    def _create_character_mesh(self):
        """Create a simple humanoid character mesh with separate limbs for animation."""
        # Create main character node
        self.node_path = self.render.attachNewNode("character")
        self.node_path.setPos(self.position)

        # Define character proportions (simple humanoid)
        # Total height: ~1.8 units (typical human height)

        # Body dimensions
        body_width = 0.4
        body_depth = 0.3
        body_height = 0.8
        body_bottom = 0.0

        # Head dimensions
        head_size = 0.25
        head_bottom = body_bottom + body_height

        # Leg dimensions
        leg_width = 0.15
        leg_depth = 0.15
        leg_height = 0.9
        leg_bottom = body_bottom - leg_height

        # Arm dimensions
        arm_width = 0.12
        arm_depth = 0.12
        arm_height = 0.6
        arm_bottom = body_bottom + body_height - 0.1
        arm_offset = body_width / 2 + arm_width / 2

        # Colors
        skin_color = Vec4(0.9, 0.7, 0.6, 1.0)
        shirt_color = Vec4(0.3, 0.5, 0.8, 1.0)
        pants_color = Vec4(0.2, 0.3, 0.5, 1.0)

        # Helper function to create a box part as a separate node
        def create_box_part(name, width, depth, height, box_color):
            """Create a box part as a separate node."""
            vformat = GeomVertexFormat.getV3n3c4()
            vdata = GeomVertexData(name, vformat, Geom.UHStatic)

            vertex = GeomVertexWriter(vdata, "vertex")
            normal = GeomVertexWriter(vdata, "normal")
            color = GeomVertexWriter(vdata, "color")

            x_min = -width / 2
            x_max = width / 2
            y_min = -depth / 2
            y_max = depth / 2
            z_min = 0
            z_max = height

            # Define the 8 corners of the box
            corners = [
                Vec3(x_min, y_min, z_min),  # 0: front-bottom-left
                Vec3(x_max, y_min, z_min),  # 1: front-bottom-right
                Vec3(x_max, y_max, z_min),  # 2: back-bottom-right
                Vec3(x_min, y_max, z_min),  # 3: back-bottom-left
                Vec3(x_min, y_min, z_max),  # 4: front-top-left
                Vec3(x_max, y_min, z_max),  # 5: front-top-right
                Vec3(x_max, y_max, z_max),  # 6: back-top-right
                Vec3(x_min, y_max, z_max),  # 7: back-top-left
            ]

            # Define faces with their vertices and normals
            faces = [
                # Front face (facing -Y)
                ([0, 1, 5, 4], Vec3(0, -1, 0)),
                # Back face (facing +Y)
                ([3, 7, 6, 2], Vec3(0, 1, 0)),
                # Left face (facing -X)
                ([0, 4, 7, 3], Vec3(-1, 0, 0)),
                # Right face (facing +X)
                ([1, 2, 6, 5], Vec3(1, 0, 0)),
                # Top face (facing +Z)
                ([4, 5, 6, 7], Vec3(0, 0, 1)),
                # Bottom face (facing -Z)
                ([0, 3, 2, 1], Vec3(0, 0, -1)),
            ]

            vertices = []
            for face_vertices, face_normal in faces:
                for idx in face_vertices:
                    vertices.append((corners[idx], face_normal, box_color))

            # Write vertices
            for v, n, c in vertices:
                vertex.addData3(v)
                normal.addData3(n)
                color.addData4(c)

            # Create triangles
            tris = GeomTriangles(Geom.UHStatic)
            num_faces = len(vertices) // 4

            for face_idx in range(num_faces):
                base = face_idx * 4
                tris.addVertices(base + 0, base + 1, base + 2)
                tris.addVertices(base + 0, base + 2, base + 3)

            tris.closePrimitive()

            # Create geometry and node
            geom = Geom(vdata)
            geom.addPrimitive(tris)
            node = GeomNode(name)
            node.addGeom(geom)

            # Create node path
            part_np = self.node_path.attachNewNode(node)
            part_np.setTwoSided(False)

            return part_np

        # Build character parts as separate nodes for animation
        # Torso (body) - centered at origin
        self.body = create_box_part(
            "body", body_width, body_depth, body_height, shirt_color
        )
        self.body.setPos(0, 0, body_bottom)

        # Head - attached to top of body
        self.head = create_box_part(
            "head", head_size * 2, head_size * 2, head_size * 2, skin_color
        )
        self.head.setPos(0, 0, head_bottom)

        # Left leg - pivot at hip
        self.left_leg = create_box_part(
            "left_leg", leg_width, leg_depth, leg_height, pants_color
        )
        self.left_leg.setPos(-body_width / 4, 0, body_bottom)

        # Right leg - pivot at hip
        self.right_leg = create_box_part(
            "right_leg", leg_width, leg_depth, leg_height, pants_color
        )
        self.right_leg.setPos(body_width / 4, 0, body_bottom)

        # Left arm - pivot at shoulder
        self.left_arm = create_box_part(
            "left_arm", arm_width, arm_depth, arm_height, skin_color
        )
        self.left_arm.setPos(-arm_offset, 0, arm_bottom)

        # Right arm - pivot at shoulder
        self.right_arm = create_box_part(
            "right_arm", arm_width, arm_depth, arm_height, skin_color
        )
        self.right_arm.setPos(arm_offset, 0, arm_bottom)

    def set_position(self, position):
        """Set the character model position.

        Args:
            position: Vec3 position
        """
        self.position = position
        if self.node_path:
            self.node_path.setPos(position)

    def set_heading(self, heading):
        """Set the character's heading (yaw rotation).

        Args:
            heading: Heading angle in degrees
        """
        if self.node_path:
            self.node_path.setHpr(heading, 0, 0)

    def show(self):
        """Show the character model."""
        if self.node_path:
            self.node_path.show()

    def hide(self):
        """Hide the character model."""
        if self.node_path:
            self.node_path.hide()

    def remove(self):
        """Remove the character model from the scene."""
        if self.node_path:
            self.node_path.removeNode()
            self.node_path = None

    def update(self, dt, is_moving=False, is_running=False, is_jumping=False):
        """Update character animations.

        Args:
            dt: Delta time since last update
            is_moving: Whether the character is moving
            is_running: Whether the character is running
            is_jumping: Whether the character is jumping
        """
        self.is_moving = is_moving
        self.is_running = is_running
        self.is_jumping = is_jumping

        if is_moving:
            # Update animation time
            speed_multiplier = 2.0 if is_running else 1.0
            self.animation_time += dt * speed_multiplier * 8.0

            # Walking/running animation (swinging limbs)
            # Legs swing opposite to each other
            leg_swing = math.sin(self.animation_time) * 30.0  # 30 degrees max swing
            arm_swing = math.sin(self.animation_time) * 20.0  # 20 degrees max swing

            # Left leg and right arm swing forward together
            # Right leg and left arm swing forward together
            if self.left_leg:
                self.left_leg.setHpr(0, leg_swing, 0)
            if self.right_leg:
                self.right_leg.setHpr(0, -leg_swing, 0)
            if self.left_arm:
                self.left_arm.setHpr(0, -arm_swing, 0)
            if self.right_arm:
                self.right_arm.setHpr(0, arm_swing, 0)

            # Add subtle body bob
            if self.body:
                bob_height = abs(math.sin(self.animation_time)) * 0.05
                body_pos = self.body.getPos()
                self.body.setZ(body_pos.getZ() + bob_height * 0.1)

        else:
            # Reset to idle pose
            if self.left_leg:
                self.left_leg.setHpr(0, 0, 0)
            if self.right_leg:
                self.right_leg.setHpr(0, 0, 0)
            if self.left_arm:
                self.left_arm.setHpr(0, 0, 0)
            if self.right_arm:
                self.right_arm.setHpr(0, 0, 0)

        # Jump animation (not yet implemented - would need vertical velocity info)
        if is_jumping:
            # Could add arms raised, legs tucked animation
            if self.left_arm:
                self.left_arm.setHpr(0, -45, 0)
            if self.right_arm:
                self.right_arm.setHpr(0, -45, 0)
