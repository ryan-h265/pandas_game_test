"""Raycasting utilities for object selection and interaction."""

from panda3d.core import Vec3, Point3, CollisionTraverser, CollisionNode, CollisionRay, CollisionHandlerQueue


class TerrainRaycaster:
    """Handles raycasting for terrain selection and interaction."""

    def __init__(self, camera, render):
        """Initialize raycaster.

        Args:
            camera: Panda3D camera NodePath
            render: Render node for collision traversal
        """
        self.camera = camera
        self.render = render

        # Setup collision system
        self.picker_traverser = CollisionTraverser()
        self.picker_queue = CollisionHandlerQueue()

        # Create picker ray
        self.picker_node = CollisionNode('mouse_ray')
        self.picker_ray = CollisionRay()
        self.picker_node.addSolid(self.picker_ray)
        self.picker_node.setFromCollideMask(1)
        self.picker_np = self.camera.attachNewNode(self.picker_node)

        # Add to traverser
        self.picker_traverser.addCollider(self.picker_np, self.picker_queue)

    def get_terrain_hit(self, mouse_watcher):
        """Cast ray from camera through mouse position to find terrain hit.

        Args:
            mouse_watcher: MouseWatcher node

        Returns:
            Dict with hit info or None if no hit:
            {
                'position': Vec3 - world position of hit,
                'normal': Vec3 - surface normal at hit,
                'node': NodePath - hit object
            }
        """
        if not mouse_watcher.hasMouse():
            return None

        # Get mouse position
        mouse_pos = mouse_watcher.getMouse()

        # Set ray from camera through mouse position
        # camera is a NodePath, we need to get the actual Camera node
        cam_node = self.camera.node()
        self.picker_ray.setFromLens(cam_node, mouse_pos.getX(), mouse_pos.getY())

        # Perform collision check
        self.picker_traverser.traverse(self.render)

        if self.picker_queue.getNumEntries() > 0:
            # Sort by distance
            self.picker_queue.sortEntries()

            # Get closest hit
            entry = self.picker_queue.getEntry(0)

            hit_pos = entry.getSurfacePoint(self.render)
            hit_normal = entry.getSurfaceNormal(self.render)

            return {
                'position': Vec3(hit_pos.getX(), hit_pos.getY(), hit_pos.getZ()),
                'normal': Vec3(hit_normal.getX(), hit_normal.getY(), hit_normal.getZ()),
                'node': entry.getIntoNodePath()
            }

        return None

    def cast_ray_from_to(self, from_pos, to_pos):
        """Cast a ray between two points.

        Args:
            from_pos: Start position Vec3
            to_pos: End position Vec3

        Returns:
            Hit info dict or None
        """
        direction = to_pos - from_pos
        distance = direction.length()
        direction.normalize()

        # Create temporary ray
        ray = CollisionRay()
        ray.setOrigin(Point3(from_pos))
        ray.setDirection(direction)

        # Would need a separate traverser for this
        # For now, return None (can be implemented if needed)
        return None
