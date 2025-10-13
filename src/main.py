from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import BulletWorld, BulletDebugNode
from panda3d.core import AmbientLight, DirectionalLight, Vec3

from config.settings import configure, PHYSICS_FPS, GRAVITY
from engine.world import World


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

        # Setup camera
        self.camera.setPos(0, -50, 30)
        self.camera.lookAt(0, 0, 0)

        # Update task
        self.taskMgr.add(self.update, "update")

        print("Game initialized successfully!")

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
    
    def update(self, task):
        """Main game loop"""
        dt = globalClock.getDt()

        # Update physics
        self.world.doPhysics(dt, 10, 1.0/PHYSICS_FPS)

        # Update game world
        camera_pos = self.camera.getPos()
        self.game_world.update(dt, camera_pos)

        return task.cont

if __name__ == "__main__":
    app = Game()
    app.run()