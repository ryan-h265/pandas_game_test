# World Save/Load System

## Overview
The world save/load system allows you to save the complete game state and reload it later. This includes terrain modifications, buildings, physics objects, and player position.

## Features

### What Gets Saved
- **Terrain**: All terrain chunks with their height modifications
- **Buildings**: All building structures with their pieces, health, positions, and rotations
- **Physics Objects**: Dynamic physics objects (cubes, debris, etc.) with their velocities
- **Player State**: Position, velocity, and on-ground status
- **World State**: Loaded chunk coordinates

### Save File Format
Save files are stored as JSON in the `saves/` directory (created automatically). Each save contains:
- Metadata (timestamp, save name, title, description)
- Complete world state
- Player state
- All object states with physics properties

## Usage

### Quick Save/Load
- **F5**: Quick save to 'quicksave' slot
- **F9**: Quick load from 'quicksave' slot

### Named Saves
- **F6**: Save with automatic timestamp (e.g., `save_20251014_143052`)
- **F7**: List all saves and load the most recent

### Programmatic API

#### Saving a World
```python
# From your game code
metadata = {
    'title': 'My Save Game',
    'description': 'Optional description',
    # Add any custom metadata you want
}
success = game_world.save_to_file('my_save_name', player, metadata)
```

#### Loading a World
```python
# Load a saved world
success = game_world.load_from_file('my_save_name', player)
```

#### Listing Saves
```python
# Get list of all saves with metadata
saves = game_world.list_saves()
for save_name, metadata in saves:
    print(f"{save_name}: {metadata['title']} ({metadata['timestamp']})")
```

#### Creating Empty World
```python
# Create world without auto-generating content
world = World(render, bullet_world, auto_generate=False)

# Then either load a save or manually populate
world.load_from_file('my_save', player)
# OR
world._generate_initial_terrain()
world._create_example_buildings()
```

## Implementation Details

### WorldSerializer Class
Located in `src/testgame/engine/world_serializer.py`, this class handles all serialization:

#### Key Methods
- `save_world(world, player, save_name, metadata)`: Save complete world state
- `load_world(world, player, save_name)`: Load world state
- `list_saves()`: List all available saves
- `get_save_path(save_name)`: Get full path to save file

#### Serialization Format
```json
{
  "metadata": {
    "version": "1.0",
    "timestamp": "2025-10-14T14:30:52.123456",
    "save_name": "quicksave",
    "title": "Quick Save",
    "description": "Auto-saved game state"
  },
  "player": {
    "position": [x, y, z],
    "velocity": [vx, vy, vz],
    "on_ground": true
  },
  "terrain": {
    "chunks": {
      "0,0": {
        "chunk_x": 0,
        "chunk_z": 0,
        "height_data": [[h00, h01, ...], ...],
        "resolution": 32
      }
    }
  },
  "buildings": [
    {
      "type": "SimpleBuilding",
      "name": "building_name",
      "position": [x, y, z],
      "pieces": [
        {
          "name": "piece_name",
          "position": [x, y, z],
          "rotation": [r, i, j, k],
          "size": [sx, sy, sz],
          "color": [r, g, b, a],
          "mass": 20.0,
          "health": 100.0,
          "piece_type": "wall",
          "velocity": [vx, vy, vz],
          "angular_velocity": [avx, avy, avz]
        }
      ]
    }
  ],
  "physics_objects": [...],
  "world_state": {
    "loaded_chunks": [[0, 0], [0, 1], ...]
  }
}
```

### Extending the System

#### Adding Custom Serializable Objects

1. **Add to World class**:
```python
# In src/testgame/engine/world.py
self.custom_objects = []
```

2. **Add to WorldSerializer**:
```python
# In src/testgame/engine/world_serializer.py
def _serialize_custom_objects(self, objects):
    serialized = []
    for obj in objects:
        obj_data = {
            'type': obj.__class__.__name__,
            'position': self._vec3_to_list(obj.get_position()),
            # Add more properties...
        }
        serialized.append(obj_data)
    return serialized

def _deserialize_custom_objects(self, data, world):
    for obj_data in data:
        # Recreate object from data
        obj = CustomObject(...)
        world.custom_objects.append(obj)
```

3. **Include in save/load**:
```python
# In save_world()
save_data['custom_objects'] = self._serialize_custom_objects(world.custom_objects)

# In load_world()
self._deserialize_custom_objects(save_data['custom_objects'], world)
```

#### Supporting New Building Types

The system automatically handles custom building types that inherit from `Building`:

```python
class MyCustomBuilding(Building):
    def __init__(self, world, render, position, custom_param, name="custom"):
        super().__init__(world, render, position, name)
        self.custom_param = custom_param
        # Build your structure...
```

To save custom parameters, extend `_serialize_buildings()`:
```python
building_data['custom_param'] = building.custom_param if hasattr(building, 'custom_param') else None
```

## Best Practices

### When to Save
- Before major actions (like destroying large structures)
- At natural checkpoints (entering new areas)
- On player request (F5 quick save)
- Periodically (auto-save every N minutes)

### Save File Management
```python
# Automatic save rotation
def manage_autosaves(world, player, max_saves=5):
    for i in range(max_saves-1, 0, -1):
        old_name = f"autosave_{i}"
        new_name = f"autosave_{i+1}"
        # Rename old saves
    
    # Create new autosave
    world.save_to_file('autosave_1', player, {
        'title': 'Auto Save',
        'description': f'Automatic save #{1}'
    })
```

### Error Handling
```python
try:
    success = world.save_to_file('my_save', player)
    if success:
        print("Saved successfully!")
    else:
        print("Save failed - check console for errors")
except Exception as e:
    print(f"Critical save error: {e}")
    # Handle gracefully - don't crash the game
```

