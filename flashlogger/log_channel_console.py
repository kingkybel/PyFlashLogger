# Repository:   https://github.com/Python-utilities
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

from colorama import Style, Fore, Back

from flashlogger.color_scheme import ColorScheme
from flashlogger.log_channel_abc import LogChannelABC, OutputFormat
from flashlogger.log_levels import LogLevel
from flashlogger.overrides import overrides

DEFAULT_FORMAT = "[%(asctime)s]\t[%(levelname)s] %(message)s"


class ConsoleFormatter(logging.Formatter):
    """
    A formatter class to customize how log-entries should be displayed on the console.
    """

    def __init__(self, fmt=DEFAULT_FORMAT, color_scheme=None, field_order=None, output_format=None):
        logging.Formatter.__init__(self, fmt=fmt)
        self.color_scheme = color_scheme if color_scheme is not None else ColorScheme()
        self.field_order = field_order if field_order is not None else ["timestamp", "pid", "tid", "level", "message"]
        self.output_format = output_format if output_format is not None else OutputFormat.HUMAN_READABLE
        self._build_level_colors()

    def _build_level_colors(self):
        self.normal_colors = {}
        self.highlight_colors = {}

        for log_level in LogLevel:
            level_str = log_level.name.lower()

            # Build normal colors
            fg_attr = f"{level_str}_normal_foreground"
            bg_attr = f"{level_str}_normal_background"
            style_attr = f"{level_str}_normal_style"
            fg = getattr(self.color_scheme, fg_attr, "")
            bg = getattr(self.color_scheme, bg_attr, "")
            sty = getattr(self.color_scheme, style_attr, "")

            # Only include background if it's not empty or "default"
            if bg in ("", "default"):
                self.normal_colors[int(log_level.logging_level())] = fg + sty
            else:
                self.normal_colors[int(log_level.logging_level())] = fg + bg + sty

            # Build highlight colors
            fg_attr = f"{level_str}_highlight_foreground"
            bg_attr = f"{level_str}_highlight_background"
            style_attr = f"{level_str}_highlight_style"
            fg = getattr(self.color_scheme, fg_attr, "")
            bg = getattr(self.color_scheme, bg_attr, "")
            sty = getattr(self.color_scheme, style_attr, "")

            # Only include background if it's not empty or "default"
            if bg in ("", "default"):
                self.highlight_colors[int(log_level.logging_level())] = fg + sty
            else:
                self.highlight_colors[int(log_level.logging_level())] = fg + bg + sty

    def get_normal_color(self, level):
        """Get the normal color for a log level."""
        return self.normal_colors.get(level, "")

    def get_highlight_color(self, level):
        """Get the highlight color for a log level."""
        return self.highlight_colors.get(level, "")

    def _get_field_tags(self, record, level_color, level_name, timestamp, pid, tid, message):
        """Get field tags dict based on field_order."""
        process_fg = getattr(self.color_scheme, "process_color_foreground", Fore.CYAN)
        timestamp_color = getattr(self.color_scheme, "timestamp_color_foreground", process_fg)
        bracket_color = getattr(self.color_scheme, "bracket_color_foreground",
                                getattr(self.color_scheme, "operator_color_foreground", Fore.YELLOW))
        message_color = getattr(self.color_scheme, "default_color_foreground", Fore.LIGHTWHITE_EX)

        left_square_brace = bracket_color + "[" + Style.RESET_ALL
        right_square_brace = bracket_color + "]" + Style.RESET_ALL

        tags = {
            "timestamp": left_square_brace + timestamp_color + timestamp + Style.RESET_ALL + right_square_brace,
            "pid": left_square_brace + process_fg + f"pid:{pid}" + Style.RESET_ALL + right_square_brace,
            "tid": left_square_brace + process_fg + f"tid:{tid}" + Style.RESET_ALL + right_square_brace,
            "level": left_square_brace + level_color + level_name + Style.RESET_ALL + right_square_brace,
            "message": left_square_brace + message_color + message + Style.RESET_ALL + right_square_brace,
        }
        return tags

    def set_level_color(self,
                        log_level: LogLevel | str | int,
                        scheme_type: str = "normal",
                        foreground: str = None,
                        background: str = None,
                        style: str = None) -> None:
        """
        Set custom colors for a specific log level and scheme type at runtime.

        :param log_level: the log level to configure (LogLevel, str, or int)
        :param scheme_type: "normal" or "highlight"
        :param foreground: color name (e.g., "RED", "GREEN") or "default" or None to keep current
        :param background: color name (e.g., "BLACK", "WHITE") or "default" or None to keep current
        :param style: style name (e.g., "NORMAL", "BRIGHT") or "default" or None to keep current
        """
        if isinstance(log_level, str):
            log_level = LogLevel[log_level.upper()]
        elif isinstance(log_level, int):
            log_level = LogLevel.custom_level(log_level)

        level_str = log_level.name.lower()

        # Validate scheme_type
        if scheme_type not in {"normal", "highlight"}:
            raise ValueError('scheme_type must be "normal" or "highlight"')

        # Get current colors if not specified
        current_fg_key = f"{level_str}_{scheme_type}_foreground"
        current_bg_key = f"{level_str}_{scheme_type}_background"
        current_style_key = f"{level_str}_{scheme_type}_style"

        current_fg = getattr(self.color_scheme, current_fg_key, "")
        current_bg = getattr(self.color_scheme, current_bg_key, "")
        current_style = getattr(self.color_scheme, current_style_key, Style.NORMAL)

        # Apply new colors if specified
        if foreground is not None:
            if foreground == "default":
                current_fg = getattr(self.color_scheme, 'default_foreground', Fore.MAGENTA)
            elif isinstance(foreground, str) and foreground.upper() in dir(Fore):
                current_fg = getattr(Fore, foreground.upper())
            else:
                # Try to get from color_scheme attributes, fall back to white
                fg_attr = f"{foreground.lower()}_{scheme_type}_foreground" if foreground != "" else ""
                current_fg = getattr(self.color_scheme, fg_attr, "") if fg_attr else Fore.WHITE

        if background is not None:
            if background in ("default", ""):
                current_bg = ""  # Don't add any background
            elif isinstance(background, str) and background.upper() in dir(Back):
                current_bg = getattr(Back, background.upper())
            else:
                # Try to get from color_scheme attributes, fall back to black
                bg_attr = f"{background.lower()}_{scheme_type}_background" if background != "" else ""
                current_bg = getattr(self.color_scheme, bg_attr, "") if bg_attr else Back.BLACK

        if style is not None:
            if style == "default":
                current_style = getattr(self.color_scheme, 'default_style', Style.NORMAL)
            elif isinstance(style, str) and style.upper() in dir(Style):
                current_style = getattr(Style, style.upper())
            else:
                # Try to get from color_scheme attributes, fall back to normal
                style_attr = f"{style.lower()}_{scheme_type}_style" if style != "" else ""
                current_style = getattr(self.color_scheme, style_attr, Style.NORMAL) if style_attr else Style.NORMAL

        # Update the colors in color_scheme and rebuild the color dictionaries
        setattr(self.color_scheme, current_fg_key, current_fg)
        setattr(self.color_scheme, current_bg_key, current_bg)
        setattr(self.color_scheme, current_style_key, current_style)

        # Rebuild level colors
        self._build_level_colors()

    @overrides(logging.Formatter)
    def format(self, record: LogRecord) -> str:
        """
        Overriding the format function in order to handle custom log-levels appropriately.
        :param record: the logging record.
        :return: the formatted record as string.
        """
        message = record.getMessage()
        timestamp = self.formatTime(record)
        log_level = LogLevel.custom_level(record.levelno)
        level_name = str(log_level).lower()
        if record.levelno in {LogLevel.ERROR.logging_level(),
                              LogLevel.WARNING.logging_level(),
                              LogLevel.FATAL.logging_level(),
                              LogLevel.CRITICAL.logging_level()}:
            level_name = level_name.upper()
        process_id = record.process
        thread_id = record.thread

        data = {
            "timestamp": timestamp,
            "level": level_name,
            "message": message,
            "pid": process_id,
            "tid": thread_id
        }

        if self.output_format != OutputFormat.HUMAN_READABLE:
            indent = 4 if self.output_format == OutputFormat.JSON_PRETTY else None
            if log_level == LogLevel.COMMAND:
                data["type"] = "command"
            elif log_level == LogLevel.COMMAND_OUTPUT:
                data["type"] = "stdout"
            elif log_level == LogLevel.COMMAND_STDERR:
                data["type"] = "stderr"
            return json.dumps(data, indent=indent, default=str)

        # Human readable
        operator_fg = getattr(self.color_scheme, "operator_color_foreground", Fore.YELLOW)
        comment_fg = getattr(self.color_scheme, "comment_color_foreground", Fore.LIGHTBLACK_EX)
        message_fg = getattr(self.color_scheme, "default_color_foreground", Fore.LIGHTWHITE_EX)
        left_round_brace = operator_fg + "(" + Style.RESET_ALL
        right_round_brace = operator_fg + ")" + Style.RESET_ALL
        normal_color = self.get_normal_color(record.levelno)
        highlight_color = self.get_highlight_color(record.levelno)

        if log_level == LogLevel.COMMAND:
            message_tag = normal_color + message + Style.RESET_ALL
            comment_tag = comment_fg + f" ## command executed at {timestamp}" + Style.RESET_ALL
            return f"{message_tag}{comment_tag}"

        if log_level == LogLevel.COMMAND_OUTPUT:
            std_tag = left_round_brace + highlight_color + "stdout" + right_round_brace + ": " + Style.RESET_ALL
            message_tag = message_fg + message + Style.RESET_ALL
            return f"{std_tag}{message_tag}"

        if log_level == LogLevel.COMMAND_STDERR:
            std_tag = left_round_brace + highlight_color + "stderr" + right_round_brace + ": " + Style.RESET_ALL
            message_tag = message_fg + message + Style.RESET_ALL
            return f"{std_tag}{message_tag}"

        # Regular log
        tags = self._get_field_tags(record, highlight_color, level_name, timestamp, process_id, thread_id, message)
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
                handler.setFormatter(ConsoleFormatter(color_scheme=self.color_scheme, field_order=self.field_order, output_format=self.output_format))
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

    def set_level_color(self, log_level: LogLevel | str | int, scheme_type: str,
                        foreground: str = None, background: str = None, style: str = None) -> None:
        """
        Set custom colors for a specific log level and scheme type at runtime.

        This method delegates to the formatter's set_level_color method.

        :param log_level: the log level to configure (LogLevel, str, or int)
        :param scheme_type: "normal" or "highlight"
        :param foreground: color name (e.g., "RED", "GREEN") or "default" or None to keep current
        :param background: color name (e.g., "BLACK", "WHITE") or "default" or None to keep current
        :param style: style name (e.g., "NORMAL", "BRIGHT") or "default" or None to keep current
        """
        # Find our formatter in the logger handlers and call set_level_color on it
        for handler in self._logger.handlers:
            if isinstance(handler, logging.StreamHandler) and isinstance(handler.formatter, ConsoleFormatter):
                handler.formatter.set_level_color(log_level, scheme_type, foreground, background, style)
                return

        # If not using shared logger, try to find the formatter directly
        if hasattr(self, '_formatter') and isinstance(self._formatter, ConsoleFormatter):
            self._formatter.set_level_color(log_level, scheme_type, foreground, background, style)

    @overrides(LogChannelABC)
    def do_log(self, log_level: LogLevel | str | int, *args, **kwargs) -> None:
        """
        Log a message to console.
        :param log_level: the logging level
        :param kwargs: any other arguments, ignored
        """
        if not self.is_loggable(log_level):
            return
        if isinstance(log_level, str):
            log_level = LogLevel[log_level.upper()]
        elif isinstance(log_level, int):
            log_level = LogLevel.custom_level(log_level)
        # now log_level is LogLevel
        self._logger.log(log_level.logging_level(), args[0] if args else "", *args[1:], **kwargs)
