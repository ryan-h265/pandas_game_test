"""Visual effects system for game."""

from panda3d.core import Vec3, Vec4, LineSegs


class BulletTrail:
    """Visual bullet trail effect."""

    def __init__(self, render, start_pos, end_pos, duration=0.5):
        """Create a bullet trail.

        Args:
            render: Panda3D render node
            start_pos: Vec3 starting position (muzzle)
            end_pos: Vec3 ending position (hit point)
            duration: How long the trail is visible (seconds)
        """
        self.render = render
        self.duration = duration
        self.lifetime = 0.0
        self.is_alive = True

        distance = (end_pos - start_pos).length()
        print(
            f"BulletTrail: Creating {distance:.2f}m trail from {start_pos} to {end_pos}"
        )

        # Create line geometry with LineSegs
        segs = LineSegs()
        segs.setThickness(10.0)  # Very thick line
        segs.setColor(1.0, 0.9, 0.1, 1.0)  # Bright yellow

        segs.moveTo(start_pos)
        segs.drawTo(end_pos)

        # Create node and attach
        self.trail_node = render.attachNewNode(segs.create())

        # Make it highly visible - render on top of everything
        self.trail_node.setRenderModeThickness(10)
        self.trail_node.setLightOff()
        self.trail_node.setBin("fixed", 1000)  # Very high priority
        self.trail_node.setDepthTest(False)  # Render through everything
        self.trail_node.setDepthWrite(False)
        self.trail_node.setTransparency(True)

        print("BulletTrail: Node created and attached to render")

    def update(self, dt):
        """Update trail effect.

        Args:
            dt: Delta time

        Returns:
            bool: True if still alive
        """
        self.lifetime += dt

        if self.lifetime >= self.duration:
            self.is_alive = False
            self.remove()
            return False

        # Fade out
        alpha = 1.0 - (self.lifetime / self.duration)
        self.trail_node.setColorScale(1, 1, 0.5, alpha)

        return True

    def remove(self):
        """Remove trail from scene."""
        if self.trail_node:
            self.trail_node.removeNode()
            self.trail_node = None


class MuzzleFlash:
    """Muzzle flash effect for gun."""

    def __init__(self, render, position, direction, duration=0.02):
        """Create muzzle flash.

        Args:
            render: Panda3D render node
            position: Vec3 muzzle position
            direction: Vec3 forward direction
            duration: Flash duration (seconds)
        """
        self.render = render
        self.duration = duration
        self.lifetime = 0.0
        self.is_alive = True

        # Create small bright sphere for flash
        from panda3d.core import (
            GeomNode,
            Geom,
            GeomVertexFormat,
            GeomVertexData,
            GeomVertexWriter,
            GeomTriangles,
        )

        vformat = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData("flash", vformat, Geom.UHStatic)

        vertex = GeomVertexWriter(vdata, "vertex")
        normal = GeomVertexWriter(vdata, "normal")
        color = GeomVertexWriter(vdata, "color")

        # Simple quad facing camera
        flash_color = Vec4(1, 1, 0.5, 1)
        size = 0.1  # Much smaller flash (was 0.2)

        # Create quad vertices
        vertices = [
            Vec3(-size, 0, -size),
            Vec3(size, 0, -size),
            Vec3(size, 0, size),
            Vec3(-size, 0, size),
        ]

        tris = GeomTriangles(Geom.UHStatic)

        for i, v in enumerate(vertices):
            vertex.addData3(v)
            normal.addData3(0, 1, 0)
            color.addData4(flash_color)

        # Two triangles
        tris.addVertices(0, 1, 2)
        tris.addVertices(0, 2, 3)
        tris.closePrimitive()

        geom = Geom(vdata)
        geom.addPrimitive(tris)

        geom_node = GeomNode("muzzle_flash")
        geom_node.addGeom(geom)

        self.flash_node = render.attachNewNode(geom_node)
        self.flash_node.setPos(
            position
        )  # Position at the muzzle (already offset in tool_manager)
        self.flash_node.lookAt(position + direction * 10)
        # Don't billboard - make it directional so it extends forward from gun
        # self.flash_node.setBillboardPointEye()  # REMOVED: This was making it face camera
        self.flash_node.setLightOff()  # Don't be affected by lighting
        self.flash_node.setTransparency(True)
        self.flash_node.setBin("fixed", 1001)  # Render on top
        self.flash_node.setDepthTest(False)
        self.flash_node.setDepthWrite(False)

    def update(self, dt):
        """Update flash effect.

        Args:
            dt: Delta time

        Returns:
            bool: True if still alive
        """
        self.lifetime += dt

        if self.lifetime >= self.duration:
            self.is_alive = False
            self.remove()
            return False

        # Fade and scale
        progress = self.lifetime / self.duration
        alpha = 1.0 - progress
        scale = 1.0 + progress * 2.0  # Expand

        self.flash_node.setScale(scale)
        self.flash_node.setColorScale(1, 1, 1, alpha)

        return True

    def remove(self):
        """Remove flash from scene."""
        if self.flash_node:
            self.flash_node.removeNode()
            self.flash_node = None


