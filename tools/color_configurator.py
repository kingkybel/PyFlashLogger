#!/usr/bin/env python3
"""
Simplified Color Configuration Tool

Interactive tool for customizing logging colors with foreground/background only.
Can load from and save to JSON configuration files.

Usage:
    python color_configurator.py [colors.json]

Author: Dieter J Kybelksties
"""
from __future__ import annotations

import json
import os
import readline
import sys
from pathlib import Path
import shutil

from fundamentals.extended_enum import ExtendedEnumError


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

COMMAND_LIST = ["quit", "save", "load", "new", "reset"]

COLOR_STRINGS = [
    "BLACK", "RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE",
    "LIGHTBLACK_EX", "LIGHTRED_EX", "LIGHTGREEN_EX", "LIGHTYELLOW_EX",
    "LIGHTBLUE_EX", "LIGHTMAGENTA_EX", "LIGHTCYAN_EX", "LIGHTWHITE_EX"
]

# Import from FlashLogger package
try:
    from flashlogger.color_scheme import ColorScheme
    from flashlogger.log_levels import LogLevel
    from flashlogger.flash_logger import FlashLogger
    from flashlogger.log_channel_console import ConsoleFormatter
    from colorama import Fore, Back, Style, init
except ImportError:
    # Fallback for local development
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from flashlogger.color_scheme import ColorScheme
    from flashlogger.log_levels import LogLevel
    from flashlogger.flash_logger import FlashLogger
    from flashlogger.log_channel_console import ConsoleFormatter
    from colorama import Fore, Back, Style, init

init(autoreset=False)


