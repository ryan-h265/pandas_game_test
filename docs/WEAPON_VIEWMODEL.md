# FPS Weapon Viewmodel System

## Overview
Added a complete first-person weapon viewmodel system to display tools like an FPS game.

## Files Created/Modified

### New File: `src/rendering/weapon_viewmodel.py`
- **WeaponViewModel class**: Manages FPS-style weapon display attached to camera
- Procedurally generated 3D models for each tool:
  - **Fist**: Simple hand with palm, fingers, and thumb
  - **Crowbar**: Metal bar with hook and handle
  - **Gun**: Pistol-style with barrel, slide, grip, trigger guard, and muzzle
  - **Terrain Tool**: Shovel/pickaxe-like tool with wooden handle and metal blade

### Features
1. **Weapon Models**: Simple but recognizable procedural geometry for each tool
2. **Animations**:
   - **Equip animation**: Weapon slides up into view when switching tools
   - **Use animations**: Tool-specific animations when used
     - Fist: Quick forward punch
     - Crowbar: Wind-up swing with rotation
     - Gun: Recoil (backward/upward movement)
     - Terrain tool: Forward digging motion
3. **Weapon Bob**: Subtle up/down movement when player walks
4. **Position/Rotation**: Each weapon has custom positioning relative to camera
5. **Toggle**: Press 'H' to hide/show weapon viewmodel

## Integration

### Modified Files

#### `src/tools/tool_manager.py`
- Added `weapon_viewmodel` parameter to `ToolManager.__init__()`
- Added `view_model_name` property to `Tool` base class
- Updated `set_active_tool()` to show weapon model when switching
- Updated `use_primary/secondary/tertiary()` to play weapon animations
- Updated `update()` to pass movement state to viewmodel for bob effect

#### `src/main.py`
- Imported `WeaponViewModel`
- Created `self.weapon_viewmodel` instance
- Passed to `ToolManager`
- Added 'H' key binding to toggle weapon viewmodel
- Added control info to help text
- Updated game loop to pass player movement state to tool manager

#### `src/player/controller.py`
- Added `is_moving()` method to check if player is moving (for weapon bob)

## Usage

### In-Game
- **Switch tools**: Press 'Q' to cycle through tools
- **Use tool**: Left-click (primary), Right-click (secondary), Middle-click (tertiary)
- **Toggle viewmodel**: Press 'H' to hide/show weapon display

### Code
```python
# Create weapon viewmodel
weapon_viewmodel = WeaponViewModel(camera)

# Show a specific weapon
weapon_viewmodel.show_weapon("gun")  # or "fist", "crowbar", "terrain"

# Play use animation
weapon_viewmodel.play_use_animation("gun")

# Update (in game loop)
weapon_viewmodel.update(dt, is_moving=True)

# Hide weapon
weapon_viewmodel.hide_weapon()
```

## Weapon Configurations

Each weapon has custom positioning (relative to camera):

```python
# Fist
position: Vec3(0.3, 0.8, -0.4)  # Right, forward, down
rotation: Vec3(0, 0, -10)       # Slight tilt

# Crowbar
position: Vec3(0.25, 1.0, -0.35)
rotation: Vec3(-45, -20, 0)     # Angled across screen

# Gun
position: Vec3(0.2, 0.9, -0.3)
rotation: Vec3(0, -5, 0)        # Slight downward angle

# Terrain Tool
position: Vec3(0.3, 0.9, -0.4)
rotation: Vec3(0, 0, -15)       # Slight tilt
```

## Animation Details

### Equip Animation (0.3s)
- Starts below screen
- Smoothly moves up into view
- Uses easeOut for natural motion

### Fist Punch (0.25s total)
- Quick forward thrust (0.1s out)
- Return to rest (0.15s back)

### Crowbar Swing (0.55s total)
- Wind-up backward (0.15s)
- Fast forward swing (0.2s)
- Return to rest (0.2s)
- Includes rotation for arc motion

### Gun Recoil (0.2s total)
- Sharp backward/upward kick (0.05s)
- Smooth return to rest (0.15s)
- Includes pitch rotation

### Terrain Tool Dig (0.25s total)
- Forward/downward motion (0.1s)
- Return to rest (0.15s)

## Future Enhancements

### Replace Procedural Models
The system is designed to easily swap procedural geometry with real 3D models:

```python
def show_weapon(self, weapon_type):
    # Instead of procedural geometry, load .gltf/.bam model
    self.current_model = loader.loadModel(f"assets/models/weapons/{weapon_type}.gltf")
    self.current_model.reparentTo(self.weapon_root)
    # Apply same positioning/animation system
```

### Additional Features
- Muzzle flash effects for gun (already in effects system)
- Weapon sway based on mouse movement
- Reload animations
- Impact sounds when hitting objects
- Particle effects for terrain tool
- Different punch animations (left/right hand)
- Sprint animation (weapon moves more)
