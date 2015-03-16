#!/usr/bin/env python3

"""Statistics aggregating module.

This module is a part of Lamplighter. See lamplighter.py for more."""

import datetime

scans              = 0
confirmation_scans = 0
state_changes      = 0
start_time         = None
last_report        = None

def start():
    global start_time
    print("Starting stats.")
    start_time = now()

def running_for():
    global start_time
    return now() - start_time

def should_report(report_frequency):
    global last_report
    return last_report is None or \
        (now() - last_report).seconds > report_frequency

def update_last_report():
    global last_report
    last_report = now()

def now():
    return datetime.datetime.now().replace(microsecond = 0)

def scans_per_hour():
    global scans
    hours_running = running_for().seconds / 60 / 60
    return round(scans / hours_running)
