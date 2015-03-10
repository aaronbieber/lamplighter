#!/usr/bin/env python

"""Configuration module.

This module is a part of Lamplighter. See lamplighter.py for more."""

import os
from ConfigParser import SafeConfigParser

config = {}

def load():
    if os.path.isfile('config.ini'):
        parser = SafeConfigParser()
        parser.read('config.ini')

        for key in parser.options('lamplighter'):
            config[key] = parser.get('lamplighter', key)
