# Japanese Stone Lantern - Quick Start Guide

## ✨ What's New?

Your game now supports **glTF 3D models**! The Japanese stone lantern has been integrated as the first example.

## 🎮 How to Place Lanterns In-Game

1. **Press `Q`** to cycle tools until you see "Building Placer"
2. **Press `3`** to select "Japanese Stone Lantern" mode
3. **Move your mouse** to position the green ghost preview
4. **Left-click** to place the lantern
5. The lantern will automatically emit a warm orange glow! 🏮

## 🔧 Technical Details

### Model Format
- **Recommended:** glTF 2.0 (`.gltf`) or GLB (`.glb`)
- **Your model:** `assets/models/props/japanese_stone_lantern/scene.gltf`
- **Library used:** `panda3d-gltf` (already installed in your pyproject.toml)

### Features Implemented
- ✅ glTF model loading with full PBR textures
- ✅ Physics collision (static)
- ✅ Point light emission (warm orange glow with flickering)
- ✅ Ghost preview in building tool
- ✅ Placement validation
- ✅ Grid snapping support

### Files Modified/Created

**New Files:**
- `src/rendering/model_loader.py` - Reusable glTF loader
- `src/props/lantern_prop.py` - Lantern prop class
- `src/props/__init__.py` - Props module init
- `docs/3D_MODEL_INTEGRATION.md` - Full documentation
- `test_lantern.py` - Test script

**Modified Files:**
- `src/engine/world.py` - Added props tracking
- `src/tools/building.py` - Added prop support
- `src/tools/tool_manager.py` - Added point_light_manager parameter
- `src/main.py` - Initialization order fix

## 🎨 Model Details

Your Japanese stone lantern includes:
- **PBR Materials:** Base color, normal maps, metallic/roughness
- **Emissive glow:** Paper section glows (uses `paper_emissive.png`)
- **Multiple materials:** Stone, wood, and paper sections
- **Textures:** 14 total texture files in the model

### Light Configuration
```
Color: Warm orange-yellow (1.0, 0.75, 0.4)
Radius: 15 units
Intensity: 3.5
Flicker: Gentle candle-like effect
```

## 🐛 Troubleshooting

### "Cannot place - overlapping with existing object!"
- Move the ghost preview to a clear area
- Check if it's overlapping with buildings or terrain

### Model not loading?
- Check console output for errors
- Verify the model file exists at: `assets/models/props/japanese_stone_lantern/scene.gltf`
- If it fails, a fallback gray box will appear

### No light appearing?
- Press `N` to ensure shadows/lighting are enabled
- Get close to the lantern (within 15 units)
- Check that you have fewer than 32 lights total (max limit)

## 🚀 Next Steps

### Add More Props
Copy the `LanternProp` pattern:
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

### Replace Existing Models
To replace procedural models (character, weapons) with glTF:
1. Export/download glTF models
2. Place in `assets/models/characters/` or `assets/models/weapons/`
3. Use `ModelLoader` to load them
4. Replace procedural geometry creation with model loading

## 📝 Controls Reference

### Building Tool (Lantern Mode)
- **Left Click:** Place lantern
- **Right Click:** (Not used for props)
- **Middle Click:** Toggle grid snapping
- **Mouse Move:** Position ghost preview
- **Q:** Cycle tools
- **1/2/3/4:** Switch building/prop types

### Number Keys
1. Simple Building (procedural)
2. Japanese Building (procedural)
3. **Japanese Stone Lantern (glTF model)** ⬅️ NEW!
4. TODO (placeholder)

## 📖 Full Documentation

See `docs/3D_MODEL_INTEGRATION.md` for:
- Complete architecture details
- Adding more models
- Format comparison
- Performance considerations
- Future enhancement ideas

## ✅ What Works

- ✅ glTF loading with `panda3d-gltf`
- ✅ PBR textures (base color, normal, metallic/roughness, emissive)
- ✅ Physics bodies
- ✅ Point lights with flickering
- ✅ Ghost preview system
- ✅ Placement validation
- ✅ Mix of procedural and model-based rendering

## 🎯 Current State

Your game now has a **hybrid rendering system**:
- **Procedural:** Characters, weapons, buildings (unchanged)
- **Model-based:** Japanese stone lantern (new!)
- **Both work together** seamlessly

This gives you the flexibility to use the best approach for each asset type!

---

Enjoy your new glTF-powered lanterns! 🏮✨
