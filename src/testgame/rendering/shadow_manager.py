"""Enhanced cascaded shadow map manager with animated sun and debug tools."""

from math import cos, pi, sin, sqrt
from pathlib import Path

from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import (
    FrameBufferProperties,
    Mat4,
    OrthographicLens,
    Shader,
    Texture,
    TransparencyAttrib,
    Vec2,
    Vec3,
    Vec4,
)

from testgame.config.settings import (
    FOG_COLOR,
    FOG_ENABLED,
    FOG_END_DISTANCE,
    FOG_START_DISTANCE,
    FOG_STRENGTH,
)
from testgame.config.shadow_config import (
    AMBIENT_COLOR,
    CASCADE_BIAS,
    CASCADE_BLEND_DISTANCE,
    CASCADE_SPLITS,
    LIGHT_COLOR,
    LIGHT_DIRECTION,
    MAX_SHADOW_DISTANCE,
    NUM_CASCADES,
    SHADOW_MAP_SIZE,
    SHADOW_SOFTNESS,
    SUN_ANIMATION_ENABLED,
    SUN_ANIMATION_SPEED,
    SUN_MAX_ELEVATION,
    SUN_MIN_ELEVATION,
    SUN_START_OFFSET,
)


class ShadowManager:
    """Manages cascaded shadow maps, sun motion, and shader inputs."""

    MAX_CASCADES = 4

    def __init__(self, base_instance, render, light_direction=None):
        self.base = base_instance
        self.render = render
        self.bound_nodes = []

        # Quality tuning
        self.shadow_map_size = int(SHADOW_MAP_SIZE)
        self.num_cascades = max(1, min(self.MAX_CASCADES, int(NUM_CASCADES)))
        self.cascade_targets = list(CASCADE_SPLITS)
        self.max_shadow_distance = float(MAX_SHADOW_DISTANCE)
        self.shadow_softness = float(SHADOW_SOFTNESS)
        self.cascade_blend_distance = float(CASCADE_BLEND_DISTANCE)
        self.cascade_bias = self._build_bias_vector(CASCADE_BIAS)
        self.shadow_inv_size = Vec2(1.0 / self.shadow_map_size, 1.0 / self.shadow_map_size)

        # Lighting state
        initial_direction = Vec3(*LIGHT_DIRECTION) if light_direction is None else light_direction
        self.light_direction = initial_direction.normalized()
        self.light_color = Vec3(*LIGHT_COLOR)
        self.ambient_color = Vec3(*AMBIENT_COLOR)

        # Sun animation parameters
        self.animate_sun = bool(SUN_ANIMATION_ENABLED)
        self.sun_speed = float(SUN_ANIMATION_SPEED)
        self.sun_time = float(SUN_START_OFFSET) % 1.0
        self.sun_min_elev = float(SUN_MIN_ELEVATION)
        self.sun_max_elev = float(SUN_MAX_ELEVATION)

        self._directional_light_np = None
        self._debug_overlays = []
        self._debug_enabled = False

        # Fog defaults
        self.fog_enabled = FOG_ENABLED
        self.fog_color = Vec3(*FOG_COLOR)
        self.fog_start = float(FOG_START_DISTANCE)
        self.fog_end = float(FOG_END_DISTANCE)
        self.fog_strength = float(FOG_STRENGTH)

        # Shadow resources
        self.shadow_cameras = []
        self.shadow_buffers = []
        self.shadow_textures = []
        self.shadow_matrices = [Mat4.identMat() for _ in range(self.MAX_CASCADES)]
        self.active_cascade_limits = [self.max_shadow_distance for _ in range(self.MAX_CASCADES)]

        self._setup_shadow_cascades()
        self._setup_shaders()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def bind_directional_light(self, light_np):
        """Attach a Panda3D directional light so it tracks the sun."""
        self._directional_light_np = light_np

    def apply_quality_settings(
        self,
        *,
        shadow_map_size=None,
        num_cascades=None,
        cascade_splits=None,
        max_shadow_distance=None,
        shadow_softness=None,
        sun_animation_speed=None,
    ):
        """Apply quality overrides and rebuild resources if needed."""

        rebuild = False

        if shadow_map_size and shadow_map_size != self.shadow_map_size:
            self.shadow_map_size = int(shadow_map_size)
            self.shadow_inv_size = Vec2(1.0 / self.shadow_map_size, 1.0 / self.shadow_map_size)
            rebuild = True

        if num_cascades:
            cascades = max(1, min(self.MAX_CASCADES, int(num_cascades)))
            if cascades != self.num_cascades:
                self.num_cascades = cascades
                rebuild = True

        if cascade_splits:
            self.cascade_targets = list(cascade_splits)

        if max_shadow_distance:
            self.max_shadow_distance = float(max_shadow_distance)

        if shadow_softness:
            self.shadow_softness = max(0.1, float(shadow_softness))

        if sun_animation_speed is not None:
            self.sun_speed = max(0.0, float(sun_animation_speed))

        if rebuild:
            self._setup_shadow_cascades()

        self._push_static_inputs()

    def set_shader_inputs(self, node_path, ssao_enabled=True, point_light_manager=None):
        """Bind shadow resources and uniforms to a node."""

        if point_light_manager is not None:
            point_light_manager.set_shader_inputs(node_path)

        self.bound_nodes = [
            existing for existing in self.bound_nodes if existing and not existing.isEmpty()
        ]
        if not any(existing == node_path for existing in self.bound_nodes):
            self.bound_nodes.append(node_path)

        int_textures = len(self.shadow_textures)
        fallback = self.shadow_textures[0] if int_textures > 0 else None

        for cascade_index in range(self.MAX_CASCADES):
            if fallback is None:
                break
            tex = self.shadow_textures[cascade_index] if cascade_index < int_textures else fallback
            node_path.setShaderInput(f"shadowMap{cascade_index}", tex)

        node_path.setShaderInput("shadowMapInvSize", self.shadow_inv_size)
        node_path.setShaderInput("shadowSoftness", float(self.shadow_softness))
        node_path.setShaderInput("numCascades", int(self.num_cascades))
        node_path.setShaderInput("cascadeBlendDistance", float(self.cascade_blend_distance))
        node_path.setShaderInput("cascadeBias", self.cascade_bias)
        node_path.setShaderInput("useVertexColor", 0)
        node_path.setShaderInput("shadowsEnabled", 1)

        node_path.setShaderInput("lightDirection", self.light_direction)
        node_path.setShaderInput("lightColor", self.light_color)
        node_path.setShaderInput("ambientColor", self.ambient_color)

        node_path.setShaderInput("cascadeSplits", Vec4(*self.active_cascade_limits[:4]))

        # SSAO
        node_path.setShaderInput("ssaoEnabled", 1 if ssao_enabled else 0)
        node_path.setShaderInput("ssaoRadius", 1.5)
        node_path.setShaderInput("ssaoBias", 0.025)
        node_path.setShaderInput("ssaoStrength", 0.8)

        self._apply_fog_inputs(node_path)
        self._push_dynamic_inputs(node_path)

    def update(self, camera_np, dt):
        """Advance sun animation, update cascades, and refresh uniforms."""

        if not self.shadow_cameras:
            return

        self._update_sun(dt)
        self._update_cascades(camera_np)
        self._push_dynamic_inputs()

        if self._debug_enabled:
            self._refresh_debug_overlay()

    def toggle_debug_overlay(self, force_state=None):
        """Toggle shadow map debug overlays. Returns new state."""

        target_state = (not self._debug_enabled) if force_state is None else bool(force_state)
        if target_state == self._debug_enabled:
            return self._debug_enabled

        if target_state:
            self._enable_debug_overlay()
        else:
            self._disable_debug_overlay()
        self._debug_enabled = target_state
        return self._debug_enabled

    def set_light_direction(self, direction):
        self.light_direction = direction.normalized()

    def set_shadow_softness(self, softness):
        self.shadow_softness = max(0.1, float(softness))
        self._push_static_inputs()

    def set_ssao_enabled(self, node_path, enabled):
        node_path.setShaderInput("ssaoEnabled", 1 if enabled else 0)

    def set_ssao_strength(self, node_path, strength):
        node_path.setShaderInput("ssaoStrength", max(0.0, min(2.0, float(strength))))

    def set_ssao_radius(self, node_path, radius):
        node_path.setShaderInput("ssaoRadius", max(0.5, min(5.0, float(radius))))

    def set_fog_settings(
        self,
        node_path,
        *,
        enabled=None,
        color=None,
        start=None,
        end=None,
        strength=None,
    ):
        if enabled is not None:
            self.fog_enabled = bool(enabled)
        if color is not None:
            if isinstance(color, Vec3):
                self.fog_color = color
            else:
                try:
                    self.fog_color = Vec3(float(color[0]), float(color[1]), float(color[2]))
                except (TypeError, ValueError, IndexError):
                    pass
        if start is not None:
            self.fog_start = float(start)
        if end is not None:
            self.fog_end = float(end)
        if strength is not None:
            self.fog_strength = float(strength)

        self._apply_fog_inputs(node_path)

    def cleanup(self):
        self._disable_debug_overlay()
        self._destroy_shadow_resources()
        self.bound_nodes.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _destroy_shadow_resources(self):
        for buffer in self.shadow_buffers:
            if buffer:
                self.base.graphicsEngine.removeWindow(buffer)

        self.shadow_cameras = []
        self.shadow_buffers = []
        self.shadow_textures = []
        self.shadow_matrices = [Mat4.identMat() for _ in range(self.MAX_CASCADES)]

    def _alive_bound_nodes(self):
        alive = []
        for node in self.bound_nodes:
            if node and not node.isEmpty():
                alive.append(node)
        self.bound_nodes = alive
        return alive

    def _build_bias_vector(self, bias_values):
        values = list(bias_values)
        if not values:
            values = [0.001 for _ in range(self.MAX_CASCADES)]
        while len(values) < self.MAX_CASCADES:
            values.append(values[-1])
        return Vec4(values[0], values[1], values[2], values[3])

    def _setup_shadow_cascades(self):
        self._destroy_shadow_resources()

        for cascade_index in range(self.num_cascades):
            depth_tex = Texture(f"shadow_map_{cascade_index}")
            depth_tex.setup2dTexture(
                self.shadow_map_size,
                self.shadow_map_size,
                Texture.TFloat,
                Texture.FDepthComponent,
            )
            depth_tex.setClearColor((1.0, 1.0, 1.0, 1.0))
            depth_tex.setWrapU(Texture.WMClamp)
            depth_tex.setWrapV(Texture.WMClamp)
            depth_tex.setMinfilter(Texture.FTLinear)
            depth_tex.setMagfilter(Texture.FTLinear)

            fb_props = FrameBufferProperties()
            fb_props.setDepthBits(32)
            fb_props.setRgbColor(False)
            fb_props.setAuxRgba(0)

            buffer = self.base.win.makeTextureBuffer(
                f"shadow_buffer_{cascade_index}",
                self.shadow_map_size,
                self.shadow_map_size,
                depth_tex,
                False,
            )

            if not buffer:
                print(f"Failed to create shadow buffer {cascade_index}")
                continue

            buffer.setClearDepthActive(True)
            buffer.setClearDepth(1.0)
            buffer.setSort(-100 - cascade_index)

            camera_np = self.base.makeCamera(buffer, scene=self.render)
            lens = OrthographicLens()
            lens.setNearFar(0.1, self.max_shadow_distance * 2.0)
            lens.setFilmSize(10.0, 10.0)
            camera_np.node().setLens(lens)

            self.shadow_cameras.append(camera_np)
            self.shadow_buffers.append(buffer)
            self.shadow_textures.append(depth_tex)

        self._push_static_inputs()

    def _setup_shaders(self):
        shader_dir = Path(__file__).resolve().parents[3] / "assets" / "shaders"
        terrain_vert = shader_dir / "terrain.vert"
        terrain_frag = shader_dir / "terrain.frag"

        shader = Shader.load(Shader.SL_GLSL, vertex=str(terrain_vert), fragment=str(terrain_frag))
        if shader:
            self.render.setShader(shader)
        else:
            print(f"Failed to load terrain shader from {shader_dir}")

    def _push_static_inputs(self):
        for node in self._alive_bound_nodes():
            if node.isEmpty():
                continue
            int_textures = len(self.shadow_textures)
            fallback = self.shadow_textures[0] if int_textures > 0 else None
            for cascade_index in range(self.MAX_CASCADES):
                if fallback is None:
                    break
                texture = (
                    self.shadow_textures[cascade_index]
                    if cascade_index < int_textures
                    else fallback
                )
                node.setShaderInput(f"shadowMap{cascade_index}", texture)
            node.setShaderInput("shadowMapInvSize", self.shadow_inv_size)
            node.setShaderInput("shadowSoftness", float(self.shadow_softness))
            node.setShaderInput("numCascades", int(self.num_cascades))
            node.setShaderInput("cascadeBlendDistance", float(self.cascade_blend_distance))
            node.setShaderInput("cascadeBias", self.cascade_bias)
            node.setShaderInput("shadowsEnabled", 1)

    def _push_dynamic_inputs(self, node_path=None):
        if node_path is not None:
            targets = [node_path]
        else:
            targets = self._alive_bound_nodes()
        cascade_limits = Vec4(
            self.active_cascade_limits[0],
            self.active_cascade_limits[1],
            self.active_cascade_limits[2],
            self.active_cascade_limits[3],
        )

        identity = Mat4.identMat()

        for node in targets:
            if node is None or node.isEmpty():
                continue

            for cascade_index in range(self.MAX_CASCADES):
                matrix = (
                    self.shadow_matrices[cascade_index]
                    if cascade_index < self.num_cascades
                    else identity
                )
                node.setShaderInput(f"shadowMatrix{cascade_index}", matrix)

            node.setShaderInput("cascadeSplits", cascade_limits)
            node.setShaderInput("lightDirection", self.light_direction)
            node.setShaderInput("lightColor", self.light_color)
            node.setShaderInput("ambientColor", self.ambient_color)

    def _apply_fog_inputs(self, node_path):
        fog_active = self.fog_enabled and self.fog_strength > 0.0
        node_path.setShaderInput("fogEnabled", 1 if fog_active else 0)
        node_path.setShaderInput("fogColor", self.fog_color)
        node_path.setShaderInput("fogStart", float(self.fog_start))
        node_path.setShaderInput(
            "fogEnd",
            float(self.fog_end if self.fog_end > self.fog_start else self.fog_start + 0.01),
        )
        node_path.setShaderInput("fogStrength", float(self.fog_strength))

    def _update_sun(self, dt):
        if not self.animate_sun or self.sun_speed <= 0.0:
            return

        self.sun_time = (self.sun_time + dt * self.sun_speed) % 1.0
        angle = self.sun_time * 2.0 * pi

        elevation_factor = 0.5 * (sin(angle) + 1.0)
        elevation = self.sun_min_elev + (self.sun_max_elev - self.sun_min_elev) * elevation_factor
        azimuth = angle

        sun_vector = Vec3(
            cos(elevation) * cos(azimuth),
            cos(elevation) * sin(azimuth),
            sin(elevation),
        )
        self.light_direction = (-sun_vector).normalized()

        if self._directional_light_np:
            focus = self.base.camera.getPos(self.render)
            sun_pos = focus - self.light_direction * max(self.max_shadow_distance * 0.5, 150.0)
            self._directional_light_np.setPos(self.render, sun_pos)
            self._directional_light_np.lookAt(focus)

    def _compute_split_distances(self, near_plane, far_plane):
        max_distance = min(far_plane, self.max_shadow_distance)
        splits = []
        prev = near_plane
        for cascade_index in range(self.num_cascades):
            target = self.cascade_targets[cascade_index] if cascade_index < len(self.cascade_targets) else max_distance
            clamped = min(max_distance, max(prev + 0.05, target))
            splits.append(clamped)
            prev = clamped
        while len(splits) < self.MAX_CASCADES:
            splits.append(max_distance)
        return splits

    def _update_cascades(self, camera_np):
        lens = getattr(self.base, "camLens", None)
        if lens is None:
            return

        near_plane = lens.getNear()
        far_plane = lens.getFar()
        self.active_cascade_limits = self._compute_split_distances(near_plane, far_plane)

        hfov, vfov = lens.getFov()
        hfov_rad = hfov * (pi / 180.0)
        vfov_rad = vfov * (pi / 180.0)
        tan_half_hfov = sin(hfov_rad * 0.5) / max(1e-6, cos(hfov_rad * 0.5))
        tan_half_vfov = sin(vfov_rad * 0.5) / max(1e-6, cos(vfov_rad * 0.5))
        aspect = lens.getAspectRatio()

        cam_pos = camera_np.getPos(self.render)
        cam_quat = camera_np.getQuat(self.render)
        forward = cam_quat.xform(Vec3(0, 1, 0))

        for cascade_index, camera_node in enumerate(self.shadow_cameras[: self.num_cascades]):
            cascade_near = near_plane if cascade_index == 0 else self.active_cascade_limits[cascade_index - 1]
            cascade_far = self.active_cascade_limits[cascade_index]
            cascade_depth = max(1.0, cascade_far - cascade_near)

            frustum_height = (cascade_far * tan_half_vfov) * 2.0
            frustum_width = frustum_height * aspect
            radius = sqrt(frustum_width * frustum_width + frustum_height * frustum_height) * 0.5
            radius += cascade_depth * 0.1

            center_offset = cascade_near + cascade_depth * 0.5
            cascade_center = cam_pos + forward * center_offset

            light_dir = self.light_direction.normalized()
            camera_pos = cascade_center - light_dir * (radius * 2.5 + cascade_depth)

            camera_node.setPos(self.render, camera_pos)
            camera_node.lookAt(cascade_center)

            lens = camera_node.node().getLens()
            lens.setFilmSize(radius * 2.0, radius * 2.0)
            lens.setNearFar(0.1, radius * 4.0 + cascade_depth)

            view_mat = Mat4()
            view_mat.invertFrom(camera_node.getMat(self.render))
            proj_mat = Mat4(lens.getProjectionMat())
            self.shadow_matrices[cascade_index] = proj_mat * view_mat

        for cascade_index in range(self.num_cascades, self.MAX_CASCADES):
            self.shadow_matrices[cascade_index] = Mat4.identMat()

    def _enable_debug_overlay(self):
        self._disable_debug_overlay()
        margin = 0.22
        scale = 0.18
        origin_x = -1.0 + scale * 1.2
        origin_y = 0.9
        for index, texture in enumerate(self.shadow_textures):
            offset_x = origin_x + index * margin
            img = OnscreenImage(image=texture, pos=(offset_x, 0, origin_y), scale=scale)
            img.setTransparency(TransparencyAttrib.MAlpha)
            self._debug_overlays.append(img)

    def _disable_debug_overlay(self):
        for img in self._debug_overlays:
            if not img.isEmpty():
                img.removeNode()
        self._debug_overlays.clear()

    def _refresh_debug_overlay(self):
        alive = []
        for img in self._debug_overlays:
            if not img.isEmpty():
                alive.append(img)
        self._debug_overlays = alive
