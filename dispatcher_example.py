#!/usr/bin/env python

"""
Lamplighter Dispatcher

This file is a part of Lamplighter.

The Lamplighter Dispatcher is the script that you will actually run,
which configures Lamplighter's callback functions and starts
Lamplighter itself.

This example Dispatcher illustrates how you could create callback
functions to control your Philips Hue lights (well, one light, anyway)
when Lamplighter detects that you have left or returned home. You can,
of course, configure these callbacks to do anything you like.

Lamplighter includes a naive configuration module called "config,"
which you can use if you'd like to externalize any settings for your
dispatcher. Simply place key/value pairs in your "config.ini" file and
access them like this:

    import config
    config.load()
    print config.config["your_key"]

Note that the config module will *always* return configuration values
as strings, so cast them as necessary for comparisons, etc.

Callbacks must accept a single argument, "quiet," which indicates
whether the callback was triggered during quiet hours. If you aren't
using quiet hours, you can simply ignore the argument. The example
here demonstrates how quiet hours will skip changing any Hue lights.
"""

import lamplighter
import config
import requests

def set_light_state(on = True):
    payload = {
        "on": on is True ? "true" : "false"
    }
    r = requests.put("http://hue_ip/username/lights/1/state", params=payload)

def lights_on(quiet = False):
    """Turn the lights on."""
    if not quiet:
        set_light_state(on = True)

def lights_off(quiet = False):
    """Turn the lights off."""
    if not quiet:
        set_light_state(on = False)

def main():
    # Set callbacks and run!
    lamplighter.on_away = lights_off
    lamplighter.on_home = lights_on
    lamplighter.run()

if __name__ == "__main__":
    main()
