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

        # Load the main configuration options.
        for key in parser.options('lamplighter'):
            config[key] = parser.get('lamplighter', key)
            
        # Populate the device search list.
        config['devices'] = {}
        for name in parser.options('devices'):
            config['devices'][name] = parser.get('devices', name)
