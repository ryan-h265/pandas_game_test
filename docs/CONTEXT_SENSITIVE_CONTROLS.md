# Context-Sensitive Tool Controls

## Overview
Tool controls (scroll wheel and `[` `]` keys) are now context-sensitive and only affect the currently equipped tool. Each tool has its own adjustable properties.

## Changes Made

### Base Tool Class (`src/testgame/tools/base.py`)
Added two new methods to the base `Tool` class:
- `adjust_primary_property(delta)` - Scroll wheel adjustments
- `adjust_secondary_property(delta)` - `[` `]` key adjustments

Each method returns `(property_name, new_value)` tuple or `None` if not applicable.

### Tool-Specific Properties

#### **Fist Tool**
- **Primary (Scroll)**: Damage (5-100)
  - Adjusts punch damage in increments of 5
  - Default: 25
- **Secondary ([ ])**: Range (2.0-10.0)
  - Adjusts melee reach in increments of 0.1
  - Default: 5.0

#### **Terrain Tool**
- **Primary (Scroll)**: Brush Size (1.0-10.0)
  - Adjusts terrain editing area
  - Default: 3.0
- **Secondary ([ ])**: Brush Strength (0.01-1.0)
  - Adjusts terrain modification intensity
  - Default: 0.05

#### **Crowbar Tool**
- **Primary (Scroll)**: Damage (10-150)
  - Adjusts crowbar hit damage in increments of 5
  - Default: 75
- **Secondary ([ ])**: Cooldown (0.1-2.0)
  - Adjusts time between swings in increments of 0.01
  - Lower = faster swings
  - Default: 0.5

#### **Gun Tool**
- **Primary (Scroll)**: Damage (10-200)
  - Adjusts bullet damage in increments of 5
  - Default: 100
- **Secondary ([ ])**: Fire Rate (0.1-2.0)
  - Adjusts time between shots in increments of 0.01
  - Lower = faster shooting
  - Default: 0.3

### Updated Main Controls (`src/testgame/game.py`)

#### `adjust_brush_size(direction)` → Context-sensitive primary property
- Now calls `active_tool.adjust_primary_property(direction)`
- Displays on-screen message showing tool name, property, and value
- Example: "Gun - Damage: 105"

#### `adjust_terrain_strength(delta)` → Context-sensitive secondary property
- Now calls `active_tool.adjust_secondary_property(delta)`
- Displays on-screen message for any tool
- Example: "Crowbar - Cooldown: 0.450"

## Usage

### In-Game
1. **Equip a tool** (press `Q` to cycle)
2. **Adjust properties**:
   - **Scroll wheel up/down** - Adjust primary property
   - **`[` key** - Decrease secondary property
   - **`]` key** - Increase secondary property
3. **See feedback**: On-screen message shows current value

### Examples

**Customize Fist for Different Playstyles:**
```
Equip Fist → 
  Scroll up several times → Increase damage to 50
  Press [ multiple times → Decrease range to 3.0 (close combat)
```

**Fine-tune Terrain Editing:**
```
Equip Terrain Tool →
  Scroll down → Smaller brush (2.0) for detail work
  Press [ many times → Very low strength (0.02) for gentle slopes
```

**Make Crowbar Super Fast:**
```
Equip Crowbar →
  Press [ many times → Cooldown 0.2 (swing 5x per second!)
  Scroll up → Damage 100 for maximum destruction
```

**Turn Gun into Sniper Mode:**
```
Equip Gun →
  Scroll up → Damage 150 (powerful shots)
  Press ] many times → Fire rate 0.8 (slower, more deliberate)
```

## Benefits

✅ **Context-aware**: Controls only affect current tool  
✅ **No confusion**: Can't accidentally change terrain when using gun  
✅ **Per-tool customization**: Each tool has unique adjustable properties  
✅ **Clear feedback**: On-screen messages show what's changing  
✅ **Intuitive**: Same controls, different effects per tool  
✅ **Flexible**: Tune each tool to your playstyle  

## Display Format

Messages show:
- Tool name
- Property being adjusted
- New value (formatted appropriately)

Examples:
```
Terrain Editor - Brush Size: 4.00
Gun - Damage: 120
Crowbar - Cooldown: 0.350
Fist - Range: 7.00
```

## Controls Reference

| Control | Terrain Tool | Fist | Crowbar | Gun |
|---------|-------------|------|---------|-----|
| **Scroll ↑** | Increase size | More damage | More damage | More damage |
| **Scroll ↓** | Decrease size | Less damage | Less damage | Less damage |
| **[ key** | Lower strength | Shorter range | Slower swings | Slower fire rate |
| **] key** | Higher strength | Longer range | Faster swings | Faster fire rate |

All adjustments are persistent until changed - perfect for finding your ideal tool settings!
