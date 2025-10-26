# Repository:   https://github.com/Python-utilities
# File Name:    dkybutils/extended_enum.py
# Description:  enumeration classes that handle "fuzzy" parameter-matching
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
# @date: 2024-07-13
# @author: Dieter J Kybelksties

from __future__ import annotations

import re
from collections.abc import Callable
from enum import Flag, Enum, auto

from dkybutils.exceptions import ExtendedEnumError


class EnumListType(Flag):
    ITEM = auto()
    VALUE = auto()
    NAME = auto()
    STR = auto()


# pylint: disable=unused-argument
def always_match(any_obj: object = None):
    """
    Predicate that always matches for any object of any type.
    :param any_obj: placeholder object
    :return: always true.
    """
    return True


def match_one_alternative(
        partial: str,
        alternatives: str | list[str],
        delimiter: str = "|",
        predicate: Callable[[object], bool] = lambda x: True,
        flags: re.RegexFlag = re.IGNORECASE,
        consecutive_only: bool = False,
) -> tuple[str | None, int, list[str]]:
    """
    Matches a string to a unique alternative.

    :param partial: A partial string to match against alternatives.
    :param alternatives: A string (split by `delimiter`) or a list of strings to match against.
    :param delimiter: Delimiter to split the alternatives string if it's not a list.
    :param predicate: A function to filter alternatives.
    :param flags: Regular expression flags.
    :param consecutive_only: If True, characters in `partial` must be consecutive; otherwise, order suffices.
    :return: A tuple:
        - Matched alternative (or None if no unique match exists).
        - Return code: 0 (success), -1 (failure).
        - List of all matching alternatives.
    """
    if not partial:
        raise ValueError("Partial string cannot be empty.")

    # Convert `alternatives` to a list if it's a string.
    if isinstance(alternatives, str):
        alternatives = alternatives.split(delimiter)

    # Check for empty alternatives.
    empty_alts = [alt for alt in alternatives if not alt]
    if empty_alts:
        raise ValueError(f"Alternatives contain empty strings: {empty_alts}")

    # Construct the search pattern.
    partial_pattern = ".*".join(re.escape(char) for char in partial) if not consecutive_only else re.escape(partial)
    regex = re.compile(f".*{partial_pattern}.*", flags)

    # Filter and match alternatives.
    matches = [alt for alt in alternatives if regex.search(alt) and predicate(alt)]

    # Determine result based on the number of matches.
    if len(matches) == 1:
        return matches[0], 0, matches
    return None, -1, matches


def _list(cls: Flag | Enum, list_type: EnumListType = EnumListType.ITEM):
    reval_list = []
    for item in cls:
        match list_type:
            case EnumListType.ITEM:
                reval_list.append(item)
            case EnumListType.VALUE:
                reval_list.append(item.value)
            case EnumListType.NAME:
                reval_list.append(item.name)
            case EnumListType.STR:
                reval_list.append(str(item))
    return reval_list


def _from_string(cls: Flag | Enum, partial: str, predicate=always_match):
    alternatives_list = []
    items = _list(cls, EnumListType.ITEM)
    if isinstance(items[0].value, str):
        alternatives_list.append((EnumListType.VALUE, _list(cls, EnumListType.VALUE)))
    alternatives_list.append((EnumListType.NAME, _list(cls, EnumListType.NAME)))
    alternatives_list.append((EnumListType.STR, _list(cls, EnumListType.STR)))
    tried_alternatives = []
    for tp, alternatives in alternatives_list:
        matched, reval, duplicates = match_one_alternative(partial=partial,
                                                           alternatives=alternatives,
                                                           predicate=predicate)
        if reval == 0:
            for item in items:
                if tp == EnumListType.VALUE and item.value == matched:
                    return item
                if tp == EnumListType.NAME and item.name == matched:
                    return item
                if tp == EnumListType.STR and str(item) == matched:
                    return item
        tried_alternatives.append((alternatives, duplicates))

    error_message = f"Cannot match partial '{partial}' to unique enum-value\n"
    for i, tried_alternative in enumerate(tried_alternatives):
        dupe = "-no match-"
        if len(tried_alternative[1]) > 1:
            dupe = f"multiple matches {tried_alternative[1]}"

        error_message += f"{tried_alternatives[i][0]}:\t{dupe}\n"
    raise ExtendedEnumError(error_message)


class ExtendedEnum(Enum):
    """
    Derived from Enum and extended to allow value creation from partial strings and listing of:
    — items
    — values
    — names
    — string-conversions.
    """

    @classmethod
    def list(cls, list_type=EnumListType.ITEM):
        return _list(cls=cls, list_type=list_type)

    @classmethod
    def from_string(cls, partial: str, predicate=always_match):
        return _from_string(cls=cls, partial=partial, predicate=predicate)

    def __or__(self, other):
        if isinstance(other, self.__class__):
            return self.__class__(self.value | other.value)
        return NotImplemented

    def __ror__(self, other):
        return self.__or__(other)


class ExtendedFlag(Flag):
    """
    Derived from Flag and extended to allow value creation from partial strings and listing of:
    — items
    — values
    — names
    — string-conversions.
    """

    @classmethod
    def list(cls, list_type=EnumListType.ITEM):
        return _list(cls=cls, list_type=list_type)

    @classmethod
    def from_string(cls, partial: str, predicate=always_match):
        return _from_string(cls=cls, partial=partial, predicate=predicate)

    def __or__(self, other):
        if isinstance(other, self.__class__):
            return self.__class__(self.value | other.value)
        return NotImplemented

    def __ror__(self, other):
        return self.__or__(other)
