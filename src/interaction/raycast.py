"""Raycasting utilities for object selection and interaction."""


class Raycast:
    """Handles raycasting for object picking and interaction detection."""

    def __init__(self, camera):
        self.camera = camera

    def cast_ray(self, from_pos, direction, max_distance=1000):
        """Cast a ray and detect intersections.

        Args:
            from_pos: Starting position of the ray
            direction: Direction vector of the ray
            max_distance: Maximum ray distance

        Returns:
            Hit result or None if no intersection
        """
        pass

    def get_object_under_mouse(self, mouse_pos):
        """Get the object under the mouse cursor.

        Args:
            mouse_pos: Mouse position on screen

        Returns:
            Object under mouse or None
        """
        pass
