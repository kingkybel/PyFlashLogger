# Color & Label Configurator Tool

Interactive tool for customizing logging colors, styles, and labels.

## Features

- 🎨 **Visual Level Display**: See actual colors for all log levels and special elements
- ⚡ **Streamlined Editing**: Direct command-line style input with fuzzy color matching
- 🔄 **Bash-like Interface**: Up/down arrow for command history, tab completion for colors
- 🌈 **Special Elements**: Configure colors for timestamps, brackets, processes, comments, etc.
- 🧪 **Live Testing**: See your changes in action with sample log output
- 💾 **JSON Persistence**: Save configurations and reload them later
- 📋 **Configuration Overview**: View current color and label settings

## Usage

### Command Line
```bash
# Start with default configuration
python3 color_configurator.py

# Load existing configurations
python3 color_configurator.py my_colors.json my_labels.json
```

### Interface Overview

The tool immediately displays all log levels and special elements using their **actual colors**:

```
🎨 Color & Label Configurator - Minimal Interface

Available levels:
 1. warning warning    # ← First "warning" normal, second highlight
 2. error error
 3. fatal fatal
 4. critical critical
...

Special elements:
21. Default Default    # ← Special colors work the same way
22. Bracket Bracket
...

Commands: q=quit, s=save, l=load custom, load colors COLOR|BW|PLAIN,
  or load labels EN|DE, or item number [1-26] to edit
Edit format for levels: <label> <fg> <bg> <style> <hfg> <hbg> <hstyle>
Edit format for specials: <fg> <bg> <style> <hfg> <hbg> <hstyle>
Use '_' to keep current values

Command: 4 RED _ DIM
```

**Dual-format display**: Each level/special shows the label twice:
- First label: Normal color scheme
- Second label: Highlight color scheme (separated by space)

### Commands

- **`q`** - Quit
- **`s`** - Save current configuration to JSON
- **`l`** - Load custom configuration from JSON
- **`load colors SCHEME`** - Load predefined color scheme (COLOR, BW, PLAIN)
- **`load labels LANG`** - Load predefined labels (EN, DE)
- **`NUMBER VALUES`** - Edit level/special NUMBER with VALUES (see below)

### Fuzzy Color Matching

Type partial color names - the tool will find the best match:
- `"lred"` → `LIGHTRED_EX`
- `"red"` → `RED`
- `"blu"` → `BLUE`
- `"lblk"` → `LIGHTBLACK_EX`

### Tab Completion

Press `Tab` to auto-complete color and style names. Command history accessible with ↑/↓ arrows (like bash).

### Editing Items

#### For Log Levels (1-20):
```bash
Command: 4 _ RED _ DIM _ YELLOW BRIGHT
```
**7 values**: `<label> <fg> <bg> <style> <hfg> <hbg> <hstyle>`

- `<label>` - New label (only for CUSTOM* levels, use `_` otherwise)
- `<fg>` - Normal foreground color (name, number 1-16, or `_`)
- `<bg>` - Normal background color (name, number 1-16, or `_`)
- `<style>` - Normal style (NORMAL, BRIGHT, DIM, number 1-3, or `_`)
- `<hfg>` - Highlight foreground color
- `<hbg>` - Highlight background color
- `<hstyle>` - Highlight style

#### For Special Elements (21-26):
```bash
Command: 21 YELLOW WHITE DIM RED BLACK BRIGHT
```
**6 values**: `<fg> <bg> <style> <hfg> <hbg> <hstyle>` (no label for specials)

**Use `_` to keep current values.**

### Examples
```bash
# Change WARNING to red highlight
Command: 4 _ _ _ _ RED _

# Make ERROR bright with fuzzy 'bright' style
Command: 5 _ _ BRIGHT

# Configure Timestamp special element
Command: 23 GREEN _ NORMAL

# Load German labels
Command: load labels DE

# Tab-completion example (type 'l' then Tab)
Command: 4 l↓
Command: 4 LIGHTRED_EX
```

