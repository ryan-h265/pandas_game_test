"""Modern menu styling and theming system."""

from panda3d.core import TextNode


class MenuTheme:
    """Unified theme for all menus - modern dark aesthetic with glass-morphism."""

    # Cache for loaded fonts
    _font_cache = {}

    # Color Palette - Modern dark with sage green accents
    COLORS = {
        # Backgrounds
        "bg_primary": (0.08, 0.10, 0.08, 0.96),  # Very dark sage green-gray
        "bg_secondary": (0.11, 0.13, 0.11, 0.92),  # Dark sage gray
        "bg_overlay": (0.05, 0.06, 0.05, 0.90),  # Almost black overlay with green tint
        
        # UI Elements with sage green
        "button_default": (0.13, 0.16, 0.13, 1.0),  # Dark sage slate
        "button_hover": (0.35, 0.48, 0.38, 1.0),  # Sage green on hover
        "button_active": (0.45, 0.60, 0.48, 1.0),  # Bright sage green on active
        "button_disabled": (0.09, 0.10, 0.09, 0.5),  # Dark disabled
        
        # Accents - sage green theme
        "accent_primary": (0.50, 0.68, 0.55, 1.0),  # Vibrant sage green
        "accent_secondary": (0.60, 0.78, 0.65, 1.0),  # Light sage green
        "accent_tertiary": (0.40, 0.58, 0.45, 1.0),  # Medium sage green
        
        # Text - high contrast
        "text_primary": (0.95, 0.96, 0.94, 1.0),  # Almost white with warm tint
        "text_secondary": (0.75, 0.80, 0.77, 1.0),  # Light sage gray
        "text_muted": (0.58, 0.63, 0.60, 1.0),  # Medium sage gray
        "text_disabled": (0.35, 0.38, 0.35, 1.0),  # Dark sage gray
        
        # Status colors - sage-friendly palette
        "status_success": (0.50, 0.72, 0.55, 1.0),  # Sage green success
        "status_warning": (0.95, 0.75, 0.30, 1.0),  # Orange warning
        "status_error": (0.85, 0.45, 0.45, 1.0),  # Muted red error
        "status_info": (0.50, 0.68, 0.55, 1.0),  # Sage green info
    }

    # Typography
    FONTS = {
        "title": {
            "scale": 0.15,
            "color": "text_primary",
            "align": TextNode.ACenter,
            "font": "HeyOctober",
        },
        "heading": {
            "scale": 0.10,
            "color": "accent_primary",
            "align": TextNode.ACenter,
            "font": "HeyOctober",
        },
        "subheading": {
            "scale": 0.08,
            "color": "text_primary",
            "align": TextNode.ACenter,
            "font": "HeyOctober",
        },
        "button": {
            "scale": 0.08,
            "color": "text_primary",
            "align": TextNode.ACenter,
            "font": "CecepsHandwriting",
        },
        "label": {
            "scale": 0.07,
            "color": "text_secondary",
            "align": TextNode.ALeft,
            "font": "HeyOctober",
        },
        "small": {
            "scale": 0.05,
            "color": "text_muted",
            "align": TextNode.ACenter,
            "font": "HeyOctober",
        },
    }

    # Component Sizes
    SIZES = {
        "button_large": {
            "frameSize": (-0.50, 0.50, -0.07, 0.07),
            "scale": 0.09,
        },
        "button_medium": {
            "frameSize": (-0.40, 0.40, -0.06, 0.06),
            "scale": 0.08,
        },
        "button_small": {
            "frameSize": (-0.25, 0.25, -0.05, 0.05),
            "scale": 0.06,
        },
        "slider": {
            "scale": 0.08,
            "frameSize": (-0.5, 0.5, -0.03, 0.03),
        },
    }

    # Spacing
    SPACING = {
        "padding_xs": 0.05,
        "padding_sm": 0.10,
        "padding_md": 0.15,
        "padding_lg": 0.20,
        "padding_xl": 0.30,
    }

    @staticmethod
    def get_color(color_name):
        """Get color by name from palette.

        Args:
            color_name: Key from COLORS dict

        Returns:
            RGBA tuple
        """
        return MenuTheme.COLORS.get(color_name, MenuTheme.COLORS["text_primary"])

    @staticmethod
    def get_font_settings(font_type):
        """Get typography settings for a font type.

        Args:
            font_type: Key from FONTS dict

        Returns:
            Dict with scale and color settings
        """
        font = MenuTheme.FONTS.get(font_type, MenuTheme.FONTS["label"])
        return {
            "scale": font["scale"],
            "fg": MenuTheme.get_color(font["color"]),
            "align": font["align"],
            "font": font.get("font", "Arial"),
        }

    @staticmethod
    def get_button_style(size="medium", state="default"):
        """Get complete button styling.

        Args:
            size: "small", "medium", or "large"
            state: "default", "hover", "active", or "disabled"

        Returns:
            Dict with button styling parameters
        """
        size_config = MenuTheme.SIZES.get(size, MenuTheme.SIZES["button_medium"])
        
        color_map = {
            "default": "button_default",
            "hover": "button_hover",
            "active": "button_active",
            "disabled": "button_disabled",
        }
        
        return {
            "frameColor": MenuTheme.get_color(color_map.get(state, "button_default")),
            "text_scale": MenuTheme.FONTS["button"]["scale"],
            "text_fg": MenuTheme.get_color("text_primary"),
            "font": MenuTheme.FONTS["button"].get("font", "Arial"),
        }

    @staticmethod
    def get_font_object(font_name):
        """Load and cache a font object for DirectGui widgets.
        
        Args:
            font_name: Font name (custom TTF filename without .ttf or system font)
            
        Returns:
            Font object or None
        """
        # Check cache first
        if font_name in MenuTheme._font_cache:
            return MenuTheme._font_cache[font_name]
        
        try:
            from pathlib import Path
            import panda3d.core as p3d
            
            # Check if it's a custom font file
            custom_font_path = Path(__file__).resolve().parents[3] / "assets" / "fonts"
            
            # Try different filename patterns
            font_files = [
                custom_font_path / f"{font_name}.ttf",
                custom_font_path / f"{font_name}-*.ttf",
            ]
            
            # Check for exact match first
            if font_files[0].exists():
                font_obj = p3d.FontPool.loadFont(str(font_files[0]))
            else:
                # Try glob pattern for variant names
                matches = list(custom_font_path.glob(f"{font_name}*.ttf"))
                if matches:
                    font_obj = p3d.FontPool.loadFont(str(matches[0]))
                else:
                    # Try to load as system font
                    font_obj = p3d.FontPool.loadFont(font_name)
            
            if font_obj:
                MenuTheme._font_cache[font_name] = font_obj
                return font_obj
        except Exception as e:
            # Font loading failed
            pass
        
        return None
        
    @staticmethod
    def get_frame_style(frame_type="primary"):
        """Get frame/background styling.

        Args:
            frame_type: "primary", "secondary", or "overlay"

        Returns:
            Dict with frame styling parameters
        """
        color_map = {
            "primary": "bg_primary",
            "secondary": "bg_secondary",
            "overlay": "bg_overlay",
        }
        
        return {
            "frameColor": MenuTheme.get_color(color_map.get(frame_type, "bg_primary")),
            "frameSize": (-1.5, 1.5, -1, 1),
        }


