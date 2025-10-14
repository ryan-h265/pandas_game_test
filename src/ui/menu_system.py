"""Menu system for pause menu, settings, and game options."""

from direct.gui.DirectGui import (
    DirectFrame,
    DirectButton,
    DirectLabel,
    DirectSlider,
    DirectCheckButton,
    DGG,
)
from panda3d.core import TextNode, TransparencyAttrib
from config.settings import RENDER_DISTANCE, TERRAIN_RESOLUTION


class MenuSystem:
    """Manages game menus including pause menu and settings."""

    def __init__(self, game):
        """Initialize the menu system.

        Args:
            game: Reference to the main Game instance
        """
        self.game = game
        self.is_paused = False
        self.active_menu = None

        # Menu colors
        self.bg_color = (0.1, 0.1, 0.15, 0.95)
        self.button_color = (0.2, 0.25, 0.3, 1)
        self.button_hover = (0.3, 0.35, 0.4, 1)
        self.text_color = (1, 1, 1, 1)
        self.accent_color = (0.4, 0.6, 0.8, 1)

        # Settings state (initialize BEFORE creating menus)
        self.settings = {
            'mouse_sensitivity': 0.2,
            'fov': 75,
            'shadows_enabled': False,
            'post_processing_enabled': True,
            'show_fps': True,
            'vsync_enabled': True,
        }

        # Load current settings from game
        self.sync_settings_from_game()

        # Create menus (initially hidden)
        self.create_pause_menu()
        self.create_settings_menu()

    def sync_settings_from_game(self):
        """Sync settings values from the game state."""
        # Use hasattr to safely check if attributes exist (they may not during initialization)
        if hasattr(self.game, 'shadows_enabled'):
            self.settings['shadows_enabled'] = self.game.shadows_enabled
        if hasattr(self.game, 'post_process') and hasattr(self.game.post_process, 'enabled'):
            self.settings['post_processing_enabled'] = self.game.post_process.enabled
        if hasattr(self.game, 'camera_controller') and hasattr(self.game.camera_controller, 'mouse_sensitivity'):
            self.settings['mouse_sensitivity'] = self.game.camera_controller.mouse_sensitivity

    def create_pause_menu(self):
        """Create the pause menu UI."""
        # Semi-transparent background overlay
        self.pause_bg = DirectFrame(
            frameColor=self.bg_color,
            frameSize=(-1.5, 1.5, -1, 1),
            sortOrder=10,
        )
        self.pause_bg.setTransparency(TransparencyAttrib.MAlpha)
        self.pause_bg.hide()

        # Title
        self.pause_title = DirectLabel(
            text="PAUSED",
            text_scale=0.15,
            text_fg=self.text_color,
            text_font=None,
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.6),
            parent=self.pause_bg,
        )

        # Buttons
        button_spacing = 0.15
        button_start_y = 0.2

        self.resume_button = DirectButton(
            text="Resume",
            text_scale=0.08,
            text_fg=self.text_color,
            frameColor=self.button_color,
            frameSize=(-0.4, 0.4, -0.06, 0.06),
            pos=(0, 0, button_start_y),
            command=self.resume_game,
            parent=self.pause_bg,
            rolloverSound=None,
            clickSound=None,
            relief=DGG.FLAT,
        )
        self.resume_button['frameColor'] = self.button_color
        self.resume_button.bind(DGG.ENTER, self.on_button_hover, [self.resume_button])
        self.resume_button.bind(DGG.EXIT, self.on_button_exit, [self.resume_button])

        self.settings_button = DirectButton(
            text="Settings",
            text_scale=0.08,
            text_fg=self.text_color,
            frameColor=self.button_color,
            frameSize=(-0.4, 0.4, -0.06, 0.06),
            pos=(0, 0, button_start_y - button_spacing),
            command=self.show_settings,
            parent=self.pause_bg,
            rolloverSound=None,
            clickSound=None,
            relief=DGG.FLAT,
        )
        self.settings_button.bind(DGG.ENTER, self.on_button_hover, [self.settings_button])
        self.settings_button.bind(DGG.EXIT, self.on_button_exit, [self.settings_button])

        self.quit_button = DirectButton(
            text="Quit to Desktop",
            text_scale=0.08,
            text_fg=self.text_color,
            frameColor=self.button_color,
            frameSize=(-0.4, 0.4, -0.06, 0.06),
            pos=(0, 0, button_start_y - button_spacing * 2),
            command=self.quit_to_desktop,
            parent=self.pause_bg,
            rolloverSound=None,
            clickSound=None,
            relief=DGG.FLAT,
        )
        self.quit_button.bind(DGG.ENTER, self.on_button_hover, [self.quit_button])
        self.quit_button.bind(DGG.EXIT, self.on_button_exit, [self.quit_button])

        # Controls reminder
        self.controls_label = DirectLabel(
            text="Press ESC to resume",
            text_scale=0.05,
            text_fg=(0.7, 0.7, 0.7, 1),
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, -0.7),
            parent=self.pause_bg,
        )

    def create_settings_menu(self):
        """Create the settings menu UI."""
        # Background
        self.settings_bg = DirectFrame(
            frameColor=self.bg_color,
            frameSize=(-1.5, 1.5, -1, 1),
            sortOrder=11,
        )
        self.settings_bg.setTransparency(TransparencyAttrib.MAlpha)
        self.settings_bg.hide()

        # Title
        self.settings_title = DirectLabel(
            text="SETTINGS",
            text_scale=0.12,
            text_fg=self.text_color,
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.7),
            parent=self.settings_bg,
        )

        # Settings controls
        y_pos = 0.45
        spacing = 0.15

        # Mouse Sensitivity
        DirectLabel(
            text="Mouse Sensitivity:",
            text_scale=0.06,
            text_fg=self.text_color,
            text_align=TextNode.ARight,
            frameColor=(0, 0, 0, 0),
            pos=(-0.6, 0, y_pos),
            parent=self.settings_bg,
        )
        self.sensitivity_slider = DirectSlider(
            range=(0.05, 0.5),
            value=self.settings['mouse_sensitivity'],
            pageSize=0.05,
            scale=0.5,
            pos=(0.2, 0, y_pos),
            command=self.on_sensitivity_change,
            parent=self.settings_bg,
        )
        self.sensitivity_value_label = DirectLabel(
            text=f"{self.settings['mouse_sensitivity']:.2f}",
            text_scale=0.06,
            text_fg=self.accent_color,
            frameColor=(0, 0, 0, 0),
            pos=(0.7, 0, y_pos),
            parent=self.settings_bg,
        )

        y_pos -= spacing

        # Shadows Toggle
        DirectLabel(
            text="Shadows:",
            text_scale=0.06,
            text_fg=self.text_color,
            text_align=TextNode.ARight,
            frameColor=(0, 0, 0, 0),
            pos=(-0.6, 0, y_pos),
            parent=self.settings_bg,
        )
        self.shadows_checkbox = DirectCheckButton(
            text="",
            scale=0.08,
            pos=(0.0, 0, y_pos),
            command=self.on_shadows_toggle,
            parent=self.settings_bg,
            boxPlacement="center",
            indicatorValue=self.settings['shadows_enabled'],
        )
        self.shadows_status_label = DirectLabel(
            text="ON" if self.settings['shadows_enabled'] else "OFF",
            text_scale=0.06,
            text_fg=self.accent_color,
            frameColor=(0, 0, 0, 0),
            pos=(0.3, 0, y_pos),
            parent=self.settings_bg,
        )

        y_pos -= spacing

        # Post-Processing Toggle
        DirectLabel(
            text="Post-Processing:",
            text_scale=0.06,
            text_fg=self.text_color,
            text_align=TextNode.ARight,
            frameColor=(0, 0, 0, 0),
            pos=(-0.6, 0, y_pos),
            parent=self.settings_bg,
        )
        self.post_process_checkbox = DirectCheckButton(
            text="",
            scale=0.08,
            pos=(0.0, 0, y_pos),
            command=self.on_post_process_toggle,
            parent=self.settings_bg,
            boxPlacement="center",
            indicatorValue=self.settings['post_processing_enabled'],
        )
        self.post_process_status_label = DirectLabel(
            text="ON" if self.settings['post_processing_enabled'] else "OFF",
            text_scale=0.06,
            text_fg=self.accent_color,
            frameColor=(0, 0, 0, 0),
            pos=(0.3, 0, y_pos),
            parent=self.settings_bg,
        )

        y_pos -= spacing

        # Show FPS Toggle
        DirectLabel(
            text="Show FPS:",
            text_scale=0.06,
            text_fg=self.text_color,
            text_align=TextNode.ARight,
            frameColor=(0, 0, 0, 0),
            pos=(-0.6, 0, y_pos),
            parent=self.settings_bg,
        )
        self.fps_checkbox = DirectCheckButton(
            text="",
            scale=0.08,
            pos=(0.0, 0, y_pos),
            command=self.on_fps_toggle,
            parent=self.settings_bg,
            boxPlacement="center",
            indicatorValue=self.settings['show_fps'],
        )
        self.fps_status_label = DirectLabel(
            text="ON" if self.settings['show_fps'] else "OFF",
            text_scale=0.06,
            text_fg=self.accent_color,
            frameColor=(0, 0, 0, 0),
            pos=(0.3, 0, y_pos),
            parent=self.settings_bg,
        )

        # Info text
        info_y = -0.3
        DirectLabel(
            text="Game Information:",
            text_scale=0.07,
            text_fg=self.accent_color,
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, info_y),
            parent=self.settings_bg,
        )
        info_y -= 0.1
        DirectLabel(
            text=f"Render Distance: {RENDER_DISTANCE} chunks",
            text_scale=0.05,
            text_fg=(0.8, 0.8, 0.8, 1),
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, info_y),
            parent=self.settings_bg,
        )
        info_y -= 0.08
        DirectLabel(
            text=f"Terrain Resolution: {TERRAIN_RESOLUTION}x{TERRAIN_RESOLUTION}",
            text_scale=0.05,
            text_fg=(0.8, 0.8, 0.8, 1),
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, info_y),
            parent=self.settings_bg,
        )

        # Back button
        self.back_button = DirectButton(
            text="Back",
            text_scale=0.08,
            text_fg=self.text_color,
            frameColor=self.button_color,
            frameSize=(-0.3, 0.3, -0.06, 0.06),
            pos=(0, 0, -0.7),
            command=self.hide_settings,
            parent=self.settings_bg,
            rolloverSound=None,
            clickSound=None,
            relief=DGG.FLAT,
        )
        self.back_button.bind(DGG.ENTER, self.on_button_hover, [self.back_button])
        self.back_button.bind(DGG.EXIT, self.on_button_exit, [self.back_button])

    def on_button_hover(self, button, event):
        """Handle button hover effect."""
        button['frameColor'] = self.button_hover

    def on_button_exit(self, button, event):
        """Handle button exit (unhover) effect."""
        button['frameColor'] = self.button_color

    def on_sensitivity_change(self):
        """Handle mouse sensitivity slider change."""
        value = self.sensitivity_slider['value']
        self.settings['mouse_sensitivity'] = value
        self.sensitivity_value_label['text'] = f"{value:.2f}"

        # Apply to game
        if hasattr(self.game.camera_controller, 'mouse_sensitivity'):
            self.game.camera_controller.mouse_sensitivity = value

    def on_shadows_toggle(self, checked):
        """Handle shadows checkbox toggle."""
        self.settings['shadows_enabled'] = self.shadows_checkbox['indicatorValue']
        self.shadows_status_label['text'] = "ON" if self.settings['shadows_enabled'] else "OFF"

        # Apply to game
        if hasattr(self.game, 'shadows_enabled') and self.settings['shadows_enabled'] != self.game.shadows_enabled:
            self.game.toggle_shadows()

    def on_post_process_toggle(self, checked):
        """Handle post-processing checkbox toggle."""
        self.settings['post_processing_enabled'] = self.post_process_checkbox['indicatorValue']
        self.post_process_status_label['text'] = "ON" if self.settings['post_processing_enabled'] else "OFF"

        # Apply to game
        if hasattr(self.game, 'post_process') and hasattr(self.game.post_process, 'enabled'):
            if self.settings['post_processing_enabled'] != self.game.post_process.enabled:
                self.game.toggle_post_process()

    def on_fps_toggle(self, checked):
        """Handle FPS display checkbox toggle."""
        self.settings['show_fps'] = self.fps_checkbox['indicatorValue']
        self.fps_status_label['text'] = "ON" if self.settings['show_fps'] else "OFF"

        # Apply to game
        if self.settings['show_fps']:
            self.game.hud.fps_text.show()
        else:
            self.game.hud.fps_text.hide()

    def toggle_pause(self):
        """Toggle pause state."""
        if self.is_paused:
            self.resume_game()
        else:
            self.pause_game()

    def pause_game(self):
        """Pause the game and show pause menu."""
        if self.is_paused:
            return

        self.is_paused = True
        self.active_menu = 'pause'

        # Release mouse cursor
        if self.game.mouse_captured:
            self.game.toggle_mouse()

        # Show pause menu
        self.pause_bg.show()

        # Hide HUD elements while paused
        if hasattr(self.game, 'hud'):
            self.game.hud.tool_text.hide()
            self.game.hud.message_text.hide()

        # Hide crosshair
        if hasattr(self.game, 'crosshair_manager'):
            self.game.crosshair_manager.hide_crosshair()

        print("Game paused")

    def resume_game(self):
        """Resume the game from pause."""
        if not self.is_paused:
            return

        self.is_paused = False
        self.active_menu = None

        # Hide all menus
        self.pause_bg.hide()
        self.settings_bg.hide()

        # Capture mouse cursor again
        if not self.game.mouse_captured:
            self.game.toggle_mouse()

        # Show HUD elements
        if hasattr(self.game, 'hud'):
            self.game.hud.tool_text.show()
            self.game.hud.message_text.show()

        # Show crosshair
        if hasattr(self.game, 'crosshair_manager') and hasattr(self.game, 'tool_manager'):
            active_tool = self.game.tool_manager.get_active_tool()
            if active_tool:
                # Use the tool_type enum value as the crosshair type string
                self.game.crosshair_manager.show_crosshair(active_tool.tool_type.value)

        print("Game resumed")

    def show_settings(self):
        """Show the settings menu."""
        self.active_menu = 'settings'
        self.pause_bg.hide()
        self.settings_bg.show()

    def hide_settings(self):
        """Hide the settings menu and return to pause menu."""
        self.active_menu = 'pause'
        self.settings_bg.hide()
        self.pause_bg.show()

    def quit_to_desktop(self):
        """Quit the game."""
        print("Quitting to desktop...")
        self.game.quit_game()

    def cleanup(self):
        """Clean up menu resources."""
        if self.pause_bg:
            self.pause_bg.destroy()
        if self.settings_bg:
            self.settings_bg.destroy()