## Configuration Files

### Colors JSON Format
```json
{
  "warning": {
    "normal": {
      "foreground": "YELLOW",
      "background": "BLUE",
      "style": "BRIGHT"
    }
  },
  "custom0": {
    "normal": {
      "foreground": "CYAN",
      "background": "",
      "style": "DIM"
    }
  }
}
```

### Labels JSON Format
```json
{
  "custom0": "DATA_PROCESSING",
  "custom1": "NETWORK_IO",
  "custom2": "VERBOSE_DEBUG"
}
```

## Example Workflow

1. **Load existing config** (optional):
   ```bash
   python3 color_configurator.py colors.json labels.json
   ```

2. **Customize colors directly**:
   ```bash
   Command: 1 CYAN BLACK DIM     # Set custom0 normal colors
   Command: 1 _ RED BRIGHT       # Set custom0 highlight to red bright
   Command: 4 _ BLUE _           # Set warning highlight background blue
   ```

3. **Configure special elements**:
   ```bash
   Command: 21 WHITE BLACK NORMAL   # Set timestamp colors
   Command: 23 GREEN _ DIM          # Set process colors
   ```

4. **Load predefined schemes**:
   ```bash
   Command: load labels DE          # Switch to German labels
   Command: load colors BW          # Switch to black/white scheme
   ```

5. **Save configuration**:
   ```bash
   Command: s
   ```

## Available Colors

### Foreground Colors
- BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE
- LIGHTBLACK_EX, LIGHTRED_EX, LIGHTGREEN_EX, LIGHTYELLOW_EX, LIGHTBLUE_EX, LIGHTMAGENTA_EX, LIGHTCYAN_EX, LIGHTWHITE_EX

### Background Colors
- Same as foreground colors
- Use "" (empty) for transparent backgrounds

### Styles
- NORMAL - Standard text
- BRIGHT - Bold/highlighted text
- DIM - Subdued/muted text

## Integration Example

```python
from dkybutils.color_scheme import ColorScheme
from dkybutils.log_levels import LogLevel
from dkybutils.flash_logger import FlashLogger

# Load your custom configuration
custom_scheme = ColorScheme(colorscheme_json="my_colors.json")
LogLevel.load_str_reprs_from_json("my_labels.json")

# Use in logging
logger = FlashLogger(console=custom_scheme)
logger.log_custom0("This will use your custom color and label!")
```

## Predefined Schemes

### Color Schemes
- **COLOR**: Full color palette (default)
- **BW**: Black and white monochrome
- **PLAIN**: Plain text, no colors

### Label Languages
- **EN**: English labels (default)
- **DE**: German labels

Load with: `load colors BW` or `load labels DE`

## Tips

- **Fuzzy Matching**: Type "red" for RED, "lblue" for LIGHTBLUE_EX
- **Tab Completion**: Press Tab for color/style name completion
- **Command History**: Use ↑/↓ arrows to recall previous commands
- **Quick Editing**: Provide only the values you want to change with `_`
- **Backup Colors**: Run `python3 color_configurator.py` to backup defaults
- **Visual Preview**: Levels display actual colors on-screen
- **Terminal Colors**: Ensure your terminal supports ANSI escape codes
- **Accessibility**: Choose high-contrast combinations for readability

## Key Benefits

- 🎨 **Visual Customization**: Make logs visually distinct for better debugging
- 🏷️ **Semantic Labels**: Use meaningful names like "NETWORK_IO" instead of "CUSTOM1"
- 💾 **Persistence**: Save and share configurations between projects
- 🔄 **Iterative Design**: Test and refine color schemes interactively
- 🌈 **Accessibility**: Choose high-contrast color combinations for readability
- ⚡ **Efficiency**: Direct editing with fuzzy matching and completion
- 🔄 **History**: Command history like modern shells
