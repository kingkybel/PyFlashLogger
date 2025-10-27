#!/usr/bin/env python3
# Repository:   https://github.com/Python-utilities
# File Name:    test/test_log_channel_console.py
# Description:  Unit tests for LogChannelConsole
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

import logging
import unittest
from unittest.mock import patch, MagicMock

import json

from flashlogger.color_scheme import ColorScheme
from flashlogger.log_channel_abc import OutputFormat
from flashlogger.log_channel_console import LogChannelConsole, ConsoleFormatter
from flashlogger.log_levels import LogLevel


class ConsoleFormatterTests(unittest.TestCase):

    def test_format_regular_message(self):
        """Test formatting regular log messages."""
        formatter = ConsoleFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Test message", args=(), exc_info=None
        )
        record.levelno = LogLevel.INFO.logging_level()

        result = formatter.format(record)
        self.assertIn("Test message", result)
        # Should not have special formatting for regular levels

    def test_format_command_message(self):
        """Test formatting command messages."""
        formatter = ConsoleFormatter()
        record = logging.LogRecord(
            name="test", level=LogLevel.COMMAND.logging_level(), pathname="", lineno=0,
            msg="ls -la", args=(), exc_info=None
        )
        record.levelno = LogLevel.COMMAND.logging_level()

        result = formatter.format(record)
        self.assertIn("ls -la", result)
        # Should include the command message

    def test_format_with_color_scheme(self):
        """Test that formatter applies color scheme."""
        color_scheme = ColorScheme()
        formatter = ConsoleFormatter(color_scheme=color_scheme)
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0,
            msg="Error message", args=(), exc_info=None
        )
        record.levelno = LogLevel.ERROR.logging_level()

        result = formatter.format(record)
        self.assertIn("Error message", result)
        # Should have color codes (escape sequences)
        # But we can't easily test the exact colors without mocking color_scheme

    def test_format_time_high_precision(self):
        """Test that formatTime adds milliseconds."""
        formatter = ConsoleFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test", args=(), exc_info=None
        )
        record.created = 1234567890.123456
        record.msecs = 123.456

        time_str = formatter.formatTime(record)
        self.assertIn("00123", time_str)  # Based on int(record.msecs) formatted as 05d

    @patch('flashlogger.log_channel_console.ColorScheme')
    def test_color_level_methods(self, mock_color_scheme):
        """Test that formatter has get_normal_color and get_highlight_color methods."""
        mock_color_scheme.return_value = MagicMock()
        # Test that the methods are available
        formatter = ConsoleFormatter()
        self.assertTrue(hasattr(formatter, 'get_normal_color'))
        self.assertTrue(hasattr(formatter, 'get_highlight_color'))
        self.assertTrue(hasattr(formatter, 'normal_colors'))
        self.assertTrue(hasattr(formatter, 'highlight_colors'))

    def test_format_json_pretty(self):
        """Test JSON pretty format."""
        formatter = ConsoleFormatter(output_format=OutputFormat.JSON_PRETTY)
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Test message", args=(), exc_info=None
        )
        record.levelno = LogLevel.INFO.logging_level()
        record.process = 12345
        record.thread = 67890

        result = formatter.format(record)
        parsed = json.loads(result)
        self.assertEqual(parsed["message"], "Test message")
        self.assertEqual(parsed["level"], "info")
        self.assertIn("timestamp", parsed)
        self.assertEqual(parsed["pid"], 12345)
        self.assertEqual(parsed["tid"], 67890)
        # Should be pretty-printed (indented)
        lines = result.split('\n')
        self.assertTrue(len(lines) > 1)  # Should have multiple lines

    def test_format_json_lines(self):
        """Test JSON lines format (compact)."""
        formatter = ConsoleFormatter(output_format=OutputFormat.JSON_LINES)
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Test message", args=(), exc_info=None
        )
        record.levelno = LogLevel.INFO.logging_level()
        record.process = 12345
        record.thread = 67890

        result = formatter.format(record)
        parsed = json.loads(result)
        self.assertEqual(parsed["message"], "Test message")
        self.assertEqual(parsed["level"], "info")
        # Should be compact (single line)
        self.assertNotIn('\n', result)

    def test_format_human_readable_default(self):
        """Test default format is human readable."""
        formatter = ConsoleFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Test message", args=(), exc_info=None
        )
        record.levelno = LogLevel.INFO.logging_level()

        result = formatter.format(record)
        self.assertIn("Test message", result)
        # Should not be JSON
        self.assertNotIn('"message"', result)


