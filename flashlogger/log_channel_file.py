# Repository:   https://github.com/Python-utilities
# File Name:    flashlogger/log_channel_file.py
# Description:  Log-channel definitions for logging to file
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

import datetime
import json
import logging
from logging import LogRecord
from pathlib import Path

from fundamentals import overrides

from flashlogger.log_channel_abc import LogChannelABC, OutputFormat
from flashlogger.log_levels import LogLevel

DEFAULT_FORMAT = '[%(asctime)s]\t[%(levelname)s] [%(threadname)s] %(message)s'


class FileLogFormatter(logging.Formatter):
    """
    A formatter class to customize how file-log-entries should be written.
    """

    def __init__(self, fmt=DEFAULT_FORMAT, output_format=None):
        logging.Formatter.__init__(self, fmt=fmt)
        self.output_format = output_format if output_format is not None else OutputFormat.HUMAN_READABLE

    @overrides(logging.Formatter)
    def format(self, record: LogRecord) -> str:
        """
        Overriding the format function in order to handle custom log-levels appropriately.
        :param record: the logging record.
        :return: the formatted record as string.
        """
        message = record.getMessage()
        timestamp = self.formatTime(record)
        log_level = LogLevel.custom_level(record.levelno)
        level_name = str(log_level).lower()
        if record.levelno in {LogLevel.ERROR.logging_level(),
                              LogLevel.WARNING.logging_level(),
                              LogLevel.FATAL.logging_level(),
                              LogLevel.CRITICAL.logging_level()}:
            level_name = level_name.upper()
        process_id = record.process
        thread_id = record.thread

        data = {
            "timestamp": timestamp,
            "level": level_name,
            "message": message,
            "pid": process_id,
            "tid": thread_id
        }

        if self.output_format != OutputFormat.HUMAN_READABLE:
            indent = 4 if self.output_format == OutputFormat.JSON_PRETTY else None
            if log_level == LogLevel.COMMAND:
                data["type"] = "command"
            elif log_level == LogLevel.COMMAND_OUTPUT:
                data["type"] = "stdout"
            elif log_level == LogLevel.COMMAND_STDERR:
                data["type"] = "stderr"
            return json.dumps(data, indent=indent, default=str)

        # Human-readable
        if log_level == LogLevel.COMMAND:
            result = f"[{timestamp}] [{str(log_level)}] [PID:{process_id}|TID:{thread_id}] {message} ## command to execute"
        elif log_level == LogLevel.COMMAND_OUTPUT:
            result = f"[{timestamp}] [{str(log_level)}] [PID:{process_id}|TID:{thread_id}] (stdout): {message}"
        elif log_level == LogLevel.COMMAND_STDERR:
            result = f"[{timestamp}] [{str(log_level)}] [PID:{process_id}|TID:{thread_id}] (stderr): {message}"
        else:
            # Regular messages: [timestamp] [level] [PID|TID] message
            if record.levelno in {LogLevel.ERROR.logging_level(),
                                  LogLevel.WARNING.logging_level(),
                                  LogLevel.FATAL.logging_level(),
                                  LogLevel.CRITICAL.logging_level()}:
                level_name = level_name.upper()
            result = f"[{timestamp}] [{level_name}] [PID:{process_id}|TID:{thread_id}] {message}"

        return result

    @overrides(logging.Formatter)
    def formatTime(self, record, datefmt=None) -> str:
        """
        Higher precision timestamps.
        :param: record: the log-record to format.
        :param: date_fmt:  the format string for dates and timestamps.
        :return: the formatted timestamp as string.
        """
        ct = datetime.datetime.fromtimestamp(record.created)
        if datefmt is not None:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime("%Y-%m-%d %H:%M:%S")
            s = f"{t}.{int(record.msecs):05d}"
        return s


class FileLogChannel(LogChannelABC):
    """
    A logging channel which writes log messages to file-log-entries.
    """

    def __init__(self,
                 log_filename: str | Path,
                 logfile_open_mode: str = "w",
                 minimum_log_level=None,
                 include_log_levels=None,
                 exclude_log_levels=None,
                 output_format: OutputFormat | str = None):
        super().__init__(minimum_log_level=minimum_log_level,
                         include_log_levels=include_log_levels,
                         exclude_log_levels=exclude_log_levels)
        if output_format is not None:
            if isinstance(output_format, str):
                output_format = OutputFormat[output_format.upper()]
            self.output_format = output_format
        self.log_file = Path(log_filename)

        log_dir = self.log_file.parent
        if not log_dir.is_dir():
            log_dir.mkdir(parents=True, exist_ok=True)

        # Touch the file to create it, then close it immediately
        self.log_file.touch(exist_ok=True)
        self.do_file_log = True

        filehandler = logging.FileHandler(log_filename, mode=logfile_open_mode)
        filehandler.setFormatter(FileLogFormatter(output_format=self.output_format))
        logging.basicConfig(format='[%(asctime)s]\t[%(levelname)s] [%(threadname)s] %(message)s',
                            datefmt="%Y%m%d-%H:%M:%S",
                            level=logging.DEBUG,  # Use DEBUG level and let our filtering handle the rest
                            handlers=[filehandler])

    @overrides(LogChannelABC)
    def do_log(self, log_level: LogLevel | str | int, *args, **kwargs) -> None:
        """
        Log a message to file.
        :param log_level: the logging level
        :param kwargs: any other arguments, ignored
        """
        if not self.is_loggable(log_level):
            return
        if isinstance(log_level, str):
            log_level = LogLevel[log_level.upper()]
        elif isinstance(log_level, int):
            log_level = LogLevel.custom_level(log_level)
        # now log_level is LogLevel

        # Use the logging system with the configured FileHandler that has our FileLogFormatter
        # This ensures all log levels go through the formatter with location information
        message = args[0] if args else ""
        logging.log(log_level.logging_level(), message, *args[1:], **kwargs)
