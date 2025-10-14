"""Building system with destructible physics-based structures."""

import random
from panda3d.core import Vec3, Vec4, NodePath
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
        vdata = GeomVertexData(f"fragment_vdata", vformat, Geom.UHStatic)

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
        body_node = self.body_np.node()
        self.world.removeRigidBody(body_node)
        self.body_np.removeNode()


class BuildingPiece:
    """A single piece of a building (wall, floor, roof, etc.)."""

    def __init__(self, world, render, position, size, mass, color, name, piece_type="wall", parent_building=None):
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
        body_node.setMass(self.mass if not self.is_foundation else 0)  # Foundation is static
        body_node.addShape(shape)

        # Set physics properties
        body_node.setFriction(0.8)
        body_node.setRestitution(0.1)  # Low bounciness for building materials
        body_node.setLinearDamping(0.3)  # Some air resistance
        body_node.setAngularDamping(0.5)  # Rotational damping

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

    def take_damage(self, amount, create_fragments=True, create_chunks=True):
        """Apply damage to this piece.

        Args:
            amount: Damage amount (0-100)
            create_fragments: If True, create debris when destroyed
            create_chunks: If True, break into chunks when destroyed

        Returns:
            bool: True if piece was destroyed
        """
        if self.is_destroyed or self.is_foundation:
            return False

        self.health -= amount

        # Update color to show damage (darker = more damaged)
        damage_factor = max(0.3, self.health / self.max_health)
        damaged_color = Vec4(
            self.color.x * damage_factor,
            self.color.y * damage_factor,
            self.color.z * damage_factor,
            self.color.w,
        )

        # Update visual color (would need to rebuild geometry or use shader)
        # For now, mark as damaged

        if self.health <= 0:
            self.destroy(create_fragments=create_fragments, create_chunks=create_chunks)
            return True

        return False

    def destroy(self, create_fragments=True, create_chunks=True):
        """Destroy this piece and remove all constraints.

        Args:
            create_fragments: If True, create debris fragments
            create_chunks: If True, break into larger chunks
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
            chunks = self._create_chunks()

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
            impulse_direction = offset.normalized() if offset.length() > 0.1 else Vec3(0, 0, 1)
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

    def _create_chunks(self):
        """Create larger chunks when wall breaks.

        Splits the wall into 2-4 larger physics-enabled chunks that fall realistically.
        Chunks are BuildingPiece objects, so they can also be damaged and break further.

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
            split_axis = 'x'
            chunk_width = self.size.x / num_chunks
            chunk_size_base = Vec3(chunk_width * 0.9, self.size.y, self.size.z)
            spacing = chunk_width
        elif self.size.y >= self.size.x and self.size.y >= self.size.z:
            # Wall is deep (Y-axis) - split along depth
            split_axis = 'y'
            chunk_depth = self.size.y / num_chunks
            chunk_size_base = Vec3(self.size.x, chunk_depth * 0.9, self.size.z)
            spacing = chunk_depth
        else:
            # Wall is tall (Z-axis) - split vertically
            split_axis = 'z'
            chunk_height = self.size.z / num_chunks
            chunk_size_base = Vec3(self.size.x, self.size.y, chunk_height * 0.9)
            spacing = chunk_height

        # Create chunks along the split axis
        for i in range(num_chunks):
            # Calculate position along split axis
            if split_axis == 'x':
                offset_along_axis = -self.size.x / 2 + spacing * (i + 0.5)
                chunk_offset = Vec3(offset_along_axis, 0, 0)
            elif split_axis == 'y':
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
                piece_type="chunk",
                parent_building=self.parent_building,
            )

            # Reduce health based on parent damage (chunks are weaker)
            chunk.health = self.max_health * 0.4  # Chunks have 40% health of original
            chunk.max_health = chunk.health

            # Register chunk with parent building so it can be damaged
            if self.parent_building:
                self.parent_building.add_piece(chunk)

            # Apply outward impulse (perpendicular to split axis)
            if split_axis == 'x':
                # Push chunks apart along Y and Z
                impulse_dir = Vec3(
                    random.uniform(-2, 2),
                    random.uniform(-5, 5),
                    random.uniform(-3, 3),
                )
            elif split_axis == 'y':
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

            # Apply impulse to the chunk
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
        body_node = self.body_np.node()
        self.world.removeRigidBody(body_node)

        # Remove from scene
        self.body_np.removeNode()

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
            print(f"Warning: Cannot connect {piece1_name} to {piece2_name} - piece not found")
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
        """Check all pieces for stability and destroy unsupported ones."""
        unstable_pieces = []

        for piece in self.pieces:
            if not piece.is_destroyed and not piece.is_stable():
                unstable_pieces.append(piece)

        # Destroy unstable pieces
        for piece in unstable_pieces:
            print(f"Piece {piece.name} is unsupported and collapsing!")
            piece.destroy()

    def damage_piece(self, piece_name, amount, create_fragments=True, create_chunks=True):
        """Apply damage to a specific piece.

        Args:
            piece_name: Name of piece to damage
            amount: Damage amount
            create_fragments: If True, create debris when destroyed
            create_chunks: If True, break into chunks when destroyed

        Returns:
            bool: True if piece was destroyed
        """
        if piece_name not in self.piece_map:
            return False

        piece = self.piece_map[piece_name]

        # Apply damage (destroy() will be called internally if health reaches 0)
        destroyed = piece.take_damage(amount, create_fragments=create_fragments, create_chunks=create_chunks)

        if destroyed:
            # Fragments and chunks are already created by destroy() method
            # Note: destroy() was already called by take_damage()

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


