# Panda3D Terrain Builder

A 3D sandbox game featuring fully destructible terrain, dynamic building construction, and physics-based interactions built with Panda3D and Bullet physics.

## Features

- **Destructible Terrain**: Dig, excavate, and sculpt hills and landscapes in real-time
- **Physics Simulation**: Realistic destruction with falling debris and collapsing structures
- **Building System**: Construct and destroy buildings with dynamic physics
- **Save/Load System**: Persistent world state with custom world templates
- **Character System**: Animated player characters and NPCs with model loading support
- **Dynamic Environment**: Procedurally generated terrain with chunk-based loading
- **Advanced Lighting**: Cascaded shadow maps with PCF soft shadows and denoising
- **Post-Processing**: SSAO ambient occlusion for enhanced depth perception

## Tech Stack

- **Engine**: Panda3D
- **Physics**: Bullet Physics (Panda3D-Bullet)
- **Languages**: Python
- **Build Tool**: Hatch
- **Graphics**: OpenGL

## Requirements

- Python 3.8 - 3.11
- Modern GPU with OpenGL 3.3+ support
- 4GB+ RAM

## Installation

```bash
# Install Hatch
pip install hatch

# Clone repository
git clone <repository-url>
cd pandas_game_test

# Create environment and install dependencies
hatch env create

# Run the game
hatch run run
```

## Development

```bash
# Run game
hatch run run

# Format code
hatch run format

# Lint code
hatch run lint

# Run tests
hatch run test
```

We prefer short, testable functions. Each logical component should be in its own module. We prefer early return over nested logic.

## Save/Load System

The game features a comprehensive world persistence system with an integrated menu interface:
- **In-Game Menu**: Access save/load through the pause menu (ESC)
- **Multiple Slots**: Quick Save + 3 manual save slots
- **Complete State**: Saves terrain, buildings, physics objects, and player state
- **Save Info Display**: Load menu shows when each save was created
- **World Templates**: Create and load pre-configured world setups

See [docs/SAVE_LOAD_SYSTEM.md](docs/SAVE_LOAD_SYSTEM.md) for detailed documentation.
See [docs/SAVE_LOAD_MENU.md](docs/SAVE_LOAD_MENU.md) for menu usage guide.

**How to Save/Load:**
1. Press **ESC** to open pause menu
2. Click **"Save Game"** or **"Load Game"**
3. Select a save slot (Quick Save or Slots 1-3)
4. Game auto-resumes after loading

**Keyboard Shortcuts (still available):**
- F5 - Quick save
- F9 - Quick load

## Shadow System

The game features an advanced shadow and lighting system with:
- **3-cascade shadow maps** for high quality at all distances
- **PCF with Poisson disk sampling** for soft, realistic shadows
- **Bilateral denoising** to reduce artifacts
- **SSAO support** for ambient occlusion

See [docs/SHADOW_SYSTEM.md](docs/SHADOW_SYSTEM.md) for detailed documentation.

**Shadow Controls:**
- Z/X - Adjust shadow softness
- C - Toggle post-processing

## TODO

Add building placement system

Create NPC system with basic AI

Implement time-of-day system with dynamic lighting
