#!/usr/bin/env python

"""Lamplighter: Automated light management.

Lamplighter will periodically search the network for specific MAC
addresses. If the MAC addresses are not found, it will switch off
the lights. It does the inverse when at least one MAC address
appears."""

import os
import sys
import time
import datetime
import subprocess
import requests
import urllib
import signal

def main():
    signal.signal(signal.SIGTERM, handle_term)

    while True:
        search()
        time.sleep(1)

def search():
    """The main thread."""

    state = current_state()

    phone_count = False
    while phone_count is False:
        log("Finding initial phone count...")
        phone_count = count_phones_present()

    if state == False:
        log("No current state. Initializing.")
        if phone_count is 0:
            log("Current state: away.")
            save_state("away")
        else:
            log("Current state: home.")
            save_state("home")
    else:
        if state == "home":
            log("Current state is home.")
            if phone_count is 0:
                # Delay ten seconds and then check three more times.
                log("*** Possible change to away; wait 10 sec. and search 3 more times...")
                time.sleep(10)

                log("*** Performing 3 confirmation searches...")
                if all(count_phones_present() is 0 for x in range(3)):
                    log("Confirmed. Changing state to away.")
                    save_state("away")
                    lights_off()
                    send_message("Lights are now off. Have a good day.")
                else:
                    log("False alarm. State unchanged.")
            else:
                log("No change in state.")
        elif state == "away":
            log("Current state is away.")
            if phone_count > 0:
                log("*** State changing to home.")
                save_state("home")
                lights_on()
                send_message("Lights are now on. Welcome home.")
            else:
                log("No change in state. Exiting.")

def log(message):
    """Output a pretty log message."""
    pid = os.getpid()
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    print "[%s] %s: %s" % (pid, now, message)

def state_file_path():
    """Return the path to the state file."""
    return  "/tmp/welcome_home_state"
    
def save_state(state):
    """Save the given state to disk."""
    statefile_name = state_file_path()
    if os.path.isfile(statefile_name):
        os.unlink(statefile_name)
    file(statefile_name, "w").write(state)

def current_state():
    """Find the current (last saved) state."""
    statefile_name = state_file_path()
    if os.path.isfile(statefile_name):
        statefile = open(statefile_name, "r")
        statefile.seek(0)
        state = statefile.readline().rstrip("\n")
        return state
    else:
        return False

def get_pidfile_name():
    """Return the name of our pid file."""
    return str("/var/run/lamplighter.pid")

def handle_term(signum, frame):
    """Clean up and exit."""
    log("Received SIGTERM; cleaning up and exiting.")
    os.unlink(get_pidfile_name())
    sys.exit()

def create_pidfile():
    """Create a pidfile for this process."""
    pid = str(os.getpid())
    log("Creating pidfile for %s" % pid)
    file(get_pidfile_name(), "w").write(pid)

def count_phones_present():
    """Count the known phones on the network."""
    log("Searching for phones...")
    try:
        count = 0
        phone_search = subprocess.check_output(["sudo",
                                                "nmap",
                                                "-sn",
                                                "-n",
                                                "-T5",
                                                "192.168.10.50-255"])

        if phone_search.find("34:4D:F7:0E:C7:5B") > -1:
            log("Found Aaron's phone.")
            count += 1

        if phone_search.find("FC:C2:DE:58:99:AD") > -1:
            log("Found Veronica's phone.")
            count += 1
        
        return count
    except subprocess.CalledProcessError:
        # Grep returns a non-zero exit status when nothing is found.
        log("Search returned non-zero exit status.")
        return False

def lights_on():
    """Turn the lights on."""
    r = requests.post("http://lights.skynet.net/scenes/by_name/Relax")

def lights_off():
    """Turn the lights off."""
    r = requests.post("http://lights.skynet.net/scenes/by_name/All+Off")

def send_message(message):
    """Send a text message to my phone through Twilio."""
    log("Twilio says: " + subprocess.check_output(
        'curl -s -XPOST https://api.twilio.com/2010-04-01/Accounts/' + \
        'ACed9a2d1111e08e78258af59b55f43c87/Messages.json ' + \
        '-d "Body=' + urllib.quote_plus(message) + '" ' + \
        '-d "To=%2B18608055785" ' + \
        '-d "From=%2B18607852006" ' + \
        '-u "ACed9a2d1111e08e78258af59b55f43c87:78d2c8e770e55d9a56cdad00e1585e82"',
        stderr=subprocess.STDOUT,
        shell=True
    ))

if __name__ == "__main__":
    main()
