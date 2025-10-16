"""Raycasting specifically for building/physics objects."""

from panda3d.core import Vec3


class BuildingRaycaster:
    """Performs raycasts against physics objects (buildings)."""

    def __init__(self, bullet_world, render):
        """Initialize building raycaster.

        Args:
            bullet_world: Bullet physics world
            render: Panda3D render node
        """
        self.bullet_world = bullet_world
        self.render = render

    def raycast_from_camera(self, camera, max_distance=100.0):
        """Perform raycast from camera forward.

        Args:
            camera: Camera node
            max_distance: Maximum ray distance

        Returns:
            dict with keys: hit (bool), position (Vec3), normal (Vec3), node (NodePath), distance (float)
        """
        # Get camera position in world space
        cam_pos = camera.getPos(self.render)

        # Get forward direction (Y-forward in Panda3D camera space)
        forward = self.render.getRelativeVector(camera, Vec3(0, 1, 0))
        forward.normalize()

        # Calculate end position
        end_pos = cam_pos + forward * max_distance

        # Perform bullet physics raycast
        result = self.bullet_world.rayTestClosest(cam_pos, end_pos)

        if result.hasHit():
            hit_pos = result.getHitPos()
            hit_normal = result.getHitNormal()
            hit_node = result.getNode()
            distance = (hit_pos - cam_pos).length()

            return {
                "hit": True,
                "position": hit_pos,
                "normal": hit_normal,
                "node": hit_node,
                "distance": distance,
            }
        else:
            # No hit - return end position
            return {
                "hit": False,
                "position": end_pos,
                "normal": Vec3(0, 0, 1),
                "node": None,
                "distance": max_distance,
            }

    def raycast(self, start_pos, end_pos):
        """Perform raycast between two points.

        Args:
            start_pos: Vec3 starting position
            end_pos: Vec3 ending position

        Returns:
            dict with hit information
        """
        result = self.bullet_world.rayTestClosest(start_pos, end_pos)

        if result.hasHit():
            hit_pos = result.getHitPos()
            hit_normal = result.getHitNormal()
            hit_node = result.getNode()
            distance = (hit_pos - start_pos).length()

            return {
                "hit": True,
                "position": hit_pos,
                "normal": hit_normal,
                "node": hit_node,
                "distance": distance,
            }
        else:
            distance = (end_pos - start_pos).length()
            return {
                "hit": False,
                "position": end_pos,
                "normal": Vec3(0, 0, 1),
                "node": None,
                "distance": distance,
            }

    def raycast_all(self, start_pos, end_pos):
        """Perform raycast and get ALL hits along the ray.

        Args:
            start_pos: Vec3 starting position
            end_pos: Vec3 ending position

        Returns:
            list of dicts with hit information, sorted by distance
        """
        result = self.bullet_world.rayTestAll(start_pos, end_pos)

        hits = []
        if result.hasHits():
            for i in range(result.getNumHits()):
                hit = result.getHit(i)
                hit_pos = hit.getHitPos()
                hit_normal = hit.getHitNormal()
                hit_node = hit.getNode()
                distance = (hit_pos - start_pos).length()

                hits.append(
                    {
                        "hit": True,
                        "position": hit_pos,
                        "normal": hit_normal,
                        "node": hit_node,
                        "distance": distance,
                    }
                )

        # Sort by distance (closest first)
        hits.sort(key=lambda h: h["distance"])
        return hits
