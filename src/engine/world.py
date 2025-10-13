"""World management and initialization."""

from config.settings import RENDER_DISTANCE
from engine.terrain import Terrain


class World:
    """Manages the game world state and updates."""

    def __init__(self, render, bullet_world):
        """Initialize the world.

        Args:
            render: Panda3D render node
            bullet_world: Bullet physics world
        """
        self.render = render
        self.bullet_world = bullet_world

        # Initialize terrain system
        self.terrain = Terrain(render, bullet_world)

        # Track loaded chunks
        self.loaded_chunks = set()

        # Generate initial terrain chunks
        self._generate_initial_terrain()

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

    def update(self, dt, camera_pos=None):
        """Update world state.

        Args:
            dt: Delta time since last update
            camera_pos: Camera position for dynamic chunk loading (optional)
        """
        # Update terrain (for dynamic loading if needed)
        if camera_pos:
            self.terrain.update(camera_pos)

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
