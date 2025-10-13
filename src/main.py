from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import BulletWorld, BulletDebugNode
from panda3d.core import AmbientLight, DirectionalLight, Vec3, WindowProperties

from config.settings import configure, PHYSICS_FPS, GRAVITY
from engine.world import World
from player.controller import PlayerController
from player.camera import CameraController
from interaction.raycast import TerrainRaycaster
from interaction.terrain_editor import TerrainEditor
from rendering.brush_indicator import BrushIndicator
from rendering.shadow_manager import ShadowManager
from rendering.post_process import PostProcessManager


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

        # Initialize shadow system
        light_dir = Vec3(1, 1, -1)  # Sun direction
        self.shadow_manager = ShadowManager(self, self.render, light_dir)
        self.shadow_manager.set_shader_inputs(self.render)

        # Initialize post-processing
        self.post_process = PostProcessManager(self.render, self.cam)

        # Terrain editing state
        self.editing_terrain = False

        # Setup input
        self.setup_input()

        # Setup mouse control
        self.mouse_captured = True
        self.setup_mouse_control()

        # Update task
        self.taskMgr.add(self.update, "update")

        print("Game initialized successfully!")
        print("\nControls:")
        print("  WASD - Move")
        print("  Shift - Run")
        print("  Space - Jump")
        print("  Mouse - Look around")
        print("  M - Toggle mouse capture")
        print("")
        print("  Left Click - Lower terrain (dig)")
        print("  Right Click - Raise terrain (build)")
        print("  Middle Click - Smooth terrain")
        print("  Scroll Wheel - Adjust brush size")
        print("  1/2/3 - Set edit mode (raise/lower/smooth)")
        print("")
        print("  Z/X - Adjust shadow softness")
        print("  C - Toggle post-processing")
        print("  ESC - Quit")

    def setup_physics(self):
        """Initialize Bullet physics world"""
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, GRAVITY))
        
        # Optional: Enable debug visualization
        debugNode = BulletDebugNode('Debug')
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
        alight = AmbientLight('alight')
        alight.setColor((0.3, 0.3, 0.3, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)

        # Directional light (sun)
        dlight = DirectionalLight('dlight')
        dlight.setColor((0.8, 0.8, 0.7, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(45, -60, 0)
        self.render.setLight(dlnp)

    def setup_input(self):
        """Setup keyboard input handlers"""
        # Movement keys
        self.accept('w', self.player.handle_input, ['w', True])
        self.accept('w-up', self.player.handle_input, ['w', False])
        self.accept('s', self.player.handle_input, ['s', True])
        self.accept('s-up', self.player.handle_input, ['s', False])
        self.accept('a', self.player.handle_input, ['a', True])
        self.accept('a-up', self.player.handle_input, ['a', False])
        self.accept('d', self.player.handle_input, ['d', True])
        self.accept('d-up', self.player.handle_input, ['d', False])

        # Jump and run
        self.accept('space', self.player.handle_input, ['space', True])
        self.accept('space-up', self.player.handle_input, ['space', False])
        self.accept('shift', self.player.handle_input, ['shift', True])
        self.accept('shift-up', self.player.handle_input, ['shift', False])

        # Mouse toggle
        self.accept('m', self.toggle_mouse)

        # Terrain editing - Mouse buttons
        self.accept('mouse1', self.on_mouse_down, [1])  # Left click
        self.accept('mouse1-up', self.on_mouse_up, [1])
        self.accept('mouse3', self.on_mouse_down, [3])  # Right click
        self.accept('mouse3-up', self.on_mouse_up, [3])
        self.accept('mouse2', self.on_mouse_down, [2])  # Middle click
        self.accept('mouse2-up', self.on_mouse_up, [2])

        # Terrain editing - Mode switching
        self.accept('1', self.terrain_editor.set_edit_mode, ['lower'])
        self.accept('2', self.terrain_editor.set_edit_mode, ['raise'])
        self.accept('3', self.terrain_editor.set_edit_mode, ['smooth'])

        # Brush size adjustment
        self.accept('wheel_up', self.adjust_brush_size, [1])
        self.accept('wheel_down', self.adjust_brush_size, [-1])

        # Shadow quality adjustments
        self.accept('z', self.adjust_shadow_softness, [-0.5])  # Decrease softness
        self.accept('x', self.adjust_shadow_softness, [0.5])   # Increase softness
        self.accept('c', self.toggle_post_process)              # Toggle post-processing

        # Quit
        self.accept('escape', self.quit_game)

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
        self.editing_terrain = True

    def on_mouse_up(self, button):
        """Handle mouse button release.

        Args:
            button: Mouse button number
        """
        self.editing_terrain = False

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

        # Handle terrain editing
        hit = self.raycaster.get_terrain_hit(self.mouseWatcherNode)
        if hit:
            # Update brush indicator position
            self.brush_indicator.update_position(hit['position'])
            self.brush_indicator.show()

            # Perform terrain editing if mouse button is held
            if self.editing_terrain:
                self.terrain_editor.modify_terrain(hit['position'])
        else:
            self.brush_indicator.hide()

        # Update player movement
        self.player.update(dt, self.camera_controller)

        # Update camera to follow player
        player_pos = self.player.get_position()
        self.camera_controller.update_position(player_pos)
        self.camera_controller.apply_rotation()

        # Update physics
        self.world.doPhysics(dt, 10, 1.0/PHYSICS_FPS)

        # Update game world
        self.game_world.update(dt, player_pos)

        return task.cont

if __name__ == "__main__":
    app = Game()
    app.run()