"""Building system with destructible physics-based structures."""

import random
from panda3d.core import Vec3, Vec4
from panda3d.core import GeomNode, GeomVertexFormat, GeomVertexData, GeomVertexWriter
from panda3d.core import Geom, GeomTriangles
from panda3d.bullet import (
    BulletRigidBodyNode,
    BulletBoxShape,
    BulletGenericConstraint,
)


class Fragment:
    """A small fragment created when a building piece breaks."""

    def __init__(self, world, render, position, size, color, impulse=None):
        """Create a small debris fragment.

        Args:
            world: Bullet physics world
            render: Panda3D render node
            position: Vec3 world position
            size: Vec3 dimensions (small)
            color: Vec4 RGBA color
            impulse: Optional Vec3 impulse to apply
        """
        self.world = world
        self.render = render
        self.creation_time = 0  # Will be set by building manager
        self.lifetime = 10.0  # Fragments disappear after 10 seconds

        # Create small physics cube
        half_extents = Vec3(size.x / 2, size.y / 2, size.z / 2)
        shape = BulletBoxShape(half_extents)

        # Create rigid body
        body_node = BulletRigidBodyNode(f"fragment_{id(self)}")
        body_node.setMass(0.5)  # Light fragments
        body_node.addShape(shape)
        body_node.setFriction(0.8)
        body_node.setRestitution(0.2)  # Some bounce
        body_node.setLinearDamping(0.5)  # Air resistance
        body_node.setAngularDamping(0.6)

        # Attach to scene
        self.body_np = render.attachNewNode(body_node)
        self.body_np.setPos(position)

        # Add to physics world
        world.attachRigidBody(body_node)

        # Apply impulse if provided
        if impulse:
            body_node.applyCentralImpulse(impulse)
            # Add some random spin
            torque = Vec3(
                random.uniform(-5, 5),
                random.uniform(-5, 5),
                random.uniform(-5, 5),
            )
            body_node.applyTorqueImpulse(torque)

        # Create simple visual geometry
        self._create_visual(half_extents, color)

    def _create_visual(self, half_extents, color):
        """Create simple visual geometry for fragment."""
        vformat = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData("fragment_vdata", vformat, Geom.UHStatic)

        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        color_writer = GeomVertexWriter(vdata, "color")

        # Simple box vertices
        s = half_extents
        vertices = [
            Vec3(-s.x, -s.y, -s.z),
            Vec3(s.x, -s.y, -s.z),
            Vec3(s.x, s.y, -s.z),
            Vec3(-s.x, s.y, -s.z),
            Vec3(-s.x, -s.y, s.z),
            Vec3(s.x, -s.y, s.z),
            Vec3(s.x, s.y, s.z),
            Vec3(-s.x, s.y, s.z),
        ]

        faces = [
            ([3, 2, 1, 0], Vec3(0, 0, -1)),
            ([4, 5, 6, 7], Vec3(0, 0, 1)),
            ([1, 5, 4, 0], Vec3(0, -1, 0)),
            ([3, 7, 6, 2], Vec3(0, 1, 0)),
            ([4, 7, 3, 0], Vec3(-1, 0, 0)),
            ([2, 6, 5, 1], Vec3(1, 0, 0)),
        ]

        tris = GeomTriangles(Geom.UHStatic)
        vtx_index = 0

        for face_indices, face_normal in faces:
            for i in [0, 1, 2]:
                v = vertices[face_indices[i]]
                vertex.addData3(v)
                normal.addData3(face_normal)
                color_writer.addData4(color)
                tris.addVertex(vtx_index)
                vtx_index += 1

            for i in [0, 2, 3]:
                v = vertices[face_indices[i]]
                vertex.addData3(v)
                normal.addData3(face_normal)
                color_writer.addData4(color)
                tris.addVertex(vtx_index)
                vtx_index += 1

        tris.closePrimitive()

        geom = Geom(vdata)
        geom.addPrimitive(tris)

        geom_node = GeomNode("fragment_geom")
        geom_node.addGeom(geom)
        self.body_np.attachNewNode(geom_node)

    def remove(self):
        """Remove fragment from world."""
        if self.body_np and not self.body_np.isEmpty():
            try:
                body_node = self.body_np.node()
                self.world.removeRigidBody(body_node)
                self.body_np.removeNode()
            except:
                # Already removed or invalid - ignore
                pass


