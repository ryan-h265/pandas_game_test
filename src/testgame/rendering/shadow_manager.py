"""Cascaded shadow map manager with PCF and denoising."""

from pathlib import Path
from panda3d.core import (
    OrthographicLens,
    Texture,
    FrameBufferProperties,
    Shader,
    Vec3,
    Vec4,
    Mat4,
)


class ShadowManager:
    """Manages cascaded shadow maps with soft shadows and denoising."""

    def __init__(self, base_instance, render, light_direction=Vec3(1, 1, -1)):
        """Initialize shadow mapping system.

        Args:
            base_instance: The ShowBase instance
            render: The root render node
            light_direction: Direction vector for the directional light
        """
        self.base = base_instance
        self.render = render
        self.light_direction = light_direction.normalized()

        # Shadow map configuration - ULTRA-LOW settings for performance
        self.shadow_map_size = 256  # Very low resolution for max FPS (was 512)
        self.num_cascades = 1  # Only 1 cascade for performance (was 2)
        self.cascade_splits = [40.0, 100.0, 250.0]  # View space split distances
        self.shadow_softness = 0.5  # Minimal softness for speed (was 1.0)

        # Storage for shadow cameras and buffers
        self.shadow_cameras = []
        self.shadow_buffers = []
        self.shadow_textures = []

        # Create shadow cascades
        self._setup_shadow_cascades()

        # Load shaders
        self._setup_shaders()

    def _setup_shadow_cascades(self):
        """Create shadow map buffers and cameras for each cascade."""
        for i in range(self.num_cascades):
            # Create depth texture
            depth_tex = Texture(f"shadow_map_{i}")
            depth_tex.setMinfilter(Texture.FTLinear)
            depth_tex.setMagfilter(Texture.FTLinear)
            depth_tex.setWrapU(Texture.WMClamp)
            depth_tex.setWrapV(Texture.WMClamp)
            depth_tex.setup2dTexture(
                self.shadow_map_size,
                self.shadow_map_size,
                Texture.TFloat,
                Texture.FDepthComponent,
            )

            # Create offscreen buffer
            fb_props = FrameBufferProperties()
            fb_props.setDepthBits(24)
            fb_props.setRgbColor(False)

            buffer = self.base.win.makeTextureBuffer(
                f"shadow_buffer_{i}",
                self.shadow_map_size,
                self.shadow_map_size,
                depth_tex,
                True,  # to_ram
            )

            if not buffer:
                print(f"Failed to create shadow buffer {i}")
                continue

            # Make buffer invisible
            buffer.setClearColorActive(False)
            buffer.setClearDepthActive(True)

            # Create camera for this cascade
            camera_np = self.base.makeCamera(buffer, scene=self.render)
            camera = camera_np.node()

            # Set up orthographic lens for directional light
            lens = OrthographicLens()
            lens.setNearFar(1, 500)
            lens.setFilmSize(50, 50)
            camera.setLens(lens)

            # Store references
            self.shadow_cameras.append(camera_np)
            self.shadow_buffers.append(buffer)
            self.shadow_textures.append(depth_tex)

            print(
                f"Created shadow cascade {i}: {self.shadow_map_size}x{self.shadow_map_size}"
            )

    def _setup_shaders(self):
        """Load and configure shadow shaders."""
        # Get absolute path to shaders
        shader_dir = Path(__file__).resolve().parents[3] / "assets" / "shaders"
        vert_path = shader_dir / "terrain.vert"
        frag_path = shader_dir / "terrain.frag"

        # Load terrain shader
        shader = Shader.load(
            Shader.SL_GLSL, vertex=str(vert_path), fragment=str(frag_path)
        )

        if shader:
            self.render.setShader(shader)
            print("Shadow shaders loaded successfully")
        else:
            print(f"Failed to load shadow shaders from {shader_dir}")
            print("Shaders will not be active")

    def update_cascade_cameras(self, camera_pos, camera_frustum_corners):
        """Update shadow camera positions and projections for each cascade.

        Args:
            camera_pos: Current camera position (Vec3)
            camera_frustum_corners: List of frustum corners for cascade fitting
        """
        # For simplicity, position cameras along light direction
        # In production, you'd calculate tight bounds around view frustum
        for i, camera_np in enumerate(self.shadow_cameras):
            # Calculate center of cascade coverage
            distance = self.cascade_splits[i] * 0.7
            center = camera_pos + Vec3(0, distance, 0)

            # Position camera along light direction
            cam_pos = center - self.light_direction * 100

            # Look at center point
            camera_np.setPos(cam_pos)
            camera_np.lookAt(center)

            # Adjust orthographic size based on cascade
            size = self.cascade_splits[i] * 1.2
            lens = camera_np.node().getLens()
            lens.setFilmSize(size, size)

    def set_shader_inputs(self, node_path, ssao_enabled=True, point_light_manager=None):
        """Set shader inputs for shadow rendering.

        Args:
            node_path: NodePath to apply shadow inputs to
            ssao_enabled: Enable ambient occlusion (default: True)
            point_light_manager: Optional PointLightManager instance for dynamic lights
        """
        # Set shadow map textures
        # Always provide 3 textures to match shader expectations
        for i in range(3):  # Always provide 3 textures
            if i < len(self.shadow_textures):
                # Use actual texture for active cascades
                tex = self.shadow_textures[i]
            else:
                # Use the first texture for inactive cascades (fallback)
                tex = self.shadow_textures[0] if self.shadow_textures else None
            
            if tex:
                node_path.setShaderInput(f"shadowMap{i}", tex)

        # Set shadow matrices (world to shadow projection)
        # Always provide 3 matrices to match shader expectations
        for i in range(3):  # Always provide 3 matrices
            if i < len(self.shadow_cameras):
                # Use actual camera for active cascades
                camera_np = self.shadow_cameras[i]
                # Get camera projection matrix
                lens = camera_np.node().getLens()
                proj_mat = Mat4(lens.getProjectionMat())

                # Get camera view matrix
                view_mat = Mat4()
                view_mat.invertFrom(camera_np.getMat(self.render))

                # Combined shadow matrix
                shadow_mat = proj_mat * view_mat
            else:
                # Use identity matrix for inactive cascades
                shadow_mat = Mat4.identMat()

            node_path.setShaderInput(f"shadowMatrix{i}", shadow_mat)

        # Set other uniforms
        node_path.setShaderInput("lightDirection", self.light_direction)
        node_path.setShaderInput("lightColor", Vec3(0.8, 0.8, 0.7))
        node_path.setShaderInput("ambientColor", Vec3(0.3, 0.3, 0.3))
        node_path.setShaderInput(
            "cascadeSplits",
            Vec4(
                self.cascade_splits[0],
                self.cascade_splits[1],
                self.cascade_splits[2],
                999999.0,
            ),
        )
        node_path.setShaderInput(
            "shadowMapSize", Vec4(self.shadow_map_size, self.shadow_map_size, 0, 0)
        )
        node_path.setShaderInput("shadowSoftness", self.shadow_softness)
        node_path.setShaderInput(
            "useVertexColor", 0
        )  # Default to not using vertex colors

        # Set SSAO uniforms
        node_path.setShaderInput("ssaoEnabled", 1 if ssao_enabled else 0)
        node_path.setShaderInput("ssaoRadius", 1.5)  # Occlusion radius
        node_path.setShaderInput("ssaoBias", 0.025)  # Depth bias
        node_path.setShaderInput("ssaoStrength", 0.8)  # AO strength (0.0-2.0)

        # Set point light uniforms (if manager provided)
        if point_light_manager:
            point_light_manager.set_shader_inputs(node_path)
        else:
            # No lights - set defaults
            node_path.setShaderInput("numPointLights", 0)

    def set_light_direction(self, direction):
        """Update light direction.

        Args:
            direction: New light direction vector (Vec3)
        """
        self.light_direction = direction.normalized()

    def set_shadow_softness(self, softness):
        """Adjust shadow softness.

        Args:
            softness: Softness factor (1.0-10.0 recommended)
        """
        self.shadow_softness = max(0.1, softness)

    def set_ssao_enabled(self, node_path, enabled):
        """Enable or disable SSAO.

        Args:
            node_path: NodePath to update
            enabled: True to enable, False to disable
        """
        node_path.setShaderInput("ssaoEnabled", 1 if enabled else 0)

    def set_ssao_strength(self, node_path, strength):
        """Adjust SSAO strength.

        Args:
            node_path: NodePath to update
            strength: AO strength (0.0-2.0 recommended)
        """
        node_path.setShaderInput("ssaoStrength", max(0.0, min(2.0, strength)))

    def set_ssao_radius(self, node_path, radius):
        """Adjust SSAO radius.

        Args:
            node_path: NodePath to update
            radius: Occlusion radius (0.5-5.0 recommended)
        """
        node_path.setShaderInput("ssaoRadius", max(0.5, min(5.0, radius)))

    def cleanup(self):
        """Clean up shadow resources."""
        for buffer in self.shadow_buffers:
            if buffer:
                self.base.graphicsEngine.removeWindow(buffer)

        self.shadow_cameras.clear()
        self.shadow_buffers.clear()
        self.shadow_textures.clear()
