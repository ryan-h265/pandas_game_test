"""Pause menu and settings."""

from direct.gui.DirectGui import (
    DirectFrame,
    DirectButton,
    DirectLabel,
    DirectSlider,
    DirectCheckButton,
    DGG,
)
from panda3d.core import TextNode, TransparencyAttrib
from testgame.config.settings import RENDER_DISTANCE, TERRAIN_RESOLUTION
from testgame.menus.menu_theme import MenuTheme, apply_menu_styling
from testgame.menus.base_menu import BaseMenu


class PauseMenu(BaseMenu):
    """Pause menu with settings, save/load."""

    def __init__(self, menu_manager):
        """Initialize pause menu.

        Args:
            menu_manager: Reference to MenuManager
        """
        super().__init__(menu_manager.game)
        self.menu_manager = menu_manager

        # Settings state
        self.settings = {
            "mouse_sensitivity": 0.2,
            "fov": 75,
            "shadows_enabled": False,
            "post_processing_enabled": True,
            "show_fps": True,
            "vsync_enabled": True,
        }
        self._sync_from_game()

        # Create menus
        self._create_pause_bg()
        self._create_settings_menu()
        self._create_save_menu()
        self._create_load_menu()

    def _sync_from_game(self):
        """Sync current settings from game state."""
        if hasattr(self.game, "shadows_enabled"):
            self.settings["shadows_enabled"] = self.game.shadows_enabled
        if hasattr(self.game, "post_process") and hasattr(
            self.game.post_process, "enabled"
        ):
            self.settings["post_processing_enabled"] = self.game.post_process.enabled
        if hasattr(self.game, "camera_controller") and hasattr(
            self.game.camera_controller, "mouse_sensitivity"
        ):
            self.settings["mouse_sensitivity"] = (
                self.game.camera_controller.mouse_sensitivity
            )

    def _create_pause_bg(self):
        """Create main pause menu."""
        # Background with theme
        frame_style = MenuTheme.get_frame_style("primary")
        self.pause_bg = DirectFrame(
            frameColor=frame_style["frameColor"],
            frameSize=frame_style["frameSize"],
            sortOrder=10,
        )
        self.pause_bg.setTransparency(TransparencyAttrib.MAlpha)
        self.pause_bg.hide()

        # Add pika logo to top left
        self._add_pika_logo(self.pause_bg)

        # Title with theme
        # title_style = MenuTheme.get_font_settings("title")
        # DirectLabel(
        #     text="PAUSED",
        #     text_scale=title_style["scale"],
        #     text_fg=title_style["fg"],
        #     frameColor=(0, 0, 0, 0),
        #     pos=(0, 0, 0.6),
        #     parent=self.pause_bg,
        # )

        buttons = [
            ("Resume", self.menu_manager.resume, 0.35),
            ("Save Game", self._show_save_menu, 0.2),
            ("Load Game", self._show_load_menu, 0.05),
            ("Settings", self._show_settings_menu, -0.1),
            ("Main Menu", self._return_to_main_menu, -0.25),
            ("Quit to Desktop", self.game.quit_game, -0.40),
        ]

        for text, cmd, y in buttons:
            btn = DirectButton(
                text=text,
                text_pos=(0, -0.02),
                frameSize=(-0.40, 0.40, -0.07, 0.07),
                pos=(0, 0, y),
                command=cmd,
                parent=self.pause_bg,
                rolloverSound=None,
                clickSound=None,
                relief=DGG.FLAT,
            )
            apply_menu_styling(btn, "button", size="medium")
            btn.bind(DGG.ENTER, self._on_hover, [btn])
            btn.bind(DGG.EXIT, self._on_unhover, [btn])

        DirectLabel(
            text="Press ESC to resume",
            text_scale=0.05,
            text_fg=(0.7, 0.7, 0.7, 1),
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, -0.7),
            parent=self.pause_bg,
        )

    def _create_settings_menu(self):
        """Create settings submenu."""
        # Background with theme
        frame_style = MenuTheme.get_frame_style("primary")
        self.settings_bg = DirectFrame(
            frameColor=frame_style["frameColor"],
            frameSize=frame_style["frameSize"],
            sortOrder=11,
        )
        self.settings_bg.setTransparency(TransparencyAttrib.MAlpha)
        self.settings_bg.hide()

        # Title with theme
        title_style = MenuTheme.get_font_settings("title")
        DirectLabel(
            text="SETTINGS",
            text_scale=title_style["scale"],
            text_fg=title_style["fg"],
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.7),
            parent=self.settings_bg,
        )

        y_pos = 0.45
        spacing = 0.15
        label_style = MenuTheme.get_font_settings("label")

        # Mouse Sensitivity
        DirectLabel(
            text="Mouse Sensitivity:",
            text_scale=label_style["scale"],
            text_fg=label_style["fg"],
            text_align=TextNode.ARight,
            frameColor=(0, 0, 0, 0),
            pos=(-0.6, 0, y_pos),
            parent=self.settings_bg,
        )
        self.sensitivity_slider = DirectSlider(
            range=(0.05, 0.5),
            value=self.settings["mouse_sensitivity"],
            pageSize=0.05,
            scale=0.5,
            pos=(0.2, 0, y_pos),
            command=self._on_sensitivity_change,
            parent=self.settings_bg,
        )
        self.sensitivity_value_label = DirectLabel(
            text=f"{self.settings['mouse_sensitivity']:.2f}",
            text_scale=label_style["scale"],
            text_fg=MenuTheme.get_color("accent_primary"),
            frameColor=(0, 0, 0, 0),
            pos=(0.7, 0, y_pos),
            parent=self.settings_bg,
        )

        y_pos -= spacing

        # Shadows Toggle
        DirectLabel(
            text="Shadows:",
            text_scale=label_style["scale"],
            text_fg=label_style["fg"],
            text_align=TextNode.ARight,
            frameColor=(0, 0, 0, 0),
            pos=(-0.6, 0, y_pos),
            parent=self.settings_bg,
        )
        self.shadows_checkbox = DirectCheckButton(
            text="",
            scale=0.08,
            pos=(0.0, 0, y_pos),
            command=self._on_shadows_toggle,
            parent=self.settings_bg,
            boxPlacement="center",
            indicatorValue=self.settings["shadows_enabled"],
        )
        self.shadows_status_label = DirectLabel(
            text="ON" if self.settings["shadows_enabled"] else "OFF",
            text_scale=0.06,
            text_fg=self.menu_manager.accent_color,
            frameColor=(0, 0, 0, 0),
            pos=(0.3, 0, y_pos),
            parent=self.settings_bg,
        )

        y_pos -= spacing

        # Post-Processing Toggle
        DirectLabel(
            text="Post-Processing:",
            text_scale=0.06,
            text_fg=self.menu_manager.text_color,
            text_align=TextNode.ARight,
            frameColor=(0, 0, 0, 0),
            pos=(-0.6, 0, y_pos),
            parent=self.settings_bg,
        )
        self.post_process_checkbox = DirectCheckButton(
            text="",
            scale=0.08,
            pos=(0.0, 0, y_pos),
            command=self._on_post_process_toggle,
            parent=self.settings_bg,
            boxPlacement="center",
            indicatorValue=self.settings["post_processing_enabled"],
        )
        self.post_process_status_label = DirectLabel(
            text="ON" if self.settings["post_processing_enabled"] else "OFF",
            text_scale=0.06,
            text_fg=self.menu_manager.accent_color,
            frameColor=(0, 0, 0, 0),
            pos=(0.3, 0, y_pos),
            parent=self.settings_bg,
        )

        y_pos -= spacing

        # Show FPS Toggle
        DirectLabel(
            text="Show FPS:",
            text_scale=0.06,
            text_fg=self.menu_manager.text_color,
            text_align=TextNode.ARight,
            frameColor=(0, 0, 0, 0),
            pos=(-0.6, 0, y_pos),
            parent=self.settings_bg,
        )
        self.fps_checkbox = DirectCheckButton(
            text="",
            scale=0.08,
            pos=(0.0, 0, y_pos),
            command=self._on_fps_toggle,
            parent=self.settings_bg,
            boxPlacement="center",
            indicatorValue=self.settings["show_fps"],
        )
        self.fps_status_label = DirectLabel(
            text="ON" if self.settings["show_fps"] else "OFF",
            text_scale=0.06,
            text_fg=self.menu_manager.accent_color,
            frameColor=(0, 0, 0, 0),
            pos=(0.3, 0, y_pos),
            parent=self.settings_bg,
        )

        # Info text
        info_y = -0.3
        DirectLabel(
            text="Game Information:",
            text_scale=0.07,
            text_fg=self.menu_manager.accent_color,
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

        # Back button with theme
        back_btn = DirectButton(
            text="Back",
            frameSize=(-0.30, 0.30, -0.07, 0.07),
            pos=(0, 0, -0.7),
            command=self._show_pause_menu,
            parent=self.settings_bg,
            rolloverSound=None,
            clickSound=None,
            relief=DGG.FLAT,
        )
        apply_menu_styling(back_btn, "button", size="small")
        back_btn.bind(DGG.ENTER, self._on_hover, [back_btn])
        back_btn.bind(DGG.EXIT, self._on_unhover, [back_btn])

    def _create_save_menu(self):
        """Create save game submenu."""
        # Background with theme
        frame_style = MenuTheme.get_frame_style("primary")
        self.save_bg = DirectFrame(
            frameColor=frame_style["frameColor"],
            frameSize=frame_style["frameSize"],
            sortOrder=11,
        )
        self.save_bg.setTransparency(TransparencyAttrib.MAlpha)
        self.save_bg.hide()

        DirectLabel(
            text="SAVE GAME",
            text_scale=0.12,
            text_fg=self.menu_manager.text_color,
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.7),
            parent=self.save_bg,
        )

        y_pos = 0.4
        spacing = 0.15

        save_slots = [
            ("Quick Save", "quicksave"),
            ("Save Slot 1", "save_slot_1"),
            ("Save Slot 2", "save_slot_2"),
            ("Save Slot 3", "save_slot_3"),
        ]

        for text, key in save_slots:
            btn = DirectButton(
                text=text,
                text_scale=0.07,
                text_fg=self.menu_manager.text_color,
                frameColor=self.menu_manager.button_color,
                frameSize=(-0.5, 0.5, -0.06, 0.06),
                pos=(0, 0, y_pos),
                command=self._on_save_slot,
                extraArgs=[key],
                parent=self.save_bg,
                rolloverSound=None,
                clickSound=None,
                relief=DGG.FLAT,
            )
            btn.bind(DGG.ENTER, self._on_hover, [btn])
            btn.bind(DGG.EXIT, self._on_unhover, [btn])
            y_pos -= spacing

        self.save_info_label = DirectLabel(
            text="Select a slot to save",
            text_scale=0.05,
            text_fg=(0.7, 0.7, 0.7, 1),
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, -0.3),
            parent=self.save_bg,
        )

        back_btn = DirectButton(
            text="Back",
            text_scale=0.08,
            text_fg=self.menu_manager.text_color,
            frameColor=self.menu_manager.button_color,
            frameSize=(-0.3, 0.3, -0.06, 0.06),
            pos=(0, 0, -0.7),
            command=self._show_pause_menu,
            parent=self.save_bg,
            rolloverSound=None,
            clickSound=None,
            relief=DGG.FLAT,
        )
        back_btn.bind(DGG.ENTER, self._on_hover, [back_btn])
        back_btn.bind(DGG.EXIT, self._on_unhover, [back_btn])

    def _create_load_menu(self):
        """Create load game submenu."""
        self.load_bg = DirectFrame(
            frameColor=self.menu_manager.bg_color,
            frameSize=(-1.5, 1.5, -1, 1),
            sortOrder=11,
        )
        self.load_bg.setTransparency(TransparencyAttrib.MAlpha)
        self.load_bg.hide()

        DirectLabel(
            text="LOAD GAME",
            text_scale=0.12,
            text_fg=self.menu_manager.text_color,
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.7),
            parent=self.load_bg,
        )

        y_pos = 0.4
        spacing = 0.15

        load_slots = [
            ("Quick Load", "quicksave"),
            ("Load Slot 1", "save_slot_1"),
            ("Load Slot 2", "save_slot_2"),
            ("Load Slot 3", "save_slot_3"),
        ]

        self.load_info_labels = {}
        for text, key in load_slots:
            btn = DirectButton(
                text=text,
                text_scale=0.07,
                text_fg=self.menu_manager.text_color,
                frameColor=self.menu_manager.button_color,
                frameSize=(-0.5, 0.5, -0.06, 0.06),
                pos=(0, 0, y_pos),
                command=self._on_load_slot,
                extraArgs=[key],
                parent=self.load_bg,
                rolloverSound=None,
                clickSound=None,
                relief=DGG.FLAT,
            )
            btn.bind(DGG.ENTER, self._on_hover, [btn])
            btn.bind(DGG.EXIT, self._on_unhover, [btn])

            # Info label for each slot
            info_label = DirectLabel(
                text="",
                text_scale=0.04,
                text_fg=(0.7, 0.7, 0.7, 1),
                frameColor=(0, 0, 0, 0),
                pos=(0, 0, y_pos - 0.08),
                parent=self.load_bg,
            )
            self.load_info_labels[key] = info_label

            y_pos -= spacing

        self.load_status_label = DirectLabel(
            text="Select a slot to load",
            text_scale=0.05,
            text_fg=(0.7, 0.7, 0.7, 1),
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, -0.3),
            parent=self.load_bg,
        )

        back_btn = DirectButton(
            text="Back",
            text_scale=0.08,
            text_fg=self.menu_manager.text_color,
            frameColor=self.menu_manager.button_color,
            frameSize=(-0.3, 0.3, -0.06, 0.06),
            pos=(0, 0, -0.7),
            command=self._show_pause_menu,
            parent=self.load_bg,
            rolloverSound=None,
            clickSound=None,
            relief=DGG.FLAT,
        )
        back_btn.bind(DGG.ENTER, self._on_hover, [back_btn])
        back_btn.bind(DGG.EXIT, self._on_unhover, [back_btn])

    def _on_sensitivity_change(self):
        """Handle sensitivity slider change."""
        value = self.sensitivity_slider["value"]
        self.settings["mouse_sensitivity"] = value
        self.sensitivity_value_label["text"] = f"{value:.2f}"
        if hasattr(self.game.camera_controller, "mouse_sensitivity"):
            self.game.camera_controller.mouse_sensitivity = value

    def _on_shadows_toggle(self, checked):
        """Handle shadows toggle."""
        self.settings["shadows_enabled"] = self.shadows_checkbox["indicatorValue"]
        self.shadows_status_label["text"] = (
            "ON" if self.settings["shadows_enabled"] else "OFF"
        )
        if (
            hasattr(self.game, "shadows_enabled")
            and self.settings["shadows_enabled"] != self.game.shadows_enabled
        ):
            self.game.toggle_shadows()

    def _on_post_process_toggle(self, checked):
        """Handle post-processing toggle."""
        self.settings["post_processing_enabled"] = self.post_process_checkbox[
            "indicatorValue"
        ]
        self.post_process_status_label["text"] = (
            "ON" if self.settings["post_processing_enabled"] else "OFF"
        )
        if hasattr(self.game, "post_process") and hasattr(
            self.game.post_process, "enabled"
        ):
            if (
                self.settings["post_processing_enabled"]
                != self.game.post_process.enabled
            ):
                self.game.toggle_post_process()

    def _on_fps_toggle(self, checked):
        """Handle FPS toggle."""
        self.settings["show_fps"] = self.fps_checkbox["indicatorValue"]
        self.fps_status_label["text"] = "ON" if self.settings["show_fps"] else "OFF"
        if self.settings["show_fps"]:
            self.game.hud.fps_text.show()
        else:
            self.game.hud.fps_text.hide()

    def _on_save_slot(self, save_key):
        """Save to slot."""
        metadata = {"title": f"Save {save_key}"}
        success = self.game.game_world.save_to_file(
            save_key, self.game.player, metadata
        )
        self.save_info_label["text"] = "Saved!" if success else "Save failed!"
        self.save_info_label["text_fg"] = (
            (0.5, 1.0, 0.5, 1) if success else (1.0, 0.5, 0.5, 1)
        )

    def _on_load_slot(self, save_key):
        """Load from slot."""
        success = self.game.game_world.load_from_file(save_key, self.game.player)
        self.load_status_label["text"] = "Loaded!" if success else "Load failed!"
        self.load_status_label["text_fg"] = (
            (0.5, 1.0, 0.5, 1) if success else (1.0, 0.5, 0.5, 1)
        )
        if success:
            self.game.taskMgr.doMethodLater(
                1.0, lambda task: self.menu_manager.resume(), "resume_after_load"
            )

    def _update_load_info(self):
        """Update load slot info labels."""
        import os
        from datetime import datetime

        for save_key, info_label in self.load_info_labels.items():
            save_path = self.game.game_world.serializer.get_save_path(save_key)
            if save_path.exists():
                mtime = os.path.getmtime(save_path)
                time_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                info_label["text"] = f"Saved: {time_str}"
                info_label["text_fg"] = (0.7, 1.0, 0.7, 1)
            else:
                info_label["text"] = "Empty Slot"
                info_label["text_fg"] = (0.7, 0.7, 0.7, 1)

    def _show_pause_menu(self):
        """Show main pause menu."""
        self.settings_bg.hide()
        self.save_bg.hide()
        self.load_bg.hide()
        self.pause_bg.show()

    def _show_settings_menu(self):
        """Show settings submenu."""
        self.pause_bg.hide()
        self.settings_bg.show()

    def _return_to_main_menu(self):
        """Return to main menu."""
        self.game.return_to_main_menu()

    def _show_save_menu(self):
        """Show save submenu."""
        self.pause_bg.hide()
        self.save_bg.show()

    def _show_load_menu(self):
        """Show load submenu."""
        self.pause_bg.hide()
        self.load_bg.show()
        self._update_load_info()

    def _on_hover(self, btn, event):
        """Handle button hover with enhanced visual feedback."""
        from direct.interval.IntervalGlobal import LerpScaleInterval
        
        # Change frame color to brighter hover state
        btn["frameColor"] = MenuTheme.get_color("button_hover")
        
        # Change text to brighter color
        btn["text_fg"] = (1.0, 1.0, 1.0, 1.0)  # White text on hover
        
        # Subtle scale up animation
        LerpScaleInterval(btn, 0.1, 1.05).start()

    def _on_unhover(self, btn, event):
        """Handle button unhover, reset to normal state."""
        from direct.interval.IntervalGlobal import LerpScaleInterval
        
        # Reset frame color
        btn["frameColor"] = MenuTheme.get_color("button_default")
        
        # Reset text to normal color
        button_style = MenuTheme.get_font_settings("button")
        btn["text_fg"] = button_style["fg"]
        
        # Scale back to normal
        LerpScaleInterval(btn, 0.1, 1.0).start()

    def show(self):
        """Show pause menu."""
        self.pause_bg.show()

    def hide(self):
        """Hide all pause menus."""
        self.pause_bg.hide()
        self.settings_bg.hide()
        self.save_bg.hide()
        self.load_bg.hide()

    def cleanup(self):
        """Clean up resources."""
        for bg in [self.pause_bg, self.settings_bg, self.save_bg, self.load_bg]:
            if bg:
                bg.destroy()
