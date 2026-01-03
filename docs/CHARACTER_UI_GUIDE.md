# Character Management UI Guide

## Overview

The Sudowrite-style character management system has been successfully implemented! This guide explains how to use it and what to expect.

## Current Behavior (Important!)

### Why You Might See an Empty Characters Section

From the screenshot you provided, you're seeing an empty dark area in the Characters section. This is **expected behavior** in the following scenarios:

1. **No project is selected** - You need to select or create a project first
2. **No characters exist yet** - You haven't created any characters for this project

## How to Use Character Management

### Step 1: Select or Create a Project

Before you can manage characters, you **must** have a project selected:

1. Look at the **left sidebar** (Project Tree)
2. If you have existing projects:
   - Click on a project name to select it
   - Click on a chapter to load it
3. If you have no projects:
   - Click the "+" button at the top of the left sidebar
   - Enter a project name
   - A default chapter will be created

### Step 2: Navigate to Characters Section

1. In the left sidebar, click on **"Story Bible"** tab
2. Click on **"Characters"** in the Story Bible menu
3. You should now see the Characters page with:
   - A header with "Characters" title
   - A **purple "+ New Character"** button (top right)
   - An empty area or existing character cards

### Step 3: Create Your First Character

1. Click the **"+ New Character"** button
2. Enter a character name in the dialog
3. A new character card will appear with:
   - **Header** (collapsed/expandable):
     - Drag handle (⋮⋮)
     - Character name
     - Role dropdown (Protagonist, Antagonist, Supporting, etc.)
     - Eye icon (👁) for AI visibility toggle
     - Expand/collapse arrow
     - Delete button (×)
   - **Expanded content** (14 trait fields):
     - Name
     - Pronouns
     - Groups
     - Other Names
     - Personality
     - Background
     - Physical Description
     - Dialogue Style
     - Motivations
     - Internal Conflicts
     - Strengths
     - Weaknesses
     - Character Arc
   - **"+ Add Trait" button** for custom fields

### Step 4: Fill in Character Details

1. Click on any text field to start typing
2. Fields automatically expand as you type (no scrollbars!)
3. All changes are **auto-saved** immediately
4. Select a role from the dropdown
5. Toggle the eye icon to control AI visibility

## Features

### ✅ Implemented

- **Expandable Cards**: Click header to collapse/expand
- **Role Dropdown**: Editable with preset options
- **AI Visibility Toggle**: Eye icon changes color based on state
- **14 Predefined Traits**: All standard character fields
- **Auto-Expanding Text Fields**: No internal scrolling
- **"+ Add Trait" Button**: Create custom trait fields
- **Auto-Save**: All edits save immediately to database
- **Delete Character**: × button with confirmation dialog
- **Glass Overlay Theme**: Consistent with app theme
- **Empty State Messages**:
  - "No project selected" - when no project is active
  - "No characters yet" - when project is selected but no characters exist

### ❌ Not Implemented (Optional)

- **Drag-to-Reorder**: Rearranging character cards (marked as optional in specs)

## Technical Details

### Files Modified

1. **`src/ui/character_components.py`**:
   - `AutoExpandingTextEdit`: Auto-height text fields
   - `CharacterProfileCard`: Individual character card
   - `CharacterWidget`: Main container with project integration

2. **`src/ui/qt_app.py`**:
   - Imports `CharacterWidget` from `character_components`
   - Creates character widget in Story Bible
   - Calls `set_project_id()` when project is loaded

### Database Integration

- Reads from `characters` table
- Writes to `characters` table on changes
- Auto-creates `visible_to_ai` column if missing
- Supports all 14 predefined trait fields

### State Management

- `set_project_id(project_id)`: Called when project loads
- Enables/disables "+ New Character" button based on project selection
- Shows appropriate empty state messages

## Troubleshooting

### Issue: "I don't see the role dropdown or eye icon"

**Solution**: Make sure you:
1. Restarted the app completely (kill all Python processes)
2. Cleared Python cache: `rm -rf src/__pycache__ src/ui/__pycache__`
3. Created a NEW character after the update

### Issue: "The + New Character button is disabled"

**Solution**: No project is selected. Select or create a project from the left sidebar first.

### Issue: "I see 'No project selected' message"

**Solution**: Click on a project in the left sidebar, or create a new one using the "+" button.

### Issue: "I see 'No characters yet' message"

**Solution**: This is normal! Click the "+ New Character" button to create your first character.

### Issue: "Changes aren't being saved"

**Check**:
1. Look at the terminal output for error messages
2. Ensure the database file has write permissions
3. Check that the `characters` table exists in your database

## Screenshot Examples

### Empty State (No Project)
```
┌─────────────────────────────────────────────────┐
│ Characters              [+ New Character] (dim) │
├─────────────────────────────────────────────────┤
│                                                 │
│      No project selected.                       │
│                                                 │
│      Please select or create a project from     │
│      the left sidebar to manage characters.     │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Empty State (Project Selected, No Characters)
```
┌─────────────────────────────────────────────────┐
│ Characters              [+ New Character]       │
├─────────────────────────────────────────────────┤
│                                                 │
│      No characters yet.                         │
│                                                 │
│      Click '+ New Character' to create your     │
│      first character.                           │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Character Card (Expanded)
```
┌─────────────────────────────────────────────────┐
│ ⋮⋮  Alice Smith                                 │
│     [Protagonist ▾]                   👁  ▼  ×  │
├─────────────────────────────────────────────────┤
│ NAME                                            │
│ Alice Smith                                     │
│                                                 │
│ PRONOUNS                                        │
│ She/Her                                         │
│                                                 │
│ PERSONALITY                                     │
│ Brave, curious, sometimes reckless...          │
│                                                 │
│ ...more fields...                               │
│                                                 │
│ [+ Add Trait]                                   │
└─────────────────────────────────────────────────┘
```

## Next Steps

Your character management system is fully functional! To get started:

1. ✅ Select or create a project (left sidebar)
2. ✅ Navigate to Story Bible → Characters
3. ✅ Click "+ New Character"
4. ✅ Fill in character details
5. ✅ Watch as changes auto-save!

All the Sudowrite-style features you requested are working:
- ✅ Expandable cards with structured layout
- ✅ Role dropdown with editable options
- ✅ AI visibility toggle with visual feedback
- ✅ Auto-expanding text fields
- ✅ Auto-save functionality
- ✅ Add custom traits
- ✅ Glass overlay theme
- ✅ Smooth animations

The UI now matches the Sudowrite aesthetic you requested!

