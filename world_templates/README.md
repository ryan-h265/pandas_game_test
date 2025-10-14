# World Templates

This directory contains world templates/presets that can be loaded to start with pre-configured worlds.

## Default Templates

### Flat World
- Empty flat terrain at height 0
- No buildings or structures
- Perfect for building from scratch

### Creative World
- Flat terrain with example buildings
- Physics objects for testing
- Good for experimentation

### Survival World
- Natural terrain with hills and valleys
- Scattered buildings
- Starting resources

## Creating Custom Templates

You can create custom templates by:
1. Building a world exactly how you want it
2. Saving it normally (F6)
3. Copying the save file to this directory
4. Renaming it descriptively

Or programmatically:
```python
from engine.world_serializer import WorldTemplateManager

template_mgr = WorldTemplateManager()
template_mgr.create_template(
    'my_template',
    'My custom world template',
    build_function
)
```
