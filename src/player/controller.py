"""Player controller for movement and input handling."""

from panda3d.core import Vec3, BitMask32
from panda3d.bullet import (
    BulletCapsuleShape,
    BulletCharacterControllerNode,
    ZUp,
)


class PlayerController:
    """Handles player movement and input with physics."""

    def __init__(self, render, bullet_world, start_pos=None):
        """Initialize player controller.

        Args:
            render: Panda3D render node
            bullet_world: Bullet physics world
            start_pos: Starting position Vec3
        """
        self.render = render
        self.bullet_world = bullet_world

        # Movement settings
        self.walk_speed = 15.0
        self.run_speed = 25.0
        self.current_speed = self.walk_speed

        # Position
        if start_pos is None:
            start_pos = Vec3(0, 0, 10)
        self.position = start_pos

        # Input state
        self.keys = {
            "forward": False,
            "backward": False,
            "left": False,
            "right": False,
            "jump": False,
            "run": False,
        }

        # Physics character
        self._setup_physics_character()

    def _setup_physics_character(self):
        """Setup bullet character controller for player."""
        # Create capsule shape for player (radius, height)
        shape = BulletCapsuleShape(0.5, 1.8, ZUp)

        # Create character controller node
        self.character = BulletCharacterControllerNode(shape, 0.4, "Player")
        self.character_np = self.render.attachNewNode(self.character)
        self.character_np.setPos(self.position)
        self.character_np.setCollideMask(BitMask32.allOn())

        # Add to physics world
        self.bullet_world.attachCharacter(self.character)

        # Character settings
        self.character.setMaxSlope(45)  # Max climbable slope in degrees
        self.character.setJumpSpeed(8.0)
        self.character.setFallSpeed(55.0)
        self.character.setGravity(30.0)

    def handle_input(self, key, pressed):
        """Handle keyboard input.

        Args:
            key: Key that was pressed
            pressed: True if pressed, False if released
        """
        key = key.lower()

        if key == "w":
            self.keys["forward"] = pressed
        elif key == "s":
            self.keys["backward"] = pressed
        elif key == "a":
            self.keys["left"] = pressed
        elif key == "d":
            self.keys["right"] = pressed
        elif key == "space":
            self.keys["jump"] = pressed
        elif key == "shift":
            self.keys["run"] = pressed

    def update(self, dt, camera_controller):
        """Update player state based on input.

        Args:
            dt: Delta time since last update
            camera_controller: Camera controller for direction
        """
        # Update speed based on run key
        self.current_speed = self.run_speed if self.keys["run"] else self.walk_speed

        # Calculate movement direction from camera
        forward = camera_controller.get_forward_vector()
        right = camera_controller.get_right_vector()

        # Build movement vector
        move_vector = Vec3(0, 0, 0)

        if self.keys["forward"]:
            move_vector += forward
        if self.keys["backward"]:
            move_vector -= forward
        if self.keys["right"]:
            move_vector += right
        if self.keys["left"]:
            move_vector -= right

        # Normalize to prevent faster diagonal movement
        if move_vector.lengthSquared() > 0:
            move_vector.normalize()
            move_vector *= self.current_speed

        # Apply movement to character
        self.character.setLinearMovement(move_vector, True)

        # Handle jump
        if self.keys["jump"] and self.character.isOnGround():
            self.character.doJump()

        # Update position from physics
        self.position = self.character_np.getPos()

    def get_position(self):
        """Get current player position.

        Returns:
            Vec3 position
        """
        return self.position

    def set_position(self, pos):
        """Set player position.

        Args:
            pos: Vec3 position
        """
        self.position = pos
        self.character_np.setPos(pos)

    def is_on_ground(self):
        """Check if player is on the ground.

        Returns:
            bool: True if on ground
        """
        return self.character.isOnGround()
