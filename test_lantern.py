"""Quick test to verify lantern loading works."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import BulletWorld
from panda3d.core import Vec3
from props.lantern_prop import LanternProp
from rendering.point_light_manager import PointLightManager


class LanternTest(ShowBase):
    """Simple test app to load and display a lantern."""

    def __init__(self):
        ShowBase.__init__(self)

        # Setup camera
        self.camera.setPos(5, -10, 3)
        self.camera.lookAt(0, 0, 1)

        # Setup physics
        self.world = BulletWorld()

        # Setup lighting
        from panda3d.core import AmbientLight, DirectionalLight

        alight = AmbientLight("alight")
        alight.setColor((0.5, 0.5, 0.5, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)

        dlight = DirectionalLight("dlight")
        dlight.setColor((1.0, 1.0, 1.0, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(45, -45, 0)
        self.render.setLight(dlnp)

        # Create point light manager
        self.point_light_manager = PointLightManager()

        # Try to create a lantern
        print("\n" + "=" * 60)
        print("TESTING LANTERN LOADING")
        print("=" * 60)

        try:
            lantern = LanternProp(
                self.world,
                self.render,
                Vec3(0, 0, 0),
                self.point_light_manager,
                static=True,
            )
            print("\nSUCCESS! Lantern loaded successfully!")
            print(f"Lantern position: {lantern.get_position()}")
            print(f"Point lights in scene: {len(self.point_light_manager.lights)}")

        except Exception as e:
            print(f"\nERROR loading lantern: {e}")
            import traceback

            traceback.print_exc()

        print("=" * 60 + "\n")
        print("Close the window to exit")


if __name__ == "__main__":
    app = LanternTest()
    app.run()
