# Repository:   https://github.com/Python-utilities
# File Name:    dkybutils/log_channel_abc.py
# Description:  Log-channel abstract base class
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
# @date: 2025-10-21
# @author: Dieter J Kybelksties

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable

from dkybutils.log_levels import LogLevel


class LogChannelABC(ABC):
    """Abstract base class for log channels.

    Provides a singleton logger instance that can be shared across log channels
    that need centralized logging infrastructure.
    """
    _shared_logger: logging.Logger | None = None

    @classmethod
    def get_shared_logger(cls) -> logging.Logger:
        """
        Get the shared logger instance (singleton pattern).
        :return: the shared logger instance
        """
        if cls._shared_logger is None:
            cls._shared_logger = logging.getLogger("dkybutils.log_channels")
            cls._shared_logger.setLevel(logging.DEBUG)

        return cls._shared_logger

    @classmethod
    def configure_shared_logger(cls, level: int = logging.DEBUG,
                                format_str: str | None = None) -> None:
        """
        Configure the shared logger.
        :param level: logging level
        :param format_str: format string for log messages
        """
        logger = cls.get_shared_logger()
        logger.setLevel(level)

        if format_str:
            # Remove any existing handlers and add a new one with formatting
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)

            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(format_str))
            logger.addHandler(handler)
            logger.propagate = False  # Prevent duplicate output

    def __init__(self, minimum_log_level=None, include_log_levels=None, exclude_log_levels=None):
        """
        Initialize the log channel.
        :param minimum_log_level: minimum log level threshold
        :param include_log_levels: specific levels to include
        :param exclude_log_levels: specific levels to exclude
        """
        self.__loggable_levels = set()  # Set of all loggable LogLevel objects
        self._configure_levels(minimum_log_level, include_log_levels, exclude_log_levels)

    @property
    def minimal_log_level(self):
        """
        Get the current log level filter.
        :return: set of loggable levels
        """
        return self.__loggable_levels

    @minimal_log_level.setter
    def minimal_log_level(self, log_level) -> None:
        """
        Set the log level filter. Supports three modes:

        1. Single log level (threshold mode): only log levels >= this level
           Example: LogLevel.WARNING or "WARNING"

        2. Iterable of log levels (inclusion mode): only log the specified levels
           Example: [LogLevel.INFO, LogLevel.ERROR, "FATAL"]

        3. Dict with "exclude" key (exclusion mode): log all levels except specified ones
           Example: {"exclude": [LogLevel.DEBUG, LogLevel.INFO]}

        Internally stores all loggable levels in a set for O(1) lookup.
        """
        # Check for exclusion mode (dict with "exclude" key)
        if isinstance(log_level, dict) and "exclude" in log_level:
            excluded_levels = set()
            for level in log_level["exclude"]:
                if isinstance(level, str):
                    excluded_levels.add(LogLevel[level.upper()])
                elif isinstance(level, int):
                    excluded_levels.add(LogLevel.custom_level(level))
                else:
                    excluded_levels.add(level)

            # Add all LogLevel members except the excluded ones
            self.__loggable_levels = set(LogLevel) - excluded_levels
            return

        # Check for inclusion mode (iterable but not string or dict)
        if not isinstance(log_level, dict) and hasattr(log_level, "__iter__") and not isinstance(log_level, str):
            try:
                loggable_levels = set()
                for level in log_level:
                    if isinstance(level, str):
                        loggable_levels.add(LogLevel[level.upper()])
                    elif isinstance(level, int):
                        loggable_levels.add(LogLevel.custom_level(level))
                    else:
                        loggable_levels.add(level)
                self.__loggable_levels = loggable_levels
                return
            except (TypeError, ValueError):
                pass  # Fall through to threshold mode

        # Default to threshold mode (single level)
        if isinstance(log_level, str):
            threshold_level = LogLevel[log_level.upper()]
        elif isinstance(log_level, int):
            threshold_level = LogLevel.custom_level(log_level)
        elif isinstance(log_level, LogLevel):
            threshold_level = log_level
        else:
            # Fallback
            threshold_level = LogLevel.NOTSET

        # Build set of all levels >= threshold
        self.__loggable_levels = {level for level in LogLevel
                                  if level.logging_level() >= threshold_level.logging_level()}

    def _configure_levels(self, minimum_log_level, include_log_levels, exclude_log_levels):
        """Configure the loggable levels based on the provided parameters."""
        # Priority: exclude > include > minimum
        if exclude_log_levels is not None:
            # Exclusion mode
            if isinstance(exclude_log_levels, str):
                excluded_levels = {LogLevel[exclude_log_levels.upper()]}
            elif isinstance(exclude_log_levels, int):
                excluded_levels = {LogLevel.custom_level(exclude_log_levels)}
            elif isinstance(exclude_log_levels, LogLevel):
                excluded_levels = {exclude_log_levels}
            elif isinstance(exclude_log_levels, Iterable) and not isinstance(exclude_log_levels, str):
                excluded_levels = set()
                for level in exclude_log_levels:
                    if isinstance(level, str):
                        excluded_levels.add(LogLevel[level.upper()])
                    elif isinstance(level, int):
                        excluded_levels.add(LogLevel.custom_level(level))
                    else:
                        excluded_levels.add(level)
            else:
                excluded_levels = set()
            self.__loggable_levels = set(LogLevel) - excluded_levels

        elif include_log_levels is not None:
            # Inclusion mode
            if isinstance(include_log_levels, str):
                self.__loggable_levels = {LogLevel[include_log_levels.upper()]}
            elif isinstance(include_log_levels, int):
                self.__loggable_levels = {LogLevel.custom_level(include_log_levels)}
            elif isinstance(include_log_levels, LogLevel):
                self.__loggable_levels = {include_log_levels}
            elif isinstance(include_log_levels, Iterable) and not isinstance(include_log_levels, str):
                self.__loggable_levels = set()
                for level in include_log_levels:
                    if isinstance(level, str):
                        self.__loggable_levels.add(LogLevel[level.upper()])
                    elif isinstance(level, int):
                        self.__loggable_levels.add(LogLevel.custom_level(level))
                    else:
                        self.__loggable_levels.add(level)
            else:
                self.__loggable_levels = set()

        elif minimum_log_level is not None:
            # Check for exclusion mode (dict with "exclude" key)
            if isinstance(minimum_log_level, dict) and "exclude" in minimum_log_level:
                excluded_levels = set()
                for level in minimum_log_level["exclude"]:
                    if isinstance(level, str):
                        excluded_levels.add(LogLevel[level.upper()])
                    elif isinstance(level, int):
                        excluded_levels.add(LogLevel.custom_level(level))
                    else:
                        excluded_levels.add(level)
                self.__loggable_levels = set(LogLevel) - excluded_levels
            else:
                # Minimum level mode (threshold)
                if isinstance(minimum_log_level, str):
                    threshold_level = LogLevel[minimum_log_level.upper()]
                elif isinstance(minimum_log_level, int):
                    threshold_level = LogLevel.custom_level(minimum_log_level)
                elif isinstance(minimum_log_level, LogLevel):
                    threshold_level = minimum_log_level
                else:
                    threshold_level = LogLevel.NOTSET

                self.__loggable_levels = {level for level in LogLevel
                                          if level.logging_level() >= threshold_level.logging_level()}
        else:
            # Default: log everything
            self.__loggable_levels = set(LogLevel)

    def is_loggable(self, log_level: LogLevel | str | int) -> bool:
        """
        Check if the given log level is loggable.
        :param log_level: the log level to check
        :return: True if loggable, False otherwise
        """
        # Convert to LogLevel object
        if isinstance(log_level, str):
            log_level = LogLevel[log_level.upper()]
        elif isinstance(log_level, int):
            log_level = LogLevel.custom_level(log_level)

        # Just check membership in the loggable levels set
        return log_level in self.__loggable_levels

    @abstractmethod
    def do_log(self, log_level: LogLevel | str | int, *args, **kwargs):
        """
        Log a message.
        :param log_level: the log level
        :param args: message arguments
        :param kwargs: additional keyword arguments
        """
        pass
