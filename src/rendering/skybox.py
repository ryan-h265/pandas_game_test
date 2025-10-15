"""Skybox system for creating atmospheric mountain environments."""

import math
from panda3d.core import (
    GeomVertexFormat,
    GeomVertexData,
    GeomVertexWriter,
    Geom,
    GeomTriangles,
    GeomNode,
    Vec3,
    Vec4,
    CardMaker,
    TransparencyAttrib,
    RenderState,
    ColorBlendAttrib,
    Shader,
    Texture,
    TextureStage,
)


class MountainSkybox:
    """Creates a procedural skybox with distant mountains, clouds, and sun."""
    
    def __init__(self, render, camera):
        """Initialize the skybox.
        
        Args:
            render: Panda3D render node
            camera: Camera node for positioning
        """
        self.render = render
        self.camera = camera
        self.skybox_node = None
        self.sky_dome = None
        
    def create_skybox(self):
        """Create complete mountain skybox with sky dome, mountains, sun, and clouds."""
        # Create the base skybox structure
        self.skybox_node = self.render.attachNewNode("mountain_skybox")
        
        # Create sky dome as base
        sky_dome = self._create_sky_dome()
        sky_dome.reparentTo(self.skybox_node)
        
        # Add distant mountain silhouettes
        mountain_ring = self._create_distant_mountains()
        mountain_ring.reparentTo(self.skybox_node)
        
        # Add sun
        sun = self._create_sun()
        sun.reparentTo(self.skybox_node)
        
        # Add cloud layer
        cloud_layer = self._create_cloud_layer()
        cloud_layer.reparentTo(self.skybox_node)
        
        # Setup skybox rendering properties
        self.skybox_node.setBin("background", 0)
        self.skybox_node.setDepthWrite(False)
        self.skybox_node.setDepthTest(False)
        self.skybox_node.setTwoSided(True)
        
        print("Created complete mountain skybox with sky, mountains, sun, and clouds!")
        print(f"Skybox components: sky dome, {mountain_ring.getNumChildren()} mountain ranges, sun, clouds")
        
        return self.skybox_node
    
    def _create_sky_dome(self):
        """Create a seamless spherical sky dome with gradient."""
        # Create proper spherical sky dome geometry
        sky_dome_geom = self._create_sphere_geometry("sky_sphere", 1800, 32, 16)
        sky_root = self.render.attachNewNode(sky_dome_geom)
        
        # Apply sky gradient colors
        zenith_color = Vec4(0.4, 0.6, 0.95, 1.0)      # Deep blue at top
        
        # Set base color
        sky_root.setColor(zenith_color)
        sky_root.setLightOff()
        sky_root.setTwoSided(True)  # Ensure visible from inside
        sky_root.setBin("background", 0)  # Render first
        sky_root.setDepthWrite(False)  # Don't write to depth buffer
        
        print("Created seamless spherical sky dome")
        
        return sky_root
    
    def _create_sphere_geometry(self, name, radius, lon_segs, lat_segs):
        """Create a sphere geometry for seamless skybox."""
        format = GeomVertexFormat.getV3c4()
        vdata = GeomVertexData(name, format, Geom.UHStatic)
        
        vertices = []
        colors = []
        
        # Generate sphere vertices with color gradient
        for lat in range(lat_segs + 1):
            lat_angle = math.pi * lat / lat_segs - math.pi / 2  # -π/2 to π/2
            
            for lon in range(lon_segs + 1):
                lon_angle = 2 * math.pi * lon / lon_segs  # 0 to 2π
                
                # Sphere coordinates
                x = radius * math.cos(lat_angle) * math.cos(lon_angle)
                y = radius * math.cos(lat_angle) * math.sin(lon_angle)
                z = radius * math.sin(lat_angle)
                
                vertices.append((x, y, z))
                
                # Color gradient from zenith to horizon
                height_factor = (math.sin(lat_angle) + 1) / 2  # 0 at horizon, 1 at zenith
                
                # Sky color gradient
                zenith_color = Vec4(0.4, 0.6, 0.95, 1.0)    # Deep blue
                horizon_color = Vec4(0.8, 0.9, 1.0, 1.0)    # Light blue
                
                # Interpolate between zenith and horizon
                color = Vec4(
                    horizon_color.x + (zenith_color.x - horizon_color.x) * height_factor,
                    horizon_color.y + (zenith_color.y - horizon_color.y) * height_factor,
                    horizon_color.z + (zenith_color.z - horizon_color.z) * height_factor,
                    1.0
                )
                colors.append(color)
        
        # Set vertex data
        vdata.setNumRows(len(vertices))
        vertex_writer = GeomVertexWriter(vdata, "vertex")
        color_writer = GeomVertexWriter(vdata, "color")
        
        for (x, y, z), color in zip(vertices, colors):
            vertex_writer.addData3(x, y, z)
            color_writer.addData4(color)
        
        # Create triangular faces
        geom = Geom(vdata)
        tris = GeomTriangles(Geom.UHStatic)
        
        for lat in range(lat_segs):
            for lon in range(lon_segs):
                # Current quad indices
                i0 = lat * (lon_segs + 1) + lon
                i1 = lat * (lon_segs + 1) + (lon + 1)
                i2 = (lat + 1) * (lon_segs + 1) + lon
                i3 = (lat + 1) * (lon_segs + 1) + (lon + 1)
                
                # Two triangles per quad (inside-facing for skybox)
                tris.addVertices(i0, i2, i1)
                tris.addVertices(i1, i2, i3)
        
        tris.closePrimitive()
        geom.addPrimitive(tris)
        
        # Create geometry node
        geom_node = GeomNode(name)
        geom_node.addGeom(geom)
        
        return geom_node
    
    def _apply_sky_gradient(self, sky_np):
        """Apply a sky gradient using a simple shader or vertex colors."""
        # Create a bright sky color that's easily visible
        sky_color = Vec4(0.5, 0.7, 1.0, 1.0)  # Bright sky blue
        sky_np.setColor(sky_color)
        
        # Make sure it's not wireframe
        sky_np.clearRenderMode()
        
        # Ensure it's visible
        sky_np.setTwoSided(True)
        sky_np.setLightOff()  # Don't let lighting affect the sky
    
    def _create_distant_mountains(self):
        """Create realistic distant mountain ranges on the horizon."""
        mountain_node = self.render.attachNewNode("distant_mountains")

        # Create multiple mountain ranges at different distances
        ranges = [
            {"distance": 1800, "height_mult": 0.8, "color": Vec4(0.3, 0.35, 0.5, 0.8)},
            {"distance": 1600, "height_mult": 1.0, "color": Vec4(0.25, 0.3, 0.45, 0.9)},
            {"distance": 1400, "height_mult": 0.6, "color": Vec4(0.2, 0.25, 0.4, 0.95)},
        ]
        
        for i, mountain_range in enumerate(ranges):
            range_node = self._create_mountain_range(
                mountain_range["distance"],
                mountain_range["height_mult"],
                mountain_range["color"],
                seed=i * 100
            )
            range_node.reparentTo(mountain_node)

        return mountain_node

    def _create_gentle_mountain(self, width, max_height, name):
        """Create simple mountain cards like the original implementation."""
        cm = CardMaker(f"mountain_{name}")
        cm.setFrame(-width/2, width/2, 0, max_height)
        
        return cm.generate()


    def _create_mountain_range(self, distance, height_multiplier, color, seed=0):
        """Create a single mountain range silhouette."""
        format = GeomVertexFormat.getV3c4()
        vdata = GeomVertexData("mountain_range", format, Geom.UHStatic)
        
        # Create mountain silhouette points
        segments = 64
        points = []
        
        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            x = distance * math.cos(angle)
            z = distance * math.sin(angle)
            
            # Generate mountain height using simple noise
            height = self._simple_mountain_noise(angle, seed) * height_multiplier * 200
            height = max(height, 0)  # No negative heights
            
            points.append((x, z, height))
        
        # Add base points (at ground level)
        base_points = []
        for x, z, _ in points:
            base_points.append((x, z, 0))
        
        all_points = points + base_points
        vdata.setNumRows(len(all_points))
        
        vertex_writer = GeomVertexWriter(vdata, "vertex")
        color_writer = GeomVertexWriter(vdata, "color")
        
        # Write vertices and colors
        for x, z, y in all_points:
            vertex_writer.addData3(x, z, y)
            color_writer.addData4(color)
        
        # Create triangles to form the mountain silhouette
        geom = Geom(vdata)
        tris = GeomTriangles(Geom.UHStatic)
        
        for i in range(segments):
            # Top vertices
            v0 = i
            v1 = (i + 1) % (segments + 1)
            # Bottom vertices
            v2 = (segments + 1) + i
            v3 = (segments + 1) + ((i + 1) % (segments + 1))
            
            # Two triangles per segment
            tris.addVertices(v0, v2, v1)
            tris.addVertices(v1, v2, v3)
        
        tris.closePrimitive()
        geom.addPrimitive(tris)
        
        # Create node
        mountain_geom_node = GeomNode("mountain_range")
        mountain_geom_node.addGeom(geom)
        mountain_np = self.render.attachNewNode(mountain_geom_node)
        
        # Enable transparency for atmospheric perspective
        mountain_np.setTransparency(TransparencyAttrib.MAlpha)
        
        return mountain_np
    
    def _simple_mountain_noise(self, angle, seed):
        """Simple noise function for mountain heights."""
        # Combine multiple sine waves for mountain-like profiles
        height = 0
        height += math.sin(angle * 3 + seed) * 0.5
        height += math.sin(angle * 7 + seed * 1.3) * 0.3
        height += math.sin(angle * 15 + seed * 1.7) * 0.15
        height += math.sin(angle * 31 + seed * 2.1) * 0.05
        
        # Make some peaks much higher (like Everest among other peaks)
        peak_factor = abs(math.sin(angle * 2 + seed))
        if peak_factor > 0.8:
            height *= 2.0 + peak_factor
        
        return max(height, -0.2)  # Allow some valleys but not too deep
    

    
    def _create_cloud_layer(self):
        """Create mountain cloud layers."""
        cloud_node = self.render.attachNewNode("mountain_clouds")
        
        # Create realistic mountain clouds at different altitudes
        cloud_layers = [
            {"distance": 1100, "height": 300, "size": 150, "density": 0.4, "color": Vec4(1.0, 1.0, 1.0, 0.7)},
            {"distance": 1000, "height": 450, "size": 120, "density": 0.3, "color": Vec4(0.95, 0.95, 0.98, 0.6)},
            {"distance": 900, "height": 600, "size": 100, "density": 0.25, "color": Vec4(0.9, 0.9, 0.95, 0.5)},
        ]
        
        for layer_idx, layer in enumerate(cloud_layers):
            layer_node = cloud_node.attachNewNode(f"cloud_layer_{layer_idx}")
            
            # Create scattered clouds around the mountains
            num_clouds = int(16 * layer["density"])
            
            for i in range(num_clouds):
                angle = 2 * math.pi * i / num_clouds + layer_idx * 0.3  # Offset each layer
                
                # Add some randomness to cloud positions
                angle_offset = (math.sin(angle * 3.7 + layer_idx) * 0.2)
                distance_offset = math.sin(angle * 2.3 + layer_idx) * 100
                
                actual_angle = angle + angle_offset
                actual_distance = layer["distance"] + distance_offset
                
                x = actual_distance * math.cos(actual_angle)
                z = actual_distance * math.sin(actual_angle)
                
                # Create natural cloud with size variation
                cloud_base_size = layer["size"] + (i % 3) * 20
                cloud_geom = self._create_fluffy_cloud(cloud_base_size, f"cloud_{layer_idx}_{i}")
                
                cloud_node_path = layer_node.attachNewNode(cloud_geom)
                cloud_node_path.setPos(x, z, layer["height"])
                cloud_node_path.setBillboardPointEye()  # Always face camera
                cloud_node_path.setColor(layer["color"])
                cloud_node_path.setTransparency(TransparencyAttrib.MAlpha)
                cloud_node_path.setLightOff()
            
            print(f"Created cloud layer {layer_idx} with {num_clouds} clouds at height {layer['height']}")
        
        return cloud_node
    
    def _create_cloud_ring(self, distance, height, density, seed):
        """Create a ring of clouds at specified distance and height."""
        format = GeomVertexFormat.getV3c4()
        vdata = GeomVertexData("cloud_ring", format, Geom.UHStatic)
        
        # Generate cloud patches
        cloud_patches = []
        segments = 32
        
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            
            # Random cloud presence
            if self._cloud_noise(angle, seed) > (1.0 - density):
                x = distance * math.cos(angle)
                z = distance * math.sin(angle)
                
                # Vary cloud height slightly
                cloud_height = height + self._cloud_noise(angle * 2, seed + 10) * 50
                
                cloud_patches.append((x, z, cloud_height, angle))
        
        if not cloud_patches:
            return self.render.attachNewNode("empty_clouds")
        
        # Create geometry for cloud patches
        vertices = []
        for x, z, y, angle in cloud_patches:
            # Create a simple quad for each cloud patch
            size = 100 + self._cloud_noise(angle * 3, seed + 20) * 50
            
            # Four corners of cloud quad
            vertices.extend([
                (x - size, z - size, y),
                (x + size, z - size, y),
                (x + size, z + size, y),
                (x - size, z + size, y),
            ])
        
        vdata.setNumRows(len(vertices))
        vertex_writer = GeomVertexWriter(vdata, "vertex")
        color_writer = GeomVertexWriter(vdata, "color")
        
        cloud_color = Vec4(1.0, 1.0, 1.0, 0.6)  # Semi-transparent white
        
        for x, z, y in vertices:
            vertex_writer.addData3(x, z, y)
            color_writer.addData4(cloud_color)
        
        # Create triangles
        geom = Geom(vdata)
        tris = GeomTriangles(Geom.UHStatic)
        
        for i in range(len(cloud_patches)):
            base = i * 4
            # Two triangles per cloud quad
            tris.addVertices(base, base + 1, base + 2)
            tris.addVertices(base, base + 2, base + 3)
        
        tris.closePrimitive()
        geom.addPrimitive(tris)
        
        cloud_geom_node = GeomNode("cloud_ring")
        cloud_geom_node.addGeom(geom)
        cloud_np = self.render.attachNewNode(cloud_geom_node)
        
        # Enable transparency
        cloud_np.setTransparency(TransparencyAttrib.MAlpha)
        
        return cloud_np
    
    def _cloud_noise(self, x, seed):
        """Simple noise for cloud generation."""
        return (math.sin(x * 2.3 + seed) + 
                math.sin(x * 5.7 + seed * 1.4) * 0.5 + 
                math.sin(x * 11.3 + seed * 1.8) * 0.25) / 1.75 + 0.5
    
    def _create_fluffy_cloud(self, base_size, name):
        """Create a fluffy cloud using CardMaker for compatibility."""
        # Create a single cloud card with natural proportions
        cm_main = CardMaker(f"fluffy_cloud_{name}")
        
        # Make clouds horizontally stretched (natural cloud shape)
        width = base_size * 1.4
        height = base_size * 0.6
        cm_main.setFrame(-width/2, width/2, -height/3, height*0.7)
        
        # Return the PandaNode from CardMaker
        return cm_main.generate()
    
    def _create_sun(self):
        """Create a bright, circular sun in the mountain sky."""
        sun_node = self.render.attachNewNode("sun_system")
        
        # Create circular sun disk using geometry
        sun_geom = self._create_circular_sun(60)  # Radius 60
        sun_disk = sun_node.attachNewNode(sun_geom)
        
        # Position sun higher and more visible
        sun_distance = 1400
        sun_elevation = math.pi / 4  # 45 degrees up (more visible)
        sun_azimuth = math.pi / 4    # 45 degrees around (southeast)
        
        sun_x = sun_distance * math.cos(sun_elevation) * math.cos(sun_azimuth)
        sun_z = sun_distance * math.cos(sun_elevation) * math.sin(sun_azimuth)
        sun_y = sun_distance * math.sin(sun_elevation)
        
        sun_disk.setPos(sun_x, sun_z, sun_y)
        # Make sun face directly towards the camera by using billboard point eye
        # but constrain it to avoid rotation with camera movement
        sun_disk.setBillboardPointEye()
        
        # Brightest center core
        sun_disk.setColor(1.5, 1.4, 1.0, 1.0)  # Very bright center
        sun_disk.setLightOff()
        sun_disk.setBin("fixed", 102)
        sun_disk.setDepthTest(False)
        sun_disk.setDepthWrite(False)
        sun_disk.setRenderModeWireframe(False)  # Ensure it's solid
        
        # Create circular layered glow for 3D depth effect
        glow_layers = [
            {"radius": 90, "color": Vec4(1.3, 1.2, 0.8, 0.7)},
            {"radius": 130, "color": Vec4(1.1, 1.0, 0.6, 0.4)},
            {"radius": 180, "color": Vec4(1.0, 0.8, 0.5, 0.2)},
        ]
        
        for i, layer in enumerate(glow_layers):
            glow_geom = self._create_simple_circle(layer["radius"])
            glow_card = sun_node.attachNewNode(glow_geom)
            glow_card.setPos(sun_x, sun_z, sun_y)
            # Make glow face camera with billboard
            glow_card.setBillboardPointEye()
            glow_card.setColor(layer["color"])
            glow_card.setTransparency(TransparencyAttrib.MAlpha)
            glow_card.setLightOff()
            glow_card.setBin("fixed", 101 - i)
            glow_card.setDepthTest(False)
            glow_card.setDepthWrite(False)
        
        print(f"Created circular sun at position ({sun_x:.0f}, {sun_z:.0f}, {sun_y:.0f})")
        print(f"Sun elevation: {math.degrees(sun_elevation):.1f}°, azimuth: {math.degrees(sun_azimuth):.1f}°")
        
        return sun_node
    
    def _create_simple_circle(self, radius):
        """Create a perfect circular geometry that maintains shape."""
        format = GeomVertexFormat.getV3()
        vdata = GeomVertexData("simple_circle", format, Geom.UHStatic)
        
        # Create perfect circle vertices with high segment count for smoothness
        segments = 32  # Higher segments for perfect circle
        vertices = []
        
        # Center vertex
        vertices.append((0, 0, 0))
        
        # Circle edge vertices - create in XZ plane so it faces forward when billboarded
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)
            vertices.append((x, 0, z))  # XZ plane so it faces towards camera
        
        vdata.setNumRows(len(vertices))
        vertex_writer = GeomVertexWriter(vdata, "vertex")
        
        for x, y, z in vertices:
            vertex_writer.addData3(x, y, z)
        
        # Create triangles from center to edge
        geom = Geom(vdata)
        tris = GeomTriangles(Geom.UHStatic)
        
        for i in range(segments):
            next_i = (i + 1) % segments
            tris.addVertices(0, i + 1, next_i + 1)
        
        tris.closePrimitive()
        geom.addPrimitive(tris)
        
        # Create geometry node
        circle_geom_node = GeomNode("simple_circle")
        circle_geom_node.addGeom(geom)
        
        return circle_geom_node
    
    def _create_circular_sun(self, radius):
        """Create a realistic circular sun with gradient effect."""
        format = GeomVertexFormat.getV3c4()  # Include color for gradient
        vdata = GeomVertexData("circular_sun", format, Geom.UHStatic)
        
        # Create circle vertices with gradient colors
        segments = 24  # More segments for smoother circle
        vertices = []
        colors = []
        
        # Center vertex - brightest
        vertices.append((0, 0, 0))
        colors.append(Vec4(1.5, 1.4, 1.0, 1.0))  # Bright white-yellow center
        
        # Create concentric rings for gradient effect
        for ring in range(3):  # 3 rings for smooth gradient
            ring_radius = radius * (ring + 1) / 3
            ring_brightness = 1.2 - (ring * 0.3)  # Fade from center
            
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                x = ring_radius * math.cos(angle)
                z = ring_radius * math.sin(angle)
                vertices.append((x, 0, z))
                
                # Sun gradient colors
                colors.append(Vec4(
                    1.3 * ring_brightness,  # Red component
                    1.2 * ring_brightness,  # Green component 
                    0.8 * ring_brightness,  # Blue component (warm sun)
                    1.0 - (ring * 0.2)      # Slight transparency at edges
                ))
        
        vdata.setNumRows(len(vertices))
        vertex_writer = GeomVertexWriter(vdata, "vertex")
        color_writer = GeomVertexWriter(vdata, "color")
        
        for (x, y, z), color in zip(vertices, colors):
            vertex_writer.addData3(x, y, z)
            color_writer.addData4(color)
        
        # Create triangles connecting rings
        geom = Geom(vdata)
        tris = GeomTriangles(Geom.UHStatic)
        
        # Connect center to first ring
        for i in range(segments):
            next_i = (i + 1) % segments
            tris.addVertices(0, i + 1, next_i + 1)
        
        # Connect rings together
        for ring in range(2):  # Connect ring 0-1 and ring 1-2
            ring_start = 1 + ring * segments
            next_ring_start = 1 + (ring + 1) * segments
            
            for i in range(segments):
                next_i = (i + 1) % segments
                
                # Current ring vertices
                v0 = ring_start + i
                v1 = ring_start + next_i
                
                # Next ring vertices
                v2 = next_ring_start + i
                v3 = next_ring_start + next_i
                
                # Two triangles to connect rings
                tris.addVertices(v0, v2, v1)
                tris.addVertices(v1, v2, v3)
        
        tris.closePrimitive()
        geom.addPrimitive(tris)
        
        # Create geometry node
        sun_geom_node = GeomNode("circular_sun")
        sun_geom_node.addGeom(geom)
        
        return sun_geom_node
    
    def update(self, camera_pos):
        """Update skybox to follow camera."""
        if self.skybox_node:
            # Keep skybox centered on camera (only X and Z, not Y)
            self.skybox_node.setPos(camera_pos.x, camera_pos.y, 0)