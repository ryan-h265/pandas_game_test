# 3D Model Integration - Japanese Stone Lantern

## Summary

Added support for loading glTF/GLB 3D models in the game, starting with a Japanese stone lantern prop that can be placed with the building tool. The lantern features:
- Full PBR rendering with textures (baseColor, normal, metallic/roughness, emissive)
- Physics body for collision
- Integrated point light that emits warm glow
- Placeable via building tool (press 3 to select lantern mode)

## Recommended Format: glTF/GLB

**glTF 2.0** (`.gltf`) or **GLB** (`.glb`) is the recommended format because:

### Advantages:
- ✅ Already supported (you have `panda3d-gltf` installed)
- ✅ Industry standard (Khronos Group)
- ✅ PBR materials support
- ✅ Skeletal animations
- ✅ Excellent tool support (Blender, Maya, 3DS Max)
- ✅ Active development and wide adoption

### Format Comparison:

| Format | Support | Notes |
|--------|---------|-------|
| **glTF/GLB** | ✅ **Excellent** | Modern standard, already installed |
| **FBX** | ❌ Not supported | Requires conversion to Panda3D formats |
| **USDZ** | ❌ Not supported | Apple ecosystem only |
| **EGG/BAM** | ✅ Native | Panda3D formats, but outdated tooling |

## Files Created

### 1. Model Loader Utility
**File:** `src/rendering/model_loader.py`

Provides a reusable model loading system:
```python
from rendering.model_loader import get_model_loader

loader = get_model_loader()
model = loader.load_gltf("assets/models/props/my_model.gltf")
```

Features:
- glTF/GLB loading via `panda3d-gltf`
- Model caching for performance
- Error handling and fallback support
- Works with any glTF 2.0 model

### 2. Props Module
**Files:**
- `src/testgame/props/__init__.py`
- `src/testgame/props/base_prop.py`
- `src/testgame/props/lantern_prop.py`
- `src/testgame/props/japanese_bar_prop.py`

**BaseProp class** provides common functionality for all props:
- glTF model loading with fallback geometry
- Physics body creation (static or dynamic)
- Consistent API for all prop types

**LanternProp class** that:
- Loads the Japanese stone lantern model from `assets/models/props/japanese_stone_lantern/scene.gltf`
- Creates physics body (static or dynamic)
- Adds warm point light with flickering effect
- Provides fallback geometry if model fails to load

**JapaneseBarProp class** that:
- Loads the Japanese bar model from `assets/models/props/japanese_bar/scene.gltf`
- Creates physics body for large building structure
- Provides fallback geometry if model fails to load

Example usage:
```python
from testgame.props.lantern_prop import LanternProp
from testgame.props.japanese_bar_prop import JapaneseBarProp

# Create a lantern
lantern = LanternProp(
    world=bullet_world,
    render=render,
    position=Vec3(10, 10, 0),
    point_light_manager=point_light_manager,
    static=True  # Immovable
)

# Create a Japanese bar
bar = JapaneseBarProp(
    world=bullet_world,
    render=render,
    position=Vec3(20, 20, 0),
    point_light_manager=point_light_manager,
    static=True  # Immovable
)
```

### 3. Updated Files

#### `src/testgame/engine/world.py`
- Added `self.props = []` list to track props separately from buildings
- Added `add_prop(prop)` method

#### `src/testgame/tools/placement.py` (formerly building.py)
- Updated to support both buildings and props
- Added `type` field to placement types ("building" or "prop")
- Placement type 3 is now the Japanese Stone Lantern
- Placement type 4 is now the Japanese Bar
- Ghost preview works for both buildings and props
- Handles placement differently based on type

#### `src/testgame/tools/tool_manager.py`
- Added `point_light_manager` parameter
- Passes point light manager to placement tool

#### `src/testgame/game.py` (main game class)
- Passes `point_light_manager` to `ToolManager`

## How to Use

### In-Game Controls

1. **Press Q** to cycle to Building tool
2. **Press 3** to select Japanese Stone Lantern
3. **Move mouse** to position the ghost preview
4. **Left-click** to place the lantern
5. The lantern will emit a warm orange glow automatically

### Placement Tool Controls:
- **Left Click**: Place object at ghost position
- **Right Click**: (Not used for props)
- **Middle Click**: Toggle grid snapping
- **1**: Simple Building
- **2**: Japanese Building
- **3**: Japanese Stone Lantern ⬅️ **NEW!**
- **4**: Japanese Bar ⬅️ **NEW!**