def apply_menu_styling(widget, style_type, **overrides):
    """Apply theme styling to a DirectGui widget.

    Args:
        widget: DirectGui widget to style
        style_type: Type of styling ("button", "frame", "label", etc.)
        **overrides: Additional properties to override
    """
    if style_type == "button":
        size = overrides.pop("size", "medium")
        state = overrides.pop("state", "default")
        style = MenuTheme.get_button_style(size, state)
    elif style_type == "frame":
        frame_type = overrides.pop("frame_type", "primary")
        style = MenuTheme.get_frame_style(frame_type)
    elif style_type == "label":
        font_type = overrides.pop("font_type", "label")
        style = MenuTheme.get_font_settings(font_type)
        style["frameColor"] = (0, 0, 0, 0)  # Transparent background
    else:
        style = {}

    # Extract font if present and handle separately
    font = style.pop("font", None)

    # Apply theme style
    for key, value in style.items():
        if key in overrides:
            continue  # Skip if overridden
        try:
            widget[key] = value
        except (KeyError, TypeError):
            pass  # Skip unsupported properties

    # Apply font if it exists
    if font:
        font_obj = MenuTheme.get_font_object(font)
        if font_obj:
            try:
                widget["text_font"] = font_obj
            except (KeyError, TypeError):
                pass  # Widget doesn't support text_font

    # Apply overrides
    for key, value in overrides.items():
        try:
            widget[key] = value
        except (KeyError, TypeError):
            pass
