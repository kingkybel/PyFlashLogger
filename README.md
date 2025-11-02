# kingkybel-pyflashlogger

Advanced console logging with color support and minimal configuration interface.

## Features

- 🎨 **Color-Coded Logging**: Automatic ANSI color coding for different log levels with flexible configuration
- 🏷️ **Custom Log Levels**: Support for custom log levels with configurable labels and fixed numeric assignments
- 🔄 **Minimal Interface**: Simple API for logging without complex setup
- 🌈 **Special Color Support**: Configurable colors for timestamps, process IDs, brackets, operators, etc.
- 📋 **Field Ordering**: Base class configurable field ordering (level, timestamp, pid, tid, message) for all log channels
- 💾 **JSON Configuration**: Save and load color/label configurations
- 🔗 **Multiple Channels**: Console and file logging implementations with unified configuration
- 🧪 **Format Flexibility**: Different formats for standard logs, commands, and std streams
- 📤 **Output Formats**: Multiple output formats (Human readable, JSON pretty, JSON lines) available to all channels with runtime switching
- 🔧 **Runtime Configuration**: Dynamically set color schemes and output formats at runtime for individual channels or all channels
- 📊 **Structured JSON Output**: Automatic parsing of message arguments into JSON with support for direct object serialization
- 🎯 **Enhanced ColorScheme API**: Flexible color retrieval supporting LogLevel enums, Field enums, and string keys
- ✅ **Comprehensive Testing**: Full test coverage including all new functionality

## Installation

```bash
pip install kingkybel-pyflashlogger
```

Or from source:
```bash
git clone https://github.com/kingkybel/FlashLogger.git
cd FlashLogger
pip install -e .
```

## Tools

FlashLogger includes interactive configuration tools:

### Color & Label Configurator (`tools/color_configurator.py`)

Interactive tool for customizing logging colors and labels with live preview:

```bash
cd tools
python color_configurator.py                 # Use default configs
python color_configurator.py colors.json labels.json  # Load custom configs

# Interactive commands:
# 4 RED _ DIM    # Change WARNING level colors
# load labels DE # Switch to German labels
# s              # Save configuration
# q              # Quit
```

**Features:**
- Visual preview of all colors and levels
- Tab completion for color names
- Load/save configurations
- Support for predefined schemes (COLOR, BW, PLAIN)
- International label support (EN, DE)

### Logger Testing Tool (`tools/try_out_logger.py`)

Sample script demonstrating FlashLogger capabilities with runtime configuration:

```bash
python tools/try_out_logger.py
```

Shows examples of:
- Runtime color scheme changes
- Output format switching
- Structured JSON output
- Custom log levels

## Quick Start

```python
from flashlogger import FlashLogger, ColorScheme, LogLevel

# Basic usage
logger = FlashLogger()
logger.log_info("This is an info message")
logger.log_warning("This is a warning")

# With custom colors
scheme = ColorScheme.default_color_scheme()
console_logger = FlashLogger(console=scheme)
console_logger.log_error("Colorized error message")

# Custom log levels
logger.log_custom0("Custom level message")
```

## Advanced Usage

### Runtime Color Scheme Configuration
```python
from flashlogger import ColorScheme, LogChannelConsole

# Create logger with initial scheme
logger = FlashLogger()
channel = logger.get_channel(LogChannelConsole.__name__)

# Dynamically change color schemes at runtime
channel.set_color_scheme(ColorScheme.Default.BLACK_AND_WHITE)
logger.set_color_scheme(ColorScheme.Default.COLOR)  # Affects all channels

# Use custom color schemes
custom_scheme = ColorScheme(color_scheme_json="my_colors.json")
channel.set_color_scheme(custom_scheme)
```

### Runtime Output Format Configuration
```python
from flashlogger import FlashLogger, OutputFormat

logger = FlashLogger()

# Set output format for all channels
logger.set_output_format(OutputFormat.JSON_PRETTY)

# Set format for individual channels
channel = logger.get_channel('LogChannelConsole')
channel.set_output_format('JSON_LINES')  # Override for this channel

# JSON output now includes structured arguments
logger.log_info("Simple message", {"complex": "data"}, arg1="value")
# Output: {"timestamp": "...", "level": "info", "message": "Simple message",
#          "message0": {"complex": "data"}, "arg1": "value"}
```

### Structured JSON Output
FlashLogger automatically structures logging arguments for JSON output:

```python
# Dict as first argument gets merged directly (no "message" wrapper)
logger.log_custom0({"user_id": 123, "action": "login"})
# JSON: {"user_id": 123, "action": "login", "level": "custom0", ...}

# Multiple args get indexed as message0, message1, etc.
logger.log_info("Operation", completed=True, duration=1.5)
# JSON: {"message": "Operation", "message0": true, "duration": 1.5, "level": "info", ...}
```

