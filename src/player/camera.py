"""Camera controller for player view."""

import math
from panda3d.core import Vec3


class CameraController:
    """Manages first-person and third-person camera with mouse look."""

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

        # Camera mode: 'first_person' or 'third_person'
        self.camera_mode = "first_person"

        # Camera offset from player
        # First person: eye height
        self.first_person_offset = Vec3(
            0, 0, 1.6
        )  # 1.6 units above player position (eye height)

        # Third person: distance behind and above the player
        self.third_person_distance = 4.0  # Distance behind player
        self.third_person_height = 2.0  # Height above player

        # Current offset (will be updated based on mode)
        self.offset = self.first_person_offset

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
        # Only apply manual rotation in first-person mode
        # In third-person, lookAt() handles the rotation
        if self.camera_mode == "first_person":
            self.camera.setHpr(self.heading, self.pitch, 0)

    def update_position(self, player_pos):
        """Update camera position to follow player.

        Args:
            player_pos: Player position Vec3
        """
        if self.camera_mode == "first_person":
            # First person: camera at eye level
            camera_pos = player_pos + self.first_person_offset
            self.camera.setPos(camera_pos)
        else:
            # Third person: camera behind and above player with pitch control
            # Calculate position based on heading and pitch
            heading_rad = math.radians(self.heading)
            pitch_rad = math.radians(self.pitch)

            # Calculate camera position in spherical coordinates
            # Distance in the horizontal plane
            horizontal_distance = self.third_person_distance * math.cos(pitch_rad)

            # Calculate offset behind the player (opposite of forward direction)
            offset_x = math.sin(heading_rad) * horizontal_distance
            offset_y = -math.cos(heading_rad) * horizontal_distance

            # Height based on pitch and base height
            # Negative pitch = looking down = camera higher
            # Positive pitch = looking up = camera lower
            offset_z = self.third_person_height - (
                self.third_person_distance * math.sin(pitch_rad)
            )

            # Position camera behind and above the player
            camera_pos = player_pos + Vec3(offset_x, offset_y, offset_z)
            self.camera.setPos(camera_pos)

            # Make camera look at the player (at their center mass)
            look_at_target = player_pos + Vec3(0, 0, 1.0)
            self.camera.lookAt(look_at_target)

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

    def toggle_camera_mode(self):
        """Toggle between first-person and third-person camera modes.

        Returns:
            str: The new camera mode ('first_person' or 'third_person')
        """
        if self.camera_mode == "first_person":
            self.camera_mode = "third_person"
        else:
            self.camera_mode = "first_person"

        return self.camera_mode

    def set_camera_mode(self, mode):
        """Set the camera mode.

        Args:
            mode: 'first_person' or 'third_person'

        Returns:
            bool: True if mode was set successfully
        """
        if mode in ["first_person", "third_person"]:
            self.camera_mode = mode
            return True
        return False

    def is_first_person(self):
        """Check if camera is in first-person mode.

        Returns:
            bool: True if in first-person mode
        """
        return self.camera_mode == "first_person"

    def is_third_person(self):
        """Check if camera is in third-person mode.

        Returns:
            bool: True if in third-person mode
        """
        return self.camera_mode == "third_person"

    def set_third_person_distance(self, distance):
        """Set the third-person camera distance from player.

        Args:
            distance: Distance behind the player
        """
        self.third_person_distance = max(1.0, min(10.0, distance))

    def adjust_third_person_distance(self, delta):
        """Adjust the third-person camera distance.

        Args:
            delta: Amount to change distance by
        """
        self.third_person_distance = max(
            1.0, min(10.0, self.third_person_distance + delta)
        )
