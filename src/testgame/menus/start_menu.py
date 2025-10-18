"""Level selection / start menu."""

from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel, DGG
from panda3d.core import TransparencyAttrib
from testgame.config.levels import LEVELS
from testgame.menus.menu_theme import MenuTheme, apply_menu_styling
from testgame.menus.base_menu import BaseMenu


class StartMenu(BaseMenu):
    """Start menu for level selection and save loading."""

    def __init__(self, menu_manager):
        """Initialize start menu.

        Args:
            menu_manager: Reference to MenuManager
        """
        super().__init__(menu_manager.game)
        self.menu_manager = menu_manager

        # Create main menu page
        self._create_main_menu()

        # Create saves list page
        self._create_saves_page()

    def _create_main_menu(self):
        """Create the main menu page with level selection."""
        # Background with theme
        frame_style = MenuTheme.get_frame_style("primary")
        self.bg = DirectFrame(
            frameColor=frame_style["frameColor"],
            frameSize=frame_style["frameSize"],
            sortOrder=10,
        )
        self.bg.setTransparency(TransparencyAttrib.MAlpha)
        self.bg.hide()

        # Add pika logo to top left
        self._add_pika_logo(self.bg)

        # Title with theme
        title_style = MenuTheme.get_font_settings("title")
        title_font = MenuTheme.get_font_object(title_style.get("font", "Courier"))
        DirectLabel(
            text="Mt. Climber",
            text_scale=title_style["scale"],
            text_fg=title_style["fg"],
            text_font=title_font,
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.8),
            parent=self.bg,
        )

        # Create level buttons
        self._create_level_buttons()

        # Load Save button with theme
        load_save_btn = DirectButton(
            text="Load",
            text_pos=(0, -0.02),
            frameSize=(-0.50, 0.50, -0.07, 0.07),
            pos=(0, 0, -0.55),
            command=self._show_saves_page,
            parent=self.bg,
            rolloverSound=None,
            clickSound=None,
            relief=DGG.FLAT,
        )
        apply_menu_styling(load_save_btn, "button", size="large")
        load_save_btn.bind(DGG.ENTER, self._on_hover, [load_save_btn])
        load_save_btn.bind(DGG.EXIT, self._on_unhover, [load_save_btn])

        # Quit button with theme
        quit_btn = DirectButton(
            text="Quit",
            text_pos=(0, -0.02),
            frameSize=(-0.50, 0.50, -0.07, 0.07),
            pos=(0, 0, -0.7),
            command=self.on_quit,
            parent=self.bg,
            rolloverSound=None,
            clickSound=None,
            relief=DGG.FLAT,
        )
        apply_menu_styling(quit_btn, "button", size="large")
        quit_btn.bind(DGG.ENTER, self._on_hover, [quit_btn])
        quit_btn.bind(DGG.EXIT, self._on_unhover, [quit_btn])

    def _create_level_buttons(self):
        """Create buttons for each level."""
        y_pos = 0.4
        spacing = 0.2

        label_style = MenuTheme.get_font_settings("label")

        for level_key, level_info in LEVELS.items():
            btn = DirectButton(
                text=level_info["name"],
                text_pos=(0, -0.02),
                frameSize=(-0.50, 0.50, -0.07, 0.07),
                pos=(0, 0, y_pos),
                command=self.on_level_select,
                extraArgs=[level_key],
                parent=self.bg,
                rolloverSound=None,
                clickSound=None,
                relief=DGG.FLAT,
            )
            apply_menu_styling(btn, "button", size="large")
            btn.bind(DGG.ENTER, self._on_hover, [btn])
            btn.bind(DGG.EXIT, self._on_unhover, [btn])

            # # Description label with theme
            # DirectLabel(
            #     text=level_info.get("description", ""),
            #     text_scale=label_style["scale"],
            #     text_fg=MenuTheme.get_color("text_muted"),
            #     frameColor=(0, 0, 0, 0),
            #     pos=(0, 0, y_pos - 0.08),
            #     parent=self.bg,
            # )

            y_pos -= spacing

    def _create_saves_page(self):
        """Create the saves list page."""
        # Background with theme
        frame_style = MenuTheme.get_frame_style("primary")
        self.saves_bg = DirectFrame(
            frameColor=frame_style["frameColor"],
            frameSize=frame_style["frameSize"],
            sortOrder=10,
        )
        self.saves_bg.setTransparency(TransparencyAttrib.MAlpha)
        self.saves_bg.hide()

        # Add pika logo to top left
        self._add_pika_logo(self.saves_bg)

        # Title with theme
        title_style = MenuTheme.get_font_settings("title")
        title_font = MenuTheme.get_font_object(title_style.get("font", "Courier"))
        DirectLabel(
            text="Load",
            text_scale=title_style["scale"],
            text_fg=title_style["fg"],
            text_font=title_font,
            frameColor=(0, 0, 0, 0),
            pos=(0, 0, 0.8),
            parent=self.saves_bg,
        )

        # Saves list container with secondary background
        frame_style_sec = MenuTheme.get_frame_style("secondary")
        self.saves_list_frame = DirectFrame(
            frameColor=frame_style_sec["frameColor"],
            frameSize=(-0.7, 0.7, -0.6, 0.6),
            pos=(0, 0, 0),
            parent=self.saves_bg,
        )

    def _show_saves_page(self):
        """Show the saves page and populate with save files."""
        # Populate saves list
        self._populate_saves_list()
        
        # Hide main menu, show saves page
        self.bg.hide()
        self.saves_bg.show()

    def _populate_saves_list(self):
        """Populate the saves list with buttons."""
        # Clear existing buttons
        for child in self.saves_list_frame.getChildren():
            child.removeNode()

        saves = self._get_available_saves()
        label_style = MenuTheme.get_font_settings("label")

        if not saves:
            DirectLabel(
                text="No saves found",
                text_scale=label_style["scale"],
                text_fg=MenuTheme.get_color("text_muted"),
                frameColor=(0, 0, 0, 0),
                pos=(0, 0, 0),
                parent=self.saves_list_frame,
            )
        else:
            y_pos = 0.5
            spacing = 0.15

            for save_name, _ in saves:
                btn = DirectButton(
                    text=save_name,
                    text_pos=(0, -0.02),
                    frameSize=(-0.60, 0.60, -0.06, 0.06),
                    pos=(0, 0, y_pos),
                    command=self._load_save_file,
                    extraArgs=[save_name],
                    parent=self.saves_list_frame,
                    rolloverSound=None,
                    clickSound=None,
                    relief=DGG.FLAT,
                )
                apply_menu_styling(btn, "button", size="medium")
                btn.bind(DGG.ENTER, self._on_hover, [btn])
                btn.bind(DGG.EXIT, self._on_unhover, [btn])

                y_pos -= spacing

        # Back button with theme
        back_btn = DirectButton(
            text="Back",
            text_pos=(0, -0.02),
            frameSize=(-0.25, 0.25, -0.06, 0.06),
            pos=(0, 0, -0.8),
            command=self._show_main_page,
            parent=self.saves_bg,
            rolloverSound=None,
            clickSound=None,
            relief=DGG.FLAT,
        )
        apply_menu_styling(back_btn, "button", size="small")
        back_btn.bind(DGG.ENTER, self._on_hover, [back_btn])
        back_btn.bind(DGG.EXIT, self._on_unhover, [back_btn])

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

    def on_level_select(self, level_key):
        """Load selected level and start game.

        Args:
            level_key: Key from LEVELS dict
        """
        print(f"Loading level: {level_key}")
        self.game.load_level(level_key)
        self.menu_manager.hide_start_menu()

    def on_quit(self):
        """Quit the game."""
        self.game.quit_game()

    def _show_main_page(self):
        """Return to main menu page."""
        self.saves_bg.hide()
        self.bg.show()

    def _load_save_file(self, save_name):
        """Load a save file and start the game.

        Args:
            save_name: Name of the save file to load
        """
        print(f"Loading save: {save_name}")

        # First load a default level
        self.game.load_level("sandbox")

        # Then load the save data
        try:
            success = self.game.game_world.load_from_file(
                save_name, self.game.player
            )
            if success:
                print(f"Successfully loaded {save_name}")
                # Hide menu after brief delay
                self.game.taskMgr.doMethodLater(
                    0.5, lambda task: self.menu_manager.hide_start_menu(), "hide_menu"
                )
            else:
                print("Load failed!")
                self._show_main_page()
        except Exception as e:
            print(f"Error loading save: {e}")
            self._show_main_page()

    def _get_available_saves(self):
        """Get list of available save files.

        Returns:
            List of tuples (save_name, metadata)
        """
        try:
            if hasattr(self.game, "world"):
                return self.game.list_saves()
        except Exception as e:
            print(f"Error loading save list: {e}")
        return []

    def show(self):
        """Show the start menu."""
        self.bg.show()

    def hide(self):
        """Hide the start menu."""
        self.bg.hide()
        self.saves_bg.hide()

    def cleanup(self):
        """Clean up resources."""
        if self.bg:
            self.bg.destroy()
        if self.saves_bg:
            self.saves_bg.destroy()
