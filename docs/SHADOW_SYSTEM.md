# Shadow System Documentation

## Overview

This implementation provides a practical shadow and lighting system for Panda3D that includes:

1. **Cascaded Shadow Maps (CSM)** - Three cascades for high-quality shadows at varying distances
2. **PCF with Poisson Disk Sampling** - Soft, realistic shadows with minimal banding
3. **Bilateral Denoising** - Reduces shadow noise while preserving edges
4. **SSAO Support** - Screen-space ambient occlusion for enhanced depth perception

## Architecture

### Components

#### 1. Shadow Manager ([rendering/shadow_manager.py](src/rendering/shadow_manager.py))

Manages the cascaded shadow map system:

- Creates 3 shadow map buffers (2048x2048 each)
- Maintains shadow cameras for each cascade
- Updates camera positions/projections based on player position
- Provides shader inputs for shadow rendering

**Key Settings:**
- `shadow_map_size`: 2048 (resolution per cascade)
- `num_cascades`: 3 (near/medium/far)
- `cascade_splits`: [20, 50, 150] (view space distances)
- `shadow_softness`: 2.0 (PCF kernel size multiplier)

#### 2. Post-Process Manager ([rendering/post_process.py](src/rendering/post_process.py))

Handles post-processing effects:

- **SSAO**: Generates hemisphere samples for ambient occlusion
- **Denoising**: Bilateral filtering for shadow smoothing

**Key Settings:**
- `ssao_radius`: 1.5 (occlusion sample radius)
- `ssao_bias`: 0.025 (depth bias to prevent self-occlusion)
- `denoise_spatial_sigma`: 2.0 (spatial blur strength)
- `denoise_depth_sigma`: 0.1 (depth edge preservation)

#### 3. Shaders ([assets/shaders/](assets/shaders/))

**Shadow Map Generation:**
- `shadow_map.vert/frag` - Renders depth from light's perspective

**Terrain Rendering with Shadows:**
- `terrain.vert` - Computes shadow coordinates for all cascades
- `terrain.frag` - PCF shadow sampling with Poisson disk

**Post-Processing:**
- `denoise.frag` - Bilateral filter for shadow denoising
- `ssao.frag` - Screen-space ambient occlusion

## How It Works

### Cascaded Shadow Maps (CSM)

Traditional shadow maps suffer from perspective aliasing - shadows near the camera are blocky while distant shadows waste resolution. CSM solves this by using multiple shadow maps at different distances:

```
Cascade 0 (0-20m):    Highest detail, covers near field
Cascade 1 (20-50m):   Medium detail, covers mid field
Cascade 2 (50-150m):  Lower detail, covers far field
```

Each cascade has its own:
- Shadow camera positioned along light direction
- 2048x2048 depth texture
- Orthographic projection sized to cover its range

### PCF with Poisson Disk Sampling

Percentage Closer Filtering (PCF) creates soft shadows by sampling the shadow map multiple times around each pixel:

1. **16 Poisson disk samples** - Distributed evenly in a disk pattern
2. **Random rotation** - Uses world position to rotate samples, reducing banding
3. **Adaptive kernel** - Larger kernels for softer shadows

This is conceptually similar to ReSTIR's spatial resampling but simpler and faster.

### Shadow Denoising

The bilateral filter smooths shadows while preserving edges:

1. **Spatial weight** - Closer samples have more influence
2. **Depth weight** - Similar depths have more influence (preserves edges)
3. **Gaussian kernel** - Configurable blur strength

This provides similar benefits to temporal denoising but works in a single frame.

### SSAO Integration

Screen-space ambient occlusion adds depth to the scene:

1. **Hemisphere sampling** - 32-64 samples around each pixel
2. **Depth comparison** - Samples occluded by geometry darken the pixel
3. **Noise texture** - Random rotation to reduce banding

## Usage

### Controls

- **Z** - Decrease shadow softness (sharper shadows)
- **X** - Increase shadow softness (softer shadows)
- **C** - Toggle post-processing effects