### Enhanced ColorScheme API
```python
from flashlogger import ColorScheme, LogLevel
from flashlogger.color_scheme import Field

scheme = ColorScheme(ColorScheme.Default.COLOR)

# Flexible color retrieval methods
color_str = scheme.get("warning")           # String key
color_enum = scheme.get(LogLevel.WARNING)   # LogLevel enum
field_color = scheme.get(Field.TIMESTAMP)   # Field enum

# With style and inverse options
bright_color = scheme.get("error", style=Style.BRIGHT)
inverse_color = scheme.get("debug", inverse=True)
```

### Color Configuration
```python
from flashlogger import ColorScheme

# Load predefined schemes
color_scheme = ColorScheme(ColorScheme.Default.COLOR)
bw_scheme = ColorScheme(ColorScheme.Default.BLACK_AND_WHITE)

# Create custom scheme from JSON
custom_scheme = ColorScheme(color_scheme_json="my_colors.json")

# Runtime color customization
scheme.set_level_color(LogLevel.WARNING, foreground="RED", background="YELLOW")
```

### Field Ordering
```python
# Customize log field display order
scheme.field_order = ["level", "timestamp", "message"]  # Omit pid/tid
logger = FlashLogger(console=scheme)

# Output: [WARNING] [2025-10-26 00:00:00.000] This is a message
```

### Custom Labels
```python
from flashlogger import LogLevel

# Define custom labels
LogLevel.set_str_repr(LogLevel.custom0, "NETWORK_IO")
LogLevel.set_str_repr(LogLevel.custom1, "DB_QUERY")

logger = FlashLogger()
logger.log_custom0("Network I/O operation")  # Shows as "NETWORK_IO"
```

## Log Levels

- **DEBUG**: Debugging information
- **INFO**: General information
- **WARNING**: Warning conditions
- **ERROR**: Error conditions
- **FATAL**: Fatal errors
- **CRITICAL**: Critical conditions
- **COMMAND**: Command execution
- **COMMAND_OUTPUT**: Command stdout capture
- **COMMAND_STDERR**: Command stderr capture
- **CUSTOM0-9**: Custom user-defined levels

## Configuration Files

FlashLogger includes default configuration files for color schemes and log level labels:

- `color_scheme_color.json`: Full color scheme
- `color_scheme_bw.json`: Black and white scheme
- `log_levels_en.json`: English log level labels
- `log_levels_de.json`: German log level labels

## Channels

### Console Channel
```python
from flashlogger import LogChannelConsole

channel = LogChannelConsole(color_scheme=my_scheme, minimum_log_level="WARNING")
channel.do_log("ERROR", "This error will be logged")
```

### File Channel
```python
from flashlogger import LogChannelFile

channel = LogChannelFile(filename="app.log")
channel.do_log("INFO", "This goes to file")
```

## Custom Channels

Extend `LogChannelABC` for custom logging destinations:

```python
from flashlogger import LogChannelABC

class MyChannel(LogChannelABC):
    def do_log(self, log_level, *args, **kwargs):
        # Your custom logging logic
        pass
```

## API Reference

### FlashLogger
- **Logging Methods**:
  - `log_debug(message)`: Log debug message
  - `log_info(message)`: Log info message
  - `log_warning(message)`: Log warning message
  - `log_error(message)`: Log error message
  - `log_fatal(message)`: Log fatal error
  - `log_custom0(message)`: Log custom level 0-9
- **Runtime Configuration**:
  - `set_output_format(format)`: Set output format for all channels
  - `set_color_scheme(scheme)`: Set color scheme for all channels
  - `add_channel(channel)`: Add a log channel with duplicate prevention
  - `get_channel(selector)`: Get channel by ID, name, or instance

### OutputFormat
- `HUMAN_READABLE`: Default human-readable format
- `JSON_PRETTY`: Pretty-printed JSON with indentation
- `JSON_LINES`: Compact single-line JSON

### ColorScheme
- Constructor: `ColorScheme(default_scheme_or_path)`
- Methods:
  - `get(level, inverse=False, style=None)`: Get colors for LogLevel, Field, or string
  - `save_to_json(path)`: Save configuration to JSON
  - `set_level_color(level, foreground, background)`: Runtime color customization

### LogChannelABC
- Methods:
  - `set_output_format(format)`: Set output format for this channel
  - `is_loggable(level)`: Check if level is loggable
  - `do_log(level, *args, **kwargs)`: Log a message

### LogChannelConsole
- Inherits from LogChannelABC
- Methods:
  - `set_color_scheme(scheme)`: Set color scheme for console output
  - `set_output_format(format)`: Set output format with formatter updates
  - `set_level_color(level, foreground, background)`: Runtime level color changes

### LogLevel
- Standard levels: `DEBUG`, `INFO`, `WARNING`, etc.
- Custom levels: `CUSTOM0` through `CUSTOM9` (with fixed numeric assignments)
- Methods: `set_str_repr(level, label)`, `load_str_reprs_from_json(path)`

## License

GPLv2 - See the LICENSE file for details.

## Contributing

Contributions welcome! Please open issues for bugs or feature requests.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request
