# Repository:   https://github.com/PyFlashLogger
# File Name:    flashlogger/flash_logger.py
# Description:  logging facility
#
# Copyright (C) 2024 Dieter J Elasticities <github@kybelksties.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# @date: 2024-07-13
# @author: Dieter J Kybelksties

from __future__ import annotations

import inspect
from collections.abc import Iterable
from os import PathLike
from pathlib import Path

from flashlogger.color_scheme import ColorScheme
from flashlogger.log_channel_abc import LogChannelABC, OutputFormat
from flashlogger.log_channel_console import LogChannelConsole
from flashlogger.log_channel_file import FileLogChannel
from flashlogger.log_levels import LogLevel


def _get_call_site_info(skip_frames: int = 2):
    """
    Get the file name and line number from the call site using stack inspection.

    :param skip_frames: Number of frames to skip in the stack trace
    :return: Tuple of (filename, lineno) or (None, None) if inspection fails
    """
    try:
        frame = inspect.currentframe()
        if frame is None:
            return None, None

        # Skip frames to get to the actual caller
        for _ in range(skip_frames):
            frame = frame.f_back
            if frame is None:
                return None, None

        filename = frame.f_code.co_filename
        lineno = frame.f_lineno

        return filename, lineno
    except Exception:
        # If anything goes wrong with stack inspection, return None
        return None, None


