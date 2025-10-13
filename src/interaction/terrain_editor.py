"""Terrain editing tools for modifying the game world."""

import math
from panda3d.core import Vec3
from src.config.settings import CHUNK_SIZE


class TerrainEditor:
    """Provides tools for editing terrain in real-time."""

    def __init__(self, terrain):
        """Initialize terrain editor.

        Args:
            terrain: Terrain instance to edit
        """
        self.terrain = terrain
        self.brush_size = 3.0
        self.brush_strength = 0.5
        self.edit_mode = 'raise'  # 'raise', 'lower', 'smooth'

    def modify_terrain(self, world_pos, mode=None, strength=None):
        """Modify terrain at the given world position.

        Args:
            world_pos: Vec3 world position to modify
            mode: Edit mode ('raise', 'lower', 'smooth') or None to use current
            strength: Strength multiplier or None to use current
        """
        if mode is None:
            mode = self.edit_mode
        if strength is None:
            strength = self.brush_strength

        # Find affected chunk
        chunk_x = int(world_pos.x // CHUNK_SIZE)
        chunk_z = int(world_pos.y // CHUNK_SIZE)
        chunk_key = (chunk_x, chunk_z)

        if chunk_key not in self.terrain.chunks:
            return

        chunk = self.terrain.chunks[chunk_key]

        # Get local position in chunk
        local_x = world_pos.x - chunk.world_x
        local_z = world_pos.y - chunk.world_z

        # Apply brush effect to all points within brush radius
        modified = False
        for dx in range(-int(self.brush_size), int(self.brush_size) + 1):
            for dz in range(-int(self.brush_size), int(self.brush_size) + 1):
                # Calculate actual position
                px = int(local_x) + dx
                pz = int(local_z) + dz

                # Check bounds
                if px < 0 or px > CHUNK_SIZE or pz < 0 or pz > CHUNK_SIZE:
                    continue

                # Calculate distance from center
                dist = math.sqrt(dx * dx + dz * dz)
                if dist > self.brush_size:
                    continue

                # Calculate falloff (stronger in center, weaker at edges)
                falloff = 1.0 - (dist / self.brush_size)
                falloff = falloff * falloff  # Square for smoother falloff

                # Apply modification based on mode
                if mode == 'raise':
                    chunk.height_data[px][pz] += strength * falloff
                    modified = True
                elif mode == 'lower':
                    chunk.height_data[px][pz] -= strength * falloff
                    modified = True
                elif mode == 'smooth':
                    # Average with neighbors
                    avg_height = self._get_average_height(chunk, px, pz)
                    blend = strength * falloff * 0.5
                    chunk.height_data[px][pz] = (
                        chunk.height_data[px][pz] * (1 - blend) +
                        avg_height * blend
                    )
                    modified = True

        # Regenerate chunk mesh if modified
        if modified:
            chunk.regenerate()

    def _get_average_height(self, chunk, x, z):
        """Get average height of neighboring vertices.

        Args:
            chunk: TerrainChunk instance
            x: Local X coordinate
            z: Local Z coordinate

        Returns:
            Average height
        """
        total = 0
        count = 0

        for dx in [-1, 0, 1]:
            for dz in [-1, 0, 1]:
                nx, nz = x + dx, z + dz
                if 0 <= nx <= CHUNK_SIZE and 0 <= nz <= CHUNK_SIZE:
                    total += chunk.height_data[nx][nz]
                    count += 1

        return total / count if count > 0 else chunk.height_data[x][z]

    def raise_terrain(self, position):
        """Raise terrain at the given position.

        Args:
            position: World position Vec3 to modify
        """
        self.modify_terrain(position, mode='raise')

    def lower_terrain(self, position):
        """Lower terrain at the given position.

        Args:
            position: World position Vec3 to modify
        """
        self.modify_terrain(position, mode='lower')

    def smooth_terrain(self, position):
        """Smooth terrain at the given position.

        Args:
            position: World position Vec3 to modify
        """
        self.modify_terrain(position, mode='smooth')

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
        self.brush_strength = max(0.1, min(2.0, strength))

    def set_edit_mode(self, mode):
        """Set the current edit mode.

        Args:
            mode: Edit mode ('raise', 'lower', 'smooth')
        """
        if mode in ['raise', 'lower', 'smooth']:
            self.edit_mode = mode
