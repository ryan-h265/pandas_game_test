# Save/Load System - Quick Reference

## Key Bindings
| Key | Action |
|-----|--------|
| **F5** | Quick save to 'quicksave' slot |
| **F9** | Quick load from 'quicksave' slot |
| **F6** | Create timestamped save |
| **F7** | List saves and load most recent |

## Basic Usage

### Save Current World
```python
# Quick save (most common)
game.quick_save()

# Or with custom name
metadata = {'title': 'My Save', 'description': 'Before boss fight'}
game.game_world.save_to_file('boss_fight', game.player, metadata)
```

### Load Saved World
```python
# Quick load
game.quick_load()

# Or load specific save
game.game_world.load_from_file('boss_fight', game.player)
```

### List All Saves
```python
saves = game.game_world.list_saves()
for save_name, metadata in saves:
    print(f"{save_name}: {metadata.get('title', 'Untitled')}")
```

## What Gets Saved
- ✅ Terrain heightmaps (all modifications)
- ✅ Building positions, rotations, health
- ✅ Physics object velocities
- ✅ Player position and velocity
- ✅ Loaded chunk coordinates

## File Locations
- **Saves**: `saves/*.json`
- **Templates**: `world_templates/*.json`

## Common Patterns

### Auto-Save Every 5 Minutes
```python
# In Game.__init__():
self.autosave_timer = 0
self.autosave_interval = 300  # 5 minutes

# In Game.update():
self.autosave_timer += dt
if self.autosave_timer >= self.autosave_interval:
    self.quick_save()
    self.autosave_timer = 0
```

### Save Before Destructive Action
```python
def destroy_large_building(self, building):
    # Auto-save before major change
    self.game_world.save_to_file('before_destruction', self.player, {
        'title': 'Before Destruction',
        'description': f'Before destroying {building.name}'
    })
    
    # Now do the destruction
    building.destroy()
```

### Create Empty World
```python
# Start with empty world (no auto-generation)
world = World(render, bullet_world, auto_generate=False)

# Then either load or manually populate
world.load_from_file('my_custom_world', player)
# OR
world._generate_initial_terrain()
```

## API Reference

### World Methods
```python
world.save_to_file(save_name, player, metadata=None)
world.load_from_file(save_name, player)
world.list_saves()
world.clear_world()
```

### Game Methods
```python
game.quick_save()
game.quick_load()
game.open_save_dialog()
game.open_load_dialog()
```

## Extending

### Add Custom Object Type
```python
# 1. In World.__init__():
self.custom_objects = []

# 2. In WorldSerializer, add methods:
def _serialize_custom_objects(self, objects):
    return [{'data': obj.serialize()} for obj in objects]

def _deserialize_custom_objects(self, data, world):
    for obj_data in data:
        obj = CustomObject.deserialize(obj_data['data'])
        world.custom_objects.append(obj)

# 3. Include in save/load:
# In save_world():
save_data['custom_objects'] = self._serialize_custom_objects(world.custom_objects)

# In load_world():
self._deserialize_custom_objects(save_data['custom_objects'], world)
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Save not found | Check `saves/` directory exists, use F7 to list saves |
| Load failed | Save may be corrupted, try different save |
| Missing objects | Ensure objects added to world tracking lists |
| Terrain wrong | Verify `_update_mesh()` called after loading heights |

## Full Documentation
See `docs/SAVE_LOAD_SYSTEM.md` for complete documentation with examples, best practices, and advanced usage.

## Example Code
See `examples/save_load_example.py` for working examples of all features.
