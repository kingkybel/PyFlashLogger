#!/usr/bin/env python3
"""
Color, Style, and Label Configuration Tool

Interactive tool for customizing logging colors, styles, and labels.
Can load from and save to JSON configuration files.

Usage:
    python color_configurator.py [colors.json] [labels.json]

Author: Dieter J Kybelksties
"""

import os
import readline
import sys
from pathlib import Path

# Import from FlashLogger package
try:
    from flashlogger.color_scheme import ColorScheme
    from flashlogger.log_levels import LogLevel
    from flashlogger.flash_logger import FlashLogger
    from flashlogger.log_channel_console import ConsoleFormatter
except ImportError:
    # Fallback for local development
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from dkybutils.color_scheme import ColorScheme
    from dkybutils.log_levels import LogLevel
    from dkybutils.flash_logger import FlashLogger
    from dkybutils.log_channel_console import ConsoleFormatter
from colorama import Fore, Back, Style, init

# Initialize colorama
init()
# Enable tab completion for color names
readline.parse_and_bind('tab: complete')
readline.set_completer_delims(' \t\n;')
readline.set_completer(lambda text, state: [x for x in
                                            ['BLACK', 'RED', 'GREEN', 'YELLOW', 'BLUE', 'MAGENTA', 'CYAN', 'WHITE',
                                             'LIGHTBLACK_EX', 'LIGHTRED_EX', 'LIGHTGREEN_EX', 'LIGHTYELLOW_EX',
                                             'LIGHTBLUE_EX', 'LIGHTMAGENTA_EX', 'LIGHTCYAN_EX', 'LIGHTWHITE_EX',
                                             'NORMAL', 'BRIGHT', 'DIM'] if x.lower().startswith(text.lower())][
    state] if [x for x in
               ['BLACK', 'RED', 'GREEN', 'YELLOW', 'BLUE', 'MAGENTA', 'CYAN', 'WHITE', 'LIGHTBLACK_EX', 'LIGHTRED_EX',
                'LIGHTGREEN_EX', 'LIGHTYELLOW_EX', 'LIGHTBLUE_EX', 'LIGHTMAGENTA_EX', 'LIGHTCYAN_EX', 'LIGHTWHITE_EX',
                'NORMAL', 'BRIGHT', 'DIM'] if x.lower().startswith(text.lower())] and state < len([x for x in
                                                                                                   ['BLACK', 'RED',
                                                                                                    'GREEN', 'YELLOW',
                                                                                                    'BLUE', 'MAGENTA',
                                                                                                    'CYAN', 'WHITE',
                                                                                                    'LIGHTBLACK_EX',
                                                                                                    'LIGHTRED_EX',
                                                                                                    'LIGHTGREEN_EX',
                                                                                                    'LIGHTYELLOW_EX',
                                                                                                    'LIGHTBLUE_EX',
                                                                                                    'LIGHTMAGENTA_EX',
                                                                                                    'LIGHTCYAN_EX',
                                                                                                    'LIGHTWHITE_EX',
                                                                                                    'NORMAL', 'BRIGHT',
                                                                                                    'DIM'] if
                                                                                                   x.lower().startswith(
                                                                                                       text.lower())]) else None)


