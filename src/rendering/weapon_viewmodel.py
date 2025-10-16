"""First-person weapon view models for FPS-style tool display."""

from panda3d.core import Vec3, Vec4, NodePath
from panda3d.core import GeomNode, GeomVertexFormat, GeomVertexData, GeomVertexWriter
from panda3d.core import Geom, GeomTriangles
from direct.interval.IntervalGlobal import (
    Sequence,
    LerpPosInterval,
    LerpHprInterval,
    Func,
)
import math


class WeaponViewModel:
    """Manages first-person weapon view models attached to camera."""

    def __init__(self, camera):
        """Initialize weapon view model system.

        Args:
            camera: Camera node to attach weapon models to
        """
        self.camera = camera
        self.current_model = None
        self.weapon_root = None
        self.bob_time = 0.0
        self.is_moving = False
        self.animation_sequence = None
        self.base_position = None  # Store base position for bob calculations

        # Weapon model configurations (position, rotation relative to camera)
        self.weapon_configs = {
            "fist": {
                "position": Vec3(
                    0.3, 0.8, -0.25
                ),  # Right, forward, down (raised from -0.4)
                "rotation": Vec3(0, 0, -10),  # HPR
                "scale": 1.0,
            },
            "crowbar": {
                "position": Vec3(0.25, 1.0, -0.20),  # Raised from -0.35
                "rotation": Vec3(-45, -20, 0),
                "scale": 1.0,
            },
            "gun": {
                "position": Vec3(0.2, 0.9, -0.18),  # Raised from -0.3
                "rotation": Vec3(0, -5, 0),
                "scale": 1.0,
            },
            "terrain": {
                "position": Vec3(0.3, 0.9, -0.25),  # Raised from -0.4
                "rotation": Vec3(0, 0, -15),
                "scale": 1.0,
            },
            "building": {
                "position": Vec3(0.35, 0.7, -0.30),
                "rotation": Vec3(0, -10, -20),
                "scale": 0.8,
            },
        }

    def create_weapon_root(self):
        """Create root node for weapon attachment."""
        if self.weapon_root:
            self.weapon_root.removeNode()

        self.weapon_root = self.camera.attachNewNode("weapon_root")
        return self.weapon_root

    def show_weapon(self, weapon_type):
        """Show a weapon model.

        Args:
            weapon_type: Type of weapon ("fist", "crowbar", "gun", "terrain")
        """
        # Remove current model
        if self.current_model:
            self.current_model.removeNode()
            self.current_model = None

        # Stop any playing animations
        if self.animation_sequence:
            self.animation_sequence.finish()
            self.animation_sequence = None

        # Create weapon root if needed
        if not self.weapon_root:
            self.create_weapon_root()

        # Create new weapon model
        if weapon_type == "fist":
            self.current_model = self._create_fist_model()
        elif weapon_type == "crowbar":
            self.current_model = self._create_crowbar_model()
        elif weapon_type == "gun":
            self.current_model = self._create_gun_model()
        elif weapon_type == "terrain":
            self.current_model = self._create_terrain_tool_model()
        elif weapon_type == "building":
            self.current_model = self._create_building_tool_model()

        if self.current_model:
            self.current_model.reparentTo(self.weapon_root)

            # Apply weapon configuration
            config = self.weapon_configs.get(weapon_type, {})
            pos = config.get("position", Vec3(0.3, 1.0, -0.4))
            rot = config.get("rotation", Vec3(0, 0, 0))
            scale = config.get("scale", 1.0)

            self.current_model.setPos(pos)
            self.current_model.setHpr(rot)
            self.current_model.setScale(scale)

            # Store base position for bob calculations
            self.base_position = Vec3(pos)

            # Play equip animation
            self._play_equip_animation()

    def hide_weapon(self):
        """Hide current weapon model."""
        if self.current_model:
            self.current_model.removeNode()
            self.current_model = None

    def play_use_animation(self, weapon_type):
        """Play weapon use animation (swing, shoot, etc.).

        Args:
            weapon_type: Type of weapon being used
        """
        if not self.current_model:
            return

        if weapon_type == "fist":
            self._play_punch_animation()
        elif weapon_type == "crowbar":
            self._play_swing_animation()
        elif weapon_type == "gun":
            self._play_shoot_animation()
        elif weapon_type == "terrain":
            self._play_dig_animation()
        elif weapon_type == "building":
            self._play_place_animation()

    def update(self, dt, is_moving=False):
        """Update weapon viewmodel (bob, sway, etc.).

        Args:
            dt: Delta time
            is_moving: Whether player is moving
        """
        if not self.current_model or not self.base_position:
            return

        self.is_moving = is_moving

        # Weapon bob when moving
        if is_moving:
            self.bob_time += dt * 8.0  # Bob speed
            bob_offset_y = math.sin(self.bob_time) * 0.02
            bob_offset_z = abs(math.sin(self.bob_time * 0.5)) * 0.015

            # Apply bob offset relative to base position (not current position!)
            new_pos = Vec3(self.base_position)
            new_pos.y += bob_offset_y
            new_pos.z += bob_offset_z
            self.current_model.setPos(new_pos)
        else:
            self.bob_time = 0.0
            # Return to base position when not moving
            self.current_model.setPos(self.base_position)

    def _play_equip_animation(self):
        """Play weapon equip animation (draw weapon)."""
        if not self.current_model:
            return

        # Start position (off screen, below)
        start_pos = self.current_model.getPos() + Vec3(0, 0, -0.5)
        end_pos = self.current_model.getPos()

        self.current_model.setPos(start_pos)

        # Animate up into view
        self.animation_sequence = Sequence(
            LerpPosInterval(
                self.current_model,
                0.3,
                end_pos,
                startPos=start_pos,
                blendType="easeOut",
            )
        )
        self.animation_sequence.start()

    def _play_punch_animation(self):
        """Play fist punch animation."""
        if not self.current_model or (
            self.animation_sequence and self.animation_sequence.isPlaying()
        ):
            return

        if not self.base_position:
            return

        original_pos = Vec3(self.base_position)
        punch_pos = original_pos + Vec3(0, 0.3, 0)  # Forward

        self.animation_sequence = Sequence(
            LerpPosInterval(self.current_model, 0.1, punch_pos, blendType="easeOut"),
            LerpPosInterval(self.current_model, 0.15, original_pos, blendType="easeIn"),
        )
        self.animation_sequence.start()

    def _play_swing_animation(self):
        """Play crowbar swing animation."""
        if not self.current_model or (
            self.animation_sequence and self.animation_sequence.isPlaying()
        ):
            return

        if not self.base_position:
            return

        original_pos = Vec3(self.base_position)
        original_hpr = self.current_model.getHpr()

        # Swing motion
        wind_up_pos = original_pos + Vec3(0.1, -0.1, 0.1)
        wind_up_hpr = original_hpr + Vec3(0, 30, 20)
        swing_pos = original_pos + Vec3(-0.2, 0.3, -0.1)
        swing_hpr = original_hpr + Vec3(0, -40, -30)

        self.animation_sequence = Sequence(
            # Wind up
            LerpPosInterval(self.current_model, 0.15, wind_up_pos, blendType="easeIn"),
            LerpHprInterval(self.current_model, 0.15, wind_up_hpr, blendType="easeIn"),
            # Swing
            LerpPosInterval(self.current_model, 0.2, swing_pos, blendType="easeOut"),
            LerpHprInterval(self.current_model, 0.2, swing_hpr, blendType="easeOut"),
            # Return
            LerpPosInterval(self.current_model, 0.2, original_pos, blendType="easeIn"),
            LerpHprInterval(self.current_model, 0.2, original_hpr, blendType="easeIn"),
        )
        self.animation_sequence.start()

    def _play_shoot_animation(self):
        """Play gun shoot animation (recoil)."""
        if not self.current_model or (
            self.animation_sequence and self.animation_sequence.isPlaying()
        ):
            return

        if not self.base_position:
            return

        original_pos = Vec3(self.base_position)
        original_hpr = self.current_model.getHpr()

        # Recoil motion
        recoil_pos = original_pos + Vec3(0, -0.15, 0.05)  # Back and up
        recoil_hpr = original_hpr + Vec3(0, 15, 0)  # Pitch up

        self.animation_sequence = Sequence(
            # Recoil
            LerpPosInterval(self.current_model, 0.05, recoil_pos, blendType="easeOut"),
            LerpHprInterval(self.current_model, 0.05, recoil_hpr, blendType="easeOut"),
            # Return
            LerpPosInterval(self.current_model, 0.15, original_pos, blendType="easeIn"),
            LerpHprInterval(self.current_model, 0.15, original_hpr, blendType="easeIn"),
        )
        self.animation_sequence.start()

    def _play_dig_animation(self):
        """Play terrain tool dig animation."""
        if not self.current_model or (
            self.animation_sequence and self.animation_sequence.isPlaying()
        ):
            return

        if not self.base_position:
            return

        original_pos = Vec3(self.base_position)
        dig_pos = original_pos + Vec3(0, 0.2, -0.1)  # Forward and down

        self.animation_sequence = Sequence(
            LerpPosInterval(self.current_model, 0.1, dig_pos, blendType="easeOut"),
            LerpPosInterval(self.current_model, 0.15, original_pos, blendType="easeIn"),
        )
        self.animation_sequence.start()

    def _create_fist_model(self):
        """Create simple fist model (hand).

        Returns:
            NodePath containing the fist model
        """
        fist_root = NodePath("fist")

        # Create simple hand shape (palm + fingers)
        # Palm (rectangular box)
        palm = self._create_box(
            Vec3(0.08, 0.12, 0.05),  # width, length, thickness
            Vec4(0.9, 0.7, 0.6, 1.0),  # Skin color
        )
        palm.reparentTo(fist_root)
        palm.setPos(0, 0, 0)

        # Fingers (4 small boxes)
        finger_color = Vec4(0.85, 0.65, 0.55, 1.0)
        for i in range(4):
            finger = self._create_box(
                Vec3(0.015, 0.08, 0.02),
                finger_color,
            )
            finger.reparentTo(fist_root)
            x_offset = -0.035 + i * 0.023
            finger.setPos(x_offset, 0.10, 0)

        # Thumb
        thumb = self._create_box(
            Vec3(0.018, 0.06, 0.025),
            finger_color,
        )
        thumb.reparentTo(fist_root)
        thumb.setPos(-0.06, 0.05, 0)
        thumb.setHpr(0, 0, -30)

        return fist_root

    def _create_crowbar_model(self):
        """Create simple crowbar model.

        Returns:
            NodePath containing the crowbar model
        """
        crowbar_root = NodePath("crowbar")

        # Main shaft (long thin box)
        shaft = self._create_box(
            Vec3(0.02, 0.6, 0.02),
            Vec4(0.3, 0.3, 0.35, 1.0),  # Dark metal
        )
        shaft.reparentTo(crowbar_root)
        shaft.setPos(0, 0.3, 0)

        # Curved end (hook)
        hook = self._create_box(
            Vec3(0.025, 0.08, 0.025),
            Vec4(0.35, 0.35, 0.4, 1.0),
        )
        hook.reparentTo(crowbar_root)
        hook.setPos(0, 0.6, 0.04)
        hook.setHpr(0, -30, 0)

        # Handle (slightly thicker)
        handle = self._create_box(
            Vec3(0.025, 0.12, 0.025),
            Vec4(0.2, 0.2, 0.2, 1.0),
        )
        handle.reparentTo(crowbar_root)
        handle.setPos(0, -0.05, 0)

        return crowbar_root

    def _create_gun_model(self):
        """Create simple gun model (pistol-style).

        Returns:
            NodePath containing the gun model
        """
        gun_root = NodePath("gun")

        gun_color = Vec4(0.2, 0.2, 0.22, 1.0)  # Dark gunmetal

        # Barrel
        barrel = self._create_box(
            Vec3(0.025, 0.15, 0.03),
            gun_color,
        )
        barrel.reparentTo(gun_root)
        barrel.setPos(0, 0.15, 0.02)

        # Slide
        slide = self._create_box(
            Vec3(0.035, 0.12, 0.04),
            Vec4(0.25, 0.25, 0.27, 1.0),
        )
        slide.reparentTo(gun_root)
        slide.setPos(0, 0.08, 0.03)

        # Grip/Handle
        grip = self._create_box(
            Vec3(0.03, 0.06, 0.12),
            Vec4(0.15, 0.15, 0.15, 1.0),
        )
        grip.reparentTo(gun_root)
        grip.setPos(0, 0.02, -0.04)

        # Trigger guard
        trigger_guard = self._create_box(
            Vec3(0.015, 0.04, 0.03),
            gun_color,
        )
        trigger_guard.reparentTo(gun_root)
        trigger_guard.setPos(0, 0.05, -0.01)

        # Muzzle (end of barrel - lighter color)
        muzzle = self._create_box(
            Vec3(0.03, 0.02, 0.035),
            Vec4(0.4, 0.4, 0.42, 1.0),
        )
        muzzle.reparentTo(gun_root)
        muzzle.setPos(0, 0.23, 0.02)

        return gun_root

    def _create_terrain_tool_model(self):
        """Create simple terrain tool model (like a shovel/pickaxe).

        Returns:
            NodePath containing the terrain tool model
        """
        tool_root = NodePath("terrain_tool")

        # Handle (wooden)
        handle = self._create_box(
            Vec3(0.025, 0.5, 0.025),
            Vec4(0.6, 0.4, 0.2, 1.0),  # Brown wood
        )
        handle.reparentTo(tool_root)
        handle.setPos(0, 0.25, 0)

        # Head/blade (metal)
        blade = self._create_box(
            Vec3(0.08, 0.12, 0.02),
            Vec4(0.4, 0.4, 0.45, 1.0),  # Metal
        )
        blade.reparentTo(tool_root)
        blade.setPos(0, 0.52, 0)
        blade.setHpr(0, 30, 0)

        # Grip area (darker)
        grip = self._create_box(
            Vec3(0.03, 0.1, 0.03),
            Vec4(0.3, 0.2, 0.1, 1.0),
        )
        grip.reparentTo(tool_root)
        grip.setPos(0, 0.05, 0)

        return tool_root

    def _create_building_tool_model(self):
        """Create simple building tool model (like a blueprint holder/tablet).

        Returns:
            NodePath containing the building tool model
        """
        tool_root = NodePath("building_tool")

        # Main tablet/blueprint holder (flat rectangle)
        tablet = self._create_box(
            Vec3(0.15, 0.20, 0.01),
            Vec4(0.3, 0.5, 0.7, 1.0),  # Blue-ish (like a blueprint screen)
        )
        tablet.reparentTo(tool_root)
        tablet.setPos(0, 0.15, 0)

        # Frame around tablet
        frame_color = Vec4(0.2, 0.2, 0.22, 1.0)

        # Top frame
        frame_top = self._create_box(
            Vec3(0.16, 0.015, 0.015),
            frame_color,
        )
        frame_top.reparentTo(tool_root)
        frame_top.setPos(0, 0.26, 0)

        # Bottom frame
        frame_bottom = self._create_box(
            Vec3(0.16, 0.015, 0.015),
            frame_color,
        )
        frame_bottom.reparentTo(tool_root)
        frame_bottom.setPos(0, 0.04, 0)

        # Left frame
        frame_left = self._create_box(
            Vec3(0.015, 0.21, 0.015),
            frame_color,
        )
        frame_left.reparentTo(tool_root)
        frame_left.setPos(-0.08, 0.15, 0)

        # Right frame
        frame_right = self._create_box(
            Vec3(0.015, 0.21, 0.015),
            frame_color,
        )
        frame_right.reparentTo(tool_root)
        frame_right.setPos(0.08, 0.15, 0)

        # Simple building icon on screen (small cube to represent a building)
        building_icon = self._create_box(
            Vec3(0.04, 0.04, 0.05),
            Vec4(0.8, 0.8, 0.9, 1.0),  # Light color for icon
        )
        building_icon.reparentTo(tool_root)
        building_icon.setPos(0, 0.15, 0.03)

        return tool_root

    def _play_place_animation(self):
        """Play building placement animation."""
        if not self.current_model or (
            self.animation_sequence and self.animation_sequence.isPlaying()
        ):
            return

        if not self.base_position:
            return

        original_pos = Vec3(self.base_position)
        original_hpr = self.current_model.getHpr()

        # Placement motion - bring tablet up and forward, then return
        place_pos = original_pos + Vec3(-0.05, 0.15, 0.1)  # Up and forward
        place_hpr = original_hpr + Vec3(0, -15, 5)  # Tilt slightly

        self.animation_sequence = Sequence(
            # Bring up to place
            LerpPosInterval(self.current_model, 0.15, place_pos, blendType="easeOut"),
            LerpHprInterval(self.current_model, 0.15, place_hpr, blendType="easeOut"),
            # Hold briefly
            Func(lambda: None),  # Small pause
            # Return
            LerpPosInterval(self.current_model, 0.2, original_pos, blendType="easeIn"),
            LerpHprInterval(self.current_model, 0.2, original_hpr, blendType="easeIn"),
        )
        self.animation_sequence.start()

    def _create_box(self, size, color):
        """Create a simple colored box geometry.

        Args:
            size: Vec3 dimensions (width, length, height)
            color: Vec4 RGBA color

        Returns:
            NodePath containing the box geometry
        """
        vformat = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData("box", vformat, Geom.UHStatic)

        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        color_writer = GeomVertexWriter(vdata, "color")

        # Half extents
        hx, hy, hz = size.x / 2, size.y / 2, size.z / 2

        # Define 8 vertices of the box
        vertices = [
            Vec3(-hx, -hy, -hz),
            Vec3(hx, -hy, -hz),
            Vec3(hx, hy, -hz),
            Vec3(-hx, hy, -hz),
            Vec3(-hx, -hy, hz),
            Vec3(hx, -hy, hz),
            Vec3(hx, hy, hz),
            Vec3(-hx, hy, hz),
        ]

        # Define 6 faces with normals
        faces = [
            ([0, 1, 2, 3], Vec3(0, 0, -1)),  # Bottom
            ([4, 7, 6, 5], Vec3(0, 0, 1)),  # Top
            ([0, 4, 5, 1], Vec3(0, -1, 0)),  # Front
            ([2, 6, 7, 3], Vec3(0, 1, 0)),  # Back
            ([0, 3, 7, 4], Vec3(-1, 0, 0)),  # Left
            ([1, 5, 6, 2], Vec3(1, 0, 0)),  # Right
        ]

        tris = GeomTriangles(Geom.UHStatic)
        vtx_index = 0

        for face_indices, face_normal in faces:
            # First triangle
            for i in [0, 1, 2]:
                vertex.addData3(vertices[face_indices[i]])
                normal.addData3(face_normal)
                color_writer.addData4(color)
                tris.addVertex(vtx_index)
                vtx_index += 1

            # Second triangle
            for i in [0, 2, 3]:
                vertex.addData3(vertices[face_indices[i]])
                normal.addData3(face_normal)
                color_writer.addData4(color)
                tris.addVertex(vtx_index)
                vtx_index += 1

        tris.closePrimitive()

        geom = Geom(vdata)
        geom.addPrimitive(tris)

        geom_node = GeomNode("box_geom")
        geom_node.addGeom(geom)

        return NodePath(geom_node)
