"""Terrain editing tools for modifying the game world."""

import math
from config.settings import CHUNK_SIZE, TERRAIN_RESOLUTION, MODIFIABLE_TERRAIN


class TerrainEditor:
    """Provides tools for editing terrain in real-time."""

    def __init__(self, terrain):
        """Initialize terrain editor.

        Args:
            terrain: Terrain instance to edit
        """
        self.terrain = terrain
        self.brush_size = 3.0
        self.brush_strength = 0.05  # Reduced from 0.5 for mild changes
        self.edit_mode = "raise"  # 'raise', 'lower', 'smooth'

    def modify_terrain(self, world_pos, mode=None, strength=None):
        """Modify terrain at the given world position.

        Args:
            world_pos: Vec3 world position to modify
            mode: Edit mode ('raise', 'lower', 'smooth') or None to use current
            strength: Strength multiplier or None to use current
        """
        # Check if terrain modification is enabled
        if not MODIFIABLE_TERRAIN:
            return

        if mode is None:
            mode = self.edit_mode
        if strength is None:
            strength = self.brush_strength

        # Track which chunks have been modified
        modified_chunks = set()

        # Store height modifications by world coordinate to ensure consistency
        height_modifications = {}

        # Apply brush effect to all points within brush radius
        for dx in range(-int(self.brush_size) - 1, int(self.brush_size) + 2):
            for dz in range(-int(self.brush_size) - 1, int(self.brush_size) + 2):
                # Calculate world position
                world_x = int(world_pos.x) + dx
                world_z = int(world_pos.y) + dz

                # Calculate distance from center
                dist = math.sqrt(dx * dx + dz * dz)
                if dist > self.brush_size:
                    continue

                # Calculate falloff (stronger in center, weaker at edges)
                falloff = 1.0 - (dist / self.brush_size)
                falloff = falloff * falloff  # Square for smoother falloff

                # Calculate the height modification for this world position
                world_key = (world_x, world_z)

                if mode == "raise":
                    if world_key not in height_modifications:
                        height_modifications[world_key] = strength * falloff
                elif mode == "lower":
                    if world_key not in height_modifications:
                        height_modifications[world_key] = -strength * falloff
                elif mode == "smooth":
                    if world_key not in height_modifications:
                        avg_height = self._get_average_height_world(world_x, world_z)
                        blend = strength * falloff * 0.5
                        height_modifications[world_key] = ("smooth", avg_height, blend)

        # Apply all modifications to all affected chunks
        for (world_x, world_z), modification in height_modifications.items():
            # Find all chunks that contain this world position
            # A vertex can be at the boundary of up to 4 chunks
            chunks_to_update = []

            # Check which chunks this vertex belongs to
            for offset_x in [0, -1]:
                for offset_z in [0, -1]:
                    test_chunk_x = (world_x + offset_x) // CHUNK_SIZE
                    test_chunk_z = (world_z + offset_z) // CHUNK_SIZE
                    chunk_key = (test_chunk_x, test_chunk_z)

                    if chunk_key in self.terrain.chunks:
                        chunk = self.terrain.chunks[chunk_key]
                        local_x = world_x - chunk.world_x
                        local_z = world_z - chunk.world_z

                        # Check if this position is within this chunk's height data
                        if 0 <= local_x <= CHUNK_SIZE and 0 <= local_z <= CHUNK_SIZE:
                            chunks_to_update.append(
                                (chunk_key, chunk, local_x, local_z)
                            )

            # Apply the same modification to all chunks that share this vertex
            for chunk_key, chunk, local_x, local_z in chunks_to_update:
                # Convert world-space local coordinates to array indices
                # Array indices go from 0 to resolution, not 0 to chunk_size
                spacing = CHUNK_SIZE / TERRAIN_RESOLUTION
                array_x = int(round(local_x / spacing))
                array_z = int(round(local_z / spacing))

                # Ensure indices are within bounds
                array_x = max(0, min(TERRAIN_RESOLUTION, array_x))
                array_z = max(0, min(TERRAIN_RESOLUTION, array_z))

                if isinstance(modification, tuple) and modification[0] == "smooth":
                    _, avg_height, blend = modification
                    chunk.height_data[array_x][array_z] = (
                        chunk.height_data[array_x][array_z] * (1 - blend)
                        + avg_height * blend
                    )
                else:
                    chunk.height_data[array_x][array_z] += modification
                modified_chunks.add(chunk_key)

        # Regenerate all modified chunks
        for chunk_key in modified_chunks:
            self.terrain.chunks[chunk_key].regenerate()

    def _get_average_height(self, chunk, x, z):
        """Get average height of neighboring vertices.

        Args:
            chunk: TerrainChunk instance
            x: Local X coordinate (array index, not world coordinate)
            z: Local Z coordinate (array index, not world coordinate)

        Returns:
            Average height
        """
        total = 0
        count = 0

        for dx in [-1, 0, 1]:
            for dz in [-1, 0, 1]:
                nx, nz = x + dx, z + dz
                if 0 <= nx <= TERRAIN_RESOLUTION and 0 <= nz <= TERRAIN_RESOLUTION:
                    total += chunk.height_data[nx][nz]
                    count += 1

        return total / count if count > 0 else chunk.height_data[x][z]

    def _get_average_height_world(self, world_x, world_z):
        """Get average height of neighboring vertices using world coordinates.

        This method can access vertices across chunk boundaries.

        Args:
            world_x: World X coordinate
            world_z: World Z coordinate

        Returns:
            Average height
        """
        total = 0
        count = 0
        spacing = CHUNK_SIZE / TERRAIN_RESOLUTION

        for dx in [-1, 0, 1]:
            for dz in [-1, 0, 1]:
                wx = world_x + dx
                wz = world_z + dz

                # Determine which chunk this position belongs to
                chunk_x = int(wx // CHUNK_SIZE)
                chunk_z = int(wz // CHUNK_SIZE)
                chunk_key = (chunk_x, chunk_z)

                if chunk_key not in self.terrain.chunks:
                    continue

                chunk = self.terrain.chunks[chunk_key]

                # Get local position in world units
                local_x = int(wx - chunk.world_x)
                local_z = int(wz - chunk.world_z)

                if 0 <= local_x <= CHUNK_SIZE and 0 <= local_z <= CHUNK_SIZE:
                    # Convert to array indices
                    array_x = int(round(local_x / spacing))
                    array_z = int(round(local_z / spacing))
                    array_x = max(0, min(TERRAIN_RESOLUTION, array_x))
                    array_z = max(0, min(TERRAIN_RESOLUTION, array_z))

                    total += chunk.height_data[array_x][array_z]
                    count += 1

        # Fallback to current height if no neighbors found
        if count == 0:
            chunk_x = int(world_x // CHUNK_SIZE)
            chunk_z = int(world_z // CHUNK_SIZE)
            chunk_key = (chunk_x, chunk_z)
            if chunk_key in self.terrain.chunks:
                chunk = self.terrain.chunks[chunk_key]
                local_x = int(world_x - chunk.world_x)
                local_z = int(world_z - chunk.world_z)
                if 0 <= local_x <= CHUNK_SIZE and 0 <= local_z <= CHUNK_SIZE:
                    # Convert to array indices
                    array_x = int(round(local_x / spacing))
                    array_z = int(round(local_z / spacing))
                    array_x = max(0, min(TERRAIN_RESOLUTION, array_x))
                    array_z = max(0, min(TERRAIN_RESOLUTION, array_z))
                    return chunk.height_data[array_x][array_z]
            return 0

        return total / count

    def raise_terrain(self, position):
        """Raise terrain at the given position.

        Args:
            position: World position Vec3 to modify
        """
        self.modify_terrain(position, mode="raise")

    def lower_terrain(self, position):
        """Lower terrain at the given position.

        Args:
            position: World position Vec3 to modify
        """
        self.modify_terrain(position, mode="lower")

    def smooth_terrain(self, position):
        """Smooth terrain at the given position.

        Args:
            position: World position Vec3 to modify
        """
        self.modify_terrain(position, mode="smooth")

    def set_brush_size(self, size):
        """Set the size of the terrain editing brush.

        Args:
            size: Brush size in world units
        """
        self.brush_size = max(1.0, min(10.0, size))

    def set_brush_strength(self, strength):
        """Set the strength of the terrain editing brush.

        Args:
            strength: Brush strength multiplier
        """
        self.brush_strength = max(0.01, min(1.0, strength))

    def set_edit_mode(self, mode):
        """Set the current edit mode.

        Args:
            mode: Edit mode ('raise', 'lower', 'smooth')
        """
        if mode in ["raise", "lower", "smooth"]:
            self.edit_mode = mode
