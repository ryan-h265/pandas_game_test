# Skybox Improvements

## Overview
Replaced vertex-color sphere skybox with a modern **shader-driven hemisphere approach** featuring dynamic day/night cycles, procedural sky gradients, and sun/moon rendering.

## Architecture

### Components
1. **Sky Dome** - Inverted hemisphere (1800 unit radius, 32x16 segments)
   - Shader-driven procedural rendering
   - No vertex colors = cleaner geometry
   - Per-frame time-based updates for day/night cycle

2. **Sky Shader** (`sky.vert` + `sky.frag`)
   - Complex gradient computation (zenith → horizon)
   - Dynamic sun/moon positioning based on time
   - Sunrise/sunset color transitions
   - Sun disk + glow effects

3. **Mountains** - 3 layered silhouette rings at varying distances
   - Procedural noise-based heights
   - Semi-transparent for atmospheric perspective

4. **Clouds** - 3 cloud layers with soft geometry
   - Overlapping circular puffs for natural shape
   - Drift animation with per-cloud speed variation
   - Optional cloud shader for realistic lighting

5. **Sun** - Deprecated geometry-based sun (now in shader)
   - Kept for optional visual fallback

## Shader Uniforms

### Required (set in Python)
- `u_time` - Elapsed time (seconds), updated each frame
- `u_cycleSpeed` - Day/night cycle speed (default: 0.5)
- `sunBaseColor` - Sun color during day (default: `vec3(1.0, 0.9, 0.7)`)
- `moonBaseColor` - Moon color at night (default: `vec3(0.8, 0.85, 1.0)`)

## Key Changes

### Removed
- ✗ `_create_gentle_mountain()` - Unused
- ✗ `_create_cloud_ring()` - Replaced by fluffy cloud geometry
- ✗ `_create_natural_cloud_geometry()` - Replaced by soft cloud geometry
- ✗ `CardMaker` import - Only used by removed function
- ✗ Old sphere geometry code

### Added
- ✓ `self.sky_dome` - Instance variable for per-frame shader updates
- ✓ `_create_sky_hemisphere()` - Clean hemisphere geometry (V3N3 format)
- ✓ Shader uniform updates in `update()` method
- ✓ Complex sky shader with day/night cycle

## Performance
- **Geometry**: ~550 triangles (hemisphere) + clouds + mountains
- **Rendering**: Background bin, no depth write/test (efficient)
- **Shaders**: 1 sky shader + optional cloud shader per cloud layer
- **CPU**: O(1) per frame (only shader inputs updated)

## Usage

```python
skybox = MountainSkybox(render, camera, base)
skybox.create_skybox()

# In game loop:
skybox.update(camera_pos, dt)
```

## Future Enhancements
- Add stars/constellations at night
- Rayleigh scattering for realistic atmospheric perspective
- Configurable day/night cycle speed via settings
- Weather system (clouds, fog, rain)
- Sun/moon positioning based on latitude/longitude

## References
- `src/testgame/rendering/skybox.py` - Main implementation
- `assets/shaders/sky.vert` + `sky.frag` - Shader code
