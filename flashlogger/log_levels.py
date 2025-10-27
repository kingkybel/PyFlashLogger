# Repository:   https://github.com/Python-utilities
# File Name:    flashlogger/log_levels.py
# Description:  Log-level definitions
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

import logging
from enum import auto

from flashlogger.extended_enum import ExtendedEnum


class LogLevel(ExtendedEnum):
    # Predefined levels
    NOTSET = auto()
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    FATAL = auto()
    CRITICAL = auto()

    COMMAND = auto()
    COMMAND_OUTPUT = auto()
    COMMAND_STDERR = auto()

    # 10 dynamic custom levels
    CUSTOM0 = auto()
    CUSTOM1 = auto()
    CUSTOM2 = auto()
    CUSTOM3 = auto()
    CUSTOM4 = auto()
    CUSTOM5 = auto()
    CUSTOM6 = auto()
    CUSTOM7 = auto()
    CUSTOM8 = auto()
    CUSTOM9 = auto()

    def logging_level(self) -> int:
        """
        Return the associated logging level for this flag.
        :return: the logging level integer
        """
        if self in LogLevel.standard_mapping.values():
            return {v: k for k, v in LogLevel.standard_mapping.items()}[self]

        # Check if it's a command level
        if self == LogLevel.COMMAND:
            return LogLevel.command_level
        if self == LogLevel.COMMAND_OUTPUT:
            return LogLevel.command_stdout_level
        if self == LogLevel.COMMAND_STDERR:
            return LogLevel.command_stderr_level

        # Check if it is a custom level - return the assigned logging level
        for i, custom_flag in enumerate(
                [LogLevel.CUSTOM0, LogLevel.CUSTOM1, LogLevel.CUSTOM2, LogLevel.CUSTOM3,
                 LogLevel.CUSTOM4, LogLevel.CUSTOM5, LogLevel.CUSTOM6, LogLevel.CUSTOM7,
                 LogLevel.CUSTOM8, LogLevel.CUSTOM9]
        ):
            if self is custom_flag:
                # Return the assigned logging level for this CUSTOM level
                return LogLevel.custom_levels[i]

        return logging.NOTSET

    @classmethod
    def custom_level(cls, level: int, representation: str = None) -> LogLevel:
        """
        Get or create a custom log level:
        - If level < 0 → return NOTSET
        - If matches a standard level → return that flag
        - If matches an existing custom level → return it
        - Otherwise, assign to the next free custom slot

        :param level: the numeric log level value
        :param representation: optional string representation to use for this level
        :return: the LogLevel enum member
        """
        if level < 0:
            return cls.NOTSET

        # 1. Match standard levels
        if level in LogLevel.standard_mapping:
            return LogLevel.standard_mapping[level]

        # 2. Match existing custom levels
        for i, val in enumerate(LogLevel.custom_levels):
            if val == level:
                return getattr(cls, f"CUSTOM{i}")

        # 3. Assign to next available custom slot
        for i, val in enumerate(LogLevel.custom_levels):
            if val == logging.NOTSET:  # free slot
                LogLevel.custom_levels[i] = int(level)
                custom_level = getattr(cls, f"CUSTOM{i}")
                if representation is not None:
                    cls.custom_str_map[custom_level] = representation
                return custom_level

        # 4. No slot available
        raise ValueError("No available custom log level slots.")

    @classmethod
    def set_str_repr(cls, level: LogLevel, representation: str) -> None:
        """
        Set a custom string representation for a log level.
        :param level: the log level to customize
        :param representation: the string representation to use
        """
        LogLevel.custom_str_map[level] = representation

    @classmethod
    def set_str_reprs(cls, str_map: dict[LogLevel, str]) -> None:
        """
        Set custom string representations for multiple log levels.
        :param str_map: dictionary mapping log levels to their string representations
        """
        LogLevel.custom_str_map.update(str_map)

    @classmethod
    def clear_str_reprs(cls) -> None:
        """
        Clear all custom string representations, reverting to defaults.
        """
        LogLevel.custom_str_map.clear()

    @classmethod
    def load_str_reprs_from_json(cls, json_file_path: str) -> None:
        """
        Load string representations from a JSON file.
        :param json_file_path: path to the JSON file
        """
        import json
        with open(json_file_path, "r", encoding="utf-8") as f:
            str_map_data = json.load(f)

        # Map the JSON data to LogLevel instances
        str_map = {}
        for level_name, representation in str_map_data.items():
            level_name_upper = level_name.upper()
            if hasattr(cls, level_name_upper):
                str_map[getattr(cls, level_name_upper)] = representation

        LogLevel.custom_str_map.update(str_map)

    @classmethod
    def save_str_reprs_to_json(cls, json_file_path: str) -> None:
        """
        Save custom string representations to a JSON file.
        :param json_file_path: path to save the JSON file
        """
        import json

        # Build a dictionary mapping level names to representations
        str_map_data = {}
        for level, representation in cls.custom_str_map.items():
            # Use the level name in lowercase as the key (like the JSON files do)
            level_name = level.name.lower()
            str_map_data[level_name] = representation

        # Save to file
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(str_map_data, f, indent=2, sort_keys=True)

    def __str__(self) -> str:
        return LogLevel.custom_str_map.get(self, self.name.lower())


# Storage for custom level values
LogLevel.custom_levels = [logging.NOTSET] * 10

LogLevel.command_level = logging.INFO + 2
LogLevel.command_stdout_level = logging.INFO + 4
LogLevel.command_stderr_level = logging.INFO + 6

# Mapping of standard Python logging levels
LogLevel.standard_mapping = {
    logging.NOTSET: LogLevel.NOTSET,
    logging.DEBUG: LogLevel.DEBUG,
    logging.INFO: LogLevel.INFO,
    LogLevel.command_level: LogLevel.COMMAND,
    LogLevel.command_stdout_level: LogLevel.COMMAND_OUTPUT,
    LogLevel.command_stderr_level: LogLevel.COMMAND_STDERR,
    logging.WARNING: LogLevel.WARNING,
    logging.ERROR: LogLevel.ERROR,
    logging.CRITICAL: LogLevel.CRITICAL,
    logging.FATAL + 1: LogLevel.FATAL,
}

# Storage for custom string representations
LogLevel.custom_str_map = {}