class CurvedRoofPiece:
    """A curved roof piece for traditional Japanese-style architecture."""

    def __init__(
        self,
        world,
        render,
        position,
        size,
        mass,
        color,
        name,
        parent_building=None,
        curve_amount=0.5,
        tier=1,
        is_ghost=False,
    ):
        """Initialize a curved roof piece.

        Args:
            world: Bullet physics world
            render: Panda3D render node
            position: Vec3 world position (center)
            size: Vec3 base dimensions (width, depth, height)
            mass: Mass in kg
            color: Vec4 RGBA color
            name: Unique identifier
            parent_building: Optional reference to parent Building object
            curve_amount: How much upward curve at edges (0-1)
            tier: Roof tier number (affects size and position)
            is_ghost: If True, don't add to physics world (for preview)
        """
        self.world = world
        self.render = render
        self.position = position
        self.size = size
        self.mass = mass
        self.color = color
        self.name = name
        self.piece_type = "roof"
        self.parent_building = parent_building
        self.curve_amount = curve_amount
        self.tier = tier
        self.is_ghost = is_ghost

        # Physics properties
        self.health = 100.0
        self.max_health = 100.0
        self.is_destroyed = False
        self.is_foundation = False

        # Constraints
        self.constraints = []
        self.bullet_hole_count = 0
        self.max_bullet_holes = 20
        self.destruction_time = None
        self.destroyed_lifetime = 5.0

        # Create the curved roof
        self.body_np = self._create_curved_roof()

    def _create_curved_roof(self):
        """Create a curved roof with physics body."""
        # Use a flat box for physics (curved visual only)
        half_extents = Vec3(self.size.x / 2, self.size.y / 2, self.size.z / 2)
        shape = BulletBoxShape(half_extents)

        body_node = BulletRigidBodyNode(self.name)
        body_node.setMass(0)  # Static initially
        body_node.addShape(shape)
        body_node.setFriction(0.9)
        body_node.setRestitution(0.05)

        body_np = self.render.attachNewNode(body_node)
        body_np.setPos(self.position)

        # Only add to physics world if not a ghost
        if not self.is_ghost:
            self.world.attachRigidBody(body_node)

        # Create curved visual geometry
        self._create_curved_visual(body_np, half_extents)

        return body_np

    def _create_curved_visual(self, parent_np, half_extents):
        """Create curved roof visual geometry."""
        from panda3d.core import (
            GeomNode,
            GeomVertexFormat,
            GeomVertexData,
            GeomVertexWriter,
        )
        from panda3d.core import Geom, GeomTriangles

        vformat = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData(f"{self.name}_curved", vformat, Geom.UHStatic)

        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        color_writer = GeomVertexWriter(vdata, "color")

        # Create a curved surface using multiple segments
        segments_x = 12  # More segments for smoother curve
        segments_y = 8

        # Generate vertices for curved roof surface
        vertices = []
        for i in range(segments_y + 1):
            row = []
            for j in range(segments_x + 1):
                # Normalized coordinates (0 to 1)
                u = j / segments_x
                v = i / segments_y

                # Position in local space (-half to +half)
                x = (u - 0.5) * self.size.x
                y = (v - 0.5) * self.size.y

                # Calculate curve - edges curve upward
                # Use a parabola for the curve
                edge_dist = abs(u - 0.5) * 2  # 0 at center, 1 at edges
                z_curve = edge_dist * edge_dist * self.curve_amount * half_extents.z * 3

                # Also curve along Y axis slightly
                y_edge_dist = abs(v - 0.5) * 2
                z_curve += (
                    y_edge_dist * y_edge_dist * self.curve_amount * half_extents.z * 1.5
                )

                z = half_extents.z + z_curve

                row.append(Vec3(x, y, z))
            vertices.append(row)

        # Create triangles
        tris = GeomTriangles(Geom.UHStatic)
        vtx_index = 0

        for i in range(segments_y):
            for j in range(segments_x):
                # Get four corners of quad
                v0 = vertices[i][j]
                v1 = vertices[i][j + 1]
                v2 = vertices[i + 1][j + 1]
                v3 = vertices[i + 1][j]

                # Calculate normal for this quad
                edge1 = v1 - v0
                edge2 = v3 - v0
                quad_normal = edge1.cross(edge2)
                quad_normal.normalize()

                # Triangle 1: v0, v1, v2
                for v in [v0, v1, v2]:
                    vertex.addData3(v)
                    normal.addData3(quad_normal)
                    color_writer.addData4(self.color)
                    tris.addVertex(vtx_index)
                    vtx_index += 1

                # Triangle 2: v0, v2, v3
                for v in [v0, v2, v3]:
                    vertex.addData3(v)
                    normal.addData3(quad_normal)
                    color_writer.addData4(self.color)
                    tris.addVertex(vtx_index)
                    vtx_index += 1

        # Add bottom surface (flat) - should face downward (visible from below)
        bottom_z = -half_extents.z
        bottom_verts = [
            Vec3(-half_extents.x, -half_extents.y, bottom_z),
            Vec3(half_extents.x, -half_extents.y, bottom_z),
            Vec3(half_extents.x, half_extents.y, bottom_z),
            Vec3(-half_extents.x, half_extents.y, bottom_z),
        ]
        bottom_normal = Vec3(0, 0, -1)  # Facing downward

        # Bottom triangle 1 (counter-clockwise when viewed from below)
        for v in [bottom_verts[0], bottom_verts[3], bottom_verts[2]]:
            vertex.addData3(v)
            normal.addData3(bottom_normal)
            color_writer.addData4(self.color)
            tris.addVertex(vtx_index)
            vtx_index += 1

        # Bottom triangle 2 (counter-clockwise when viewed from below)
        for v in [bottom_verts[0], bottom_verts[2], bottom_verts[1]]:
            vertex.addData3(v)
            normal.addData3(bottom_normal)
            color_writer.addData4(self.color)
            tris.addVertex(vtx_index)
            vtx_index += 1

        # Add side walls connecting curved top to flat bottom (makes it 3D)
        # Front edge (Y-) - facing outward (negative Y direction)
        for j in range(segments_x):
            top_left = vertices[0][j]
            top_right = vertices[0][j + 1]
            bottom_left = Vec3(top_left.x, -half_extents.y, bottom_z)
            bottom_right = Vec3(top_right.x, -half_extents.y, bottom_z)

            # Calculate normal facing outward
            edge1 = top_right - top_left
            edge2 = bottom_left - top_left
            wall_normal = edge2.cross(edge1)  # Reversed cross product order
            wall_normal.normalize()

            # Triangle 1 (counter-clockwise from outside)
            for v in [top_left, bottom_left, bottom_right]:
                vertex.addData3(v)
                normal.addData3(wall_normal)
                color_writer.addData4(self.color)
                tris.addVertex(vtx_index)
                vtx_index += 1

            # Triangle 2
            for v in [top_left, bottom_right, top_right]:
                vertex.addData3(v)
                normal.addData3(wall_normal)
                color_writer.addData4(self.color)
                tris.addVertex(vtx_index)
                vtx_index += 1

        # Back edge (Y+) - facing outward (positive Y direction)
        for j in range(segments_x):
            top_left = vertices[segments_y][j]
            top_right = vertices[segments_y][j + 1]
            bottom_left = Vec3(top_left.x, half_extents.y, bottom_z)
            bottom_right = Vec3(top_right.x, half_extents.y, bottom_z)

            # Calculate normal facing outward
            edge1 = top_right - top_left
            edge2 = bottom_left - top_left
            wall_normal = edge1.cross(edge2)  # Normal cross product order
            wall_normal.normalize()

            # Triangle 1 (counter-clockwise from outside)
            for v in [top_left, top_right, bottom_right]:
                vertex.addData3(v)
                normal.addData3(wall_normal)
                color_writer.addData4(self.color)
                tris.addVertex(vtx_index)
                vtx_index += 1

            # Triangle 2
            for v in [top_left, bottom_right, bottom_left]:
                vertex.addData3(v)
                normal.addData3(wall_normal)
                color_writer.addData4(self.color)
                tris.addVertex(vtx_index)
                vtx_index += 1

        # Left edge (X-) - facing outward (negative X direction)
        for i in range(segments_y):
            top_front = vertices[i][0]
            top_back = vertices[i + 1][0]
            bottom_front = Vec3(-half_extents.x, top_front.y, bottom_z)
            bottom_back = Vec3(-half_extents.x, top_back.y, bottom_z)

            # Calculate normal facing outward
            edge1 = top_back - top_front
            edge2 = bottom_front - top_front
            wall_normal = edge1.cross(edge2)  # Reversed cross product order
            wall_normal.normalize()

            # Triangle 1 (counter-clockwise from outside)
            for v in [top_front, top_back, bottom_back]:
                vertex.addData3(v)
                normal.addData3(wall_normal)
                color_writer.addData4(self.color)
                tris.addVertex(vtx_index)
                vtx_index += 1

            # Triangle 2
            for v in [top_front, bottom_back, bottom_front]:
                vertex.addData3(v)
                normal.addData3(wall_normal)
                color_writer.addData4(self.color)
                tris.addVertex(vtx_index)
                vtx_index += 1

        # Right edge (X+) - facing outward (positive X direction)
        for i in range(segments_y):
            top_front = vertices[i][segments_x]
            top_back = vertices[i + 1][segments_x]
            bottom_front = Vec3(half_extents.x, top_front.y, bottom_z)
            bottom_back = Vec3(half_extents.x, top_back.y, bottom_z)

            # Calculate normal facing outward
            edge1 = top_back - top_front
            edge2 = bottom_front - top_front
            wall_normal = edge2.cross(edge1)  # Normal cross product order
            wall_normal.normalize()

            # Triangle 1 (counter-clockwise from outside)
            for v in [top_front, bottom_front, bottom_back]:
                vertex.addData3(v)
                normal.addData3(wall_normal)
                color_writer.addData4(self.color)
                tris.addVertex(vtx_index)
                vtx_index += 1

            # Triangle 2
            for v in [top_front, bottom_back, top_back]:
                vertex.addData3(v)
                normal.addData3(wall_normal)
                color_writer.addData4(self.color)
                tris.addVertex(vtx_index)
                vtx_index += 1

        tris.closePrimitive()

        geom = Geom(vdata)
        geom.addPrimitive(tris)

        geom_node = GeomNode(f"{self.name}_geom")
        geom_node.addGeom(geom)
        parent_np.attachNewNode(geom_node)

    def add_constraint(self, other_piece, constraint):
        """Add a constraint connecting this piece to another."""
        self.constraints.append({"piece": other_piece, "constraint": constraint})

    def remove_from_world(self):
        """Remove this piece from the world."""
        for constraint_info in self.constraints:
            try:
                self.world.removeConstraint(constraint_info["constraint"])
            except:
                pass

        if self.body_np and not self.body_np.isEmpty():
            try:
                body_node = self.body_np.node()
                self.world.removeRigidBody(body_node)
                self.body_np.removeNode()
            except:
                pass

    def is_stable(self, checked_pieces=None):
        """Check if this piece has a path to a foundation.

        Args:
            checked_pieces: Set of already checked pieces (for recursion)

        Returns:
            bool: True if piece is connected to foundation
        """
        if checked_pieces is None:
            checked_pieces = set()

        # Avoid infinite recursion
        if self in checked_pieces:
            return False

        checked_pieces.add(self)

        # Foundation is always stable
        if self.is_foundation:
            return True

        # Destroyed pieces are not stable
        if self.is_destroyed:
            return False

        # Check if any connected piece is stable
        for constraint_info in self.constraints:
            try:
                other_piece = constraint_info.get("piece")
                if (
                    other_piece
                    and hasattr(other_piece, "is_destroyed")
                    and not other_piece.is_destroyed
                ):
                    if hasattr(other_piece, "is_stable") and other_piece.is_stable(
                        checked_pieces
                    ):
                        return True
            except Exception as e:
                # Skip this constraint if there's any issue
                print(f"Warning: Error checking stability for {self.name}: {e}")
                continue

        return False

    def destroy(self, create_fragments=False, create_chunks=False, impact_pos=None):
        """Destroy this curved roof piece.

        Args:
            create_fragments: Unused for curved roofs
            create_chunks: Unused for curved roofs
            impact_pos: Unused for curved roofs

        Returns:
            list: Empty list (curved roofs don't create debris)
        """
        if self.is_destroyed:
            return []

        self.is_destroyed = True

        # Remove all constraints safely
        for constraint_info in self.constraints:
            try:
                constraint = constraint_info["constraint"]
                if constraint:
                    self.world.removeConstraint(constraint)
            except Exception as e:
                print(f"Warning: Error removing constraint from {self.name}: {e}")
                pass

        # Remove from world safely
        if self.body_np and not self.body_np.isEmpty():
            try:
                body_node = self.body_np.node()
                if body_node:
                    self.world.removeRigidBody(body_node)
            except Exception as e:
                print(f"Warning: Error removing rigid body from {self.name}: {e}")
                pass

            try:
                self.body_np.removeNode()
            except Exception as e:
                print(f"Warning: Error removing node from {self.name}: {e}")
                pass

        print(f"Curved roof piece {self.name} destroyed!")
        return []

    def take_damage(
        self, amount, create_fragments=True, create_chunks=True, impact_pos=None
    ):
        """Apply damage to this piece.

        Args:
            amount: Damage amount (0-100)
            create_fragments: If True, create debris when destroyed (not supported for curved roofs)
            create_chunks: If True, create destructible chunks when destroyed (not supported for curved roofs)
            impact_pos: Vec3 world position where damage was applied

        Returns:
            bool: True if piece was destroyed
        """
        if self.is_destroyed or self.is_foundation:
            return False

        self.health -= amount

        if self.health <= 0:
            # Use destroy method for cleanup
            self.destroy(create_fragments, create_chunks, impact_pos)
            return True

        return False