class FlashLogger:
    """
    A logger class that uses the LogLevels enum to format log entries for logfiles and console.
    """

    def __init__(self,
                 log_channels: LogChannelABC | Iterable[LogChannelABC] = None,
                 console: ColorScheme.Default = None,
                 log_file: str | PathLike | Path = None):
        """
        Initialize FlashLogger with optional automatic channel creation.

        :param log_channels: explicitly provided channels to add
        :param console: if not None and not ColorScheme.Default.PLAIN_TEXT, creates a default console channel
        :param log_file: if provided, creates a default file channel writing to this path
        """
        # Collect all channels to add
        channels_to_add = []

        # Add explicitly provided channels
        if log_channels is not None:
            if isinstance(log_channels, LogChannelABC):
                channels_to_add.append(log_channels)
            elif hasattr(log_channels, '__iter__'):
                channels_to_add.extend(log_channels)

        # Create default console channel if requested (handle PLAIN_TEXT properly)
        if console is not None and console != ColorScheme.Default.NONE:
            console_channel = LogChannelConsole(color_scheme=console, minimum_log_level=None)  # Show all levels
            channels_to_add.append(console_channel)

        # Create default file channel if requested
        if log_file is not None:
            file_channel = FileLogChannel(log_file, minimum_log_level=LogLevel.WARNING)
            channels_to_add.append(file_channel)

        # Ensure we have at least one channel
        if not channels_to_add:
            raise ValueError(f"No log channels specified when creating {__class__.__name__} instance")

        self.log_channels = []
        self._channel_id_counter = 0
        self._channel_ids = {}  # id -> channel mapping
        self._channel_selectors = {}  # selector -> channel mapping

        for log_channel in channels_to_add:
            self.add_channel(log_channel)

    def add_channel(self, log_channel: LogChannelABC, selector: str = None):
        """
        Add a log channel to this logger.
        :param log_channel: the channel to add
        :param selector: optional name/ID for accessing this channel later
        """
        # Don't add if already present
        if log_channel in self.log_channels:
            # Update selector if provided and not already set
            if selector is not None:
                self._channel_selectors[selector] = log_channel
            return

        self.log_channels.append(log_channel)

        # Assign ID
        channel_id = self._channel_id_counter
        self._channel_ids[channel_id] = log_channel
        self._channel_id_counter += 1

        # Store selector if provided
        if selector is not None:
            self._channel_selectors[selector] = log_channel

    def remove_channel(self, channel: LogChannelABC | int | str):
        """
        Remove a log channel from this logger.
        :param channel: Either the LogChannelABC instance to remove, its ID, or its selector name
        """
        channel_to_remove = None

        if isinstance(channel, int):
            # Remove by ID
            if channel in self._channel_ids:
                channel_to_remove = self._channel_ids[channel]
        elif isinstance(channel, str):
            # Remove by selector
            if channel in self._channel_selectors:
                channel_to_remove = self._channel_selectors[channel]
        else:
            # Remove by instance
            channel_to_remove = channel

        # Remove the channel if found
        if channel_to_remove and channel_to_remove in self.log_channels:
            self.log_channels.remove(channel_to_remove)

            # Remove from ID mapping
            for cid, chan in list(self._channel_ids.items()):
                if chan is channel_to_remove:
                    del self._channel_ids[cid]
                    break

            # Remove from selector mapping
            for sel, chan in list(self._channel_selectors.items()):
                if chan is channel_to_remove:
                    del self._channel_selectors[sel]
                    break

    def get_channel(self, selector: int | str | LogChannelABC):
        """
        Get a specific log channel by selector.

        :param selector: Channel identifier - can be:
                        - Integer ID (channel index)
                        - String name (e.g., 'console', 'file') - matches class name or type
                        - Channel instance (returns the channel if it's in the logger)
        :return: The requested LogChannelABC instance
        :raises: ValueError if no matching channel is found
        """
        # 1. By integer ID
        if isinstance(selector, int):
            if selector in self._channel_ids:
                return self._channel_ids[selector]
            raise ValueError(f"No channel found with ID {selector}")

        # 2. By string name - check selectors first, then match class name
        if isinstance(selector, str):
            # First check explicit selectors
            if selector in self._channel_selectors:
                return self._channel_selectors[selector]

            # Then match class name (ignoring case)
            selector_lower = selector.lower()
            for channel in self.log_channels:
                channel_class_name = type(channel).__name__.lower()
                # Match common patterns
                if selector_lower in channel_class_name or channel_class_name in selector_lower:
                    return channel
                # Direct match for common names
                if selector_lower == 'console' and 'console' in channel_class_name:
                    return channel
                if selector_lower == 'file' and 'file' in channel_class_name:
                    return channel
            raise ValueError(f"No channel found matching '{selector}'")

        # 3. By channel instance - check if it's in our channels
        for channel in self.log_channels:
            if channel is selector:
                return channel

        raise ValueError(f"No matching channel found for selector: {selector}")

    def log(self, level: LogLevel | str | int, *args, **kwargs):
        """Log a message at the specified level to all registered channels.

        :param level: The log level
        :param args: Message and arguments passed to channel.do_log()
        :param kwargs: Additional keyword arguments passed to channel.do_log(). May include 'file' and 'line' to override call site detection.
        """
        # Get call site information if not already provided
        file = kwargs.get('file')
        line = kwargs.get('line')
        if file is None or line is None:
            # Skip frames to get to the actual caller
            # Normal case: FlashLogger.log() method -> log_* method -> caller (skip 3)
            # Global function case: log_global() -> FlashLogger.log_*() -> FlashLogger.log() -> caller (skip 4)
            import inspect
            frame = inspect.currentframe()
            skip_frames = 3
            if frame and \
                    frame.f_back and \
                    frame.f_back.f_code.co_name.startswith('log_') and \
                    frame.f_back.f_code.co_filename == __file__:
                # We were called from a log_* method in this file, which means it was called from a global function
                skip_frames = 4

            detected_file, detected_line = _get_call_site_info(skip_frames=skip_frames)

            if file is None:
                file = detected_file
            if line is None:
                line = detected_line

        # Pass the file and line information to channels
        kwargs['file'] = file
        kwargs['line'] = line

        for channel in self.log_channels:
            try:
                channel.do_log(level, *args, **kwargs)
            except Exception as e:
                # Log errors to stderr but don't crash the logging system
                import sys
                print(f"Error logging to channel {type(channel).__name__}: {e}", file=sys.stderr)

    # Generate shortcuts for all LogLevel enum members
    def log_notset(self, *args, **kwargs):
        """Log at NOTSET level."""
        self.log(LogLevel.NOTSET, *args, **kwargs)

    def log_debug(self, *args, **kwargs):
        """Log at DEBUG level."""
        self.log(LogLevel.DEBUG, *args, **kwargs)

    def log_info(self, *args, **kwargs):
        """Log at INFO level."""
        self.log(LogLevel.INFO, *args, **kwargs)

    def log_warning(self, *args, **kwargs):
        """Log at WARNING level."""
        self.log(LogLevel.WARNING, *args, **kwargs)

    def log_error(self, *args: object, **kwargs: object) -> None:
        """Log at ERROR level."""
        self.log(LogLevel.ERROR, *args, **kwargs)

    def log_fatal(self, *args, **kwargs):
        """Log at FATAL level."""
        self.log(LogLevel.FATAL, *args, **kwargs)

    def log_critical(self, *args, **kwargs):
        """Log at CRITICAL level."""
        self.log(LogLevel.CRITICAL, *args, **kwargs)

    def log_command(self, *args, **kwargs):
        """Log at COMMAND level."""
        self.log(LogLevel.COMMAND, *args, **kwargs)

    def log_command_output(self, *args, **kwargs):
        """Log at COMMAND_OUTPUT level."""
        self.log(LogLevel.COMMAND_OUTPUT, *args, **kwargs)

    def log_command_stderr(self, *args, **kwargs):
        """Log at COMMAND_STDERR level."""
        self.log(LogLevel.COMMAND_STDERR, *args, **kwargs)

    # Custom level shortcuts
    def log_custom0(self, *args, **kwargs):
        """Log at CUSTOM0 level."""
        self.log(LogLevel.CUSTOM0, *args, **kwargs)

    def log_custom1(self, *args, **kwargs):
        """Log at CUSTOM1 level."""
        self.log(LogLevel.CUSTOM1, *args, **kwargs)

    def log_custom2(self, *args, **kwargs):
        """Log at CUSTOM2 level."""
        self.log(LogLevel.CUSTOM2, *args, **kwargs)

    def log_custom3(self, *args, **kwargs):
        """Log at CUSTOM3 level."""
        self.log(LogLevel.CUSTOM3, *args, **kwargs)

    def log_custom4(self, *args, **kwargs):
        """Log at CUSTOM4 level."""
        self.log(LogLevel.CUSTOM4, *args, **kwargs)

    def log_custom5(self, *args, **kwargs):
        """Log at CUSTOM5 level."""
        self.log(LogLevel.CUSTOM5, *args, **kwargs)

    def log_custom6(self, *args, **kwargs):
        """Log at CUSTOM6 level."""
        self.log(LogLevel.CUSTOM6, *args, **kwargs)

    def log_custom7(self, *args, **kwargs):
        """Log at CUSTOM7 level."""
        self.log(LogLevel.CUSTOM7, *args, **kwargs)

    def log_custom8(self, *args, **kwargs):
        """Log at CUSTOM8 level."""
        self.log(LogLevel.CUSTOM8, *args, **kwargs)

    def log_custom9(self, *args, **kwargs):
        """Log at CUSTOM9 level."""
        self.log(LogLevel.CUSTOM9, *args, **kwargs)

    def log_header(self, header: str):
        """Log a header message (typically at INFO level)."""
        self.log_info(f"# {header} #")

    def log_progress_output(self, message: str, verbosity: LogLevel | str | int = LogLevel.INFO, extra_comment: str = None):
        """Log progress output with optional extra comment."""
        if extra_comment:
            full_message = f"{message} ({extra_comment})"
        else:
            full_message = message
        self.log(verbosity, full_message)

    def set_output_format(self, output_format: OutputFormat | str):
        """
        Set the output format for all channels in this logger.

        :param output_format: OutputFormat enum or string equivalent
        """
        if isinstance(output_format, str):
            output_format = OutputFormat[output_format.upper()] if output_format else OutputFormat.HUMAN_READABLE

        # Set output format on all channels
        for channel in self.log_channels:
            channel.set_output_format(output_format)


