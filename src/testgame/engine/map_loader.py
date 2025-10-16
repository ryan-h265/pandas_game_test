"""Map loader for 3D model-based maps."""

from panda3d.core import NodePath, Vec3
from panda3d.bullet import (
    BulletRigidBodyNode,
    BulletTriangleMesh,
    BulletTriangleMeshShape,
)
from testgame.rendering.model_loader import ModelLoader
from testgame.config.settings import MAP_MODEL_SCALE


class MapLoader:
    """Loads and manages 3D model-based maps with physics collision."""

    def __init__(self, render, bullet_world):
        """Initialize map loader.

        Args:
            render: Panda3D render node
            bullet_world: Bullet physics world
        """
        self.render = render
        self.bullet_world = bullet_world
        self.model_loader = ModelLoader()
        self.map_node = None
        self.collision_node = None

    def load_map(self, model_path):
        """Load a 3D map model with physics collision.

        Args:
            model_path: Path to the map model (e.g., "assets/models/maps/rocks/scene.gltf")

        Returns:
            NodePath of the loaded map, or None if loading failed
        """
        print(f"Loading map model: {model_path}")

        # Load the model
        model = self.model_loader.load_gltf(model_path, cache=False)
        if model is None:
            print(f"ERROR: Failed to load map model: {model_path}")
            return None

        # Create map node and attach model
        self.map_node = self.render.attachNewNode("map")
        
        # Handle both NodePath and ModelRoot return types
        if isinstance(model, NodePath):
            model.reparentTo(self.map_node)
        else:
            # ModelRoot needs to be wrapped in NodePath
            model_np = NodePath(model)
            model_np.reparentTo(self.map_node)

        # Scale up the map (configurable via MAP_MODEL_SCALE setting)
        self.map_node.setScale(MAP_MODEL_SCALE, MAP_MODEL_SCALE, MAP_MODEL_SCALE)
        print(f"Map model loaded successfully (scaled {MAP_MODEL_SCALE}x)")

        # Create physics collision from the model geometry
        self._create_collision(self.map_node)

        return self.map_node

    def _create_collision(self, model):
        """Create static physics collision mesh from model geometry.

        Args:
            model: NodePath of the model to extract geometry from
        """
        print("Generating physics collision for map...")

        # Create triangle mesh for collision
        mesh = BulletTriangleMesh()

        # Recursively traverse the model and add all geometry
        triangle_count = self._add_geometry_to_mesh(model, mesh)

        # Create shape from mesh
        shape = BulletTriangleMeshShape(mesh, dynamic=False)

        # Create static rigid body (mass = 0)
        body_node = BulletRigidBodyNode("map_collision")
        body_node.addShape(shape)
        body_node.setMass(0)  # Static collision
        body_node.setFriction(0.7)
        body_node.setRestitution(0.3)

        # Attach collision to map node
        self.collision_node = self.map_node.attachNewNode(body_node)

        # Add to physics world
        self.bullet_world.attachRigidBody(body_node)

        print(f"Map collision generated with {triangle_count} triangles and added to physics world")

    def _add_geometry_to_mesh(self, node_path, mesh):
        """Recursively extract geometry from a node and add to triangle mesh.

        Args:
            node_path: NodePath to extract geometry from
            mesh: BulletTriangleMesh to add triangles to
            
        Returns:
            Number of triangles added
        """
        from panda3d.core import GeomNode
        
        triangle_count = 0

        # Check if this node is a GeomNode
        node = node_path.node()
        if isinstance(node, GeomNode):
            # Get the transform from this node to the root
            transform = node_path.getTransform(self.map_node)

            # Extract all geoms from this node
            for i in range(node.getNumGeoms()):
                geom = node.getGeom(i)
                # Count triangles before adding
                from panda3d.core import GeomTriangles
                for j in range(geom.getNumPrimitives()):
                    prim = geom.getPrimitive(j)
                    if prim.isOfType(GeomTriangles.getClassType()):
                        triangle_count += prim.getNumPrimitives()
                
                mesh.addGeom(geom, True, transform)

        # Recursively process children
        for child in node_path.getChildren():
            triangle_count += self._add_geometry_to_mesh(child, mesh)
            
        return triangle_count

    def unload_map(self):
        """Unload the current map and remove physics collision."""
        if self.collision_node:
            # Remove from physics world
            body_node = self.collision_node.node()
            self.bullet_world.removeRigidBody(body_node)
            self.collision_node.removeNode()
            self.collision_node = None

        if self.map_node:
            self.map_node.removeNode()
            self.map_node = None

        print("Map unloaded")

    def get_map_bounds(self):
        """Get the bounding box of the loaded map.

        Returns:
            Tuple of (min_point, max_point) as Vec3, or None if no map loaded
        """
        if not self.map_node:
            return None

        # Get tight bounds of the model
        bounds = self.map_node.getTightBounds()
        if bounds:
            min_point, max_point = bounds
            return (Vec3(min_point), Vec3(max_point))

        return None
