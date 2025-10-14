"""Building system with destructible physics-based structures."""

import random
import math
import time
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
        if self.body_np and not self.body_np.isEmpty():
            try:
                body_node = self.body_np.node()
                self.world.removeRigidBody(body_node)
                self.body_np.removeNode()
            except:
                # Already removed or invalid - ignore
                pass


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

    def take_damage(self, amount, create_fragments=True, create_chunks=False, impact_pos=None):
        """Apply damage to this piece.

        Args:
            amount: Damage amount (0-100)
            create_fragments: If True, create debris when destroyed
            create_chunks: Unused, kept for compatibility
            impact_pos: Unused, kept for compatibility

        Returns:
            bool: True if piece was destroyed
        """
        if self.is_destroyed or self.is_foundation:
            return False

        self.health -= amount

        # Update color to show damage (reduce saturation)
        health_ratio = max(0.0, self.health / self.max_health)
        self._update_damage_color(health_ratio)

        if self.health <= 0:
            # Destroy the piece (it becomes dynamic and falls)
            fragments = self.destroy(create_fragments=create_fragments)
            
            # Store fragment debris in parent building's fragments list
            if fragments and self.parent_building:
                current_time = time.time()
                for fragment in fragments:
                    # Set creation time for lifetime tracking
                    fragment.creation_time = current_time
                    self.parent_building.fragments.append(fragment)
            elif fragments:
                # If no parent building, store in class-level list to prevent GC
                if not hasattr(BuildingPiece, '_orphan_fragments'):
                    BuildingPiece._orphan_fragments = []
                current_time = time.time()
                for fragment in fragments:
                    fragment.creation_time = current_time
                    BuildingPiece._orphan_fragments.append(fragment)
            return True

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
            self.color.w
        )
        
        # Update the geometry colors
        self._apply_color_to_geometry(new_color)

    def destroy(self, create_fragments=True, create_chunks=False, impact_pos=None):
        """Destroy this piece and remove all constraints.

        Args:
            create_fragments: If True, create debris fragments
            create_chunks: Unused, kept for compatibility
            impact_pos: Unused, kept for compatibility
        """
        if self.is_destroyed:
            return []

        self.is_destroyed = True

        # Make the piece dynamic so it can fall
        body_node = self.body_np.node()
        body_node.setMass(self.mass)  # Restore the original mass
        body_node.setActive(True, True)  # Ensure it's active

        # Remove all constraints so piece can fall freely
        for constraint_info in self.constraints:
            constraint = constraint_info["constraint"]
            self.world.removeConstraint(constraint)

        # Create small debris fragments
        fragments = []
        if create_fragments:
            fragments = self._create_fragments()

        print(f"Building piece {self.name} destroyed!")
        
        # Return fragments for storage
        return fragments

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

    def _create_chunks(self, impact_pos=None):
        """Create chunks with radial fracture pattern from impact point on wall face.

        Creates irregular chunks radiating from the impact point across the 2D face,
        like a shattered window. Each chunk extends through the full depth of the wall.

        Args:
            impact_pos: Vec3 world position of impact (center of radial cracks)

        Returns:
            List of FaceChunk objects (chunks created from face fracture)
        """
        chunks = []

        # Get current position and velocity
        piece_pos = self.body_np.getPos()
        piece_node = self.body_np.node()
        piece_velocity = piece_node.getLinearVelocity()

        # Convert impact position to local coordinates
        if impact_pos:
            local_impact = impact_pos - piece_pos
        else:
            # Default to center if no impact position
            local_impact = Vec3(0, 0, 0)

        # Determine which face was hit and project impact onto that face's 2D plane
        # Also determine the 2D coordinate system for that face
        half_size = self.size / 2

        # Find which face the impact is closest to
        face_distances = {
            'x+': abs(local_impact.x - half_size.x),
            'x-': abs(local_impact.x + half_size.x),
            'y+': abs(local_impact.y - half_size.y),
            'y-': abs(local_impact.y + half_size.y),
            'z+': abs(local_impact.z - half_size.z),
            'z-': abs(local_impact.z + half_size.z),
        }

        hit_face = min(face_distances, key=face_distances.get)

        # Project impact onto face and get 2D coordinates
        if hit_face.startswith('x'):
            # Face perpendicular to X axis - use Y-Z plane
            face_normal = Vec3(1 if hit_face == 'x+' else -1, 0, 0)
            impact_2d = Vec3(local_impact.y, local_impact.z, 0)  # Y and Z coords
            face_width = self.size.y
            face_height = self.size.z
            depth_axis = 'x'
        elif hit_face.startswith('y'):
            # Face perpendicular to Y axis - use X-Z plane
            face_normal = Vec3(0, 1 if hit_face == 'y+' else -1, 0)
            impact_2d = Vec3(local_impact.x, local_impact.z, 0)  # X and Z coords
            face_width = self.size.x
            face_height = self.size.z
            depth_axis = 'y'
        else:  # z face
            # Face perpendicular to Z axis - use X-Y plane
            face_normal = Vec3(0, 0, 1 if hit_face == 'z+' else -1)
            impact_2d = Vec3(local_impact.x, local_impact.y, 0)  # X and Y coords
            face_width = self.size.x
            face_height = self.size.y
            depth_axis = 'z'

        # Generate radial crack pattern from impact point on the 2D face
        num_chunks = random.randint(3, 5)  # 3-5 chunks radiating from impact

        # Generate crack angles radiating from impact on the face
        crack_angles = []
        for i in range(num_chunks):
            # Distribute angles around impact point
            base_angle = (i / num_chunks) * 2 * math.pi
            # Add random variation
            angle_variation = random.uniform(-0.4, 0.4)
            crack_angles.append(base_angle + angle_variation)

        # Create chunks based on radial sectors on the face
        for i in range(num_chunks):
            # Calculate chunk's angular sector
            start_angle = crack_angles[i]
            end_angle = crack_angles[(i + 1) % num_chunks]

            # Chunk color (slightly darker)
            chunk_color = Vec4(
                self.color.x * 0.95,
                self.color.y * 0.95,
                self.color.z * 0.95,
                self.color.w,
            )

            # Create face chunk that extends through wall depth
            chunk_mass = 5.0
            chunk = FaceChunk(
                self.world,
                self.render,
                piece_pos,
                self.size,
                chunk_mass,
                chunk_color,
                f"{self.name}_chunk_{i}",
                parent_building=self.parent_building,
                hit_face=hit_face,
                depth_axis=depth_axis,
                impact_2d=impact_2d,
                face_width=face_width,
                face_height=face_height,
                start_angle=start_angle,
                end_angle=end_angle,
                chunk_index=i,
                total_chunks=num_chunks,
            )

            # Reduce health (chunks are weaker)
            chunk.health = self.max_health * 0.4
            chunk.max_health = chunk.health

            # Make chunk dynamic immediately (it's debris, not a building)
            chunk_body = chunk.body_np.node()
            chunk_body.setMass(chunk_mass)
            chunk_body.setActive(True, True)

            # Store chunk in parent building's fragments list (not pieces list)
            # Chunks are temporary debris, not structural pieces
            if self.parent_building:
                self.parent_building.fragments.append(chunk)

            # Apply outward impulse from impact point (in 3D space)
            chunk_center = chunk.body_np.getPos()
            direction_from_impact = chunk_center - (impact_pos if impact_pos else piece_pos)

            if direction_from_impact.length() > 0.1:
                direction_from_impact.normalize()
            else:
                # Fallback direction based on chunk angle
                mid_angle = start_angle + (end_angle - start_angle) / 2
                if depth_axis == 'x':
                    direction_from_impact = Vec3(face_normal.x, math.cos(mid_angle), math.sin(mid_angle))
                elif depth_axis == 'y':
                    direction_from_impact = Vec3(math.cos(mid_angle), face_normal.y, math.sin(mid_angle))
                else:
                    direction_from_impact = Vec3(math.cos(mid_angle), math.sin(mid_angle), face_normal.z)
                direction_from_impact.normalize()

            impulse_strength = random.uniform(15, 25)
            impulse = direction_from_impact * impulse_strength

            if piece_velocity.length() > 0.1:
                impulse += piece_velocity * 0.5

            # Apply physics
            chunk_node = chunk.body_np.node()
            chunk_node.applyCentralImpulse(impulse)
            torque = Vec3(
                random.uniform(-10, 10),
                random.uniform(-10, 10),
                random.uniform(-10, 10),
            )
            chunk_node.applyTorqueImpulse(torque)

            chunks.append(chunk)

        print(f"Created {len(chunks)} face chunks from impact at {impact_2d}")
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


