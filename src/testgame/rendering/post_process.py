"""Post-processing effects: SSAO and shadow denoising."""

import random
from panda3d.core import (
    Texture,
    Shader,
    Vec3,
    Vec4,
)


class PostProcessManager:
    """Manages post-processing effects like SSAO and denoising."""

    def __init__(self, render, camera):
        """Initialize post-processing.

        Args:
            render: Root render node
            camera: Main camera
        """
        self.render = render
        self.camera = camera
        self.enabled = True

        # SSAO settings
        self.ssao_radius = 1.5
        self.ssao_bias = 0.025
        self.ssao_kernel_size = 32

        # Denoising settings
        self.denoise_spatial_sigma = 2.0
        self.denoise_depth_sigma = 0.1
        self.denoise_kernel_size = 5

        # Generate SSAO kernel
        self.ssao_samples = self._generate_ssao_kernel()

        # Setup render targets and shaders
        self._setup_buffers()

    def _generate_ssao_kernel(self):
        """Generate random samples for SSAO hemisphere.

        Returns:
            List of Vec3 samples in hemisphere
        """
        samples = []
        for i in range(64):
            # Random point in hemisphere
            sample = Vec3(
                random.random() * 2.0 - 1.0,
                random.random() * 2.0 - 1.0,
                random.random(),
            )
            sample.normalize()

            # Scale to distribute samples (more near center)
            scale = float(i) / 64.0
            scale = 0.1 + scale * scale * 0.9
            sample *= scale

            samples.append(sample)

        return samples

    def _generate_noise_texture(self):
        """Generate noise texture for SSAO.

        Returns:
            Texture with random rotation vectors
        """
        noise_size = 4
        noise_tex = Texture("ssao_noise")
        noise_tex.setup2dTexture(
            noise_size, noise_size, Texture.TFloat, Texture.FRgba16
        )

        # Generate random rotation vectors
        noise_data = []
        for i in range(noise_size * noise_size):
            noise_data.extend(
                [
                    random.random() * 2.0 - 1.0,  # X
                    random.random() * 2.0 - 1.0,  # Y
                    0.0,  # Z (tangent space)
                    0.0,  # W (padding)
                ]
            )

        # Load data into texture
        noise_tex.setRamImage(noise_data)

        return noise_tex

    def _setup_buffers(self):
        """Setup render-to-texture buffers for post-processing."""
        # For now, we'll apply effects directly
        # In production, you'd set up multiple render targets
        print("Post-processing manager initialized")

    def apply_ssao(self, node_path):
        """Apply SSAO shader to node.

        Args:
            node_path: NodePath to apply SSAO to
        """
        shader = Shader.load(
            Shader.SL_GLSL,
            vertex="assets/shaders/denoise.vert",
            fragment="assets/shaders/ssao.frag",
        )

        if not shader:
            print("Failed to load SSAO shader")
            return

        # Generate noise texture
        noise_tex = self._generate_noise_texture()

        # Set shader and inputs
        node_path.setShader(shader)
        node_path.setShaderInput("noiseTexture", noise_tex)
        node_path.setShaderInput("radius", self.ssao_radius)
        node_path.setShaderInput("bias", self.ssao_bias)
        node_path.setShaderInput("kernelSize", self.ssao_kernel_size)

        # Set sample positions
        for i, sample in enumerate(self.ssao_samples[:64]):
            node_path.setShaderInput(f"samples[{i}]", sample)

    def apply_denoising(self, node_path, screen_size):
        """Apply bilateral denoising filter.

        Args:
            node_path: NodePath to apply denoising to
            screen_size: Tuple of (width, height)
        """
        shader = Shader.load(
            Shader.SL_GLSL,
            vertex="assets/shaders/denoise.vert",
            fragment="assets/shaders/denoise.frag",
        )

        if not shader:
            print("Failed to load denoise shader")
            return

        texel_size = Vec4(1.0 / screen_size[0], 1.0 / screen_size[1], 0, 0)

        node_path.setShader(shader)
        node_path.setShaderInput("texelSize", texel_size)
        node_path.setShaderInput("spatialSigma", self.denoise_spatial_sigma)
        node_path.setShaderInput("depthSigma", self.denoise_depth_sigma)
        node_path.setShaderInput("kernelSize", self.denoise_kernel_size)

    def set_ssao_radius(self, radius):
        """Adjust SSAO radius.

        Args:
            radius: New radius value
        """
        self.ssao_radius = max(0.1, radius)

    def set_denoise_strength(self, strength):
        """Adjust denoising strength.

        Args:
            strength: Denoising strength (0.1-5.0)
        """
        self.denoise_spatial_sigma = max(0.1, strength)

    def toggle(self):
        """Toggle post-processing on/off.

        Returns:
            New enabled state
        """
        self.enabled = not self.enabled
        return self.enabled
