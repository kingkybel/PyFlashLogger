#!/usr/bin/env python3
# Repository:   https://github.com/Python-utilities
# File Name:    test/test_flash_logger.py
# Description:  Unit tests for FlashLogger
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
from unittest.mock import patch, MagicMock

from dkybutils.flash_logger import FlashLogger, get_logger, log_info, log_warning, log_error
from dkybutils.log_channel_abc import LogChannelABC
from dkybutils.log_channel_console import LogChannelConsole
from dkybutils.color_scheme import ColorScheme
from dkybutils.log_levels import LogLevel


class MockChannel(LogChannelABC):
    """Mock log channel for testing."""

    def __init__(self):
        super().__init__()
        self.logged_messages = []

    def do_log(self, level, *args, **kwargs):
        self.logged_messages.append((level, args, kwargs))


class FlashLoggerTests(unittest.TestCase):

    def test_init_with_single_channel(self):
        """Test initialization with a single channel."""
        channel = MockChannel()
        logger = FlashLogger(channel)

        self.assertEqual(len(logger.log_channels), 1)
        self.assertIn(channel, logger.log_channels)
        self.assertEqual(logger._channel_ids[0], channel)

    def test_init_with_multiple_channels(self):
        """Test initialization with multiple channels."""
        channel1 = MockChannel()
        channel2 = MockChannel()
        logger = FlashLogger([channel1, channel2])

        self.assertEqual(len(logger.log_channels), 2)
        self.assertIn(channel1, logger.log_channels)
        self.assertIn(channel2, logger.log_channels)

    def test_init_no_channels_raises_error(self):
        """Test that initialization without channels raises ValueError."""
        with self.assertRaises(ValueError):
            FlashLogger(None)

        with self.assertRaises(ValueError):
            FlashLogger([])

    def test_add_channel(self):
        """Test adding channels."""
        logger = FlashLogger(MockChannel())
        channel2 = MockChannel()
        logger.add_channel(channel2)

        self.assertEqual(len(logger.log_channels), 2)
        self.assertIn(channel2, logger.log_channels)
        self.assertEqual(logger._channel_ids[1], channel2)
        self.assertEqual(logger._channel_id_counter, 2)

    def test_remove_channel_by_instance(self):
        """Test removing channel by instance."""
        channel1 = MockChannel()
        channel2 = MockChannel()
        logger = FlashLogger([channel1, channel2])

        logger.remove_channel(channel1)

        self.assertEqual(len(logger.log_channels), 1)
        self.assertNotIn(channel1, logger.log_channels)
        self.assertIn(channel2, logger.log_channels)
        self.assertNotIn(channel1, logger._channel_ids.values())

    def test_remove_channel_by_id(self):
        """Test removing channel by ID."""
        channel1 = MockChannel()
        channel2 = MockChannel()
        logger = FlashLogger([channel1, channel2])

        logger.remove_channel(1)  # Remove channel with ID 1

        self.assertEqual(len(logger.log_channels), 1)
        self.assertNotIn(channel2, logger.log_channels)
        self.assertIn(channel1, logger.log_channels)
        self.assertNotIn(1, logger._channel_ids)

    def test_remove_nonexistent_channel(self):
        """Test removing a channel that doesn't exist doesn't crash."""
        logger = FlashLogger(MockChannel())
        nonexistent_channel = MockChannel()

        logger.remove_channel(nonexistent_channel)
        # Should not raise exception
        self.assertEqual(len(logger.log_channels), 1)

    def test_log_method(self):
        """Test basic logging."""
        channel = MockChannel()
        logger = FlashLogger(channel)

        logger.log(LogLevel.INFO, "Test message")

        self.assertEqual(len(channel.logged_messages), 1)
        level, args, kwargs = channel.logged_messages[0]
        self.assertEqual(level, LogLevel.INFO)
        self.assertEqual(args, ("Test message",))

    def test_log_with_multiple_args(self):
        """Test logging with multiple arguments."""
        channel = MockChannel()
        logger = FlashLogger(channel)

        logger.log(LogLevel.WARNING, "Test message", "extra", kwarg="value")

        self.assertEqual(len(channel.logged_messages), 1)
        level, args, kwargs = channel.logged_messages[0]
        self.assertEqual(level, LogLevel.WARNING)
        self.assertEqual(args, ("Test message", "extra"))
        self.assertEqual(kwargs, {"kwarg": "value"})

    def test_log_level_shortcuts(self):
        """Test all log level shortcut methods."""
        channel = MockChannel()
        logger = FlashLogger(channel)

        # Test standard levels
        logger.log_info("info msg")
        logger.log_debug("debug msg")
        logger.log_warning("warning msg")
        logger.log_error("error msg")
        logger.log_fatal("fatal msg")
        logger.log_critical("critical msg")

        # Test command levels
        logger.log_command("command msg")
        logger.log_command_output("command output msg")
        logger.log_command_stderr("command stderr msg")

        # Test custom levels
        logger.log_custom0("custom0 msg")

        self.assertEqual(len(channel.logged_messages), 10)

        expected_levels = [
            LogLevel.INFO, LogLevel.DEBUG, LogLevel.WARNING, LogLevel.ERROR,
            LogLevel.FATAL, LogLevel.CRITICAL, LogLevel.COMMAND,
            LogLevel.COMMAND_OUTPUT, LogLevel.COMMAND_STDERR, LogLevel.CUSTOM0
        ]

        for i, (level, args, kwargs) in enumerate(channel.logged_messages):
            self.assertEqual(level, expected_levels[i])

    def test_log_header(self):
        """Test log_header method."""
        channel = MockChannel()
        logger = FlashLogger(channel)

        logger.log_header("Test Header")

        self.assertEqual(len(channel.logged_messages), 1)
        level, args, kwargs = channel.logged_messages[0]
        self.assertEqual(level, LogLevel.INFO)
        self.assertEqual(args, ("# Test Header #",))

    def test_log_progress_output_no_extra(self):
        """Test log_progress_output without extra comment."""
        channel = MockChannel()
        logger = FlashLogger(channel)

        logger.log_progress_output("Progress message")

        self.assertEqual(len(channel.logged_messages), 1)
        level, args, kwargs = channel.logged_messages[0]
        self.assertEqual(level, LogLevel.INFO)
        self.assertEqual(args, ("Progress message",))

    def test_log_progress_output_with_extra(self):
        """Test log_progress_output with extra comment."""
        channel = MockChannel()
        logger = FlashLogger(channel)

        logger.log_progress_output("Progress message", extra_comment="Details")

        self.assertEqual(len(channel.logged_messages), 1)
        level, args, kwargs = channel.logged_messages[0]
        self.assertEqual(level, LogLevel.INFO)
        self.assertEqual(args, ("Progress message (Details)",))

    def test_log_progress_output_custom_level(self):
        """Test log_progress_output with custom verbosity level."""
        channel = MockChannel()
        logger = FlashLogger(channel)

        logger.log_progress_output("Progress message", verbosity=LogLevel.DEBUG)

        self.assertEqual(len(channel.logged_messages), 1)
        level, args, kwargs = channel.logged_messages[0]
        self.assertEqual(level, LogLevel.DEBUG)

    def test_channel_exception_handling(self):
        """Test that exceptions in channels are handled gracefully."""

        class FailingChannel(LogChannelABC):
            def do_log(self, level, *args, **kwargs):
                raise Exception("Channel failed")

        logger = FlashLogger([FailingChannel()])

        # Should not raise exception
        try:
            logger.log(LogLevel.INFO, "Test")
        except Exception:
            self.fail("Logging should not raise exceptions from channels")

    def test_get_logger_creates_default_logger(self):
        """Test get_logger creates default console logger."""
        logger = get_logger()
        self.assertIsInstance(logger, FlashLogger)
        self.assertIsInstance(logger.log_channels[0], LogChannelConsole)

    def test_get_logger_caches_instance(self):
        """Test get_logger returns the same instance."""
        logger1 = get_logger()
        logger2 = get_logger()
        self.assertIs(logger1, logger2)

    def test_global_log_functions(self):
        """Test global log functions use the default logger."""
        with patch('dkybutils.flash_logger.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            log_info("test")
            log_warning("test")
            log_error("test")

            mock_logger.log_info.assert_called_once_with("test")
            mock_logger.log_warning.assert_called_once_with("test")
            mock_logger.log_error.assert_called_once_with("test")

    def test_get_logger_with_console_channel(self):
        """Test get_logger adds console channel when requested."""
        # Clear any existing logger
        from dkybutils.flash_logger import _global_logger
        import dkybutils.flash_logger
        dkybutils.flash_logger._global_logger = None

        try:
            # Request a console channel
            logger = get_logger(console=ColorScheme.Default.BLACK_AND_WHITE)

            # Should have a console channel (the default one gets replaced)
            console_channels = [ch for ch in logger.log_channels if isinstance(ch, LogChannelConsole)]
            self.assertEqual(len(console_channels), 1)
            # Note: We can't easily check the color scheme type, so just verify it exists

            # Calling again with same parameters should not add duplicate
            logger2 = get_logger(console=ColorScheme.Default.BLACK_AND_WHITE)
            self.assertIs(logger, logger2)
            self.assertEqual(len(logger.log_channels), 1)  # Should not have added another

        finally:
            # Reset global logger
            dkybutils.flash_logger._global_logger = None

    def test_get_logger_with_file_channel(self):
        """Test get_logger adds file channel when requested."""
        import tempfile
        from dkybutils.log_channel_file import FileLogChannel

        # Clear any existing logger
        from dkybutils.flash_logger import _global_logger
        import dkybutils.flash_logger
        dkybutils.flash_logger._global_logger = None

        with tempfile.NamedTemporaryFile() as temp_file:
            temp_path = temp_file.name

            try:
                # Request a file channel
                logger = get_logger(log_file=temp_path)

                # Should have a console channel (default) + file channel (requested)
                console_channels = [ch for ch in logger.log_channels if isinstance(ch, LogChannelConsole)]
                file_channels = [ch for ch in logger.log_channels if isinstance(ch, FileLogChannel)]
                self.assertEqual(len(console_channels), 1)
                self.assertEqual(len(file_channels), 1)
                self.assertEqual(str(file_channels[0].log_file), temp_path)

                # Calling again with same file should not add duplicate
                logger2 = get_logger(log_file=temp_path)
                self.assertIs(logger, logger2)
                self.assertEqual(len(logger.log_channels), 2)  # One console + one file

            finally:
                # Reset global logger
                dkybutils.flash_logger._global_logger = None

    def test_get_logger_no_params_creates_default(self):
        """Test get_logger with no params creates only default console channel when none exist."""
        # Clear any existing logger
        from dkybutils.flash_logger import _global_logger
        import dkybutils.flash_logger
        dkybutils.flash_logger._global_logger = None

        try:
            # Request logger with no parameters
            logger = get_logger()

            # Should have only one default console channel
            self.assertEqual(len(logger.log_channels), 1)
            self.assertIsInstance(logger.log_channels[0], LogChannelConsole)

            # Calling again should not add another channel
            logger2 = get_logger()
            self.assertIs(logger, logger2)
            self.assertEqual(len(logger.log_channels), 1)

        finally:
            # Reset global logger
            dkybutils.flash_logger._global_logger = None

    def test_get_channel_by_id(self):
        """Test getting channel by integer ID."""
        channel1 = MockChannel()
        channel2 = MockChannel()
        logger = FlashLogger([channel1, channel2])

        result = logger.get_channel(0)
        self.assertIs(result, channel1)

        result = logger.get_channel(1)
        self.assertIs(result, channel2)

        # Invalid ID
        with self.assertRaises(ValueError):
            logger.get_channel(999)

    def test_get_channel_by_name(self):
        """Test getting channel by string name."""
        console_channel = LogChannelConsole()
        mock_channel = MockChannel()
        logger = FlashLogger([console_channel, mock_channel])

        # Find console channel
        result = logger.get_channel("console")
        self.assertIs(result, console_channel)

        # Find mock channel
        result = logger.get_channel("mock")
        self.assertIs(result, mock_channel)

        # Invalid name
        with self.assertRaises(ValueError):
            logger.get_channel("nonexistent")

    def test_get_channel_by_instance(self):
        """Test getting channel by channel instance."""
        channel1 = MockChannel()
        channel2 = MockChannel()
        logger = FlashLogger([channel1, channel2])

        result = logger.get_channel(channel1)
        self.assertIs(result, channel1)

        # Non-existent channel instance
        invalid_channel = MockChannel()
        with self.assertRaises(ValueError):
            logger.get_channel(invalid_channel)

    def test_constructor_with_console_and_log_file(self):
        """Test constructor with console and log_file parameters."""
        import tempfile
        from dkybutils.log_channel_file import FileLogChannel

        with tempfile.NamedTemporaryFile() as temp_file:
            temp_path = temp_file.name

            # Test creating logger with console and file channels
            logger = FlashLogger(console=ColorScheme.Default.COLOR, log_file=temp_path)

            # Should have both channels
            self.assertEqual(len(logger.log_channels), 2)
            self.assertIsInstance(logger.log_channels[0], LogChannelConsole)
            self.assertIsInstance(logger.log_channels[1], FileLogChannel)

    def test_add_channel_with_selector(self):
        """Test adding channels with custom selectors."""
        logger = FlashLogger(MockChannel())
        channel2 = MockChannel()

        logger.add_channel(channel2, selector="custom_name")

        # Should be accessible by selector
        result = logger.get_channel("custom_name")
        self.assertIs(result, channel2)

    def test_remove_channel_by_selector(self):
        """Test removing channels by selector name."""
        logger = FlashLogger(MockChannel())  # Start with one channel

        # Add channels with selectors
        channel2 = MockChannel()
        logger.add_channel(channel2, selector="removable")

        self.assertEqual(len(logger.log_channels), 2)

        # Remove by selector
        logger.remove_channel("removable")

        self.assertEqual(len(logger.log_channels), 1)
        self.assertNotIn(channel2, logger.log_channels)

        # Selector should no longer work
        with self.assertRaises(ValueError):
            logger.get_channel("removable")

    def test_default_channel(self):
        """Test default channel."""
        logger = FlashLogger(console=ColorScheme.Default.COLOR)
        self.assertEqual(len(logger.log_channels), 1)
        logger.log_command("sudo apt install -y python")
        logger.log_command_output("successful command")
        logger.log_command_stderr("unsuccessful command")


if __name__ == '__main__':
    unittest.main()
