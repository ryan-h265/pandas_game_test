"""Terrain generation and management."""

import noise
import numpy as np
from panda3d.core import (
    GeomVertexFormat, GeomVertexData, GeomVertexWriter,
    Geom, GeomTriangles, GeomNode, Vec3, Vec4
)
from panda3d.bullet import BulletRigidBodyNode, BulletTriangleMesh, BulletTriangleMeshShape

from config.settings import CHUNK_SIZE, FLAT_WORLD


class TerrainChunk:
    """Represents a single chunk of terrain."""

    def __init__(self, chunk_x, chunk_z, world, render, bullet_world):
        """Initialize a terrain chunk.

        Args:
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
            world: Reference to World instance
            render: Panda3D render node
            bullet_world: Bullet physics world
        """
        self.chunk_x = chunk_x
        self.chunk_z = chunk_z
        self.world = world
        self.render = render
        self.bullet_world = bullet_world

        self.size = CHUNK_SIZE
        self.world_x = chunk_x * self.size
        self.world_z = chunk_z * self.size

        self.height_data = None
        self.node_path = None
        self.physics_node = None

    def generate(self):
        """Generate the terrain mesh and collision."""
        self.height_data = self._generate_height_data()
        self._create_mesh()
        self._create_collision()

    def _generate_height_data(self):
        """Generate height data using Perlin noise.

        Returns:
            2D numpy array of height values
        """
        heights = np.zeros((self.size + 1, self.size + 1))

        # If flat world is enabled, return all zeros (flat at height 0)
        if FLAT_WORLD:
            return heights

        for x in range(self.size + 1):
            for z in range(self.size + 1):
                world_x = self.world_x + x
                world_z = self.world_z + z

                # Multi-octave noise for more natural terrain
                height = 0

                # Base terrain
                height += noise.pnoise2(
                    world_x * 0.01,
                    world_z * 0.01,
                    octaves=6,
                    persistence=0.5,
                    lacunarity=2.0,
                    repeatx=1024,
                    repeaty=1024,
                    base=0
                ) * 20

                # Hills
                height += noise.pnoise2(
                    world_x * 0.05,
                    world_z * 0.05,
                    octaves=4,
                    persistence=0.5,
                    lacunarity=2.0,
                    repeatx=1024,
                    repeaty=1024,
                    base=1
                ) * 5

                # Fine details
                height += noise.pnoise2(
                    world_x * 0.1,
                    world_z * 0.1,
                    octaves=2,
                    persistence=0.3,
                    lacunarity=2.0,
                    repeatx=1024,
                    repeaty=1024,
                    base=2
                ) * 2

                heights[x][z] = height

        return heights

    def _calculate_normal(self, x, z):
        """Calculate normal vector at a vertex by averaging adjacent face normals.

        Args:
            x: Local X coordinate
            z: Local Z coordinate

        Returns:
            Tuple of (nx, ny, nz) normal components
        """
        # Get height at current position
        h = self.height_data[x][z]

        # Calculate normal using adjacent vertices (if they exist)
        # Sample points around the vertex
        h_left = self.height_data[x - 1][z] if x > 0 else h
        h_right = self.height_data[x + 1][z] if x < self.size else h
        h_down = self.height_data[x][z - 1] if z > 0 else h
        h_up = self.height_data[x][z + 1] if z < self.size else h

        # Calculate normal using cross product of tangent vectors
        # Tangent in X direction
        tx = Vec3(2.0, 0, h_right - h_left)
        # Tangent in Z direction
        tz = Vec3(0, 2.0, h_up - h_down)

        # Normal is perpendicular to both tangents
        normal = tz.cross(tx)
        normal.normalize()

        return normal.x, normal.y, normal.z

    def _create_mesh(self):
        """Create the visual mesh for the terrain."""
        # Create vertex data format
        vformat = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData('terrain', vformat, Geom.UHStatic)
        vdata.setNumRows((self.size + 1) * (self.size + 1))

        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')

        # Create vertices
        for z in range(self.size + 1):
            for x in range(self.size + 1):
                world_x = self.world_x + x
                world_z = self.world_z + z
                height = self.height_data[x][z]

                vertex.addData3(world_x, world_z, height)

                # Calculate proper normal by averaging adjacent faces
                nx, ny, nz = self._calculate_normal(x, z)
                normal.addData3(nx, ny, nz)

                # Color based on height
                vertex_color = self._get_vertex_color(height)
                color.addData4(vertex_color)

        # Create triangles
        tris = GeomTriangles(Geom.UHStatic)

        for z in range(self.size):
            for x in range(self.size):
                # Calculate vertex indices
                v0 = z * (self.size + 1) + x
                v1 = v0 + 1
                v2 = v0 + (self.size + 1)
                v3 = v2 + 1

                # First triangle (counter-clockwise winding for front face)
                tris.addVertices(v0, v1, v2)
                # Second triangle (counter-clockwise winding for front face)
                tris.addVertices(v1, v3, v2)

        tris.closePrimitive()

        # Create geometry
        geom = Geom(vdata)
        geom.addPrimitive(tris)

        # Create node
        node = GeomNode('terrain_chunk')
        node.addGeom(geom)

        # Attach to render
        self.node_path = self.render.attachNewNode(node)

        # Enable two-sided rendering (render both front and back faces)
        self.node_path.setTwoSided(True)

        # Set collision mask so raycasting can detect it
        self.node_path.setCollideMask(1)

    def _get_vertex_color(self, height):
        """Get color based on terrain height.

        Args:
            height: Height value

        Returns:
            Vec4 color
        """
        if height < -2:
            # Deep water - dark blue
            return Vec4(0.1, 0.2, 0.5, 1.0)
        elif height < 0:
            # Shallow water - light blue
            return Vec4(0.2, 0.4, 0.7, 1.0)
        elif height < 2:
            # Beach - sandy
            return Vec4(0.8, 0.7, 0.5, 1.0)
        elif height < 10:
            # Grass - green
            return Vec4(0.2, 0.6, 0.2, 1.0)
        elif height < 15:
            # Hills - dark green
            return Vec4(0.15, 0.45, 0.15, 1.0)
        elif height < 20:
            # Mountain - gray
            return Vec4(0.5, 0.5, 0.5, 1.0)
        else:
            # Snow - white
            return Vec4(0.9, 0.9, 0.9, 1.0)

    def _create_collision(self):
        """Create physics collision mesh."""
        mesh = BulletTriangleMesh()

        for z in range(self.size):
            for x in range(self.size):
                world_x = self.world_x + x
                world_z = self.world_z + z

                # Get the four corners of this quad
                h00 = self.height_data[x][z]
                h10 = self.height_data[x + 1][z]
                h01 = self.height_data[x][z + 1]
                h11 = self.height_data[x + 1][z + 1]

                # Create two triangles
                v0 = Vec3(world_x, world_z, h00)
                v1 = Vec3(world_x + 1, world_z, h10)
                v2 = Vec3(world_x, world_z + 1, h01)
                v3 = Vec3(world_x + 1, world_z + 1, h11)

                mesh.addTriangle(v0, v2, v1)
                mesh.addTriangle(v1, v2, v3)

        shape = BulletTriangleMeshShape(mesh, dynamic=False)

        self.physics_node = BulletRigidBodyNode(f'terrain_collision_{self.chunk_x}_{self.chunk_z}')
        self.physics_node.addShape(shape)
        self.physics_node.setMass(0)  # Static

        physics_np = self.render.attachNewNode(self.physics_node)
        self.bullet_world.attachRigidBody(self.physics_node)

    def regenerate(self):
        """Regenerate mesh and collision after terrain modification."""
        # Remove old mesh and collision
        if self.node_path:
            self.node_path.removeNode()
        if self.physics_node:
            self.bullet_world.removeRigidBody(self.physics_node)

        # Regenerate
        self._create_mesh()
        self._create_collision()

    def remove(self):
        """Remove this chunk from the scene."""
        if self.node_path:
            self.node_path.removeNode()
        if self.physics_node:
            self.bullet_world.removeRigidBody(self.physics_node)


