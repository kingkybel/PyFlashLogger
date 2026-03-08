# Repository:   https://github.com/PyFlashLogger
# File Name:    test/test_error.py
# Description:  Unit tests for the error module.
#
# Copyright (C) 2026 Dieter J Kybelksties <github@kybelksties.com>
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
# @date: 2026-03-08
# @author: Dieter J Kybelksties

import unittest
from unittest.mock import patch
from flashlogger.error import fatal, critical, error


class TestError(unittest.TestCase):

    @patch('flashlogger.error.log_fatal')
    def test_fatal_logs_and_exits(self, mock_log):
        """Test that fatal() logs a message and raises SystemExit."""
        with self.assertRaises(SystemExit) as cm:
            fatal("Fatal error occurred")
        mock_log.assert_called_once_with(message="Fatal error occurred")
        self.assertEqual(cm.exception.code, 1)

    @patch('flashlogger.error.log_critical')
    def test_critical_logs_and_exits(self, mock_log):
        """Test that critical() logs a message and raises SystemExit."""
        with self.assertRaises(SystemExit) as cm:
            critical("Critical error occurred")
        mock_log.assert_called_once_with(message="Critical error occurred")
        self.assertEqual(cm.exception.code, 1)

    @patch('flashlogger.error.log_error')
    def test_error_logs_and_exits(self, mock_log):
        """Test that error() logs a message and raises SystemExit."""
        with self.assertRaises(SystemExit) as cm:
            error("Error occurred")
        mock_log.assert_called_once_with(message="Error occurred")
        self.assertEqual(cm.exception.code, 1)

    @patch('flashlogger.error.log_fatal')
    def test_fatal_with_custom_exception(self, mock_log):
        """Test fatal() with a custom exception."""
        class CustomException(Exception):
            pass

        with self.assertRaises(CustomException):
            fatal("Custom exception test", exception=CustomException)
        mock_log.assert_called_once_with(message="Custom exception test")

    @patch('flashlogger.error.log_critical')
    def test_critical_with_custom_error_code(self, mock_log):
        """Test critical() with a custom error code."""
        with self.assertRaises(SystemExit) as cm:
            critical("Custom error code test", error_code=127)
        mock_log.assert_called_once_with(message="Custom error code test")
        self.assertEqual(cm.exception.code, 127)


if __name__ == '__main__':
    unittest.main()
