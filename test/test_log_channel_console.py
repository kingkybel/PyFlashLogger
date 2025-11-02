#!/usr/bin/env python3
# Repository:   https://github.com/PyFlashLogger
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
from pathlib import Path

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
    def test_color_level_methods(self, _mock_color_scheme):
        """Test that formatter uses simplified ColorScheme."""
        # Test that the simplified color scheme methods work
        formatter = ConsoleFormatter()
        # Should not have old methods
        self.assertFalse(hasattr(formatter, 'get_normal_color'))
        self.assertFalse(hasattr(formatter, 'get_highlight_color'))
        self.assertFalse(hasattr(formatter, 'normal_colors'))
        self.assertFalse(hasattr(formatter, 'highlight_colors'))
        # Should have set_level_color method
        self.assertTrue(hasattr(formatter, 'set_level_color'))
        self.assertTrue(callable(getattr(formatter, 'set_level_color')))

    def test_format_json_pretty(self):
        """Test JSON pretty format."""
        from flashlogger.log_channel_abc import LogChannelABC
        mock_channel = MagicMock(spec=LogChannelABC)
        mock_channel.process_id = 12345
        mock_channel.thread_id = 67890
        formatter = ConsoleFormatter(output_format=OutputFormat.JSON_PRETTY, channel=mock_channel)
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Test message", args=(), exc_info=None
        )
        record.levelno = LogLevel.INFO.logging_level()

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
        from flashlogger.log_channel_abc import LogChannelABC
        mock_channel = MagicMock(spec=LogChannelABC)
        mock_channel.process_id = 12345
        mock_channel.thread_id = 67890
        formatter = ConsoleFormatter(output_format=OutputFormat.JSON_LINES, channel=mock_channel)
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Test message", args=(), exc_info=None
        )
        record.levelno = LogLevel.INFO.logging_level()

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
            LogLevel.INFO.logging_level(), "Test message", "extra", extra={}
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
            LogLevel.INFO.logging_level(), "Test message", extra={}
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

    def test_set_color_scheme_with_enum(self):
        """Test set_color_scheme with ColorScheme.Default enum."""
        channel = LogChannelConsole()

        original_color_scheme = channel.color_scheme

        # Change to black and white
        channel.set_color_scheme(ColorScheme.Default.BLACK_AND_WHITE)

        # Color scheme should have changed
        self.assertNotEqual(channel.color_scheme, original_color_scheme)
        self.assertIsNotNone(channel.color_scheme.get("info"))

        # Change back to color
        channel.set_color_scheme(ColorScheme.Default.COLOR)
        self.assertNotEqual(channel.color_scheme, original_color_scheme)

    def test_set_color_scheme_with_path(self):
        """Test set_color_scheme with config file path."""
        channel = LogChannelConsole()
        config_path = Path(__file__).parent.parent / "flashlogger" / "config" / "color_scheme_bw.json"

        original_color_scheme = channel.color_scheme

        # Change to file path
        channel.set_color_scheme(config_path)
        self.assertNotEqual(channel.color_scheme, original_color_scheme)

    def test_set_color_scheme_with_color_scheme_instance(self):
        """Test set_color_scheme with ColorScheme instance."""
        channel = LogChannelConsole()

        original_color_scheme = channel.color_scheme
        new_color_scheme = ColorScheme(ColorScheme.Default.PLAIN_TEXT)

        # Change to instance
        channel.set_color_scheme(new_color_scheme)
        self.assertEqual(channel.color_scheme, new_color_scheme)
        self.assertNotEqual(channel.color_scheme, original_color_scheme)

    def test_set_color_scheme_invalid_type(self):
        """Test set_color_scheme with invalid type raises error."""
        channel = LogChannelConsole()

        with self.assertRaises(ValueError):
            channel.set_color_scheme(123)

    def test_format_with_structured_json_args(self):
        """Test JSON formatting includes structured message arguments."""
        from flashlogger.log_channel_abc import LogChannelABC
        mock_channel = MagicMock(spec=LogChannelABC)
        mock_channel.process_id = 12345
        mock_channel.thread_id = 67890

        formatter = ConsoleFormatter(output_format=OutputFormat.JSON_PRETTY, channel=mock_channel)

        # Create a log record that would result from log_info("test", "arg1", key="value")
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test", args=("arg1",), exc_info=None
        )
        record.levelno = LogLevel.INFO.logging_level()
        # Simulate kwargs stored in record.__dict__
        record.key = "value"

        result = formatter.format(record)
        parsed = json.loads(result)

        # Should have the standard JSON fields
        self.assertEqual(parsed["message"], "test")
        self.assertEqual(parsed["level"], "info")

        # Should have standard message and structured args
        self.assertEqual(parsed["message"], "test")
        self.assertEqual(parsed["message0"], "arg1")  # positional args start at message0
        self.assertEqual(parsed["key"], "value")

    def test_format_message_safe_fallback(self):
        """Test format() safely handles message formatting errors."""
        formatter = ConsoleFormatter()

        # Create a record that would cause formatting error
        # (msg with % but args don't match)
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Hello %s %s", args=("world",), exc_info=None  # Missing second arg
        )
        record.levelno = LogLevel.INFO.logging_level()

        # Should not crash - should use raw message
        result = formatter.format(record)

        # Should contain the raw message instead of crashing
        self.assertIn("Hello", result)

    def test_format_json_handles_complex_args(self):
        """Test JSON formatting handles lists, dicts, and complex objects."""
        from flashlogger.log_channel_abc import LogChannelABC
        mock_channel = MagicMock(spec=LogChannelABC)
        mock_channel.process_id = 12345
        mock_channel.thread_id = 67890

        formatter = ConsoleFormatter(output_format=OutputFormat.JSON_PRETTY, channel=mock_channel)

        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Test message", args=("arg1", [1, 2, 3], {"nested": "value"}), exc_info=None
        )
        record.levelno = LogLevel.INFO.logging_level()

        result = formatter.format(record)
        parsed = json.loads(result)

        # Should preserve structure of complex args
        self.assertEqual(parsed["message"], "Test message")
        self.assertEqual(parsed["message0"], "arg1")
        self.assertEqual(parsed["message1"], [1, 2, 3])
        self.assertEqual(parsed["message2"], {"nested": "value"})

    def test_formatter_updates_color_scheme(self):
        """Test that ConsoleFormatter color_scheme gets updated by set_color_scheme."""
        channel = LogChannelConsole()
        original_formatter_scheme = None

        # Find the ConsoleFormatter in handlers
        for handler in channel._logger.handlers:
            if isinstance(handler, logging.StreamHandler) and isinstance(handler.formatter, ConsoleFormatter):
                original_formatter_scheme = handler.formatter.color_scheme
                break

        self.assertIsNotNone(original_formatter_scheme)

        # Change color scheme via channel
        channel.set_color_scheme(ColorScheme.Default.BLACK_AND_WHITE)

        # ConsoleFormatter should be updated
        for handler in channel._logger.handlers:
            if isinstance(handler, logging.StreamHandler) and isinstance(handler.formatter, ConsoleFormatter):
                self.assertNotEqual(handler.formatter.color_scheme, original_formatter_scheme)
                break

    def test_set_output_format_string(self):
        """Test set_output_format with string parameter."""
        channel = LogChannelConsole()

        channel.set_output_format("JSON_LINES")
        self.assertEqual(channel.output_format, OutputFormat.JSON_LINES)

    def test_set_output_format_enum(self):
        """Test set_output_format with enum parameter."""
        channel = LogChannelConsole()

        channel.set_output_format(OutputFormat.JSON_PRETTY)
        self.assertEqual(channel.output_format, OutputFormat.JSON_PRETTY)

    def test_set_output_format_invalid_type(self):
        """Test set_output_format raises error for invalid type."""
        channel = LogChannelConsole()

        with self.assertRaises(ValueError):
            channel.set_output_format(123)

    def test_formatter_updates_output_format(self):
        """Test that ConsoleFormatter output_format gets updated."""
        channel = LogChannelConsole()
        original_formatter_format = None

        # Find the ConsoleFormatter in handlers
        for handler in channel._logger.handlers:
            if isinstance(handler, logging.StreamHandler) and isinstance(handler.formatter, ConsoleFormatter):
                original_formatter_format = handler.formatter.output_format
                break

        self.assertIsNotNone(original_formatter_format)

        # Change output format via channel
        channel.set_output_format(OutputFormat.JSON_LINES)

        # ConsoleFormatter should be updated
        for handler in channel._logger.handlers:
            if isinstance(handler, logging.StreamHandler) and isinstance(handler.formatter, ConsoleFormatter):
                self.assertEqual(handler.formatter.output_format, OutputFormat.JSON_LINES)
                break

    def test_logger_set_output_format_propagates(self):
        """Test that FlashLogger.set_output_format affects all channels."""
        from flashlogger.flash_logger import FlashLogger

        channel1 = LogChannelConsole()
        channel2 = LogChannelConsole()
        logger = FlashLogger([channel1, channel2])

        # Both channels should start with HUMAN_READABLE
        self.assertEqual(channel1.output_format, OutputFormat.HUMAN_READABLE)
        self.assertEqual(channel2.output_format, OutputFormat.HUMAN_READABLE)

        # Set output format on logger
        logger.set_output_format(OutputFormat.JSON_PRETTY)

        # Both channels should be updated
        self.assertEqual(channel1.output_format, OutputFormat.JSON_PRETTY)
        self.assertEqual(channel2.output_format, OutputFormat.JSON_PRETTY)

if __name__ == '__main__':
    unittest.main()
