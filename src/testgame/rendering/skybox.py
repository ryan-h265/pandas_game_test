"""Skybox system for creating atmospheric mountain environments."""

import math
from pathlib import Path
from panda3d.core import (
    GeomVertexFormat,
    GeomVertexData,
    GeomVertexWriter,
    Geom,
    GeomTriangles,
    GeomNode,
    Vec3,
    Vec4,
    TransparencyAttrib,
    ColorBlendAttrib,
    Shader,
)


class MountainSkybox:
    """Creates a procedural skybox with distant mountains, clouds, and sun."""

    def __init__(self, render, camera, base):
        """Initialize the skybox.

        Args:
            render: Panda3D render node
            camera: Camera node for positioning
            base: ShowBase instance for camera lens access
        """
        self.render = render
        self.camera = camera
        self.base = base
        self.skybox_node = None
        self.cloud_nodes = []  # Track cloud nodes for animation
        self.animation_time = 0.0  # Track time for cloud movement
        self.sky_shader = None  # Sky shader reference
        self.cloud_shader = None  # Cloud shader reference
        self._load_shaders()

    def _load_shaders(self):
        """Load sky and cloud shaders."""
        shader_dir = Path(__file__).resolve().parents[3] / "assets" / "shaders"
        
        # Load sky shader
        sky_vert = shader_dir / "sky.vert"
        sky_frag = shader_dir / "sky.frag"
        if sky_vert.exists() and sky_frag.exists():
            self.sky_shader = Shader.load(
                Shader.SL_GLSL, vertex=str(sky_vert), fragment=str(sky_frag)
            )
            if self.sky_shader:
                print("Successfully loaded sky shader")
        else:
            print("Warning: Sky shader files not found")
        
        # Load cloud shader
        cloud_vert = shader_dir / "cloud.vert"
        cloud_frag = shader_dir / "cloud.frag"
        if cloud_vert.exists() and cloud_frag.exists():
            self.cloud_shader = Shader.load(
                Shader.SL_GLSL, vertex=str(cloud_vert), fragment=str(cloud_frag)
            )
            if self.cloud_shader:
                print("Successfully loaded cloud shader")

    def create_skybox(self):
        """Create complete mountain skybox with sky dome, mountains, sun, and clouds."""
        # Create the base skybox structure
        self.skybox_node = self.render.attachNewNode("mountain_skybox")

        # Create shader-driven sky dome
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
        print(
            f"Skybox components: sky quad, {mountain_ring.getNumChildren()} mountain ranges, sun, clouds"
        )

        return self.skybox_node

    def _create_sky_dome(self):
        """Create sky dome with shader-based procedural rendering."""
        import math
        
        # Create inverted hemisphere geometry for sky
        sky_geom = self._create_sky_hemisphere(1800, 32, 16)
        sky_dome = self.render.attachNewNode(sky_geom)
        
        # Apply sky shader
        if self.sky_shader:
            sky_dome.setShader(self.sky_shader)
            # Pass shader uniforms
            sky_dome.setShaderInput("zenithColor", Vec3(0.4, 0.6, 0.95))
            sky_dome.setShaderInput("horizonColor", Vec3(0.8, 0.9, 1.0))
            sky_dome.setShaderInput("sunDirection", Vec3(0.5, 0.5, 0.7).normalized())
            # Camera vectors will be updated per frame in update()
            print("Applied sky shader to sky dome")
        else:
            # Fallback: solid color
            sky_dome.setColor(Vec4(0.5, 0.7, 1.0, 1.0))
            print("Warning: No sky shader, using solid color")
        
        sky_dome.setLightOff()
        sky_dome.setBin("background", 0)
        sky_dome.setDepthWrite(False)
        sky_dome.setDepthTest(False)
        sky_dome.setTwoSided(True)
        
        return sky_dome
    
    def _create_sky_hemisphere(self, radius, lon_segs, lat_segs):
        """Create simple hemisphere geometry for sky (no vertex colors, shader-driven)."""
        import math
        
        format = GeomVertexFormat.getV3n3()
        vdata = GeomVertexData("sky_hemisphere", format, Geom.UHStatic)
        
        vertices = []
        
        # Generate hemisphere vertices (only upper half)
        for lat in range(lat_segs + 1):
            lat_angle = (math.pi * 0.5) * lat / lat_segs  # 0 to π/2
            
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
            # Normals point inward (inverted for inside viewing)
            normal_writer.addData3(-x, -y, -z)
        
        # Create triangles
        geom = Geom(vdata)
        tris = GeomTriangles(Geom.UHStatic)
        
        for lat in range(lat_segs):
            for lon in range(lon_segs):
                i0 = lat * (lon_segs + 1) + lon
                i1 = lat * (lon_segs + 1) + (lon + 1)
                i2 = (lat + 1) * (lon_segs + 1) + lon
                i3 = (lat + 1) * (lon_segs + 1) + (lon + 1)
                
                # Reverse winding for inverted geometry
                tris.addVertices(i0, i1, i2)
                tris.addVertices(i1, i3, i2)
        
        tris.closePrimitive()
        geom.addPrimitive(tris)
        
        geom_node = GeomNode("sky_hemisphere")
        geom_node.addGeom(geom)
        return geom_node

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
                seed=i * 100,
            )
            range_node.reparentTo(mountain_node)

        return mountain_node

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

        # Add base points (below ground level to eliminate floating appearance)
        base_points = []
        for x, z, _ in points:
            base_points.append((x, z, -50))  # Extend below ground level

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

        # Set mountains to render after clouds
        mountain_np.setBin("background", 10)  # Higher priority than clouds
        mountain_np.setDepthWrite(False)
        mountain_np.setDepthTest(False)

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

        # Create clouds farther than mountains (behind terrain)
        cloud_layers = [
            {
                "distance": 2200,
                "height": 400,
                "size": 180,
                "density": 0.3,
                "color": Vec4(1.0, 1.0, 1.0, 0.6),
            },
            {
                "distance": 2000,
                "height": 550,
                "size": 150,
                "density": 0.25,
                "color": Vec4(0.95, 0.95, 0.98, 0.5),
            },
            {
                "distance": 1900,
                "height": 700,
                "size": 120,
                "density": 0.2,
                "color": Vec4(0.9, 0.9, 0.95, 0.4),
            },
        ]

        for layer_idx, layer in enumerate(cloud_layers):
            layer_node = cloud_node.attachNewNode(f"cloud_layer_{layer_idx}")

            # Create scattered clouds around the mountains
            num_clouds = int(16 * layer["density"])

            for i in range(num_clouds):
                angle = (
                    2 * math.pi * i / num_clouds + layer_idx * 0.3
                )  # Offset each layer

                # Add some randomness to cloud positions
                angle_offset = math.sin(angle * 3.7 + layer_idx) * 0.2
                distance_offset = math.sin(angle * 2.3 + layer_idx) * 100

                actual_angle = angle + angle_offset
                actual_distance = layer["distance"] + distance_offset

                x = actual_distance * math.cos(actual_angle)
                z = actual_distance * math.sin(actual_angle)

                # Create fluffy cloud with size variation
                cloud_base_size = layer["size"] + (i % 3) * 20
                cloud_cluster = self._create_fluffy_cloud(
                    cloud_base_size, f"cloud_{layer_idx}_{i}"
                )

                # Position cloud and set properties
                cloud_cluster.setPos(x, z, layer["height"])
                cloud_cluster.setColor(layer["color"])
                cloud_cluster.setTransparency(TransparencyAttrib.MAlpha)
                cloud_cluster.setLightOff()

                # Apply cloud shader for realistic rendering
                if self.cloud_shader:
                    cloud_cluster.setShader(self.cloud_shader)
                    # Set shader inputs
                    cloud_cluster.setShaderInput(
                        "lightDirection", Vec3(1, 1, -1)
                    )  # Sun direction
                    cloud_cluster.setShaderInput(
                        "sunColor", Vec3(1.0, 0.95, 0.8)
                    )  # Warm sun color
                    cloud_cluster.setShaderInput(
                        "time", 0.0
                    )  # Will be updated in update()
                    cloud_cluster.setShaderInput(
                        "cloudDensity", 0.8 + layer_idx * 0.1
                    )  # Vary density by layer
                    cloud_cluster.setShaderInput("camera", self.camera.getPos())

                # Ensure clouds render behind terrain but still visible
                cloud_cluster.setBin(
                    "background", 1 + layer_idx
                )  # Just behind sky dome
                cloud_cluster.setDepthWrite(False)
                cloud_cluster.setDepthTest(
                    False
                )  # Background elements don't need depth test

                # Reparent to layer and track for animation
                cloud_cluster.reparentTo(layer_node)

                # Store cloud info for animation
                cloud_info = {
                    "node": cloud_cluster,
                    "original_x": x,
                    "original_z": z,
                    "speed": 0.5 + (i % 3) * 0.2,  # Varying speeds
                    "layer": layer_idx,
                }
                self.cloud_nodes.append(cloud_info)

            print(
                f"Created cloud layer {layer_idx} with {num_clouds} clouds at height {layer['height']}"
            )

        return cloud_node

    def _cloud_noise(self, x, seed):
        """Simple noise for cloud generation."""
        return (
            math.sin(x * 2.3 + seed)
            + math.sin(x * 5.7 + seed * 1.4) * 0.5
            + math.sin(x * 11.3 + seed * 1.8) * 0.25
        ) / 1.75 + 0.5

    def _create_fluffy_cloud(self, base_size, name):
        """Create a soft, natural-looking cloud using circular geometry."""
        # Create cloud using circular puffs instead of rectangles
        cloud_geom = self._create_soft_cloud_geometry(base_size, name)
        return cloud_geom

    def _create_soft_cloud_geometry(self, size, name):
        """Create natural cloud geometry with soft, rounded edges."""
        # Create cloud root to hold multiple circular puffs
        cloud_root = self.render.attachNewNode(f"soft_cloud_{name}")

        # Create multiple overlapping circular puffs for soft appearance
        num_puffs = 6 + int(size / 30)  # More puffs for smoother clouds

        for puff_idx in range(num_puffs):
            # Create circular puff geometry
            puff_radius = size * (0.4 + 0.3 * abs(math.sin(puff_idx * 1.7)))
            puff_geom = self._create_soft_circle(puff_radius, f"{name}_puff_{puff_idx}")
            puff_node = cloud_root.attachNewNode(puff_geom)

            # Position puffs in natural clustering
            if puff_idx == 0:
                # Center puff
                puff_x, puff_y = 0, 0
                opacity = 0.8
            else:
                # Surrounding puffs with natural variation
                angle = 2 * math.pi * (puff_idx - 1) / (num_puffs - 1)
                # Add irregularity for natural shape
                angle += 0.4 * math.sin(puff_idx * 2.3)

                distance = size * (0.2 + 0.3 * abs(math.sin(puff_idx * 1.9)))
                puff_x = distance * math.cos(angle)
                puff_y = distance * math.sin(angle)
                opacity = 0.5 + 0.3 * abs(math.sin(puff_idx * 2.1))

            puff_node.setPos(puff_x, puff_y, 0)

            # Set soft cloud appearance with enhanced blending
            puff_node.setColor(1.0, 1.0, 1.0, opacity)
            puff_node.setTransparency(TransparencyAttrib.MAlpha)
            # Remove billboard - use static orientation to avoid compression
            # puff_node.lookAt(0, 0, 0)  # Face towards center instead of billboarding
            puff_node.lookAt(
                cloud_root.getPos()
            )  # Face towards cloud center instead of billboarding
            puff_node.setLightOff()

            # Enhanced soft rendering for blurred edges
            puff_node.setBin("background", 2 + puff_idx)  # Just behind sky dome
            puff_node.setDepthWrite(False)  # Essential for soft blending
            puff_node.setDepthTest(False)  # Background elements don't need depth test

            # Enable additive blending for softer cloud overlap
            puff_node.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd))

            # Vary scale for natural irregularity
            scale_variation = 0.8 + 0.4 * abs(math.sin(puff_idx * 3.1))
            puff_node.setScale(scale_variation)

        return cloud_root

    def _create_soft_circle(self, radius, name):
        """Create a soft oblong cloud geometry with feathered edges."""
        format = GeomVertexFormat.getV3c4()  # Include color for feathered edges
        vdata = GeomVertexData(name, format, Geom.UHStatic)

        # Create smooth oblong with more segments for soft edges
        segments = 32  # Higher segment count for smoother feathered edges
        vertices = []
        colors = []

        # Center vertex - fully opaque
        vertices.append((0, 0, 0))
        colors.append(Vec4(1.0, 1.0, 1.0, 1.0))

        # Create multiple concentric rings for ultra-smooth falloff
        rings = 8  # Many more rings for very smooth gradient
        for ring in range(rings):
            ring_progress = (ring + 1) / rings

            for i in range(segments):
                angle = 2 * math.pi * i / segments

                # Create oblong shape - stretch horizontally for natural cloud shape
                horizontal_stretch = 1.8  # Make clouds wider than tall
                vertical_compression = 0.6  # Flatten vertically

                base_x = radius * ring_progress * math.cos(angle) * horizontal_stretch
                base_z = radius * ring_progress * math.sin(angle) * vertical_compression

                # Create smooth, soft edges instead of pointy variations
                # Use smooth falloff instead of sharp edge variation
                smooth_falloff = 1.0 - (
                    ring_progress * 0.1
                )  # Very gentle size reduction

                # Add subtle, smooth variation for natural shape
                gentle_variation = 0.05 * math.sin(angle * 3.1 + ring * 0.7)

                x = base_x * (smooth_falloff + gentle_variation)
                z = base_z * (smooth_falloff + gentle_variation)

                # Create slight volume variation
                y = radius * 0.08 * math.sin(angle * 5.1 + ring * 1.9) * ring_progress

                vertices.append((x, y, z))

                # Smooth opacity falloff for blurred edges
                # Use smooth mathematical falloff for natural cloud transparency
                center_distance = ring_progress

                # Smooth exponential falloff for soft edges
                opacity = math.exp(-center_distance * 3.0)  # Exponential falloff

                # Additional smooth cosine falloff for even softer edges
                opacity *= math.cos(center_distance * math.pi * 0.5) ** 2

                # Ensure minimum visibility but very soft edges
                opacity = max(0.02, opacity * 0.8)

                colors.append(Vec4(1.0, 1.0, 1.0, opacity))

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
        for ring in range(rings - 1):
            ring_start = 1 + ring * segments
            next_ring_start = 1 + (ring + 1) * segments

            for i in range(segments):
                next_i = (i + 1) % segments

                v0 = ring_start + i
                v1 = ring_start + next_i
                v2 = next_ring_start + i
                v3 = next_ring_start + next_i

                # Two triangles per segment
                tris.addVertices(v0, v2, v1)
                tris.addVertices(v1, v2, v3)

        tris.closePrimitive()
        geom.addPrimitive(tris)

        # Create geometry node
        circle_geom_node = GeomNode(name)
        circle_geom_node.addGeom(geom)

        return circle_geom_node

    def _animate_clouds(self):
        """Animate cloud movement and subtle transformations."""
        for cloud_info in self.cloud_nodes:
            cloud_node = cloud_info["node"]
            if not cloud_node or cloud_node.isEmpty():
                continue

            # Update shader time for procedural animation
            if self.cloud_shader:
                cloud_node.setShaderInput("time", self.animation_time)
                cloud_node.setShaderInput("camera", self.camera.getPos())

            # Drift clouds slowly across the sky
            drift_speed = cloud_info["speed"] * 2.0  # Units per second
            drift_x = math.sin(self.animation_time * 0.1 * drift_speed) * 20
            drift_z = self.animation_time * drift_speed

            # Wrap around when clouds drift too far
            max_drift = 500
            if drift_z > max_drift:
                # Reset cloud position to other side
                drift_z -= max_drift * 2

            new_x = cloud_info["original_x"] + drift_x
            new_z = cloud_info["original_z"] + drift_z

            current_pos = cloud_node.getPos()
            cloud_node.setPos(new_x, new_z, current_pos.z)

            # Subtle size pulsing for living clouds
            pulse_scale = 1.0 + 0.05 * math.sin(
                self.animation_time * 0.5 + cloud_info["layer"]
            )
            cloud_node.setScale(pulse_scale, pulse_scale, 1.0)

            # Gentle rotation
            rotation_speed = 5.0  # degrees per second
            current_h = cloud_node.getH()
            cloud_node.setH(current_h + rotation_speed * 0.016)  # Assuming 60fps

    def _create_sun(self):
        """Create a bright, circular sun in the mountain sky."""
        sun_node = self.render.attachNewNode("sun_system")

        # Create circular sun disk using geometry
        sun_geom = self._create_circular_sun(60)  # Radius 60
        sun_disk = sun_node.attachNewNode(sun_geom)

        # Position sun higher and more visible
        sun_distance = 1400
        sun_elevation = math.pi / 4  # 45 degrees up (more visible)
        sun_azimuth = math.pi / 4  # 45 degrees around (southeast)

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

        print(
            f"Created circular sun at position ({sun_x:.0f}, {sun_z:.0f}, {sun_y:.0f})"
        )
        print(
            f"Sun elevation: {math.degrees(sun_elevation):.1f}°, azimuth: {math.degrees(sun_azimuth):.1f}°"
        )

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
                colors.append(
                    Vec4(
                        1.3 * ring_brightness,  # Red component
                        1.2 * ring_brightness,  # Green component
                        0.8 * ring_brightness,  # Blue component (warm sun)
                        1.0 - (ring * 0.2),  # Slight transparency at edges
                    )
                )

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

    def update(self, camera_pos, dt=0.016):
        """Update skybox to follow camera and animate clouds.

        Args:
            camera_pos: Camera position
            dt: Delta time for animation (default 60fps)
        """
        if self.skybox_node:
            # Keep skybox centered on camera (only X and Y, not Z)
            self.skybox_node.setPos(camera_pos.x, camera_pos.y, 0)

            # Sky shader doesn't need per-frame updates for dome approach
            # (colors and sun direction are set once at creation)

            # Animate clouds
            self.animation_time += dt
            self._animate_clouds()