# Lazy global logger - created when first accessed
_global_logger: FlashLogger | None = None


def get_logger(console: ColorScheme.Default = None, log_file: str | PathLike | Path = None) -> FlashLogger:
    """
    Get the global logger instance, creating it if necessary.
    Additional channels are added if they don't already exist.

    :param console: if provided and not PLAIN_TEXT, ensures a console channel exists
    :param log_file: if provided, ensures a file channel exists for the given path
    :return: the global FlashLogger instance
    """
    global _global_logger
    if _global_logger is None:
        # Create a default console logger if none exists
        from flashlogger.log_channel_console import LogChannelConsole
        console_channel = LogChannelConsole(minimum_log_level=None,
                                            color_scheme=ColorScheme.Default.COLOR)  # Show all levels
        _global_logger = FlashLogger([console_channel])

    # Add additional channels if requested and they don't exist
    if console is not None and console != ColorScheme.Default.PLAIN_TEXT:
        # Check if any console channel already exists
        from flashlogger.log_channel_console import LogChannelConsole
        has_console = any(isinstance(ch, LogChannelConsole) for ch in _global_logger.log_channels)
        if not has_console:
            console_channel = LogChannelConsole(color_scheme=console, minimum_log_level=None)  # Show all levels
            _global_logger.add_channel(console_channel)

    if log_file is not None:
        # Check if file channel with this path already exists
        file_path = Path(log_file)
        has_file = any(isinstance(ch, FileLogChannel) and hasattr(ch, 'log_file') and ch.log_file == file_path
                       for ch in _global_logger.log_channels)
        if not has_file:
            file_channel = FileLogChannel(log_file, minimum_log_level=LogLevel.WARNING)
            _global_logger.add_channel(file_channel)

    return _global_logger