### Configuration

Adjust settings in the shadow manager initialization:

```python
# In main.py
light_dir = Vec3(1, 1, -1)  # Change sun angle
self.shadow_manager = ShadowManager(self.render, light_dir)

# Adjust shadow quality
self.shadow_manager.shadow_map_size = 4096  # Higher resolution
self.shadow_manager.cascade_splits = [30, 80, 200]  # Wider coverage
self.shadow_manager.shadow_softness = 3.0  # Softer shadows
```

### Performance Tuning

**For better performance:**
- Reduce `shadow_map_size` to 1024
- Use 2 cascades instead of 3
- Reduce `shadow_softness` to 1.0 (fewer samples)
- Reduce Poisson disk samples from 16 to 8 in terrain.frag

**For better quality:**
- Increase `shadow_map_size` to 4096
- Add 4th cascade for very distant shadows
- Increase `shadow_softness` to 4.0
- Increase Poisson disk samples to 32

## Comparison to ReSTIR/RTXDI

### What We Implemented

This is a **practical approximation** that captures the spirit of advanced techniques:

| Feature | Our Implementation | Full ReSTIR/RTXDI |
|---------|-------------------|-------------------|
| Shadow Quality | PCF with 16 samples | Importance-sampled with RIS |
| Temporal Stability | Bilateral denoising | Temporal reservoir reuse |
| Performance | ~5-10ms | ~2-5ms (with RT hardware) |
| Soft Shadows | Poisson disk PCF | Area light sampling |
| Hardware Req | OpenGL 3.3+ | RTX/DXR ray tracing |

### Why This Approach

1. **Works on any GPU** - No ray tracing hardware required
2. **Easier to implement** - ~500 lines vs 5000+ for full ReSTIR
3. **Good visual quality** - Soft shadows with minimal artifacts
4. **Proven technique** - Used in many AAA games
5. **Easier to debug** - Standard shadow mapping pipeline

### When to Use Full ReSTIR

Consider implementing full ReSTIR/RTXDI if:
- You have RTX GPU requirement
- You need many dynamic lights (100+)
- You need physically-based soft shadows
- You have months for implementation
- You're targeting high-end hardware

## Troubleshooting

### Shadows not appearing
- Check shader compilation: Look for "Shadow shaders loaded successfully"
- Verify shadow cameras are created: Should see 3 shadow buffers
- Check light direction isn't pointing up

### Shadow acne (artifacts on surfaces)
- Increase bias in terrain.frag (currently 0.005)
- Adjust cascade-specific bias multipliers

### Peter panning (shadows detached from objects)
- Decrease bias in terrain.frag
- Check shadow camera near/far planes

### Performance issues
- Reduce shadow_map_size
- Reduce number of cascades
- Reduce Poisson samples
- Reduce shadow_softness

### Blocky shadows
- Increase shadow_map_size
- Adjust cascade_splits for better distribution
- Increase shadow_softness

## Future Enhancements

Possible improvements:

1. **Temporal filtering** - Accumulate samples across frames
2. **Variance shadow maps** - Better soft shadow quality
3. **Contact hardening** - Shadows softer farther from caster
4. **Multiple lights** - Point/spot light shadow support
5. **Ray traced shadows** - If GPU supports it via Vulkan

## References

- [Cascaded Shadow Maps (Microsoft)](https://docs.microsoft.com/en-us/windows/win32/dxtecharts/cascaded-shadow-maps)
- [PCF and Poisson Sampling](https://developer.nvidia.com/gpugems/gpugems/part-ii-lighting-and-shadows/chapter-11-shadow-map-antialiasing)
- [ReSTIR GI Paper](https://research.nvidia.com/publication/2021-06_restir-gi-path-resampling-real-time-path-tracing)
- [RTXDI SDK](https://github.com/NVIDIAGameWorks/RTXDI)

## License

This shadow system implementation is part of the Panda3D Terrain Builder project (MIT License).