## Performance Considerations

### Save Performance
- Saves are synchronous (game will pause briefly)
- Large worlds (many chunks/objects) take longer
- Typical save time: 0.1-0.5 seconds for normal worlds

### Load Performance
- Loads are synchronous (loads before game continues)
- Rebuilding terrain meshes is the slowest part
- Typical load time: 0.5-2 seconds for normal worlds

### Optimization Tips
1. **Limit save frequency**: Don't save every frame
2. **Clean up destroyed objects**: Remove old fragments before saving
3. **Compress large saves**: Consider using compression for height data
4. **Background saving**: For very large worlds, implement threaded saving

## Troubleshooting

### Save File Not Found
```
Error: Save file not found: saves/my_save.json
```
- Check that the `saves/` directory exists
- Verify the save name is correct
- Use `list_saves()` to see available saves

### Load Failed - Missing Data
```
Error loading world: KeyError: 'terrain'
```
- Save file may be corrupted
- Save file version mismatch
- Try loading a different save

### Objects Not Appearing After Load
- Ensure objects are added to world tracking lists
- Check that serialization includes all object types
- Verify deserialization properly recreates objects

### Terrain Looks Wrong After Load
- Height data may not be applying correctly
- Call `chunk._update_mesh()` after loading height data
- Check that terrain resolution matches save data

## Future Enhancements

### Planned Features
- **World Templates**: Pre-built world configurations
- **Compressed Saves**: Reduce file size for large worlds
- **Incremental Saves**: Save only changed objects
- **Cloud Saves**: Sync saves across devices
- **Save Thumbnails**: Generate preview images
- **Version Migration**: Handle saves from different game versions

### World Templates Example
```python
from engine.world_serializer import WorldTemplateManager

template_mgr = WorldTemplateManager()

# Create a flat world template
def build_flat_world(world):
    world._generate_initial_terrain()
    # Don't add any buildings

template_mgr.create_template(
    'flat_world',
    'Empty flat terrain with no structures',
    build_flat_world
)

# Load template
template_mgr.load_template('flat_world', world)
```

## API Reference

### World Methods
- `save_to_file(save_name, player, metadata=None)`: Save world
- `load_from_file(save_name, player)`: Load world
- `clear_world()`: Remove all objects

### WorldSerializer Methods
- `save_world(world, player, save_name, metadata)`: Main save function
- `load_world(world, player, save_name)`: Main load function
- `list_saves()`: List all saves with metadata
- `get_save_path(save_name)`: Get file path for save

### Helper Methods
- `_vec3_to_list(vec)`: Convert Vec3 to JSON list
- `_vec4_to_list(vec)`: Convert Vec4 to JSON list
- `_quat_to_list(quat)`: Convert Quat to JSON list
- `_serialize_player(player)`: Serialize player state
- `_serialize_terrain(terrain)`: Serialize terrain data
- `_serialize_buildings(buildings)`: Serialize all buildings
- `_serialize_physics_objects(objects)`: Serialize physics objects

## Examples

### Example 1: Auto-Save System
```python
class Game(ShowBase):
    def __init__(self):
        # ... initialization ...
        self.auto_save_timer = 0
        self.auto_save_interval = 300  # 5 minutes
        
    def update(self, task):
        dt = globalClock.getDt()
        
        # Auto-save every 5 minutes
        self.auto_save_timer += dt
        if self.auto_save_timer >= self.auto_save_interval:
            self.auto_save()
            self.auto_save_timer = 0
        
        return task.cont
    
    def auto_save(self):
        metadata = {
            'title': 'Auto Save',
            'description': 'Automatic periodic save'
        }
        success = self.game_world.save_to_file('autosave', self.player, metadata)
        if success:
            self.hud.show_message("Auto-saved!", duration=1.5)
```

### Example 2: Custom Save Dialog
```python
def show_save_dialog(self):
    """Show a GUI dialog for saving."""
    from direct.gui.DirectGui import DirectFrame, DirectButton, DirectEntry
    
    # Create dialog frame
    dialog = DirectFrame(
        frameSize=(-0.5, 0.5, -0.3, 0.3),
        frameColor=(0.2, 0.2, 0.2, 0.9),
        pos=(0, 0, 0)
    )
    
    # Add text entry for save name
    entry = DirectEntry(
        scale=0.05,
        pos=(-0.4, 0, 0.1),
        initialText="my_save",
        width=15
    )
    
    # Add save button
    def do_save():
        save_name = entry.get()
        metadata = {'title': save_name}
        self.game_world.save_to_file(save_name, self.player, metadata)
        dialog.destroy()
    
    save_btn = DirectButton(
        text="Save",
        scale=0.05,
        pos=(0, 0, -0.1),
        command=do_save
    )
    
    dialog.show()
```

### Example 3: Load Menu
```python
def show_load_menu(self):
    """Show a menu with all saves."""
    saves = self.game_world.list_saves()
    
    # Create menu
    y_pos = 0.5
    for save_name, metadata in saves:
        title = metadata.get('title', save_name)
        timestamp = metadata.get('timestamp', '')
        
        # Create button for each save
        btn = DirectButton(
            text=f"{title}\n{timestamp}",
            scale=0.04,
            pos=(0, 0, y_pos),
            command=lambda name=save_name: self.load_save(name)
        )
        y_pos -= 0.15
    
def load_save(self, save_name):
    success = self.game_world.load_from_file(save_name, self.player)
    if success:
        self.hud.show_message(f"Loaded: {save_name}", duration=2.0)
```
