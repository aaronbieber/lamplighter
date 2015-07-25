#!/usr/bin/env python

"""Configuration module.

This module is a part of Lamplighter. See lamplighter.py for more."""

import os
from configparser import SafeConfigParser

config = {}

def load(reload = False):
    if not len(config) or reload:
        if os.path.isfile('config.ini'):
            parser = SafeConfigParser()
            parser.read('config.ini')
            config['users'] = []

            for section in parser.sections():
                if section == 'lamplighter':
                    # Load the main configuration options.
                    for key in parser.options(section):
                        config[key] = parser.get(section, key)
                else:
                    # User options
                    config['users'].append({
                        'alias': section,
                        'name': parser.get(section, 'name'),
                        'user_agent_match': parser.get(section, 'user_agent_match'),
                        'notification_number': parser.get(section, 'notification_number')
                    })
