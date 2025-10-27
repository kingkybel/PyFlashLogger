# Repository:   https://github.com/Python-utilities
# File Name:    dkybutils/exceptions.py
# Description:  exception classes derived from Exception to handle exception in this library
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


class BaseScriptError(Exception):
    def __init__(self, message: str = None):
        if message is None:
            message = ""
        self.message = message
        super().__init__(message)


class StringUtilError(BaseScriptError):
    def __init__(self, message: str = None):
        if message is None:
            message = ""
        self.message = message
        super().__init__(message)


class ExtendedEnumError(BaseScriptError):
    def __init__(self, message: str = None):
        if message is None:
            message = ""
        self.message = message
        super().__init__(message)


class CsvError(BaseScriptError):
    def __init__(self, message: str = None):
        if message is None:
            message = ""
        self.message = message
        super().__init__(message)


class JsonError(BaseScriptError):
    pass


class JsonGeneralError(JsonError):
    def __init__(self, message: str = None):
        if message is None:
            message = ""
        self.message = message
        super().__init__(message)


class JsonMalformedKey(JsonError):
    pass


class JsonMalformedIndex(JsonMalformedKey):
    def __init__(self, index: (str | int)):
        self.message = f"Index '{index}' (type={type(index)}) is not a valid index. " \
                       "Only 0, positive ints or '^'/'$' are allowed"
        super().__init__(self.message)


class JsonMalformedStringKey(JsonMalformedKey):
    def __init__(self, key: str):
        self.message = f"Json-key '{key}' (type={type(key)}) is not a valid index. " \
                       "Must not have whitespace at front or back, or contain '[', ']', '/' or '\"'"
        super().__init__(self.message)


class JsonPathFormatError(JsonError, ValueError):
    def __init__(self, path_string: str = None, extra_info: str = None):
        if path_string is None:
            path_string = ""
        if extra_info is None:
            extra_info = ""
        else:
            extra_info = f". ({extra_info})"
        self.message = f"Json path-string '{path_string}' does not conform to " \
                       f"(\\[ <int> | '^' | '$' \\] | <string-id>)+{extra_info}"
        super().__init__(self.message)


class JsonKeyStringRequired(JsonError, KeyError):
    def __init__(self, key_index: int, keys: list[str], json_obj=None):
        if json_obj is not None:
            self.message = f"Object at depth {key_index} has type '{type(json_obj)}', but " \
                           f"key '{keys[key_index]}' requires '{list}'"
        elif json_obj is not None:
            self.message = f"Index '{keys[key_index]}' at index {key_index} is out of bounds [0..{len(json_obj) - 1}"
        else:
            self.message = f"Index '{keys[key_index]}' at index {key_index} cannot be found in empty json-object'"
        super().__init__(self.message)


class JsonIndexRequired(JsonError, KeyError):
    def __init__(self, key_index: int, keys: list[str], json_obj=None):
        if json_obj is not None:
            self.message = f"Object at depth {key_index} has type '{type(json_obj)}', but " \
                           f"key '{keys[key_index]}' requires '{dict}'"
        elif json_obj is not None:
            self.message = f"Key '{keys[key_index]}' at key-number {key_index} cannot be found in '{json_obj}'"
        else:
            self.message = f"Key '{keys[key_index]}' at key-number {key_index} found empty json-object'"
        super().__init__(self.message)


class JsonValueMismatch(JsonError, ValueError):
    def __init__(self,
                 orig_value: (bool | int | float | str | list | dict),
                 new_value: (bool | int | float | str | list | dict)):
        self.message = f"Cannot overwrite value of different type if not forced. " \
                       f"Original value '{orig_value}' type({type(orig_value)}), New value '{new_value}' " \
                       f"type({type(new_value)})"
        super().__init__(self.message)
