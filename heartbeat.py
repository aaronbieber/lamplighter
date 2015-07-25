#!/usr/bin/env python3

import os
import sys
import sqlite3
import dispatcher
import config
import time
import datetime
from pprint import pprint
from pprint import pformat

HB = "/var/www/glow/htdocs/data/heartbeat.db"
LL = "/home/airborne/bin/lamplighter/lamplighter.db"

# Default callbacks, which do nothing.
on_home = lambda quiet, who = []: None
on_away = lambda quiet, who = []: None

# Definition of log levels.
LOG_NONE  = 0
LOG_BRIEF = 1
LOG_INFO  = 2
LOG_DEBUG = 3

def get_all_aliases():
    return [ u["alias"] for u in config.config["users"] ]

def get_all_aliases_for_where():
    return ', '.join([ "'%s'" % x for x in get_all_aliases() ])

def log_name_by_value(log_value):
    vars = globals().copy()
    for var in vars:
        if var[:4] == "LOG_" and vars[var] == log_value:
            return var[4:]

    return False

def log(message, level = LOG_BRIEF):
    """Output a pretty log message."""
    user_log_level = config.config["log_level"]
    log_level_name = log_name_by_value(level)
    if globals()[user_log_level] >= level:
        pid = os.getpid()
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        print("[%s] %s %s: %s" % (pid, log_level_name, now, message))
        sys.stdout.flush()

def query(db, sql, params = {}, attempt = 1):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    try:
        log("Executing: %s" % sql, LOG_DEBUG)
        log("Params:\n%s" % pformat(params, indent = 2), LOG_DEBUG)
        c.execute(sql, params)
        conn.commit()
        row = c.fetchall()
        conn.close()
        return row
    except sqlite3.OperationalError:
        if attempt > 1:
            log("Big trouble in little China.")
            return False

        init_database()
        return query(db, sql, params, attempt = 2)

def init_database():
    query(LL, "CREATE TABLE state (who varchar(32), state varchar(32), updated bigint)")

def get_state(who):
    state = query(LL, "SELECT state, updated FROM state WHERE who = :who", {"who": who})
    if state != False and len(state):
        return state[0]

    return False

def get_all_states():
    rows = query(LL,
                 """
                 SELECT who,
                        state,
                        updated
                 FROM   state
                 WHERE  who IN (%s)""" % get_all_aliases_for_where())

    return [{ "who": r[0],
              "state": r[1],
              "updated": r[2] }
            for r in rows ]

def set_state(who, state):
    exists = get_state(who)
    if exists == False:
        log("State not found, adding.", LOG_DEBUG)
        return query(LL, "INSERT INTO state (who, state, updated) VALUES (:who, :state, :updated)",
                     { "who": who, "state": state, "updated": int(time.time()) })
    else:
        log("State found, updating.", LOG_DEBUG)
        return query(LL, "UPDATE state SET state = :state, updated = :updated WHERE who = :who",
                     { "who": who, "state": state, "updated": int(time.time()) })

def get_last_heartbeats():
    heartbeats = query(HB,
                       """
                       SELECT who,
                              (strftime('%s') - ts) AS ts
                       FROM   heartbeats
                       WHERE  who IN (%s)""" % ('%s', get_all_aliases_for_where()))

    return heartbeats

def get_heartbeat(who):
    row = query("SELECT ts FROM heartbeats WHERE who = :who", { "who": who })

    if len(row):
        return int(row[0])

    return False

def who_is_home():
    heartbeats = get_last_heartbeats()

    # From [('aaron': 123), ('veronica': 456)] to {'aaron': 123, 'veronica': 456}
    heartbeats_by_person = { row[0]: row[1] for row in heartbeats }

    # Only names whose last heartbeat was < 45 minutes ago.
    people_at_home = [ name
                       for name
                       in heartbeats_by_person.keys()
                       if heartbeats_by_person[name] < 2700 ]

    return people_at_home

def observe_state_changes():
    # Current presence based on heartbeat.
    people_at_home = who_is_home()

    # Last recorded state.
    known_state = get_all_states()

    # Current combined state (anyone home = home, else away)
    initial_state = get_combined_state()

    # Whose state changed?
    who_changed = []

    for row in known_state:
        if row["state"] == "away" and row["who"] in people_at_home:
            # Has returned home!
            set_state(row["who"], "home")
            log("%s has returned home!" % row["who"])
            who_changed.append(row["who"])

        elif row["state"] == "home" and row["who"] not in people_at_home:
            # Has gone away!
            set_state(row["who"], "away")
            log("%s appears to have left!" % row["who"])
            likely_departure = datetime.datetime.fromtimestamp(time.time() - 2700).strftime("%c")
            log("Likely departure time: %s" % likely_departure)
            who_changed.append(row["who"])

        else:
            since = datetime.datetime.fromtimestamp(row["updated"])
            log("No change for %s since %s (%s)." % (row["who"], since, row["state"]), LOG_INFO)

    return (initial_state, get_combined_state(), who_changed)

def get_combined_state():
    states = get_all_states()

    if all(r["state"] == "away" for r in states):
        return "away"
    else:
        return "home"

def within_quiet_hours():
    now = datetime.datetime.now()

    # The config module does not know nor care what the values within
    # the config file are, nor their types. We'll get strings for
    # everything, so coerce them into ints so we can compare them.
    start = int(config.config["quiet_hours_start"])
    end = int(config.config["quiet_hours_end"])

    if start is 0 and end is 0:
        return False

    # Quiet hours is a range within the same day.
    if start < end and \
       start <= now.hour and end > now.hour:
        return True

    # Quiet hours is a range spanning a day change (through midnight).
    if start > end and \
       (start <= now.hour or end > now.hour):
        return True

    return False

def run():
    """Loop continuously, responding to state changes."""

    no_ops = 0
    log("Beginning observation...")

    while True:
        state_change = observe_state_changes()
        if state_change[0] != state_change[1]:
            log("Observed state change from %s to %s!" % (state_change[0], state_change[1]))

        if state_change[1] == "away":
            on_away(within_quiet_hours(), state_change[2])

        elif state_change[1] == "home":
            on_home(within_quiet_hours(), state_change[2])

        else:
            no_ops += 1
            if no_ops >= 60:
                no_ops = 0
                log("No state changes observed in the last five minutes.", LOG_BRIEF)

        time.sleep(5)

def main():
    """Run the main program directly.

Note that this program is designed to be imported into a dispatcher
script and run from there (by calling run()). This entrypoint
supports running this script directly, which will do essentially the
same thing, except that the on_away() and on_home() callbacks will
be empty, so it won't do much."""
    config.load()

    log("Configuration loaded.")
    run()

if __name__ == "__main__":
    main()
