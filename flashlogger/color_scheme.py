# Repository:   https://github.com/PyFlashLogger
# File Name:    flashlogger/color_scheme.py
# Description:  color schemes for logger handling different log-levels etc
#
# Copyright (C) 2024 Dieter J Kybelksties <github@kybelksties.com>
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
import shutil
from enum import auto
from pathlib import Path

from colorama import init as colorama_init, Fore, Back, Style
from fundamentals.extended_enum import ExtendedEnum

from flashlogger.log_levels import LogLevel

colorama_init()


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
    - LIGHT_BG_BLACK_AND_WHITE: Black and white color scheme for light background
    - LIGHT_BG_COLOR: Full color scheme for light background

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
        LIGHT_BG_BLACK_AND_WHITE = auto()
        LIGHT_BG_COLOR = auto()

    def __init__(self,
                 default_scheme: ColorScheme.Default = Default.COLOR,
                 colorscheme_json: Path = None,
                 update_active_link: bool = False):
        """
        Initialize the color scheme.
        :param default_scheme: the default color scheme to use
        :param colorscheme_json: optional path to custom color scheme JSON file
        :param update_active_link: if True and colorscheme_json is provided, update the active_display.json symlink
        """

        if default_scheme and not isinstance(default_scheme, ColorScheme.Default):
            raise ValueError(f"Invalid Default-color-scheme: '{default_scheme}'")
        field_levels = ["operator", "timestamp", "pid", "tid", "file", "level", "message"]
        log_levels = [log_level.name.lower() for log_level in LogLevel]
        self.all_levels = field_levels + log_levels

        # Set all colors to default
        for level_str in self.all_levels:
            setattr(self, f"{level_str}_foreground", None)
            setattr(self, f"{level_str}_background", None)
            setattr(self, f"{level_str}_foreground_inverse", None)
            setattr(self, f"{level_str}_background_inverse", None)

        if colorscheme_json:
            # explicit path provided by caller
            self._load_from_config(colorscheme_json, update_active_link)
        else:
            # if the user has a config file, always load that first (overrides factory defaults)
            user_active = get_user_config_dir() / "colors" / "active"
            if user_active.exists():
                try:
                    self._load_from_config(user_active)
                    return
                except Exception:
                    # fall back to factory defaults on failure
                    pass

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
        if isinstance(level, (LogLevel, Field)):
            level_str = level.name.lower()
        else:
            level_str = str(level).lower()

        # Validate that it's a known level
        if level_str not in self.all_levels:
            # For backward compatibility, allow any string
            pass

        fg_attr = f"{level_str}_foreground{'_inverse' if inverse else ''}"
        bg_attr = f"{level_str}_background{'_inverse' if inverse else ''}"

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

    def _load_default_scheme(self, default_scheme: ColorScheme.Default):
        """Load the default color scheme from config directory."""
        # Map default scheme to config file
        scheme_files = {
            ColorScheme.Default.NONE: "colors/active",  # Uses symlink
            ColorScheme.Default.COLOR: "colors/factory/display_dark_bg_color.json",
            ColorScheme.Default.BLACK_AND_WHITE: "colors/factory/display_dark_bg_bw.json",
            ColorScheme.Default.PLAIN_TEXT: "colors/factory/display_plain.json",
            ColorScheme.Default.LIGHT_BG_COLOR: "colors/factory/display_light_bg_color.json",
            ColorScheme.Default.LIGHT_BG_BLACK_AND_WHITE: "colors/factory/display_light_bg_bw.json"
        }

        # Handle None as default (should be COLOR)
        if default_scheme is None:
            default_scheme = ColorScheme.Default.COLOR

        if default_scheme not in scheme_files:
            raise ValueError(f"Unknown default color scheme: {default_scheme}")

        # Get factory and user config directories
        factory_config_dir = Path(__file__).parent / "config"
        user_config_dir = get_user_config_dir()
        user_colors_dir = user_config_dir / "colors"

        if default_scheme == ColorScheme.Default.NONE:
            # prefer user active symlink if present
            user_active = user_colors_dir / "active"
            if user_active.exists():
                self._load_from_config(user_active)
                return

            # Load from factory active symlink
            active_file = factory_config_dir / "colors" / "active"
            self._load_from_config(Path(active_file))
            return

        # determine scheme file names without the factory prefix
        scheme_name = Path(scheme_files[default_scheme]).name

        # first try user override file (same name under ~/.config/flashlogger/colors)
        user_file = user_colors_dir / scheme_name
        if user_file.exists():
            self._load_from_config(user_file)
            return

        # fall back to factory config
        scheme_file = factory_config_dir / scheme_files[default_scheme]
        self._load_from_config(Path(scheme_file))

        # Update symlink if needed - point colors/active to this scheme
        active_link = factory_config_dir / "colors" / "active"
        active_target = os.path.realpath(active_link) if active_link.exists() else None

        if active_target != str(scheme_file):
            # Update symlink with relative path
            if active_link.exists() or active_link.is_symlink():
                active_link.unlink(missing_ok=True)
            rel_path = os.path.relpath(scheme_file, factory_config_dir / "colors")
            active_link.symlink_to(rel_path)

    def _load_from_config(self, config_file: Path, update_active_link: bool = False):
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

        # Update active symlink if requested
        if update_active_link:
            # Get factory config directory
            factory_config_dir = Path(__file__).parent / "config"
            # Get user config directory (~/.config/flashlogger)
            user_config_dir = get_user_config_dir()
            
            # Use the colors/active symlink location
            active_link = factory_config_dir / "colors" / "active"
            source_file = Path(config_file).resolve()

            # Determine which folder the source is in (factory, user, or elsewhere)
            if str(user_config_dir) in str(source_file):
                # Source is in user config folder - link directly
                target_path = source_file
            elif "factory" in str(source_file):
                # Source is in factory folder - copy to user config and link there
                # Create user colors directory
                user_colors_dir = user_config_dir / "colors"
                user_colors_dir.mkdir(parents=True, exist_ok=True)
                target_path = user_colors_dir / source_file.name
                shutil.copy2(source_file, target_path)
            else:
                # Source is elsewhere - copy to user config and link there
                user_colors_dir = user_config_dir / "colors"
                user_colors_dir.mkdir(parents=True, exist_ok=True)
                target_path = user_colors_dir / source_file.name
                shutil.copy2(source_file, target_path)

            # Remove existing link if it exists
            if active_link.exists() or active_link.is_symlink():
                active_link.unlink(missing_ok=True)

            # Create absolute symlink to the target in user config
            try:
                active_link.symlink_to(target_path)
            except OSError:
                # If symlink creation fails, just copy the file
                shutil.copy2(target_path, active_link)
