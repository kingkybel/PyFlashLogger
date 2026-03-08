# Repository:   https://github.com/PyFlashLogger
# File Name:    flashlogger/error.py
# Description:  error functions that log before exit.
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

from flashlogger.flash_logger import log_fatal, log_critical, log_error


def fatal(message, exception=SystemExit, error_code=1):
    log_fatal(message=message)
    raise exception(error_code)


def critical(message, exception=SystemExit, error_code=1):
    log_critical(message=message)
    raise exception(error_code)


def error(message, exception=SystemExit, error_code=1):
    log_error(message=message)
    raise exception(error_code)
