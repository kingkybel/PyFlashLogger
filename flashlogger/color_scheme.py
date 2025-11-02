# Repository:   https://github.com/PyFlashLogger
# File Name:    flashlogger/color_scheme.py
# Description:  color schemes for logger handling different log-levels etc
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
# @date: 2025-11-02
# @author: Dieter J Kybelksties

from __future__ import annotations

import json
import os
from enum import auto
from pathlib import Path

from colorama import init as colorama_init, Fore, Back, Style
from fundamentals import ExtendedEnum

from flashlogger.log_levels import LogLevel

colorama_init()


class Field(ExtendedEnum):
    """Special field types for color schemes."""
    OPERATOR = auto()
    TIMESTAMP = auto()
    PID = auto()
    TID = auto()
    FILE = auto()
    LEVEL = auto()
    MESSAGE = auto()


class ColorScheme:
    """
    Simplified color scheme management for console logging.

    This class provides ANSI color codes for different log levels and formatting elements.
    Each level has foreground and background colors that can be combined with optional styling.

    Available default schemes:
    - COLOR: Full color scheme with ANSI color codes (default)
    - BLACK_AND_WHITE: Monochrome color scheme using only white/black tones
    - PLAIN_TEXT: No ANSI colors at all - plain text output

    Custom color schemes can be loaded by providing a custom JSON file path:

        custom_scheme = ColorScheme(colorscheme_json=Path("/path/to/custom.json"))

    JSON Configuration Format:
    {
      "operator": {"foreground": "YELLOW", "background": "BLACK"},
      "timestamp": {"foreground": "CYAN", "background": "BLACK"},
      "pid": {"foreground": "CYAN", "background": "BLACK"},
      "tid": {"foreground": "CYAN", "background": "BLACK"},
      "file": {"foreground": "GREEN", "background": "BLACK"},
      "level": {"foreground": "YELLOW", "background": "BLACK"},
      "message": {"foreground": "WHITE", "background": "BLACK"},
      "debug": {"foreground": "BLUE", "background": "BLACK"},
      "info": {"foreground": "GREEN", "background": "BLACK"},
      "warning": {"foreground": "YELLOW", "background": "BLACK"},
      ...
    }

    Use get(level, inverse=False, style=Style.NORMAL) to get the combined ANSI color code.
    """

    class Default(ExtendedEnum):
        NONE = auto()
        BLACK_AND_WHITE = auto()
        COLOR = auto()
        PLAIN_TEXT = auto()

    def __init__(self, default_scheme: ColorScheme.Default = Default.COLOR, colorscheme_json: Path = None):
        """
        Initialize the color scheme.
        :param default_scheme: the default color scheme to use
        :param colorscheme_json: optional path to custom color scheme JSON file
        """
        # Initialize all levels with their foreground and background colors

        # Field levels (used by formatters)
        self.operator_foreground = None
        self.operator_background = None
        self.operator_foreground_inverse = None
        self.operator_background_inverse = None
        self.timestamp_foreground = None
        self.timestamp_background = None
        self.timestamp_foreground_inverse = None
        self.timestamp_background_inverse = None
        self.pid_foreground = None
        self.pid_background = None
        self.pid_foreground_inverse = None
        self.pid_background_inverse = None
        self.tid_foreground = None
        self.tid_background = None
        self.tid_foreground_inverse = None
        self.tid_background_inverse = None
        self.file_foreground = None
        self.file_background = None
        self.file_foreground_inverse = None
        self.file_background_inverse = None
        self.level_foreground = None
        self.level_background = None
        self.level_foreground_inverse = None
        self.level_background_inverse = None
        self.message_foreground = None
        self.message_background = None
        self.message_foreground_inverse = None
        self.message_background_inverse = None

        # Log levels
        for log_level in LogLevel:
            level_str = log_level.name.lower()
            setattr(self, f"{level_str}_foreground", None)
            setattr(self, f"{level_str}_background", None)
            setattr(self, f"{level_str}_foreground_inverse", None)
            setattr(self, f"{level_str}_background_inverse", None)

        # Define all levels that have colors
        field_levels = ["timestamp", "pid", "tid", "file", "level", "message"]
        log_levels = [log_level.name.lower() for log_level in LogLevel]
        self.all_levels = field_levels + log_levels

        if colorscheme_json:
            self._load_from_config(colorscheme_json)
        else:
            self._load_default_scheme(default_scheme)

    def get(self, level: str | LogLevel | Field, inverse: bool = False, style: str = Style.NORMAL) -> str:
        """
        Get the combined ANSI color code for the given level.

        :param level: the level name as string, LogLevel enum, or Field enum
                     (e.g., "info", LogLevel.INFO, Field.TIMESTAMP, "timestamp")
        :param inverse: if True, use inverse colors for this level
        :param style: ANSI style to apply
        :return: combined ANSI color code
        """
        # Convert level parameter to string
        if isinstance(level, LogLevel):
            level_str = level.name.lower()
        elif isinstance(level, Field):
            level_str = level.name.lower()
        else:
            level_str = str(level).lower()

        # Validate that it's a known level
        if level_str not in self.all_levels:
            # For backward compatibility, allow any string
            pass

        if inverse:
            fg_attr = f"{level_str}_foreground_inverse"
            bg_attr = f"{level_str}_background_inverse"
        else:
            fg_attr = f"{level_str}_foreground"
            bg_attr = f"{level_str}_background"

        foreground = getattr(self, fg_attr, None)
        background = getattr(self, bg_attr, None)

        if not style:
            style = Style.NORMAL
        reval = style
        if foreground:
            reval += foreground
        if background:
            reval += background

        return reval

    def _create_color_scheme(self):
        """Create the default color scheme."""
        # Field colors
        self.operator_foreground = Fore.YELLOW
        self.operator_background = None
        self.operator_foreground_inverse = None
        self.operator_background_inverse = Back.YELLOW
        self.timestamp_foreground = Fore.CYAN
        self.timestamp_background = None
        self.timestamp_foreground_inverse = None
        self.timestamp_background_inverse = Back.CYAN
        self.pid_foreground = Fore.CYAN
        self.pid_background = None
        self.pid_foreground_inverse = None
        self.pid_background_inverse = Back.CYAN
        self.tid_foreground = Fore.CYAN
        self.tid_background = None
        self.tid_foreground_inverse = None
        self.tid_background_inverse = Back.CYAN
        self.file_foreground = Fore.GREEN
        self.file_background = None
        self.file_foreground_inverse = None
        self.file_background_inverse = Back.GREEN
        self.level_foreground = Fore.YELLOW
        self.level_background = None
        self.level_foreground_inverse = None
        self.level_background_inverse = Back.YELLOW
        self.message_foreground = Fore.WHITE
        self.message_background = None
        self.message_foreground_inverse = None
        self.message_background_inverse = Back.WHITE

        # Log level colors
        self.debug_foreground = Fore.BLUE
        self.debug_background = None
        self.debug_foreground_inverse = Fore.WHITE
        self.debug_background_inverse = Back.BLUE
        self.info_foreground = Fore.GREEN
        self.info_background = None
        self.info_foreground_inverse = None
        self.info_background_inverse = Back.GREEN
        self.warning_foreground = Fore.YELLOW
        self.warning_background = None
        self.warning_foreground_inverse = None
        self.warning_background_inverse = Back.YELLOW
        self.error_foreground = Fore.RED
        self.error_background = None
        self.error_foreground_inverse = Fore.WHITE
        self.error_background_inverse = Back.RED
        self.critical_foreground = Fore.RED
        self.critical_background = Back.YELLOW
        self.critical_foreground_inverse = Fore.YELLOW
        self.critical_background_inverse = Back.RED
        self.fatal_foreground = Fore.RED
        self.fatal_background = Back.YELLOW
        self.fatal_foreground_inverse = Fore.YELLOW
        self.fatal_background_inverse = Back.RED
        self.notset_foreground = Fore.WHITE
        self.notset_background = None
        self.notset_foreground_inverse = None
        self.notset_background_inverse = Back.WHITE

        # Set custom log levels to same as info
        for i in range(10):
            setattr(self, f"custom{i}_foreground", Fore.GREEN)
            setattr(self, f"custom{i}_background", None)
            setattr(self, f"custom{i}_foreground_inverse", None)
            setattr(self, f"custom{i}_background_inverse", Back.GREEN)

        # Set command levels
        for level in ("command", "command_output", "command_stderr"):
            setattr(self, f"{level}_foreground", Fore.MAGENTA)
            setattr(self, f"{level}_background", None)
            setattr(self, f"{level}_foreground_inverse", None)
            setattr(self, f"{level}_background_inverse", Back.MAGENTA)

    def _load_default_scheme(self, default_scheme: ColorScheme.Default):
        """Load the default color scheme from config directory."""
        # Map default scheme to config file
        scheme_files = {
            ColorScheme.Default.COLOR: "color_scheme_color.json",
            ColorScheme.Default.BLACK_AND_WHITE: "color_scheme_bw.json",
            ColorScheme.Default.PLAIN_TEXT: "color_scheme_plain.json"
        }

        # Handle None as default (should be COLOR)
        if default_scheme is None:
            default_scheme = ColorScheme.Default.COLOR

        if default_scheme not in scheme_files:
            raise ValueError(f"Unknown default color scheme: {default_scheme}")

        # Get config directory
        config_dir = Path(__file__).parent / "config"

        if default_scheme == ColorScheme.Default.NONE:
            # Load from active color scheme
            active_file = os.path.join(config_dir, "active_color_scheme.json")
            self._load_from_config(Path(active_file))
            return

        # Load from specific scheme file
        scheme_file = os.path.join(config_dir, scheme_files[default_scheme])
        self._load_from_config(Path(scheme_file))

        # Update symlink if needed
        active_file = os.path.join(config_dir, "active_color_scheme.json")
        active_target = os.path.realpath(active_file) if os.path.exists(active_file) else None

        if active_target != scheme_file:
            # Update symlink
            if os.path.exists(active_file) or os.path.islink(active_file):
                os.unlink(active_file)
            os.symlink(scheme_file, active_file)

    def _create_black_and_white_scheme(self):
        """Create a black and white color scheme."""
        # Field colors
        self.operator_foreground = Fore.WHITE
        self.operator_background = Back.BLACK
        self.operator_foreground_inverse = Fore.BLACK
        self.operator_background_inverse = Back.WHITE
        self.timestamp_foreground = Fore.WHITE
        self.timestamp_background = Back.BLACK
        self.timestamp_foreground_inverse = Fore.BLACK
        self.timestamp_background_inverse = Back.WHITE
        self.pid_foreground = Fore.WHITE
        self.pid_background = Back.BLACK
        self.pid_foreground_inverse = Fore.BLACK
        self.pid_background_inverse = Back.WHITE
        self.tid_foreground = Fore.WHITE
        self.tid_background = Back.BLACK
        self.tid_foreground_inverse = Fore.BLACK
        self.tid_background_inverse = Back.WHITE
        self.file_foreground = Fore.WHITE
        self.file_background = Back.BLACK
        self.file_foreground_inverse = Fore.BLACK
        self.file_background_inverse = Back.WHITE
        self.level_foreground = Fore.WHITE
        self.level_background = Back.BLACK
        self.level_foreground_inverse = Fore.BLACK
        self.level_background_inverse = Back.WHITE
        self.message_foreground = Fore.WHITE
        self.message_background = Back.BLACK
        self.message_foreground_inverse = Fore.BLACK
        self.message_background_inverse = Back.WHITE

        # Log level colors (all white on black)
        for log_level in LogLevel:
            level_str = log_level.name.lower()
            setattr(self, f"{level_str}_foreground", Fore.WHITE)
            setattr(self, f"{level_str}_background", Back.BLACK)
            setattr(self, f"{level_str}_foreground_inverse", Fore.BLACK)
            setattr(self, f"{level_str}_background_inverse", Back.WHITE)

    def _load_from_config(self, config_file: Path):
        """Load color scheme from JSON file."""
        with open(config_file, encoding="utf-8") as f:
            data = json.load(f)

        # Set colors for each level in the config
        for level_name, colors in data.items():
            fg_str = colors.get("foreground")
            bg_str = colors.get("background")
            fg_inv_str = bg_str
            bg_inv_str = fg_str

            # Convert color names to ANSI codes
            foreground = getattr(Fore, fg_str) if fg_str else None
            background = getattr(Back, bg_str) if bg_str else None
            foreground_inverse = getattr(Fore, fg_inv_str) if fg_inv_str else None
            background_inverse = getattr(Back, bg_inv_str) if bg_inv_str else None

            setattr(self, f"{level_name}_foreground", foreground)
            setattr(self, f"{level_name}_background", background)
            setattr(self, f"{level_name}_foreground_inverse", foreground_inverse)
            setattr(self, f"{level_name}_background_inverse", background_inverse)
