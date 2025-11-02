# Repository:   https://github.com/PyFlashLogger
# File Name:    flashlogger/log_channel_file.py
# Description:  Log-channel definitions for logging to file
#
# Copyright (C) 2025 Dieter J Kybelksties <github@kybelksties.com>
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
# @date: 2025-10-21
# @author: Dieter J Kybelksties

from __future__ import annotations

import datetime
import json
import logging
from logging import LogRecord
from pathlib import Path

from colorama import Style, Fore, Back
from fundamentals import overrides

from flashlogger.color_scheme import ColorScheme
from flashlogger.log_channel_abc import LogChannelABC, OutputFormat
from flashlogger.log_levels import LogLevel

DEFAULT_FORMAT = "[%(asctime)s]\t[%(levelname)s] %(message)s"


class ConsoleFormatter(logging.Formatter):
    """
    A formatter class to customize how log-entries should be displayed on the console.
    """

    def __init__(self, fmt=DEFAULT_FORMAT, color_scheme=None, field_order=None, output_format=None, channel=None):
        logging.Formatter.__init__(self, fmt=fmt)
        self.color_scheme = color_scheme if color_scheme is not None else ColorScheme()
        self.field_order = field_order if field_order is not None else ["timestamp", "pid", "tid", "file", "level", "message"]
        self.output_format = output_format if output_format is not None else OutputFormat.HUMAN_READABLE
        self.channel = channel

    # Removed _build_level_colors, get_normal_color, get_highlight_color methods
    # as they are no longer needed with the simplified ColorScheme.get() method

    def _get_field_tags(self, record, level_color, level_name, timestamp, pid, tid, message, file=None, line=None):
        """Get field tags dict based on field_order."""
        # Use the new ColorScheme.get() method for field colors
        timestamp_color = self.color_scheme.get("timestamp")
        pid_color = self.color_scheme.get("pid")
        tid_color = self.color_scheme.get("tid")
        bracket_color = self.color_scheme.get("operator")

        left_square_brace = bracket_color + "[" + Style.RESET_ALL
        right_square_brace = bracket_color + "]" + Style.RESET_ALL

        # Format file information
        file_info = "unknown"
        if file and line:
            # Get just the filename without path
            import os
            filename = os.path.basename(file) if file != "<stdin>" else file
            file_info = f"{filename}:{line}"
        elif file:
            import os
            filename = os.path.basename(file) if file != "<stdin>" else file
            file_info = filename
        elif line:
            file_info = f"line:{line}"

        tags = {
            "timestamp": left_square_brace + timestamp_color + timestamp + Style.RESET_ALL + right_square_brace,
            "pid": left_square_brace + pid_color + f"pid:{pid}" + Style.RESET_ALL + right_square_brace,
            "tid": left_square_brace + tid_color + f"tid:{tid}" + Style.RESET_ALL + right_square_brace,
            "file": left_square_brace + self.color_scheme.get("file") + file_info + Style.RESET_ALL + right_square_brace,
            "level": left_square_brace + level_color + level_name + Style.RESET_ALL + right_square_brace,
            "message": left_square_brace + self.color_scheme.get("message") + message + Style.RESET_ALL + right_square_brace,
        }
        return tags

    def set_level_color(self, log_level: LogLevel | str | int,
                        foreground: str = None, background: str = None) -> None:
        """
        Set custom colors for a specific log level at runtime.

        :param log_level: the log level to configure (LogLevel, str, or int)
        :param foreground: color name (e.g., "RED", "GREEN")
        :param background: color name (e.g., "BLACK", "WHITE")
        """
        if isinstance(log_level, str):
            log_level = LogLevel[log_level.upper()]
        elif isinstance(log_level, int):
            log_level = LogLevel.custom_level(log_level)

        level_str = log_level.name.lower()

        # Convert color names to ANSI codes and set attributes
        if foreground is not None:
            fg = getattr(Fore, foreground.upper(), Fore.WHITE)
            setattr(self.color_scheme, f"{level_str}_foreground", fg)

        if background is not None:
            bg = getattr(Back, background.upper(), Back.BLACK)
            setattr(self.color_scheme, f"{level_str}_background", bg)

    def _format_args_for_json(self, record: LogRecord) -> dict:
        """
        Format the logging record for JSON output.

        For JSON formats, we create a clean structure with:
        - Standard fields: timestamp, level, pid, tid
        - If first arg is a dict, merge it directly
        - Additional args as message1, message2, etc.
        - Keyword args as direct fields

        :param record: the logging record
        :return: dict for JSON serialization
        """
        # Get standard fields
        timestamp = self.formatTime(record)
        log_level = LogLevel.custom_level(record.levelno)
        level_name = str(log_level).lower()
        if record.levelno in {LogLevel.ERROR.logging_level(),
                              LogLevel.WARNING.logging_level(),
                              LogLevel.FATAL.logging_level(),
                              LogLevel.CRITICAL.logging_level()}:
            level_name = level_name.upper()

        data = {
            "timestamp": timestamp,
            "level": level_name,
            "pid": self.channel.process_id if self.channel else record.process,
            "tid": self.channel.thread_id if self.channel else record.thread,
        }

        # Check if the main message content is a dict that should be merged directly
        main_message = getattr(record, 'msg', '')
        if isinstance(main_message, dict):
            # Main message is a dict - merge directly into data
            data.update(main_message)
            # Add remaining args if any
            for i, arg in enumerate(record.args):
                key = f"message{i}"
                data[key] = arg
        else:
            # Regular case - add message and positional args
            data["message"] = main_message
            for i, arg in enumerate(record.args):
                key = f"message{i}"
                data[key] = arg

        # Add file/line info if available
        file_info = getattr(record, 'file', None)
        line_info = getattr(record, 'line', None)
        if file_info:
            data["file"] = file_info
        if line_info:
            data["line"] = line_info

        # Add any keyword arguments that were stored in record.__dict__
        for key, value in record.__dict__.items():
            if key not in {'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'exc_text', 'exc_info', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'message',
                          'asctime', 'file', 'line'}:  # Standard LogRecord attributes + our additions
                data[key] = value

        return data

    @overrides(logging.Formatter)
    def format(self, record: LogRecord) -> str:
        """
        Overriding the format function in order to handle custom log-levels appropriately.
        :param record: the logging record.
        :return: the formatted record as string.
        """
        # Safely get message - if formatting fails, use the raw msg
        try:
            message = record.getMessage()
        except (TypeError, ValueError):
            message = record.msg  # Use raw message without formatting
        timestamp = self.formatTime(record)
        log_level = LogLevel.custom_level(record.levelno)
        level_name = str(log_level).lower()
        if record.levelno in {LogLevel.ERROR.logging_level(),
                              LogLevel.WARNING.logging_level(),
                              LogLevel.FATAL.logging_level(),
                              LogLevel.CRITICAL.logging_level()}:
            level_name = level_name.upper()
        process_id = self.channel.process_id if self.channel else record.process
        thread_id = self.channel.thread_id if self.channel else record.thread

        data = {
            "timestamp": timestamp,
            "level": level_name,
            "message": message,
            "pid": process_id,
            "tid": thread_id
        }

        if self.output_format != OutputFormat.HUMAN_READABLE:
            # Use the complete structured format for JSON output
            data = self._format_args_for_json(record)
            # Add command types if applicable
            if log_level == LogLevel.COMMAND:
                data["type"] = "command"
            elif log_level == LogLevel.COMMAND_OUTPUT:
                data["type"] = "stdout"
            elif log_level == LogLevel.COMMAND_STDERR:
                data["type"] = "stderr"
            indent = 4 if self.output_format == OutputFormat.JSON_PRETTY else None
            return json.dumps(data, indent=indent, default=str)

        # Human readable
        operator_fg = Fore.YELLOW  # Use yellow for operators
        comment_fg = Fore.LIGHTBLACK_EX  # Use light black for comments
        left_round_brace = operator_fg + "(" + Style.RESET_ALL
        right_round_brace = operator_fg + ")" + Style.RESET_ALL
        # Use ColorScheme.get() for log level colors
        log_level_str = str(LogLevel.custom_level(record.levelno)).lower()
        normal_color = self.color_scheme.get(log_level_str)
        highlight_color = self.color_scheme.get(log_level_str, style=Style.BRIGHT)  # Highlight with bright style

        if log_level == LogLevel.COMMAND:
            message_tag = normal_color + message + Style.RESET_ALL
            comment_tag = comment_fg + f" ## command executed at {timestamp}" + Style.RESET_ALL
            return f"{message_tag}{comment_tag}"

        if log_level == LogLevel.COMMAND_OUTPUT:
            std_tag = left_round_brace + highlight_color + "stdout" + right_round_brace + ": " + Style.RESET_ALL
            message_tag = self.color_scheme.get("message") + message + Style.RESET_ALL
            return f"{std_tag}{message_tag}"

        if log_level == LogLevel.COMMAND_STDERR:
            std_tag = left_round_brace + highlight_color + "stderr" + right_round_brace + ": " + Style.RESET_ALL
            message_tag = self.color_scheme.get("message") + message + Style.RESET_ALL
            return f"{std_tag}{message_tag}"

        # Regular log - get file and line from record's __dict__ if available
        file_info = getattr(record, 'file', None)
        line_info = getattr(record, 'line', None)
        tags = self._get_field_tags(record, highlight_color, level_name, timestamp, process_id, thread_id, message, file=file_info, line=line_info)
        return " ".join([tags[field] for field in self.field_order if field in tags])

    @overrides(logging.Formatter)
    def formatTime(self, record, datefmt=None) -> str:
        """
        Higher precision timestamps.
        :param: record: the log-record to format.
        :param: date_fmt:  the format string for dates and timestamps.
        :return: the formatted timestamp as string.
        """
        ct = datetime.datetime.fromtimestamp(record.created)
        if datefmt is not None:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime("%Y-%m-%d %H:%M:%S")
            s = f"{t}.{int(record.msecs):05d}"
        return s


