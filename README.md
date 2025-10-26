# FlashLogger

Advanced console logging with color support and minimal configuration interface.

## Features

- 🎨 **Color-Coded Logging**: Automatic ANSI color coding for different log levels
- 🏷️ **Custom Log Levels**: Support for custom log levels with configurable labels
- 🔄 **Minimal Interface**: Simple API for logging without complex setup
- 🌈 **Special Color Support**: Configurable colors for timestamps, process IDs, brackets, operators, etc.
- 📋 **Field Ordering**: Customize which fields display and their order (level, timestamp, pid, tid, message)
- 💾 **JSON Configuration**: Save and load color/label configurations
- 🔗 **Multiple Channels**: Console and file logging implementations
- 🧪 **Format Flexibility**: Different formats for standard logs, commands, and std streams

## Installation

```bash
pip install git+https://github.com/kingkybel/FlashLogger.git
```

Or locally:
```bash
git clone https://github.com/kingkybel/FlashLogger.git
cd FlashLogger
pip install -e .
```

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

### Color Configuration
```python
from flashlogger import ColorScheme

# Load predefined schemes
color_scheme = ColorScheme(ColorScheme.Default.COLOR)
bw_scheme = ColorScheme(ColorScheme.Default.BLACK_AND_WHITE)

# Create custom scheme
custom_scheme = ColorScheme()
custom_scheme.warning_normal_foreground = Fore.RED
custom_scheme.warning_normal_background = Back.YELLOW
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
- `log_debug(message)`: Log debug message
- `log_info(message)`: Log info message
- `log_warning(message)`: Log warning message
- `log_error(message)`: Log error message
- `log_fatal(message)`: Log fatal error
- `log_custom0(message)`: Log custom level 0

### ColorScheme
- Constructor: `ColorScheme(default_scheme_or_path)`
- Methods: `save_to_json(path)`, `set_level_color()`

### LogLevel
- Standard levels: `DEBUG`, `INFO`, `WARNING`, etc.
- Custom levels: `CUSTOM0` through `CUSTOM9`
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