class ColorConfigurator:
    """Interactive tool for configuring colors, styles, and labels."""

    def __init__(self, color_file=None, label_file=None):
        self.color_scheme = ColorScheme()
        self.formatter = ConsoleFormatter(color_scheme=self.color_scheme)

        # Load configurations if provided
        if color_file and os.path.exists(color_file):
            print(f"Loading colors from: {color_file}")
            self.color_scheme = ColorScheme(colorscheme_json=Path(color_file))
            self.formatter = ConsoleFormatter(color_scheme=self.color_scheme)

        if label_file and os.path.exists(label_file):
            print(f"Loading labels from: {label_file}")
            LogLevel.load_str_reprs_from_json(label_file)

        self.color_file = color_file or "custom_colors.json"
        self.label_file = label_file or "custom_labels.json"

        # Available colors and styles
        self.available_colors = [
            'BLACK', 'RED', 'GREEN', 'YELLOW', 'BLUE', 'MAGENTA', 'CYAN', 'WHITE',
            'LIGHTBLACK_EX', 'LIGHTRED_EX', 'LIGHTGREEN_EX', 'LIGHTYELLOW_EX',
            'LIGHTBLUE_EX', 'LIGHTMAGENTA_EX', 'LIGHTCYAN_EX', 'LIGHTWHITE_EX'
        ]

        self.available_styles = ['NORMAL', 'BRIGHT', 'DIM']
        self.special_list = [
            ('default', 'Default'),
            ('bracket_color', 'Bracket'),
            ('timestamp_color', 'Timestamp'),
            ('process_color', 'Process'),
            ('comment_color', 'Comment'),
            ('operator_color', 'Operator')
        ]

    def _find_color(self, s):
        """Find color by fuzzy match."""
        s = s.lower()
        for c in self.available_colors:
            if s in c.lower():
                return c
        return None

    def _find_style(self, s):
        """Find style by fuzzy match."""
        s = s.lower()
        for st in self.available_styles:
            if s in st.lower():
                return st
        return None

    def _resolve_color_or_index(self, s):
        """Resolve color from index or name or fuzzy."""
        if not s or s == '_':
            return '_'
        if s.isdigit():
            idx = int(s) - 1
            if 0 <= idx < len(self.available_colors):
                return self.available_colors[idx]
        found = self._find_color(s)
        if found:
            return found
        try:
            return getattr(Fore, s.upper(), None) or getattr(Back, s.upper(), None)
        except:
            pass
        return None

    def run(self):
        """Run the interactive configurator."""
        print("🎨 Color & Label Configurator - Minimal Interface")
        print("=" * 60)

        self.main_loop()

    def main_loop(self):
        """Main input loop for commands."""
        level_list = list(LogLevel)
        num_items = len(level_list) + len(self.special_list)
        while True:
            self.display_levels()
            print("Commands: q=quit, s=save, l=load custom, load colors COLOR|BW|PLAIN,")
            print(f"  or load labels EN|DE, or item number [1-{num_items}] to edit")
            print("Edit format for levels: <label> <fg> <bg> <style> <hfg> <hbg> <hstyle>")
            print("Edit format for specials: <fg> <bg> <style> <hfg> <hbg> <hstyle>")
            print("Use '_' to keep current values")
            try:
                cmd_line = input("\nCommand: ").strip()
                parts = cmd_line.split()
                if not parts:
                    continue
                cmd = parts[0].lower()
                if cmd == 'q':
                    print("Goodbye!")
                    break
                elif cmd == 's':
                    self.save_configuration()
                elif cmd == 'l':
                    self.load_configuration()
                elif cmd == "load":
                    if len(parts) < 3:
                        print("❌ Usage: load colors COLOR|BW|PLAIN or load labels EN|DE")
                        continue
                    what = parts[1].lower()
                    scheme = parts[2].upper()
                    if what == "colors":
                        try:
                            if scheme == "COLOR":
                                self.color_scheme = ColorScheme(default_scheme=ColorScheme.Default.COLOR)
                            elif scheme == "BW":
                                self.color_scheme = ColorScheme(default_scheme=ColorScheme.Default.BLACK_AND_WHITE)
                            elif scheme == "PLAIN":
                                self.color_scheme = ColorScheme(default_scheme=ColorScheme.Default.PLAIN_TEXT)
                            else:
                                print("❌ Invalid color scheme: COLOR, BW, PLAIN")
                                continue
                            self.formatter = ConsoleFormatter(color_scheme=self.color_scheme)
                            print(f"✅ Loaded color scheme: {scheme}")
                        except Exception as e:
                            print(f"❌ Error loading color scheme: {e}")
                    elif what == "labels":
                        try:
                            if scheme == "EN":
                                LogLevel.load_str_reprs_from_json("dkybutils/config/log_levels_en.json")
                            elif scheme == "DE":
                                LogLevel.load_str_reprs_from_json("dkybutils/config/log_levels_de.json")
                            else:
                                print("❌ Invalid label scheme: EN, DE")
                                continue
                            print(f"✅ Loaded label scheme: {scheme}")
                        except Exception as e:
                            print(f"❌ Error loading label scheme: {e}")
                    else:
                        print("❌ Usage: load colors COLOR|BW|PLAIN or load labels EN|DE")
                elif cmd.isdigit():
                    item_idx = int(cmd) - 1
                    if 0 <= item_idx < num_items:
                        values = parts[1:] if len(parts) > 1 else None
                        if item_idx < len(level_list):
                            self._edit_level_colors(level_list[item_idx], values)
                        else:
                            special_idx = item_idx - len(level_list)
                            attr, name = self.special_list[special_idx]
                            self._edit_special_colors(attr, name, values)
                    else:
                        print("❌ Invalid item number.")
                else:
                    print("❌ Invalid command.")
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break

    def display_levels(self):
        """Display all levels with their current normal and highlight colors."""
        print("\nAvailable levels:")

        level_list = list(LogLevel)
        for i, level in enumerate(level_list):
            print(f"{i + 1:2d}. ", end='')

            # Show label in normal colors
            self._log_level_sample(level, use_highlight=False)

            # Leave a space between the repeated labels
            print(" ", end='')

            # Show label in highlight colors
            self._log_level_sample(level, use_highlight=True)

            print()  # Move to next line for the next level

        # Display special colors
        print("\nSpecial elements:")
        for i, (attr, name) in enumerate(self.special_list):
            idx = len(level_list) + i + 1
            print(f"{idx:2d}. ", end='')

            self._log_level_sample_special(attr, False, name)

            print(" ", end='')

            self._log_level_sample_special(attr, True, name)

            print()

    def _log_level_sample(self, level: LogLevel, use_highlight: bool = False):
        """Print a sample label for a level using specified color scheme."""
        level_lower = level.name.lower()
        if use_highlight:
            fg_attr = f'{level_lower}_highlight_foreground'
            bg_attr = f'{level_lower}_highlight_background'
            style_attr = f'{level_lower}_highlight_style'
        else:
            fg_attr = f'{level_lower}_normal_foreground'
            bg_attr = f'{level_lower}_normal_background'
            style_attr = f'{level_lower}_normal_style'

        # Get colors, fallback for highlight to normal if not set
        fg = getattr(self.color_scheme, fg_attr, '') or getattr(self.color_scheme, f'{level_lower}_normal_foreground',
                                                                '')
        bg = getattr(self.color_scheme, bg_attr, '') or getattr(self.color_scheme, f'{level_lower}_normal_background',
                                                                '')
        style = getattr(self.color_scheme, style_attr, '') or getattr(self.color_scheme, f'{level_lower}_normal_style',
                                                                      '')

        # Print with colors
        print(f"{fg}{bg}{style}{str(level)}{Style.RESET_ALL}", end='')

    def _log_level_sample_special(self, attr, use_highlight, label):
        """Print a sample label for a special element."""
        if use_highlight:
            fg_attr = f'{attr}_highlight_foreground'
            bg_attr = f'{attr}_highlight_background'
            style_attr = f'{attr}_highlight_style'
        else:
            fg_attr = f'{attr}_normal_foreground'
            bg_attr = f'{attr}_normal_background'
            style_attr = f'{attr}_normal_style'

        fg = getattr(self.color_scheme, fg_attr, '')
        bg = getattr(self.color_scheme, bg_attr, '')
        style = getattr(self.color_scheme, style_attr, '')

        print(f"{fg}{bg}{style}{label}{Style.RESET_ALL}", end='')

    def _edit_level_colors(self, level: LogLevel, values: list = None):
        """Edit colors for a specific level."""
        level_lower = level.name.lower()

        # Get current values
        current_label = str(level)
        current_fg = getattr(self.color_scheme, f'{level_lower}_normal_foreground', '')
        current_bg = getattr(self.color_scheme, f'{level_lower}_normal_background', '')
        current_style = getattr(self.color_scheme, f'{level_lower}_normal_style', '')
        current_hfg = getattr(self.color_scheme, f'{level_lower}_highlight_foreground', '')
        current_hbg = getattr(self.color_scheme, f'{level_lower}_highlight_background', '')
        current_hstyle = getattr(self.color_scheme, f'{level_lower}_highlight_style', '')

        # Convert to names
        fg_name = self._ansi_to_name(current_fg, Fore) or "DEFAULT"
        bg_name = self._ansi_to_name(current_bg, Back) or ""
        style_name = self._ansi_to_name(current_style, Style) or "NORMAL"
        hfg_name = self._ansi_to_name(current_hfg, Fore) or "DEFAULT"
        hbg_name = self._ansi_to_name(current_hbg, Back) or ""
        hstyle_name = self._ansi_to_name(current_hstyle, Style) or "NORMAL"

        # Get new values
        if values is None:
            values = input(
                "Enter: <label> <fg> <bg> <style> <hfg> <hbg> <hstyle> (use '_' to keep):\n  ").strip().split()

        # Pad with '_' if fewer than 7, truncate if more
        values += ['_'] * (7 - len(values))
        values = values[:7]

        # Show current configuration if interactive
        if values[0] != '' and any(v != '_' for v in values):
            print(f"\nEditing {level.name}:")
            print(
                f"  Current: {current_label} | {fg_name} on {bg_name} ({style_name}) | {hfg_name} on {hbg_name} ({hstyle_name})")

        label, fg, bg, style, hfg, hbg, hstyle = values

        # Set label if changed
        if label != '_':
            if level.name.startswith('CUSTOM'):
                LogLevel.set_str_repr(level, label)
            else:
                print(f"⚠️  Cannot change label for standard level {level.name}")

        # Set normal colors
        if fg != '_':
            if fg.isdigit():
                fg = self.available_colors[int(fg) - 1] if 1 <= int(fg) <= len(self.available_colors) else fg
            try:
                self.formatter.set_level_color(level, 'normal', foreground=fg)
            except:
                pass

        if bg != '_':
            if bg.isdigit():
                bg = self.available_colors[int(bg) - 1] if 1 <= int(bg) <= len(self.available_colors) else bg
            try:
                self.formatter.set_level_color(level, 'normal', background=bg)
            except:
                pass

        if style != '_':
            if style.isdigit():
                style = self.available_styles[int(style) - 1] if 1 <= int(style) <= len(
                    self.available_styles) else style
            try:
                self.formatter.set_level_color(level, 'normal', style=style)
            except:
                pass

        # Set highlight colors
        if hfg != '_':
            if hfg.isdigit():
                hfg = self.available_colors[int(hfg) - 1] if 1 <= int(hfg) <= len(self.available_colors) else hfg
            try:
                self.formatter.set_level_color(level, 'highlight', foreground=hfg)
            except:
                pass

        if hbg != '_':
            if hbg.isdigit():
                hbg = self.available_colors[int(hbg) - 1] if 1 <= int(hbg) <= len(self.available_colors) else hbg
            try:
                self.formatter.set_level_color(level, 'highlight', background=hbg)
            except:
                pass

        if hstyle != '_':
            if hstyle.isdigit():
                hstyle = self.available_styles[int(hstyle) - 1] if 1 <= int(hstyle) <= len(
                    self.available_styles) else hstyle
            try:
                self.formatter.set_level_color(level, 'highlight', style=hstyle)
            except:
                pass

        print("✅ Configuration updated")

    def _edit_special_colors(self, attr, name, values=None):
        """Edit colors for a special element."""
        # Get current values
        current_fg = getattr(self.color_scheme, f'{attr}_normal_foreground', '')
        current_bg = getattr(self.color_scheme, f'{attr}_normal_background', '')
        current_style = getattr(self.color_scheme, f'{attr}_normal_style', '')
        current_hfg = getattr(self.color_scheme, f'{attr}_highlight_foreground', '')
        current_hbg = getattr(self.color_scheme, f'{attr}_highlight_background', '')
        current_hstyle = getattr(self.color_scheme, f'{attr}_highlight_style', '')

        # Convert to names
        fg_name = self._ansi_to_name(current_fg, Fore) or "DEFAULT"
        bg_name = self._ansi_to_name(current_bg, Back) or ""
        style_name = self._ansi_to_name(current_style, Style) or "NORMAL"
        hfg_name = self._ansi_to_name(current_hfg, Fore) or "DEFAULT"
        hbg_name = self._ansi_to_name(current_hbg, Back) or ""
        hstyle_name = self._ansi_to_name(current_hstyle, Style) or "NORMAL"

        # Get new values
        if values is None:
            values = input("Enter: <fg> <bg> <style> <hfg> <hbg> <hstyle> (use '_' to keep):\n  ").strip().split()

        # Pad with '_' to 6, truncate if more
        values += ['_'] * (6 - len(values))
        values = values[:6]

        # Show current if not all _
        if any(v != '_' for v in values):
            print(f"\nEditing {name} special:")
            print(f"  Current: {fg_name} on {bg_name} ({style_name}) | {hfg_name} on {hbg_name} ({hstyle_name})")

        fg, bg, style, hfg, hbg, hstyle = values

        # Set normal colors
        if fg != '_':
            if fg.isdigit():
                fg = self.available_colors[int(fg) - 1] if 1 <= int(fg) <= len(self.available_colors) else fg
            setattr(self.color_scheme, f'{attr}_normal_foreground', getattr(Fore, fg.upper(), Fore.WHITE))
        if bg != '_':
            if bg.isdigit():
                bg = self.available_colors[int(bg) - 1] if 1 <= int(bg) <= len(self.available_colors) else bg
            setattr(self.color_scheme, f'{attr}_normal_background', getattr(Back, bg.upper(), Back.BLACK))
        if style != '_':
            if style.isdigit():
                style = self.available_styles[int(style) - 1] if 1 <= int(style) <= len(
                    self.available_styles) else style
            setattr(self.color_scheme, f'{attr}_normal_style', getattr(Style, style.upper(), Style.NORMAL))

        # Set highlight colors
        if hfg != '_':
            if hfg.isdigit():
                hfg = self.available_colors[int(hfg) - 1] if 1 <= int(hfg) <= len(self.available_colors) else hfg
            setattr(self.color_scheme, f'{attr}_highlight_foreground', getattr(Fore, hfg.upper(), Fore.WHITE))
        if hbg != '_':
            if hbg.isdigit():
                hbg = self.available_colors[int(hbg) - 1] if 1 <= int(hbg) <= len(self.available_colors) else hbg
            setattr(self.color_scheme, f'{attr}_highlight_background', getattr(Back, hbg.upper(), Back.BLACK))
        if hstyle != '_':
            if hstyle.isdigit():
                hstyle = self.available_styles[int(hstyle) - 1] if 1 <= int(hstyle) <= len(
                    self.available_styles) else hstyle
            setattr(self.color_scheme, f'{attr}_highlight_style', getattr(Style, hstyle.upper(), Style.NORMAL))

        print("✅ Special configuration updated")

    def load_configuration(self):
        """Load configuration from JSON files."""
        print("\n📁 Loading Configuration")
        print("-" * 25)

        # Load colors
        if os.path.exists(self.color_file):
            try:
                self.color_scheme = ColorScheme(colorscheme_json=Path(self.color_file))
                self.formatter = ConsoleFormatter(color_scheme=self.color_scheme)
                print(f"✅ Colors loaded from: {self.color_file}")
            except Exception as e:
                print(f"❌ Error loading colors: {e}")
        else:
            print(f"⚠️  Colors file not found: {self.color_file}")

        # Load labels
        if os.path.exists(self.label_file):
            try:
                LogLevel.load_str_reprs_from_json(self.label_file)
                print(f"✅ Labels loaded from: {self.label_file}")
            except Exception as e:
                print(f"❌ Error loading labels: {e}")
        else:
            print(f"⚠️  Labels file not found: {self.label_file}")

    def configure_styles(self):
        """Configure styles interactively."""
        print("\n✨ Style Configuration")
        print("-" * 25)

        # Show available log levels
        levels = [level.name.lower() for level in LogLevel]
        print("Available levels:")
        for i, level in enumerate(levels):
            print(f"  {i + 1}. {level}")

        level_choice = input("\nChoose level number (or 'back'): ").strip()
        if level_choice.lower() == 'back':
            return

        try:
            level_idx = int(level_choice) - 1
            if 0 <= level_idx < len(levels):
                level_name = levels[level_idx]
            else:
                print("❌ Invalid level number.")
                return
        except ValueError:
            print("❌ Invalid input.")
            return

        # Choose normal or highlight
        print("\nChoose scheme:")
        print("1. Normal")
        print("2. Highlight")

        scheme_choice = input("Choice: ").strip()
        if scheme_choice == '1':
            scheme = 'normal'
        elif scheme_choice == '2':
            scheme = 'highlight'
        else:
            print("❌ Invalid choice.")
            return

        # Show available styles
        print("\nAvailable styles:")
        for i, style in enumerate(self.available_styles):
            styled_text = getattr(Style, style, '') + f"Style: {style}" + Style.RESET_ALL
            print(f"  {i + 1}. {styled_text}")

        style_choice = input("Choose style number: ").strip()
        try:
            style_idx = int(style_choice) - 1
            if 0 <= style_idx < len(self.available_styles):
                selected_style = self.available_styles[style_idx]
            else:
                print("❌ Invalid style number.")
                return
        except ValueError:
            print("❌ Invalid input.")
            return

        # Apply the style change
        try:
            self.formatter.set_level_color(LogLevel[level_name.upper()], scheme, style=selected_style)
            print(f"✅ Applied {selected_style} style to {level_name} {scheme}")
        except Exception as e:
            print(f"❌ Error applying style: {e}")

    def configure_labels(self):
        """Configure custom level labels."""
        print("\n🏷️  Label Configuration")
        print("-" * 25)

        # Show current custom level mappings
        print("Current custom level labels:")
        for level in LogLevel:
            if level.name.startswith('CUSTOM'):
                current_repr = str(level)
                print(f"  {level.name}: '{current_repr}'")

        print("\nChoose an action:")
        print("1. Set label for a level")
        print("2. Clear all custom labels")

        action_choice = input("Choice: ").strip()

        if action_choice == '1':
            # Set label for a specific level
            print("\nAvailable CUSTOM levels:")
            custom_levels = [level for level in LogLevel if level.name.startswith('CUSTOM')]
            for i, level in enumerate(custom_levels):
                print(f"  {i + 1}. {level.name}")

            level_choice = input("\nChoose level number: ").strip()
            try:
                level_idx = int(level_choice) - 1
                if 0 <= level_idx < len(custom_levels):
                    selected_level = custom_levels[level_idx]
                else:
                    print("❌ Invalid level number.")
                    return
            except ValueError:
                print("❌ Invalid input.")
                return

            new_label = input(f"Enter new label for {selected_level.name}: ").strip()
            if new_label:
                LogLevel.set_str_repr(selected_level, new_label)
                print(f"✅ Set label '{new_label}' for {selected_level.name}")
            else:
                print("❌ Label cannot be empty.")

        elif action_choice == '2':
            # Clear all custom labels
            LogLevel.clear_str_reprs()
            print("✅ Cleared all custom labels.")
        else:
            print("❌ Invalid choice.")

    def test_configuration(self):
        """Test the current configuration with sample logging."""
        print("\n🧪 Testing Configuration")
        print("-" * 25)

        # Create a temporary logger for testing
        logger = FlashLogger(console=self.color_scheme)

        print("Sample log output:")
        print("-" * 20)

        # Test various levels
        logger.log_debug("Debug message")
        logger.log_info("Info message")
        logger.log_warning("Warning message")
        logger.log_error("Error message")

        # Test custom levels if available
        try:
            logger.log_custom0("Custom level 0")
            logger.log_custom1("Custom level 1")
        except AttributeError:
            pass

        print("-" * 20)
        print("✅ Test complete")

    def save_configuration(self):
        """Save the current configuration to JSON files."""
        print("\n💾 Saving Configuration")
        print("-" * 25)

        # Save colors
        try:
            color_path = Path(self.color_file)
            self.color_scheme.save_to_json(color_path)
            print(f"✅ Colors saved to: {color_path}")
        except Exception as e:
            print(f"❌ Error saving colors: {e}")

        # Save labels
        try:
            label_path = Path(self.label_file)
            LogLevel.save_str_reprs_to_json(str(label_path))
            print(f"✅ Labels saved to: {label_path}")
        except Exception as e:
            print(f"❌ Error saving labels: {e}")

    def show_current_config(self):
        """Show the current configuration with actual color demonstrations."""
        print("\n📋 Current Configuration")
        print("-" * 30)

        print("\n🎨 Color Demonstrations:")
        print("-" * 25)

        # Create a temporary logger to show colors in action
        logger = FlashLogger(console=self.color_scheme)

        # Demonstrate each CUSTOM level with actual colors
        for level in LogLevel:
            if not level.name.startswith('CUSTOM'):
                continue

            level_lower = level.name.lower()

            # Get readable names for display
            fg = getattr(self.color_scheme, f'{level_lower}_normal_foreground', '')
            bg = getattr(self.color_scheme, f'{level_lower}_normal_background', '')
            style = getattr(self.color_scheme, f'{level_lower}_normal_style', '')

            fg_name = self._ansi_to_name(fg, Fore) or "DEFAULT"
            bg_name = self._ansi_to_name(bg, Back) or ""
            style_name = self._ansi_to_name(style, Style) or "NORMAL"

            # Show metadata
            bg_desc = f" on {bg_name}" if bg_name else ""
            style_desc = f" ({style_name})" if style_name != "NORMAL" else ""

            print(f"  {level.name} [{fg_name}{bg_desc}{style_desc}]:")

            # Log actual sample to show the color
            try:
                log_method = getattr(logger, f'log_{level_lower}')
                log_method(f"Sample {str(level)} message")
            except AttributeError:
                print(f"    (Unable to demonstrate {level.name})")

        print("\n🏷️  Label Mappings:")
        print("-" * 20)
        if LogLevel.custom_str_map:
            for level, label in LogLevel.custom_str_map.items():
                print(f"  {level.name} → '{label}'")
        else:
            print("  No custom labels set.")

    def _ansi_to_name(self, ansi_code, module):
        """Convert ANSI code back to name from a colorama module."""
        if not ansi_code:
            return None

        # Check all attributes in the module
        for attr_name in dir(module):
            attr_value = getattr(module, attr_name, None)
            if attr_value == ansi_code:
                return attr_name

        return None


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Color and Label Configuration Tool")
    parser.add_argument('color_file', nargs='?', help='JSON file for colors')
    parser.add_argument('label_file', nargs='?', help='JSON file for labels')

    args = parser.parse_args()

    configurator = ColorConfigurator(args.color_file, args.label_file)
    configurator.run()


if __name__ == "__main__":
    main()
