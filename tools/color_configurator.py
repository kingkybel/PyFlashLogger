#!/usr/bin/env python3
"""
Simplified Color Configuration Tool

Interactive tool for customizing logging colors with foreground/background only.
Can load from and save to JSON configuration files.

Usage:
    python color_configurator.py [colors.json]

Author: Dieter J Kybelksties
"""

import os
import readline
import sys
from pathlib import Path
import json

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

# Enable tab completion for color names
readline.parse_and_bind("tab: complete")
readline.set_completer_delims(" \t\n;")
readline.set_completer(lambda text, state: [x for x in COLOR_STRINGS \
                                            if x.lower().startswith(text.lower())][state] \
    if [x for x in COLOR_STRINGS if x.lower().startswith(text.lower())] and \
       state < len([x for x in COLOR_STRINGS if x.lower().startswith(text.lower())]) \
    else None)


class ColorConfigurator:
    """Interactive tool for configuring simplified colors."""

    def __init__(self, color_file=None):
        config_dir = Path(__file__).parent.parent / "flashlogger" / "config"

        # Use provided color file or default
        if color_file:
            self.color_file = Path(color_file)
        else:
            self.color_file = config_dir / "active_color_scheme.json"

        # Load configurations
        if self.color_file.exists():
            print(f"{Style.RESET_ALL}Loading colors from: {self.color_file}")
            self.color_scheme = ColorScheme(colorscheme_json=self.color_file)
        else:
            print(f"{Style.RESET_ALL}Loading default colors")
            self.color_scheme = ColorScheme()


    def run(self):
        """Run the interactive configurator."""
        print(f"{Style.RESET_ALL}🎨 Simplified Color Configurator")
        print("=" * 40)

        self.main_loop()

    def main_loop(self):
        """Main input loop for commands."""
        while True:
            self.display_levels()
            print(f"{Style.RESET_ALL}CAommands: q=quit, s=sAve, load COLOR|BW|PLAIN,")
            print(f"or item number [1-{len(self.color_scheme.all_levels)}] to edit")
            print(f"{Style.RESET_ALL}Edit format: <fg> <bg> (use '_' to keep current)")

            try:
                cmd_line = input(f"{Style.RESET_ALL}\nCommand: ").strip()
                parts = cmd_line.split()
                if not parts:
                    continue
                cmd = parts[0].lower()
                if cmd == "q":
                    print("Goodbye!")
                    break
                elif cmd == "s":
                    self.save_configuration()
                elif cmd == "load":
                    scheme = parts[1].upper() if len(parts) > 1 else None
                    if scheme in ["COLOR", "BW", "PLAIN"]:
                        self.load_color_scheme(scheme)
                    else:
                        print("❌ Invalid scheme: COLOR, BW, PLAIN")
                elif cmd.isdigit():
                    item_idx = int(cmd) - 1
                    if 0 <= item_idx < len(self.color_scheme.all_levels):
                        self.edit_level_colors(self.color_scheme.all_levels[item_idx])
                    else:
                        print("❌ Invalid item number.")
                else:
                    print("❌ Invalid command.")
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break

    def display_levels(self):
        """Display all levels with their current color and inverse color."""
        print(f"{Style.RESET_ALL}\nAvailable levels:")

        for i, level_name in enumerate(self.color_scheme.all_levels):
            print(f"{i + 1:2d}. ", end="")

            # Show level in normal colors
            print(f"{self.color_scheme.get(level_name)}{level_name}{Style.RESET_ALL}", end=" ")

            # Show level in inverse colors
            print(f"{self.color_scheme.get(level_name, inverse=True)}{level_name} (inverse){Style.RESET_ALL}")

    def edit_level_colors(self, level_name):
        """Edit colors for a specific level."""
        # Get current values
        current_fg = getattr(self.color_scheme, f"{level_name}_foreground", "")
        current_bg = getattr(self.color_scheme, f"{level_name}_background", "")

        # Convert to color names or "_" for no color
        fg_name = self._ansi_to_name(current_fg, Fore) or "_"
        bg_name = self._ansi_to_name(current_bg, Back) or "_"

        print(f"\nEditing {level_name} (current: fg={fg_name} bg={bg_name})")

        # Get new values
        colors_str = input("Enter: <fg> <bg> (color names or '_', tab for completion):\n  ").strip()
        parts = colors_str.split()

        fg_part = parts[0] if len(parts) > 0 else "_"
        bg_part = parts[1] if len(parts) > 1 else "_"

        # Process foreground
        if fg_part != "_":
            if fg_part.upper() in [c.upper() for c in COLOR_STRINGS]:
                setattr(self.color_scheme, f"{level_name}_foreground",
                        getattr(Fore, fg_part.upper()))
            else:
                print(f"❌ Invalid foreground color: {fg_part}")
                return

        # Process background
        if bg_part != "_":
            if bg_part.upper() in [c.upper() for c in COLOR_STRINGS]:
                setattr(self.color_scheme, f"{level_name}_background",
                        getattr(Back, bg_part.upper()))
            else:
                print(f"❌ Invalid background color: {bg_part}")
                return

        print("✅ Configuration updated")

    def load_color_scheme(self, scheme):
        """Load a color scheme."""
        config_dir = Path(__file__).parent.parent / "flashlogger" / "config"
        config_file = config_dir / f"color_scheme_{scheme.lower()}.json"

        try:
            self.color_scheme = ColorScheme(colorscheme_json=config_file)
            print(f"✅ Loaded color scheme: {scheme}")
        except Exception as e:
            print(f"❌ Error loading scheme: {e}")

    def save_configuration(self):
        """Save the current configuration."""
        try:
            # Convert color scheme to JSON and save
            config_data = {}
            for level in self.color_scheme.all_levels:
                fg = getattr(self.color_scheme, f"{level}_foreground", "")
                bg = getattr(self.color_scheme, f"{level}_background", "")

                # Convert ANSI codes back to color names
                fg_name = self._ansi_to_name(fg, Fore) or ""
                bg_name = self._ansi_to_name(bg, Back) or ""

                config_data[level] = {
                    "foreground": fg_name,
                    "background": bg_name
                }

            with open(self.color_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)

            print(f"✅ Colors saved to: {self.color_file}")
        except Exception as e:
            print(f"❌ Error saving colors: {e}")

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
        print("❌ Cannot import PyFlashLogger modules. Please make sure the package is installed or run from the project directory.")
        return

    configurator = ColorConfigurator(args.color_file)
    configurator.run()


if __name__ == "__main__":
    main()
