# Shadow Performance Optimization Guide

## Problem Diagnosed
Shadows were causing low FPS (~6 FPS) due to:
1. High shadow map resolution (512x512 per cascade)
2. Multiple shadow cascades (2 cascades = 2 render passes)
3. PCF (Percentage Closer Filtering) with 4 samples per pixel
4. Shadow camera updates every frame
5. Post-processing overhead (SSAO + denoising)

## Optimizations Applied

### 1. Shadows Disabled by Default
- **Change**: Shadows now start DISABLED (line 70-76 in [src/testgame/game.py](src/testgame/game.py))
- **Impact**: Massive FPS boost (should be 60+ FPS without shadows)
- **Toggle**: Press `N` to toggle shadows on/off during gameplay

### 2. Reduced Shadow Map Resolution
- **Before**: 512x512 per cascade
- **After**: 256x256 (line 31 in [src/testgame/rendering/shadow_manager.py](src/testgame/rendering/shadow_manager.py))
- **Impact**: 4x fewer pixels to render = 4x faster shadow map generation
- **Trade-off**: Slightly blockier shadow edges

### 3. Single Shadow Cascade
- **Before**: 2 cascades (2 render passes)
- **After**: 1 cascade (line 32 in [src/testgame/rendering/shadow_manager.py](src/testgame/rendering/shadow_manager.py))
- **Impact**: 50% reduction in shadow rendering cost
- **Trade-off**: Shadows only visible in ~40m radius

### 4. Minimal PCF Filtering
- **Before**: 4 samples per pixel (2x2 grid)
- **After**: 2 samples per pixel (line 43-54 in [assets/shaders/terrain.frag](assets/shaders/terrain.frag))
- **Impact**: 50% fewer texture lookups per pixel
- **Trade-off**: Slightly harder shadow edges

### 5. Reduced Shadow Softness
- **Before**: 1.0 softness
- **After**: 0.5 softness (line 34 in [src/testgame/rendering/shadow_manager.py](src/testgame/rendering/shadow_manager.py))
- **Impact**: Smaller PCF kernel = better cache coherency
- **Trade-off**: Harder shadows

## Performance Monitoring

### New FPS Counter
- **Location**: Top-left corner of screen
- **Display**: Updates every 0.5 seconds
- **Format**: "FPS: XX"

## Controls for Performance Testing

| Key | Action | Purpose |
|-----|--------|---------|
| `N` | Toggle shadows on/off | Test FPS with/without shadows |
| `Z` | Decrease shadow softness | Make shadows harder (faster) |
| `X` | Increase shadow softness | Make shadows softer (slower) |
| `C` | Toggle post-processing | Disable SSAO/denoising for more FPS |

## Expected Performance

### Without Shadows (Press `N` to disable)
- **Target**: 60+ FPS
- **What you get**: Flat lighting, no shadows, maximum performance

### With Shadows (Press `N` to enable)
- **Target**: 30-45 FPS (depending on GPU)
- **What you get**: Basic shadows with minimal quality loss

## Further Optimizations (If Still Slow)

If you're still getting low FPS even WITHOUT shadows, try:

1. **Reduce terrain resolution** in [src/testgame/config/settings.py](src/testgame/config/settings.py)
2. **Disable post-processing** (press `C`)
3. **Reduce view distance** (modify chunk loading in [src/testgame/engine/world.py](src/testgame/engine/world.py))
4. **Disable chunk debug colors** (press `V` if enabled)
5. **Disable wireframe** (press `B` if enabled)

## Technical Details

### Why Shadows Are Expensive

1. **Shadow Map Generation**: Each cascade requires rendering the entire scene from the light's perspective
2. **PCF Filtering**: Multiple texture lookups per pixel for soft shadows
3. **Bandwidth**: Large shadow maps consume GPU memory bandwidth
4. **Shader Complexity**: Shadow calculations in fragment shader run for every pixel

### Optimization Trade-offs

| Optimization | FPS Gain | Quality Loss |
|--------------|----------|--------------|
| Disable shadows | 5-10x | All shadows gone |
| 256x256 vs 512x512 | ~2x | Slightly blockier |
| 1 cascade vs 2 | ~1.5x | Shadows fade sooner |
| 2 samples vs 4 | ~1.3x | Slightly harder edges |

## Recommended Settings by Hardware

### Low-End GPU (Integrated Graphics)
```
Shadows: OFF (press N)
Post-processing: OFF (press C)
Expected FPS: 60+
```

### Mid-Range GPU (GTX 1060 / RX 580)
```
Shadows: ON (current optimized settings)
Post-processing: OFF (press C)
Expected FPS: 40-60
```

### High-End GPU (RTX 3060+ / RX 6700+)
```
Shadows: ON
Post-processing: ON
Shadow softness: Can increase with Z/X keys
Expected FPS: 60+
```

## Testing Instructions

1. **Start the game** - Shadows are now OFF by default
2. **Check FPS** - Look at top-left corner (should be 60+)
3. **Press `N`** - Enable shadows
4. **Check FPS again** - Should drop but still be playable (30-45 FPS)
5. **Press `N`** - Disable shadows if FPS is too low

## Reverting Changes

To re-enable shadows by default, edit [src/testgame/game.py](src/testgame/game.py) line 69-76:
```python
# Change from:
self.shadows_enabled = False
self.shadow_manager = None

# To:
light_dir = Vec3(1, 1, -1)
self.shadow_manager = ShadowManager(self, self.render, light_dir)
self.shadow_manager.set_shader_inputs(self.render)
self.shadows_enabled = True
```