class BuildingPiece:
    """A single piece of a building (wall, floor, roof, etc.)."""

    def __init__(
        self,
        world,
        render,
        position,
        size,
        mass,
        color,
        name,
        piece_type="wall",
        parent_building=None,
    ):
        """Initialize a building piece.

        Args:
            world: Bullet physics world
            render: Panda3D render node
            position: Vec3 world position
            size: Vec3 dimensions (width, depth, height)
            mass: Mass in kg
            color: Vec4 RGBA color
            name: Unique identifier
            piece_type: Type of piece (wall, floor, roof, foundation)
            parent_building: Optional reference to parent Building object
        """
        self.world = world
        self.render = render
        self.position = position
        self.size = size
        self.mass = mass
        self.color = color
        self.name = name
        self.piece_type = piece_type
        self.parent_building = parent_building

        # Physics properties
        self.health = 100.0
        self.max_health = 100.0
        self.is_destroyed = False
        self.is_foundation = piece_type == "foundation"

        # Constraints connecting this piece to others
        self.constraints = []

        # Track bullet holes to limit accumulation
        self.bullet_hole_count = 0
        self.max_bullet_holes = 20  # Limit to prevent too many geometry nodes

        # Lifetime tracking for destroyed pieces
        self.destruction_time = None
        self.destroyed_lifetime = 5.0  # Destroyed pieces disappear after 5 seconds

        # Create the physical piece
        self.body_np = self._create_physics_body()

    def _create_physics_body(self):
        """Create the physics body and visual geometry.

        Returns:
            NodePath of the created piece
        """
        # Create physics shape (box)
        half_extents = Vec3(self.size.x / 2, self.size.y / 2, self.size.z / 2)
        shape = BulletBoxShape(half_extents)

        # Create rigid body node
        body_node = BulletRigidBodyNode(self.name)
        # All building pieces start as static (kinematic) - mass 0
        body_node.setMass(0)
        body_node.addShape(shape)

        # Set physics properties
        body_node.setFriction(0.9)
        body_node.setRestitution(0.05)  # Very low bounciness for building materials
        body_node.setLinearDamping(0.8)  # High damping to resist movement
        body_node.setAngularDamping(0.9)  # High rotational damping to resist rotation

        # Create NodePath and attach to scene
        body_np = self.render.attachNewNode(body_node)
        body_np.setPos(self.position)

        # Add to physics world
        self.world.attachRigidBody(body_node)

        # Create visual geometry
        self._create_visual_geometry(body_np, half_extents)

        return body_np

    def _create_visual_geometry(self, parent_np, half_extents):
        """Create visual mesh for the piece.

        Args:
            parent_np: Parent NodePath to attach to
            half_extents: Vec3 half-extents of the box
        """
        # Create vertex data
        vformat = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData(f"{self.name}_vdata", vformat, Geom.UHStatic)

        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        color_writer = GeomVertexWriter(vdata, "color")

        # Define box vertices (8 corners)
        s = half_extents
        vertices = [
            Vec3(-s.x, -s.y, -s.z),
            Vec3(s.x, -s.y, -s.z),
            Vec3(s.x, s.y, -s.z),
            Vec3(-s.x, s.y, -s.z),  # bottom
            Vec3(-s.x, -s.y, s.z),
            Vec3(s.x, -s.y, s.z),
            Vec3(s.x, s.y, s.z),
            Vec3(-s.x, s.y, s.z),  # top
        ]

        # Define faces with normals (counter-clockwise winding from outside)
        faces = [
            ([3, 2, 1, 0], Vec3(0, 0, -1)),  # bottom (reversed)
            ([4, 5, 6, 7], Vec3(0, 0, 1)),  # top
            ([1, 5, 4, 0], Vec3(0, -1, 0)),  # front (reversed)
            ([3, 7, 6, 2], Vec3(0, 1, 0)),  # back (reversed)
            ([4, 7, 3, 0], Vec3(-1, 0, 0)),  # left (reversed)
            ([2, 6, 5, 1], Vec3(1, 0, 0)),  # right (reversed)
        ]

        # Build geometry
        tris = GeomTriangles(Geom.UHStatic)
        vtx_index = 0

        for face_indices, face_normal in faces:
            # Two triangles per face
            for i in [0, 1, 2]:
                v = vertices[face_indices[i]]
                vertex.addData3(v)
                normal.addData3(face_normal)
                color_writer.addData4(self.color)
                tris.addVertex(vtx_index)
                vtx_index += 1

            for i in [0, 2, 3]:
                v = vertices[face_indices[i]]
                vertex.addData3(v)
                normal.addData3(face_normal)
                color_writer.addData4(self.color)
                tris.addVertex(vtx_index)
                vtx_index += 1

        tris.closePrimitive()

        # Create geometry
        geom = Geom(vdata)
        geom.addPrimitive(tris)

        # Create node and attach
        geom_node = GeomNode(f"{self.name}_geom")
        geom_node.addGeom(geom)
        parent_np.attachNewNode(geom_node)

    def add_constraint(self, other_piece, constraint):
        """Add a constraint connecting this piece to another.

        Args:
            other_piece: The BuildingPiece this is connected to
            constraint: The BulletConstraint object
        """
        self.constraints.append({"piece": other_piece, "constraint": constraint})

    def add_opening(self, opening_type, local_center, opening_size, color=None):
        """Add a visual opening (door/window) to the piece.

        Creates a colored quad on the surface of the piece to represent an opening.
        Note: This is visual only - doesn't affect physics collision.

        Args:
            opening_type: "door" or "window"
            local_center: Vec3 position in local coordinates (relative to piece center)
            opening_size: Vec3(width, depth, height) of the opening
            color: Vec4 color for the opening (default: dark for doors, light blue for windows)
        """
        from panda3d.core import (
            GeomNode,
            GeomVertexFormat,
            GeomVertexData,
            GeomVertexWriter,
        )
        from panda3d.core import Geom, GeomTriangles

        # Default colors
        if color is None:
            if opening_type == "door":
                color = Vec4(0.2, 0.15, 0.1, 1.0)  # Dark brown
            else:  # window
                color = Vec4(0.6, 0.8, 0.9, 0.7)  # Light blue (semi-transparent)

        # Create geometry for opening
        vformat = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData(f"{opening_type}_opening", vformat, Geom.UHStatic)

        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        color_writer = GeomVertexWriter(vdata, "color")

        # Determine which face the opening is on based on local position
        half_size = self.size / 2

        # Find closest face
        distances = {
            "x+": abs(local_center.x - half_size.x),
            "x-": abs(local_center.x + half_size.x),
            "y+": abs(local_center.y - half_size.y),
            "y-": abs(local_center.y + half_size.y),
            "z+": abs(local_center.z - half_size.z),
            "z-": abs(local_center.z + half_size.z),
        }

        closest_face = min(distances, key=distances.get)

        # Create a quad on the detected face
        offset = 0.02  # Slight offset to prevent z-fighting
        half_opening = opening_size / 2

        # Generate quad vertices based on which face
        if closest_face == "x+":
            x = half_size.x + offset
            vertices = [
                Vec3(
                    x, local_center.y - half_opening.y, local_center.z - half_opening.z
                ),
                Vec3(
                    x, local_center.y + half_opening.y, local_center.z - half_opening.z
                ),
                Vec3(
                    x, local_center.y + half_opening.y, local_center.z + half_opening.z
                ),
                Vec3(
                    x, local_center.y - half_opening.y, local_center.z + half_opening.z
                ),
            ]
            face_normal = Vec3(1, 0, 0)
        elif closest_face == "x-":
            x = -half_size.x - offset
            vertices = [
                Vec3(
                    x, local_center.y + half_opening.y, local_center.z - half_opening.z
                ),
                Vec3(
                    x, local_center.y - half_opening.y, local_center.z - half_opening.z
                ),
                Vec3(
                    x, local_center.y - half_opening.y, local_center.z + half_opening.z
                ),
                Vec3(
                    x, local_center.y + half_opening.y, local_center.z + half_opening.z
                ),
            ]
            face_normal = Vec3(-1, 0, 0)
        elif closest_face == "y+":
            y = half_size.y + offset
            vertices = [
                Vec3(
                    local_center.x + half_opening.x, y, local_center.z - half_opening.z
                ),
                Vec3(
                    local_center.x - half_opening.x, y, local_center.z - half_opening.z
                ),
                Vec3(
                    local_center.x - half_opening.x, y, local_center.z + half_opening.z
                ),
                Vec3(
                    local_center.x + half_opening.x, y, local_center.z + half_opening.z
                ),
            ]
            face_normal = Vec3(0, 1, 0)
        elif closest_face == "y-":
            y = -half_size.y - offset
            vertices = [
                Vec3(
                    local_center.x - half_opening.x, y, local_center.z - half_opening.z
                ),
                Vec3(
                    local_center.x + half_opening.x, y, local_center.z - half_opening.z
                ),
                Vec3(
                    local_center.x + half_opening.x, y, local_center.z + half_opening.z
                ),
                Vec3(
                    local_center.x - half_opening.x, y, local_center.z + half_opening.z
                ),
            ]
            face_normal = Vec3(0, -1, 0)
        elif closest_face == "z+":
            z = half_size.z + offset
            vertices = [
                Vec3(
                    local_center.x - half_opening.x, local_center.y - half_opening.y, z
                ),
                Vec3(
                    local_center.x + half_opening.x, local_center.y - half_opening.y, z
                ),
                Vec3(
                    local_center.x + half_opening.x, local_center.y + half_opening.y, z
                ),
                Vec3(
                    local_center.x - half_opening.x, local_center.y + half_opening.y, z
                ),
            ]
            face_normal = Vec3(0, 0, 1)
        else:  # z-
            z = -half_size.z - offset
            vertices = [
                Vec3(
                    local_center.x + half_opening.x, local_center.y - half_opening.y, z
                ),
                Vec3(
                    local_center.x - half_opening.x, local_center.y - half_opening.y, z
                ),
                Vec3(
                    local_center.x - half_opening.x, local_center.y + half_opening.y, z
                ),
                Vec3(
                    local_center.x + half_opening.x, local_center.y + half_opening.y, z
                ),
            ]
            face_normal = Vec3(0, 0, -1)

        # Add vertices for two triangles (quad)
        tris = GeomTriangles(Geom.UHStatic)

        # Triangle 1: 0, 1, 2
        for i in [0, 1, 2]:
            vertex.addData3(vertices[i])
            normal.addData3(face_normal)
            color_writer.addData4(color)
            tris.addVertex(i)

        # Triangle 2: 0, 2, 3
        for i in [0, 2, 3]:
            vertex.addData3(vertices[i])
            normal.addData3(face_normal)
            color_writer.addData4(color)
            tris.addVertex(3 + (i if i == 0 else i - 1))

        tris.closePrimitive()

        # Create geometry
        geom = Geom(vdata)
        geom.addPrimitive(tris)

        # Create node and attach to the piece
        geom_node = GeomNode(f"{opening_type}_{id(self)}")
        geom_node.addGeom(geom)
        opening_np = self.body_np.attachNewNode(geom_node)

        # Enable transparency for windows
        if opening_type == "window":
            from panda3d.core import TransparencyAttrib

            opening_np.setTransparency(TransparencyAttrib.MAlpha)

    def _apply_color_to_geometry(self, new_color):
        """Apply a new color to all vertices in the piece's geometry.

        Args:
            new_color: Vec4 RGBA color to apply
        """
        # Find the GeomNode child
        geom_node_path = None
        for child in self.body_np.getChildren():
            if isinstance(child.node(), GeomNode):
                geom_node_path = child
                break

        if not geom_node_path:
            return

        geom_node = geom_node_path.node()

        # Update all geoms in the node
        for i in range(geom_node.getNumGeoms()):
            geom = geom_node.modifyGeom(i)
            vdata = geom.modifyVertexData()

            # Make vertex data writable
            if vdata.getUsageHint() == Geom.UHStatic:
                # Create a modifiable copy
                new_vdata = GeomVertexData(vdata)
                new_vdata.setUsageHint(Geom.UHDynamic)
                geom.setVertexData(new_vdata)
                vdata = new_vdata

            # Update color data
            color_writer = GeomVertexWriter(vdata, "color")
            num_vertices = vdata.getNumRows()

            for v in range(num_vertices):
                color_writer.setRow(v)
                color_writer.setData4(new_color)

    def add_bullet_hole(self, world_impact_pos):
        """Add a black bullet hole mark at the impact position.

        Args:
            world_impact_pos: Vec3 world position where bullet hit
        """
        # Limit number of bullet holes to prevent performance issues
        if self.bullet_hole_count >= self.max_bullet_holes:
            return

        self.bullet_hole_count += 1

        # Convert world position to local position
        local_pos = self.body_np.getRelativePoint(self.render, world_impact_pos)

        # Create a small black sphere as a bullet hole mark
        from panda3d.core import (
            GeomNode,
            GeomVertexFormat,
            GeomVertexData,
            GeomVertexWriter,
        )
        from panda3d.core import Geom, GeomTriangles

        bullet_hole_size = 0.15  # Small hole

        # Create a simple black quad as the bullet hole
        vformat = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData("bullet_hole", vformat, Geom.UHStatic)

        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        color_writer = GeomVertexWriter(vdata, "color")

        # Determine which face was hit based on local position
        half_size = self.size / 2

        # Find closest face
        distances = {
            "x+": abs(local_pos.x - half_size.x),
            "x-": abs(local_pos.x + half_size.x),
            "y+": abs(local_pos.y - half_size.y),
            "y-": abs(local_pos.y + half_size.y),
            "z+": abs(local_pos.z - half_size.z),
            "z-": abs(local_pos.z + half_size.z),
        }

        closest_face = min(distances, key=distances.get)

        # Create a small quad on the hit face
        black = Vec4(0.1, 0.1, 0.1, 1.0)  # Dark gray/black
        offset = 0.01  # Slight offset to prevent z-fighting

        # Generate quad vertices based on which face was hit
        # All quads use CCW winding when viewed from outside (from the normal direction)
        if closest_face == "x+":
            x = half_size.x + offset
            vertices = [
                Vec3(x, local_pos.y - bullet_hole_size, local_pos.z - bullet_hole_size),
                Vec3(x, local_pos.y + bullet_hole_size, local_pos.z - bullet_hole_size),
                Vec3(x, local_pos.y + bullet_hole_size, local_pos.z + bullet_hole_size),
                Vec3(x, local_pos.y - bullet_hole_size, local_pos.z + bullet_hole_size),
            ]
            face_normal = Vec3(1, 0, 0)
        elif closest_face == "x-":
            x = -half_size.x - offset
            vertices = [
                Vec3(x, local_pos.y + bullet_hole_size, local_pos.z - bullet_hole_size),
                Vec3(x, local_pos.y - bullet_hole_size, local_pos.z - bullet_hole_size),
                Vec3(x, local_pos.y - bullet_hole_size, local_pos.z + bullet_hole_size),
                Vec3(x, local_pos.y + bullet_hole_size, local_pos.z + bullet_hole_size),
            ]
            face_normal = Vec3(-1, 0, 0)
        elif closest_face == "y+":
            y = half_size.y + offset
            vertices = [
                Vec3(local_pos.x + bullet_hole_size, y, local_pos.z - bullet_hole_size),
                Vec3(local_pos.x - bullet_hole_size, y, local_pos.z - bullet_hole_size),
                Vec3(local_pos.x - bullet_hole_size, y, local_pos.z + bullet_hole_size),
                Vec3(local_pos.x + bullet_hole_size, y, local_pos.z + bullet_hole_size),
            ]
            face_normal = Vec3(0, 1, 0)
        elif closest_face == "y-":
            y = -half_size.y - offset
            vertices = [
                Vec3(local_pos.x - bullet_hole_size, y, local_pos.z - bullet_hole_size),
                Vec3(local_pos.x + bullet_hole_size, y, local_pos.z - bullet_hole_size),
                Vec3(local_pos.x + bullet_hole_size, y, local_pos.z + bullet_hole_size),
                Vec3(local_pos.x - bullet_hole_size, y, local_pos.z + bullet_hole_size),
            ]
            face_normal = Vec3(0, -1, 0)
        elif closest_face == "z+":
            z = half_size.z + offset
            vertices = [
                Vec3(local_pos.x - bullet_hole_size, local_pos.y - bullet_hole_size, z),
                Vec3(local_pos.x + bullet_hole_size, local_pos.y - bullet_hole_size, z),
                Vec3(local_pos.x + bullet_hole_size, local_pos.y + bullet_hole_size, z),
                Vec3(local_pos.x - bullet_hole_size, local_pos.y + bullet_hole_size, z),
            ]
            face_normal = Vec3(0, 0, 1)
        else:  # z-
            z = -half_size.z - offset
            vertices = [
                Vec3(local_pos.x + bullet_hole_size, local_pos.y - bullet_hole_size, z),
                Vec3(local_pos.x - bullet_hole_size, local_pos.y - bullet_hole_size, z),
                Vec3(local_pos.x - bullet_hole_size, local_pos.y + bullet_hole_size, z),
                Vec3(local_pos.x + bullet_hole_size, local_pos.y + bullet_hole_size, z),
            ]
            face_normal = Vec3(0, 0, -1)

        # Add vertices for two triangles (quad)
        tris = GeomTriangles(Geom.UHStatic)

        # Triangle 1: 0, 1, 2
        for i in [0, 1, 2]:
            vertex.addData3(vertices[i])
            normal.addData3(face_normal)
            color_writer.addData4(black)
            tris.addVertex(i)

        # Triangle 2: 0, 2, 3
        for i in [0, 2, 3]:
            vertex.addData3(vertices[i])
            normal.addData3(face_normal)
            color_writer.addData4(black)
            tris.addVertex(3 + (i if i == 0 else i - 1))

        tris.closePrimitive()

        # Create geometry
        geom = Geom(vdata)
        geom.addPrimitive(tris)

        # Create node and attach to the piece
        geom_node = GeomNode(f"bullet_hole_{id(self)}")
        geom_node.addGeom(geom)
        self.body_np.attachNewNode(geom_node)

    def take_damage(
        self, amount, create_fragments=True, create_chunks=True, impact_pos=None
    ):
        """Apply damage to this piece.

        Args:
            amount: Damage amount (0-100)
            create_fragments: If True, create debris when destroyed
            create_chunks: If True, create destructible chunks when destroyed
            impact_pos: Vec3 world position where damage was applied (for break lines)

        Returns:
            bool: True if piece was destroyed
        """
        if self.is_destroyed or self.is_foundation:
            return False

        # Add bullet hole mark at impact position
        # TODO: Re-enable bullet hole marks when the bullet hole system is ready/fixed.
        # if impact_pos:
        #     self.add_bullet_hole(impact_pos)

        self.health -= amount

        # Update color to show damage (reduce saturation)
        health_ratio = max(0.0, self.health / self.max_health)
        self._update_damage_color(health_ratio)

        if self.health <= 0:
            # Destroy the piece (it becomes dynamic and falls)
            chunks = self.destroy(
                create_fragments=create_fragments,
                create_chunks=create_chunks,
                impact_pos=impact_pos,
            )
            return True

            # # Store fragment debris in parent building's fragments list
            # if fragments and self.parent_building:
            #     current_time = time.time()
            #     for fragment in fragments:
            #         # Set creation time for lifetime tracking
            #         fragment.creation_time = current_time
            #         self.parent_building.fragments.append(fragment)
            # elif fragments:
            #     # If no parent building, store in class-level list to prevent GC
            #     if not hasattr(BuildingPiece, '_orphan_fragments'):
            #         BuildingPiece._orphan_fragments = []
            #     current_time = time.time()
            #     for fragment in fragments:
            #         fragment.creation_time = current_time
            #         BuildingPiece._orphan_fragments.append(fragment)

        return False

    def _update_damage_color(self, health_ratio):
        """Update the visual color of the piece based on health.

        Reduces saturation as health decreases, making the piece appear more gray/desaturated.

        Args:
            health_ratio: Health ratio from 0.0 (dead) to 1.0 (full health)
        """
        # Convert RGB to grayscale (perceived brightness)
        gray = 0.299 * self.color.x + 0.587 * self.color.y + 0.114 * self.color.z

        # Interpolate between original color (healthy) and grayscale (damaged)
        # At full health: use original color
        # At zero health: use mostly grayscale with slight hint of original color
        saturation = 0.2 + (0.8 * health_ratio)  # Range from 0.2 to 1.0

        new_color = Vec4(
            gray + (self.color.x - gray) * saturation,
            gray + (self.color.y - gray) * saturation,
            gray + (self.color.z - gray) * saturation,
            self.color.w,
        )

        # Update the geometry colors
        self._apply_color_to_geometry(new_color)

    def destroy(self, create_fragments=True, create_chunks=True, impact_pos=None):
        """Destroy this piece and remove all constraints.

        Args:
            create_fragments: If True, create debris fragments
            create_chunks: If True, create destructible chunks
            impact_pos: Unused, kept for compatibility
        """
        if self.is_destroyed:
            return []

        self.is_destroyed = True

        # Remove all constraints FIRST (before creating debris)
        for constraint_info in self.constraints:
            constraint = constraint_info["constraint"]
            self.world.removeConstraint(constraint)

        # Chunks should only break into fragments, not more chunks (to prevent infinite subdivision)
        if self.piece_type == "chunk":
            create_chunks = False

        # Create both fragments and chunks (while node still exists to get position/velocity)
        fragments = []
        chunks = []

        if create_fragments:
            fragments = self._create_fragments()

        if create_chunks:
            chunks = self._create_chunks(impact_pos=impact_pos)

        # NOW remove the original piece from the physics world and scene
        body_node = self.body_np.node()
        self.world.removeRigidBody(body_node)
        self.body_np.removeNode()

        print(f"Building piece {self.name} destroyed and replaced with debris!")

        # Return both fragments and chunks
        return fragments + chunks

    def _create_fragments(self):
        """Create debris fragments from this piece.

        Returns:
            List of Fragment objects
        """
        fragments = []
        num_fragments = random.randint(4, 8)  # 4-8 fragments

        # Get current position and velocity
        piece_pos = self.body_np.getPos()
        piece_node = self.body_np.node()
        piece_velocity = piece_node.getLinearVelocity()

        # Create fragments scattered around the piece
        for i in range(num_fragments):
            # Random size (smaller than the original piece)
            fragment_size = Vec3(
                random.uniform(0.3, 0.8),
                random.uniform(0.3, 0.8),
                random.uniform(0.3, 0.8),
            )

            # Random position around the piece
            offset = Vec3(
                random.uniform(-self.size.x / 2, self.size.x / 2),
                random.uniform(-self.size.y / 2, self.size.y / 2),
                random.uniform(-self.size.z / 2, self.size.z / 2),
            )
            fragment_pos = piece_pos + offset

            # Random impulse (outward from center)
            impulse_direction = (
                offset.normalized() if offset.length() > 0.1 else Vec3(0, 0, 1)
            )
            impulse_strength = random.uniform(5, 15)
            impulse = impulse_direction * impulse_strength

            # Add piece's current velocity to impulse
            if piece_velocity.length() > 0.1:
                impulse += piece_velocity * 0.5

            # Slightly darker color for fragments
            fragment_color = Vec4(
                self.color.x * 0.8,
                self.color.y * 0.8,
                self.color.z * 0.8,
                self.color.w,
            )

            # Create fragment
            fragment = Fragment(
                self.world,
                self.render,
                fragment_pos,
                fragment_size,
                fragment_color,
                impulse,
            )
            fragments.append(fragment)

        print(f"Created {len(fragments)} fragments")
        return fragments

    def _create_chunks(self, impact_pos=None):
        """Create chunks wall.

        Splits the wall into 2-4 larger physics-enabled chunks that fall realistically.
        Chunks are BuildingPiece objects, so they can also be damaged and break further.

        Args:
            impact_pos: Vec3 world position of impact (center of radial cracks)

        Returns:
            List of BuildingPiece objects (destructible chunks)
        """
        chunks = []

        # Determine how many chunks based on piece size
        # Larger pieces break into more chunks
        size_factor = (self.size.x + self.size.y + self.size.z) / 3
        if size_factor > 5:
            num_chunks = random.randint(3, 4)
        else:
            num_chunks = random.randint(2, 3)

        # Get current position and velocity
        piece_pos = self.body_np.getPos()
        piece_node = self.body_np.node()
        piece_velocity = piece_node.getLinearVelocity()

        # Determine dominant dimension (largest axis)
        if self.size.x >= self.size.y and self.size.x >= self.size.z:
            # Wall is wide (X-axis) - split horizontally
            split_axis = "x"
            chunk_width = self.size.x / num_chunks
            chunk_size_base = Vec3(chunk_width * 0.9, self.size.y, self.size.z)
            spacing = chunk_width
        elif self.size.y >= self.size.x and self.size.y >= self.size.z:
            # Wall is deep (Y-axis) - split along depth
            split_axis = "y"
            chunk_depth = self.size.y / num_chunks
            chunk_size_base = Vec3(self.size.x, chunk_depth * 0.9, self.size.z)
            spacing = chunk_depth
        else:
            # Wall is tall (Z-axis) - split vertically
            split_axis = "z"
            chunk_height = self.size.z / num_chunks
            chunk_size_base = Vec3(self.size.x, self.size.y, chunk_height * 0.9)
            spacing = chunk_height

        # Create chunks along the split axis
        for i in range(num_chunks):
            # Calculate position along split axis
            if split_axis == "x":
                offset_along_axis = -self.size.x / 2 + spacing * (i + 0.5)
                chunk_offset = Vec3(offset_along_axis, 0, 0)
            elif split_axis == "y":
                offset_along_axis = -self.size.y / 2 + spacing * (i + 0.5)
                chunk_offset = Vec3(0, offset_along_axis, 0)
            else:  # z
                offset_along_axis = -self.size.z / 2 + spacing * (i + 0.5)
                chunk_offset = Vec3(0, 0, offset_along_axis)

            chunk_pos = piece_pos + chunk_offset

            # Add slight random variation to chunk size
            chunk_size = Vec3(
                chunk_size_base.x * random.uniform(0.95, 1.0),
                chunk_size_base.y * random.uniform(0.95, 1.0),
                chunk_size_base.z * random.uniform(0.95, 1.0),
            )

            # Chunks have same color as original piece (slightly darker)
            chunk_color = Vec4(
                self.color.x * 0.95,
                self.color.y * 0.95,
                self.color.z * 0.95,
                self.color.w,
            )

            # Create chunk as a BuildingPiece (so it can be damaged)
            chunk_mass = 5.0  # Heavier than fragments
            chunk = BuildingPiece(
                self.world,
                self.render,
                chunk_pos,
                chunk_size,
                chunk_mass,
                chunk_color,
                f"{self.name}_chunk_{i}",
                piece_type=self.piece_type,
                parent_building=self.parent_building,
            )

            # Reduce health (chunks are weaker)
            chunk.health = self.max_health * 0.4
            chunk.max_health = chunk.health

            # Register chunk with parent building so it can be damaged
            if self.parent_building:
                self.parent_building.add_piece(chunk)

            # Apply outward impulse (perpendicular to split axis)
            if split_axis == "x":
                # Push chunks apart along Y and Z
                impulse_dir = Vec3(
                    random.uniform(-2, 2),
                    random.uniform(-5, 5),
                    random.uniform(-3, 3),
                )
            elif split_axis == "y":
                impulse_dir = Vec3(
                    random.uniform(-5, 5),
                    random.uniform(-2, 2),
                    random.uniform(-3, 3),
                )
            else:  # z
                impulse_dir = Vec3(
                    random.uniform(-5, 5),
                    random.uniform(-5, 5),
                    random.uniform(-2, 2),
                )

            impulse_strength = random.uniform(10, 20)
            impulse = impulse_dir.normalized() * impulse_strength

            # Add parent velocity
            if piece_velocity.length() > 0.1:
                impulse += piece_velocity * 0.7

            # Apply impulse to chunk
            chunk_node = chunk.body_np.node()
            chunk_node.applyCentralImpulse(impulse)

            # Add some random spin
            torque = Vec3(
                random.uniform(-10, 10),
                random.uniform(-10, 10),
                random.uniform(-10, 10),
            )
            chunk_node.applyTorqueImpulse(torque)

            chunks.append(chunk)

        print(f"Created {len(chunks)} destructible chunks along {split_axis}-axis")

        return chunks

    def remove_from_world(self):
        """Completely remove this piece from the world."""
        # Remove constraints
        for constraint_info in self.constraints:
            try:
                self.world.removeConstraint(constraint_info["constraint"])
            except:
                pass  # Already removed

        # Remove physics body
        if self.body_np and not self.body_np.isEmpty():
            try:
                body_node = self.body_np.node()
                self.world.removeRigidBody(body_node)
                # Remove from scene
                self.body_np.removeNode()
            except:
                pass  # Already removed or invalid

    def is_stable(self, checked_pieces=None):
        """Check if this piece has a path to a foundation.

        Args:
            checked_pieces: Set of already checked pieces (for recursion)

        Returns:
            bool: True if piece is connected to foundation
        """
        if checked_pieces is None:
            checked_pieces = set()

        # Avoid infinite recursion
        if self in checked_pieces:
            return False

        checked_pieces.add(self)

        # Foundation is always stable
        if self.is_foundation:
            return True

        # Chunks are exempt from stability checks (they're falling debris that can be damaged)
        if self.piece_type == "chunk":
            return True

        # Destroyed pieces are not stable
        if self.is_destroyed:
            return False

        # Check if any connected piece is stable
        for constraint_info in self.constraints:
            other_piece = constraint_info["piece"]
            if not other_piece.is_destroyed:
                if other_piece.is_stable(checked_pieces):
                    return True

        return False


