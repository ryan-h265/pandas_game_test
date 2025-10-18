"""Central menu state management."""

from testgame.menus.menu_theme import MenuTheme
from testgame.menus.pause_menu import PauseMenu
from testgame.menus.start_menu import StartMenu


class MenuManager:
    """Manages all game menus (start, pause, settings, save/load)."""

    def __init__(self, game):
        """Initialize menu manager.

        Args:
            game: Reference to main Game instance
        """
        self.game = game
        self.is_paused = False
        self.active_menu = None

        # Use modern theme
        self.theme = MenuTheme
        self.bg_color = self.theme.get_color("bg_primary")
        self.button_color = self.theme.get_color("button_default")
        self.button_hover = self.theme.get_color("button_hover")
        self.text_color = self.theme.get_color("text_primary")
        self.accent_color = self.theme.get_color("accent_primary")

        # Create menus (defer pause menu creation until after game init)
        self.start_menu = StartMenu(self)
        self.pause_menu = None

    def init_pause_menu(self):
        """Initialize pause menu after game is fully set up."""
        if self.pause_menu is None:
            self.pause_menu = PauseMenu(self)

    def show_start_menu(self):
        """Show the start/level selection menu."""
        self.active_menu = "start"
        self.is_paused = True
        self.start_menu.show()

    def hide_start_menu(self):
        """Hide the start menu and unpause game."""
        self.active_menu = None
        self.is_paused = False
        self.start_menu.hide()

    def toggle_pause(self):
        """Toggle pause state."""
        if self.is_paused:
            self.resume()
        else:
            self.pause()

    def pause(self):
        """Pause the game and show pause menu."""
        if self.is_paused or self.pause_menu is None:
            return

        self.is_paused = True
        self.active_menu = "pause"

        # Release mouse cursor
        if self.game.mouse_captured:
            self.game.toggle_mouse()

        self.pause_menu.show()

        # Hide HUD
        self._hide_hud()
        print("Game paused")

    def resume(self):
        """Resume from pause."""
        if not self.is_paused or self.active_menu == "start":
            return

        self.is_paused = False
        self.active_menu = None

        if self.pause_menu:
            self.pause_menu.hide()

        # Capture mouse again
        if not self.game.mouse_captured:
            self.game.toggle_mouse()

        # Show HUD
        self._show_hud()
        print("Game resumed")

    def _hide_hud(self):
        """Hide HUD elements while paused."""
        if hasattr(self.game, "hud"):
            self.game.hud.tool_text.hide()
            self.game.hud.message_text.hide()
        if hasattr(self.game, "crosshair_manager"):
            self.game.crosshair_manager.hide_crosshair()

    def _show_hud(self):
        """Show HUD elements on resume."""
        if hasattr(self.game, "hud"):
            self.game.hud.tool_text.show()
            self.game.hud.message_text.show()
        if hasattr(self.game, "crosshair_manager") and hasattr(
            self.game, "tool_manager"
        ):
            active_tool = self.game.tool_manager.get_active_tool()
            if active_tool:
                self.game.crosshair_manager.show_crosshair(active_tool.view_model_name)

    def cleanup(self):
        """Clean up menu resources."""
        self.start_menu.cleanup()
        if self.pause_menu:
            self.pause_menu.cleanup()
