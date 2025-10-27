from __future__ import annotations

import json
from enum import auto
from pathlib import Path

from colorama import init as colorama_init, Fore, Back, Style

from flashlogger.extended_enum import ExtendedEnum
from flashlogger.log_levels import LogLevel

colorama_init()


class ColorScheme:
    """
    Color scheme management for console logging.

    This class loads color configurations from JSON files and provides ANSI color
    codes for different log levels and special formatting elements.

    Available default schemes:
    - COLOR: Full color scheme with ANSI color codes (default)
    - BLACK_AND_WHITE: Monochrome color scheme using only white/black tones
    - PLAIN_TEXT: No ANSI colors at all - plain text output

    Custom color schemes can be loaded by providing a custom JSON file path:

        custom_scheme = ColorScheme(colorscheme_json=Path("/path/to/custom.json"))

    JSON Configuration Format:
    {
      "level_name": {
        "normal": {
          "foreground": "COLOR_NAME",
          "background": "COLOR_NAME",
          "style": "STYLE_NAME"
        },
        "highlight": {...}
      },
      "special": {
        "default": {"foreground": "...", "background": "...", "style": "..."},
        "bracket_color": {...},
        "timestamp_color": {...}
      }
    }

    Color Names: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, [LIGHT]COLOR_EX
    Style Names: NORMAL, BRIGHT, DIM
    Special Values: "" or "default" (inherits from special.default)
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
        if colorscheme_json:
            self._load_from_config(colorscheme_json)
        elif default_scheme == ColorScheme.Default.PLAIN_TEXT:
            self._create_plain_text_scheme()
        elif default_scheme == ColorScheme.Default.BLACK_AND_WHITE:
            self._load_from_config(Path(__file__).parent / "config/color_scheme_bw.json")
        else:
            self._load_from_config(Path(__file__).parent / "config/color_scheme_color.json")
        self._set_defaults()

    def _set_defaults(self):
        """
        Set default values for special attributes that may not be loaded from config.
        This ensures all expected attributes are present.
        """
        # Ensure special colors are set, defaulting to the 'default' special color if not set
        if hasattr(self, 'default_foreground'):
            default_fg = self.default_foreground
            default_bg = self.default_background
            default_style = self.default_style
            default_highlight_fg = self.default_highlight_foreground
            default_highlight_bg = self.default_highlight_background
            default_highlight_style = self.default_highlight_style
        else:
            from colorama import Fore, Back, Style
            default_fg = Fore.WHITE
            default_bg = Back.BLACK
            default_style = Style.NORMAL
            default_highlight_fg = Fore.WHITE
            default_highlight_bg = Back.BLACK
            default_highlight_style = Style.NORMAL

        special_types = ['bracket_color', 'timestamp_color']
        for special_type in special_types:
            if not hasattr(self, f"{special_type}_foreground"):
                setattr(self, f"{special_type}_foreground", default_fg)
                setattr(self, f"{special_type}_background", default_bg)
                setattr(self, f"{special_type}_style", default_style)
                setattr(self, f"{special_type}_highlight_foreground", default_highlight_fg)
                setattr(self, f"{special_type}_highlight_background", default_highlight_bg)
                setattr(self, f"{special_type}_highlight_style", default_highlight_style)

    def _load_from_config(self, config_file: Path):
        with open(config_file, encoding="utf-8") as f:
            data = json.load(f)
        self.field_order = data.get("fields", ["timestamp", "pid", "tid", "level", "message"])
        for level_str, schemes in data.items():
            if level_str == "special":
                # Handle special level-independent colors
                for special_type, colors in schemes.items():
                    fg_str = colors.get("foreground", "WHITE")
                    bg_str = colors.get("background", "BLACK")
                    style_str = colors.get("style", "NORMAL")
                    fg = getattr(Fore, fg_str.upper(), Fore.WHITE)
                    bg = getattr(Back, bg_str.upper(), Back.BLACK)
                    style = getattr(Style, style_str.upper(), Style.NORMAL)
                    attr_name = f"{special_type}_foreground"
                    setattr(self, attr_name, fg)
                    attr_name = f"{special_type}_background"
                    setattr(self, attr_name, bg)
                    attr_name = f"{special_type}_style"
                    setattr(self, attr_name, style)
                    # Set highlight to same as normal for compatibility
                    setattr(self, f"{special_type}_highlight_foreground", fg)
                    setattr(self, f"{special_type}_highlight_background", bg)
                    setattr(self, f"{special_type}_highlight_style", style)
            else:
                # Handle level-specific colors
                level_name = level_str.upper()
                try:
                    _ = getattr(LogLevel, level_name)
                except AttributeError:
                    continue  # skip if not in LogLevel
                for scheme_type, colors in schemes.items():
                    fg_str = colors.get("foreground", "WHITE")
                    bg_str = colors.get("background", "BLACK")
                    style_str = colors.get("style", "NORMAL")

                    # Check for "" or "default" - use special default colors
                    if fg_str in {"", "default"}:
                        fg = self.default_foreground if hasattr(self, 'default_foreground') else Fore.MAGENTA
                    else:
                        fg = getattr(Fore, fg_str.upper(), Fore.WHITE)

                    if bg_str in ("", "default"):
                        bg = self.default_background if hasattr(self, 'default_background') else Back.BLACK
                    else:
                        bg = getattr(Back, bg_str.upper(), Back.BLACK)

                    if style_str in ("", "default"):
                        style = self.default_style if hasattr(self, 'default_style') else Style.NORMAL
                    else:
                        style = getattr(Style, style_str.upper(), Style.NORMAL)

                    # Set the attributes
                    attr_name = f"{level_str}_{scheme_type}_foreground"
                    setattr(self, attr_name, fg)
                    attr_name = f"{level_str}_{scheme_type}_background"
                    setattr(self, attr_name, bg)
                    attr_name = f"{level_str}_{scheme_type}_style"
                    setattr(self, attr_name, style)

    def _create_plain_text_scheme(self):
        """
        Create a plain text color scheme with no ANSI colors.
        This sets all colors and styles to empty strings for plain text output.
        """
        # Create empty/plane text equivalents for all Fore/Back/Style attributes
        empty_fg = ""
        empty_bg = ""
        empty_style = ""

        # Set all level-specific colors to plain text
        for log_level in LogLevel:
            level_str = log_level.name.lower()

            # Set both normal and highlight variants
            for scheme_type in ["normal", "highlight"]:
                attr_name = f"{level_str}_{scheme_type}_foreground"
                setattr(self, attr_name, empty_fg)
                attr_name = f"{level_str}_{scheme_type}_background"
                setattr(self, attr_name, empty_bg)
                attr_name = f"{level_str}_{scheme_type}_style"
                setattr(self, attr_name, empty_style)

        # Set special colors to plain text as well
        for special in ['default', 'bracket_color', 'timestamp_color', 'process_color', 'comment_color', 'operator_color']:
            setattr(self, f'{special}_foreground', empty_fg)
            setattr(self, f'{special}_background', empty_bg)
            setattr(self, f'{special}_style', empty_style)
            setattr(self, f'{special}_highlight_foreground', empty_fg)
            setattr(self, f'{special}_highlight_background', empty_bg)
            setattr(self, f'{special}_highlight_style', empty_style)

        self.field_order = ["timestamp", "pid", "tid", "level", "message"]

    def save_to_json(self, file_path: Path) -> None:
        """
        Save the current color scheme configuration to a JSON file.

        :param file_path: path to save the JSON configuration
        """
        import json

        # Build the JSON structure
        config = {}

        # Process level-specific colors
        for log_level in LogLevel:
            level_name = log_level.name.lower()
            level_config = {}

            # Get normal and highlight schemes
            for scheme_type in ['normal', 'highlight']:
                fg_attr = f"{level_name}_{scheme_type}_foreground"
                bg_attr = f"{level_name}_{scheme_type}_background"
                style_attr = f"{level_name}_{scheme_type}_style"

                fg_value = getattr(self, fg_attr, '')
                bg_value = getattr(self, bg_attr, '')
                style_value = getattr(self, style_attr, '')

                # Convert ANSI codes back to color names
                fg_name = self._ansi_to_color_name(fg_value)
                bg_name = self._ansi_to_color_name(bg_value)
                style_name = self._ansi_to_style_name(style_value)

                level_config[scheme_type] = {
                    "foreground": fg_name,
                    "background": bg_name,
                    "style": style_name
                }

            config[level_name] = level_config

        # Process special colors
        special_config = {}
        special_types = ['default', 'bracket_color', 'timestamp_color', 'operator_color', 'process_color', 'comment_color']

        for special_type in special_types:
            fg_attr = f"{special_type}_foreground"
            bg_attr = f"{special_type}_background"
            style_attr = f"{special_type}_style"

            fg_value = getattr(self, fg_attr, '')
            bg_value = getattr(self, bg_attr, '')
            style_value = getattr(self, style_attr, '')

            fg_name = self._ansi_to_color_name(fg_value)
            bg_name = self._ansi_to_color_name(bg_value)
            style_name = self._ansi_to_style_name(style_value)

            special_config[special_type] = {
                "foreground": fg_name,
                "background": bg_name,
                "style": style_name
            }

        config["special"] = special_config
        config["fields"] = getattr(self, 'field_order', ["timestamp", "pid", "tid", "level", "message"])

        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

    @staticmethod
    def _ansi_to_color_name(ansi_code: str) -> str:
        """
        Convert ANSI color code back to color name.
        :param ansi_code: ANSI escape sequence
        :return: color name string
        """
        # Import colorama modules to get exact ANSI codes
        from colorama import Fore, Back

        # Map ANSI codes to color names (foregrounds)
        ansi_to_color = {
            Fore.BLACK: 'BLACK',
            Fore.RED: 'RED',
            Fore.GREEN: 'GREEN',
            Fore.YELLOW: 'YELLOW',
            Fore.BLUE: 'BLUE',
            Fore.MAGENTA: 'MAGENTA',
            Fore.CYAN: 'CYAN',
            Fore.WHITE: 'WHITE',
            Fore.LIGHTBLACK_EX: 'LIGHTBLACK_EX',
            Fore.LIGHTRED_EX: 'LIGHTRED_EX',
            Fore.LIGHTGREEN_EX: 'LIGHTGREEN_EX',
            Fore.LIGHTYELLOW_EX: 'LIGHTYELLOW_EX',
            Fore.LIGHTBLUE_EX: 'LIGHTBLUE_EX',
            Fore.LIGHTMAGENTA_EX: 'LIGHTMAGENTA_EX',
            Fore.LIGHTCYAN_EX: 'LIGHTCYAN_EX',
            Fore.LIGHTWHITE_EX: 'LIGHTWHITE_EX',
        }

        # Check backgrounds too
        bg_to_color = {
            Back.BLACK: 'BLACK',
            Back.RED: 'RED',
            Back.GREEN: 'GREEN',
            Back.YELLOW: 'YELLOW',
            Back.BLUE: 'BLUE',
            Back.MAGENTA: 'MAGENTA',
            Back.CYAN: 'CYAN',
            Back.WHITE: 'WHITE',
        }

        # Try foreground colors first, then backgrounds
        return ansi_to_color.get(ansi_code, bg_to_color.get(ansi_code, ""))

    @staticmethod
    def _ansi_to_style_name(ansi_code: str) -> str:
        """
        Convert ANSI style code back to style name.
        :param ansi_code: ANSI escape sequence
        :return: style name string
        """
        # Map ANSI codes to style names
        ansi_to_style = {
            '\x1b[1m': 'BRIGHT',
            '\x1b[2m': 'DIM',
            '\x1b[22m': 'NORMAL',
        }
        return ansi_to_style.get(ansi_code, "NORMAL")
