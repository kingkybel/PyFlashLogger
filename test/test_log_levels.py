#!/usr/bin/env python3
# Repository:   https://github.com/Python-utilities
# File Name:    test/test_log_levels.py
# Description:  Unit tests for LogLevel enum
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
import logging
import json
import tempfile

from flashlogger.log_levels import LogLevel


class LogLevelTests(unittest.TestCase):

    def setUp(self):
        """Reset custom str representations before each test."""
        LogLevel.clear_str_reprs()
        # Reset custom levels
        LogLevel.custom_levels = [logging.NOTSET] * 10

    def test_standard_levels_exist(self):
        """Test that all standard LogLevel members exist."""
        self.assertTrue(hasattr(LogLevel, 'NOTSET'))
        self.assertTrue(hasattr(LogLevel, 'DEBUG'))
        self.assertTrue(hasattr(LogLevel, 'INFO'))
        self.assertTrue(hasattr(LogLevel, 'WARNING'))
        self.assertTrue(hasattr(LogLevel, 'ERROR'))
        self.assertTrue(hasattr(LogLevel, 'FATAL'))
        self.assertTrue(hasattr(LogLevel, 'CRITICAL'))

    def test_command_levels_exist(self):
        """Test that command-related levels exist."""
        self.assertTrue(hasattr(LogLevel, 'COMMAND'))
        self.assertTrue(hasattr(LogLevel, 'COMMAND_OUTPUT'))
        self.assertTrue(hasattr(LogLevel, 'COMMAND_STDERR'))

    def test_custom_levels_exist(self):
        """Test that custom levels exist."""
        for i in range(10):
            self.assertTrue(hasattr(LogLevel, f'CUSTOM{i}'))

    def test_logging_level_mapping(self):
        """Test logging_level() method returns correct values."""
        self.assertEqual(LogLevel.NOTSET.logging_level(), logging.NOTSET)
        self.assertEqual(LogLevel.DEBUG.logging_level(), logging.DEBUG)
        self.assertEqual(LogLevel.INFO.logging_level(), logging.INFO)
        self.assertEqual(LogLevel.WARNING.logging_level(), logging.WARNING)
        self.assertEqual(LogLevel.ERROR.logging_level(), logging.ERROR)
        self.assertEqual(LogLevel.CRITICAL.logging_level(), logging.CRITICAL)

    def test_custom_level_assignment(self):
        """Test custom_level() method assigns custom levels correctly."""
        # Test assigning to first available slot
        level = LogLevel.custom_level(777)
        self.assertEqual(level, LogLevel.CUSTOM0)
        self.assertEqual(level.logging_level(), 777)

        # Test finding existing custom level
        same_level = LogLevel.custom_level(777)
        self.assertEqual(same_level, LogLevel.CUSTOM0)

    def test_custom_level_negative_returns_notset(self):
        """Test that negative levels return NOTSET."""
        level = LogLevel.custom_level(-5)
        self.assertEqual(level, LogLevel.NOTSET)

    def test_custom_level_no_slots_raises_error(self):
        """Test that custom_level raises error when no slots available."""
        # Fill all custom slots
        for i in range(10):
            LogLevel.custom_levels[i] = i + 100

        with self.assertRaises(ValueError):
            LogLevel.custom_level(999)

    def test_custom_level_matches_standard(self):
        """Test that custom_level returns standard levels when they match."""
        level = LogLevel.custom_level(logging.DEBUG)
        self.assertEqual(level, LogLevel.DEBUG)

    def test_str_default_representation(self):
        """Test default string representation."""
        self.assertEqual(str(LogLevel.INFO), "info")
        self.assertEqual(str(LogLevel.DEBUG), "debug")
        self.assertEqual(str(LogLevel.CUSTOM0), "custom0")

    def test_set_str_repr_single(self):
        """Test setting custom string representation for single level."""
        LogLevel.set_str_repr(LogLevel.INFO, "INFORMATION")
        self.assertEqual(str(LogLevel.INFO), "INFORMATION")
        # Other levels should remain unchanged
        self.assertEqual(str(LogLevel.DEBUG), "debug")

    def test_set_str_reprs_multiple(self):
        """Test setting custom string representations for multiple levels."""
        str_map = {
            LogLevel.INFO: "INFORMATION",
            LogLevel.ERROR: "FAILURE"
        }
        LogLevel.set_str_reprs(str_map)
        self.assertEqual(str(LogLevel.INFO), "INFORMATION")
        self.assertEqual(str(LogLevel.ERROR), "FAILURE")
        self.assertEqual(str(LogLevel.DEBUG), "debug")

    def test_clear_str_reprs(self):
        """Test clearing custom string representations."""
        LogLevel.set_str_repr(LogLevel.INFO, "CUSTOM_INFO")
        self.assertEqual(str(LogLevel.INFO), "CUSTOM_INFO")

        LogLevel.clear_str_reprs()
        self.assertEqual(str(LogLevel.INFO), "info")

    def test_load_str_reprs_from_json(self):
        """Test loading string representations from JSON file."""
        json_data = {
            "info": "INFORMATION",
            "error": "PROBLEM"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            json_file = f.name

        try:
            LogLevel.load_str_reprs_from_json(json_file)
            self.assertEqual(str(LogLevel.INFO), "INFORMATION")
            self.assertEqual(str(LogLevel.ERROR), "PROBLEM")
            self.assertEqual(str(LogLevel.DEBUG), "debug")  # Unchanged
        finally:
            import os
            os.unlink(json_file)

    def test_load_str_reprs_from_json_invalid_file(self):
        """Test behavior when JSON file has invalid entries."""
        json_data = {
            "nonexistent_level": "VALUE",
            "info": "INFORMATION"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            json_file = f.name

        try:
            LogLevel.load_str_reprs_from_json(json_file)
            # Should only set levels that exist
            self.assertEqual(str(LogLevel.INFO), "INFORMATION")
            self.assertEqual(str(LogLevel.DEBUG), "debug")  # Unchanged
        finally:
            import os
            os.unlink(json_file)

    def test_extended_flag_behavior(self):
        """Test basic ExtendedFlag behavior."""
        # LogLevel should support bitwise operations if ExtendedFlag supports it
        # But mainly test that it's an instance
        self.assertIsInstance(LogLevel.INFO, LogLevel)


if __name__ == '__main__':
    unittest.main()
