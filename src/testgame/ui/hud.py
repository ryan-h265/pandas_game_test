"""HUD (Heads-Up Display) implementation."""

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, CardMaker, TransparencyAttrib

from testgame.tools.base import ToolType


class HUD:
    """Manages the in-game heads-up display."""

    def __init__(self, aspect2d, render=None):
        """Initialize HUD.

        Args:
            aspect2d: Panda3D aspect2d node for 2D overlay
            render: Panda3D render node (optional, for minimap)
        """
        self.visible = True
        self.elements = []
        self.aspect2d = aspect2d
        self.render = render

        # Health bar (bottom-left)
        self.health_bar_bg = self._create_bar(
            -1.2, -0.9, 0.4, 0.05, (0.3, 0.3, 0.3, 0.8)
        )
        self.health_bar_fg = self._create_bar(
            -1.2, -0.9, 0.4, 0.05, (0.8, 0.1, 0.1, 1.0)
        )
        self.health_text = OnscreenText(
            text="Health: 100/100",
            pos=(-1.2, -0.96),
            scale=0.04,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            mayChange=True,
        )
        self.max_health = 100
        self.current_health = 100

        # Compass (top-center)
        self.compass_bg = self._create_bar(-0.15, 0.85, 0.3, 0.08, (0.2, 0.2, 0.2, 0.7))
        self.compass_text = OnscreenText(
            text="N",
            pos=(0, 0.85),
            scale=0.06,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            mayChange=True,
        )
        self.compass_degree_text = OnscreenText(
            text="0°",
            pos=(0, 0.78),
            scale=0.04,
            fg=(0.8, 0.8, 0.8, 1),
            align=TextNode.ACenter,
            mayChange=True,
        )

        # Minimap (top-right)
        # self.minimap_size = 0.25
        # self.minimap_bg = self._create_bar(0.95, 0.65, self.minimap_size, self.minimap_size, (0.1, 0.1, 0.1, 0.8))
        # self.minimap_text = OnscreenText(
        #     text="MAP",
        #     pos=(1.08, 0.88),
        #     scale=0.03,
        #     fg=(0.7, 0.7, 0.7, 1),
        #     align=TextNode.ACenter,
        #     mayChange=True,
        # )
        # self.minimap_pos_text = OnscreenText(
        #     text="X: 0, Y: 0",
        #     pos=(1.08, 0.62),
        #     scale=0.025,
        #     fg=(0.6, 0.6, 0.6, 1),
        #     align=TextNode.ACenter,
        #     mayChange=True,
        # )

        # Tool info panel (bottom-right)
        self.tool_panel_bg = self._create_bar(
            0.7, -0.95, 0.5, 0.25, (0.15, 0.15, 0.15, 0.8)
        )
        self.tool_name_text = OnscreenText(
            text="Tool: None",
            pos=(0.72, -0.78),
            scale=0.045,
            fg=(1, 1, 0.5, 1),
            align=TextNode.ALeft,
            mayChange=True,
        )
        self.tool_info_text = OnscreenText(
            text="",
            pos=(0.72, -0.84),
            scale=0.035,
            fg=(0.9, 0.9, 0.9, 1),
            align=TextNode.ALeft,
            mayChange=True,
        )
        self.tool_info_text2 = OnscreenText(
            text="",
            pos=(0.72, -0.88),
            scale=0.035,
            fg=(0.9, 0.9, 0.9, 1),
            align=TextNode.ALeft,
            mayChange=True,
        )
        self.tool_info_text3 = OnscreenText(
            text="",
            pos=(0.72, -0.92),
            scale=0.028,
            fg=(0.7, 0.7, 0.7, 1),
            align=TextNode.ALeft,
            mayChange=True,
        )
        self.tool_info_text4 = OnscreenText(
            text="",
            pos=(0.72, -0.95),
            scale=0.028,
            fg=(0.7, 0.7, 0.7, 1),
            align=TextNode.ALeft,
            mayChange=True,
        )

        # Tool display text (top-right, legacy position)
        self.tool_text = OnscreenText(
            text="",
            pos=(1.3, 0.9),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ARight,
            mayChange=True,
        )

        # Message display (center-bottom)
        self.message_text = OnscreenText(
            text="",
            pos=(0, -0.8),
            scale=0.04,
            fg=(1, 1, 0.5, 1),
            align=TextNode.ACenter,
            mayChange=True,
        )
        self.message_timer = 0.0
        self.message_duration = 2.0  # Show messages for 2 seconds

        # FPS counter (top-left)
        self.fps_text = OnscreenText(
            text="FPS: --",
            pos=(-1.3, 0.9),
            scale=0.05,
            fg=(0.5, 1, 0.5, 1),
            align=TextNode.ALeft,
            mayChange=True,
        )
        self.fps_update_timer = 0.0
        self.fps_update_interval = 0.5  # Update every 0.5 seconds

    def _create_bar(self, x, y, width, height, color):
        """Create a colored rectangular bar.

        Args:
            x: X position
            y: Y position
            width: Width of bar
            height: Height of bar
            color: RGBA color tuple

        Returns:
            CardMaker node
        """
        cm = CardMaker("bar")
        cm.setFrame(x, x + width, y, y + height)
        bar = self.aspect2d.attachNewNode(cm.generate())
        bar.setTransparency(TransparencyAttrib.MAlpha)
        bar.setColor(*color)
        return bar

    def show(self):
        """Show the HUD."""
        self.visible = True

    def hide(self):
        """Hide the HUD."""
        self.visible = False

    def update(self, dt, fps=None, camera_heading=None, player_pos=None, tool=None):
        """Update HUD elements.

        Args:
            dt: Delta time since last update
            fps: Current FPS (frames per second)
            camera_heading: Camera heading in degrees (for compass)
            player_pos: Player position Vec3 (for minimap)
            tool: Current active tool (for tool info)
        """
        # Update message timer
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message_text.setText("")

        # Update FPS counter
        if fps is not None:
            self.fps_update_timer += dt
            if self.fps_update_timer >= self.fps_update_interval:
                self.fps_text.setText(f"FPS: {int(fps)}")
                self.fps_update_timer = 0.0

        # Update compass
        if camera_heading is not None:
            self.update_compass(camera_heading)

        # Update minimap position
        # if player_pos is not None:
        #     self.update_minimap(player_pos)

    def set_tool_name(self, tool_name):
        """Update tool display.

        Args:
            tool_name: Name of current tool
        """
        self.tool_text.setText(f"Tool: {tool_name}")

    def show_message(self, message, duration=None):
        """Display a temporary message.

        Args:
            message: Message text to display
            duration: Optional duration in seconds (uses default if not provided)
        """
        self.message_text.setText(message)
        self.message_timer = duration if duration is not None else self.message_duration

    def add_element(self, element):
        """Add a UI element to the HUD.

        Args:
            element: UI element to add
        """
        self.elements.append(element)

    def remove_element(self, element):
        """Remove a UI element from the HUD.

        Args:
            element: UI element to remove
        """
        if element in self.elements:
            self.elements.remove(element)

    def set_health(self, current, maximum=None):
        """Update health display.

        Args:
            current: Current health value
            maximum: Maximum health (optional, uses current max if not provided)
        """
        if maximum is not None:
            self.max_health = maximum
        self.current_health = max(0, min(current, self.max_health))

        # Update health bar width
        health_percent = (
            self.current_health / self.max_health if self.max_health > 0 else 0
        )

        # Update foreground bar scale
        self.health_bar_fg.setScale(health_percent, 1, 1)

        # Update health text
        self.health_text.setText(
            f"Health: {int(self.current_health)}/{int(self.max_health)}"
        )

        # Change color based on health level
        if health_percent > 0.6:
            self.health_bar_fg.setColor(0.1, 0.8, 0.1, 1.0)  # Green
        elif health_percent > 0.3:
            self.health_bar_fg.setColor(0.9, 0.7, 0.1, 1.0)  # Yellow
        else:
            self.health_bar_fg.setColor(0.8, 0.1, 0.1, 1.0)  # Red

    def update_compass(self, heading_degrees):
        """Update compass display.

        Args:
            heading_degrees: Camera heading in degrees (0 = North, 90 = East, etc.)
        """
        # Normalize heading to 0-360
        heading = heading_degrees % 360

        # Determine cardinal direction
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = int((heading + 22.5) / 45) % 8
        direction = directions[index]

        self.compass_text.setText(direction)
        self.compass_degree_text.setText(f"{int(heading)}°")

    # def update_minimap(self, player_pos):
    #     """Update minimap with player position.

    #     Args:
    #         player_pos: Player position Vec3
    #     """
    #     self.minimap_pos_text.setText(f"X: {int(player_pos.x)}, Y: {int(player_pos.y)}")

    def update_tool_info(self, tool):
        """Update tool info panel with tool-specific information.

        Args:
            tool: Active tool instance
        """
        if not tool:
            self.tool_name_text.setText("Tool: None")
            self.tool_info_text.setText("")
            self.tool_info_text2.setText("")
            self.tool_info_text3.setText("")
            self.tool_info_text4.setText("")
            return

        print("Updating tool info for:", tool.name)

        tool_type = tool.tool_type
        self.tool_name_text.setText(f"Tool: {tool.name}")

        # Tool-specific information
        if tool_type == ToolType.GUN:
            # Gun: show damage and fire rate
            damage = getattr(tool, "damage_per_shot", 0)
            fire_rate = getattr(tool, "fire_rate", 0)
            bullets = getattr(tool, "bullets_fired", 0)
            self.tool_info_text.setText(
                f"Damage: {int(damage)}  Fire Rate: {fire_rate:.2f}s"
            )
            self.tool_info_text2.setText(f"Bullets Fired: {bullets}")
            self.tool_info_text3.setText("")
            self.tool_info_text4.setText("")

        elif tool_type == ToolType.BUILDING:
            # Building tool: show building type, size, and controls
            building_type = getattr(tool, "current_placement_type", 1)

            width = getattr(tool, "building_width", 0)
            depth = getattr(tool, "building_depth", 0)
            height = getattr(tool, "building_height", 0)

            building_types = getattr(tool, "placement_types", {})

            type_name = building_types.get(building_type, {}).get("name", "Unknown")
            snap_to_grid = getattr(tool, "snap_to_grid", False)

            self.tool_info_text.setText(f"Type: {type_name}")
            self.tool_info_text2.setText(
                f"Size: {width:.0f}x{depth:.0f}x{height:.0f} | Grid: {'ON' if snap_to_grid else 'OFF'}"
            )
            self.tool_info_text3.setText("LClick:Place RClick:Rotate MClick:Grid")
            self.tool_info_text4.setText("Scroll:Width [/]:Height 1-4:Type")

        elif tool_type == ToolType.TERRAIN:
            # Terrain tool: show mode and radius
            mode = getattr(tool, "mode", "Unknown")
            radius = getattr(tool, "radius", 0)
            strength = getattr(tool, "strength", 0)
            self.tool_info_text.setText(f"Mode: {mode}")
            self.tool_info_text2.setText(
                f"Radius: {radius:.1f}  Strength: {strength:.1f}"
            )
            self.tool_info_text3.setText("")
            self.tool_info_text4.setText("")

        elif tool_type == ToolType.CROWBAR:
            # Crowbar: show damage
            damage = getattr(tool, "damage_per_hit", 0)
            self.tool_info_text.setText(f"Damage: {int(damage)}")
            self.tool_info_text2.setText("Melee weapon")
            self.tool_info_text3.setText("")
            self.tool_info_text4.setText("")

        elif tool_type == ToolType.FIST:
            # Fist: show damage
            damage = getattr(tool, "damage_per_hit", 0)
            self.tool_info_text.setText(f"Damage: {int(damage)}")
            self.tool_info_text2.setText("Melee weapon")
            self.tool_info_text3.setText("")
            self.tool_info_text4.setText("")

        else:
            # Default: just show tool name
            self.tool_info_text.setText("")
            self.tool_info_text2.setText("")
            self.tool_info_text3.setText("")
            self.tool_info_text4.setText("")