class Building:
    """A building composed of multiple connected pieces."""

    def __init__(self, world, render, position, name="building"):
        """Initialize a building.

        Args:
            world: Bullet physics world
            render: Panda3D render node
            position: Vec3 base position
            name: Building identifier
        """
        self.world = world
        self.render = render
        self.position = position
        self.name = name
        self.pieces = []
        self.piece_map = {}  # name -> piece lookup
        self.fragments = []  # Debris fragments

    def add_piece(self, piece):
        """Add a piece to this building.

        Args:
            piece: BuildingPiece to add
        """
        self.pieces.append(piece)
        self.piece_map[piece.name] = piece
        # Set parent building reference if not already set
        if piece.parent_building is None:
            piece.parent_building = self

    def connect_pieces(self, piece1_name, piece2_name, breaking_threshold=50.0):
        """Create a constraint between two pieces.

        Args:
            piece1_name: Name of first piece
            piece2_name: Name of second piece
            breaking_threshold: Force required to break constraint
        """
        if piece1_name not in self.piece_map or piece2_name not in self.piece_map:
            print(
                f"Warning: Cannot connect {piece1_name} to {piece2_name} - piece not found"
            )
            return

        piece1 = self.piece_map[piece1_name]
        piece2 = self.piece_map[piece2_name]

        # Create a generic constraint (acts like a fixed joint)
        body1 = piece1.body_np.node()
        body2 = piece2.body_np.node()

        # Calculate frame transforms (identity for now - pieces connect at their centers)
        from panda3d.core import TransformState

        frame_a = TransformState.makeIdentity()
        frame_b = TransformState.makeIdentity()

        constraint = BulletGenericConstraint(body1, body2, frame_a, frame_b, True)

        # Lock all axes for a rigid connection
        constraint.setLinearLimit(0, 0, 0)  # No linear movement
        constraint.setLinearLimit(1, 0, 0)
        constraint.setLinearLimit(2, 0, 0)
        constraint.setAngularLimit(0, 0, 0)  # No rotation
        constraint.setAngularLimit(1, 0, 0)
        constraint.setAngularLimit(2, 0, 0)

        # Set breaking threshold
        constraint.setBreakingThreshold(breaking_threshold)

        # Add constraint to world
        self.world.attachConstraint(constraint)

        # Track constraint in both pieces
        piece1.add_constraint(piece2, constraint)
        piece2.add_constraint(piece1, constraint)

    def check_stability(self):
        """Check all pieces for stability and make unsupported ones dynamic."""
        unstable_pieces = []

        for piece in self.pieces:
            if not piece.is_destroyed and not piece.is_stable():
                unstable_pieces.append(piece)

        # Make unstable pieces dynamic so they fall
        for piece in unstable_pieces:
            print(f"Piece {piece.name} is unsupported and collapsing!")
            body_node = piece.body_np.node()
            body_node.setMass(piece.mass)  # Make it dynamic
            body_node.setActive(True, True)
            # Don't destroy them - let them fall naturally

    def damage_piece(
        self,
        piece_name,
        amount,
        create_fragments=False,
        create_chunks=True,
        impact_pos=None,
    ):
        """Apply damage to a specific piece.

        Args:
            piece_name: Name of piece to damage
            amount: Damage amount
            create_fragments: If True, create debris when destroyed
            create_chunks: Unused, kept for compatibility
            impact_pos: Unused, kept for compatibility

        Returns:
            bool: True if piece was destroyed
        """
        if piece_name not in self.piece_map:
            return False

        piece = self.piece_map[piece_name]

        # Apply damage (destroy() will be called internally if health reaches 0)
        destroyed = piece.take_damage(
            amount,
            create_fragments=create_fragments,
            create_chunks=create_chunks,
            impact_pos=impact_pos,
        )

        if destroyed:
            # Fragments are already stored in self.fragments by take_damage()
            # Check if other pieces are now unstable
            self.check_stability()

        return destroyed

    def get_piece_at_position(self, position, max_distance=2.0):
        """Find the closest piece to a position.

        Args:
            position: Vec3 world position
            max_distance: Maximum distance to consider

        Returns:
            BuildingPiece or None
        """
        closest_piece = None
        closest_dist = max_distance

        for piece in self.pieces:
            if piece.is_destroyed:
                continue

            piece_pos = piece.body_np.getPos()
            dist = (piece_pos - position).length()

            if dist < closest_dist:
                closest_dist = dist
                closest_piece = piece

        return closest_piece

    def update(self, dt, current_time):
        """Update building state and cleanup old debris.

        Args:
            dt: Delta time since last update
            current_time: Current game time in seconds
        """
        # Clean up old fragments
        fragments_to_remove = []

        for fragment in self.fragments:
            # Check if fragment has expired
            if hasattr(fragment, "lifetime") and hasattr(fragment, "creation_time"):
                if (
                    fragment.creation_time > 0
                    and (current_time - fragment.creation_time) > fragment.lifetime
                ):
                    fragments_to_remove.append(fragment)

        # Also enforce hard limit on total fragments (remove oldest if too many)
        max_fragments = 100  # Hard limit to prevent excessive accumulation
        if len(self.fragments) > max_fragments:
            # Sort by creation time and remove oldest
            sorted_fragments = sorted(
                [f for f in self.fragments if hasattr(f, "creation_time")],
                key=lambda f: f.creation_time,
            )
            excess_count = len(self.fragments) - max_fragments
            fragments_to_remove.extend(sorted_fragments[:excess_count])

        # Remove expired/excess fragments safely
        for fragment in fragments_to_remove:
            try:
                if hasattr(fragment, "remove"):
                    fragment.remove()
                if fragment in self.fragments:
                    self.fragments.remove(fragment)
            except Exception as e:
                print(f"Warning: Error removing fragment: {e}")
                # Still try to remove from list
                if fragment in self.fragments:
                    self.fragments.remove(fragment)

        # Clean up destroyed pieces that have exceeded their lifetime
        pieces_to_remove = []
        for piece in self.pieces:
            if piece.is_destroyed and piece.destruction_time is not None:
                time_since_destruction = current_time - piece.destruction_time
                if time_since_destruction > piece.destroyed_lifetime:
                    pieces_to_remove.append(piece)

        # Remove expired destroyed pieces
        for piece in pieces_to_remove:
            try:
                print(
                    f"Removing destroyed piece {piece.name} after {piece.destroyed_lifetime}s"
                )
                piece.remove_from_world()
                if piece in self.pieces:
                    self.pieces.remove(piece)
                if piece.name in self.piece_map:
                    del self.piece_map[piece.name]
            except Exception as e:
                print(f"Warning: Error removing destroyed piece {piece.name}: {e}")
                # Still try to remove from lists
                if piece in self.pieces:
                    self.pieces.remove(piece)
                if piece.name in self.piece_map:
                    del self.piece_map[piece.name]

    def cleanup_destroyed_pieces(self, age_threshold=5.0):
        """Remove destroyed pieces that have been falling for a while.

        Args:
            age_threshold: Time in seconds before removing
        """
        # For now, just remove all destroyed pieces
        # In a full implementation, you'd track destruction time
        pieces_to_remove = [p for p in self.pieces if p.is_destroyed]

        for piece in pieces_to_remove:
            piece.remove_from_world()
            self.pieces.remove(piece)
            del self.piece_map[piece.name]

    def destroy(self):
        """Completely destroy this building and remove all pieces."""
        # Remove all constraints first
        for piece in self.pieces:
            for constraint_data in piece.constraints:
                constraint = constraint_data["constraint"]
                if constraint:
                    self.world.removeConstraint(constraint)

        # Remove all pieces
        for piece in self.pieces:
            if not piece.is_destroyed:
                piece.remove_from_world()

        # Clear fragments
        for fragment in self.fragments:
            if hasattr(fragment, "remove"):
                fragment.remove()

        self.pieces.clear()
        self.piece_map.clear()
        self.fragments.clear()
