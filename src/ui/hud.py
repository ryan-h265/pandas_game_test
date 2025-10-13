"""HUD (Heads-Up Display) implementation."""


class HUD:
    """Manages the in-game heads-up display."""

    def __init__(self):
        self.visible = True
        self.elements = []

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
        pass

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