class ColorConfigurator:
    """Interactive tool for simplified configuring of colors."""

    def __init__(self, color_file=None, label_file=None):
        self._sorted_level_info = None
        # Factory config directory (package defaults)
        self.factory_config_dir = Path(__file__).parent.parent / "flashlogger" / "config"
        # User config directory (~/.config/flashlogger on Linux/macOS, %APPDATA%/flashlogger on Windows)
        self.user_config_dir = get_user_config_dir()
        
        # Use user config dir for saving, factory for loading defaults
        self.config_dir = self.user_config_dir

        # Use provided color file or default (use colors/active in user config first, then factory)
        if color_file:
            self.color_file = Path(color_file)
        else:
            # Check user config first, then fall back to factory
            user_active = self.user_config_dir / "colors" / "active"
            factory_active = self.factory_config_dir / "colors" / "active"
            if user_active.exists():
                self.color_file = user_active
            else:
                self.color_file = factory_active

        if self.color_file.exists():
            print(f"{Style.RESET_ALL}Loading colors from: {self.color_file}")
            self.color_scheme = ColorScheme(colorscheme_json=self.color_file)
        else:
            print(f"{Style.RESET_ALL}Loading default colors")
            self.color_scheme = ColorScheme()

        if label_file:
            self.label_file = Path(label_file)
        else:
            # Check user config first, then fall back to factory
            user_active = self.user_config_dir / "strings" / "active"
            factory_active = self.factory_config_dir / "strings" / "active"
            if user_active.exists():
                self.label_file = user_active
            else:
                self.label_file = factory_active

        if self.label_file.exists():
            print(f"{Style.RESET_ALL}Loading labels from: {self.label_file}")
            LogLevel.load_str_reprs_from_json(self.label_file)

        self.changed = False
        self._collect_schemes()

        # Enable tab completion
        readline.parse_and_bind("tab: complete")
        readline.set_completer_delims(" \t\n;")
        readline.set_completer(self._completer)

    def run(self):
        """Run the interactive configurator."""
        print(f"{Style.RESET_ALL}🎨 Color Configurator")
        print("=" * 40)
        self.main_loop()

    def main_loop(self):
        """Main input loop for commands."""
        self._print_help()

        while True:
            try:
                cmd_line = input(f"{Style.RESET_ALL}\nCommand: ").strip()
                if not cmd_line:
                    self.display_levels()
                    continue

                if not self._process_command(cmd_line):
                    break

            except KeyboardInterrupt:
                self.confirm_save_and_quit()
                break

    def _print_help(self):
        """Print command help."""
        print(f"{Style.RESET_ALL}Commands: q)uit, s)ave, lo)ad [colorscheme|stringdefs] <scheme>, new <name> [l)abels | c)olors], re)set")
        print(
            f"{Style.RESET_ALL}<Enter> displays current colors, reset customlevels|colors|labels (always replaces with factory defaults)")

    def _process_command(self, command):
        """Process a command and return True to continue, False to exit."""
        parts = command.split(" ")
        input_cmd = parts[0].lower()

        # Find matching commands using substring fuzzy matching
        command_mapping = {
            "quit": self._handle_quit,
            "save": self._handle_save,
            "load": self._handle_load,
            "new": self._handle_new,
            "reset": self._handle_reset,
        }

        # Find commands that contain the input as a substring
        matching_commands = [
            cmd_type for cmd_type in command_mapping.keys()
            if input_cmd in cmd_type  # input_cmd is substring of cmd_type
        ]

        if input_cmd.isdigit():
            # change the colors for this line
            self._handle_level_edit(parts)
            return True

        if not matching_commands:
            # Try level name matching for direct color editing (e.g., "error red blue")
            level_name = input_cmd.upper()
            if hasattr(LogLevel, level_name) or level_name in self.color_scheme.all_levels:
                return self._handle_level_by_name(parts)
            print("❌ Invalid command.")
            return True

        if len(matching_commands) == 1:
            # Exact match - execute
            return command_mapping[matching_commands[0]](parts)

        # Multiple matches - show ambiguity
        print(f"❌ Ambiguous command '{input_cmd}'. Could match: {', '.join(matching_commands)}")
        return True

    def _handle_quit(self, _):
        """Handle quit command."""
        self.confirm_save_and_quit()
        return False

    def _handle_save(self, _):
        """Handle save command."""
        self.save_configuration()
        return True

    def _handle_load(self, parts):
        """Handle load command with improved UX: load [type] [scheme]"""
        if len(parts) == 1:
            # No args: list all schemes
            self.list_schemes()
        elif len(parts) == 2:
            # One arg: check if it's a type or a scheme
            arg = parts[1].lower()
            if arg in ['colorscheme', 'colors', 'color']:
                self.list_color_schemes()
            elif arg in ['stringdefs', 'strings', 'labels', 'label']:
                self.list_label_schemes()
            else:
                # Assume it's a scheme name
                self.load_scheme(arg)
        elif len(parts) == 3:
            # Two args: type and scheme
            type_arg = parts[1].lower()
            scheme_arg = parts[2]
            if type_arg in ['colorscheme', 'colors', 'color']:
                self.load_color_scheme(scheme_arg)
            elif type_arg in ['stringdefs', 'strings', 'labels', 'label']:
                self.load_label_scheme(scheme_arg)
            else:
                print("❌ Invalid type. Use 'colorscheme' or 'stringdefs'")
        else:
            print("❌ Usage: load [type] [scheme]")
        return True

    def _handle_new(self, parts):
        """Handle new scheme command."""
        if len(parts) > 1:
            name = parts[1]
            schema_type = "color"
            if len(parts) > 2 and parts[2].startswith("l"):
                schema_type = "label"
            self.create_new_scheme(name, schema_type)
        else:
            print("❌ Provide scheme name: new <name> <type=color|labels>")
        return True

    def _handle_list(self, _):
        """Handle list command."""
        self.display_levels()
        return True

    def _handle_reset(self, parts):
        """Handle reset command for customlevels|colors|labels with fuzzy matching."""
        if len(parts) < 2:
            print("❌ Reset what? Usage: reset customlevels|colors|labels")
            return True

        reset_type = parts[1].lower()

        # Find reset type using fuzzy substring matching against valid types
        valid_reset_types = ['customlevels', 'colors', 'labels', 'custom', 'color', 'label', 'strings']

        # Find all valid types that contain the input as substring
        matching_types = []
        for valid_type in valid_reset_types:
            if reset_type in valid_type:
                # Map to normalized type
                if valid_type in {'customlevels', 'custom'}:
                    normalized_type = 'customlevels'
                elif valid_type in {'colors', 'color'}:
                    normalized_type = 'colors'
                else:  # 'labels', 'label', 'strings'
                    normalized_type = 'labels'

                if normalized_type not in matching_types:
                    matching_types.append(normalized_type)

        if not matching_types:
            print(f"❌ Invalid reset type '{reset_type}'. Use: customlevels, colors, or labels")
            return True
        if len(matching_types) > 1:
            print(f"❌ Ambiguous reset type '{reset_type}'. Could match: {', '.join(matching_types)}")
            return True

        matched_reset_type = matching_types[0]

        if matched_reset_type == 'customlevels':
            # Reset custom levels - copy factory to custom and update symlink
            factory_file = self.factory_config_dir / "levels" / "factory" / "default_custom_levels.json"
            user_active_link = self.user_config_dir / "levels" / "active"

            if factory_file.exists():
                # Copy factory to user custom directory
                user_custom_dir = self.user_config_dir / "levels" / "custom"
                user_custom_dir.mkdir(parents=True, exist_ok=True)
                user_custom_file = user_custom_dir / "custom_levels.json"
                shutil.copy2(factory_file, user_custom_file)
                
                # Update user symlink to point to custom
                user_active_link.parent.mkdir(parents=True, exist_ok=True)
                user_active_link.unlink(missing_ok=True)
                user_active_link.symlink_to("custom/custom_levels.json")
                
                print("✅ Custom levels reset to factory defaults")

                # Reload configuration
                LogLevel.load_custom_levels_from_json(str(user_custom_file))
            else:
                print("❌ Factory defaults not found")

        elif matched_reset_type == 'colors':
            # Reset color scheme - copy factory to user config and update symlink
            factory_file = self.factory_config_dir / "colors" / "factory" / "display_dark_bg_color.json"
            user_active_link = self.user_config_dir / "colors" / "active"

            if factory_file.exists():
                # Copy factory to user custom directory
                user_custom_dir = self.user_config_dir / "colors" / "custom"
                user_custom_dir.mkdir(parents=True, exist_ok=True)
                user_custom_file = user_custom_dir / "display_dark_bg_color.json"
                shutil.copy2(factory_file, user_custom_file)
                
                # Update user symlink
                user_active_link.parent.mkdir(parents=True, exist_ok=True)
                user_active_link.unlink(missing_ok=True)
                user_active_link.symlink_to("custom/display_dark_bg_color.json")

                print("✅ Colors reset to factory defaults (dark background color scheme)")
                # Reload the color scheme
                self.color_scheme = ColorScheme()
            else:
                print("❌ Factory defaults not found")

        elif matched_reset_type == 'labels':
            # Reset language labels - copy factory to user config and update symlink
            factory_file = self.factory_config_dir / "strings" / "factory" / "strings_en.json"
            user_active_link = self.user_config_dir / "strings" / "active"

            if factory_file.exists():
                # Copy factory to user custom directory
                user_custom_dir = self.user_config_dir / "strings" / "custom"
                user_custom_dir.mkdir(parents=True, exist_ok=True)
                user_custom_file = user_custom_dir / "strings_en.json"
                shutil.copy2(factory_file, user_custom_file)
                
                # Update user symlink
                user_active_link.parent.mkdir(parents=True, exist_ok=True)
                user_active_link.unlink(missing_ok=True)
                user_active_link.symlink_to("custom/strings_en.json")

                print("✅ Language labels reset to factory defaults (English)")
                # Reload the language strings
                LogLevel.load_str_reprs_from_json(str(user_custom_file))
            else:
                print("❌ Factory defaults not found")

        return True

    def _handle_level_by_name(self, parts):
        """Handle level editing by level name (e.g., 'error red blue')."""
        level_name = parts[0].upper()

        # Check if it's a valid LogLevel enum name or a level in the color scheme
        actual_level_name = None
        try:
            _ = LogLevel.from_string(level_name)
            actual_level_name = level_name
        except ExtendedEnumError:
            # Not a LogLevel, check if it's in the color scheme
            if level_name in self.color_scheme.all_levels:
                actual_level_name = level_name
            else:
                print(f"❌ Unknown level: {level_name}")
                return True

        if len(parts) == 1:
            # Only level name provided - go to interactive mode
            self.edit_level_colors(actual_level_name)
        elif len(parts) == 2:
            # Level name + one parameter (could be new level for custom or color for regular)
            if actual_level_name.startswith("CUSTOM"):
                # For custom levels: levelname <new_level> or levelname -
                param = parts[1]
                if param == '-':
                    self.reset_custom_level(actual_level_name)
                elif param.isdigit():
                    new_level = int(param)
                    if new_level > 0:
                        self.adjust_custom_level(actual_level_name, new_level)
                    else:
                        print("❌ Custom level must be a positive integer.")
                else:
                    print(f"❌ Invalid parameter for custom level: {param}")
            else:
                # For regular levels: treat as foreground color with default/no background
                self.edit_level_colors(actual_level_name, parts[1], "_")
        elif len(parts) >= 3:
            # Level name + foreground + background (+ optional label)
            fg_part = parts[1]
            bg_part = parts[2]
            label_part = parts[3] if len(parts) >= 4 else "_"
            self.edit_level_colors(actual_level_name, fg_part, bg_part, label_part)

        return True

    def _handle_level_edit(self, parts):
        """Handle level editing commands."""
        sequential_num = int(parts[0])
        level_info = self._get_level_by_sequential_number(sequential_num)

        if not level_info:
            print("❌ Could not find level for sequential number.")
            return True

        level_name, display_label, level_number_str, sort_key = level_info

        # Handle custom levels
        if level_number_str.strip().startswith('-'):
            self._handle_custom_level_edit(sequential_num, parts, level_name)
            return True

        # Handle regular levels
        self._handle_regular_level_edit(parts, level_name)
        return True

    def _handle_custom_level_edit(self, sequential_num, parts, level_name):
        """Handle custom level specific editing."""
        cmd = str(sequential_num)

        if len(parts) == 2:
            param = parts[1]
            if param == '-':
                self.reset_custom_level(level_name)
            elif param.isdigit():
                new_level = int(param)
                if new_level > 0:
                    self.adjust_custom_level(level_name, new_level)
                else:
                    print("❌ Custom level must be a positive integer.")
            else:
                print(f"❌ Invalid parameter for custom level: {param}")
        else:
            print(f"❌ For custom levels, provide: {cmd} <new_level> (positive integer) or {cmd} - (to reset)")

    def _handle_regular_level_edit(self, parts, level_name):
        """Handle regular level editing."""
        if len(parts) == 1:
            self.edit_level_colors(level_name)
        else:
            # Parse arguments for color/label editing
            remaining = parts[1:5]
            if len(remaining) < 2:
                print(f"❌ Provide colors: {parts[0]} <fg> <bg> or <label> <fg> <bg>")
                return

            if len(remaining) == 2:
                # Field level: fg bg
                fg_part, bg_part = remaining[0], remaining[1]
                label_part = "_"
            else:
                # Log level: label fg bg
                label_part, fg_part, bg_part = remaining[0], remaining[1], remaining[2]

            self.edit_level_colors(level_name, fg_part, bg_part, label_part)

    def display_levels(self):
        """Display all levels with their current color and inverse color."""
        print(f"{Style.RESET_ALL}\nAvailable levels:")

        # Cache the sorted level information for reuse
        self._sorted_level_info = self._get_sorted_level_info()

        for sequential_index, (level_name, display_label, level_number_str, _) in enumerate(self._sorted_level_info, 1):
            normal_color = self.color_scheme.get(level_name)
            inverse_color = self.color_scheme.get(level_name, inverse=True)

            print("%2s. %s %s%-20s%s%s%-20s%s" % (
                sequential_index,
                level_number_str,
                normal_color,
                display_label,
                Style.RESET_ALL,
                inverse_color,
                display_label,
                Style.RESET_ALL
            ))

    def _display_level_line(self, level_name):
        """Display only the line for the specified level."""
        # Cache the sorted level information for reuse
        if self._sorted_level_info is None:
            self._sorted_level_info = self._get_sorted_level_info()

        # Find the sequential number for this level (case-insensitive match)
        for sequential_index, (lvl_name, display_label, level_number_str, _) in enumerate(self._sorted_level_info, 1):
            if lvl_name.upper() == level_name.upper():
                normal_color = self.color_scheme.get(lvl_name)
                inverse_color = self.color_scheme.get(lvl_name, inverse=True)

                print("%2s. %s %s%-20s%s%s%-20s%s" % (
                    sequential_index,
                    level_number_str,
                    normal_color,
                    display_label,
                    Style.RESET_ALL,
                    inverse_color,
                    display_label,
                    Style.RESET_ALL
                ))
                break

    def edit_level_colors(self, level_name, fg_part=None, bg_part=None, label_part=None):
        """Edit colors for a specific level."""
        if fg_part is not None or bg_part is not None or label_part is not None:
            self.apply_colors(level_name, fg_part, bg_part, label_part)
            return

        # Interactive mode
        # Get current values
        current_fg = getattr(self.color_scheme, f"{level_name}_foreground", "")
        current_bg = getattr(self.color_scheme, f"{level_name}_background", "")

        # Convert to color names, "null" for None, "_" for no color
        fg_name = ("null" if current_fg is None else self._ansi_to_name(current_fg, Fore) or "_")
        bg_name = ("null" if current_bg is None else self._ansi_to_name(current_bg, Back) or "_")

        print(f"\nEditing {level_name} (current: fg={fg_name} bg={bg_name})")

        # Get new values
        colors_str = input("Enter: <fg> <bg> (color names, 'null', or '_', tab for completion):\n  ").strip()
        parts = colors_str.split()

        fg_part = parts[0] if len(parts) > 0 else "_"
        bg_part = parts[1] if len(parts) > 1 else "_"

        self.apply_colors(level_name, fg_part, bg_part, None)

    def apply_colors(self, level_name, fg_part, bg_part, label_part):
        """Apply colors to a level."""
        # Process label if provided
        if label_part and label_part != "_":
            try:
                log_level = LogLevel(level_name.upper())
                LogLevel.set_str_repr(log_level, label_part)
            except ValueError:
                # Not a LogLevel, ignore label
                pass

        # Process foreground
        fg_set = False
        bg_set = False
        if fg_part is not None and fg_part.lower() != "_":
            if fg_part.lower() == "null":
                setattr(self.color_scheme, f"{level_name}_foreground", None)
                fg_set = True
            elif fg_part.upper() in [c.upper() for c in COLOR_STRINGS]:
                setattr(self.color_scheme, f"{level_name}_foreground",
                        getattr(Fore, fg_part.upper()))
                fg_set = True
            else:
                print(f"❌ Invalid foreground color: {fg_part}")
                return

        # Process background
        if bg_part is not None and bg_part.lower() != "_":
            if bg_part.lower() == "null":
                setattr(self.color_scheme, f"{level_name}_background", None)
                bg_set = True
            elif bg_part.upper() in [c.upper() for c in COLOR_STRINGS]:
                setattr(self.color_scheme, f"{level_name}_background",
                        getattr(Back, bg_part.upper()))
                bg_set = True
            else:
                print(f"❌ Invalid background color: {bg_part}")
                return

        # Update inverse colors if both fg and bg were set (swap them)
        if fg_set and bg_set:
            if bg_part.lower() == "null":
                fg_inv = None
            else:
                fg_inv = getattr(Fore, bg_part.upper())
            if fg_part.lower() == "null":
                bg_inv = None
            else:
                bg_inv = getattr(Back, fg_part.upper())
            setattr(self.color_scheme, f"{level_name}_foreground_inverse", fg_inv)
            setattr(self.color_scheme, f"{level_name}_background_inverse", bg_inv)

        # Display the updated line
        self._display_level_line(level_name)
        self.changed = True

    def reset_custom_level(self, level_name):
        """Reset a custom level back to its original negative number."""
        # Extract the level number from the level name (custom0 -> 0, etc.)
        try:
            level_index = int(level_name[6:])  # Extract number after "custom"
        except ValueError:
            print(f"❌ Invalid custom level name: {level_name}")
            return

        if not (0 <= level_index < len(LogLevel.custom_levels)):
            print(f"❌ Level index out of range: {level_index}")
            return

        # Find the original negative level from the levels/custom/custom_levels.json or levels/active
        config_file = self.config_dir / "levels" / "active"
        if not config_file.exists():
            # Fallback to factory
            config_file = self.config_dir / "levels" / "factory" / "default_custom_levels.json"
            
        if not config_file.exists():
            print("❌ Custom levels configuration file not found")
            return

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ Error reading custom levels configuration: {e}")
            return

        custom_levels = data.get("custom_levels", {})
        config_name = level_name.lower()
        if config_name not in custom_levels:
            print(f"❌ Configuration not found for {config_name}")
            return

        original_level = int(custom_levels[config_name]["logging_level"])

        # Check if it's already at the original negative level
        current_level = LogLevel.custom_levels[level_index]
        if current_level == original_level:
            print(f"ℹ️ Custom level {level_name} is already at original level {original_level}")
            return

        # Apply the reset
        LogLevel.custom_levels[level_index] = original_level

        # Show the reset
        level_enum = LogLevel.from_string(level_name.upper())
        print(
            f"🔄 Custom level {level_name} reset: {current_level} → {original_level} (displays as {level_enum.logging_level()})")

        self.changed = True

    def load_scheme(self, scheme):
        """Load a display scheme from either factory or user config directory."""
        scheme_lower = scheme.lower()
        
        # Try to find color scheme in both directories
        config_file = None
        
        # Check user config colors
        for subdir in ['custom', 'factory']:
            candidate = self.user_config_dir / "colors" / subdir / f"display_{scheme_lower}.json"
            if candidate.exists():
                config_file = candidate
                break
        
        # Check factory config colors if not found in user
        if config_file is None:
            for subdir in ['custom', 'factory']:
                candidate = self.factory_config_dir / "colors" / subdir / f"display_{scheme_lower}.json"
                if candidate.exists():
                    config_file = candidate
                    break
        
        if config_file:
            try:
                self.color_scheme = ColorScheme(colorscheme_json=config_file, update_active_link=True)
                print(f"✅ Loaded display scheme: {scheme}")
                self.changed = True
                self.display_levels()
                return
            except Exception:
                pass  # might be a labels file
        
        # Try to find label scheme in both directories
        label_file = None
        
        # Check user config strings
        for subdir in ['custom', 'factory']:
            candidate = self.user_config_dir / "strings" / subdir / f"strings_{scheme_lower}.json"
            if candidate.exists():
                label_file = candidate
                break
        
        # Check factory config strings if not found in user
        if label_file is None:
            for subdir in ['custom', 'factory']:
                candidate = self.factory_config_dir / "strings" / subdir / f"strings_{scheme_lower}.json"
                if candidate.exists():
                    label_file = candidate
                    break
        
        if label_file:
            try:
                LogLevel.load_str_reprs_from_json(str(label_file), update_active_link=True)
                print(f"✅ Loaded label scheme: {scheme}")
                self.changed = True
                self.display_levels()
            except Exception as e:
                print(f"❌ Error loading label scheme: {scheme}")
        else:
            print(f"❌ Error loading scheme: {scheme}")

    def load_color_scheme(self, scheme_arg):
        """Load a color scheme with fuzzy matching and numbered selection."""
        if scheme_arg.isdigit():
            # Load by number
            index = int(scheme_arg) - 1  # 1-based to 0-based
            if 0 <= index < len(self.color_schemes):
                scheme = self.color_schemes[index]
                self.load_scheme(scheme)
            else:
                print(f"❌ Color scheme number {scheme_arg} out of range")
        else:
            # Fuzzy match by name
            matching_schemes = [s for s in self.color_schemes if scheme_arg.lower() in s.lower()]
            if not matching_schemes:
                print(f"❌ No color scheme matches '{scheme_arg}'")
            elif len(matching_schemes) == 1:
                self.load_scheme(matching_schemes[0])
            else:
                print(f"❌ Multiple matches: {', '.join(matching_schemes)}. Be more specific.")

    def load_label_scheme(self, scheme_arg):
        """Load a label scheme with fuzzy matching and numbered selection."""
        if scheme_arg.isdigit():
            # Load by number
            index = int(scheme_arg) - 1  # 1-based to 0-based
            if 0 <= index < len(self.label_schemes):
                scheme = self.label_schemes[index]
                self.load_scheme(scheme)
            else:
                print(f"❌ Label scheme number {scheme_arg} out of range")
        else:
            # Fuzzy match by name
            matching_schemes = [s for s in self.label_schemes if scheme_arg.lower() in s.lower()]
            if not matching_schemes:
                print(f"❌ No label scheme matches '{scheme_arg}'")
            elif len(matching_schemes) == 1:
                self.load_scheme(matching_schemes[0])
            else:
                print(f"❌ Multiple matches: {', '.join(matching_schemes)}. Be more specific.")

    def save_colors_to_file(self, file_path):
        """Save the current color scheme to a JSON file."""
        config_data = {}
        for level in self.color_scheme.all_levels:
            fg = getattr(self.color_scheme, f"{level}_foreground", "")
            bg = getattr(self.color_scheme, f"{level}_background", "")

            # Convert ANSI codes back to color names
            fg_name = self._ansi_to_name(fg, Fore)
            bg_name = self._ansi_to_name(bg, Back)

            config_data[level] = {
                "foreground": fg_name,
                "background": bg_name
            }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, default=str)

    @staticmethod
    def save_labels_to_file(file_path):
        """Save the current color scheme to a JSON file."""
        LogLevel.save_str_reprs_to_json(str(file_path))

    def save_configuration(self):
        """Save the current configuration."""
        try:
            # Save colors to colors/custom (create a custom copy if saving a modified factory)
            color_target = self._get_save_target("colors")
            self.save_colors_to_file(color_target)
            print(f"✅ Colors saved to: {color_target}")
            
            # Update symlink to point to the saved file
            active_link = self.config_dir / "colors" / "active"
            if not active_link.exists() or os.readlink(str(active_link)) != str(color_target.relative_to(self.config_dir / "colors")):
                active_link.unlink(missing_ok=True)
                active_link.symlink_to(color_target.relative_to(self.config_dir / "colors"))
            
            # Save labels to strings/custom
            label_target = self._get_save_target("strings")
            self.save_labels_to_file(label_target)
            print(f"✅ Labels saved to: {label_target}")
            
            # Update symlink
            active_link = self.config_dir / "strings" / "active"
            if not active_link.exists() or os.readlink(str(active_link)) != str(label_target.relative_to(self.config_dir / "strings")):
                active_link.unlink(missing_ok=True)
                active_link.symlink_to(label_target.relative_to(self.config_dir / "strings"))
            
            # Save custom levels
            levels_target = self.config_dir / "levels" / "custom" / "custom_levels.json"
            levels_target.parent.mkdir(parents=True, exist_ok=True)
            LogLevel.save_custom_levels_to_json(str(levels_target))
            print(f"✅ Custom levels saved to: {levels_target}")
            
            # Update symlink
            active_link = self.config_dir / "levels" / "active"
            if not active_link.exists() or os.readlink(str(active_link)) != "custom/custom_levels.json":
                active_link.unlink(missing_ok=True)
                active_link.symlink_to("custom/custom_levels.json")
            
            self.changed = False
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")

    def _get_save_target(self, category):
        """Get the target path for saving based on current active link."""
        active_link = self.config_dir / category / "active"
        
        if active_link.exists() and active_link.is_symlink():
            target = os.readlink(str(active_link))
            # If currently pointing to factory, we need to copy to custom
            if target.startswith("factory/"):
                # Get the filename from the factory link
                filename = target.split("/")[-1]
                custom_path = self.config_dir / category / "custom" / filename
                custom_path.parent.mkdir(parents=True, exist_ok=True)
                return custom_path
            elif target.startswith("custom/"):
                # Already pointing to custom
                return self.config_dir / category / target
        
        # Default to custom with default name
        custom_dir = self.config_dir / category / "custom"
        custom_dir.mkdir(parents=True, exist_ok=True)
        
        if category == "colors":
            return custom_dir / "display_dark_bg_color.json"
        else:
            return custom_dir / "strings_en.json"

    def update_active_scheme(self):
        """Update the active display scheme with current configuration."""
        color_target = self._get_save_target("colors")
        self.save_colors_to_file(color_target)

    def confirm_save_and_quit(self):
        """Confirm saving changes before quitting."""
        if self.changed:
            save_choice = input(f"{Style.RESET_ALL}Save changes? (y/n): ").strip().lower()
            if save_choice == "y":
                self.save_configuration()
        print("Goodbye!")

    @staticmethod
    def list_schemes():
        """List available display schemes."""
        config_dir = Path(__file__).parent.parent / "flashlogger" / "config"
        schemes = []
        for f in config_dir.glob("display_*.json"):
            name = f.stem[len("display_"):].upper()
            schemes.append(name)
        if schemes:
            print(f"{Style.RESET_ALL}Available display schemes: {', '.join(schemes)}")
        else:
            print(f"{Style.RESET_ALL}No display schemes found.")

    def list_color_schemes(self):
        """List available color schemes with numbers."""
        if self.color_schemes:
            print(f"{Style.RESET_ALL}Available color schemes:")
            for i, scheme in enumerate(self.color_schemes, 1):
                print(f"{i}. {scheme}")
        else:
            print(f"{Style.RESET_ALL}No color schemes found.")

    def list_label_schemes(self):
        """List available label schemes with numbers."""
        if self.label_schemes:
            print(f"{Style.RESET_ALL}Available label schemes:")
            for i, scheme in enumerate(self.label_schemes, 1):
                print(f"{i}. {scheme}")
        else:
            print(f"{Style.RESET_ALL}No label schemes found.")

    def create_new_scheme(self, name, schema_type):
        """Create a new display scheme with current configuration."""
        config_dir = Path(__file__).parent.parent / "flashlogger" / "config"
        file_path = config_dir / f"display_{name.lower()}.json"
        active_label_file = config_dir / "active_strings.json"
        if schema_type == "label":
            file_path = config_dir / f"strings_{name.lower()}.json"
        if file_path.exists():
            overwrite = input(f"{Style.RESET_ALL}Scheme '{name}' exists. Overwrite? (y/n): ").strip().lower()
            if overwrite != "y":
                return
        # Save current config as new
        config_data = {}
        if schema_type == "color":
            for level in self.color_scheme.all_levels:
                fg = getattr(self.color_scheme, f"{level}_foreground", "")
                bg = getattr(self.color_scheme, f"{level}_background", "")
                fg_name = self._ansi_to_name(fg, Fore)
                bg_name = self._ansi_to_name(bg, Back)
                config_data[level] = {
                    "foreground": fg_name,
                    "background": bg_name
                }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, default=str)
            # Load the newly created scheme to make it active (updates symlink)
            self.color_scheme = ColorScheme(colorscheme_json=file_path, update_active_link=True)
            print(f"✅ New display scheme '{name}' saved and activated.")
            self.changed = True
            self.display_levels()
        else:
            # For labels, use current LogLevel reprs
            LogLevel.save_str_reprs_to_json(str(file_path))
            # Load the newly created scheme to make it active (updates symlink)
            LogLevel.load_str_reprs_from_json(str(file_path), update_active_link=True)
            print(f"✅ New labels '{name}' saved and activated.")
            self.changed = True
            self.display_levels()

    @staticmethod
    def _is_log_level(level_name):
        """Check if level_name is a LogLevel."""
        try:
            LogLevel(level_name.upper())
            return True
        except ValueError:
            return False

    def _collect_schemes(self):
        """Collect available display and label schemes from both factory and user config directories."""
        # Collect from factory config directory
        factory_dir = self.factory_config_dir
        factory_colors = [f.stem[len("display_"):].lower() for f in factory_dir.glob("colors/*/display_*.json")]
        factory_labels = [f.stem[len("strings_"):].lower() for f in factory_dir.glob("strings/*/strings_*.json")]
        
        # Collect from user config directory (if exists)
        user_colors = []
        user_labels = []
        if self.user_config_dir.exists():
            user_colors = [f.stem[len("display_"):].lower() for f in self.user_config_dir.glob("colors/*/display_*.json")]
            user_labels = [f.stem[len("strings_"):].lower() for f in self.user_config_dir.glob("strings/*/strings_*.json")]
        
        # Combine factory and user schemes, removing duplicates
        self.color_schemes = list(set(factory_colors + user_colors))
        self.label_schemes = list(set(factory_labels + user_labels))
        self.schemes = self.color_schemes + self.label_schemes

    def _completer(self, text, state) -> str | None:
        """Tab completer that provides context-aware completion."""

        def _matches(options: list[str], fragment: str) -> list[str]:
            frag = fragment.lower()
            return [opt for opt in options if opt.lower().startswith(frag) or frag in opt.lower()]

        def _nth_or_none(options: list[str], idx: int) -> str | None:
            return options[idx] if idx < len(options) else None

        line = readline.get_line_buffer()
        line_parts = line.split()
        ends_with_space = bool(line) and line[-1].isspace()
        token_index = len(line_parts) if ends_with_space else max(0, len(line_parts) - 1)
        current_text = "" if ends_with_space else text

        if not line_parts:
            return _nth_or_none(_matches(COMMAND_LIST, current_text), state)

        command = line_parts[0].lower()

        # Complete first token as a command.
        if token_index == 0:
            return _nth_or_none(_matches(COMMAND_LIST, current_text), state)

        # load [colorscheme|stringdefs] <scheme>
        if command == "load":
            if token_index == 1:
                load_types = ['colorscheme', 'stringdefs']
                return _nth_or_none(_matches(load_types + self.schemes, current_text), state)
            if token_index >= 2:
                type_arg = line_parts[1].lower()
                if type_arg in ['colorscheme', 'colors', 'color']:
                    return _nth_or_none(_matches(self.color_schemes, current_text), state)
                if type_arg in ['stringdefs', 'strings', 'labels', 'label']:
                    return _nth_or_none(_matches(self.label_schemes, current_text), state)
                return _nth_or_none(_matches(self.schemes, current_text), state)

        # new <name> [colors|labels]
        if command == "new" and token_index >= 2:
            return _nth_or_none(_matches(['colors', 'labels'], current_text), state)

        # reset customlevels|colors|labels
        if command == "reset" and token_index == 1:
            return _nth_or_none(_matches(['customlevels', 'colors', 'labels'], current_text), state)

        # Level editing by number or level name: suggest color tokens.
        is_numeric_level = command.isdigit()
        is_named_level = command.lower() in [lvl.lower() for lvl in self.color_scheme.all_levels]
        if is_numeric_level or is_named_level:
            color_tokens = ["_", "null"] + COLOR_STRINGS
            return _nth_or_none(_matches(color_tokens, current_text), state)

        return None

    @staticmethod
    def _ansi_to_name(ansi_code, module):
        """Convert ANSI code back to name from a colorama module."""
        if not ansi_code:
            return None

        for attr_name in dir(module):
            attr_value = getattr(module, attr_name, None)
            if attr_value == ansi_code:
                return attr_name

        return None

    def _get_sorted_level_info(self):
        """Get the sorted level information for consistent use."""
        # Collect level information with log level numbers for sorting
        level_info = []
        start_non_log_level = -666
        for level_name in self.color_scheme.all_levels:
            try:
                log_level = LogLevel.from_string(level_name.upper())
                log_level_num = log_level.logging_level()
                display_label = str(log_level)  # get the (custom-) string representation of the enum
                level_number_str = f"{log_level_num:4d}"
                sort_key = log_level_num
            except ExtendedEnumError:
                # Not a log level
                log_level_num = start_non_log_level  # Will sort these to the end
                start_non_log_level -= 1
                display_label = level_name
                level_number_str = " -/-"
                sort_key = log_level_num

            level_info.append((
                level_name,
                display_label,
                level_number_str,
                sort_key
            ))

        # Sort by descending log level number (non-log levels will be -999 and appear last)
        level_info.sort(key=lambda x: x[3], reverse=True)
        return level_info

    def _get_level_by_sequential_number(self, sequential_num):
        """Get level information by sequential number from the display."""
        sorted_info = self._get_sorted_level_info()
        if 1 <= sequential_num <= len(sorted_info):
            return sorted_info[sequential_num - 1]  # 1-based to 0-based
        return None

    def adjust_custom_level(self, level_name, new_level):
        """Adjust the logging level of a custom level."""
        # Extract the level number from the level name (custom0 -> 0, etc.)
        try:
            level_index = int(level_name[6:])  # Extract number after "custom"
        except ValueError:
            print(f"❌ Invalid custom level name: {level_name}")
            return

        if not (0 <= level_index < len(LogLevel.custom_levels)):
            print(f"❌ Level index out of range: {level_index}")
            return

        # Check if the new level is already taken by another custom level
        taken_levels = []
        for i, existing_level in enumerate(LogLevel.custom_levels):
            if i != level_index and existing_level == new_level:
                print(f"❌ Level {new_level} is already used by CUSTOM{i}")
                return
            if existing_level > 0:  # Only track positive levels (already configured)
                taken_levels.append(existing_level)

        # Check if new_level conflicts with standard levels
        if new_level in LogLevel.standard_mapping.keys():
            conflicting_level = LogLevel.standard_mapping[new_level]
            print(f"❌ Level {new_level} conflicts with standard {conflicting_level.name.lower()} level")
            return

        # Check for command levels conflicts
        if new_level in [LogLevel.command_level, LogLevel.command_stdout_level, LogLevel.command_stderr_level]:
            print(f"❌ Level {new_level} conflicts with command levels")
            return

        # Validate the new level range (keep it reasonable)
        if new_level > 1000000 or new_level < 1:
            print("❌ Level must be between 1 and 1,000,000")
            return

        # Apply the change
        old_level = LogLevel.custom_levels[level_index]
        LogLevel.custom_levels[level_index] = new_level

        # Show the change
        level_enum = LogLevel.from_string(level_name.upper())
        print(
            f"✅ Custom level {level_name} adjusted: {old_level} → {new_level} (displays as {level_enum.logging_level()})")

        self.changed = True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Simplified Color Configuration Tool")
    parser.add_argument("color_file", nargs="?", help="JSON file for colors")

    args = parser.parse_args()

    try:
        from flashlogger.color_scheme import ColorScheme
        from flashlogger.log_levels import LogLevel
        from flashlogger.flash_logger import FlashLogger
        from flashlogger.log_channel_console import ConsoleFormatter
    except ImportError:
        print(
            "❌ Cannot import PyFlashLogger modules. Please make sure the package is installed or run from the project directory.")
        return

    configurator = ColorConfigurator(args.color_file)
    configurator.run()


def debug_main():
    """Debug main function."""
    c = ColorConfigurator()
    c.display_levels()

    # Test some commands directly
    print("\nTesting commands:")
    print("li command test:", c._process_command('li'))
    print("l command test:", c._process_command('l'))
    print("lo command test:", c._process_command('lo'))
    print("load command test:", c._process_command('load'))
    print("load colorscheme test:", c._process_command('load colorscheme'))
    print("load stringdefs test:", c._process_command('load stringdefs'))


if __name__ == "__main__":
    # debug_main()
    main()
