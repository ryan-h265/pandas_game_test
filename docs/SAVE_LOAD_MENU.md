# Save/Load Menu Integration

## Overview
Save and load functionality has been integrated into the pause menu system. Players can now save and load their game through an intuitive in-game menu interface.

## How to Access

1. **Press ESC** to open the pause menu
2. Select **"Save Game"** or **"Load Game"**
3. Choose a save slot (Quick Save or Slots 1-3)

## Save Menu Features

### Save Slots Available
- **Quick Save** - Fast access save slot (recommended for quick saves during gameplay)
- **Slot 1** - Manual save slot 1
- **Slot 2** - Manual save slot 2
- **Slot 3** - Manual save slot 3

### How to Save
1. Press **ESC** to open pause menu
2. Click **"Save Game"**
3. Click on any save slot to save your game
4. Success message will appear
5. Click **"Back"** to return to pause menu

## Load Menu Features

### Load Slots Display
Each save slot shows:
- **Saved: [Date/Time]** - When the save was created (green text)
- **Empty Slot** - No save exists in this slot (gray text)

### How to Load
1. Press **ESC** to open pause menu
2. Click **"Load Game"**
3. View available saves (shows timestamp for each)
4. Click on a save slot to load
5. Game will automatically resume after 1 second

### Load Behavior
- Loading a game will restore:
  - Terrain modifications
  - All buildings and their states
  - Physics objects
  - Player position
- The game automatically resumes after loading
- If no save exists in a slot, an error message appears

## Menu Navigation

```
Pause Menu
├── Resume          → Return to game
├── Save Game       → Open save menu
│   ├── Quick Save
│   ├── Save Slot 1
│   ├── Save Slot 2
│   ├── Save Slot 3
│   └── Back        → Return to pause menu
├── Load Game       → Open load menu
│   ├── Quick Load  → (Shows save date if exists)
│   ├── Load Slot 1 → (Shows save date if exists)
│   ├── Load Slot 2 → (Shows save date if exists)
│   ├── Load Slot 3 → (Shows save date if exists)
│   └── Back        → Return to pause menu
├── Settings        → Game settings
└── Quit to Desktop → Exit game
```

## Implementation Details

### Menu Components
- **Save Menu** (`create_save_menu()`)
  - 4 save buttons (Quick Save + 3 slots)
  - Info label for feedback
  - Back button

- **Load Menu** (`create_load_menu()`)
  - 4 load buttons (Quick Load + 3 slots)
  - Timestamp display for each slot
  - Info label for feedback
  - Back button

### Save Naming Convention
- Quick Save: `quicksave.json`
- Slot 1: `save_slot_1.json`
- Slot 2: `save_slot_2.json`
- Slot 3: `save_slot_3.json`

All saves are stored in the `saves/` directory.

## Keyboard Shortcuts (Still Available)

For advanced users, keyboard shortcuts are still functional:
- **F5** - Quick save (same as menu Quick Save)
- **F9** - Quick load (same as menu Quick Load)
- **F6** - Create timestamped save
- **F7** - List saves in console

However, the **menu is now the primary way** to save and load.

## User Experience Improvements

### Visual Feedback
- **Green text** - Successful save/load
- **Red text** - Failed save/load
- **Gray text** - Empty save slot
- **Hover effects** - Buttons highlight on mouse hover

### Save Information
- Load menu shows when each save was created
- Clear indication of empty vs. occupied slots
- Success/error messages appear immediately

### Smooth Workflow
1. Player presses ESC (muscle memory for pause)
2. Clear "Save Game" and "Load Game" buttons
3. Simple slot selection
4. Automatic game resume after loading
5. No need to remember keyboard shortcuts

## Code Structure

### New Methods in MenuSystem

**Save Menu:**
```python
create_save_menu()       # Creates save UI
show_save_menu()         # Shows save menu
hide_save_menu()         # Returns to pause menu
on_quick_save()          # Handles quick save
on_save_slot(slot_num)   # Handles slot save
update_save_slot_info()  # Updates slot info
```

**Load Menu:**
```python
create_load_menu()       # Creates load UI
show_load_menu()         # Shows load menu
hide_load_menu()         # Returns to pause menu
on_quick_load()          # Handles quick load
on_load_slot(slot_num)   # Handles slot load
update_load_slot_info()  # Updates slot info with timestamps
```

## Future Enhancements

Potential improvements for the menu system:

1. **Save Thumbnails** - Show screenshot of save
2. **Save Descriptions** - Allow custom save descriptions
3. **Delete Save** - Add delete button for each slot
4. **More Slots** - Expand to 10+ save slots with scrolling
5. **Auto-Save Indicator** - Show last auto-save time
6. **Confirmation Dialogs** - "Overwrite existing save?" prompt
7. **Save Metadata Display** - Show playtime, building count, etc.
8. **Quick Save Hotkey** - Show F5/F9 hints in menu

## Testing Checklist

✅ Save menu appears when clicking "Save Game"
✅ Load menu appears when clicking "Load Game"
✅ Quick save button saves to quicksave.json
✅ Slot buttons save to correct files
✅ Load menu shows correct timestamps
✅ Empty slots show "Empty Slot"
✅ Loading a game resumes after 1 second
✅ Error messages appear for failed loads
✅ Success messages appear for successful saves
✅ Back buttons return to pause menu
✅ All menus hide when resuming game

## Troubleshooting

**Menu doesn't appear:**
- Ensure you're pressing ESC
- Check console for errors

**Save buttons don't work:**
- Check that `saves/` directory exists
- Verify write permissions
- Check console for error messages

**Load shows all empty slots:**
- Save a game first using save menu
- Check `saves/` directory for .json files

**Game doesn't resume after loading:**
- Check console for load errors
- Verify save file is not corrupted
- Try a different save slot

## Summary

The save/load system is now fully integrated into the pause menu, providing a user-friendly interface for game state management. Players can easily save and load their progress without needing to remember keyboard shortcuts, making the game more accessible and professional.

**Key Changes:**
- Added "Save Game" and "Load Game" buttons to pause menu
- Created dedicated save and load menu screens
- 4 save slots available (Quick Save + 3 manual slots)
- Load menu shows save timestamps
- Automatic game resume after loading
- Visual feedback for all operations
- Clean, intuitive navigation
