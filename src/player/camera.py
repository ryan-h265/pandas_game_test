"""Camera controller for player view."""

import math
from panda3d.core import Vec3


class CameraController:
    """Manages first-person camera with mouse look."""

    def __init__(self, camera_node, win, mouse_sensitivity=0.1):
        """Initialize camera controller.

        Args:
            camera_node: Panda3D camera node
            win: Window handle for mouse control
            mouse_sensitivity: Mouse sensitivity multiplier
        """
        self.camera = camera_node
        self.win = win

        # Camera rotation
        self.heading = 0.0  # Horizontal rotation (yaw)
        self.pitch = -20.0  # Vertical rotation (pitch) - start looking down slightly

        # Mouse control
        self.mouse_sensitivity = mouse_sensitivity
        self.center_x = 0
        self.center_y = 0

        # Camera offset from player (eye height)
        self.offset = Vec3(0, 0, 1.6)  # 1.6 units above player position (eye height)

    def setup_mouse(self):
        """Setup mouse for FPS-style control."""
        # Disable default mouse control
        if self.win.hasPointer(0):
            props = self.win.getProperties()
            self.center_x = props.getXSize() // 2
            self.center_y = props.getYSize() // 2

    def update_look(self, delta_x, delta_y):
        """Update camera rotation based on mouse movement.

        Args:
            delta_x: Mouse X delta movement
            delta_y: Mouse Y delta movement
        """
        # Update rotation
        self.heading -= delta_x * self.mouse_sensitivity
        self.pitch -= delta_y * self.mouse_sensitivity

        # Clamp pitch to avoid gimbal lock
        self.pitch = max(-89, min(89, self.pitch))

        # Normalize heading
        while self.heading > 360:
            self.heading -= 360
        while self.heading < 0:
            self.heading += 360

    def apply_rotation(self):
        """Apply current rotation to camera."""
        self.camera.setHpr(self.heading, self.pitch, 0)

    def update_position(self, player_pos):
        """Update camera position to follow player.

        Args:
            player_pos: Player position Vec3
        """
        # Position camera at player position plus offset
        camera_pos = player_pos + self.offset
        self.camera.setPos(camera_pos)

    def get_forward_vector(self):
        """Get the forward direction vector.

        Returns:
            Vec3 forward direction (normalized)
        """
        # Convert heading to radians
        # Panda3D: Y is forward, X is right
        heading_rad = math.radians(self.heading)

        # Calculate forward vector in Panda3D's coordinate system
        # heading 0 = facing +Y, heading 90 = facing -X
        forward_x = -math.sin(heading_rad)
        forward_y = math.cos(heading_rad)

        return Vec3(forward_x, forward_y, 0).normalized()

    def get_right_vector(self):
        """Get the right direction vector.

        Returns:
            Vec3 right direction (normalized)
        """
        # Right is 90 degrees clockwise from forward
        heading_rad = math.radians(self.heading - 90)

        right_x = -math.sin(heading_rad)
        right_y = math.cos(heading_rad)

        return Vec3(right_x, right_y, 0).normalized()