class DebugRayVisualization:
    """Debug visualization for raycasts."""

    def __init__(self, render, start_pos, end_pos, hit, duration=2.0):
        """Create debug ray visualization.

        Args:
            render: Panda3D render node
            start_pos: Vec3 ray start
            end_pos: Vec3 ray end
            hit: bool - whether ray hit something
            duration: How long to show (seconds)
        """
        self.render = render
        self.duration = duration
        self.lifetime = 0.0
        self.is_alive = True

        # Create ray line
        segs = LineSegs()
        segs.setThickness(3.0)

        # Green if hit, red if miss
        if hit:
            segs.setColor(0.0, 1.0, 0.0, 1.0)  # Bright green
        else:
            segs.setColor(1.0, 0.0, 0.0, 0.8)  # Red

        segs.moveTo(start_pos)
        segs.drawTo(end_pos)

        self.line_node = render.attachNewNode(segs.create())
        self.line_node.setRenderModeThickness(3)
        self.line_node.setLightOff()
        self.line_node.setBin("fixed", 999)
        self.line_node.setDepthTest(False)
        self.line_node.setDepthWrite(False)

        # Create hit marker X if hit
        self.marker_node = None
        if hit:
            self._create_hit_marker(end_pos)

    def _create_hit_marker(self, position):
        """Create an X marker at hit position."""
        segs = LineSegs()
        segs.setThickness(4.0)
        segs.setColor(0, 1, 0, 1)  # Green

        size = 0.5
        # Draw X
        segs.moveTo(position + Vec3(-size, -size, -size))
        segs.drawTo(position + Vec3(size, size, size))
        segs.moveTo(position + Vec3(size, -size, -size))
        segs.drawTo(position + Vec3(-size, size, size))
        segs.moveTo(position + Vec3(-size, -size, size))
        segs.drawTo(position + Vec3(size, size, -size))
        segs.moveTo(position + Vec3(size, -size, size))
        segs.drawTo(position + Vec3(-size, size, -size))

        self.marker_node = self.render.attachNewNode(segs.create())
        self.marker_node.setRenderModeThickness(4)
        self.marker_node.setLightOff()
        self.marker_node.setBin("fixed", 999)
        self.marker_node.setDepthTest(False)
        self.marker_node.setDepthWrite(False)

    def update(self, dt):
        """Update debug visualization."""
        self.lifetime += dt

        if self.lifetime >= self.duration:
            self.is_alive = False
            self.remove()
            return False

        # Fade out
        alpha = 1.0 - (self.lifetime / self.duration)
        self.line_node.setColorScale(1, 1, 1, alpha)
        if self.marker_node:
            self.marker_node.setColorScale(1, 1, 1, alpha)

        return True

    def remove(self):
        """Remove debug visualization."""
        if self.line_node:
            self.line_node.removeNode()
            self.line_node = None
        if self.marker_node:
            self.marker_node.removeNode()
            self.marker_node = None


class EffectsManager:
    """Manages visual effects."""

    def __init__(self, render):
        """Initialize effects manager.

        Args:
            render: Panda3D render node
        """
        self.render = render
        self.active_effects = []
        self.debug_mode = False  # Toggle debug raycast visualization

    def set_debug_mode(self, enabled):
        """Enable/disable debug visualization.

        Args:
            enabled: bool
        """
        self.debug_mode = enabled
        print(f"Debug raycast visualization: {'ON' if enabled else 'OFF'}")

    def create_debug_ray(self, start_pos, end_pos, hit):
        """Create debug ray visualization.

        Args:
            start_pos: Vec3 start position
            end_pos: Vec3 end position
            hit: bool - whether ray hit something

        Returns:
            DebugRayVisualization instance
        """
        if self.debug_mode:
            debug_ray = DebugRayVisualization(self.render, start_pos, end_pos, hit)
            self.active_effects.append(debug_ray)
            return debug_ray
        return None

    def create_bullet_trail(self, start_pos, end_pos):
        """Create a bullet trail effect.

        Args:
            start_pos: Vec3 start position
            end_pos: Vec3 end position

        Returns:
            BulletTrail instance
        """
        trail = BulletTrail(self.render, start_pos, end_pos)
        self.active_effects.append(trail)
        return trail

    def create_muzzle_flash(self, position, direction):
        """Create muzzle flash effect.

        Args:
            position: Vec3 muzzle position
            direction: Vec3 forward direction

        Returns:
            MuzzleFlash instance
        """
        flash = MuzzleFlash(self.render, position, direction)
        self.active_effects.append(flash)
        return flash

    def update(self, dt):
        """Update all effects.

        Args:
            dt: Delta time
        """
        # Update and remove dead effects
        self.active_effects = [
            effect for effect in self.active_effects if effect.update(dt)
        ]
