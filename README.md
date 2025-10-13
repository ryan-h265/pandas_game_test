# Panda3D Terrain Builder

A 3D sandbox game featuring fully destructible terrain, dynamic building construction, and physics-based interactions built with Panda3D and Bullet physics.

## Features

- **Destructible Terrain**: Dig, excavate, and sculpt hills and landscapes in real-time
- **Physics Simulation**: Realistic destruction with falling debris and collapsing structures
- **Building System**: Construct and destroy buildings with dynamic physics
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

## Shadow System

The game features an advanced shadow and lighting system with:
- **3-cascade shadow maps** for high quality at all distances
- **PCF with Poisson disk sampling** for soft, realistic shadows
- **Bilateral denoising** to reduce artifacts
- **SSAO support** for ambient occlusion

See [SHADOW_SYSTEM.md](SHADOW_SYSTEM.md) for detailed documentation.

**Shadow Controls:**
- Z/X - Adjust shadow softness
- C - Toggle post-processing

## TODO

Add building placement system

Create NPC system with basic AI

Implement time-of-day system with dynamic lighting
