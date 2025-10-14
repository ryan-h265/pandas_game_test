from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import BulletWorld, BulletDebugNode
from panda3d.core import AmbientLight, DirectionalLight, Vec3, WindowProperties

from config.settings import configure, PHYSICS_FPS, GRAVITY
from engine.world import World
from player.controller import PlayerController
from player.camera import CameraController
from interaction.raycast import TerrainRaycaster
from interaction.terrain_editor import TerrainEditor
from interaction.building_raycast import BuildingRaycaster
from rendering.brush_indicator import BrushIndicator
from rendering.shadow_manager import ShadowManager
from rendering.post_process import PostProcessManager
from rendering.effects import EffectsManager
from tools.tool_manager import ToolManager, ToolType
from ui.hud import HUD


class Game(ShowBase):
    def __init__(self):
        # Load configuration
        configure()

        ShowBase.__init__(self)

        # Initialize physics
        self.setup_physics()

        # Setup lighting
        self.setup_lighting()

        # Initialize world and terrain
        self.game_world = World(self.render, self.world)

        # Initialize player (start at a good viewing position)
        start_pos = Vec3(16, 16, 50)  # Start at center of terrain, high up
        self.player = PlayerController(self.render, self.world, start_pos)

        # Initialize camera controller
        self.camera_controller = CameraController(self.camera, self.win)
        self.camera_controller.setup_mouse()

        # Initialize terrain editing
        self.raycaster = TerrainRaycaster(self.cam, self.render)
        self.terrain_editor = TerrainEditor(self.game_world.terrain)
        self.brush_indicator = BrushIndicator(self.render)

        # Initialize building raycaster for physics-based shooting
        self.building_raycaster = BuildingRaycaster(self.world, self.render)

        # Initialize HUD
        self.hud = HUD()

        # Initialize effects manager
        self.effects_manager = EffectsManager(self.render)

        # Initialize tool system
        self.tool_manager = ToolManager(
            self.terrain_editor,
            self.game_world,
            self.camera,
            self.effects_manager,
            self.building_raycaster
        )
        # Set up tool message callback to display on HUD
        self.tool_manager.tool_message_callback = self.on_tool_change

        # Initialize shadow system
        light_dir = Vec3(1, 1, -1)  # Sun direction
        self.shadow_manager = ShadowManager(self, self.render, light_dir)
        self.shadow_manager.set_shader_inputs(self.render)

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
        print("  Shift - Run")
        print("  Space - Jump")
        print("  Mouse - Look around")
        print("  M - Toggle mouse capture")
        print("")
        print("  Q - Switch tools (Fist / Terrain / Crowbar / Gun)")
        print("  Left Click - Use tool (punch/dig/swing/shoot)")
        print("  Right Click - Secondary action (raise terrain)")
        print("  Middle Click - Tertiary action (smooth terrain)")
        print("  Scroll Wheel - Adjust brush size")
        print("  1/2/3 - Set terrain mode (lower/raise/smooth)")
        print("")
        print("  Z/X - Adjust shadow softness")
        print("  C - Toggle post-processing")
        print("  V - Toggle chunk debug colors")
        print("  B - Toggle wireframe debug")
        print("  R - Toggle raycast debug (shows gun ray paths)")
        print("  ESC - Quit")

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
            print(f"GLSL Version: {gsg.getDriverShaderVersionMajor()}.{gsg.getDriverShaderVersionMinor()}")

            # Check if using hardware rendering
            if gsg.isHardware():
                print("Hardware Acceleration: ENABLED (Using GPU)")
            else:
                print("Hardware Acceleration: DISABLED (Using CPU - Software Rendering)")

            # Shader support
            if gsg.getSupportsBasicShaders():
                print("Shader Support: YES")
            else:
                print("Shader Support: NO")

            # Texture stages
            print(f"Max Texture Stages: {gsg.getMaxTextureStages()}")

            # Additional GPU capabilities
            if hasattr(gsg, 'getMaxVertexTextureImages'):
                print(f"Max Vertex Textures: {gsg.getMaxVertexTextureImages()}")
            if hasattr(gsg, 'getMaxLights'):
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
        """Setup basic lighting"""
        # Ambient light
        alight = AmbientLight("alight")
        alight.setColor((0.3, 0.3, 0.3, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)

        # Directional light (sun)
        dlight = DirectionalLight("dlight")
        dlight.setColor((0.8, 0.8, 0.7, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(45, -60, 0)
        self.render.setLight(dlnp)

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

        # Tool switching
        self.accept("q", self.tool_manager.cycle_tool)

        # Tool usage - Mouse buttons
        self.accept("mouse1", self.on_mouse_down, [1])  # Left click
        self.accept("mouse1-up", self.on_mouse_up, [1])
        self.accept("mouse3", self.on_mouse_down, [3])  # Right click
        self.accept("mouse3-up", self.on_mouse_up, [3])
        self.accept("mouse2", self.on_mouse_down, [2])  # Middle click
        self.accept("mouse2-up", self.on_mouse_up, [2])

        # Terrain mode switching (only when terrain tool is active)
        self.accept("1", self.set_terrain_mode, ["lower"])
        self.accept("2", self.set_terrain_mode, ["raise"])
        self.accept("3", self.set_terrain_mode, ["smooth"])

        # Brush size adjustment
        self.accept("wheel_up", self.adjust_brush_size, [1])
        self.accept("wheel_down", self.adjust_brush_size, [-1])

        # Shadow quality adjustments
        self.accept("z", self.adjust_shadow_softness, [-0.5])  # Decrease softness
        self.accept("x", self.adjust_shadow_softness, [0.5])  # Increase softness
        self.accept("c", self.toggle_post_process)  # Toggle post-processing

        # Debug visualization
        self.accept("v", self.toggle_chunk_colors)  # Toggle chunk debug colors
        self.accept("b", self.toggle_wireframe)  # Toggle wireframe
        self.accept("r", self.toggle_raycast_debug)  # Toggle raycast debug visualization

        # Quit
        self.accept("escape", self.quit_game)

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
        if active_tool and active_tool.tool_type in [ToolType.GUN, ToolType.CROWBAR, ToolType.FIST]:
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

    def adjust_brush_size(self, direction):
        """Adjust terrain brush size.

        Args:
            direction: 1 for increase, -1 for decrease
        """
        new_size = self.terrain_editor.brush_size + direction
        self.terrain_editor.set_brush_size(new_size)
        self.brush_indicator.update_size(new_size)
        print(f"Brush size: {self.terrain_editor.brush_size:.1f}")

    def adjust_shadow_softness(self, delta):
        """Adjust shadow softness.

        Args:
            delta: Amount to adjust softness by
        """
        if self.shadow_manager:
            current = self.shadow_manager.shadow_softness
            new_softness = max(0.5, min(10.0, current + delta))
            self.shadow_manager.set_shadow_softness(new_softness)
            self.shadow_manager.set_shader_inputs(self.render)
            print(f"Shadow softness: {new_softness:.1f}")
        else:
            print("Shadows are disabled (for performance)")

    def toggle_post_process(self):
        """Toggle post-processing effects."""
        if self.post_process:
            enabled = self.post_process.toggle()
            print(f"Post-processing: {'ON' if enabled else 'OFF'}")
        else:
            print("Post-processing is disabled (for performance)")

    def toggle_chunk_colors(self):
        """Toggle debug chunk colors."""
        try:
            import config.settings as settings
            settings.DEBUG_CHUNK_COLORS = not settings.DEBUG_CHUNK_COLORS
            print(f"\n=== Chunk debug colors: {'ON' if settings.DEBUG_CHUNK_COLORS else 'OFF'} ===")
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
            print(f"\n=== Wireframe debug: {'ON' if settings.DEBUG_CHUNK_WIREFRAME else 'OFF'} ===")
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

    def set_terrain_mode(self, mode):
        """Set terrain editing mode (only works with terrain tool).

        Args:
            mode: 'lower', 'raise', or 'smooth'
        """
        active_tool = self.tool_manager.get_active_tool()
        if active_tool and active_tool.tool_type == ToolType.TERRAIN:
            active_tool.set_mode(mode)
        else:
            self.hud.show_message("Terrain modes only work with Terrain tool! Press Q to switch.")

    def quit_game(self):
        """Clean quit handler"""
        print("\nQuitting game...")
        if self.shadow_manager:
            self.shadow_manager.cleanup()
        self.userExit()

    def update(self, task):
        """Main game loop"""
        dt = globalClock.getDt()

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
                button = getattr(self, 'current_mouse_button', 1)
                if button == 1:  # Left click
                    self.tool_manager.use_primary(hit)
                elif button == 3:  # Right click
                    self.tool_manager.use_secondary(hit)
                elif button == 2:  # Middle click
                    self.tool_manager.use_tertiary(hit)
        else:
            self.brush_indicator.hide()

        # Update tool manager
        self.tool_manager.update(dt)

        # Update effects
        self.effects_manager.update(dt)

        # Update HUD
        self.hud.update(dt)

        # Update player movement
        self.player.update(dt, self.camera_controller)

        # Update camera to follow player
        player_pos = self.player.get_position()
        self.camera_controller.update_position(player_pos)
        self.camera_controller.apply_rotation()

        # Update physics
        self.world.doPhysics(dt, 10, 1.0 / PHYSICS_FPS)

        # Update game world
        self.game_world.update(dt, player_pos)

        return task.cont


if __name__ == "__main__":
    app = Game()
    app.run()
