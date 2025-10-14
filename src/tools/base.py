"""Base classes and enums for the tool system."""

from enum import Enum


class ToolType(Enum):
    """Types of tools available to the player."""

    FIST = "fist"
    TERRAIN = "terrain"
    CROWBAR = "crowbar"
    GUN = "gun"


class Tool:
    """Base class for player tools."""

    def __init__(self, name, tool_type):
        """Initialize tool.

        Args:
            name: Display name of the tool
            tool_type: ToolType enum value
        """
        self.name = name
        self.tool_type = tool_type
        self.is_active = False
        self.view_model_name = tool_type.value  # Name for the weapon viewmodel

    def on_activate(self):
        """Called when tool becomes active."""
        self.is_active = True
        # Return message for HUD display
        return f"Equipped: {self.name}"

    def on_deactivate(self):
        """Called when tool is switched away from."""
        self.is_active = False

    def on_primary_use(self, hit_info):
        """Called when primary action is used (e.g., left click).

        Args:
            hit_info: Dictionary with hit information (position, normal, etc.)

        Returns:
            bool: True if action was performed
        """
        return False

    def on_secondary_use(self, hit_info):
        """Called when secondary action is used (e.g., right click).

        Args:
            hit_info: Dictionary with hit information

        Returns:
            bool: True if action was performed
        """
        return False

    def on_tertiary_use(self, hit_info):
        """Called when tertiary action is used (e.g., middle click).

        Args:
            hit_info: Dictionary with hit information

        Returns:
            bool: True if action was performed
        """
        return False

    def update(self, dt):
        """Update tool state.

        Args:
            dt: Delta time since last update
        """
        pass

    def adjust_primary_property(self, delta):
        """Adjust the tool's primary property (e.g., with scroll wheel).

        Args:
            delta: Amount to adjust (positive or negative)

        Returns:
            tuple: (property_name, new_value) or None if not applicable
        """
        return None

    def adjust_secondary_property(self, delta):
        """Adjust the tool's secondary property (e.g., with [ ] keys).

        Args:
            delta: Amount to adjust (positive or negative)

        Returns:
            tuple: (property_name, new_value) or None if not applicable
        """
        return None
