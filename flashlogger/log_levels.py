# Repository:   https://github.com/PyFlashLogger
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

import json
import logging
import os
import shutil
from enum import auto
from pathlib import Path

from fundamentals.extended_enum import ExtendedEnum


def get_user_config_dir() -> Path:
    """Get the user configuration directory, creating it if needed.
    
    Cross-platform: Uses appropriate user config directory for each OS:
    - Linux: ~/.config/flashlogger (or $XDG_CONFIG_HOME/flashlogger)
    - macOS: ~/.config/flashlogger
    - Windows: %APPDATA%/flashlogger
    """
    import platform
    system = platform.system()
    
    if system == 'Windows':
        # Windows: use APPDATA environment variable
        config_home = os.environ.get('APPDATA', os.path.expanduser('~'))
        user_config_dir = Path(config_home) / 'flashlogger'
    elif system == 'Darwin':
        # macOS: use ~/.config (standard XDG location on macOS)
        config_home = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
        user_config_dir = Path(config_home) / 'flashlogger'
    else:
        # Linux and others: use XDG_CONFIG_HOME or ~/.config
        config_home = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
        user_config_dir = Path(config_home) / 'flashlogger'
    
    if not user_config_dir.exists():
        user_config_dir.mkdir(parents=True, exist_ok=True)
    return user_config_dir


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
        :raises ValueError: no free custom slot available
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
    def load_str_reprs_from_json(cls, json_file_path: str | Path, update_active_link: bool = False) -> None:
        """
        Load string representations from a JSON file.
        :param json_file_path: path to the JSON file
        :param update_active_link: if True, update the strings/active symlink to point to this file
        """

        with open(json_file_path, "r", encoding="utf-8") as f:
            str_map_data = json.load(f)

        # Load all string representations from the JSON file
        # Map LogLevel enum members where possible
        str_map = {}
        for level_name, representation in str_map_data.items():
            level_name_upper = level_name.upper()
            if hasattr(cls, level_name_upper):
                str_map[getattr(cls, level_name_upper)] = representation
            else:
                # For non-LogLevel keys (like field names), store with original case
                str_map[level_name] = representation

        LogLevel.custom_str_map.update(str_map)

        # Update active symlink if requested
        if update_active_link:
            factory_config_dir = Path(__file__).parent / "config"
            user_config_dir = get_user_config_dir()
            
            # Use the strings/active symlink location in user config
            active_link = user_config_dir / "strings" / "active"
            source_file = Path(json_file_path).resolve()

            # Determine which folder the source is in (factory, user, or elsewhere)
            if str(user_config_dir) in str(source_file):
                # Source is in user config folder - link directly
                target_path = source_file
            elif "factory" in str(source_file):
                # Source is in factory folder - copy to user config and link there
                user_strings_dir = user_config_dir / "strings"
                user_strings_dir.mkdir(parents=True, exist_ok=True)
                target_path = user_strings_dir / source_file.name
                shutil.copy2(source_file, target_path)
            else:
                # Source is elsewhere - copy to user config and link there
                user_strings_dir = user_config_dir / "strings"
                user_strings_dir.mkdir(parents=True, exist_ok=True)
                target_path = user_strings_dir / source_file.name
                shutil.copy2(source_file, target_path)

            # Ensure directories exist
            active_link.parent.mkdir(parents=True, exist_ok=True)
            
            # Remove existing symlink if it exists
            if active_link.exists() or active_link.is_symlink():
                active_link.unlink(missing_ok=True)

            # Create absolute symlink to the target in user config
            try:
                active_link.symlink_to(target_path)
            except OSError:
                # If symlink creation fails, just copy the file
                shutil.copy2(target_path, active_link)

    @classmethod
    def load_custom_levels_from_json(cls, json_file_path: str | Path) -> None:
        """
        Load custom level logging numbers from a JSON file.
        :param json_file_path: path to the JSON file containing custom level logging numbers
        """
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        custom_levels = data.get("custom_levels", {})

        for custom_name, config in custom_levels.items():
            level_num = int(config["logging_level"])

            # Update custom_levels array with the logging level
            if custom_name.startswith("custom"):
                try:
                    index = int(custom_name[6:])  # Extract number from "custom0"
                    if 0 <= index < len(cls.custom_levels):
                        cls.custom_levels[index] = level_num
                except ValueError:
                    continue

    @classmethod
    def save_custom_levels_to_json(cls, json_file_path: str | Path) -> None:
        """
        Save custom level logging numbers to a JSON file.
        :param json_file_path: path to save the JSON file
        """
        # Build custom levels configuration
        custom_levels_data = {}
        for i in range(len(cls.custom_levels)):
            custom_name = f"custom{i}"
            logging_level = cls.custom_levels[i]
            custom_levels_data[custom_name] = {
                "logging_level": logging_level
            }

        data = {"custom_levels": custom_levels_data}

        # Save to file
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    @classmethod
    def save_str_reprs_to_json(cls, json_file_path: str | Path) -> None:
        """
        Save custom string representations to a JSON file.
        :param json_file_path: path to save the JSON file
        """
        # Build a dictionary mapping level/field names to representations
        str_map_data = {}
        for level, representation in cls.custom_str_map.items():
            if hasattr(level, "name"):
                # It's a LogLevel enum member
                level_name = level.name.lower()
            else:
                # It's a string key (field name)
                level_name = str(level)
            str_map_data[level_name] = representation

        # Save to file
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(str_map_data, f, indent=2, sort_keys=True)

    def __str__(self) -> str:
        return LogLevel.custom_str_map.get(self, self.name.lower())


# Initialize custom logging levels (negative = unconfigured but distinct)
LogLevel.custom_levels = [
    -1,  # CUSTOM0 - will be loaded from custom_levels.json
    -2,  # CUSTOM1
    -3,  # CUSTOM2
    -4,  # CUSTOM3
    -5,  # CUSTOM4
    -6,  # CUSTOM5
    -7,  # CUSTOM6
    -8,  # CUSTOM7
    -9,  # CUSTOM8
    -10,  # CUSTOM9
]

# Initialize custom level configurations
LogLevel.custom_level_configs = {}

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

# Load default configurations on module import
try:
    # Get config directory relative to this file
    factory_config_dir = Path(__file__).parent / "config"
    # Get user config directory (~/.config/flashlogger)
    user_config_dir = get_user_config_dir()

    # Load custom level configurations - check user config first, then factory
    user_levels_link = user_config_dir / "levels" / "active"
    if user_levels_link.exists():
        try:
            LogLevel.load_custom_levels_from_json(str(user_levels_link))
        except Exception:
            pass
    else:
        # Fall back to factory config
        factory_levels_link = factory_config_dir / "levels" / "active"
        if factory_levels_link.exists():
            try:
                LogLevel.load_custom_levels_from_json(str(factory_levels_link))
            except Exception:
                pass

    # Load string representations - check user config first, then factory
    user_strings_link = user_config_dir / "strings" / "active"
    if user_strings_link.exists():
        try:
            LogLevel.load_str_reprs_from_json(str(user_strings_link))
        except Exception:
            pass
    else:
        # Fall back to factory config
        factory_strings_link = factory_config_dir / "strings" / "active"
        if factory_strings_link.exists():
            try:
                LogLevel.load_str_reprs_from_json(str(factory_strings_link))
            except Exception:
                pass
except Exception:
    # If loading fails, continue with defaults (don't crash import)
    pass
