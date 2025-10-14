"""Tool management system for player interactions with the world."""

from .base import ToolType
from .fist import FistTool
from .terrain import TerrainTool
from .crowbar import CrowbarTool
from .gun import GunTool


class ToolManager:
    """Manages player tools and tool switching."""

    def __init__(self, terrain_editor, world, camera=None, effects_manager=None, building_raycaster=None, weapon_viewmodel=None):
        """Initialize tool manager.

        Args:
            terrain_editor: TerrainEditor instance
            world: Game world instance
            camera: Camera node for gun aiming (optional)
            effects_manager: EffectsManager for visual effects (optional)
            building_raycaster: BuildingRaycaster for physics raycasting (optional)
            weapon_viewmodel: WeaponViewModel for displaying FPS-style weapons (optional)
        """
        self.tools = {}
        self.active_tool = None
        self.tool_message_callback = None  # Optional callback for UI messages
        self.weapon_viewmodel = weapon_viewmodel

        # Create tools (all melee weapons now use camera + building_raycaster for accurate hit detection)
        self.tools[ToolType.FIST] = FistTool(world, camera, building_raycaster)
        self.tools[ToolType.TERRAIN] = TerrainTool(terrain_editor)
        self.tools[ToolType.CROWBAR] = CrowbarTool(world, camera, building_raycaster)
        if camera:
            self.tools[ToolType.GUN] = GunTool(world, camera, effects_manager, building_raycaster)

        # Start with fist (default)
        self.set_active_tool(ToolType.FIST)

    def set_active_tool(self, tool_type):
        """Switch to a different tool.

        Args:
            tool_type: ToolType enum value
        """
        if tool_type not in self.tools:
            return

        # Deactivate current tool
        if self.active_tool:
            self.active_tool.on_deactivate()

        # Activate new tool
        self.active_tool = self.tools[tool_type]
        message = self.active_tool.on_activate()

        # Update weapon viewmodel
        if self.weapon_viewmodel:
            self.weapon_viewmodel.show_weapon(self.active_tool.view_model_name)

        # Send message to callback if set
        if self.tool_message_callback and message:
            self.tool_message_callback(message)
        else:
            print(message)

    def get_active_tool(self):
        """Get currently active tool.

        Returns:
            Tool instance or None
        """
        return self.active_tool

    def use_primary(self, hit_info):
        """Use active tool's primary action.

        Args:
            hit_info: Hit information from raycast

        Returns:
            bool: True if action was performed
        """
        if self.active_tool:
            result = self.active_tool.on_primary_use(hit_info)
            # Play weapon animation
            if result and self.weapon_viewmodel:
                self.weapon_viewmodel.play_use_animation(self.active_tool.view_model_name)
            return result
        return False

    def use_secondary(self, hit_info):
        """Use active tool's secondary action.

        Args:
            hit_info: Hit information from raycast

        Returns:
            bool: True if action was performed
        """
        if self.active_tool:
            result = self.active_tool.on_secondary_use(hit_info)
            # Play weapon animation for secondary use
            if result and self.weapon_viewmodel:
                self.weapon_viewmodel.play_use_animation(self.active_tool.view_model_name)
            return result
        return False

    def use_tertiary(self, hit_info):
        """Use active tool's tertiary action.

        Args:
            hit_info: Hit information from raycast

        Returns:
            bool: True if action was performed
        """
        if self.active_tool:
            result = self.active_tool.on_tertiary_use(hit_info)
            # Play weapon animation for tertiary use
            if result and self.weapon_viewmodel:
                self.weapon_viewmodel.play_use_animation(self.active_tool.view_model_name)
            return result
        return False

    def update(self, dt, is_moving=False):
        """Update active tool and weapon viewmodel.

        Args:
            dt: Delta time
            is_moving: Whether the player is currently moving
        """
        if self.active_tool:
            self.active_tool.update(dt)
        
        # Update weapon viewmodel (for bob, sway, etc.)
        if self.weapon_viewmodel:
            self.weapon_viewmodel.update(dt, is_moving)

    def cycle_tool(self):
        """Cycle to next tool."""
        tool_types = list(self.tools.keys())
        if not self.active_tool:
            self.set_active_tool(tool_types[0])
            return

        current_type = self.active_tool.tool_type
        current_index = tool_types.index(current_type)
        next_index = (current_index + 1) % len(tool_types)
        self.set_active_tool(tool_types[next_index])