class LogChannelConsole(LogChannelABC):
    """
    A logging channel which writes log messages to console.
    """

    def __init__(self,
                 color_scheme: ColorScheme | ColorScheme.Default = None,
                 minimum_log_level=None,
                 include_log_levels=None,
                 exclude_log_levels=None,
                 use_shared_logger: bool = True,
                 output_format: OutputFormat | str = None):
        super().__init__(minimum_log_level=minimum_log_level,
                         include_log_levels=include_log_levels,
                         exclude_log_levels=exclude_log_levels)
        if output_format is not None:
            if isinstance(output_format, str):
                output_format = OutputFormat[output_format.upper()]
            self.output_format = output_format
        self.color_scheme = color_scheme if color_scheme and isinstance(color_scheme, ColorScheme) \
            else ColorScheme(default_scheme=color_scheme)
        self.use_shared_logger = use_shared_logger

        if use_shared_logger:
            # Use the shared logger from LogChannelABC
            self._logger = self.__class__.get_shared_logger()
            # Ensure shared logger has our formatter
            if not any(isinstance(h, logging.StreamHandler) and
                       isinstance(getattr(h, "formatter", None), ConsoleFormatter)
                       for h in self._logger.handlers):
                # Add our console formatter if not already present
                handler = logging.StreamHandler()
                handler.setFormatter(ConsoleFormatter(color_scheme=self.color_scheme,
                                                      field_order=self.field_order,
                                                      output_format=self.output_format,
                                                      channel=self))
                self._logger.addHandler(handler)
        else:
            # Create instance-specific logger (legacy behavior)
            if not hasattr(LogChannelConsole, "_handler_added"):
                handler = logging.StreamHandler()
                handler.setFormatter(ConsoleFormatter(color_scheme=self.color_scheme))
                logging.getLogger().addHandler(handler)
                logging.getLogger().setLevel(logging.DEBUG)
                LogChannelConsole._handler_added = True
            self._logger = logging.getLogger()

    def set_level_color(self, log_level: LogLevel | str | int,
                        foreground: str = None, background: str = None) -> None:
        """
        Set custom colors for a specific log level at runtime.

        This method delegates to the formatter's set_level_color method.

        :param log_level: the log level to configure (LogLevel, str, or int)
        :param foreground: color name (e.g., "RED", "GREEN")
        :param background: color name (e.g., "BLACK", "WHITE")
        """
        # Find our formatter in the logger handlers and call set_level_color on it
        for handler in self._logger.handlers:
            if isinstance(handler, logging.StreamHandler) and isinstance(handler.formatter, ConsoleFormatter):
                handler.formatter.set_level_color(log_level, foreground, background)
                return

        # If not using shared logger, try to find the formatter directly
        if hasattr(self, '_formatter') and isinstance(self._formatter, ConsoleFormatter):
            self._formatter.set_level_color(log_level, foreground, background)

    def set_color_scheme(self, color_scheme) -> None:
        """
        Set the color scheme for this console logger.

        :param color_scheme: either a ColorScheme.Default enum or a path (str/Path) to a color scheme JSON file
        """
        if isinstance(color_scheme, ColorScheme.Default):
            self.color_scheme = ColorScheme(default_scheme=color_scheme)
        elif isinstance(color_scheme, (str, Path)):
            self.color_scheme = ColorScheme(colorscheme_json=Path(color_scheme))
        elif isinstance(color_scheme, ColorScheme):
            self.color_scheme = color_scheme
        else:
            raise ValueError(f"Invalid color_scheme type: {type(color_scheme)}. Expected ColorScheme.Default, path, or ColorScheme instance.")

        # Update the color_scheme in all ConsoleFormatters
        for handler in self._logger.handlers:
            if isinstance(handler, logging.StreamHandler) and isinstance(handler.formatter, ConsoleFormatter):
                handler.formatter.color_scheme = self.color_scheme

    def set_output_format(self, output_format: OutputFormat | str) -> None:
        """
        Set the output format for this console logger.

        :param output_format: OutputFormat enum or string equivalent
        """
        # Call the parent method to update self.output_format
        super().set_output_format(output_format)

        # Update the output_format in all ConsoleFormatters
        for handler in self._logger.handlers:
            if isinstance(handler, logging.StreamHandler) and isinstance(handler.formatter, ConsoleFormatter):
                handler.formatter.output_format = self.output_format

    @overrides(LogChannelABC)
    def do_log(self, log_level: LogLevel | str | int, *args, **kwargs) -> None:
        """
        Log a message to console.
        :param log_level: the logging level
        :param kwargs: additional keyword arguments, including file and line info
        """
        if not self.is_loggable(log_level):
            return
        if isinstance(log_level, str):
            log_level = LogLevel[log_level.upper()]
        elif isinstance(log_level, int):
            log_level = LogLevel.custom_level(log_level)
        # now log_level is LogLevel

        # Extract file and line info for the LogRecord
        extra = {}
        if 'file' in kwargs:
            extra['file'] = kwargs['file']
        if 'line' in kwargs:
            extra['line'] = kwargs['line']

        # Remove file/line from kwargs so they don't interfere with message formatting
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ('file', 'line')}

        # Add all remaining kwargs to extra dict (for JSON args and custom data)
        extra.update(filtered_kwargs)

        self._logger.log(log_level.logging_level(), args[0] if args else "", *args[1:], extra=extra)
