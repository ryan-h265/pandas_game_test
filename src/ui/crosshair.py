"""Crosshair system with tool-specific designs."""

from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import TransparencyAttrib, Vec4
from direct.gui.DirectGui import DirectFrame


class CrosshairManager:
    """Manages tool-specific crosshairs."""

    def __init__(self, base):
        """Initialize crosshair manager.
        
        Args:
            base: ShowBase instance for accessing aspect2d
        """
        self.base = base
        self.current_crosshair = None
        self.crosshair_elements = []
        
        # Crosshair configurations for each tool
        self.crosshair_configs = {
            "fist": {
                "type": "circle",
                "color": Vec4(1, 1, 1, 0.8),
                "size": 0.03,
            },
            "terrain": {
                "type": "square",
                "color": Vec4(0.5, 1, 0.5, 0.7),
                "size": 0.04,
            },
            "crowbar": {
                "type": "cross_thick",
                "color": Vec4(1, 0.8, 0.3, 0.8),
                "size": 0.035,
            },
            "gun": {
                "type": "cross_precise",
                "color": Vec4(1, 0.2, 0.2, 0.9),
                "size": 0.025,
            },
        }

    def show_crosshair(self, tool_type):
        """Show crosshair for specific tool.

        Args:
            tool_type: Type of tool ("fist", "crowbar", "gun", "terrain")
        """
        # Remove current crosshair
        self.hide_crosshair()

        # Get configuration
        config = self.crosshair_configs.get(tool_type, self.crosshair_configs["fist"])
        crosshair_type = config["type"]
        color = config["color"]
        size = config["size"]

        # Create crosshair based on type
        if crosshair_type == "circle":
            self._create_circle_crosshair(color, size)
        elif crosshair_type == "square":
            self._create_square_crosshair(color, size)
        elif crosshair_type == "cross_thick":
            self._create_cross_thick_crosshair(color, size)
        elif crosshair_type == "cross_precise":
            self._create_cross_precise_crosshair(color, size)

    def hide_crosshair(self):
        """Hide current crosshair."""
        for element in self.crosshair_elements:
            element.destroy()
        self.crosshair_elements.clear()

    def _create_circle_crosshair(self, color, size):
        """Create circular crosshair (fist - close combat).

        Args:
            color: Vec4 RGBA color
            size: Size of crosshair
        """
        # Outer circle
        outer = DirectFrame(
            frameSize=(-size, size, -size, size),
            frameColor=color,
            pos=(0, 0, 0),
            parent=self.base.aspect2d,
        )
        outer.setTransparency(TransparencyAttrib.MAlpha)
        self.crosshair_elements.append(outer)

        # Inner circle (hollow)
        inner_size = size * 0.6
        inner = DirectFrame(
            frameSize=(-inner_size, inner_size, -inner_size, inner_size),
            frameColor=(0, 0, 0, 0.5),
            pos=(0, 0, 0),
            parent=self.base.aspect2d,
        )
        inner.setTransparency(TransparencyAttrib.MAlpha)
        self.crosshair_elements.append(inner)

        # Center dot
        dot_size = size * 0.15
        dot = DirectFrame(
            frameSize=(-dot_size, dot_size, -dot_size, dot_size),
            frameColor=color,
            pos=(0, 0, 0),
            parent=self.base.aspect2d,
        )
        dot.setTransparency(TransparencyAttrib.MAlpha)
        self.crosshair_elements.append(dot)

    def _create_square_crosshair(self, color, size):
        """Create square crosshair with corners (terrain tool).

        Args:
            color: Vec4 RGBA color
            size: Size of crosshair
        """
        gap = size * 0.6
        thickness = size * 0.15
        length = size * 0.6

        # Four corner brackets
        corners = [
            # Top-left
            ((-gap - length, -gap - thickness), (-gap, -gap)),
            ((-gap - thickness, -gap - length), (-gap, -gap)),
            # Top-right
            ((gap, -gap - thickness), (gap + length, -gap)),
            ((gap, -gap - length), (gap + thickness, -gap)),
            # Bottom-left
            ((-gap - length, gap), (-gap, gap + thickness)),
            ((-gap - thickness, gap), (-gap, gap + length)),
            # Bottom-right
            ((gap, gap), (gap + length, gap + thickness)),
            ((gap, gap), (gap + thickness, gap + length)),
        ]

        for (x1, y1), (x2, y2) in corners:
            frame = DirectFrame(
                frameSize=(x1, x2, y1, y2),
                frameColor=color,
                pos=(0, 0, 0),
                parent=self.base.aspect2d,
            )
            frame.setTransparency(TransparencyAttrib.MAlpha)
            self.crosshair_elements.append(frame)

        # Center dot
        dot_size = size * 0.1
        dot = DirectFrame(
            frameSize=(-dot_size, dot_size, -dot_size, dot_size),
            frameColor=color,
            pos=(0, 0, 0),
            parent=self.base.aspect2d,
        )
        dot.setTransparency(TransparencyAttrib.MAlpha)
        self.crosshair_elements.append(dot)

    def _create_cross_thick_crosshair(self, color, size):
        """Create thick cross crosshair (crowbar - melee weapon).

        Args:
            color: Vec4 RGBA color
            size: Size of crosshair
        """
        gap = size * 0.3
        length = size * 1.2
        thickness = size * 0.25

        # Horizontal bar
        h_bar = DirectFrame(
            frameSize=(-gap - length, gap + length, -thickness, thickness),
            frameColor=color,
            pos=(0, 0, 0),
            parent=self.base.aspect2d,
        )
        h_bar.setTransparency(TransparencyAttrib.MAlpha)
        self.crosshair_elements.append(h_bar)

        # Vertical bar
        v_bar = DirectFrame(
            frameSize=(-thickness, thickness, -gap - length, gap + length),
            frameColor=color,
            pos=(0, 0, 0),
            parent=self.base.aspect2d,
        )
        v_bar.setTransparency(TransparencyAttrib.MAlpha)
        self.crosshair_elements.append(v_bar)

        # Center square (covers middle intersection)
        center_size = gap
        center = DirectFrame(
            frameSize=(-center_size, center_size, -center_size, center_size),
            frameColor=(0, 0, 0, 0.3),
            pos=(0, 0, 0),
            parent=self.base.aspect2d,
        )
        center.setTransparency(TransparencyAttrib.MAlpha)
        self.crosshair_elements.append(center)

    def _create_cross_precise_crosshair(self, color, size):
        """Create precise cross crosshair with gap (gun - accurate shooting).

        Args:
            color: Vec4 RGBA color
            size: Size of crosshair
        """
        gap = size * 0.8
        length = size * 1.5
        thickness = size * 0.12

        # Four lines extending from center
        lines = [
            # Top
            (-thickness, thickness, gap, gap + length),
            # Bottom
            (-thickness, thickness, -gap - length, -gap),
            # Left
            (-gap - length, -gap, -thickness, thickness),
            # Right
            (gap, gap + length, -thickness, thickness),
        ]

        for x1, x2, y1, y2 in lines:
            line = DirectFrame(
                frameSize=(x1, x2, y1, y2),
                frameColor=color,
                pos=(0, 0, 0),
                parent=self.base.aspect2d,
            )
            line.setTransparency(TransparencyAttrib.MAlpha)
            self.crosshair_elements.append(line)

        # Very small center dot for precision
        dot_size = size * 0.08
        dot = DirectFrame(
            frameSize=(-dot_size, dot_size, -dot_size, dot_size),
            frameColor=color,
            pos=(0, 0, 0),
            parent=self.base.aspect2d,
        )
        dot.setTransparency(TransparencyAttrib.MAlpha)
        self.crosshair_elements.append(dot)

    def set_color(self, color):
        """Change color of current crosshair.

        Args:
            color: Vec4 RGBA color
        """
        for element in self.crosshair_elements:
            element['frameColor'] = color

    def set_scale(self, scale):
        """Scale current crosshair.

        Args:
            scale: Scale multiplier
        """
        for element in self.crosshair_elements:
            current_scale = element.getScale()
            element.setScale(current_scale * scale)

    def cleanup(self):
        """Clean up crosshair resources."""
        self.hide_crosshair()
