#!/usr/bin/env python3
# Repository:   https://github.com/Python-utilities
# File Name:    test/test_log_channel_abc.py
# Description:  Unit tests for LogChannelABC
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
from unittest.mock import patch, MagicMock

from flashlogger.log_channel_abc import LogChannelABC, OutputFormat
from flashlogger.log_levels import LogLevel


class MockLogChannel(LogChannelABC):
    """Concrete implementation of LogChannelABC for testing."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logged_messages = []

    def do_log(self, log_level, *args, **kwargs):
        self.logged_messages.append((log_level, args, kwargs))


class LogChannelABCTests(unittest.TestCase):

    def setUp(self):
        """Reset shared logger before each test."""
        LogChannelABC._shared_logger = None

    def test_get_shared_logger_creates_logger(self):
        """Test get_shared_logger creates a logger instance."""
        logger = LogChannelABC.get_shared_logger()
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.level, logging.DEBUG)

    def test_get_shared_logger_singleton(self):
        """Test get_shared_logger returns the same instance."""
        logger1 = LogChannelABC.get_shared_logger()
        logger2 = LogChannelABC.get_shared_logger()
        self.assertIs(logger1, logger2)

    def test_configure_shared_logger(self):
        """Test configure_shared_logger sets level and format."""
        LogChannelABC.configure_shared_logger(
            level=logging.INFO,
            format_str="[%(levelname)s] %(message)s"
        )

        logger = LogChannelABC.get_shared_logger()
        self.assertEqual(logger.level, logging.INFO)

    @patch('flashlogger.log_channel_abc.LogChannelABC.get_shared_logger')
    def test_configure_shared_logger_format(self, mock_get_logger):
        """Test configure_shared_logger sets formatter."""
        mock_logger = MagicMock()
        # Mock an existing handler in handlers list
        mock_existing_handler = MagicMock()
        mock_logger.handlers = [mock_existing_handler]
        mock_get_logger.return_value = mock_logger

        LogChannelABC.configure_shared_logger(format_str="[%(levelname)s] %(message)s")

        mock_logger.removeHandler.assert_called_once_with(mock_existing_handler)
        mock_logger.addHandler.assert_called_once()
        self.assertFalse(mock_logger.propagate)

    def test_init_default_all_levels_loggable(self):
        """Test default initialization allows all levels."""
        channel = MockLogChannel()
        for level in LogLevel:
            self.assertTrue(channel.is_loggable(level))

    def test_init_minimum_log_level_threshold(self):
        """Test minimum_log_level sets threshold."""
        channel = MockLogChannel(minimum_log_level=LogLevel.WARNING)

        # Should log WARNING and above
        self.assertFalse(channel.is_loggable(LogLevel.DEBUG))
        self.assertFalse(channel.is_loggable(LogLevel.INFO))
        self.assertTrue(channel.is_loggable(LogLevel.WARNING))
        self.assertTrue(channel.is_loggable(LogLevel.ERROR))

    def test_init_minimum_log_level_string(self):
        """Test minimum_log_level accepts string."""
        channel = MockLogChannel(minimum_log_level="ERROR")
        self.assertFalse(channel.is_loggable(LogLevel.WARNING))
        self.assertTrue(channel.is_loggable(LogLevel.ERROR))

    def test_init_minimum_log_level_int(self):
        """Test minimum_log_level accepts int."""
        channel = MockLogChannel(minimum_log_level=logging.ERROR)
        self.assertFalse(channel.is_loggable(LogLevel.WARNING))
        self.assertTrue(channel.is_loggable(LogLevel.ERROR))

    def test_init_include_log_levels(self):
        """Test include_log_levels specifies allowed levels."""
        channel = MockLogChannel(include_log_levels=[LogLevel.INFO, LogLevel.ERROR])

        self.assertTrue(channel.is_loggable(LogLevel.INFO))
        self.assertTrue(channel.is_loggable(LogLevel.ERROR))
        self.assertFalse(channel.is_loggable(LogLevel.DEBUG))
        self.assertFalse(channel.is_loggable(LogLevel.WARNING))

    def test_init_include_log_levels_strings(self):
        """Test include_log_levels accepts strings."""
        channel = MockLogChannel(include_log_levels=["info", "error"])

        self.assertTrue(channel.is_loggable(LogLevel.INFO))
        self.assertTrue(channel.is_loggable(LogLevel.ERROR))
        self.assertFalse(channel.is_loggable(LogLevel.DEBUG))

    def test_init_include_log_levels_ints(self):
        """Test include_log_levels accepts ints."""
        channel = MockLogChannel(include_log_levels=[logging.INFO, logging.ERROR])

        self.assertTrue(channel.is_loggable(LogLevel.INFO))
        self.assertTrue(channel.is_loggable(LogLevel.ERROR))

    def test_init_exclude_log_levels(self):
        """Test exclude_log_levels blocks specified levels."""
        channel = MockLogChannel(exclude_log_levels=[LogLevel.DEBUG, LogLevel.INFO])

        self.assertFalse(channel.is_loggable(LogLevel.DEBUG))
        self.assertFalse(channel.is_loggable(LogLevel.INFO))
        self.assertTrue(channel.is_loggable(LogLevel.WARNING))

    def test_init_exclude_log_levels_strings(self):
        """Test exclude_log_levels accepts strings."""
        channel = MockLogChannel(exclude_log_levels=["debug", "info"])

        self.assertFalse(channel.is_loggable(LogLevel.DEBUG))
        self.assertFalse(channel.is_loggable(LogLevel.INFO))

    def test_exclude_log_levels_dict_syntax(self):
        """Test exclude_log_levels with {"exclude": [...]} syntax."""
        channel = MockLogChannel(minimum_log_level={"exclude": [LogLevel.DEBUG, LogLevel.INFO]})

        self.assertFalse(channel.is_loggable(LogLevel.DEBUG))
        self.assertFalse(channel.is_loggable(LogLevel.INFO))
        self.assertTrue(channel.is_loggable(LogLevel.WARNING))

    def test_minimal_log_level_property_getter(self):
        """Test minimal_log_level property getter."""
        channel = MockLogChannel(minimum_log_level=LogLevel.WARNING)
        loggable_levels = channel.minimal_log_level
        self.assertIsInstance(loggable_levels, set)
        self.assertIn(LogLevel.WARNING, loggable_levels)
        self.assertNotIn(LogLevel.DEBUG, loggable_levels)

    def test_minimal_log_level_property_setter_threshold(self):
        """Test minimal_log_level property setter with threshold."""
        channel = MockLogChannel()
        channel.minimal_log_level = LogLevel.WARNING

        self.assertFalse(channel.is_loggable(LogLevel.DEBUG))
        self.assertTrue(channel.is_loggable(LogLevel.WARNING))

    def test_minimal_log_level_property_setter_inclusion(self):
        """Test minimal_log_level property setter with inclusion list."""
        channel = MockLogChannel()
        channel.minimal_log_level = [LogLevel.INFO, LogLevel.ERROR]

        self.assertTrue(channel.is_loggable(LogLevel.INFO))
        self.assertTrue(channel.is_loggable(LogLevel.ERROR))
        self.assertFalse(channel.is_loggable(LogLevel.DEBUG))

    def test_minimal_log_level_property_setter_exclusion(self):
        """Test minimal_log_level property setter with exclusion dict."""
        channel = MockLogChannel()
        channel.minimal_log_level = {"exclude": [LogLevel.DEBUG, LogLevel.INFO]}

        self.assertFalse(channel.is_loggable(LogLevel.DEBUG))
        self.assertFalse(channel.is_loggable(LogLevel.INFO))
        self.assertTrue(channel.is_loggable(LogLevel.WARNING))

    def test_is_loggable_by_string(self):
        """Test is_loggable accepts string log levels."""
        channel = MockLogChannel(minimum_log_level=LogLevel.WARNING)

        self.assertFalse(channel.is_loggable("DEBUG"))
        self.assertTrue(channel.is_loggable("WARNING"))

    def test_is_loggable_by_int(self):
        """Test is_loggable accepts int log levels."""
        channel = MockLogChannel(minimum_log_level=LogLevel.WARNING)

        self.assertFalse(channel.is_loggable(logging.DEBUG))
        self.assertTrue(channel.is_loggable(logging.WARNING))

    def test_do_log_not_implemented_in_abstract_class(self):
        """Test that abstract class cannot be instantiated without implementing do_log."""
        class PartialChannel(LogChannelABC):
            pass

        with self.assertRaises(TypeError):
            PartialChannel()

    def test_output_format_default(self):
        """Test default output_format is HUMAN_READABLE."""
        channel = MockLogChannel()
        self.assertEqual(channel.output_format, OutputFormat.HUMAN_READABLE)

    def test_output_format_enum_values(self):
        """Test OutputFormat enum has expected values."""
        self.assertEqual(OutputFormat.HUMAN_READABLE.name, 'HUMAN_READABLE')
        self.assertEqual(OutputFormat.JSON_PRETTY.name, 'JSON_PRETTY')
        self.assertEqual(OutputFormat.JSON_LINES.name, 'JSON_LINES')
        self.assertEqual(len(OutputFormat), 3)

    def test_field_order_default(self):
        """Test default field_order."""
        channel = MockLogChannel()
        expected = ["timestamp", "pid", "tid", "level", "message"]
        self.assertEqual(channel.field_order, expected)


if __name__ == '__main__':
    unittest.main()
