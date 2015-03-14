#!/usr/bin/env python

import core
import requests

def lights_on():
    """Turn the lights on."""
    r = requests.post("http://lights.skynet.net/scenes/by_name/Relax")

def lights_off():
    """Turn the lights off."""
    r = requests.post("http://lights.skynet.net/scenes/by_name/All+Off")

def main():
    # Set callbacks and run!
    core.on_away = lights_off
    core.on_home = lights_on
    core.run()

if __name__ == "__main__":
    main()
