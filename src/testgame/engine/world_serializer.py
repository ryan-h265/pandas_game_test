"""World save/load system for persisting game state."""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from panda3d.core import Vec3, Vec4, Quat


class WorldSerializer:
    """Handles saving and loading of world state to/from files."""

    def __init__(self, saves_directory="saves"):
        """Initialize the world serializer.

        Args:
            saves_directory: Directory to store save files (relative to project root)
        """
        self.saves_dir = Path(saves_directory)
        self.saves_dir.mkdir(exist_ok=True)

    def get_save_path(self, save_name):
        """Get the full path for a save file.

        Args:
            save_name: Name of the save file (without extension)

        Returns:
            Path object for the save file
        """
        return self.saves_dir / f"{save_name}.json"

    def save_world(self, world, player, save_name, metadata=None):
        """Save the current world state to a file.

        Args:
            world: World instance to save
            player: PlayerController instance to save
            save_name: Name for the save file
            metadata: Optional dict with additional metadata (title, description, etc.)

        Returns:
            bool: True if save was successful
        """
        try:
            save_data = {
                "metadata": {
                    "version": "1.0",
                    "timestamp": datetime.now().isoformat(),
                    "save_name": save_name,
                    **(metadata or {}),
                },
                "player": self._serialize_player(player),
                "terrain": self._serialize_terrain(world.terrain),
                "buildings": self._serialize_buildings(world.buildings),
                "props": self._serialize_props(getattr(world, "props", [])),
                "physics_objects": self._serialize_physics_objects(
                    world.physics_objects
                ),
                "world_state": {
                    "loaded_chunks": list(world.loaded_chunks),
                },
            }

            save_path = self.get_save_path(save_name)
            with open(save_path, "w") as f:
                json.dump(save_data, f, indent=2)

            print(f"World saved successfully to {save_path}")
            return True

        except Exception as e:
            print(f"Error saving world: {e}")
            import traceback

            traceback.print_exc()
            return False

    def load_world(self, world, player, save_name):
        """Load a world state from a file.

        Args:
            world: World instance to load into
            player: PlayerController instance to update
            save_name: Name of the save file to load

        Returns:
            bool: True if load was successful
        """
        try:
            save_path = self.get_save_path(save_name)
            if not save_path.exists():
                print(f"Save file not found: {save_path}")
                return False

            with open(save_path, "r") as f:
                save_data = json.load(f)

            # Clear existing world state
            self._clear_world(world)

            # Load terrain
            self._deserialize_terrain(save_data["terrain"], world.terrain)

            # Load buildings
            self._deserialize_buildings(save_data["buildings"], world)

            # Load props
            self._deserialize_props(save_data.get("props", []), world)

            # Load physics objects
            self._deserialize_physics_objects(save_data["physics_objects"], world)

            # Load player state
            self._deserialize_player(save_data["player"], player)

            # Restore world state
            world.loaded_chunks = set(
                tuple(chunk) for chunk in save_data["world_state"]["loaded_chunks"]
            )

            print(f"World loaded successfully from {save_path}")
            return True

        except Exception as e:
            print(f"Error loading world: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _serialize_player(self, player):
        """Serialize player state.

        Args:
            player: PlayerController instance

        Returns:
            dict with player state
        """
        position = player.character_np.getPos()

        # Character controllers don't have getLinearVelocity like rigid bodies
        # We'll just save the position and let the player start stationary
        return {
            "position": [position.x, position.y, position.z],
            "on_ground": player.character.isOnGround(),
        }

    def _deserialize_player(self, data, player):
        """Deserialize player state.

        Args:
            data: Dict with player state
            player: PlayerController instance to update
        """
        pos = Vec3(*data["position"])
        player.character_np.setPos(pos)
        player.position = pos  # Update the cached position too

        # Character controllers don't need velocity restoration
        # They start stationary which is fine for loading a save

    def _serialize_terrain(self, terrain):
        """Serialize terrain state.

        Args:
            terrain: Terrain instance

        Returns:
            dict with terrain data
        """
        chunks = {}
        for (chunk_x, chunk_z), chunk in terrain.chunks.items():
            chunks[f"{chunk_x},{chunk_z}"] = {
                "chunk_x": chunk_x,
                "chunk_z": chunk_z,
                "height_data": chunk.height_data.tolist(),  # Convert numpy array to list
                "resolution": chunk.resolution,
            }

        return {
            "chunks": chunks,
        }

    def _deserialize_terrain(self, data, terrain):
        """Deserialize terrain state.

        Args:
            data: Dict with terrain data
            terrain: Terrain instance to update
        """
        # Remove all existing chunks
        for chunk_coord in list(terrain.chunks.keys()):
            terrain.remove_chunk(chunk_coord[0], chunk_coord[1])

        # Load saved chunks
        for chunk_key, chunk_data in data["chunks"].items():
            chunk_x = chunk_data["chunk_x"]
            chunk_z = chunk_data["chunk_z"]

            # Generate chunk
            chunk = terrain.generate_chunk(chunk_x, chunk_z)

            # Restore height data
            chunk.height_data = np.array(chunk_data["height_data"])

            # Rebuild mesh and collision with restored data
            chunk._update_mesh()
            chunk._update_collision()

    def _serialize_buildings(self, buildings):
        """Serialize all buildings.

        Args:
            buildings: List of Building instances

        Returns:
            list of dicts with building data
        """
        serialized = []
        for building in buildings:
            building_data = {
                "type": building.__class__.__name__,
                "name": building.name,
                "position": self._vec3_to_list(building.position),
                "pieces": [],
            }

            # Serialize each piece (building.pieces is a list, not a dict)
            for piece in building.pieces:
                if not piece.is_destroyed:
                    piece_data = {
                        "name": piece.name,
                        "position": self._vec3_to_list(piece.body_np.getPos()),
                        "rotation": self._quat_to_list(piece.body_np.getQuat()),
                        "size": self._vec3_to_list(piece.size),
                        "color": self._vec4_to_list(piece.color),
                        "mass": piece.mass,
                        "health": piece.health,
                        "piece_type": piece.piece_type,
                    }

                    # Store velocity if piece is moving
                    body_node = piece.body_np.node()
                    velocity = body_node.getLinearVelocity()
                    angular_velocity = body_node.getAngularVelocity()

                    piece_data["velocity"] = self._vec3_to_list(velocity)
                    piece_data["angular_velocity"] = self._vec3_to_list(
                        angular_velocity
                    )

                    building_data["pieces"].append(piece_data)

            # Only save building if it has pieces
            if building_data["pieces"]:
                serialized.append(building_data)

        return serialized

    def _deserialize_buildings(self, data, world):
        """Deserialize buildings.

        Args:
            data: List of dicts with building data
            world: World instance to add buildings to
        """
        from testgame.structures.building import Building, BuildingPiece

        for building_data in data:
            building_type = building_data["type"]
            position = Vec3(*building_data["position"])

            # Create appropriate building type
            if building_type == "SimpleBuilding":
                # For SimpleBuilding, we need to reconstruct it manually
                # since it has special constructor parameters
                building = Building(
                    world.bullet_world,
                    world.render,
                    position,
                    name=building_data["name"],
                )

                # Add each piece
                for piece_data in building_data["pieces"]:
                    piece_pos = Vec3(*piece_data["position"])
                    piece_size = Vec3(*piece_data["size"])
                    piece_color = Vec4(*piece_data["color"])

                    piece = BuildingPiece(
                        world.bullet_world,
                        world.render,
                        piece_pos,
                        piece_size,
                        piece_data["mass"],
                        piece_color,
                        piece_data["name"],
                        piece_type=piece_data["piece_type"],
                        parent_building=building,
                    )

                    # Restore rotation
                    piece.body_np.setQuat(Quat(*piece_data["rotation"]))

                    # Restore velocity
                    piece.body_np.node().setLinearVelocity(
                        Vec3(*piece_data["velocity"])
                    )
                    piece.body_np.node().setAngularVelocity(
                        Vec3(*piece_data["angular_velocity"])
                    )

                    # Restore health
                    piece.health = piece_data["health"]

                    building.add_piece(piece)

                world.buildings.append(building)
            else:
                # Generic building type
                building = Building(
                    world.bullet_world,
                    world.render,
                    position,
                    name=building_data["name"],
                )

                for piece_data in building_data["pieces"]:
                    piece_pos = Vec3(*piece_data["position"])
                    piece_size = Vec3(*piece_data["size"])
                    piece_color = Vec4(*piece_data["color"])

                    piece = BuildingPiece(
                        world.bullet_world,
                        world.render,
                        piece_pos,
                        piece_size,
                        piece_data["mass"],
                        piece_color,
                        piece_data["name"],
                        piece_type=piece_data["piece_type"],
                        parent_building=building,
                    )

                    piece.body_np.setQuat(Quat(*piece_data["rotation"]))
                    piece.body_np.node().setLinearVelocity(
                        Vec3(*piece_data["velocity"])
                    )
                    piece.body_np.node().setAngularVelocity(
                        Vec3(*piece_data["angular_velocity"])
                    )
                    piece.health = piece_data["health"]

                    building.add_piece(piece)

                world.buildings.append(building)

    def _serialize_physics_objects(self, physics_objects):
        """Serialize physics objects (like cubes).

        Args:
            physics_objects: List of NodePath objects with physics

        Returns:
            list of dicts with object data
        """
        serialized = []
        for obj_np in physics_objects:
            if obj_np and not obj_np.isEmpty():
                body_node = obj_np.node()

                obj_data = {
                    "name": obj_np.getName(),
                    "position": self._vec3_to_list(obj_np.getPos()),
                    "rotation": self._quat_to_list(obj_np.getQuat()),
                    "velocity": self._vec3_to_list(body_node.getLinearVelocity()),
                    "angular_velocity": self._vec3_to_list(
                        body_node.getAngularVelocity()
                    ),
                    "mass": body_node.getMass(),
                }

                # Try to extract size and color from the object
                # This is a simplified approach - may need customization
                try:
                    # Get the shape
                    shape = body_node.getShape(0)
                    if shape:
                        # For box shapes, try to get half extents
                        from panda3d.bullet import BulletBoxShape

                        if isinstance(shape, BulletBoxShape):
                            half_extents = shape.getHalfExtentsWithoutMargin()
                            obj_data["size"] = self._vec3_to_list(
                                half_extents * 2
                            )  # Convert to full size

                    # Try to extract color from geometry
                    # This is approximate - you may want to store this explicitly
                    obj_data["color"] = [0.7, 0.7, 0.7, 1.0]  # Default gray

                except Exception as e:
                    print(
                        f"Warning: Could not extract full data for {obj_np.getName()}: {e}"
                    )
                    obj_data["size"] = [1.0, 1.0, 1.0]
                    obj_data["color"] = [0.7, 0.7, 0.7, 1.0]

                serialized.append(obj_data)

        return serialized

    def _deserialize_physics_objects(self, data, world):
        """Deserialize physics objects.

        Args:
            data: List of dicts with object data
            world: World instance to add objects to
        """
        for obj_data in data:
            position = Vec3(*obj_data["position"])
            size = Vec3(*obj_data.get("size", [1.0, 1.0, 1.0]))
            mass = obj_data["mass"]

            # Recreate the physics cube
            obj_np = world._create_physics_cube(
                position,
                size.x,  # Assuming cube (size is half-extent * 2)
                mass,
                obj_data["name"],
            )

            # Restore rotation
            obj_np.setQuat(Quat(*obj_data["rotation"]))

            # Restore velocities
            obj_np.node().setLinearVelocity(Vec3(*obj_data["velocity"]))
            obj_np.node().setAngularVelocity(Vec3(*obj_data["angular_velocity"]))

            world.physics_objects.append(obj_np)

    def _serialize_props(self, props):
        """Serialize decorative props (glTF models).

        Args:
            props: List of prop instances

        Returns:
            list of dicts with prop data
        """
        serialized = []

        for prop in props:
            try:
                base_position = getattr(prop, "position", None)
                if base_position is None and hasattr(prop, "get_position"):
                    base_position = prop.get_position()

                if base_position is None:
                    continue

                if isinstance(base_position, Vec3):
                    position_vec = base_position
                else:
                    position_vec = Vec3(*base_position)

                position_list = self._vec3_to_list(position_vec)

                prop_entry = {
                    "type": prop.__class__.__name__,
                    "position": position_list,
                    "static": getattr(prop, "static", True),
                }

                # Capture orientation (prefer physics body for dynamic props)
                rotation_quat = None
                if getattr(prop, "static", True):
                    model_node = getattr(prop, "model_node", None)
                    if model_node:
                        rotation_quat = model_node.getQuat()
                else:
                    physics_np = getattr(prop, "physics_body", None)
                    if physics_np:
                        rotation_quat = physics_np.getQuat()
                if rotation_quat:
                    prop_entry["rotation"] = self._quat_to_list(rotation_quat)

                # Capture scale for visual parity
                model_node = getattr(prop, "model_node", None)
                if model_node:
                    scale_vec = model_node.getScale()
                    prop_entry["scale"] = self._vec3_to_list(scale_vec)

                # Capture physics state for dynamic props
                physics_np = getattr(prop, "physics_body", None)
                if physics_np and not getattr(prop, "static", True):
                    body_node = physics_np.node()
                    prop_entry["linear_velocity"] = self._vec3_to_list(
                        body_node.getLinearVelocity()
                    )
                    prop_entry["angular_velocity"] = self._vec3_to_list(
                        body_node.getAngularVelocity()
                    )

                serialized.append(prop_entry)
            except Exception as exc:
                print(f"Warning: Could not serialize prop {prop}: {exc}")

        return serialized

    def _deserialize_props(self, data, world):
        """Deserialize decorative props from saved data."""

        if not data:
            return

        try:
            from testgame.props.lantern_prop import LanternProp
            from testgame.props.japanese_bar_prop import JapaneseBarProp
        except ImportError as exc:
            print(f"Warning: Could not import prop classes: {exc}")
            return

        prop_classes = {
            "LanternProp": LanternProp,
            "JapaneseBarProp": JapaneseBarProp,
        }

        point_light_manager = getattr(world, "point_light_manager", None)

        for prop_data in data:
            prop_type = prop_data.get("type")
            prop_class = prop_classes.get(prop_type)

            if not prop_class:
                print(f"Warning: Unknown prop type '{prop_type}', skipping")
                continue

            try:
                position = Vec3(*prop_data.get("position", [0, 0, 0]))
                static = prop_data.get("static", True)

                prop_instance = prop_class(
                    world.bullet_world,
                    world.render,
                    position,
                    point_light_manager=point_light_manager,
                    static=static,
                )

                if hasattr(prop_instance, "set_position"):
                    prop_instance.set_position(position)

                # Restore scale if saved
                scale_data = prop_data.get("scale")
                if scale_data and hasattr(prop_instance, "model_node"):
                    model_node = prop_instance.model_node
                    if model_node:
                        model_node.setScale(*scale_data)

                # Restore rotation (apply to both visual and physics nodes as needed)
                rotation_data = prop_data.get("rotation")
                if rotation_data:
                    rotation_quat = Quat(*rotation_data)
                    physics_np = getattr(prop_instance, "physics_body", None)
                    model_node = getattr(prop_instance, "model_node", None)

                    if physics_np:
                        physics_np.setQuat(rotation_quat)
                    if model_node and getattr(prop_instance, "static", True):
                        model_node.setQuat(rotation_quat)

                # Restore physics velocity for dynamic props
                if not getattr(prop_instance, "static", True):
                    physics_np = getattr(prop_instance, "physics_body", None)
                    if physics_np:
                        body_node = physics_np.node()
                        linear_velocity = prop_data.get("linear_velocity")
                        angular_velocity = prop_data.get("angular_velocity")

                        if linear_velocity:
                            body_node.setLinearVelocity(Vec3(*linear_velocity))
                        if angular_velocity:
                            body_node.setAngularVelocity(Vec3(*angular_velocity))

                if hasattr(world, "add_prop"):
                    world.add_prop(prop_instance)
                else:
                    world.props.append(prop_instance)

            except Exception as exc:
                print(f"Warning: Failed to deserialize prop '{prop_type}': {exc}")

    def _clear_world(self, world):
        """Clear all existing world objects before loading.

        Args:
            world: World instance to clear
        """
        # Remove all buildings
        for building in world.buildings:
            building.destroy()
        world.buildings.clear()

        # Remove all props (gltf models, lights)
        for prop in getattr(world, "props", []):
            try:
                if hasattr(prop, "remove"):
                    prop.remove()
            except Exception as exc:
                print(f"Warning: Failed to remove prop during clear: {exc}")
        if hasattr(world, "props"):
            world.props.clear()

        # Remove all physics objects
        for obj_np in world.physics_objects:
            if obj_np and not obj_np.isEmpty():
                body_node = obj_np.node()
                world.bullet_world.removeRigidBody(body_node)
                obj_np.removeNode()
        world.physics_objects.clear()

    # Helper methods for converting Panda3D types to/from JSON-serializable formats
    def _vec3_to_list(self, vec):
        """Convert Vec3 to list."""
        return [vec.x, vec.y, vec.z]

    def _vec4_to_list(self, vec):
        """Convert Vec4 to list."""
        return [vec.x, vec.y, vec.z, vec.w]

    def _quat_to_list(self, quat):
        """Convert Quat to list."""
        return [quat.getR(), quat.getI(), quat.getJ(), quat.getK()]


class WorldTemplateManager:
    """Manages world templates/presets that can be loaded."""

    def __init__(self, templates_directory="world_templates"):
        """Initialize the template manager.

        Args:
            templates_directory: Directory containing world templates
        """
        self.templates_dir = Path(templates_directory)
        self.templates_dir.mkdir(exist_ok=True)

    def create_template(self, name, description, build_function):
        """Create a new world template.

        Args:
            name: Template name
            description: Description of the template
            build_function: Function that builds the world (takes world as parameter)

        Returns:
            dict with template metadata
        """
        template_data = {
            "name": name,
            "description": description,
            "created": datetime.now().isoformat(),
        }

        template_path = self.templates_dir / f"{name}.json"
        with open(template_path, "w") as f:
            json.dump(template_data, f, indent=2)

        return template_data

    def list_templates(self):
        """List all available templates.

        Returns:
            List of template metadata dicts
        """
        templates = []
        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file, "r") as f:
                    template_data = json.load(f)
                    templates.append(template_data)
            except Exception as e:
                print(f"Error reading template {template_file}: {e}")
        return templates

    def load_template(self, name, world):
        """Load a world template.

        Args:
            name: Template name
            world: World instance to load into

        Returns:
            bool: True if successful
        """
        # Templates are more like "generators" - you'd implement specific
        # template loading logic here based on your needs
        print(f"Loading template: {name}")
        # This would call specific world generation functions
        return True
