#!/bin/env python3
from flashlogger import get_logger, log_error, log_warning, LogLevel, LogChannelConsole, log_debug, ColorScheme, \
    log_info, log_custom0, OutputFormat

if __name__ == '__main__':
    logger = get_logger()

    console_log_channel = logger.get_channel(LogChannelConsole.__name__)
    log_error("This is an error")
    log_warning({"x": "This is an error"})
    console_log_channel.log_levels = LogLevel.ERROR  # minimum error
    log_warning({"x": "This is an warning"})

    # enumerate
    console_log_channel.log_levels = [LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR]
    log_debug({"x": "This is an debug"})

    # exclude
    console_log_channel.log_levels = {
        "exclude": [LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR]}
    log_debug({"x": "This is an debug2"})
    log_custom0({"x": "This is an custom0"})

    console_log_channel.set_color_scheme(ColorScheme.Default.BLACK_AND_WHITE)
    log_custom0({"x": "This is an custom0"})

    console_log_channel.set_color_scheme(ColorScheme.Default.PLAIN_TEXT)
    log_custom0({"x": "This is an custom0"})

    logger.set_output_format(OutputFormat.JSON_PRETTY)
    log_custom0({"x": {"y":"This is an custom0"}}, [1,2,3])
