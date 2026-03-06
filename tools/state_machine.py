from __future__ import annotations

import json
from collections.abc import Iterable, Callable
from enum import Enum
from pathlib import Path

from flashlogger.log_levels import LogLevel


# !/usr/bin/env python3
# Repository:   https://github.com/PyFlashLogger
# File Name:    tools/state_machine.py
# Description:  Completion state machine for autocompletion based on input state
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


class State(Enum):
    INITIAL = "initial"
    LIST = "list"
    LOAD = "load"
    LOAD_COLOR = "load_color"
    LOAD_STRINGS = "load_strings"
    LOAD_CUSTOM_LEVELS = "load_custom_levels"
    RESET = "reset"
    CHANGE = "change"
    SAVE = "save"
    CHANGE_COLOR = "change_color"
    CHANGE_STRINGS = "change_strings"
    CHANGE_CUSTOM_LEVEL = "change_custom_level"
    QUIT = "quit"


class CompletionStateMachine:
    """
    A finite state machine for handling autocompletion based on the current state of input.

    The state machine maintains a current state and provides autocompletion suggestions
    based on the possible inputs allowed in the current state.
    """

    def __init__(self):
        """
        Initialize the state machine.
        """

        self._number_of_colors = None
        self._color_choices = None
        self._current_state = State.INITIAL

        self._transitions = [
            (State.INITIAL, State.LIST, ["", "list"]),
            (State.INITIAL, State.LOAD, ["load"]),
            (State.INITIAL, State.RESET, ["reset"]),
            (State.INITIAL, State.CHANGE, self.__choices_change),
            (State.INITIAL, State.SAVE, ["save"]),
            (State.INITIAL, State.QUIT, ["quit"]),
            (State.LOAD, State.LOAD_COLOR, self.__choices_load_color),
            (State.LOAD, State.LOAD_STRINGS, self.__choices_load_strings),
            (State.LOAD, State.LOAD_CUSTOM_LEVELS, ["custom_levels", "levels"]),
            (State.LIST, State.INITIAL, []),
            (State.LOAD_COLOR, State.INITIAL, self.__choices_load_color),
            (State.LOAD_STRINGS, State.INITIAL, self.__choices_load_strings),
            (State.SAVE, State.INITIAL, ["", "color", "strings", "levels"]),
        ]

        self.choices_funcs = {
            State.INITIAL: self.__choices_initial,
            State.LOAD: self.__choices_load,
            State.LOAD_COLOR: self.__choices_load_color,
            State.LOAD_STRINGS: self.__choices_load_strings,
            State.CHANGE: self.__choices_change,
            State.SAVE: lambda _: (True, ["", "color", "strings", "levels"]),
        }

    def get_color_choices(self):
        """
        Set self.color_choices from the currently configured active strings.

        Both keys and values need to be present.
        """
        # Read the active_strings.json file
        config_dir = Path(__file__).parent.parent / "flashlogger" / "config"
        active_strings_file = config_dir / "active_strings.json"

        try:
            with open(active_strings_file, "r", encoding="utf-8") as f:
                active_strings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Fallback to empty dict if file doesn't exist or is invalid
            active_strings = {}

        # Collect all string representations from the active configuration
        self._color_choices = set()

        # Add both keys and values from the JSON file
        for key, value in active_strings.items():
            if isinstance(key, str):
                self._color_choices.add(key.lower())
            if isinstance(value, str):
                self._color_choices.add(value.lower())

        # Convert to sorted list for consistency
        self._color_choices = sorted(self._color_choices)

        # Set number_of_colors (total number of entries in the JSON file)
        self._number_of_colors = len(active_strings)

    @staticmethod
    def __choices_change(choice_str=None) -> tuple[bool, list[str]]:
        all_choices = ([str(level) for level in LogLevel] +
                       list(LogLevel.custom_str_map.keys()) +
                       [v for v in LogLevel.custom_str_map.values() if isinstance(v, str)])
        # Keep expected well-known schema labels available even if custom map is empty.
        all_choices = list(dict.fromkeys(all_choices + ["timestamp"]))
        if choice_str is None:
            return True, all_choices
        has_match, matches = CompletionStateMachine.match(choice_str, all_choices)
        return has_match, matches

    @staticmethod
    def __choices_initial(choice_str=None) -> tuple[bool, list[str]]:
        all_choices = ["", "list", "load", "reset", "change", "save", "quit"]
        if choice_str is None:
            return True, all_choices
        return CompletionStateMachine.match(choice_str, all_choices)

    @staticmethod
    def __choices_load(choice_str=None) -> tuple[bool, list[str]]:
        all_choices = ["color", "strings", "custom_levels"]
        if choice_str is None:
            return True, all_choices
        return CompletionStateMachine.match(choice_str, all_choices)

    @staticmethod
    def __choices_load_color(choice_str=None) -> tuple[bool, list[str]]:
        config_dir = Path(__file__).parent.parent / "flashlogger" / "config"
        all_choices = [f.stem.replace("display_", "") for f in config_dir.glob("display_*.json")]
        if choice_str is None:
            return True, all_choices
        has_match, matches = CompletionStateMachine.match(choice_str, all_choices)
        return has_match, matches

    @staticmethod
    def __choices_load_strings(choice_str=None) -> tuple[bool, list[str]]:
        config_dir = Path(__file__).parent.parent / "flashlogger" / "config"
        all_choices = [f.stem.replace("strings_", "") for f in config_dir.glob("strings_*.json")]
        if choice_str is None:
            return True, all_choices
        has_match, matches = CompletionStateMachine.match(choice_str, all_choices)
        return has_match, matches

    @staticmethod
    def match(string_to_match: str, choices: Iterable[str], num_configurable_colors: int = None) -> tuple[
        bool, list[str]]:
        """
        Fuzzy-match strings based on custom criteria.

        Returns a tuple where:
        - First value (bool): True if there are any matches, False otherwise
        - Second value (list[str]): List of matching strings that:
            - Have all characters from string_to_match in the same order (subsequence match), ignoring case
            - Or, if string_to_match consists of digits, also include strings that start with it

        :param string_to_match: The string to match against
        :param choices: Set of strings to search in
        :param num_configurable_colors: Number of configurable colors for digit matching
        :return: Tuple of (has_matches: bool, matches: list[str])
        """
        result = set()
        lower_match = string_to_match.lower()

        # If string_to_match is digits, also check starts with
        if string_to_match.isdigit():
            if num_configurable_colors:
                for num in range(num_configurable_colors):
                    if str(num).startswith(lower_match):
                        result.add(str(num))
            else:
                result.add(lower_match)

        for choice in choices:
            lower_choice = choice.lower()

            # Check subsequence match (all characters in order)
            i = 0
            match = True
            for char in lower_match:
                found = False
                while i < len(lower_choice):
                    if lower_choice[i] == char:
                        found = True
                        i += 1
                        break
                    i += 1
                if not found:
                    match = False
                    break
            if match:
                result.add(choice)

        matches_list = sorted(result)
        return bool(result), matches_list

    def process_input(self, input_str: str) -> bool:
        """
        Process an input string, transitioning to the next state if valid.

        :param input_str: The input to process.
        :return: True if the input was valid and state transitioned, False otherwise.
        """
        normalized_input = (input_str or "").strip()
        for from_state, to_state, choices in self._transitions:
            if from_state == self._current_state:
                if isinstance(choices, Callable):
                    if choices(normalized_input)[0]:
                        self._current_state = to_state
                        return True
                elif not choices:
                    self._current_state = to_state
                    return True
                else:
                    if normalized_input in choices:
                        self._current_state = to_state
                        return True
        return False

    def get_completions(self, partial=""):
        """
        Get autocompletion suggestions for the current state, filtered by partial input.

        :param partial: Partial input to filter completions.
        :return: List of possible completions starting with the partial input.
        """
        func = self.choices_funcs.get(self._current_state)
        if func is None:
            possible = []
        else:
            _, possible = func(None)
        return [comp for comp in possible if comp.startswith(partial)]

    def get_current_state(self):
        """
        Get the current state.

        :return: The current state.
        """
        return self._current_state

    def reset(self, state=None):
        """
        Reset the state machine to the initial state or a specified state.

        :param state: State to reset to. If None, resets to initial state.
        """
        if state is None:
            self._current_state = State.INITIAL
        elif state in State:
            self._current_state = state
        else:
            raise ValueError(f"Invalid state: {state}")
