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
    log_critical,
    log_fatal,
    log_warning,
    log_info,
    log_debug,
    log_header,
    log_command,
    log_progress_output,
    log_custom0,
    log_custom1,
    log_custom2,
    log_custom3,
    log_custom4,
    log_custom5,
    log_custom6,
    log_custom7,
    log_custom8,
    log_custom9,
)
from .log_channel_abc import LogChannelABC, OutputFormat
from .log_channel_console import LogChannelConsole, ConsoleFormatter
from .log_channel_file import FileLogChannel, FileLogFormatter
from .log_levels import LogLevel

__version__ = "1.0.3"

__all__ = [
    "FlashLogger",
    "LogLevel",
    "ColorScheme",
    "LogChannelABC",
    "LogChannelConsole",
    "FileLogChannel",
    "OutputFormat",
    "ConsoleFormatter",
    "FileLogFormatter",
    "get_logger",
    "log_error",
    "log_critical",
    "log_fatal",
    "log_warning",
    "log_info",
    "log_debug",
    "log_header",
    "log_command",
    "log_progress_output",
    "log_custom0",
    "log_custom1",
    "log_custom2",
    "log_custom3",
    "log_custom4",
    "log_custom5",
    "log_custom6",
    "log_custom7",
    "log_custom8",
    "log_custom9",
]