class SimpleBuilding(Building):
    """A simple building with walls and a roof."""

    def __init__(self, world, render, position, width=10, depth=10, height=8, name="simple_building"):
        """Create a simple building.

        Args:
            world: Bullet physics world
            render: Panda3D render node
            position: Vec3 base position
            width: Building width (X axis)
            depth: Building depth (Y axis)
            height: Building height (Z axis)
            name: Building identifier
        """
        super().__init__(world, render, position, name)

        # Colors
        wall_color = Vec4(0.8, 0.7, 0.6, 1.0)  # Tan/beige
        roof_color = Vec4(0.5, 0.3, 0.2, 1.0)  # Brown
        foundation_color = Vec4(0.6, 0.6, 0.6, 1.0)  # Gray

        wall_thickness = 0.5
        wall_height = height
        wall_mass = 20.0

        # Create foundation (static)
        foundation = BuildingPiece(
            world,
            render,
            position,
            Vec3(width, depth, 1.0),
            0,  # Mass 0 = static
            foundation_color,
            f"{name}_foundation",
            "foundation",
        )
        self.add_piece(foundation)

        # Create four walls
        # Front wall (negative Y)
        front_wall = BuildingPiece(
            world,
            render,
            position + Vec3(0, -depth / 2, wall_height / 2),
            Vec3(width, wall_thickness, wall_height),
            wall_mass,
            wall_color,
            f"{name}_wall_front",
            "wall",
        )
        self.add_piece(front_wall)

        # Back wall (positive Y)
        back_wall = BuildingPiece(
            world,
            render,
            position + Vec3(0, depth / 2, wall_height / 2),
            Vec3(width, wall_thickness, wall_height),
            wall_mass,
            wall_color,
            f"{name}_wall_back",
            "wall",
        )
        self.add_piece(back_wall)

        # Left wall (negative X)
        left_wall = BuildingPiece(
            world,
            render,
            position + Vec3(-width / 2, 0, wall_height / 2),
            Vec3(wall_thickness, depth, wall_height),
            wall_mass,
            wall_color,
            f"{name}_wall_left",
            "wall",
        )
        self.add_piece(left_wall)

        # Right wall (positive X)
        right_wall = BuildingPiece(
            world,
            render,
            position + Vec3(width / 2, 0, wall_height / 2),
            Vec3(wall_thickness, depth, wall_height),
            wall_mass,
            wall_color,
            f"{name}_wall_right",
            "wall",
        )
        self.add_piece(right_wall)

        # Create roof
        roof = BuildingPiece(
            world,
            render,
            position + Vec3(0, 0, wall_height + 0.5),
            Vec3(width + 1, depth + 1, 0.5),  # Slightly larger than walls
            wall_mass * 1.5,  # Heavier roof
            roof_color,
            f"{name}_roof",
            "roof",
        )
        self.add_piece(roof)

        # Connect everything with constraints
        # Connect walls to foundation
        self.connect_pieces(f"{name}_wall_front", f"{name}_foundation", breaking_threshold=100)
        self.connect_pieces(f"{name}_wall_back", f"{name}_foundation", breaking_threshold=100)
        self.connect_pieces(f"{name}_wall_left", f"{name}_foundation", breaking_threshold=100)
        self.connect_pieces(f"{name}_wall_right", f"{name}_foundation", breaking_threshold=100)

        # Connect walls to each other at corners
        self.connect_pieces(f"{name}_wall_front", f"{name}_wall_left", breaking_threshold=80)
        self.connect_pieces(f"{name}_wall_front", f"{name}_wall_right", breaking_threshold=80)
        self.connect_pieces(f"{name}_wall_back", f"{name}_wall_left", breaking_threshold=80)
        self.connect_pieces(f"{name}_wall_back", f"{name}_wall_right", breaking_threshold=80)

        # Connect roof to walls
        self.connect_pieces(f"{name}_roof", f"{name}_wall_front", breaking_threshold=60)
        self.connect_pieces(f"{name}_roof", f"{name}_wall_back", breaking_threshold=60)
        self.connect_pieces(f"{name}_roof", f"{name}_wall_left", breaking_threshold=60)
        self.connect_pieces(f"{name}_roof", f"{name}_wall_right", breaking_threshold=60)

        print(f"Created {name} with {len(self.pieces)} pieces and structural connections")
