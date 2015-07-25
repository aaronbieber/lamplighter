#!/usr/bin/env python

import os
import sys
import time
import config

# Definition of log levels.
LOG_NONE  = 0
LOG_BRIEF = 1
LOG_INFO  = 2
LOG_DEBUG = 3

def log_name_by_value(log_value):
    vars = globals().copy()
    for var in vars:
        if var[:4] == "LOG_" and vars[var] == log_value:
            return var[4:]

    return False

def log(message, level = LOG_BRIEF):
    """Output a pretty log message."""
    config.load()
    user_log_level = config.config["log_level"]
    log_level_name = log_name_by_value(level)
    if globals()[user_log_level] >= level:
        pid = os.getpid()
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        print("[%s] %s %s: %s" % (pid, log_level_name, now, message))
        sys.stdout.flush()
