#!/usr/bin/env python3
# Repository:   https://github.com/PyFlashLogger
# File Name:    test/test_color_scheme.py
# Description:  Unit tests for ColorScheme functionality
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
# @date: 2025-10-24
# @author: Dieter J Kybelksties

import unittest
from pathlib import Path

from flashlogger.color_scheme import ColorScheme, Field
from flashlogger.log_levels import LogLevel


class ColorSchemeTests(unittest.TestCase):

    def test_get_with_string_parameter(self):
        """Test get() method with string parameters."""
        cs = ColorScheme(ColorScheme.Default.COLOR)

        # Test string parameters
        self.assertIsInstance(cs.get("info"), str)
        self.assertIsInstance(cs.get("warning"), str)
        self.assertIsInstance(cs.get("message"), str)

        # Should start with ANSI escape codes
        color_code = cs.get("info")
        self.assertTrue(color_code.startswith('\x1b['))

        # Should contain ANSI escape sequences
        self.assertIn('\x1b[', color_code)

    def test_get_with_log_level_enum(self):
        """Test get() method with LogLevel enum parameters."""
        cs = ColorScheme(ColorScheme.Default.COLOR)

        debug_color = cs.get(LogLevel.DEBUG)
        info_color = cs.get(LogLevel.INFO)
        error_color = cs.get(LogLevel.ERROR)

        self.assertIsInstance(debug_color, str)
        self.assertIsInstance(info_color, str)
        self.assertIsInstance(error_color, str)

        # Different levels should have different colors
        self.assertNotEqual(debug_color, info_color)
        self.assertNotEqual(info_color, error_color)

    def test_get_with_field_enum(self):
        """Test get() method with Field enum parameters."""
        cs = ColorScheme(ColorScheme.Default.COLOR)

        timestamp_color = cs.get(Field.TIMESTAMP)
        message_color = cs.get(Field.MESSAGE)
        level_color = cs.get(Field.LEVEL)

        self.assertIsInstance(timestamp_color, str)
        self.assertIsInstance(message_color, str)
        self.assertIsInstance(level_color, str)

        # Should be different from each other
        self.assertNotEqual(timestamp_color, message_color)
        self.assertNotEqual(message_color, level_color)

    def test_get_with_inverse(self):
        """Test get() method with inverse colors."""
        cs = ColorScheme(ColorScheme.Default.COLOR)

        normal = cs.get("info")
        inverse = cs.get("info", inverse=True)

        self.assertIsInstance(inverse, str)
        self.assertNotEqual(normal, inverse)

        # Normal and inverse should use different color codes
        # (inverse colors are specifically designed for each level)
        self.assertTrue(normal.startswith('\x1b['))
        self.assertTrue(inverse.startswith('\x1b['))

    def test_get_with_style_parameter(self):
        """Test get() method with custom style parameter."""
        from colorama import Style
        cs = ColorScheme(ColorScheme.Default.COLOR)

        normal_style = cs.get("info", style=Style.NORMAL)
        bright_style = cs.get("info", style=Style.BRIGHT)

        self.assertIsInstance(normal_style, str)
        self.assertIsInstance(bright_style, str)
        self.assertNotEqual(normal_style, bright_style)

        # Bright style should include bright code
        self.assertIn('\x1b[1m', bright_style)

    def test_field_enum_values(self):
        """Test Field enum has expected values."""
        self.assertEqual(Field.OPERATOR.name, "OPERATOR")
        self.assertEqual(Field.TIMESTAMP.name, "TIMESTAMP")
        self.assertEqual(Field.PID.name, "PID")
        self.assertEqual(Field.TID.name, "TID")
        self.assertEqual(Field.FILE.name, "FILE")
        self.assertEqual(Field.LEVEL.name, "LEVEL")
        self.assertEqual(Field.MESSAGE.name, "MESSAGE")

        # Test they convert to lowercase properly
        self.assertEqual(Field.TIMESTAMP.name.lower(), "timestamp")
        self.assertEqual(Field.MESSAGE.name.lower(), "message")

    def test_all_levels_attribute(self):
        """Test all_levels attribute contains all expected levels."""
        cs = ColorScheme()

        # Should include field levels and all LogLevel entries
        expected_fields = ["timestamp", "pid", "tid", "file", "level", "message"]

        for field in expected_fields:
            self.assertIn(field, cs.all_levels)

        # Should include all log levels
        for level in LogLevel:
            self.assertIn(level.name.lower(), cs.all_levels)

        # Should include custom levels
        self.assertIn("custom0", cs.all_levels)
        self.assertIn("custom9", cs.all_levels)

    def test_default_color_schemes(self):
        """Test different default color schemes."""
        color_cs = ColorScheme(ColorScheme.Default.COLOR)
        bw_cs = ColorScheme(ColorScheme.Default.BLACK_AND_WHITE)
        plain_cs = ColorScheme(ColorScheme.Default.PLAIN_TEXT)

        # All should be ColorScheme instances
        self.assertIsInstance(color_cs, ColorScheme)
        self.assertIsInstance(bw_cs, ColorScheme)
        self.assertIsInstance(plain_cs, ColorScheme)

        # They should have different colors for the same level
        color_info = color_cs.get("info")
        bw_info = bw_cs.get("info")
        plain_info = plain_cs.get("info")

        # Color and BW should have ANSI codes
        self.assertTrue(color_info.startswith('\x1b['))
        self.assertTrue(bw_info.startswith('\x1b['))

        # Plain text style should be normal (no color codes beyond style)
        self.assertEqual(plain_info, "\x1b[22m")

    def test_load_from_config_json(self):
        """Test loading color scheme from JSON config file."""
        # Use existing config file
        config_path = Path(__file__).parent.parent / "flashlogger" / "config" / "color_scheme_color.json"
        cs = ColorScheme(colorscheme_json=config_path)

        self.assertIsInstance(cs, ColorScheme)
        # Should have loaded colors
        info_color = cs.get("info")
        self.assertIsInstance(info_color, str)
        self.assertTrue(len(info_color) > 0)

    def test_invalid_default_scheme(self):
        """Test error handling for invalid default scheme."""
        with self.assertRaises(ValueError):
            ColorScheme(default_scheme="INVALID")

    def test_get_unknown_level_fallback(self):
        """Test get() with unknown level doesn't crash."""
        cs = ColorScheme()

        # Should handle unknown level gracefully
        unknown_color = cs.get("unknown_level")
        self.assertIsInstance(unknown_color, str)

        # Should still work for inverse
        unknown_inverse = cs.get("unknown_level", inverse=True)
        self.assertIsInstance(unknown_inverse, str)

    def test_custom_log_levels_have_inverse(self):
        """Test that custom log levels have inverse colors defined."""
        cs = ColorScheme(ColorScheme.Default.COLOR)

        for i in range(10):
            level_name = f"custom{i}"
            normal_color = cs.get(level_name)
            inverse_color = cs.get(level_name, inverse=True)

            self.assertIsInstance(normal_color, str)
            self.assertIsInstance(inverse_color, str)
            self.assertNotEqual(normal_color, inverse_color)

    def test_ansi_escape_codes_in_colors(self):
        """Test that colors contain proper ANSI escape codes."""
        cs = ColorScheme(ColorScheme.Default.COLOR)

        # Regular color scheme should have ANSI codes
        info_color = cs.get("info")
        self.assertIn('\x1b[', info_color)  # ESC [
        self.assertIn('\x1b[22m', info_color)  # Normal style reset

    def test_plain_text_has_no_ansi_codes(self):
        """Test that plain text scheme has no ANSI codes."""
        cs = ColorScheme(ColorScheme.Default.PLAIN_TEXT)

        # Plain text should have no escape codes
        colors = []
        for level in cs.all_levels:
            color = cs.get(level)
            colors.append(color)
            # Should not contain ANSI escape codes
            self.assertEqual(color, "\x1b[22m")  # Only the style reset

if __name__ == '__main__':
    unittest.main()
