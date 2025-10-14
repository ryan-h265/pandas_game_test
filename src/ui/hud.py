"""HUD (Heads-Up Display) implementation."""

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode


class HUD:
    """Manages the in-game heads-up display."""

    def __init__(self):
        self.visible = True
        self.elements = []

        # Tool display text (top-right)
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

        # Crosshair (center)
        self.crosshair = OnscreenText(
            text="+",
            pos=(0, 0),
            scale=0.06,
            fg=(1, 1, 1, 0.8),
            align=TextNode.ACenter,
            mayChange=False,
        )

    def show(self):
        """Show the HUD."""
        self.visible = True

    def hide(self):
        """Hide the HUD."""
        self.visible = False

    def update(self, dt):
        """Update HUD elements.

        Args:
            dt: Delta time since last update
        """
        # Update message timer
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message_text.setText("")

    def set_tool_name(self, tool_name):
        """Update tool display.

        Args:
            tool_name: Name of current tool
        """
        self.tool_text.setText(f"Tool: {tool_name}")

    def show_message(self, message):
        """Display a temporary message.

        Args:
            message: Message text to display
        """
        self.message_text.setText(message)
        self.message_timer = self.message_duration

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
