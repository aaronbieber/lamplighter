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

        for key in ['twilio_account_id',
                    'twilio_auth_token',
                    'twilio_outgoing_number',
                    'twilio_notification_numbers']:

            config[key] = parser.get('lamplighter', key)
