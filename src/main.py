from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import BulletWorld, BulletDebugNode
from panda3d.core import AmbientLight, DirectionalLight, Vec3, WindowProperties

from config.settings import configure, PHYSICS_FPS, GRAVITY
from engine.world import World
from player.controller import PlayerController
from player.camera import CameraController


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

    def quit_game(self):
        """Clean quit handler"""
        print("\nQuitting game...")
        self.userExit()
    
    def update(self, task):
        """Main game loop"""
        dt = globalClock.getDt()

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