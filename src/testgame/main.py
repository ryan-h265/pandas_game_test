from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import BulletWorld, BulletDebugNode
from panda3d.core import AmbientLight, DirectionalLight, Vec3, WindowProperties
from direct.showbase.ShowBaseGlobal import globalClock

from testgame.config.settings import configure, PHYSICS_FPS, GRAVITY
from testgame.engine.world import World
from testgame.player.controller import PlayerController
from testgame.player.camera import CameraController
from testgame.player.character_model import CharacterModel
from testgame.interaction.raycast import TerrainRaycaster
from testgame.interaction.terrain_editor import TerrainEditor
from testgame.interaction.building_raycast import BuildingRaycaster
from testgame.rendering.brush_indicator import BrushIndicator
from testgame.rendering.shadow_manager import ShadowManager
from testgame.rendering.post_process import PostProcessManager
from testgame.rendering.effects import EffectsManager
from testgame.rendering.weapon_viewmodel import WeaponViewModel
from testgame.rendering.skybox import MountainSkybox
from testgame.rendering.point_light_manager import PointLightManager
from testgame.tools.tool_manager import ToolManager, ToolType
from testgame.ui.hud import HUD
from testgame.ui.crosshair import CrosshairManager
from testgame.ui.menu_system import MenuSystem


