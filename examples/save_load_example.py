"""Example script demonstrating the save/load system."""

from panda3d.core import Vec3
from testgame.engine.world import World

# This is a conceptual example - would be integrated into your Game class


def example_save_load_usage(game):
    """Example of using the save/load system in your game.

    Args:
        game: Game instance with game_world and player
    """

    # === QUICK SAVE/LOAD ===

    # Quick save (F5 by default)
    def quick_save():
        metadata = {"title": "Quick Save", "description": "Auto-saved game state"}
        success = game.game_world.save_to_file("quicksave", game.player, metadata)
        if success:
            print("Quick saved!")
            game.hud.show_message("Game saved!", duration=2.0)

    # Quick load (F9 by default)
    def quick_load():
        success = game.game_world.load_from_file("quicksave", game.player)
        if success:
            print("Quick loaded!")
            game.hud.show_message("Game loaded!", duration=2.0)

    # === NAMED SAVES ===

    def save_with_name(save_name):
        """Save with a custom name."""
        metadata = {
            "title": f"Save: {save_name}",
            "description": f"Player saved at {save_name}",
            "player_position": game.player.get_position(),
        }
        success = game.game_world.save_to_file(save_name, game.player, metadata)
        return success

    def load_by_name(save_name):
        """Load a specific save by name."""
        success = game.game_world.load_from_file(save_name, game.player)
        return success

    # === LISTING SAVES ===

    def list_all_saves():
        """List all available saves."""
        saves = game.list_saves()
        print(f"\nFound {len(saves)} save(s):")
        for save_name, metadata in saves:
            timestamp = metadata.get("timestamp", "Unknown")
            title = metadata.get("title", "Untitled")
            print(f"  - {save_name}: {title} ({timestamp})")
        return saves

    # === AUTO-SAVE SYSTEM ===

    class AutoSaveManager:
        """Manages automatic periodic saves."""

        def __init__(self, game, interval=300, max_autosaves=3):
            """Initialize auto-save manager.

            Args:
                game: Game instance
                interval: Seconds between auto-saves (default: 5 minutes)
                max_autosaves: Number of auto-saves to keep
            """
            self.game = game
            self.interval = interval
            self.max_autosaves = max_autosaves
            self.timer = 0
            self.enabled = True

        def update(self, dt):
            """Update auto-save timer."""
            if not self.enabled:
                return

            self.timer += dt
            if self.timer >= self.interval:
                self.perform_autosave()
                self.timer = 0

        def perform_autosave(self):
            """Perform an auto-save."""
            # Rotate existing auto-saves
            for i in range(self.max_autosaves - 1, 0, -1):
                old_name = f"autosave_{i}"
                new_name = f"autosave_{i + 1}"
                # In a real implementation, you'd rename the files
                # For now, they'll just be overwritten

            # Create new auto-save
            metadata = {
                "title": "Auto Save",
                "description": "Automatic periodic save",
                "autosave": True,
            }
            success = self.game.game_world.save_to_file(
                "autosave_1", self.game.player, metadata
            )

            if success:
                print("Auto-saved!")
                self.game.hud.show_message("Auto-saved", duration=1.5)

    # === CREATING EMPTY WORLDS ===

    def create_custom_world(render, bullet_world):
        """Create a world without auto-generating content."""
        # Create empty world
        world = World(render, bullet_world, auto_generate=False)

        # Optionally generate just terrain (no buildings)
        world._generate_initial_terrain()

        # Or load a saved world
        # world.load_from_file('my_custom_world', player)

        return world

    # === WORLD TEMPLATES ===

    def create_flat_world_template(world):
        """Example: Create a flat world template."""
        # Clear any existing content
        world.clear_world()

        # Generate flat terrain only
        world._generate_initial_terrain()

        # Don't add any buildings or objects
        print("Flat world template created")

    def create_city_template(world):
        """Example: Create a city world template."""
        # Clear existing
        world.clear_world()

        # Generate terrain
        world._generate_initial_terrain()

        # Add multiple buildings in a grid
        from src.structures.simple_building import SimpleBuilding

        for x in range(0, 100, 30):
            for y in range(0, 100, 30):
                building = SimpleBuilding(
                    world.bullet_world,
                    world.render,
                    Vec3(x, y, 0),
                    width=15,
                    depth=15,
                    height=10,
                    name=f"building_{x}_{y}",
                )
                world.buildings.append(building)

        print("City template created")

    # === SAVE FILE MANAGEMENT ===

    def delete_save(save_name):
        """Delete a save file."""
        import os

        save_path = game.game_world.serializer.get_save_path(save_name)
        if save_path.exists():
            os.remove(save_path)
            print(f"Deleted save: {save_name}")
            return True
        return False

    def backup_save(save_name, backup_name):
        """Create a backup copy of a save."""
        import shutil

        save_path = game.game_world.serializer.get_save_path(save_name)
        backup_path = game.game_world.serializer.get_save_path(backup_name)

        if save_path.exists():
            shutil.copy(save_path, backup_path)
            print(f"Backed up {save_name} to {backup_name}")
            return True
        return False

    # === INTEGRATION WITH GAME LOOP ===

    # Add to Game.__init__:
    # self.autosave_manager = AutoSaveManager(self, interval=300)

    # Add to Game.update():
    # self.autosave_manager.update(dt)

    # Add key bindings in Game.setup_input():
    # self.accept("f5", quick_save)
    # self.accept("f9", quick_load)


# Example of checking save data before loading
def inspect_save_file(save_name):
    """Inspect a save file without loading it."""
    import json
    from pathlib import Path

    save_path = Path("saves") / f"{save_name}.json"

    if not save_path.exists():
        print(f"Save not found: {save_name}")
        return None

    with open(save_path, "r") as f:
        data = json.load(f)

    print(f"\nSave: {save_name}")
    print(f"Version: {data['metadata']['version']}")
    print(f"Timestamp: {data['metadata']['timestamp']}")
    print(f"Title: {data['metadata'].get('title', 'Untitled')}")
    print(f"\nPlayer position: {data['player']['position']}")
    print(f"Terrain chunks: {len(data['terrain']['chunks'])}")
    print(f"Buildings: {len(data['buildings'])}")
    print(f"Physics objects: {len(data['physics_objects'])}")

    return data


if __name__ == "__main__":
    print("This is an example script showing save/load system usage.")
    print("See docs/SAVE_LOAD_SYSTEM.md for full documentation.")