## Model Files Structure

```
assets/models/props/japanese_stone_lantern/
├── scene.gltf                    # Main glTF file
├── scene.bin                     # Binary data
├── license.txt                   # License info
└── textures/
    ├── stone_baseColor.png       # Stone base color
    ├── stone_normal.png          # Stone normal map
    ├── stone_metallicRoughness.png
    ├── wood_baseColor.png        # Wood base color
    ├── wood_normal.png           # Wood normal map
    ├── wood_metallicRoughness.png
    ├── wood_lantern_baseColor.png
    ├── wood_lantern_normal.png
    ├── wood_lantern_metallicRoughness.png
    ├── paper_baseColor.png       # Paper section
    ├── paper_normal.png          # Paper normal map
    ├── paper_emissive.png        # Emissive glow ✨
    └── paper_metallicRoughness.png
```

The model uses full PBR workflow with:
- **Base Color**: Diffuse color
- **Normal Maps**: Surface detail
- **Metallic/Roughness**: Material properties
- **Emissive**: Self-illumination (paper glows)

## Lighting Configuration

Lanterns emit a warm point light:
```python
# Light properties
position: Lantern center + Vec3(0, 0, 1.2)
color: (1.0, 0.75, 0.4)  # Warm orange-yellow
radius: 15.0              # Moderate ambient range
intensity: 3.5            # Gentle glow

# Flickering (candle-like effect)
enabled: True
speed: 3.0               # Gentle flicker
amount: 0.08             # Subtle variation
```

## Adding More 3D Models

To add additional glTF models:

### Option 1: Create a New Prop Class
```python
# src/props/my_prop.py
from panda3d.core import Vec3
from rendering.model_loader import get_model_loader

class MyProp:
    MODEL_PATH = "assets/models/props/my_model.gltf"

    def __init__(self, world, render, position):
        loader = get_model_loader()
        self.model = loader.load_gltf(self.MODEL_PATH)
        self.model.reparentTo(render)
        self.model.setPos(position)
```

### Option 2: Add to Placement Tool
In `src/testgame/tools/placement.py`, add to `placement_types`:
```python
5: {
    "name": "My New Prop",
    "class": MyPropClass,
    "type": "prop",
    "default_width": 1.0,
    "default_depth": 1.0,
    "default_height": 2.0,
},
```

## Testing

Created `test_lantern.py` for basic testing:
```bash
python test_lantern.py
```

This creates a simple scene with a lantern to verify:
- Model loads without errors
- Physics body is created
- Point light is added
- Textures are applied

## Future Enhancements

Possible improvements:
1. **Replace procedural models** with glTF models:
   - Character model (currently procedural boxes)
   - Weapon viewmodels (currently procedural geometry)

2. **Add more props**:
   - Torches
   - Furniture
   - Trees/vegetation
   - Environmental objects

3. **Animation support**:
   - Animated characters
   - Moving mechanical props
   - Particle effects

4. **LOD (Level of Detail)**:
   - Multiple model versions for different distances
   - Automatic switching based on camera distance

5. **Model variants**:
   - Different colored lanterns
   - Various sizes
   - Damaged/broken versions

## Architecture Notes

The system is designed with flexibility in mind:

### Procedural vs. Model-Based
- **Procedural rendering** (character, weapons, buildings) remains **unchanged**
- **glTF models** work **alongside** procedural geometry
- Easy to swap individual components

### Separation of Concerns
- **Buildings**: Multi-piece structures with destruction physics
- **Props**: Single-object decorations with optional lights/physics
- Both can be placed with the same building tool

### Performance Considerations
- Models are cached after first load
- Physics bodies are optimized (simple box shapes)
- Point lights use smart culling (closest 32 lights visible)

## Troubleshooting

### Model doesn't load?
Check console output for errors. The system will create fallback geometry if loading fails.

### No light appearing?
Verify:
1. `point_light_manager` was passed to the prop
2. Shadows are enabled (press N)
3. You're within the light radius

### Ghost preview not showing?
Check that the building tool has all required dependencies (camera, render, bullet_world, terrain_raycaster, mouse_watcher, point_light_manager).

## Credits

Model format recommendation based on your existing `panda3d-gltf` dependency (version >= 1.3.0).
