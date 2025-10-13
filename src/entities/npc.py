"""NPC (Non-Player Character) implementation."""


class NPC:
    """Base class for non-player characters."""

    def __init__(self, name, position=None):
        self.name = name
        self.position = position or [0, 0, 0]
        self.health = 100

    def update(self, dt):
        """Update NPC state.

        Args:
            dt: Delta time since last update
        """
        pass

    def interact(self, player):
        """Handle interaction with player.

        Args:
            player: Player object interacting with this NPC
        """
        pass