class LogChannelConsoleTests(unittest.TestCase):

    def setUp(self):
        """Reset any static/global state."""
        # Ensure we start with clean static flags
        if hasattr(LogChannelConsole, '_handler_added'):
            delattr(LogChannelConsole, '_handler_added')

    @patch('flashlogger.log_channel_console.LogChannelConsole.get_shared_logger')
    def test_init_use_shared_logger(self, mock_get_logger):
        """Test initialization with shared logger."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        channel = LogChannelConsole(use_shared_logger=True)

        # Should configure shared logger
        mock_get_logger.assert_called()
        self.assertEqual(channel._logger, mock_logger)

    @patch('sys.stderr')
    @patch('logging.getLogger')
    def test_init_use_instance_logger(self, mock_get_logger, mock_stderr):
        """Test initialization with instance logger (legacy mode)."""
        mock_root_logger = MagicMock()
        mock_get_logger.return_value = mock_root_logger

        channel = LogChannelConsole(use_shared_logger=False)

        # Should configure root logger
        mock_get_logger.assert_called()
        self.assertEqual(channel._logger, mock_root_logger)

    def test_init_with_color_scheme(self):
        """Test initialization with custom color scheme."""
        color_scheme = ColorScheme()
        channel = LogChannelConsole(color_scheme=color_scheme)

        # Color scheme should be stored (though formatter creation is lazy)
        self.assertEqual(channel.color_scheme, color_scheme)

    def test_init_with_default_color_scheme(self):
        """Test initialization with default color scheme."""
        channel = LogChannelConsole()

        self.assertIsInstance(channel.color_scheme, ColorScheme)

    @patch('flashlogger.log_channel_console.ColorScheme')
    def test_default_color_scheme_creation(self, mock_color_scheme_class):
        """Test that a ColorScheme is created if none provided."""
        mock_color_scheme_class.return_value = MagicMock()

        channel = LogChannelConsole()

        mock_color_scheme_class.assert_called_once()

    def test_level_filtering_inherited(self):
        """Test that log level filtering is inherited from ABC."""
        channel = LogChannelConsole(minimum_log_level=LogLevel.WARNING)

        self.assertFalse(channel.is_loggable(LogLevel.DEBUG))
        self.assertTrue(channel.is_loggable(LogLevel.WARNING))

    @patch('flashlogger.log_channel_console.LogChannelConsole.get_shared_logger')
    def test_do_log_calls_underlying_logger(self, mock_get_logger):
        """Test do_log delegates to underlying logger."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        channel = LogChannelConsole(minimum_log_level=LogLevel.INFO)
        channel.do_log(LogLevel.INFO, "Test message", "extra")

        mock_logger.log.assert_called_once_with(
            LogLevel.INFO.logging_level(), "Test message", "extra"
        )

    @patch('flashlogger.log_channel_console.LogChannelConsole.get_shared_logger')
    def test_do_log_respects_level_filter(self, mock_get_logger):
        """Test do_log respects log level filtering."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        channel = LogChannelConsole(minimum_log_level=LogLevel.WARNING)

        # Should not log DEBUG message
        channel.do_log(LogLevel.DEBUG, "Debug message")
        mock_logger.log.assert_not_called()

        # Should log WARNING message
        channel.do_log(LogLevel.WARNING, "Warning message")
        mock_logger.log.assert_called_once()

    @patch('flashlogger.log_channel_console.LogChannelConsole.get_shared_logger')
    def test_do_log_with_string_level(self, mock_get_logger):
        """Test do_log accepts string level."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        channel = LogChannelConsole()
        channel.do_log("INFO", "Test message")

        mock_logger.log.assert_called_once_with(
            LogLevel.INFO.logging_level(), "Test message"
        )

    @patch('logging.getLogger')
    def test_legacy_logger_mode_static_handler(self, mock_get_logger):
        """Test that legacy mode adds handler only once."""
        with patch('flashlogger.log_channel_console.logging.StreamHandler') as mock_handler:
            # First instance
            LogChannelConsole(use_shared_logger=False)
            # Second instance
            LogChannelConsole(use_shared_logger=False)

            # StreamHandler should only be created once
            self.assertEqual(mock_handler.call_count, 1)

    @patch('flashlogger.log_channel_console.LogChannelConsole.get_shared_logger')
    def test_init_with_output_format_json(self, mock_get_logger):
        """Test initialization with JSON output format."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        channel = LogChannelConsole(output_format=OutputFormat.JSON_PRETTY)

        self.assertEqual(channel.output_format, OutputFormat.JSON_PRETTY)

    def test_init_with_output_format_string(self):
        """Test initialization with output format as string."""
        channel = LogChannelConsole(output_format="JSON_LINES")

        self.assertEqual(channel.output_format, OutputFormat.JSON_LINES)

    def test_init_default_output_format(self):
        """Test default output format."""
        channel = LogChannelConsole()

        self.assertEqual(channel.output_format, OutputFormat.HUMAN_READABLE)


if __name__ == '__main__':
    unittest.main()
