"""World management and initialization."""

from panda3d.core import Vec3, Vec4
from panda3d.bullet import BulletRigidBodyNode, BulletBoxShape

from testgame.config.settings import RENDER_DISTANCE
from testgame.engine.terrain import Terrain
from testgame.structures.simple_building import SimpleBuilding
from testgame.structures.japanese_building import JapaneseBuilding
from testgame.engine.world_serializer import WorldSerializer


class World:
    """Manages the game world state and updates."""

    def __init__(self, render, bullet_world, auto_generate=True):
        """Initialize the world.

        Args:
            render: Panda3D render node
            bullet_world: Bullet physics world
            auto_generate: Whether to automatically generate initial terrain and buildings
        """
        self.render = render
        self.bullet_world = bullet_world

        # Initialize terrain system
        self.terrain = Terrain(render, bullet_world)

        # Track loaded chunks
        self.loaded_chunks = set()

        # Track physics objects
        self.physics_objects = []

        # Track buildings
        self.buildings = []

        # Track props (lanterns, decorations, etc.)
        self.props = []

        # Initialize world serializer
        self.serializer = WorldSerializer()

        if auto_generate:
            # Generate initial terrain chunks
            self._generate_initial_terrain()

            # Add example cubes to demonstrate physics and shadows
            # self._create_example_cubes()

            # Create example destructible buildings
            # self._create_example_buildings()

            # Create example destructible wall
            # self._create_example_wall()

    def _generate_initial_terrain(self):
        """Generate initial terrain chunks around spawn point."""
        print("Generating initial terrain...")

        # Generate chunks in a grid around the origin
        half_render = RENDER_DISTANCE // 2

        for chunk_x in range(-half_render, half_render):
            for chunk_z in range(-half_render, half_render):
                self.terrain.generate_chunk(chunk_x, chunk_z)
                self.loaded_chunks.add((chunk_x, chunk_z))

        print(f"Generated {len(self.loaded_chunks)} terrain chunks")

    def _create_example_cubes(self):
        """Create example cubes to demonstrate physics and shadows."""
        print("Creating example physics cubes...")

        # Define cube positions and sizes
        cube_specs = [
            # Position (x, y, z), size, mass
            (Vec3(20, 20, 50), 2.0, 1.0),  # Medium cube
            (Vec3(18, 18, 55), 1.5, 0.5),  # Small cube
            (Vec3(22, 22, 60), 3.0, 2.0),  # Large cube
            (Vec3(16, 24, 45), 1.0, 0.3),  # Tiny cube
            (Vec3(24, 16, 48), 2.5, 1.5),  # Another medium cube
        ]

        for i, (pos, size, mass) in enumerate(cube_specs):
            cube = self._create_physics_cube(pos, size, mass, f"cube_{i}")
            self.physics_objects.append(cube)

        print(f"Created {len(cube_specs)} example cubes")

    def _create_physics_cube(self, position, size, mass, name):
        """Create a single physics-enabled cube.

        Args:
            position: Vec3 world position
            size: Size of the cube (half-extents)
            mass: Mass of the cube in kg
            name: Name for the node

        Returns:
            NodePath of the created cube
        """
        # Create physics shape
        shape = BulletBoxShape(Vec3(size / 2, size / 2, size / 2))

        # Create rigid body node
        body_node = BulletRigidBodyNode(name)
        body_node.setMass(mass)
        body_node.addShape(shape)

        # Set physics properties
        body_node.setFriction(0.7)
        body_node.setRestitution(0.3)  # Some bounciness

        # Create NodePath and attach to scene
        body_np = self.render.attachNewNode(body_node)
        body_np.setPos(position)

        # Add to physics world
        self.bullet_world.attachRigidBody(body_node)

        # Create visual geometry
        from panda3d.core import (
            GeomNode,
            GeomVertexFormat,
            GeomVertexData,
            GeomVertexWriter,
        )
        from panda3d.core import Geom, GeomTriangles, Vec4

        # Create vertex data
        vformat = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData(f"{name}_vdata", vformat, Geom.UHStatic)

        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        color = GeomVertexWriter(vdata, "color")

        # Generate cube vertices with different colors per cube
        import random

        cube_color = Vec4(
            random.uniform(0.5, 1.0),
            random.uniform(0.5, 1.0),
            random.uniform(0.5, 1.0),
            1.0,
        )

        # Define cube vertices (8 corners)
        s = size / 2
        vertices = [
            Vec3(-s, -s, -s),
            Vec3(s, -s, -s),
            Vec3(s, s, -s),
            Vec3(-s, s, -s),  # bottom
            Vec3(-s, -s, s),
            Vec3(s, -s, s),
            Vec3(s, s, s),
            Vec3(-s, s, s),  # top
        ]

        # Define faces with normals (counter-clockwise winding for outward-facing)
        faces = [
            # Face vertices (CCW from outside), normal
            ([3, 2, 1, 0], Vec3(0, 0, -1)),  # bottom
            ([4, 5, 6, 7], Vec3(0, 0, 1)),  # top
            ([1, 5, 4, 0], Vec3(0, -1, 0)),  # front
            ([3, 7, 6, 2], Vec3(0, 1, 0)),  # back
            ([4, 7, 3, 0], Vec3(-1, 0, 0)),  # left
            ([2, 6, 5, 1], Vec3(1, 0, 0)),  # right
        ]

        # Build geometry
        tris = GeomTriangles(Geom.UHStatic)
        vtx_index = 0

        for face_indices, face_normal in faces:
            # Two triangles per face (counter-clockwise winding)
            # First triangle: 0, 1, 2
            for i in [0, 1, 2]:
                v = vertices[face_indices[i]]
                vertex.addData3(v)
                normal.addData3(face_normal)
                color.addData4(cube_color)
                tris.addVertex(vtx_index)
                vtx_index += 1

            # Second triangle: 0, 2, 3
            for i in [0, 2, 3]:
                v = vertices[face_indices[i]]
                vertex.addData3(v)
                normal.addData3(face_normal)
                color.addData4(cube_color)
                tris.addVertex(vtx_index)
                vtx_index += 1

        tris.closePrimitive()

        # Create geometry
        geom = Geom(vdata)
        geom.addPrimitive(tris)

        # Create node and attach
        geom_node = GeomNode(f"{name}_geom")
        geom_node.addGeom(geom)
        geom_np = body_np.attachNewNode(geom_node)

        return body_np

    def _create_example_buildings(self):
        """Create example destructible buildings."""
        print("Creating example buildings...")

        # Create a Western-style building
        western_building = SimpleBuilding(
            self.bullet_world,
            self.render,
            Vec3(30, 30, 0),
            width=15,
            depth=12,
            height=10,
            name="western_building",
        )
        self.buildings.append(western_building)

        # Create a Japanese-style building
        japanese_building = JapaneseBuilding(
            self.bullet_world,
            self.render,
            Vec3(55, 30, 0),
            width=14,
            depth=11,
            height=7,
            name="japanese_building",
        )
        self.buildings.append(japanese_building)

        print(f"Created {len(self.buildings)} example buildings (Western + Japanese)")

    def add_building(self, building):
        """Add a building to the world.

        Args:
            building: Building instance to add
        """
        self.buildings.append(building)
        print(
            f"Added building '{building.name}' to world (total: {len(self.buildings)} buildings)"
        )

    def add_prop(self, prop):
        """Add a prop (lantern, decoration, etc.) to the world.

        Args:
            prop: Prop instance to add
        """
        self.props.append(prop)
        print(f"Added prop to world (total: {len(self.props)} props)")

    def damage_building_at_position(self, position, damage=50):
        """Damage a building piece at or near a position.

        Args:
            position: Vec3 world position
            damage: Amount of damage to apply

        Returns:
            bool: True if something was damaged
        """
        # Find the closest building piece
        closest_building = None
        closest_piece = None
        closest_dist = float("inf")

        for building in self.buildings:
            piece = building.get_piece_at_position(position, max_distance=5.0)
            if piece:
                piece_pos = piece.body_np.getPos()
                dist = (piece_pos - position).length()
                if dist < closest_dist:
                    closest_dist = dist
                    closest_piece = piece
                    closest_building = building

        if closest_piece and closest_building:
            print(f"Damaging {closest_piece.name} (distance: {closest_dist:.2f})")
            closest_building.damage_piece(
                closest_piece.name, damage, impact_pos=position
            )
            return True

        return False

    def update(self, dt, camera_pos=None):
        """Update world state.

        Args:
            dt: Delta time since last update
            camera_pos: Camera position for dynamic chunk loading (optional)
        """
        # Update terrain (for dynamic loading if needed)
        if camera_pos:
            self.terrain.update(camera_pos)

        # Update buildings (cleanup debris)
        import time

        current_time = time.time()
        for building in self.buildings:
            if hasattr(building, "update"):
                building.update(dt, current_time)

    def update_chunks_around_position(self, position):
        """Load/unload chunks based on position.

        Args:
            position: World position (typically camera position)
        """
        # Calculate chunk coordinates
        chunk_x = int(position[0] // 32)  # Using CHUNK_SIZE
        chunk_z = int(position[1] // 32)

        # Determine which chunks should be loaded
        half_render = RENDER_DISTANCE // 2
        desired_chunks = set()

        for dx in range(-half_render, half_render):
            for dz in range(-half_render, half_render):
                desired_chunks.add((chunk_x + dx, chunk_z + dz))

        # Unload chunks that are too far
        chunks_to_unload = self.loaded_chunks - desired_chunks
        for chunk_coord in chunks_to_unload:
            self.terrain.remove_chunk(chunk_coord[0], chunk_coord[1])
            self.loaded_chunks.remove(chunk_coord)

        # Load new chunks that came into range
        chunks_to_load = desired_chunks - self.loaded_chunks
        for chunk_coord in chunks_to_load:
            self.terrain.generate_chunk(chunk_coord[0], chunk_coord[1])
            self.loaded_chunks.add(chunk_coord)

    def get_height_at(self, x, z):
        """Get terrain height at world position.

        Args:
            x: World X coordinate
            z: World Z coordinate

        Returns:
            Height at position or 0 if not loaded
        """
        height = self.terrain.get_height_at(x, z)
        return height if height is not None else 0

    def _create_example_wall(self):
        """Create example destructible wall to demonstrate building mechanics."""
        print("Creating example destructible wall...")

        # Create a simple standalone wall using the building system
        from structures.building import BuildingPiece

        # Wall parameters
        wall_position = Vec3(25, 25, 0)  # Position on terrain
        wall_width = 15.0  # Wide wall
        wall_thickness = 0.8  # Thin wall
        wall_height = 8.0  # Tall wall
        wall_color = Vec4(0.7, 0.6, 0.5, 1.0)  # Stone/concrete color

        # Get terrain height at wall position
        terrain_height = self.get_height_at(wall_position.x, wall_position.y)
        wall_base_position = Vec3(
            wall_position.x, wall_position.y, terrain_height + wall_height / 2
        )

        # Create a single large wall piece
        wall = BuildingPiece(
            self.bullet_world,
            self.render,
            wall_base_position,
            Vec3(wall_width, wall_thickness, wall_height),
            mass=50.0,  # Heavy wall
            color=wall_color,
            name="example_wall_main",
            piece_type="wall",
        )

        # Add to buildings list for damage handling
        # Create a simple Building wrapper to manage this standalone wall
        from structures.building import Building

        wall_building = Building(
            self.bullet_world,
            self.render,
            wall_base_position,
            name="standalone_wall",
        )
        wall_building.add_piece(wall)
        self.buildings.append(wall_building)

        print(f"Created standalone destructible wall at {wall_base_position}")

    def save_to_file(self, save_name, player, metadata=None):
        """Save the current world state to a file.

        Args:
            save_name: Name for the save file
            player: PlayerController instance
            metadata: Optional metadata dict (title, description, etc.)

        Returns:
            bool: True if save was successful
        """
        return self.serializer.save_world(self, player, save_name, metadata)

    def load_from_file(self, save_name, player):
        """Load world state from a file.

        Args:
            save_name: Name of the save file to load
            player: PlayerController instance

        Returns:
            bool: True if load was successful
        """
        return self.serializer.load_world(self, player, save_name)

    def list_saves(self):
        """List all available save files.

        Returns:
            List of tuples (save_name, metadata_dict)
        """
        return self.serializer.list_saves()

    def clear_world(self):
        """Clear all objects from the world (buildings, physics objects, etc.)."""
        # Remove all buildings
        for building in self.buildings:
            if hasattr(building, "destroy"):
                building.destroy()
        self.buildings.clear()

        # Remove all physics objects
        for obj_np in self.physics_objects:
            if obj_np and not obj_np.isEmpty():
                body_node = obj_np.node()
                self.bullet_world.removeRigidBody(body_node)
                obj_np.removeNode()
        self.physics_objects.clear()

        print("World cleared")
