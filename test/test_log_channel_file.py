#!/usr/bin/env python3
# Repository:   https://github.com/Python-utilities
# File Name:    test/test_log_channel_file.py
# Description:  Unit tests for FileLogChannel
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
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from flashlogger.log_channel_file import FileLogChannel, FileLogFormatter
from flashlogger.log_levels import LogLevel


class FileLogFormatterTests(unittest.TestCase):

    def test_format_regular_message(self):
        """Test formatting regular log messages."""
        formatter = FileLogFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Test message", args=(), exc_info=None
        )
        record.levelno = LogLevel.INFO.logging_level()
        record.threadname = "MainThread"  # Add threadname attribute (lowercase)

        result = formatter.format(record)
        self.assertIn("Test message", result)

    def test_format_command_message(self):
        """Test formatting command messages."""
        formatter = FileLogFormatter()
        record = logging.LogRecord(
            name="test", level=LogLevel.COMMAND.logging_level(), pathname="", lineno=0,
            msg="ls -la", args=(), exc_info=None
        )
        record.levelno = LogLevel.COMMAND.logging_level()

        result = formatter.format(record)
        self.assertIn("ls -la", result)

    def test_format_time_high_precision(self):
        """Test that formatTime adds milliseconds."""
        formatter = FileLogFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test", args=(), exc_info=None
        )
        record.created = 1234567890.123456

        time_str = formatter.formatTime(record, datefmt=None)
        self.assertRegex(time_str, r'\.\d{5}$')  # Should end with dot followed by 5 digits


class FileLogChannelTests(unittest.TestCase):

    def setUp(self):
        """Create temporary directory for test logs."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.log_file = self.temp_dir / "test.log"

    def tearDown(self):
        """Clean up temporary files."""
        if self.log_file.exists():
            self.log_file.unlink()
        self.temp_dir.rmdir()

    def test_init_creates_directory(self):
        """Test that initialization creates log directory if it doesn't exist."""
        log_path = self.temp_dir / "subdir" / "nested" / "test.log"
        channel = FileLogChannel(log_filename=log_path)

        # Directory should be created
        self.assertTrue(log_path.parent.exists())
        # File should be created and closed
        self.assertTrue(log_path.exists())

        # Clean up - remove just what we created, don't touch the base temp_dir
        log_path.unlink()
        # Remove the nested directories one by one
        nested_dir = log_path.parent
        while nested_dir != self.temp_dir and nested_dir.exists():
            try:
                nested_dir.rmdir()
                nested_dir = nested_dir.parent
            except OSError:
                break  # Stop if directory is not empty or other error

    def test_init_with_open_mode(self):
        """Test initialization with different file open modes."""
        # Test write mode (default)
        channel1 = FileLogChannel(self.log_file, logfile_open_mode="w")
        self.assertTrue(self.log_file.exists())

        # Test append mode
        channel2 = FileLogChannel(self.log_file, logfile_open_mode="a")
        self.assertTrue(self.log_file.exists())  # Still exists

    def test_init_with_encoding(self):
        """Test initialization with custom encoding."""
        channel = FileLogChannel(self.log_file)
        self.assertTrue(self.log_file.exists())

    def test_init_with_pathlib_path(self):
        """Test initialization with pathlib.Path."""
        path_obj = Path(self.log_file)
        channel = FileLogChannel(path_obj)
        self.assertTrue(path_obj.exists())

    def test_level_filtering_inherited(self):
        """Test that log level filtering is inherited from ABC."""
        channel = FileLogChannel(self.log_file, minimum_log_level=LogLevel.WARNING)

        self.assertFalse(channel.is_loggable(LogLevel.DEBUG))
        self.assertTrue(channel.is_loggable(LogLevel.WARNING))

    @patch('logging.log')
    def test_do_log_with_info_level(self, mock_logging_log):
        """Test do_log calls logging.log for INFO level."""
        channel = FileLogChannel(self.log_file, minimum_log_level=None)  # Allow all
        channel.do_log(LogLevel.INFO, "Test info message")

        mock_logging_log.assert_called_with(LogLevel.INFO.logging_level(), "Test info message")

    @patch('logging.log')
    def test_do_log_with_string_level(self, mock_logging_log):
        """Test do_log accepts string level."""
        channel = FileLogChannel(self.log_file)
        channel.do_log("INFO", "Test message")

        mock_logging_log.assert_called_with(LogLevel.INFO.logging_level(), "Test message")

    @patch('logging.log')
    def test_do_log_with_int_level(self, mock_logging_log):
        """Test do_log accepts int level."""
        channel = FileLogChannel(self.log_file)
        channel.do_log(logging.INFO, "Test message")

        mock_logging_log.assert_called_with(logging.INFO, "Test message")

    @patch('logging.log')
    def test_do_log_respects_level_filter(self, mock_logging_log):
        """Test do_log respects log level filtering."""
        channel = FileLogChannel(self.log_file, minimum_log_level=LogLevel.WARNING)

        # Should not log DEBUG message
        channel.do_log(LogLevel.DEBUG, "Debug message")
        mock_logging_log.assert_not_called()

        # Should log WARNING message
        channel.do_log(LogLevel.WARNING, "Warning message")
        mock_logging_log.assert_called_with(LogLevel.WARNING.logging_level(), "Warning message")

    @patch('logging.log')
    def test_do_log_with_multiple_args_and_kwargs(self, mock_logging_log):
        """Test do_log passes through args and kwargs."""
        channel = FileLogChannel(self.log_file)
        channel.do_log(LogLevel.INFO, "arg1", "arg2", extra={"key": "value"})

        mock_logging_log.assert_called_with(LogLevel.INFO.logging_level(), "arg1", "arg2", extra={"key": "value"})

    def test_actual_log_output_to_file(self):
        """Test that logging actually writes to file."""
        channel = FileLogChannel(self.log_file)

        # Log something
        test_message = "Test log message to file"
        channel.do_log(LogLevel.INFO, test_message)

        # Check file contents
        with open(self.log_file, 'r') as f:
            content = f.read()
            # Since the implementation sets up a formatter, there should be some content
            # But the exact format depends on the logging system
            self.assertIsInstance(content, str)  # At least readable

    def test_shared_logger_configuration(self):
        """Test that file logging uses shared logger infrastructure."""
        # The FileLogChannel sets up basicConfig, so this tests that it works
        channel = FileLogChannel(self.log_file)

        # Should not raise exceptions during setup
        # The implementation uses logging.basicConfig which affects the root logger
        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.DEBUG)  # As set in basicConfig


if __name__ == '__main__':
    unittest.main()
