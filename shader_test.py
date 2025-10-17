#!/usr/bin/env python3
"""Lightweight shader testing application for rapid iteration.

Usage:
    python shader_test.py sky                    # Test sky shader on hemisphere
    python shader_test.py sky --cube             # Test sky shader on cube
    python shader_test.py cloud --sphere         # Test cloud shader on sphere
    python shader_test.py terrain --plane        # Test terrain shader on plane
    python shader_test.py <name> --geometry auto # Auto-select geometry (default)

Geometry Options:
    --cube, --sphere, --plane, --hemisphere, --auto (default)

Controls:
    ESC - Quit
    R - Reload shaders (live editing!)
    SPACE - Toggle animation
    1/2 - Adjust u_time speed
    Arrow Keys - Rotate view
"""

import sys
import argparse
from pathlib import Path
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    GeomVertexFormat,
    GeomVertexData,
    GeomVertexWriter,
    Geom,
    GeomTriangles,
    GeomNode,
    Shader,
    Vec3,
    Vec4,
    ClockObject,
)
import math


globalClock = ClockObject.getGlobalClock()


class ShaderTester(ShowBase):
    """Minimal app to test shaders quickly."""

    def __init__(self, shader_name="sky", geometry_override=None):
        super().__init__()
        
        self.shader_name = shader_name
        self.geometry_override = geometry_override
        self.shader_dir = Path(__file__).parent / "assets" / "shaders"
        self.test_object = None
        self.current_shader = None
        self.time_scale = 1.0
        self.paused = False
        self.elapsed_time = 0.0
        
        # Mouse control state
        self.mouse_enabled = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.object_h = 0  # Heading rotation
        self.object_p = 0  # Pitch rotation
        self.zoom_distance = 8.0  # Distance from object for zoom
        
        # Disable default mouse controls
        self.disableMouse()
        
        # Setup camera - position at origin for sky dome, or back for objects
        self.camera.setPos(0, 0, 0)
        
        # Create test geometry based on shader type
        self._create_test_geometry()
        
        # Load and apply shader
        self._load_shader()
        
        # Setup controls
        self._setup_controls()
        
        # Update task
        self.taskMgr.add(self._update, "update")
        
        print(f"\n{'='*60}")
        print(f"Shader Tester - {shader_name}")
        if geometry_override:
            print(f"Geometry Override: {geometry_override}")
        print(f"{'='*60}")
        print("Controls:")
        print("  ESC - Quit")
        print("  R - Reload shader (live editing!)")
        print("  SPACE - Toggle animation")
        print("  1/2 - Adjust time scale (slower/faster)")
        print("  Left Mouse Drag - Rotate object")
        print("  Arrow Keys - Rotate object")
        print("  Mouse Scroll - Zoom in/out")
        print(f"{'='*60}\n")
    
    def _get_geometry_type(self):
        """Determine which geometry to use (auto or override)."""
        if self.geometry_override:
            return self.geometry_override
        
        # Auto-select based on shader name
        auto_map = {
            "sky": "hemisphere",
            "cloud": "sphere",
            "terrain": "plane",
        }
        return auto_map.get(self.shader_name, "sphere")
    
    def _create_test_geometry(self):
        """Create appropriate geometry for the shader type."""
        geom_type = self._get_geometry_type()
        
        # Determine if camera should be inside or outside
        inside_geom = geom_type == "hemisphere"
        
        if geom_type == "hemisphere":
            # Large hemisphere for sky shader (viewed from inside)
            self.test_object = self._create_hemisphere(1800, 32, 16)
            self.test_object.setPos(0, 0, 0)
            self.camera.setPos(0, 0, 0)
        elif geom_type == "sphere":
            # Sphere for cloud/general shaders - view from outside
            self.test_object = self._create_sphere(2, 32, 16)
            self.test_object.setPos(0, self.zoom_distance, 0)  # Place in front of camera
            self.camera.setPos(0, 0, 0)
            self.camera.lookAt(self.test_object)
        elif geom_type == "cube":
            # Cube for quick color testing - view from outside
            self.test_object = self._create_cube(2)
            self.test_object.setPos(0, self.zoom_distance, 0)  # Place in front of camera
            self.camera.setPos(0, 0, 0)
            self.camera.lookAt(self.test_object)
        elif geom_type == "plane":
            # Flat plane for terrain shader
            self.test_object = self._create_plane(10, 10, 32, 32)
            self.test_object.setPos(0, self.zoom_distance, -2)
            self.camera.setPos(0, 0, 2)
            self.camera.lookAt(self.test_object)
        else:
            # Default fallback
            self.test_object = self._create_sphere(2, 32, 16)
            self.test_object.setPos(0, self.zoom_distance, 0)
            self.camera.setPos(0, 0, 0)
            self.camera.lookAt(self.test_object)
            self.test_object.setPos(0, 0, 0)
        
        self.test_object.reparentTo(self.render)
        self.test_object.setTwoSided(True)
        self.test_object.setLightOff()
    
    def _create_hemisphere(self, radius, lon_segs, lat_segs):
        """Create hemisphere geometry (for sky)."""
        format = GeomVertexFormat.getV3n3()
        vdata = GeomVertexData("hemisphere", format, Geom.UHStatic)
        
        vertices = []
        for lat in range(lat_segs + 1):
            lat_angle = (math.pi * 0.5) * lat / lat_segs
            for lon in range(lon_segs + 1):
                lon_angle = 2 * math.pi * lon / lon_segs
                x = radius * math.cos(lat_angle) * math.cos(lon_angle)
                y = radius * math.cos(lat_angle) * math.sin(lon_angle)
                z = radius * math.sin(lat_angle)
                vertices.append((x, y, z))
        
        vdata.setNumRows(len(vertices))
        vertex_writer = GeomVertexWriter(vdata, "vertex")
        normal_writer = GeomVertexWriter(vdata, "normal")
        
        for x, y, z in vertices:
            vertex_writer.addData3(x, y, z)
            normal_writer.addData3(-x, -y, -z)  # Inverted for inside viewing
        
        geom = Geom(vdata)
        tris = GeomTriangles(Geom.UHStatic)
        
        for lat in range(lat_segs):
            for lon in range(lon_segs):
                i0 = lat * (lon_segs + 1) + lon
                i1 = lat * (lon_segs + 1) + (lon + 1)
                i2 = (lat + 1) * (lon_segs + 1) + lon
                i3 = (lat + 1) * (lon_segs + 1) + (lon + 1)
                tris.addVertices(i0, i1, i2)
                tris.addVertices(i1, i3, i2)
        
        tris.closePrimitive()
        geom.addPrimitive(tris)
        
        geom_node = GeomNode("hemisphere")
        geom_node.addGeom(geom)
        return self.render.attachNewNode(geom_node)
    
    def _create_sphere(self, radius, lon_segs, lat_segs):
        """Create sphere geometry."""
        format = GeomVertexFormat.getV3n3()
        vdata = GeomVertexData("sphere", format, Geom.UHStatic)
        
        vertices = []
        for lat in range(lat_segs + 1):
            lat_angle = math.pi * lat / lat_segs - math.pi / 2
            for lon in range(lon_segs + 1):
                lon_angle = 2 * math.pi * lon / lon_segs
                x = radius * math.cos(lat_angle) * math.cos(lon_angle)
                y = radius * math.cos(lat_angle) * math.sin(lon_angle)
                z = radius * math.sin(lat_angle)
                vertices.append((x, y, z))
        
        vdata.setNumRows(len(vertices))
        vertex_writer = GeomVertexWriter(vdata, "vertex")
        normal_writer = GeomVertexWriter(vdata, "normal")
        
        for x, y, z in vertices:
            vertex_writer.addData3(x, y, z)
            nx, ny, nz = x / radius, y / radius, z / radius
            normal_writer.addData3(nx, ny, nz)
        
        geom = Geom(vdata)
        tris = GeomTriangles(Geom.UHStatic)
        
        for lat in range(lat_segs):
            for lon in range(lon_segs):
                i0 = lat * (lon_segs + 1) + lon
                i1 = lat * (lon_segs + 1) + (lon + 1)
                i2 = (lat + 1) * (lon_segs + 1) + lon
                i3 = (lat + 1) * (lon_segs + 1) + (lon + 1)
                tris.addVertices(i0, i2, i1)
                tris.addVertices(i1, i2, i3)
        
        tris.closePrimitive()
        geom.addPrimitive(tris)
        
        geom_node = GeomNode("sphere")
        geom_node.addGeom(geom)
        return self.render.attachNewNode(geom_node)
    
    def _create_plane(self, width, height, w_segs, h_segs):
        """Create flat plane geometry."""
        format = GeomVertexFormat.getV3n3()
        vdata = GeomVertexData("plane", format, Geom.UHStatic)
        
        vertices = []
        for y in range(h_segs + 1):
            for x in range(w_segs + 1):
                px = (x / w_segs - 0.5) * width
                py = (y / h_segs - 0.5) * height
                vertices.append((px, py, 0))
        
        vdata.setNumRows(len(vertices))
        vertex_writer = GeomVertexWriter(vdata, "vertex")
        normal_writer = GeomVertexWriter(vdata, "normal")
        
        for x, y, z in vertices:
            vertex_writer.addData3(x, y, z)
            normal_writer.addData3(0, 0, 1)
        
        geom = Geom(vdata)
        tris = GeomTriangles(Geom.UHStatic)
        
        for y in range(h_segs):
            for x in range(w_segs):
                i0 = y * (w_segs + 1) + x
                i1 = y * (w_segs + 1) + (x + 1)
                i2 = (y + 1) * (w_segs + 1) + x
                i3 = (y + 1) * (w_segs + 1) + (x + 1)
                tris.addVertices(i0, i2, i1)
                tris.addVertices(i1, i2, i3)
        
        tris.closePrimitive()
        geom.addPrimitive(tris)
        
        geom_node = GeomNode("plane")
        geom_node.addGeom(geom)
        return self.render.attachNewNode(geom_node)
    
    def _create_cube(self, size):
        """Create simple cube geometry for quick testing."""
        format = GeomVertexFormat.getV3n3()
        vdata = GeomVertexData("cube", format, Geom.UHStatic)
        
        s = size / 2  # Half size for centering
        
        # Define 8 vertices of cube
        cube_vertices = [
            (-s, -s, -s), (s, -s, -s), (s, s, -s), (-s, s, -s),  # Bottom
            (-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s),  # Top
        ]
        
        # Define 6 faces with normals
        faces = [
            # vertices, normal
            ([0, 1, 2, 3], (0, 0, -1)),  # Bottom
            ([4, 7, 6, 5], (0, 0, 1)),   # Top
            ([0, 4, 5, 1], (0, -1, 0)),  # Front
            ([2, 6, 7, 3], (0, 1, 0)),   # Back
            ([0, 3, 7, 4], (-1, 0, 0)),  # Left
            ([1, 5, 6, 2], (1, 0, 0)),   # Right
        ]
        
        # Build vertex data
        vertices = []
        normals = []
        indices = []
        
        vertex_index = 0
        for face_verts, normal in faces:
            # Add 4 vertices for this face
            for vi in face_verts:
                vertices.append(cube_vertices[vi])
                normals.append(normal)
            
            # Two triangles per face
            indices.append((vertex_index, vertex_index + 1, vertex_index + 2))
            indices.append((vertex_index, vertex_index + 2, vertex_index + 3))
            vertex_index += 4
        
        vdata.setNumRows(len(vertices))
        vertex_writer = GeomVertexWriter(vdata, "vertex")
        normal_writer = GeomVertexWriter(vdata, "normal")
        
        for v, n in zip(vertices, normals):
            vertex_writer.addData3(*v)
            normal_writer.addData3(*n)
        
        geom = Geom(vdata)
        tris = GeomTriangles(Geom.UHStatic)
        
        for tri in indices:
            tris.addVertices(*tri)
        
        tris.closePrimitive()
        geom.addPrimitive(tris)
        
        geom_node = GeomNode("cube")
        geom_node.addGeom(geom)
        return self.render.attachNewNode(geom_node)
    
    def _load_shader(self):
        """Load shader files and apply to test object."""
        vert_path = self.shader_dir / f"{self.shader_name}.vert"
        frag_path = self.shader_dir / f"{self.shader_name}.frag"
        
        if not vert_path.exists():
            print(f"ERROR: {vert_path} not found!")
            return
        if not frag_path.exists():
            print(f"ERROR: {frag_path} not found!")
            return
        
        shader = Shader.load(
            Shader.SL_GLSL,
            vertex=str(vert_path),
            fragment=str(frag_path)
        )
        
        if shader:
            self.current_shader = shader
            self.test_object.setShader(shader)
            
            # Set default uniforms based on shader type
            if self.shader_name == "sky":
                self.test_object.setShaderInput("u_time", 0.0)
                self.test_object.setShaderInput("u_cycleSpeed", 0.1)  # Fast for testing
                self.test_object.setShaderInput("sunBaseColor", Vec3(1.0, 0.9, 0.7))
                self.test_object.setShaderInput("moonBaseColor", Vec3(0.8, 0.85, 1.0))
            elif self.shader_name == "cloud":
                self.test_object.setShaderInput("time", 0.0)
                self.test_object.setShaderInput("lightDirection", Vec3(1, 1, -1))
                self.test_object.setShaderInput("sunColor", Vec3(1.0, 0.95, 0.8))
                self.test_object.setShaderInput("cloudDensity", 0.8)
                self.test_object.setShaderInput("camera", Vec3(0, -10, 0))
            elif self.shader_name == "terrain":
                self.test_object.setShaderInput("time", 0.0)
            
            print(f"✓ Loaded shader: {self.shader_name}")
        else:
            print(f"✗ Failed to load shader: {self.shader_name}")
    
    def _setup_controls(self):
        """Setup keyboard and mouse controls."""
        self.accept("escape", sys.exit)
        self.accept("r", self._reload_shader)
        self.accept("space", self._toggle_pause)
        self.accept("1", self._decrease_speed)
        self.accept("2", self._increase_speed)
        
        # Arrow keys for rotation
        self.accept("arrow_up", self._rotate_up)
        self.accept("arrow_down", self._rotate_down)
        self.accept("arrow_left", self._rotate_left)
        self.accept("arrow_right", self._rotate_right)
        
        # Mouse drag for rotation
        self.accept("mouse1", self._start_mouse_rotate)
        self.accept("mouse1-up", self._stop_mouse_rotate)
        
        # Mouse scroll for zoom
        self.accept("wheel_up", self._zoom_in)
        self.accept("wheel_down", self._zoom_out)
        
        # Task for mouse rotation
        self.taskMgr.add(self._mouse_rotate_task, "mouse_rotate")
    
    def _reload_shader(self):
        """Reload shader files (for live editing)."""
        print("Reloading shader...")
        self._load_shader()
        print(f"Time scale: {self.time_scale:.2f}x")
    
    def _toggle_pause(self):
        """Toggle animation pause."""
        self.paused = not self.paused
        print(f"Animation: {'PAUSED' if self.paused else 'RUNNING'}")
    
    def _decrease_speed(self):
        """Decrease time scale."""
        self.time_scale = max(0.1, self.time_scale - 0.1)
        print(f"Time scale: {self.time_scale:.2f}x")
    
    def _increase_speed(self):
        """Increase time scale."""
        self.time_scale = min(10.0, self.time_scale + 0.1)
        print(f"Time scale: {self.time_scale:.2f}x")
    
    def _start_mouse_rotate(self):
        """Start mouse rotation mode."""
        self.mouse_enabled = True
        if self.mouseWatcherNode.hasMouse():
            self.last_mouse_x = self.mouseWatcherNode.getMouseX()
            self.last_mouse_y = self.mouseWatcherNode.getMouseY()
    
    def _stop_mouse_rotate(self):
        """Stop mouse rotation mode."""
        self.mouse_enabled = False
    
    def _zoom_in(self):
        """Zoom in (decrease distance)."""
        self.zoom_distance = max(1.0, self.zoom_distance - 1.0)
        self._update_camera_distance()
    
    def _zoom_out(self):
        """Zoom out (increase distance)."""
        self.zoom_distance = min(30.0, self.zoom_distance + 1.0)
        self._update_camera_distance()
    
    def _update_camera_distance(self):
        """Update camera distance based on geometry type."""
        if self._get_geometry_type() != "hemisphere":
            # For non-hemisphere objects, move them away from camera
            self.test_object.setPos(0, self.zoom_distance, 0)
    
    def _mouse_rotate_task(self, task):
        """Handle mouse drag rotation."""
        if self.mouse_enabled and self.mouseWatcherNode.hasMouse():
            # Get current mouse position
            mouse_x = self.mouseWatcherNode.getMouseX()
            mouse_y = self.mouseWatcherNode.getMouseY()
            
            # Calculate delta from last position
            dx = mouse_x - self.last_mouse_x
            dy = mouse_y - self.last_mouse_y
            
            # Update rotation (inverted controls for intuitive dragging)
            self.object_h += dx * 50
            self.object_p -= dy * 50
            
            # Clamp pitch to avoid flipping
            self.object_p = max(-89, min(89, self.object_p))
            
            # Apply rotation to object (not camera, except for hemisphere)
            if self._get_geometry_type() == "hemisphere":
                # For hemisphere, rotate camera view
                self.camera.setHpr(self.object_h, self.object_p, 0)
            else:
                # For other objects, rotate the object
                self.test_object.setHpr(self.object_h, self.object_p, 0)
            
            # Update last mouse position
            self.last_mouse_x = mouse_x
            self.last_mouse_y = mouse_y
        
        return task.cont

    
    def _rotate_up(self):
        """Rotate object/view up."""
        self.object_p += 5
        self.object_p = max(-89, min(89, self.object_p))
        if self._get_geometry_type() == "hemisphere":
            self.camera.setHpr(self.object_h, self.object_p, 0)
        else:
            self.test_object.setHpr(self.object_h, self.object_p, 0)
    
    def _rotate_down(self):
        """Rotate object/view down."""
        self.object_p -= 5
        self.object_p = max(-89, min(89, self.object_p))
        if self._get_geometry_type() == "hemisphere":
            self.camera.setHpr(self.object_h, self.object_p, 0)
        else:
            self.test_object.setHpr(self.object_h, self.object_p, 0)
    
    def _rotate_left(self):
        """Rotate object/view left."""
        self.object_h += 5
        if self._get_geometry_type() == "hemisphere":
            self.camera.setHpr(self.object_h, self.object_p, 0)
        else:
            self.test_object.setHpr(self.object_h, self.object_p, 0)
    
    def _rotate_right(self):
        """Rotate object/view right."""
        self.object_h -= 5
        if self._get_geometry_type() == "hemisphere":
            self.camera.setHpr(self.object_h, self.object_p, 0)
        else:
            self.test_object.setHpr(self.object_h, self.object_p, 0)
    
    def _update(self, task):
        """Update shader uniforms each frame."""
        dt = globalClock.getDt()
        
        if not self.paused:
            self.elapsed_time += dt * self.time_scale
        
        # Update shader-specific uniforms
        if self.shader_name == "sky":
            self.test_object.setShaderInput("u_time", self.elapsed_time)
        elif self.shader_name == "cloud":
            self.test_object.setShaderInput("time", self.elapsed_time)
        elif self.shader_name == "terrain":
            self.test_object.setShaderInput("time", self.elapsed_time)
        
        return task.cont


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test Panda3D shaders with live reloading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python shader_test.py sky                 # Sky shader on hemisphere
  python shader_test.py sky --cube          # Sky shader on cube
  python shader_test.py cloud --sphere      # Cloud shader on sphere
  python shader_test.py terrain --plane     # Terrain shader on plane
        """
    )
    parser.add_argument(
        "shader",
        nargs="?",
        default="sky",
        help="Shader name to test (default: sky)"
    )
    
    # Geometry override options (mutually exclusive)
    geom_group = parser.add_mutually_exclusive_group()
    geom_group.add_argument("--cube", action="store_const", const="cube", dest="geometry")
    geom_group.add_argument("--sphere", action="store_const", const="sphere", dest="geometry")
    geom_group.add_argument("--plane", action="store_const", const="plane", dest="geometry")
    geom_group.add_argument("--hemisphere", action="store_const", const="hemisphere", dest="geometry")
    geom_group.add_argument("--auto", action="store_const", const=None, dest="geometry")
    
    args = parser.parse_args()
    
    app = ShaderTester(args.shader, geometry_override=args.geometry)
    app.run()
