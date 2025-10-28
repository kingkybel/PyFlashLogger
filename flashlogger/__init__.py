"""
FlashLogger: Advanced console logging with color support.

This package provides a flexible logging system with support for multiple channels,
custom log levels, and ANSI color schemes for console output.
"""

from .color_scheme import ColorScheme
from .flash_logger import (
    FlashLogger,
    get_logger,
    log_error,
    log_warning,
    log_info,
    log_debug,
    log_header,
    log_command,
    log_progress_output,
)
from .log_channel_abc import LogChannelABC
from .log_channel_console import LogChannelConsole
from .log_channel_file import FileLogChannel
from .log_levels import LogLevel

__version__ = "1.0.2"

__all__ = [
    "FlashLogger",
    "LogLevel",
    "ColorScheme",
    "LogChannelABC",
    "LogChannelConsole",
    "FileLogChannel",
    "get_logger",
    "log_error",
    "log_warning",
    "log_info",
    "log_debug",
    "log_header",
    "log_command",
    "log_progress_output",
]
