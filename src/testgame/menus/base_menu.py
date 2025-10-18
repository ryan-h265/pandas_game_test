"""Base menu class with shared functionality."""

from pathlib import Path
from panda3d.core import TransparencyAttrib, CardMaker, Texture


class BaseMenu:
    """Base class for all menus with shared functionality."""

    def __init__(self, game):
        """Initialize base menu.

        Args:
            game: Reference to Game instance
        """
        self.game = game

    def _add_pika_logo(self, parent):
        """Add Himalayan pika logo to top left of menu.

        Args:
            parent: Parent frame to attach logo to
        """
        try:
            # Get image path
            img_path = (
                Path(__file__).resolve().parents[3]
                / "assets"
                / "images"
                / "himalayan_pika.png"
            )

            if not img_path.exists():
                print(f"Pika image not found at {img_path}")
                return

            # Create image frame with texture
            from direct.gui.DirectGui import DirectFrame

            logo_frame = DirectFrame(
                parent=parent,
                frameSize=(-0.075, 0.075, -0.075, 0.075),
                frameColor=(0, 0, 0, 0),
                pos=(1.05, 0, 0.5),
                scale=0.5,
            )
            logo_frame.setTransparency(TransparencyAttrib.MAlpha)

            # Load texture onto frame
            cm = CardMaker("pika_card")
            cm.setFrame(-1, 1, -1, 1)
            pika_card = logo_frame.attachNewNode(cm.generate())

            # Load and apply texture
            tex = self.game.loader.loadTexture(str(img_path))
            tex.setMinfilter(Texture.FT_linear)
            tex.setMagfilter(Texture.FT_linear)
            pika_card.setTexture(tex)
            pika_card.setTransparency(TransparencyAttrib.MAlpha)

        except Exception as e:
            print(f"Error loading pika logo: {e}")