class Game(ShowBase):
    def __init__(self):
        # Load configuration
        configure()

        ShowBase.__init__(self)

        # Initialize physics
        self.setup_physics()

        # Setup lighting
        self.setup_lighting()

        # Initialize skybox with distant mountains, clouds, and sun
        self.skybox = MountainSkybox(self.render, self.camera)
        self.skybox.create_skybox()
        print("Created mountain skybox with distant peaks, clouds, and sun")

        # Initialize world and terrain
        self.game_world = World(self.render, self.world)

        # Initialize player (start at the base of Mount Everest)
        start_pos = Vec3(
            300, 300, 50
        )  # Start at base camp area, looking toward the mountain
        self.player = PlayerController(self.render, self.world, start_pos)

        # Initialize camera controller
        self.camera_controller = CameraController(self.camera, self.win)
        self.camera_controller.setup_mouse()

        # Initialize character model (for third-person view)
        self.character_model = CharacterModel(self.render, start_pos)
        self.character_model.hide()  # Start hidden (first-person mode)

        # Initialize terrain editing
        self.raycaster = TerrainRaycaster(self.cam, self.render)
        self.terrain_editor = TerrainEditor(self.game_world.terrain)
        self.brush_indicator = BrushIndicator(self.render)

        # Initialize building raycaster for physics-based shooting
        self.building_raycaster = BuildingRaycaster(self.world, self.render)

        # Initialize HUD
        self.hud = HUD(self.aspect2d, self.render)

        # Set initial player health (for demonstration)
        self.player_health = 100
        self.player_max_health = 100
        self.hud.set_health(self.player_health, self.player_max_health)

        # Initialize crosshair system
        self.crosshair_manager = CrosshairManager(self)

        # Initialize menu system
        self.menu_system = MenuSystem(self)

        # Initialize effects manager
        self.effects_manager = EffectsManager(self.render)

        # Initialize weapon viewmodel (FPS-style weapon display)
        self.weapon_viewmodel = WeaponViewModel(self.camera)

        # Initialize point light system (for torches, lanterns, etc.)
        # IMPORTANT: Must be initialized before ToolManager for prop lighting
        self.point_light_manager = PointLightManager()
        print("Point light system initialized (0 lights active)")

        # Initialize tool system
        self.tool_manager = ToolManager(
            self.terrain_editor,
            self.game_world,
            self.camera,
            self.effects_manager,
            self.building_raycaster,
            self.weapon_viewmodel,
            self.render,
            self.world,
            self.raycaster,
            self.mouseWatcherNode,
            self.point_light_manager,
        )
        # Set up tool message callback to display on HUD
        self.tool_manager.tool_message_callback = self.on_tool_change

        # Show initial crosshair (fist tool is default)
        self.crosshair_manager.show_crosshair("fist")

        # Initialize shadow system (enabled by default)
        self.shadows_enabled = True
        self.ssao_enabled = False  # Ambient occlusion enabled by default
        self.ssao_strength = 0.8  # Default AO strength
        light_dir = Vec3(1, 1, -1)  # Sun direction
        self.shadow_manager = ShadowManager(self, self.render, light_dir)
        # Initial shader inputs (camera pos will be updated each frame)
        self.shadow_manager.set_shader_inputs(
            self.render,
            ssao_enabled=self.ssao_enabled,
            point_light_manager=self.point_light_manager,
        )
        print("Shadows and ambient occlusion enabled by default")
        print(
            f"Point light system supports up to {self.point_light_manager.MAX_LIGHTS} visible lights with smart culling"
        )

        # Initialize post-processing
        self.post_process = PostProcessManager(self.render, self.cam)

        # Interaction state
        self.is_using_tool = False

        # Setup input
        self.setup_input()

        # Setup mouse control
        self.mouse_captured = True
        self.setup_mouse_control()

        # Update task
        self.taskMgr.add(self.update, "update")

        # Display GPU information
        self.print_gpu_info()

        print("Game initialized successfully!")
        print("\nControls:")
        print("  WASD - Move")
        print("  Shift - Run (or fly down in flying mode)")
        print("  Space - Jump (or fly up in flying mode)")
        print("  Mouse - Look around")
        print("  M - Toggle mouse capture")
        print("  F - Toggle first-person / third-person camera")
        print("  T/Y - Adjust third-person camera distance")
        print("")
        print("  Q - Switch tools (Fist / Terrain / Crowbar / Gun / Placement)")
        print("  Left Click - Use tool (punch/dig/swing/shoot/place)")
        print("  Right Click - Secondary action (raise terrain/rotate placement)")
        print("  Middle Click - Tertiary action (smooth terrain/toggle grid snap)")
        print("")
        print("  Scroll Wheel - Adjust tool property 1 (context-sensitive)")
        print(
            "    • Terrain: Brush size  • Fist: Damage  • Crowbar: Damage  • Gun: Damage  • Placement: Width"
        )
        print("  [ / ] - Adjust tool property 2 (context-sensitive)")
        print(
            "    • Terrain: Strength  • Fist: Range  • Crowbar: Cooldown  • Gun: Fire rate  • Placement: Height"
        )
        print("  1/2/3 - Set terrain mode (lower/raise/smooth)")
        print("  H - Toggle weapon viewmodel (FPS-style weapon display)")
        print("  J - Toggle crosshair on/off")
        print("")
        print("  G - Toggle God Mode (enables double-tap space to fly)")
        print("    When flying: WASD to move, Space to ascend, Shift to descend")
        print("")
        print("  ESC - Pause menu (Save/Load, Settings, Quit)")
        print("")
        print("  N - Toggle shadows on/off")
        print("  Z/X - Adjust shadow softness")
        print("  O - Toggle ambient occlusion (SSAO) on/off")
        print("  ,/. - Adjust ambient occlusion strength")
        print("  C - Toggle post-processing")
        print("  V - Toggle chunk debug colors")
        print("  B - Toggle wireframe debug")
        print("  R - Toggle raycast debug (shows gun ray paths)")

    def print_gpu_info(self):
        """Print GPU and graphics information"""
        print("\n" + "=" * 60)
        print("GPU / GRAPHICS INFORMATION")
        print("=" * 60)

        # Get graphics state guardian (GSG) which contains GPU info
        gsg = self.win.getGsg()

        if gsg:
            # Driver and renderer info
            print(f"Graphics API: {gsg.getDriverRenderer()}")
            print(f"Driver Vendor: {gsg.getDriverVendor()}")
            print(f"Driver Version: {gsg.getDriverVersion()}")
            print(
                f"GLSL Version: {gsg.getDriverShaderVersionMajor()}.{gsg.getDriverShaderVersionMinor()}"
            )

            # Check if using hardware rendering
            if gsg.isHardware():
                print("Hardware Acceleration: ENABLED (Using GPU)")
            else:
                print(
                    "Hardware Acceleration: DISABLED (Using CPU - Software Rendering)"
                )

            # Shader support
            if gsg.getSupportsBasicShaders():
                print("Shader Support: YES")
            else:
                print("Shader Support: NO")

            # Texture stages
            print(f"Max Texture Stages: {gsg.getMaxTextureStages()}")

            # Additional GPU capabilities
            if hasattr(gsg, "getMaxVertexTextureImages"):
                print(f"Max Vertex Textures: {gsg.getMaxVertexTextureImages()}")
            if hasattr(gsg, "getMaxLights"):
                print(f"Max Lights: {gsg.getMaxLights()}")
        else:
            print("WARNING: Could not retrieve graphics information!")

        print("=" * 60 + "\n")

    def setup_physics(self):
        """Initialize Bullet physics world"""
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, GRAVITY))

        # Optional: Enable debug visualization
        debugNode = BulletDebugNode("Debug")
        debugNode.showWireframe(True)
        debugNode.showConstraints(True)
        debugNode.showBoundingBoxes(False)
        debugNode.showNormals(False)

        debugNP = self.render.attachNewNode(debugNode)
        self.world.setDebugNode(debugNP.node())
        # debugNP.show()  # Uncomment to see physics debug

    def setup_lighting(self):
        """Setup mountain environment lighting"""
        # Ambient light - cooler mountain air
        alight = AmbientLight("alight")
        alight.setColor(
            (0.4, 0.45, 0.5, 1)
        )  # Slightly blue ambient for mountain atmosphere
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)

        # Directional light (sun) - warm mountain sun
        dlight = DirectionalLight("dlight")
        dlight.setColor((1.0, 0.95, 0.8, 1))  # Warm yellowish sunlight
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(45, -45, 0)  # Sun position matching skybox
        self.render.setLight(dlnp)

        # Store light reference for skybox coordination
        self.sun_light = dlnp

    def setup_input(self):
        """Setup keyboard input handlers"""
        # Movement keys
        self.accept("w", self.player.handle_input, ["w", True])
        self.accept("w-up", self.player.handle_input, ["w", False])
        self.accept("s", self.player.handle_input, ["s", True])
        self.accept("s-up", self.player.handle_input, ["s", False])
        self.accept("a", self.player.handle_input, ["a", True])
        self.accept("a-up", self.player.handle_input, ["a", False])
        self.accept("d", self.player.handle_input, ["d", True])
        self.accept("d-up", self.player.handle_input, ["d", False])

        # Jump and run
        self.accept("space", self.player.handle_input, ["space", True])
        self.accept("space-up", self.player.handle_input, ["space", False])
        self.accept("shift", self.player.handle_input, ["shift", True])
        self.accept("shift-up", self.player.handle_input, ["shift", False])

        # Mouse toggle
        self.accept("m", self.toggle_mouse)

        # Camera mode switching
        self.accept("f", self.toggle_camera_mode)
        self.accept("t", self.adjust_camera_distance, [-0.5])  # Closer
        self.accept("y", self.adjust_camera_distance, [0.5])  # Farther

        # Tool switching
        self.accept("q", self.tool_manager.cycle_tool)

        # Tool usage - Mouse buttons
        self.accept("mouse1", self.on_mouse_down, [1])  # Left click
        self.accept("mouse1-up", self.on_mouse_up, [1])
        self.accept("mouse3", self.on_mouse_down, [3])  # Right click
        self.accept("mouse3-up", self.on_mouse_up, [3])
        self.accept("mouse2", self.on_mouse_down, [2])  # Middle click
        self.accept("mouse2-up", self.on_mouse_up, [2])

        # Context-sensitive number keys (1-4)
        # For terrain tool: terrain modes (1=lower, 2=raise, 3=smooth)
        # For building tool: building types (1=simple, 2=japanese, 3=todo, 4=todo)
        self.accept("1", self.on_number_key, [1])
        self.accept("2", self.on_number_key, [2])
        self.accept("3", self.on_number_key, [3])
        self.accept("4", self.on_number_key, [4])

        # Brush size adjustment
        self.accept("wheel_up", self.adjust_brush_size, [1])
        self.accept("wheel_down", self.adjust_brush_size, [-1])

        # Terrain strength adjustment (for terrain tool)
        self.accept("[", self.adjust_terrain_strength, [-0.01])  # Decrease strength
        self.accept("]", self.adjust_terrain_strength, [0.01])  # Increase strength

        # Shadow quality adjustments
        self.accept("z", self.adjust_shadow_softness, [-0.5])  # Decrease softness
        self.accept("x", self.adjust_shadow_softness, [0.5])  # Increase softness
        self.accept("c", self.toggle_post_process)  # Toggle post-processing
        self.accept("n", self.toggle_shadows)  # Toggle shadows on/off

        # SSAO (Ambient Occlusion) controls
        self.accept("o", self.toggle_ssao)  # Toggle SSAO on/off
        self.accept(",", self.adjust_ssao_strength, [-0.1])  # Decrease AO strength
        self.accept(".", self.adjust_ssao_strength, [0.1])  # Increase AO strength

        # Point light controls (for testing)
        self.accept("l", self.add_test_torch)  # Add a torch at current position

        # Debug visualization
        self.accept("v", self.toggle_chunk_colors)  # Toggle chunk debug colors
        self.accept("b", self.toggle_wireframe)  # Toggle wireframe
        self.accept(
            "r", self.toggle_raycast_debug
        )  # Toggle raycast debug visualization
        self.accept("h", self.toggle_weapon_viewmodel)  # Toggle weapon viewmodel on/off
        self.accept("j", self.toggle_crosshair)  # Toggle crosshair on/off

        # God mode
        self.accept("g", self.toggle_godmode)  # Toggle god mode

        # Pause menu
        self.accept("escape", self.toggle_pause_menu)

        # Save/Load system
        self.accept("f5", self.quick_save)  # Quick save
        self.accept("f9", self.quick_load)  # Quick load
        self.accept("f6", self.open_save_dialog)  # Save with name
        self.accept("f7", self.open_load_dialog)  # Load dialog

    def setup_mouse_control(self):
        """Setup mouse for FPS-style look control"""
        # Disable default mouse camera control
        self.disableMouse()

        # Configure window properties for mouse capture
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_confined)
        self.win.requestProperties(props)

        # Center the mouse initially
        if self.win.hasPointer(0):
            window_props = self.win.getProperties()
            center_x = window_props.getXSize() // 2
            center_y = window_props.getYSize() // 2
            self.win.movePointer(0, center_x, center_y)

    def toggle_mouse(self):
        """Toggle mouse capture on/off"""
        self.mouse_captured = not self.mouse_captured
        props = WindowProperties()
        if self.mouse_captured:
            props.setCursorHidden(True)
            props.setMouseMode(WindowProperties.M_confined)
            print("Mouse captured")
            # Re-center mouse when capturing
            if self.win.hasPointer(0):
                window_props = self.win.getProperties()
                center_x = window_props.getXSize() // 2
                center_y = window_props.getYSize() // 2
                self.win.movePointer(0, center_x, center_y)
        else:
            props.setCursorHidden(False)
            props.setMouseMode(WindowProperties.M_absolute)
            print("Mouse released")
        self.win.requestProperties(props)

    def on_mouse_down(self, button):
        """Handle mouse button press.

        Args:
            button: Mouse button number (1=left, 2=middle, 3=right)
        """
        self.is_using_tool = True
        self.current_mouse_button = button

        # For gun/crowbar/fist, fire immediately on click (not continuous)
        active_tool = self.tool_manager.get_active_tool()
        if active_tool and active_tool.tool_type in [
            ToolType.GUN,
            ToolType.CROWBAR,
            ToolType.FIST,
        ]:
            # Get hit info for these tools
            hit = self.raycaster.get_terrain_hit(self.mouseWatcherNode)

            if button == 1:  # Left click
                result = self.tool_manager.use_primary(hit)
                if result:
                    print(f"{active_tool.name} used successfully")
            elif button == 3:  # Right click
                self.tool_manager.use_secondary(hit)
            elif button == 2:  # Middle click
                self.tool_manager.use_tertiary(hit)

    def on_mouse_up(self, button):
        """Handle mouse button release.

        Args:
            button: Mouse button number
        """
        self.is_using_tool = False
        self.current_mouse_button = None

        # Notify active tool that mouse button was released
        active_tool = self.tool_manager.get_active_tool()
        if active_tool:
            active_tool.on_mouse_release(button)

    def adjust_brush_size(self, direction):
        """Adjust active tool's primary property (context-sensitive).

        Args:
            direction: 1 for increase, -1 for decrease
        """
        active_tool = self.tool_manager.get_active_tool()
        if active_tool:
            result = active_tool.adjust_primary_property(direction)
            if result:
                prop_name, value = result
                # Format value based on type
                if isinstance(value, float):
                    value_str = f"{value:.2f}"
                else:
                    value_str = f"{value}"

                message = f"{active_tool.name} - {prop_name}: {value_str}"
                self.hud.show_message(message)
                print(message)

                # Update brush indicator if terrain tool
                if active_tool.tool_type == ToolType.TERRAIN:
                    self.brush_indicator.update_size(self.terrain_editor.brush_size)

    def adjust_terrain_strength(self, delta):
        """Adjust active tool's secondary property (context-sensitive).

        Args:
            delta: Amount to adjust (positive or negative)
        """
        active_tool = self.tool_manager.get_active_tool()
        if active_tool:
            result = active_tool.adjust_secondary_property(delta)
            if result:
                prop_name, value = result
                # Format value based on type
                if isinstance(value, float):
                    value_str = f"{value:.3f}"
                else:
                    value_str = f"{value}"

                message = f"{active_tool.name} - {prop_name}: {value_str}"
                self.hud.show_message(message)
                print(message)

    def adjust_shadow_softness(self, delta):
        """Adjust shadow softness.

        Args:
            delta: Amount to adjust softness by
        """
        if self.shadow_manager:
            current = self.shadow_manager.shadow_softness
            new_softness = max(0.5, min(10.0, current + delta))
            self.shadow_manager.set_shadow_softness(new_softness)
            self.shadow_manager.set_shader_inputs(
                self.render, point_light_manager=self.point_light_manager
            )
            print(f"Shadow softness: {new_softness:.1f}")
        else:
            print("Shadows are disabled (for performance)")

    def add_test_torch(self):
        """Add a torch light at the player's current position (for testing)."""
        player_pos = self.player.get_position()
        # Add torch slightly above ground
        torch_pos = player_pos + Vec3(0, 0, 2)

        # Create warm orange torch light (wider reach, softer intensity)
        light = self.point_light_manager.add_light(
            position=torch_pos,
            color=(1.0, 0.7, 0.4),  # Warm orange
            radius=40.0,  # Wider reach (was 20.0)
            intensity=3.0,  # Less intense (was 8.0)
        )

        if light:
            # Enable flickering for torch effect
            light.set_flicker(True, speed=6.0, amount=0.2)

            # Update shader inputs
            if self.shadow_manager:
                self.shadow_manager.set_shader_inputs(
                    self.render,
                    ssao_enabled=self.ssao_enabled,
                    point_light_manager=self.point_light_manager,
                )

            light_count = self.point_light_manager.get_light_count()
            self.hud.show_message(
                f"Torch added at {torch_pos} ({light_count}/{self.point_light_manager.MAX_LIGHTS} lights)"
            )
            print(f"Added flickering torch at {torch_pos}")
        else:
            self.hud.show_message("Cannot add more lights (max reached!)")
            print("Max lights reached!")

    def toggle_shadows(self):
        """Toggle shadows on/off."""
        if self.shadows_enabled:
            # Disable shadows
            if self.shadow_manager:
                self.shadow_manager.cleanup()
                self.shadow_manager = None
            self.shadows_enabled = False
            self.hud.show_message("Shadows: OFF (Performance Mode)")
            print("Shadows disabled - should see FPS increase")
        else:
            # Enable shadows
            light_dir = Vec3(1, 1, -1)
            self.shadow_manager = ShadowManager(self, self.render, light_dir)
            self.shadow_manager.set_shader_inputs(
                self.render,
                ssao_enabled=self.ssao_enabled,
                point_light_manager=self.point_light_manager,
            )
            self.shadows_enabled = True
            self.hud.show_message("Shadows: ON (Quality Mode)")
            print("Shadows enabled")

    def toggle_ssao(self):
        """Toggle ambient occlusion (SSAO) on/off."""
        if self.shadow_manager:
            self.ssao_enabled = not self.ssao_enabled
            self.shadow_manager.set_ssao_enabled(self.render, self.ssao_enabled)
            status = "ON" if self.ssao_enabled else "OFF"
            self.hud.show_message(f"Ambient Occlusion: {status}")
            print(f"Ambient occlusion {status}")
        else:
            print("Shadows must be enabled to use ambient occlusion")
            self.hud.show_message("Enable shadows first (press N)")

    def adjust_ssao_strength(self, delta):
        """Adjust ambient occlusion strength.

        Args:
            delta: Amount to adjust strength by
        """
        if self.shadow_manager and self.ssao_enabled:
            self.ssao_strength = max(0.0, min(2.0, self.ssao_strength + delta))
            self.shadow_manager.set_ssao_strength(self.render, self.ssao_strength)
            self.hud.show_message(f"AO Strength: {self.ssao_strength:.1f}")
            print(f"Ambient occlusion strength: {self.ssao_strength:.1f}")
        else:
            if not self.shadow_manager:
                print("Shadows must be enabled to adjust ambient occlusion")
            else:
                print("Ambient occlusion is disabled (press O to enable)")

    def toggle_post_process(self):
        """Toggle post-processing effects."""
        if self.post_process:
            enabled = self.post_process.toggle()
            self.hud.show_message(f"Post-processing: {'ON' if enabled else 'OFF'}")
        else:
            print("Post-processing is disabled (for performance)")

    def toggle_chunk_colors(self):
        """Toggle debug chunk colors."""
        try:
            import config.settings as settings

            settings.DEBUG_CHUNK_COLORS = not settings.DEBUG_CHUNK_COLORS
            print(
                f"\n=== Chunk debug colors: {'ON' if settings.DEBUG_CHUNK_COLORS else 'OFF'} ==="
            )
            # Regenerate all chunks to apply the change
            chunk_count = 0
            for chunk in self.game_world.terrain.chunks.values():
                chunk.regenerate()
                chunk_count += 1
            print(f"Regenerated {chunk_count} chunks")
        except Exception as e:
            print(f"Error toggling chunk colors: {e}")
            import traceback

            traceback.print_exc()

    def toggle_wireframe(self):
        """Toggle debug wireframe."""
        try:
            import config.settings as settings

            settings.DEBUG_CHUNK_WIREFRAME = not settings.DEBUG_CHUNK_WIREFRAME
            print(
                f"\n=== Wireframe debug: {'ON' if settings.DEBUG_CHUNK_WIREFRAME else 'OFF'} ==="
            )
            # Regenerate all chunks to apply the change
            chunk_count = 0
            for chunk in self.game_world.terrain.chunks.values():
                chunk.regenerate()
                chunk_count += 1
            print(f"Regenerated {chunk_count} chunks")
        except Exception as e:
            print(f"Error toggling wireframe: {e}")
            import traceback

            traceback.print_exc()

    def toggle_raycast_debug(self):
        """Toggle raycast debug visualization."""
        self.effects_manager.set_debug_mode(not self.effects_manager.debug_mode)
        status = "ON" if self.effects_manager.debug_mode else "OFF"
        self.hud.show_message(f"Raycast Debug: {status}")

    def toggle_weapon_viewmodel(self):
        """Toggle weapon viewmodel on/off."""
        if self.weapon_viewmodel.current_model:
            # Hide weapon
            self.weapon_viewmodel.hide_weapon()
            self.hud.show_message("Weapon Viewmodel: OFF")
            print("Weapon viewmodel hidden")
        else:
            # Show current weapon
            active_tool = self.tool_manager.get_active_tool()
            if active_tool:
                self.weapon_viewmodel.show_weapon(active_tool.view_model_name)
                self.hud.show_message("Weapon Viewmodel: ON")
                print("Weapon viewmodel shown")

    def toggle_crosshair(self):
        """Toggle crosshair on/off."""
        if self.crosshair_manager.crosshair_elements:
            # Hide crosshair
            self.crosshair_manager.hide_crosshair()
            self.hud.show_message("Crosshair: OFF")
            print("Crosshair hidden")
        else:
            # Show crosshair for current tool
            active_tool = self.tool_manager.get_active_tool()
            if active_tool:
                self.crosshair_manager.show_crosshair(active_tool.view_model_name)
                self.hud.show_message("Crosshair: ON")
                print("Crosshair shown")

    def toggle_godmode(self):
        """Toggle god mode on/off."""
        enabled = self.player.set_godmode(not self.player.godmode_enabled)
        status = "ON" if enabled else "OFF"
        self.hud.show_message(f"God Mode: {status} (Double-tap Space to fly)")

        # If disabling while flying, inform the user
        if not enabled:
            print("God mode disabled. Flying mode will be turned off if active.")

    def toggle_camera_mode(self):
        """Toggle between first-person and third-person camera modes."""
        new_mode = self.camera_controller.toggle_camera_mode()

        if new_mode == "third_person":
            # Show character model in third-person
            self.character_model.show()
            # Hide weapon viewmodel in third-person
            if self.weapon_viewmodel.current_model:
                self.weapon_viewmodel.hide_weapon()
            self.hud.show_message("Camera: Third-Person")
            print("Switched to third-person view")
        else:
            # Hide character model in first-person
            self.character_model.hide()
            # Show weapon viewmodel in first-person (if it was visible before)
            active_tool = self.tool_manager.get_active_tool()
            if active_tool:
                self.weapon_viewmodel.show_weapon(active_tool.view_model_name)
            self.hud.show_message("Camera: First-Person")
            print("Switched to first-person view")

    def adjust_camera_distance(self, delta):
        """Adjust third-person camera distance.

        Args:
            delta: Amount to change distance by
        """
        if self.camera_controller.is_third_person():
            self.camera_controller.adjust_third_person_distance(delta)
            distance = self.camera_controller.third_person_distance
            self.hud.show_message(f"Camera Distance: {distance:.1f}")
            print(f"Third-person camera distance: {distance:.1f}")
        else:
            self.hud.show_message("Switch to third-person mode first (F)")

    def on_tool_change(self, message):
        """Handle tool change event.

        Args:
            message: Tool change message
        """
        # Extract tool name from message
        if ":" in message:
            tool_name = message.split(":", 1)[1].strip()
            tool_name = tool_name.split("(")[0].strip()
            self.hud.set_tool_name(tool_name)
        self.hud.show_message(message)

        # Update crosshair for new tool
        active_tool = self.tool_manager.get_active_tool()
        if active_tool:
            self.crosshair_manager.show_crosshair(active_tool.view_model_name)

    def on_number_key(self, number):
        """Handle number key press - context sensitive based on active tool.

        Args:
            number: Number key pressed (1-4)
        """
        active_tool = self.tool_manager.get_active_tool()

        if not active_tool:
            return

        # Placement tool: switch placement type (building/prop/model)
        if active_tool.tool_type == ToolType.BUILDING:
            message = active_tool.set_placement_type(number)
            self.hud.show_message(message)
            print(message)

        # Terrain tool: switch terrain mode (only 1-3)
        elif active_tool.tool_type == ToolType.TERRAIN:
            if number == 1:
                active_tool.set_mode("lower")
                self.hud.show_message("Terrain Mode: Lower")
            elif number == 2:
                active_tool.set_mode("raise")
                self.hud.show_message("Terrain Mode: Raise")
            elif number == 3:
                active_tool.set_mode("smooth")
                self.hud.show_message("Terrain Mode: Smooth")

        else:
            self.hud.show_message(
                f"Number keys have no function for {active_tool.name}"
            )

    def set_terrain_mode(self, mode):
        """Set terrain editing mode (only works with terrain tool).
        [DEPRECATED: Use on_number_key instead]

        Args:
            mode: 'lower', 'raise', or 'smooth'
        """
        active_tool = self.tool_manager.get_active_tool()
        if active_tool and active_tool.tool_type == ToolType.TERRAIN:
            active_tool.set_mode(mode)
        else:
            self.hud.show_message(
                "Terrain modes only work with Terrain tool! Press Q to switch."
            )

    def toggle_pause_menu(self):
        """Toggle the pause menu on/off"""
        self.menu_system.toggle_pause()

    def quit_game(self):
        """Clean quit handler"""
        print("\nQuitting game...")
        if self.shadow_manager:
            self.shadow_manager.cleanup()
        self.userExit()

    def update(self, task):
        """Main game loop"""
        dt = globalClock.getDt()

        # Skip game logic if paused, but still update HUD
        if self.menu_system.is_paused:
            # Update HUD (for FPS counter if enabled)
            fps = globalClock.getAverageFrameRate()
            self.hud.update(dt, fps=fps)
            return task.cont

        # Update shadow cameras to follow player (if shadows enabled)
        player_pos = self.player.get_position()
        if self.shadow_manager:
            self.shadow_manager.update_cascade_cameras(player_pos, None)

        # Handle mouse look (centered mode - track from center)
        if self.mouse_captured and self.win.hasPointer(0):
            # Get absolute mouse position
            pointer = self.win.getPointer(0)
            mouse_x = pointer.getX()
            mouse_y = pointer.getY()

            # Get window center
            props = self.win.getProperties()
            center_x = props.getXSize() // 2
            center_y = props.getYSize() // 2

            # Only update if mouse has moved from center
            if mouse_x != center_x or mouse_y != center_y:
                # Calculate delta from center
                delta_x = mouse_x - center_x
                delta_y = mouse_y - center_y

                # Update camera rotation
                self.camera_controller.update_look(delta_x, delta_y)

                # Re-center the mouse
                self.win.movePointer(0, center_x, center_y)

        # Handle tool usage
        hit = self.raycaster.get_terrain_hit(self.mouseWatcherNode)
        if hit:
            # Update brush indicator position (only show for terrain tool)
            active_tool = self.tool_manager.get_active_tool()
            if active_tool and active_tool.tool_type == ToolType.TERRAIN:
                self.brush_indicator.update_position(hit["position"])
                self.brush_indicator.show()
            else:
                self.brush_indicator.hide()

            # Use tool if mouse button is held
            if self.is_using_tool:
                button = getattr(self, "current_mouse_button", 1)
                if button == 1:  # Left click
                    self.tool_manager.use_primary(hit)
                elif button == 3:  # Right click
                    self.tool_manager.use_secondary(hit)
                elif button == 2:  # Middle click
                    self.tool_manager.use_tertiary(hit)
        else:
            self.brush_indicator.hide()

        # Update player movement
        self.player.update(dt, self.camera_controller)

        # Update skybox to follow camera and animate clouds
        camera_pos = self.camera.getPos()
        self.skybox.update(camera_pos, dt)

        # Check if player is moving (for weapon bob)
        is_moving = self.player.is_moving()

        # Update tool manager (includes weapon viewmodel animations)
        self.tool_manager.update(dt, is_moving)

        # Update effects
        self.effects_manager.update(dt)

        # Update point lights (for flickering animations)
        self.point_light_manager.update(dt)

        # Update point light shader inputs with camera position for smart culling
        if self.shadow_manager and len(self.point_light_manager.lights) > 0:
            camera_pos = self.camera.getPos()
            self.point_light_manager.set_shader_inputs(
                self.render, camera_pos=camera_pos
            )

        # Update HUD with FPS, compass, minimap, and tool info
        fps = globalClock.getAverageFrameRate()
        camera_heading = self.camera_controller.heading
        active_tool = self.tool_manager.get_active_tool()
        self.hud.update(
            dt,
            fps=fps,
            camera_heading=camera_heading,
            player_pos=player_pos,
            tool=active_tool,
        )

        # Show flying status if active
        if self.player.is_flying_mode():
            self.hud.show_message(
                "FLYING MODE (Double-tap Space to disable)", duration=0.1
            )

        # Update camera to follow player
        player_pos = self.player.get_position()
        self.camera_controller.update_position(player_pos)
        self.camera_controller.apply_rotation()

        # Update character model position and rotation (for third-person view)
        if self.camera_controller.is_third_person():
            self.character_model.set_position(player_pos)
            self.character_model.set_heading(self.camera_controller.heading)

        # Update character animations
        is_moving = self.player.is_moving()
        is_running = self.player.keys.get("run", False)
        is_jumping = not self.player.is_on_ground()
        self.character_model.update(dt, is_moving, is_running, is_jumping)

        # Update physics
        self.world.doPhysics(dt, 10, 1.0 / PHYSICS_FPS)

        # Update game world
        self.game_world.update(dt, player_pos)

        return task.cont

    def quick_save(self):
        """Quick save to 'quicksave' slot."""
        print("Quick saving...")
        metadata = {"title": "Quick Save", "description": "Auto-saved game state"}
        success = self.game_world.save_to_file("quicksave", self.player, metadata)
        if success:
            self.hud.show_message("Game saved!", duration=2.0)
        else:
            self.hud.show_message("Save failed!", duration=2.0)

    def quick_load(self):
        """Quick load from 'quicksave' slot."""
        print("Quick loading...")
        success = self.game_world.load_from_file("quicksave", self.player)
        if success:
            self.hud.show_message("Game loaded!", duration=2.0)
        else:
            self.hud.show_message("Load failed! No save found.", duration=2.0)

    def open_save_dialog(self):
        """Open a simple save dialog (text input for now)."""
        print("\n" + "=" * 50)
        print("SAVE GAME")
        print("=" * 50)
        print("Enter save name (or press Enter for 'save_1'):")
        # Note: In a real game, you'd use a proper GUI dialog
        # For now, we'll use the quick save with a timestamped name
        import datetime

        save_name = f"save_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        metadata = {
            "title": f"Manual Save {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "description": "Manually saved game state",
        }

        success = self.game_world.save_to_file(save_name, self.player, metadata)
        if success:
            print(f"Game saved as: {save_name}")
            self.hud.show_message(f"Saved: {save_name}", duration=3.0)
        else:
            print("Save failed!")
            self.hud.show_message("Save failed!", duration=2.0)

    def open_load_dialog(self):
        """Open a simple load dialog (list saves)."""
        print("\n" + "=" * 50)
        print("LOAD GAME")
        print("=" * 50)

        saves = self.game_world.list_saves()

        if not saves:
            print("No saved games found!")
            self.hud.show_message("No saves found!", duration=2.0)
            return

        print(f"Found {len(saves)} saved game(s):\n")
        for i, (save_name, metadata) in enumerate(saves):
            timestamp = metadata.get("timestamp", "Unknown")
            title = metadata.get("title", "Untitled")
            print(f"  {i + 1}. {save_name}")
            print(f"     Title: {title}")
            print(f"     Date: {timestamp}")
            print()

        print("Note: Use F9 to load 'quicksave', or edit code to load specific saves")
        print("=" * 50 + "\n")

        # For now, just load the most recent save
        if saves:
            most_recent = saves[0][0]
            print(f"Loading most recent save: {most_recent}")
            success = self.game_world.load_from_file(most_recent, self.player)
            if success:
                self.hud.show_message(f"Loaded: {most_recent}", duration=3.0)
            else:
                self.hud.show_message("Load failed!", duration=2.0)


def main():
    app = Game()
    app.run()


if __name__ == "__main__":
    main()
