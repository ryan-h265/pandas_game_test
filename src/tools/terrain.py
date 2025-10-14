"""Terrain tool - for editing terrain heightmaps."""

from .base import Tool, ToolType


class TerrainTool(Tool):
    """Tool for terrain editing (dig, raise, smooth)."""

    def __init__(self, terrain_editor):
        """Initialize terrain tool.

        Args:
            terrain_editor: TerrainEditor instance
        """
        super().__init__("Terrain Editor", ToolType.TERRAIN)
        self.terrain_editor = terrain_editor
        self.edit_mode = "lower"

    def on_activate(self):
        """Called when terrain tool is equipped."""
        return "Equipped: Terrain Editor (dig/build/smooth)"

    def on_primary_use(self, hit_info):
        """Dig/lower terrain."""
        if hit_info:
            self.terrain_editor.set_edit_mode("lower")
            self.terrain_editor.modify_terrain(hit_info["position"])
            return True
        return False

    def on_secondary_use(self, hit_info):
        """Raise terrain."""
        if hit_info:
            self.terrain_editor.set_edit_mode("raise")
            self.terrain_editor.modify_terrain(hit_info["position"])
            return True
        return False

    def on_tertiary_use(self, hit_info):
        """Smooth terrain."""
        if hit_info:
            self.terrain_editor.set_edit_mode("smooth")
            self.terrain_editor.modify_terrain(hit_info["position"])
            return True
        return False

    def set_mode(self, mode):
        """Set terrain editing mode.

        Args:
            mode: 'lower', 'raise', or 'smooth'
        """
        self.edit_mode = mode
        self.terrain_editor.set_edit_mode(mode)
        # Return nothing - parent will handle via tool_manager

    def adjust_strength(self, delta):
        """Adjust terrain editing strength.

        Args:
            delta: Amount to adjust (positive or negative)
        """
        new_strength = self.terrain_editor.brush_strength + delta
        self.terrain_editor.set_brush_strength(new_strength)
        return self.terrain_editor.brush_strength

    def get_strength(self):
        """Get current terrain editing strength.

        Returns:
            float: Current brush strength
        """
        return self.terrain_editor.brush_strength

    def adjust_primary_property(self, delta):
        """Adjust brush size (scroll wheel).

        Args:
            delta: Amount to adjust

        Returns:
            tuple: (property_name, new_value)
        """
        new_size = self.terrain_editor.brush_size + delta
        self.terrain_editor.set_brush_size(new_size)
        return ("Brush Size", self.terrain_editor.brush_size)

    def adjust_secondary_property(self, delta):
        """Adjust brush strength ([ ] keys).

        Args:
            delta: Amount to adjust

        Returns:
            tuple: (property_name, new_value)
        """
        new_strength = self.terrain_editor.brush_strength + delta
        self.terrain_editor.set_brush_strength(new_strength)
        return ("Brush Strength", self.terrain_editor.brush_strength)
