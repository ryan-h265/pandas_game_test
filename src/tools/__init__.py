"""Tool system for player interactions."""

from .base import Tool, ToolType
from .fist import FistTool
from .terrain import TerrainTool
from .crowbar import CrowbarTool
from .gun import GunTool
from .placement import PlacementTool
from .tool_manager import ToolManager

# Backward compatibility alias
BuildingTool = PlacementTool

__all__ = [
    "Tool",
    "ToolType",
    "FistTool",
    "TerrainTool",
    "CrowbarTool",
    "GunTool",
    "PlacementTool",
    "BuildingTool",  # Legacy name
    "ToolManager",
]
