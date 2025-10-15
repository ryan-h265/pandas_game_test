"""Tool management system for player interactions with the world."""

from .base import ToolType
from .fist import FistTool
from .terrain import TerrainTool
from .crowbar import CrowbarTool
from .gun import GunTool
from .building import BuildingTool


class ToolManager:
    """Manages player tools and tool switching."""

    def __init__(self, terrain_editor, world, camera=None, effects_manager=None, building_raycaster=None, weapon_viewmodel=None, render=None, bullet_world=None, terrain_raycaster=None, mouse_watcher=None, enabled_tools=None):
        """Initialize tool manager.

        Args:
            terrain_editor: TerrainEditor instance
            world: Game world instance
            camera: Camera node for gun aiming (optional)
            effects_manager: EffectsManager for visual effects (optional)
            building_raycaster: BuildingRaycaster for physics raycasting (optional)
            weapon_viewmodel: WeaponViewModel for displaying FPS-style weapons (optional)
            render: Panda3D render node (optional, for building tool)
            bullet_world: Bullet physics world (optional, for building tool)
            terrain_raycaster: TerrainRaycaster for ground placement (optional, for building tool)
            mouse_watcher: MouseWatcher node for raycasting (optional, for building tool)
            enabled_tools: Set of ToolType enums to enable initially. If None, all tools except FIST and CROWBAR are enabled.
        """
        self.tools = {}
        self.active_tool = None
        self.tool_message_callback = None  # Optional callback for UI messages
        self.weapon_viewmodel = weapon_viewmodel

        # Store dependencies for dynamic tool creation
        self._terrain_editor = terrain_editor
        self._world = world
        self._camera = camera
        self._effects_manager = effects_manager
        self._building_raycaster = building_raycaster
        self._render = render
        self._bullet_world = bullet_world
        self._terrain_raycaster = terrain_raycaster
        self._mouse_watcher = mouse_watcher

        # Default enabled tools (excluding fist and crowbar - player must find them)
        if enabled_tools is None:
            enabled_tools = {ToolType.FIST, ToolType.GUN, ToolType.BUILDING}

        # Create enabled tools (all melee weapons now use camera + building_raycaster for accurate hit detection)
        if ToolType.FIST in enabled_tools:
            self.tools[ToolType.FIST] = FistTool(world, camera, building_raycaster)
        if ToolType.TERRAIN in enabled_tools:
            self.tools[ToolType.TERRAIN] = TerrainTool(terrain_editor)
        if ToolType.CROWBAR in enabled_tools:
            self.tools[ToolType.CROWBAR] = CrowbarTool(world, camera, building_raycaster)
        if ToolType.GUN in enabled_tools and camera:
            self.tools[ToolType.GUN] = GunTool(world, camera, effects_manager, building_raycaster)
        if ToolType.BUILDING in enabled_tools and camera and render and bullet_world:
            self.tools[ToolType.BUILDING] = BuildingTool(world, camera, render, bullet_world, terrain_raycaster, mouse_watcher)

        # Start with first available tool
        if self.tools:
            first_tool = next(iter(self.tools.keys()))
            self.set_active_tool(first_tool)

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
        if not tool_types:
            return

        if not self.active_tool:
            self.set_active_tool(tool_types[0])
            return

        current_type = self.active_tool.tool_type
        current_index = tool_types.index(current_type)
        next_index = (current_index + 1) % len(tool_types)
        self.set_active_tool(tool_types[next_index])

    def add_tool(self, tool_type):
        """Add/enable a tool (e.g., when player picks it up).

        Args:
            tool_type: ToolType enum value to enable

        Returns:
            bool: True if tool was added, False if already present or dependencies missing
        """
        if tool_type in self.tools:
            return False

        # Create the tool instance based on type
        tool_created = False
        if tool_type == ToolType.FIST:
            self.tools[ToolType.FIST] = FistTool(self._world, self._camera, self._building_raycaster)
            tool_created = True
        elif tool_type == ToolType.TERRAIN:
            self.tools[ToolType.TERRAIN] = TerrainTool(self._terrain_editor)
            tool_created = True
        elif tool_type == ToolType.CROWBAR:
            self.tools[ToolType.CROWBAR] = CrowbarTool(self._world, self._camera, self._building_raycaster)
            tool_created = True
        elif tool_type == ToolType.GUN and self._camera:
            self.tools[ToolType.GUN] = GunTool(self._world, self._camera, self._effects_manager, self._building_raycaster)
            tool_created = True
        elif tool_type == ToolType.BUILDING and self._camera and self._render and self._bullet_world:
            self.tools[ToolType.BUILDING] = BuildingTool(self._world, self._camera, self._render, self._bullet_world, self._terrain_raycaster, self._mouse_watcher)
            tool_created = True

        if tool_created and self.tool_message_callback:
            tool_name = self.tools[tool_type].name if tool_type in self.tools else str(tool_type)
            self.tool_message_callback(f"Picked up {tool_name}!")

        return tool_created

    def remove_tool(self, tool_type):
        """Remove/disable a tool (e.g., when player drops it).

        Args:
            tool_type: ToolType enum value to disable

        Returns:
            bool: True if tool was removed, False if not present
        """
        if tool_type not in self.tools:
            return False

        # If this was the active tool, switch to another
        if self.active_tool and self.active_tool.tool_type == tool_type:
            self.active_tool.on_deactivate()
            self.active_tool = None

            # Switch to first available tool
            remaining_tools = [t for t in self.tools.keys() if t != tool_type]
            if remaining_tools:
                self.set_active_tool(remaining_tools[0])

        # Remove the tool
        del self.tools[tool_type]
        return True

    def has_tool(self, tool_type):
        """Check if a tool is currently available.

        Args:
            tool_type: ToolType enum value to check

        Returns:
            bool: True if tool is available
        """
        return tool_type in self.tools

    def get_available_tools(self):
        """Get list of currently available tool types.

        Returns:
            list: List of ToolType enums
        """
        return list(self.tools.keys())
