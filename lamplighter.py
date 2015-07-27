#!/usr/bin/env python

import os
import sys
import copy
import dispatcher
import config
import time
import datetime
import logger
from db import query
from db import HB
from db import LL
from pprint import pprint
from pprint import pformat

# Default callbacks, which do nothing.
on_home       = lambda quiet, who: None
on_away       = lambda quiet, who: None
on_first_home = lambda quiet, who: None
on_last_away  = lambda quiet, who: None

def get_all_aliases():
    return [ u["alias"] for u in config.config["users"] ]

def get_all_aliases_for_where():
    return ', '.join([ "'%s'" % x for x in get_all_aliases() ])

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
        logger.log("State not found, adding.", logger.LOG_DEBUG)
        return query(LL, "INSERT INTO state (who, state, updated) VALUES (:who, :state, :updated)",
                     { "who": who, "state": state, "updated": int(time.time()) })
    else:
        logger.log("State found, updating.", logger.LOG_DEBUG)
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
    new_state = []

    # Whose state changed?
    changes = {}

    for row in known_state:
        new_row = copy.deepcopy(row)
        if row["state"] == "away" and row["who"] in people_at_home:
            # Has returned home!
            set_state(row["who"], "home")
            new_row['state'] = 'home'
            logger.log("%s has returned home!" % row["who"])
            changes[row["who"]] = ('away', 'home')

        elif row["state"] == "home" and row["who"] not in people_at_home:
            # Has gone away!
            set_state(row["who"], "away")
            new_row['state'] = 'away'
            logger.log("%s appears to have left!" % row["who"])
            likely_departure = datetime.datetime.fromtimestamp(time.time() - 2700).strftime("%c")
            logger.log("Likely departure time: %s" % likely_departure)
            changes[row["who"]] = ('home', 'away')

        else:
            since = datetime.datetime.fromtimestamp(row["updated"])
            logger.log("No change for %s since %s (%s)." % (row["who"], since, row["state"]), logger.LOG_INFO)

        new_state.append(new_row)

    return (get_combined_state(known_state),
            get_combined_state(new_state),
            changes)

def get_combined_state(states):
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
    logger.log("Beginning observation...")

    while True:
        state_change = observe_state_changes()
        logger.log("Observed change: %s" % pformat(state_change, indent = 2), logger.LOG_INFO)

        if state_change[0] != state_change[1]:
            logger.log("Observed state change from %s to %s!" % (state_change[0], state_change[1]))

            if state_change[1] == "away":
                on_last_away(within_quiet_hours(), state_change[2])

            elif state_change[1] == "home":
                on_first_home(within_quiet_hours(), state_change[2])

        elif len(state_change[2]):
            # Someone's state changed, but it didn't affect the combined state.
            for alias in state_change[2]:
                if state_change[2][alias][1] == 'away':
                    on_away(within_quiet_hours(), alias)
                elif state_change[2][alias][1] == 'home':
                    on_home(within_quiet_hours(), alias)

            logger.log("Single state change: %s" % pformat(state_change[2], indent = 2))

        else:
            no_ops += 1
            if no_ops >= 60:
                no_ops = 0
                logger.log("No state changes observed in the last five minutes.")

        time.sleep(5)

def main():
    """Run the main program directly.

Note that this program is designed to be imported into a dispatcher
script and run from there (by calling run()). This entrypoint
supports running this script directly, which will do essentially the
same thing, except that the on_away() and on_home() callbacks will
be empty, so it won't do much."""
    config.load()

    logger.log("Configuration loaded.")
    run()

if __name__ == "__main__":
    main()
