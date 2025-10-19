"""Terrain generation and management."""

import numpy as np
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
from panda3d.bullet import (
    BulletRigidBodyNode,
    BulletTriangleMesh,
    BulletTriangleMeshShape,
)

from testgame.config.settings import (
    CHUNK_SIZE,
    WORLD_TYPE,
    TERRAIN_RESOLUTION,
    MODIFIABLE_TERRAIN,
)
import testgame.config.settings
from testgame.engine.terrain_generation import TerrainGenerator


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

        self.size = CHUNK_SIZE  # World size of chunk
        # Use minimal resolution for non-modifiable flat terrain (just 2x2 = 2 triangles)
        # Otherwise use configured resolution for detailed terrain
        # self.resolution = (
        #     1 if (not MODIFIABLE_TERRAIN and FLAT_WORLD) else TERRAIN_RESOLUTION
        # )

        self.resolution = (
            1 if (not MODIFIABLE_TERRAIN and WORLD_TYPE == "flat") else TERRAIN_RESOLUTION
        )

        self.world_x = chunk_x * self.size
        self.world_z = chunk_z * self.size

        self.height_data = None
        self.node_path = None
        self.physics_node = None
        self.wireframe_node = None

        # Initialize terrain generator
        self.terrain_generator = TerrainGenerator(self.size, self.resolution)

        # Generate a unique color for this chunk based on its coordinates
        self.debug_color = self._generate_chunk_color()

    def generate(self):
        """Generate the terrain mesh and collision."""
        self.height_data = self._generate_height_data()
        self._create_mesh()
        self._create_collision()

    def _generate_chunk_color(self):
        """Generate a unique color for this chunk based on its coordinates.

        Returns:
            Vec4 color
        """
        import random

        # Use chunk coordinates as seed for consistent colors
        seed = (self.chunk_x * 73856093) ^ (self.chunk_z * 19349663)
        rng = random.Random(seed)
        r = rng.uniform(0.4, 1.0)
        g = rng.uniform(0.4, 1.0)
        b = rng.uniform(0.4, 1.0)
        return Vec4(r, g, b, 1.0)

    def _generate_height_data(self):
        """Generate height data using the terrain generator.

        Returns:
            2D numpy array of height values
        """
        return self.terrain_generator.generate_height_data(
            self.chunk_x, self.chunk_z, self.world_x, self.world_z
        )

    def generate_donut_terrain(self, outer_radius=200, inner_radius=80, height=50):
        """Generate donut-shaped terrain for this chunk.

        Args:
            outer_radius: Outer radius of the donut
            inner_radius: Inner radius (hole size)  
            height: Height of the donut rim

        Returns:
            2D numpy array of height values
        """
        return self.terrain_generator.generate_donut_terrain(
            self.chunk_x, self.chunk_z, self.world_x, self.world_z,
            outer_radius, inner_radius, height
        )

    def _calculate_normal(self, x, z):
        """Calculate normal vector at a vertex by averaging adjacent face normals.

        Args:
            x: Local X coordinate (index in height_data array)
            z: Local Z coordinate (index in height_data array)

        Returns:
            Tuple of (nx, ny, nz) normal components
        """
        # Get height at current position
        h = self.height_data[x][z]

        # Calculate spacing for proper normal calculation
        spacing = self.size / self.resolution

        # Calculate normal using adjacent vertices (if they exist)
        # Sample points around the vertex
        h_left = self.height_data[x - 1][z] if x > 0 else h
        h_right = self.height_data[x + 1][z] if x < self.resolution else h
        h_down = self.height_data[x][z - 1] if z > 0 else h
        h_up = self.height_data[x][z + 1] if z < self.resolution else h

        # Calculate normal using cross product of tangent vectors
        # Tangent in X direction (scaled by spacing)
        tx = Vec3(2.0 * spacing, 0, h_right - h_left)
        # Tangent in Z direction (scaled by spacing)
        tz = Vec3(0, 2.0 * spacing, h_up - h_down)

        # Normal is perpendicular to both tangents
        normal = tz.cross(tx)
        normal.normalize()

        return normal.x, normal.y, normal.z

    def _create_mesh(self):
        """Create the visual mesh for the terrain."""
        # Create vertex data format
        vformat = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData("terrain", vformat, Geom.UHStatic)
        vdata.setNumRows((self.resolution + 1) * (self.resolution + 1))

        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        color = GeomVertexWriter(vdata, "color")

        # Calculate spacing between vertices in world units
        spacing = self.size / self.resolution

        # Create vertices
        for z in range(self.resolution + 1):
            for x in range(self.resolution + 1):
                world_x = self.world_x + (x * spacing)
                world_z = self.world_z + (z * spacing)
                height = self.height_data[x][z]

                vertex.addData3(world_x, world_z, height)

                # Calculate proper normal by averaging adjacent faces
                nx, ny, nz = self._calculate_normal(x, z)
                normal.addData3(nx, ny, nz)

                # Color based on height or debug color
                if testgame.config.settings.DEBUG_CHUNK_COLORS:
                    vertex_color = self.debug_color
                else:
                    vertex_color = self._get_vertex_color(height)
                color.addData4(vertex_color)

        # Create triangles
        tris = GeomTriangles(Geom.UHStatic)

        for z in range(self.resolution):
            for x in range(self.resolution):
                # Calculate vertex indices
                v0 = z * (self.resolution + 1) + x
                v1 = v0 + 1
                v2 = v0 + (self.resolution + 1)
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
        node = GeomNode("terrain_chunk")
        node.addGeom(geom)

        # Attach to render
        self.node_path = self.render.attachNewNode(node)

        # Enable two-sided rendering (render both front and back faces)
        self.node_path.setTwoSided(True)

        # Set collision mask so raycasting can detect it
        self.node_path.setCollideMask(1)

        # Set shader input to enable/disable vertex colors
        if testgame.config.settings.DEBUG_CHUNK_COLORS:
            self.node_path.setShaderInput("useVertexColor", 1)
        else:
            self.node_path.setShaderInput("useVertexColor", 0)

        # Add wireframe overlay if debug mode is enabled
        if testgame.config.settings.DEBUG_CHUNK_WIREFRAME:
            self._create_wireframe()

    def _get_vertex_color(self, height):
        """Get color based on terrain height - Mount Everest style coloring with base camp areas.

        Args:
            height: Height value

        Returns:
            Vec4 color
        """
        if height < 25:
            # Valley floor and base areas - green vegetation/grass
            return Vec4(0.25, 0.45, 0.15, 1.0)
        elif height < 40:
            # Lower foothills - mixed grass and alpine meadows
            return Vec4(0.35, 0.42, 0.25, 1.0)
        elif height < 75:
            # Base camp areas and lower slopes - brown earth and scree
            return Vec4(0.40, 0.30, 0.20, 1.0)
        elif height < 120:
            # Lower mountain slopes - darker brown/grey rock
            return Vec4(0.32, 0.28, 0.24, 1.0)
        elif height < 200:
            # Mid-elevation rocky slopes - grey-brown exposed rock
            return Vec4(0.42, 0.38, 0.34, 1.0)
        elif height < 280:
            # Upper rocky faces - grey granite-like rock
            return Vec4(0.50, 0.48, 0.44, 1.0)
        elif height < 350:
            # High altitude rock with snow patches - light grey with white
            return Vec4(0.58, 0.60, 0.62, 1.0)
        elif height < 420:
            # Snow line begins - mixed rock and snow
            return Vec4(0.68, 0.72, 0.76, 1.0)
        elif height < 500:
            # Ice walls and glaciated zones - blue-white ice
            return Vec4(0.75, 0.82, 0.90, 1.0)
        elif height < 600:
            # Deep snow and ice fields - bright blue-white
            return Vec4(0.82, 0.88, 0.95, 1.0)
        elif height < 700:
            # High altitude permanent snow - very bright white with blue tint
            return Vec4(0.88, 0.92, 0.98, 1.0)
        elif height < 800:
            # Summit approaches - pristine white snow
            return Vec4(0.92, 0.95, 1.0, 1.0)
        else:
            # Summit zone - pure brilliant white (like Everest summit)
            return Vec4(0.96, 0.98, 1.0, 1.0)

    def _create_wireframe(self):
        """Create a wireframe overlay for debugging chunk boundaries."""
        from panda3d.core import LineSegs

        # Create line segments for the wireframe
        lines = LineSegs()
        lines.setThickness(2)
        lines.setColor(0, 0, 0, 1)  # Black wireframe

        # Calculate spacing between vertices in world units
        spacing = self.size / self.resolution

        # Draw horizontal lines
        for z in range(self.resolution + 1):
            for x in range(self.resolution):
                world_x = self.world_x + (x * spacing)
                world_z = self.world_z + (z * spacing)
                height1 = self.height_data[x][z]
                height2 = self.height_data[x + 1][z]

                lines.moveTo(world_x, world_z, height1 + 0.01)
                lines.drawTo(world_x + spacing, world_z, height2 + 0.01)

        # Draw vertical lines
        for x in range(self.resolution + 1):
            for z in range(self.resolution):
                world_x = self.world_x + (x * spacing)
                world_z = self.world_z + (z * spacing)
                height1 = self.height_data[x][z]
                height2 = self.height_data[x][z + 1]

                lines.moveTo(world_x, world_z, height1 + 0.01)
                lines.drawTo(world_x, world_z + spacing, height2 + 0.01)

        # Create and attach the wireframe node
        wireframe_geom = lines.create()
        self.wireframe_node = self.render.attachNewNode(wireframe_geom)

    def _create_collision(self):
        """Create physics collision mesh."""
        mesh = BulletTriangleMesh()

        # Calculate spacing between vertices in world units
        spacing = self.size / self.resolution

        for z in range(self.resolution):
            for x in range(self.resolution):
                world_x = self.world_x + (x * spacing)
                world_z = self.world_z + (z * spacing)

                # Get the four corners of this quad
                h00 = self.height_data[x][z]
                h10 = self.height_data[x + 1][z]
                h01 = self.height_data[x][z + 1]
                h11 = self.height_data[x + 1][z + 1]

                # Create two triangles
                v0 = Vec3(world_x, world_z, h00)
                v1 = Vec3(world_x + spacing, world_z, h10)
                v2 = Vec3(world_x, world_z + spacing, h01)
                v3 = Vec3(world_x + spacing, world_z + spacing, h11)

                mesh.addTriangle(v0, v2, v1)
                mesh.addTriangle(v1, v2, v3)

        shape = BulletTriangleMeshShape(mesh, dynamic=False)

        self.physics_node = BulletRigidBodyNode(
            f"terrain_collision_{self.chunk_x}_{self.chunk_z}"
        )
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
        if self.wireframe_node:
            self.wireframe_node.removeNode()
            self.wireframe_node = None

        # Regenerate
        self._create_mesh()
        self._create_collision()

    def _update_mesh(self):
        """Update mesh after height data modification (alias for regenerate)."""
        self.regenerate()

    def _update_collision(self):
        """Update collision after height data modification (alias for regenerate)."""
        # Note: regenerate() already handles both mesh and collision
        pass

    def remove(self):
        """Remove this chunk from the scene."""
        if self.node_path:
            self.node_path.removeNode()
        if self.physics_node:
            self.bullet_world.removeRigidBody(self.physics_node)
        if self.wireframe_node:
            self.wireframe_node.removeNode()


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
