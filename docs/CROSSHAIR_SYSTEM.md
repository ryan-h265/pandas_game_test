# Tool-Specific Crosshair System

## Overview
Each tool now has its own unique crosshair design that matches its purpose and feel. Crosshairs automatically change when you switch tools and can be toggled on/off with the `J` key.

## Crosshair Designs

### 🤜 Fist - Circle Crosshair
**Design:** Circular with hollow center and small dot
- **Color:** White (RGB: 1, 1, 1, 0.8 alpha)
- **Purpose:** Close-range melee combat
- **Visual:** Three concentric circles - outer ring, hollow middle, center dot
- **Feel:** Friendly, non-threatening, suitable for basic interaction

### 🌍 Terrain Tool - Square Brackets
**Design:** Four corner brackets forming a square
- **Color:** Green tint (RGB: 0.5, 1, 0.5, 0.7 alpha)
- **Purpose:** Terrain editing and building
- **Visual:** L-shaped brackets at each corner with center dot
- **Feel:** Builder/architect mode, suggests area of effect

### 🔨 Crowbar - Thick Cross
**Design:** Bold cross with thick arms
- **Color:** Golden/Orange (RGB: 1, 0.8, 0.3, 0.8 alpha)
- **Purpose:** Heavy melee weapon for destruction
- **Visual:** Wide horizontal and vertical bars with darkened center
- **Feel:** Powerful, destructive, impact-focused

### 🔫 Gun - Precise Cross
**Design:** Thin cross with gap for precision
- **Color:** Red (RGB: 1, 0.2, 0.2, 0.9 alpha)
- **Purpose:** Accurate ranged shooting
- **Visual:** Four thin lines with gap in center, tiny center dot
- **Feel:** Tactical, precise, sniper-like

## Implementation Details

### File Structure
```
src/ui/crosshair.py - CrosshairManager class
```

### CrosshairManager Class

#### Initialization
```python
crosshair_manager = CrosshairManager(base)
```
- Takes ShowBase instance for access to `aspect2d` (2D overlay)
- Creates crosshairs dynamically using DirectFrame widgets

#### Methods

**`show_crosshair(tool_type)`**
- Displays crosshair for specified tool
- Parameters: `"fist"`, `"terrain"`, `"crowbar"`, or `"gun"`
- Automatically removes previous crosshair

**`hide_crosshair()`**
- Hides current crosshair
- Cleans up all GUI elements

**`set_color(color)`**
- Change color of current crosshair
- Parameter: Vec4(R, G, B, A)

**`set_scale(scale)`**
- Scale current crosshair
- Parameter: float multiplier

**`cleanup()`**
- Full cleanup of resources

### Integration Points

#### Main Game (`src/main.py`)

1. **Initialization:**
   ```python
   self.crosshair_manager = CrosshairManager(self)
   self.crosshair_manager.show_crosshair("fist")  # Show default
   ```

2. **Tool Change Callback:**
   ```python
   def on_tool_change(self, message):
       active_tool = self.tool_manager.get_active_tool()
       if active_tool:
           self.crosshair_manager.show_crosshair(active_tool.view_model_name)
   ```

3. **Toggle Control:**
   - Press `J` to hide/show crosshair
   - State persists until toggled again

## Configuration

### Crosshair Properties (in `CrosshairManager.__init__`)

Each tool's crosshair is configured with:
```python
{
    "type": "circle"|"square"|"cross_thick"|"cross_precise",
    "color": Vec4(R, G, B, A),
    "size": float  # Base size in screen units
}
```

### Customization Examples

**Make gun crosshair green (friendly fire mode):**
```python
self.crosshair_manager.show_crosshair("gun")
self.crosshair_manager.set_color(Vec4(0, 1, 0, 0.9))
```

**Enlarge terrain crosshair:**
```python
self.crosshair_manager.show_crosshair("terrain")
self.crosshair_manager.set_scale(1.5)  # 50% larger
```

**Change fist to red for combat mode:**
```python
config = self.crosshair_manager.crosshair_configs["fist"]
config["color"] = Vec4(1, 0, 0, 0.8)
self.crosshair_manager.show_crosshair("fist")
```

## Visual Design Philosophy

### Color Coding
- **White** (Fist): Neutral, non-threatening
- **Green** (Terrain): Creative, building mode
- **Orange/Gold** (Crowbar): Warning, destructive
- **Red** (Gun): Danger, combat mode

### Shape Language
- **Circle** (Fist): Soft, rounded, friendly
- **Square** (Terrain): Structured, architectural
- **Thick Cross** (Crowbar): Bold, powerful
- **Thin Cross** (Gun): Precise, focused

### Size Philosophy
- **Fist:** Medium (0.03) - comfortable close range
- **Terrain:** Large (0.04) - shows area of effect
- **Crowbar:** Medium-large (0.035) - impact zone
- **Gun:** Small (0.025) - precision targeting

## Controls Reference

| Key | Action |
|-----|--------|
| **Q** | Cycle tools (crosshair auto-updates) |
| **J** | Toggle crosshair on/off |

## Advanced Features

### Dynamic Crosshair Changes
The system supports runtime changes based on game state:

```python
# Example: Expand crosshair when holding breath for precision
if player.is_holding_breath:
    crosshair_manager.set_scale(0.5)  # Smaller = more precise
else:
    crosshair_manager.set_scale(1.0)  # Normal size

# Example: Change color based on target
if target_is_friendly:
    crosshair_manager.set_color(Vec4(0, 1, 0, 0.9))  # Green
elif target_is_enemy:
    crosshair_manager.set_color(Vec4(1, 0, 0, 0.9))  # Red
```

### Performance
- Crosshairs use DirectFrame GUI elements (very lightweight)
- No texture files needed (procedurally generated)
- Minimal memory footprint (~10 GUI nodes total)
- Zero performance impact on gameplay

## Future Enhancements

Potential additions:
1. **Dynamic spread indication** - Crosshair expands when moving
2. **Hit markers** - Visual feedback when hitting targets
3. **Damage indicators** - Show health of aimed target
4. **Custom crosshair editor** - Let players design their own
5. **Animated crosshairs** - Pulse, rotate, or react to events
6. **Texture-based crosshairs** - Load custom images
7. **Multiple reticle styles** - Toggle between designs per tool

## Technical Details

### Coordinate System
- Uses Panda3D's `aspect2d` node (2D screen overlay)
- Origin (0, 0) is screen center
- Coordinates normalized to aspect ratio
- Positive X = right, Positive Y = up

### Transparency
All crosshairs use `TransparencyAttrib.MAlpha` for proper alpha blending with game world.

### Z-ordering
Crosshairs render on top of 3D scene but behind HUD text.

### Resolution Independence
Sizes are specified in normalized units, so crosshairs scale properly at any resolution.