def log(level: LogLevel | str | int, *args, **kwargs):
    get_logger().log(level, *args, **kwargs)


def log_error(*args, **kwargs):
    get_logger().log_error(*args, **kwargs)


def log_critical(*args, **kwargs):
    get_logger().log_critical(*args, **kwargs)


def log_fatal(*args, **kwargs):
    get_logger().log_fatal(*args, **kwargs)


def log_warning(*args, **kwargs):
    get_logger().log_warning( *args, **kwargs)


def log_info(*args, **kwargs):
    get_logger().log_info(*args, **kwargs)


def log_debug(*args, **kwargs):
    get_logger().log_debug(*args, **kwargs)


def log_header(*args, **kwargs):
    get_logger().log_header(*args, **kwargs)


def log_command(message: str | dict | list, extra_comment: str = None, dryrun: bool = False):
    get_logger().log_command(message, extra_comment=extra_comment, dryrun=dryrun)


def log_progress_output(message: str | dict | list,
                        verbosity: (str | LogLevel) = LogLevel.INFO,
                        extra_comment: str = None):
    get_logger().log_progress_output(message, verbosity=verbosity, extra_comment=extra_comment)


def log_custom0(*args, **kwargs):
    get_logger().log_custom0(*args, **kwargs)


def log_custom1(*args, **kwargs):
    get_logger().log_custom1(*args, **kwargs)


def log_custom2(*args, **kwargs):
    get_logger().log_custom2(*args, **kwargs)


def log_custom3(*args, **kwargs):
    get_logger().log_custom3(*args, **kwargs)


def log_custom4(*args, **kwargs):
    get_logger().log_custom4(*args, **kwargs)


def log_custom5(*args, **kwargs):
    get_logger().log_custom5(*args, **kwargs)


def log_custom6(*args, **kwargs):
    get_logger().log_custom6(*args, **kwargs)


def log_custom7(*args, **kwargs):
    get_logger().log_custom7(*args, **kwargs)


def log_custom8(*args, **kwargs):
    get_logger().log_custom8(*args, **kwargs)


def log_custom9(*args, **kwargs):
    get_logger().log_custom9(*args, **kwargs)
