# Panda3D Terrain Builder - AI Coding Instructions

## Project Overview
A 3D sandbox game with destructible terrain, physics-based building destruction, and advanced shadow rendering. Built with Panda3D engine and Bullet physics, managed via Hatch build system.

## Architecture

### Core Systems (6 major subsystems)
1. **World/Terrain** (`engine/`): Chunk-based terrain with configurable resolution. Terrain uses numpy heightmaps + Perlin noise. Chunks are 32x32 world units with TERRAIN_RESOLUTION vertices per edge (default: 32x32 = 2,048 triangles/chunk)
2. **Physics** (Bullet): Managed through `ShowBase.world`. Player uses `BulletCharacterControllerNode`, destructible objects use `BulletRigidBodyNode`. Physics runs at 60Hz (`PHYSICS_FPS`)
3. **Rendering** (`rendering/`): Cascaded shadow maps (CSM), SSAO, bilateral denoising, post-processing pipeline. Shaders in `assets/shaders/`
4. **Player/Camera** (`player/`): Character controller with capsule physics, separate camera controller for mouse look
5. **Tool System** (`tools/`): Enum-based tool switching (FIST, TERRAIN, CROWBAR, GUN). Each tool implements `on_primary_use()`, `on_secondary_use()`, `on_tertiary_use()`
6. **Structures** (`structures/`): Destructible buildings with `Fragment` debris system. Buildings generate small physics fragments on destruction with 10s lifetime

### Key Data Flows
- **Terrain Editing**: `TerrainRaycaster` → `TerrainEditor` → modifies chunk heightmap → triggers `_update_mesh()` + `_update_collision()`
- **Building Destruction**: `BuildingRaycaster` → finds hit `BuildingPiece` → calls `destroy()` → spawns `Fragment` objects → physics simulation
- **Shadow Rendering**: Per-frame `ShadowManager.update()` repositions shadow cameras around player → 1-3 cascades render to depth buffers → terrain shader samples with PCF

## Critical Settings (`config/settings.py`)

```python
CHUNK_SIZE = 32              # World units per chunk (don't change)
TERRAIN_RESOLUTION = 32      # Vertices per chunk edge (↓=better FPS, ↑=detail)
FLAT_WORLD = True            # True for flat terrain at height 0
MODIFIABLE_TERRAIN = True    # False disables editing (uses minimal 2-tri geometry)
RENDER_DISTANCE = 8          # Chunks to load in each direction
```

**Performance**: Shadows OFF by default (see line 70-76 in `main.py`). Press `N` to toggle. See `PERFORMANCE_GUIDE.md` for optimization details.

## Development Workflow

### Run Game
```bash
hatch run python -m src.main  # Note: NOT 'hatch run run' (script not defined)
# Or directly:
python -m src.main
```

### Code Quality
```bash
hatch run format  # Black formatter
hatch run lint    # Flake8
hatch run test    # Pytest (if tests exist)
```

### Dependencies
Add to `pyproject.toml` under `[project.dependencies]`. Critical deps: `panda3d>=1.10.14`, `panda3d-gltf>=1.3.0`, `numpy`, `noise`, `Pillow`

## Code Conventions

### Style
- **Prefer early returns** over nested conditionals
- **Short, testable functions**: Each logical unit in own method
- **Module organization**: One logical component per file
- **Docstrings**: Google style with Args/Returns sections (see examples throughout)

### Common Patterns
```python
# Physics setup pattern (see player/controller.py, structures/building.py)
shape = BulletCapsuleShape(radius, height, ZUp)
node = BulletCharacterControllerNode(shape, step_height, "Name")
node_path = render.attachNewNode(node)
bullet_world.attachCharacter(node)  # or .attachRigidBody()

# Terrain modification (interaction/terrain_editor.py)
chunk = terrain.get_chunk_at_world(x, z)
chunk.modify_heights(brush_fn)  # Updates heightmap
chunk._update_mesh()            # Rebuilds Geom
chunk._update_collision()       # Rebuilds BulletTriangleMesh

# Shader inputs (rendering/shadow_manager.py)
render.setShaderInput("shadow_map", depth_texture)
render.setShaderInput("shadow_mvp", camera_transform_matrix)
```

### Shadow System Integration
When modifying rendering code:
1. Shadow cascades are **disabled by default** (performance). User enables with `N` key
2. Terrain shader (`terrain.frag`) expects `shadow_map` texture array + `shadow_mvp` matrices
3. PCF samples use Poisson disk pattern (16 samples) + per-pixel rotation
4. Adjust `shadow_config.py` for quality presets (low/medium/high/ultra)

## File Reference
- **Entry Point**: `src/main.py` → `Game(ShowBase)` → `app.run()`
- **Config**: `config/settings.py` (game constants), `config/shadow_config.py` (rendering)
- **Terrain Core**: `engine/terrain.py` → `Terrain` + `TerrainChunk` classes
- **Physics Buildings**: `structures/building.py` → `SimpleBuilding` + `Fragment`
- **Shaders**: `assets/shaders/*.{vert,frag}` (GLSL)
- **Docs**: `SHADOW_SYSTEM.md`, `IMPLEMENTATION_SUMMARY.md`, `PERFORMANCE_GUIDE.md`

## Common Tasks

### Add New Tool
1. Create class inheriting `Tool` in `tools/tool_manager.py`
2. Implement `on_primary_use()`, `on_secondary_use()`, `on_tertiary_use()`
3. Add to `ToolType` enum
4. Register in `ToolManager.__init__()`

### Optimize Performance
1. Reduce `TERRAIN_RESOLUTION` (8-16 for low-end)
2. Toggle shadows off (`N` key) or reduce cascades (`shadow_config.py`)
3. Decrease `RENDER_DISTANCE` in settings
4. Set `MODIFIABLE_TERRAIN = False` with `FLAT_WORLD = True` for 2-triangle chunks

### Add Post-Processing Effect
1. Create shader pair in `assets/shaders/` (`.vert` + `.frag`)
2. Add buffer/texture in `PostProcessManager` (`rendering/post_process.py`)
3. Call `self.base.makeFullscreenQuad()` or equivalent for screen-space passes
4. Set shader inputs via `quad.setShader()` + `setShaderInput()`

## GPU Requirements
- OpenGL 3.3+ (shaders use GLSL 330)
- Hardware acceleration must be enabled (`load-display pandagl` in settings.py)
- 4GB+ RAM for chunk loading + physics simulation
