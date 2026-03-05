#!/usr/bin/env python3
# Repository:   https://github.com/PyFlashLogger
# File Name:    test/test_state_machine.py
# Description:  Unit tests for CompletionStateMachine functionality
#
# Copyright (C) 2025 Dieter J Kybelksties <github@kybelksties.com>
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
# @date: 2025-12-14
# @author: Dieter J Kybelksties

import unittest

from tools.state_machine import CompletionStateMachine, State


class CompletionStateMachineTests(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.sm = CompletionStateMachine()

    def test_initialization(self):
        """Test that the state machine initializes correctly."""
        self.assertEqual(State.INITIAL, self.sm.get_current_state())
        self.assertIsInstance(self.sm._transitions, list)
        self.assertIsInstance(self.sm.choices_funcs, dict)

    def test_process_input_valid_commands(self):
        """Test processing valid input commands."""
        # Test list command
        result = self.sm.process_input("list")
        self.assertTrue(result)
        self.assertEqual(State.LIST, self.sm.get_current_state())

        # Reset to initial
        self.sm.reset()

        # Test load command
        result = self.sm.process_input("load")
        self.assertTrue(result)
        self.assertEqual(State.LOAD, self.sm.get_current_state())

        # Reset to initial
        self.sm.reset()

        # Test change command with digit
        result = self.sm.process_input("5")
        self.assertTrue(result)
        self.assertEqual(State.CHANGE, self.sm.get_current_state())

    def test_process_input_invalid_commands(self):
        """Test processing invalid input commands."""
        result = self.sm.process_input("invalid")
        self.assertFalse(result)
        self.assertEqual(State.INITIAL, self.sm.get_current_state())

    def test_process_input_from_load_state(self):
        """Test processing input from load state."""
        # Go to load state
        self.sm.process_input("load")
        self.assertEqual(self.sm.get_current_state().value, "load")

        # Test loading color
        result = self.sm.process_input("dark_bg_color")  # Assuming this exists
        self.assertTrue(result)
        self.assertEqual(self.sm.get_current_state().value, "load_color")

    def test_get_completions_initial_state(self):
        """Test getting completions in initial state."""
        completions = self.sm.get_completions()
        expected = ["", "list", "load", "reset", "change", "save", "quit"]
        self.assertEqual(set(completions), set(expected))

    def test_get_completions_with_partial(self):
        """Test getting completions with partial input."""
        completions = self.sm.get_completions("l")
        self.assertIn("list", completions)
        self.assertIn("load", completions)
        self.assertNotIn("reset", completions)

    def test_get_completions_load_state(self):
        """Test getting completions in load state."""
        self.sm.process_input("load")
        completions = self.sm.get_completions()
        expected = ["color", "strings", "custom_levels"]
        self.assertEqual(set(completions), set(expected))

    def test_reset_to_initial(self):
        """Test resetting to initial state."""
        self.sm.process_input("load")
        self.assertEqual(self.sm.get_current_state().value, "load")
        self.sm.reset()
        self.assertEqual(self.sm.get_current_state().value, "initial")

    def test_reset_to_specific_state(self):
        """Test resetting to a specific state."""
        self.sm.reset(State.LOAD)
        self.assertEqual(self.sm.get_current_state().value, "load")

    def test_reset_invalid_state(self):
        """Test resetting to invalid state raises error."""
        with self.assertRaises(ValueError):
            self.sm.reset("invalid_state")

    def test_choices_change_with_digit(self):
        """Test __choices_change with digit."""
        has_match, _ = CompletionStateMachine._CompletionStateMachine__choices_change("123")
        self.assertTrue(has_match)

    def test_choices_change_with_loglevel_fuzzy(self):
        """Test __choices_change with fuzzy loglevel match."""
        has_match, matches = CompletionStateMachine._CompletionStateMachine__choices_change("deb")  # debug
        self.assertTrue(has_match)
        self.assertIn("debug", matches)

    def test_choices_change_with_string_schema_fuzzy(self):
        """Test __choices_change with fuzzy string schema match."""
        # Assuming there are string keys in custom_str_map
        has_match, _ = CompletionStateMachine._CompletionStateMachine__choices_change("timestamp")
        self.assertTrue(has_match)

    def test_choices_change_invalid(self):
        """Test __choices_change with invalid input."""
        has_match, matches = CompletionStateMachine._CompletionStateMachine__choices_change("xyz")
        self.assertFalse(has_match)
        self.assertEqual(matches, [])

    def test_choices_load_color_fuzzy_match(self):
        """Test __choices_load_color with fuzzy match."""
        # Assuming "dark_bg_color" exists
        has_match, matches = CompletionStateMachine._CompletionStateMachine__choices_load_color("dark")
        self.assertTrue(has_match)
        self.assertIn("dark_bg_color", matches)

    def test_choices_load_color_no_match(self):
        """Test __choices_load_color with no match."""
        has_match, matches = CompletionStateMachine._CompletionStateMachine__choices_load_color("nonexistent")
        self.assertFalse(has_match)
        self.assertEqual(matches, [])

    def test_choices_load_strings_fuzzy_match(self):
        """Test __choices_load_strings with fuzzy match."""
        # Assuming "en" exists
        has_match, matches = CompletionStateMachine._CompletionStateMachine__choices_load_strings("en")
        self.assertTrue(has_match)
        self.assertIn("en", matches)

    def test_choices_initial(self):
        """Test __choices_initial returns expected tuple."""
        has_match, choices = CompletionStateMachine._CompletionStateMachine__choices_initial()
        self.assertTrue(has_match)
        expected = ["", "list", "load", "reset", "change", "save", "quit"]
        self.assertEqual(choices, expected)

    def test_choices_load(self):
        """Test __choices_load returns expected tuple."""
        has_match, choices = CompletionStateMachine._CompletionStateMachine__choices_load()
        self.assertTrue(has_match)
        expected = ["color", "strings", "custom_levels"]
        self.assertEqual(choices, expected)

    def test_choices_load_color(self):
        """Test __choices_load_color returns color schemes."""
        has_match, choices = CompletionStateMachine._CompletionStateMachine__choices_load_color()
        self.assertTrue(has_match)
        self.assertIsInstance(choices, list)
        self.assertGreater(len(choices), 0)
        # Should be scheme names like "dark_bg_color"
        self.assertIn("dark_bg_color", choices)

    def test_choices_load_strings(self):
        """Test __choices_load_strings returns string schemes."""
        has_match, choices = CompletionStateMachine._CompletionStateMachine__choices_load_strings()
        self.assertTrue(has_match)
        self.assertIsInstance(choices, list)
        self.assertGreater(len(choices), 0)
        # Should be language codes like "en", "de"
        self.assertIn("en", choices)

    def test_choices_change(self):
        """Test __choices_change returns loglevels and schemas."""
        has_match, choices = CompletionStateMachine._CompletionStateMachine__choices_change()
        self.assertTrue(has_match)
        self.assertIsInstance(choices, list)
        self.assertGreater(len(choices), 0)
        # Should contain loglevel names
        self.assertIn("debug", choices)
        self.assertIn("info", choices)

    def test_fuzzy_matching_ratio(self):
        """Test that fuzzy matching uses appropriate similarity ratio."""
        from difflib import SequenceMatcher

        # Test high similarity
        ratio = SequenceMatcher(None, "debug", "deb").ratio()
        self.assertGreater(ratio, 0.8)

        # Test low similarity
        ratio = SequenceMatcher(None, "debug", "xyz").ratio()
        self.assertLess(ratio, 0.8)

    def test_match_subsequence(self):
        """Test match function with subsequence matching."""
        choices = {"debug", "info", "warning", "error"}
        has_match, matches = CompletionStateMachine.match("db", choices)
        self.assertTrue(has_match)
        self.assertIn("debug", matches)

        has_match, matches = CompletionStateMachine.match("inf", choices)
        self.assertTrue(has_match)
        self.assertIn("info", matches)

    def test_match_ignore_case(self):
        """Test match function ignores case."""
        choices = {"Debug", "INFO", "Warning"}
        has_match, matches = CompletionStateMachine.match("debug", choices)
        self.assertTrue(has_match)
        self.assertIn("Debug", matches)

        has_match, matches = CompletionStateMachine.match("INFO", choices)
        self.assertTrue(has_match)
        self.assertIn("INFO", matches)

    def test_match_starts_with_digit(self):
        """Test match function with digit starting match."""
        choices = {"123abc", "456def", "789ghi"}
        has_match, matches = CompletionStateMachine.match("123", choices)
        self.assertTrue(has_match)
        self.assertIn("123abc", matches)
        self.assertNotIn("456def", matches)

    def test_match_no_match(self):
        """Test match function with no matches."""
        choices = {"debug", "info"}
        has_match, matches = CompletionStateMachine.match("xyz", choices)
        self.assertFalse(has_match)
        self.assertEqual(len(matches), 0)

    def test_match_empty_string(self):
        """Test match function with empty string."""
        choices = {"debug", "info"}
        has_match, matches = CompletionStateMachine.match("", choices)
        self.assertTrue(has_match)
        self.assertEqual(len(matches), 2)  # All should match empty subsequence


if __name__ == '__main__':
    unittest.main()