class Terrain:
    """Handles terrain generation and chunk management."""

    def __init__(self, render, bullet_world):
        """Initialize the terrain system.

        Args:
            render: Panda3D render node
            bullet_world: Bullet physics world
        """
        self.render = render
        self.bullet_world = bullet_world
        self.chunks = {}  # Dict of (chunk_x, chunk_z) -> TerrainChunk

    def generate_chunk(self, chunk_x, chunk_z):
        """Generate a terrain chunk at the given coordinates.

        Args:
            chunk_x: Chunk x coordinate
            chunk_z: Chunk z coordinate

        Returns:
            TerrainChunk instance
        """
        chunk_key = (chunk_x, chunk_z)

        if chunk_key not in self.chunks:
            chunk = TerrainChunk(chunk_x, chunk_z, self, self.render, self.bullet_world)
            chunk.generate()
            self.chunks[chunk_key] = chunk

        return self.chunks[chunk_key]

    def remove_chunk(self, chunk_x, chunk_z):
        """Remove a terrain chunk.

        Args:
            chunk_x: Chunk x coordinate
            chunk_z: Chunk z coordinate
        """
        chunk_key = (chunk_x, chunk_z)

        if chunk_key in self.chunks:
            self.chunks[chunk_key].remove()
            del self.chunks[chunk_key]

    def get_height_at(self, world_x, world_z):
        """Get the terrain height at a world position.

        Args:
            world_x: World X coordinate
            world_z: World Z coordinate

        Returns:
            Height value or None if chunk not loaded
        """
        chunk_x = int(world_x // CHUNK_SIZE)
        chunk_z = int(world_z // CHUNK_SIZE)
        chunk_key = (chunk_x, chunk_z)

        if chunk_key not in self.chunks:
            return None

        chunk = self.chunks[chunk_key]
        local_x = int(world_x - chunk.world_x)
        local_z = int(world_z - chunk.world_z)

        if 0 <= local_x <= CHUNK_SIZE and 0 <= local_z <= CHUNK_SIZE:
            return chunk.height_data[local_x][local_z]

        return None

    def update(self, camera_pos):
        """Update terrain (for dynamic loading/unloading).

        Args:
            camera_pos: Camera position for determining visible chunks
        """
        # This can be extended for dynamic chunk loading/unloading
        pass