class FaceChunk(BuildingPiece):
    """A wedge-shaped chunk on a wall face that extends through the full depth of the wall."""

    def __init__(self, world, render, position, size, mass, color, name, parent_building=None,
                 hit_face=None, depth_axis=None, impact_2d=None, face_width=None, face_height=None,
                 start_angle=0.0, end_angle=0.0, chunk_index=0, total_chunks=3):
        """Initialize a face chunk.

        Args:
            world: Bullet physics world
            render: Panda3D render node
            position: Vec3 world position
            size: Vec3 base dimensions of original piece
            mass: Mass in kg
            color: Vec4 RGBA color
            name: Unique identifier
            parent_building: Optional reference to parent Building object
            hit_face: String indicating hit face ('x+', 'x-', 'y+', 'y-', 'z+', 'z-')
            depth_axis: String indicating depth axis ('x', 'y', or 'z')
            impact_2d: Vec3 with X and Y being the 2D coords on the face plane (Z unused)
            face_width: Width of the face in 2D plane
            face_height: Height of the face in 2D plane
            start_angle: Starting angle of this wedge (radians)
            end_angle: Ending angle of this wedge (radians)
            chunk_index: Index of this chunk (0 to total_chunks-1)
            total_chunks: Total number of chunks created
        """
        self.hit_face = hit_face if hit_face else 'x+'
        self.depth_axis = depth_axis if depth_axis else 'x'
        self.impact_2d = impact_2d if impact_2d else Vec3(0, 0, 0)
        self.face_width = face_width if face_width else size.y
        self.face_height = face_height if face_height else size.z
        self.start_angle = start_angle
        self.end_angle = end_angle
        self.chunk_index = chunk_index
        self.total_chunks = total_chunks

        # Chunks have a limited lifetime (like fragments)
        self.creation_time = 0  # Will be set externally
        self.lifetime = 10.0  # Chunks disappear after 10 seconds

        # Call parent init (which creates the body and geometry)
        super().__init__(world, render, position, size, mass, color, name, "chunk", parent_building)

    def _create_physics_body(self):
        """Create the physics body with a convex hull shape matching the wedge geometry.

        Returns:
            NodePath of the created piece
        """
        from panda3d.bullet import BulletConvexHullShape

        # Get half extents
        half_extents = Vec3(self.size.x / 2, self.size.y / 2, self.size.z / 2)
        s = half_extents

        # Generate the wedge profile points (same as visual geometry)
        wedge_profile = self._get_wedge_profile_points(s)

        if not wedge_profile or len(wedge_profile) < 3:
            # Fallback to box shape if wedge generation fails
            return super()._create_physics_body()

        # Create convex hull shape from the wedge points
        shape = BulletConvexHullShape()

        # Add all vertices of the wedge to the convex hull
        for point in wedge_profile:
            shape.addPoint(point)

        # Create rigid body node
        body_node = BulletRigidBodyNode(self.name)
        body_node.setMass(0)  # Start as kinematic like other building pieces
        body_node.addShape(shape)

        # Set physics properties
        body_node.setFriction(0.9)
        body_node.setRestitution(0.05)
        body_node.setLinearDamping(0.8)
        body_node.setAngularDamping(0.9)

        # Create NodePath and attach to scene
        body_np = self.render.attachNewNode(body_node)
        body_np.setPos(self.position)

        # Add to physics world
        self.world.attachRigidBody(body_node)

        # Create visual geometry
        self._create_visual_geometry(body_np, half_extents)

        return body_np

    def _get_wedge_profile_points(self, half_extents):
        """Get all 3D vertices of the wedge for collision hull.

        Args:
            half_extents: Vec3 half extents

        Returns:
            List of Vec3 points forming the wedge shape
        """
        s = half_extents

        # Generate wedge geometry
        if self.depth_axis == 'x':
            return self._get_wedge_points_yz_plane(s)
        elif self.depth_axis == 'y':
            return self._get_wedge_points_xz_plane(s)
        else:  # z
            return self._get_wedge_points_xy_plane(s)

    def _get_wedge_points_xy_plane(self, s):
        """Get wedge vertices for X-Y plane (Z-axis walls)."""
        impact = self.impact_2d

        max_radius = math.sqrt(
            max(abs(impact.x - s.x), abs(impact.x + s.x))**2 +
            max(abs(impact.y - s.y), abs(impact.y + s.y))**2
        ) * 1.5

        # Generate crack lines (simplified, no jagged edges for collision)
        start_dir = Vec3(math.cos(self.start_angle), math.sin(self.start_angle), 0)
        start_outer = impact + start_dir * max_radius

        end_dir = Vec3(math.cos(self.end_angle), math.sin(self.end_angle), 0)
        end_outer = impact + end_dir * max_radius

        # Clip to bounds
        start_outer.x = max(-s.x, min(s.x, start_outer.x))
        start_outer.y = max(-s.y, min(s.y, start_outer.y))
        end_outer.x = max(-s.x, min(s.x, end_outer.x))
        end_outer.y = max(-s.y, min(s.y, end_outer.y))

        # Generate outer arc points
        outer_arc = self._generate_outer_arc_2d(impact, self.start_angle, self.end_angle, s.x, s.y)

        # Build 2D profile
        wedge_2d = [impact, start_outer] + outer_arc + [end_outer]

        # Extrude to 3D through depth
        front_z = s.z if self.hit_face == 'z+' else -s.z
        back_z = -s.z if self.hit_face == 'z+' else s.z

        points_3d = []
        for p in wedge_2d:
            points_3d.append(Vec3(p.x, p.y, front_z))
            points_3d.append(Vec3(p.x, p.y, back_z))

        return points_3d

    def _get_wedge_points_xz_plane(self, s):
        """Get wedge vertices for X-Z plane (Y-axis walls)."""
        impact = self.impact_2d

        max_radius = math.sqrt(
            max(abs(impact.x - s.x), abs(impact.x + s.x))**2 +
            max(abs(impact.y - s.z), abs(impact.y + s.z))**2
        ) * 1.5

        start_dir = Vec3(math.cos(self.start_angle), math.sin(self.start_angle), 0)
        start_outer = impact + start_dir * max_radius

        end_dir = Vec3(math.cos(self.end_angle), math.sin(self.end_angle), 0)
        end_outer = impact + end_dir * max_radius

        start_outer.x = max(-s.x, min(s.x, start_outer.x))
        start_outer.y = max(-s.z, min(s.z, start_outer.y))
        end_outer.x = max(-s.x, min(s.x, end_outer.x))
        end_outer.y = max(-s.z, min(s.z, end_outer.y))

        outer_arc = self._generate_outer_arc_2d(impact, self.start_angle, self.end_angle, s.x, s.z)

        wedge_2d = [impact, start_outer] + outer_arc + [end_outer]

        front_y = s.y if self.hit_face == 'y+' else -s.y
        back_y = -s.y if self.hit_face == 'y+' else s.y

        points_3d = []
        for p in wedge_2d:
            points_3d.append(Vec3(p.x, front_y, p.y))
            points_3d.append(Vec3(p.x, back_y, p.y))

        return points_3d

    def _get_wedge_points_yz_plane(self, s):
        """Get wedge vertices for Y-Z plane (X-axis walls)."""
        impact = self.impact_2d

        max_radius = math.sqrt(
            max(abs(impact.x - s.y), abs(impact.x + s.y))**2 +
            max(abs(impact.y - s.z), abs(impact.y + s.z))**2
        ) * 1.5

        start_dir = Vec3(math.cos(self.start_angle), math.sin(self.start_angle), 0)
        start_outer = impact + start_dir * max_radius

        end_dir = Vec3(math.cos(self.end_angle), math.sin(self.end_angle), 0)
        end_outer = impact + end_dir * max_radius

        start_outer.x = max(-s.y, min(s.y, start_outer.x))
        start_outer.y = max(-s.z, min(s.z, start_outer.y))
        end_outer.x = max(-s.y, min(s.y, end_outer.x))
        end_outer.y = max(-s.z, min(s.z, end_outer.y))

        outer_arc = self._generate_outer_arc_2d(impact, self.start_angle, self.end_angle, s.y, s.z)

        wedge_2d = [impact, start_outer] + outer_arc + [end_outer]

        front_x = s.x if self.hit_face == 'x+' else -s.x
        back_x = -s.x if self.hit_face == 'x+' else s.x

        points_3d = []
        for p in wedge_2d:
            points_3d.append(Vec3(front_x, p.x, p.y))
            points_3d.append(Vec3(back_x, p.x, p.y))

        return points_3d

    def _create_visual_geometry(self, parent_np, half_extents):
        """Create wedge-shaped visual mesh that extends through full wall depth.

        Args:
            parent_np: Parent NodePath to attach to
            half_extents: Vec3 half-extents of the base box
        """
        # Create vertex data
        vformat = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData(f"{self.name}_vdata", vformat, Geom.UHStatic)

        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        color_writer = GeomVertexWriter(vdata, "color")

        s = half_extents

        # Generate wedge geometry based on hit face and depth axis
        faces = self._generate_wedge_geometry(s)

        # Build all faces
        tris = GeomTriangles(Geom.UHStatic)
        vtx_index = 0

        for face_verts, face_normal in faces:
            # Triangulate face using fan triangulation from first vertex
            if len(face_verts) < 3:
                continue  # Skip degenerate faces

            # Simple fan triangulation - trust the face_normal provided
            for i in range(1, len(face_verts) - 1):
                # Create triangle with vertices in order
                for idx in [0, i, i + 1]:
                    v = face_verts[idx]
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

    def _generate_wedge_geometry(self, half_extents):
        """Generate wedge-shaped geometry that extends through full wall depth.

        Args:
            half_extents: Vec3 half extents

        Returns:
            List of (face_vertices, normal) tuples
        """
        s = half_extents

        # Generate wedge based on depth axis (which is perpendicular to the hit face)
        if self.depth_axis == 'x':
            # Wall perpendicular to X, wedge in Y-Z plane, extends through X
            return self._generate_wedge_yz_plane(s)
        elif self.depth_axis == 'y':
            # Wall perpendicular to Y, wedge in X-Z plane, extends through Y
            return self._generate_wedge_xz_plane(s)
        else:  # z
            # Wall perpendicular to Z, wedge in X-Y plane, extends through Z
            return self._generate_wedge_xy_plane(s)

    def _generate_jagged_crack_line(self, start_point, end_point, num_points=7):
        """Generate jagged points along a crack line.

        Args:
            start_point: Vec3 starting point (2D coords in face plane)
            end_point: Vec3 ending point (2D coords in face plane)
            num_points: Number of jagged points to generate

        Returns:
            List of Vec3 points forming jagged line (2D coords in face plane)
        """
        points = [start_point]

        for i in range(1, num_points - 1):
            # Interpolate along line
            t = i / (num_points - 1)
            base_point = start_point + (end_point - start_point) * t

            # Add random perpendicular offset (jagged variation)
            direction = end_point - start_point
            direction.normalize()

            # Create perpendicular vector in 2D
            perp = Vec3(-direction.y, direction.x, 0)
            perp.normalize()

            # Random offset along perpendicular
            offset_amount = random.uniform(-0.3, 0.3)
            jagged_point = base_point + perp * offset_amount

            points.append(jagged_point)

        points.append(end_point)
        return points

    def _generate_wedge_xy_plane(self, s):
        """Generate wedge in X-Y plane (for Z-axis walls) extending through Z depth.

        Args:
            s: Vec3 half_extents

        Returns:
            List of (face_vertices, normal) tuples
        """
        faces = []

        # Impact point in 2D face coordinates
        impact = self.impact_2d

        # Calculate max radius from impact to wall corners
        max_radius = math.sqrt(
            max(abs(impact.x - s.x), abs(impact.x + s.x))**2 +
            max(abs(impact.y - s.y), abs(impact.y + s.y))**2
        ) * 1.5

        # Generate radial crack lines with jagged edges
        start_dir = Vec3(math.cos(self.start_angle), math.sin(self.start_angle), 0)
        start_outer = impact + start_dir * max_radius

        end_dir = Vec3(math.cos(self.end_angle), math.sin(self.end_angle), 0)
        end_outer = impact + end_dir * max_radius

        # Generate jagged points along crack lines
        num_jagged = random.randint(5, 10)
        start_crack_points = self._generate_jagged_crack_line(impact, start_outer, num_jagged)
        end_crack_points = self._generate_jagged_crack_line(impact, end_outer, num_jagged)

        # Clip to wall boundaries
        start_crack_points = self._clip_points_to_bounds_2d(start_crack_points, s.x, s.y)
        end_crack_points = self._clip_points_to_bounds_2d(end_crack_points, s.x, s.y)

        # Generate arc points along outer edge between the two crack lines
        outer_arc_points = self._generate_outer_arc_2d(impact, self.start_angle, self.end_angle, s.x, s.y)

        # Build 2D wedge profile
        wedge_profile = []
        wedge_profile.extend(start_crack_points)
        wedge_profile.extend(outer_arc_points)
        wedge_profile.extend(reversed(end_crack_points))

        # Remove duplicates
        wedge_profile = self._remove_duplicate_points(wedge_profile)

        if len(wedge_profile) >= 3:
            # Front face (positive Z) - using face normal based on hit_face
            front_z = s.z if self.hit_face == 'z+' else -s.z
            back_z = -s.z if self.hit_face == 'z+' else s.z

            # For front face: keep wedge_profile order (CCW from front)
            front_face_verts = [Vec3(p.x, p.y, front_z) for p in wedge_profile]
            front_normal = Vec3(0, 0, 1) if self.hit_face == 'z+' else Vec3(0, 0, -1)
            faces.append((front_face_verts, front_normal))

            # Back face: reverse order so it's CCW when viewed from back (outside)
            back_face_verts = [Vec3(p.x, p.y, back_z) for p in reversed(wedge_profile)]
            back_normal = Vec3(0, 0, -1) if self.hit_face == 'z+' else Vec3(0, 0, 1)
            faces.append((back_face_verts, back_normal))

            # Side faces connecting front and back (extruding through depth)
            # For each edge on perimeter, create a quad face
            for i in range(len(wedge_profile)):
                j = (i + 1) % len(wedge_profile)
                p1 = wedge_profile[i]
                p2 = wedge_profile[j]

                # Create quad vertices - standard order
                v1 = Vec3(p1.x, p1.y, front_z)
                v2 = Vec3(p2.x, p2.y, front_z)
                v3 = Vec3(p2.x, p2.y, back_z)
                v4 = Vec3(p1.x, p1.y, back_z)
                
                # Calculate what normal this vertex order produces
                edge1 = v2 - v1
                edge2 = v4 - v1
                test_normal = edge1.cross(edge2)
                
                if test_normal.length() > 0.001:
                    test_normal.normalize()
                    
                    # Calculate quad center and direction from impact to center
                    quad_center = (v1 + v2 + v3 + v4) * 0.25
                    impact_center = Vec3(impact.x, impact.y, (front_z + back_z) * 0.5)
                    outward = quad_center - impact_center
                    
                    if outward.length() > 0.001:
                        outward.normalize()
                        
                        # If normal points outward (same direction as from impact to quad), use this order
                        if test_normal.dot(outward) > 0:
                            face_verts = [v1, v2, v3, v4]
                            face_normal = test_normal
                        else:
                            # Reverse to make outward facing
                            face_verts = [v4, v3, v2, v1]
                            edge1_rev = face_verts[1] - face_verts[0]
                            edge2_rev = face_verts[3] - face_verts[0]
                            face_normal = edge1_rev.cross(edge2_rev)
                            if face_normal.length() > 0.001:
                                face_normal.normalize()
                        
                        faces.append((face_verts, face_normal))

        return faces

    def _generate_wedge_xz_plane(self, s):
        """Generate wedge in X-Z plane (for Y-axis walls) extending through Y depth.

        Args:
            s: Vec3 half_extents

        Returns:
            List of (face_vertices, normal) tuples
        """
        faces = []

        impact = self.impact_2d

        max_radius = math.sqrt(
            max(abs(impact.x - s.x), abs(impact.x + s.x))**2 +
            max(abs(impact.y - s.z), abs(impact.y + s.z))**2  # y maps to z in 2D coords
        ) * 1.5

        # Generate crack lines
        start_dir = Vec3(math.cos(self.start_angle), math.sin(self.start_angle), 0)
        start_outer = impact + start_dir * max_radius

        end_dir = Vec3(math.cos(self.end_angle), math.sin(self.end_angle), 0)
        end_outer = impact + end_dir * max_radius

        num_jagged = random.randint(5, 10)
        start_crack_points = self._generate_jagged_crack_line(impact, start_outer, num_jagged)
        end_crack_points = self._generate_jagged_crack_line(impact, end_outer, num_jagged)

        start_crack_points = self._clip_points_to_bounds_2d(start_crack_points, s.x, s.z)
        end_crack_points = self._clip_points_to_bounds_2d(end_crack_points, s.x, s.z)

        outer_arc_points = self._generate_outer_arc_2d(impact, self.start_angle, self.end_angle, s.x, s.z)

        wedge_profile = []
        wedge_profile.extend(start_crack_points)
        wedge_profile.extend(outer_arc_points)
        wedge_profile.extend(reversed(end_crack_points))

        wedge_profile = self._remove_duplicate_points(wedge_profile)

        if len(wedge_profile) >= 3:
            # Front face (hit face side)
            front_y = s.y if self.hit_face == 'y+' else -s.y
            back_y = -s.y if self.hit_face == 'y+' else s.y

            # Map 2D coords to 3D: x stays x, y (2D) becomes z (3D)
            front_face_verts = [Vec3(p.x, front_y, p.y) for p in wedge_profile]
            front_normal = Vec3(0, 1, 0) if self.hit_face == 'y+' else Vec3(0, -1, 0)
            faces.append((front_face_verts, front_normal))

            # Back face
            back_face_verts = [Vec3(p.x, back_y, p.y) for p in reversed(wedge_profile)]
            back_normal = Vec3(0, -1, 0) if self.hit_face == 'y+' else Vec3(0, 1, 0)
            faces.append((back_face_verts, back_normal))

            # Side faces
            for i in range(len(wedge_profile)):
                j = (i + 1) % len(wedge_profile)
                p1 = wedge_profile[i]
                p2 = wedge_profile[j]

                # Create quad vertices (2D: x->X, y->Z)
                v1 = Vec3(p1.x, front_y, p1.y)
                v2 = Vec3(p2.x, front_y, p2.y)
                v3 = Vec3(p2.x, back_y, p2.y)
                v4 = Vec3(p1.x, back_y, p1.y)
                
                # Test normal from vertex order
                edge1 = v2 - v1
                edge2 = v4 - v1
                test_normal = edge1.cross(edge2)
                
                if test_normal.length() > 0.001:
                    test_normal.normalize()
                    
                    # Calculate quad center and direction from impact to center
                    quad_center = (v1 + v2 + v3 + v4) * 0.25
                    impact_center = Vec3(impact.x, (front_y + back_y) * 0.5, impact.y)
                    outward = quad_center - impact_center
                    
                    if outward.length() > 0.001:
                        outward.normalize()
                        
                        if test_normal.dot(outward) > 0:
                            face_verts = [v1, v2, v3, v4]
                            face_normal = test_normal
                        else:
                            face_verts = [v4, v3, v2, v1]
                            edge1_rev = face_verts[1] - face_verts[0]
                            edge2_rev = face_verts[3] - face_verts[0]
                            face_normal = edge1_rev.cross(edge2_rev)
                            if face_normal.length() > 0.001:
                                face_normal.normalize()
                        
                        faces.append((face_verts, face_normal))

        return faces

    def _generate_wedge_yz_plane(self, s):
        """Generate wedge in Y-Z plane (for X-axis walls) extending through X depth.

        Args:
            s: Vec3 half_extents

        Returns:
            List of (face_vertices, normal) tuples
        """
        faces = []

        impact = self.impact_2d

        max_radius = math.sqrt(
            max(abs(impact.x - s.y), abs(impact.x + s.y))**2 +  # x (2D) maps to y (3D)
            max(abs(impact.y - s.z), abs(impact.y + s.z))**2   # y (2D) maps to z (3D)
        ) * 1.5

        # Generate crack lines
        start_dir = Vec3(math.cos(self.start_angle), math.sin(self.start_angle), 0)
        start_outer = impact + start_dir * max_radius

        end_dir = Vec3(math.cos(self.end_angle), math.sin(self.end_angle), 0)
        end_outer = impact + end_dir * max_radius

        num_jagged = random.randint(5, 10)
        start_crack_points = self._generate_jagged_crack_line(impact, start_outer, num_jagged)
        end_crack_points = self._generate_jagged_crack_line(impact, end_outer, num_jagged)

        start_crack_points = self._clip_points_to_bounds_2d(start_crack_points, s.y, s.z)
        end_crack_points = self._clip_points_to_bounds_2d(end_crack_points, s.y, s.z)

        outer_arc_points = self._generate_outer_arc_2d(impact, self.start_angle, self.end_angle, s.y, s.z)

        wedge_profile = []
        wedge_profile.extend(start_crack_points)
        wedge_profile.extend(outer_arc_points)
        wedge_profile.extend(reversed(end_crack_points))

        wedge_profile = self._remove_duplicate_points(wedge_profile)

        if len(wedge_profile) >= 3:
            # Front face (hit face side)
            front_x = s.x if self.hit_face == 'x+' else -s.x
            back_x = -s.x if self.hit_face == 'x+' else s.x

            # Map 2D coords to 3D: x (2D) becomes y (3D), y (2D) becomes z (3D)
            front_face_verts = [Vec3(front_x, p.x, p.y) for p in wedge_profile]
            front_normal = Vec3(1, 0, 0) if self.hit_face == 'x+' else Vec3(-1, 0, 0)
            faces.append((front_face_verts, front_normal))

            # Back face
            back_face_verts = [Vec3(back_x, p.x, p.y) for p in reversed(wedge_profile)]
            back_normal = Vec3(-1, 0, 0) if self.hit_face == 'x+' else Vec3(1, 0, 0)
            faces.append((back_face_verts, back_normal))

            # Side faces
            for i in range(len(wedge_profile)):
                j = (i + 1) % len(wedge_profile)
                p1 = wedge_profile[i]
                p2 = wedge_profile[j]

                # Create quad vertices (2D: x->Y, y->Z)
                v1 = Vec3(front_x, p1.x, p1.y)
                v2 = Vec3(front_x, p2.x, p2.y)
                v3 = Vec3(back_x, p2.x, p2.y)
                v4 = Vec3(back_x, p1.x, p1.y)
                
                # Test normal from vertex order
                edge1 = v2 - v1
                edge2 = v4 - v1
                test_normal = edge1.cross(edge2)
                
                if test_normal.length() > 0.001:
                    test_normal.normalize()
                    
                    # Calculate quad center and direction from impact to center
                    quad_center = (v1 + v2 + v3 + v4) * 0.25
                    impact_center = Vec3((front_x + back_x) * 0.5, impact.x, impact.y)
                    outward = quad_center - impact_center
                    
                    if outward.length() > 0.001:
                        outward.normalize()
                        
                        if test_normal.dot(outward) > 0:
                            face_verts = [v1, v2, v3, v4]
                            face_normal = test_normal
                        else:
                            face_verts = [v4, v3, v2, v1]
                            edge1_rev = face_verts[1] - face_verts[0]
                            edge2_rev = face_verts[3] - face_verts[0]
                            face_normal = edge1_rev.cross(edge2_rev)
                            if face_normal.length() > 0.001:
                                face_normal.normalize()
                        
                        faces.append((face_verts, face_normal))

        return faces

    def _generate_outer_arc_2d(self, impact, start_angle, end_angle, width_bound, height_bound):
        """Generate points along outer edge of wedge in 2D plane.

        Args:
            impact: Vec3 impact point (2D coords)
            start_angle: Start angle in radians
            end_angle: End angle in radians
            width_bound: Half width of face (X bound)
            height_bound: Half height of face (Y bound)

        Returns:
            List of Vec3 points along outer arc (2D coords)
        """
        points = []
        num_arc_points = 8

        # Determine angle span
        angle_span = end_angle - start_angle
        if angle_span < 0:
            angle_span += 2 * math.pi

        for i in range(num_arc_points + 1):
            t = i / num_arc_points
            angle = start_angle + angle_span * t

            # Project ray to wall boundary
            direction = Vec3(math.cos(angle), math.sin(angle), 0)

            # Find intersection with 2D bounds
            point = self._ray_to_bounds_2d(impact, direction, width_bound, height_bound)
            if point:
                points.append(point)

        return points

    def _ray_to_bounds_2d(self, origin, direction, width_bound, height_bound):
        """Cast ray from origin in direction until it hits 2D rectangular bounds.

        Args:
            origin: Vec3 origin point (2D coords)
            direction: Vec3 direction vector (2D)
            width_bound: Half width bound
            height_bound: Half height bound

        Returns:
            Vec3 intersection point (2D coords) or None
        """
        t_values = []

        if abs(direction.x) > 0.0001:
            t_values.append((width_bound - origin.x) / direction.x)
            t_values.append((-width_bound - origin.x) / direction.x)

        if abs(direction.y) > 0.0001:
            t_values.append((height_bound - origin.y) / direction.y)
            t_values.append((-height_bound - origin.y) / direction.y)

        # Find smallest positive t
        valid_t = [t for t in t_values if t > 0.001]
        if valid_t:
            t = min(valid_t)
            point = origin + direction * t
            # Clamp to bounds
            point.x = max(-width_bound, min(width_bound, point.x))
            point.y = max(-height_bound, min(height_bound, point.y))
            return Vec3(point.x, point.y, 0)
        return None

    def _clip_points_to_bounds_2d(self, points, width_bound, height_bound):
        """Clip points to stay within 2D rectangular bounds.

        Args:
            points: List of Vec3 points (2D coords)
            width_bound: Half width bound
            height_bound: Half height bound

        Returns:
            List of clipped Vec3 points
        """
        clipped = []
        for p in points:
            clipped_p = Vec3(
                max(-width_bound, min(width_bound, p.x)),
                max(-height_bound, min(height_bound, p.y)),
                0
            )
            clipped.append(clipped_p)
        return clipped

    def _remove_duplicate_points(self, points, tolerance=0.01):
        """Remove duplicate points from list while preserving order.

        Args:
            points: List of Vec3 points
            tolerance: Distance threshold for considering points duplicate

        Returns:
            List of unique Vec3 points
        """
        unique = []
        for p in points:
            is_duplicate = False
            for existing in unique:
                if (p - existing).length() < tolerance:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique.append(p)
        return unique


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

    def damage_piece(self, piece_name, amount, create_fragments=True, create_chunks=False, impact_pos=None):
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
        destroyed = piece.take_damage(amount, create_fragments=create_fragments)

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
            if hasattr(fragment, 'lifetime') and hasattr(fragment, 'creation_time'):
                if fragment.creation_time > 0 and (current_time - fragment.creation_time) > fragment.lifetime:
                    fragments_to_remove.append(fragment)
        
        # Remove expired fragments
        for fragment in fragments_to_remove:
            if hasattr(fragment, 'remove'):
                fragment.remove()
            self.fragments.remove(fragment)

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
                constraint = constraint_data['constraint']
                if constraint:
                    self.world.removeConstraint(constraint)

        # Remove all pieces
        for piece in self.pieces:
            if not piece.is_destroyed:
                piece.remove_from_world()

        # Clear fragments
        for fragment in self.fragments:
            if hasattr(fragment, 'remove'):
                fragment.remove()

        self.pieces.clear()
        self.piece_map.clear()
        self.fragments.clear()


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
        wall_mass = 20.0  # Reasonable mass for when pieces become dynamic

        # Corner overlap amount - walls will extend this much into corners
        # to create seamless joints
        corner_overlap = wall_thickness

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

        # Create four walls with extended lengths to overlap at corners
        # Front and back walls extend the full width plus corner overlaps
        # Left and right walls fit between them with no extension

        # Front wall (negative Y) - extends full width + overlaps on both sides
        front_wall = BuildingPiece(
            world,
            render,
            position + Vec3(0, -depth / 2, wall_height / 2),
            Vec3(width + (2 * corner_overlap), wall_thickness, wall_height),
            wall_mass,
            wall_color,
            f"{name}_wall_front",
            "wall",
        )
        self.add_piece(front_wall)

        # Back wall (positive Y) - extends full width + overlaps on both sides
        back_wall = BuildingPiece(
            world,
            render,
            position + Vec3(0, depth / 2, wall_height / 2),
            Vec3(width + (2 * corner_overlap), wall_thickness, wall_height),
            wall_mass,
            wall_color,
            f"{name}_wall_back",
            "wall",
        )
        self.add_piece(back_wall)

        # Left wall (negative X) - fits between front and back (no extension needed)
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

        # Right wall (positive X) - fits between front and back (no extension needed)
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

        # Connect everything - since pieces are kinematic, constraints just track connections
        # They don't need high breaking thresholds since there's no physics forces on them

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
