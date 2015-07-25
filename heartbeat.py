#!/usr/bin/env python3

import sqlite3
import dispatcher
import config
import time
import datetime
from pprint import pprint

HB = '/var/www/glow/htdocs/data/heartbeat.db'
LL = '/home/airborne/bin/lamplighter/lamplighter.db'

# Default callbacks, which do nothing.
on_home = lambda: None
on_away = lambda: None

def query(db, sql, params = {}, attempt = 1):
  conn = sqlite3.connect(db)
  c = conn.cursor()
  try:
    #print("Executing: %s" % sql)
    #pprint(params)
    c.execute(sql, params)
    conn.commit()
    row = c.fetchall()
    conn.close()
    return row
  except sqlite3.OperationalError:
    if attempt > 1:
      print("Big trouble in little China.")
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
               WHERE  who IN ('aaron', 'veronica')""")

  return [ { 'who': r[0],
             'state': r[1],
             'updated': r[2] }
           for r in rows ]

def set_state(who, state):
  exists = get_state(who)
  if exists == False:
    print("State not found, adding.")
    return query(LL, "INSERT INTO state (who, state, updated) VALUES (:who, :state, :updated)",
                    { "who": who, "state": state, "updated": int(time.time()) })
  else:
    print("State found, updating.")
    return query(LL, "UPDATE state SET state = :state, updated = :updated WHERE who = :who",
                    { "who": who, "state": state, "updated": int(time.time()) })

def get_last_heartbeats():
  heartbeats = query(HB,
                     """
                     SELECT who,
                            (strftime('%s') - ts) AS ts
                     FROM   heartbeats
                     WHERE  who IN ('aaron', 'veronica')""")

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
  people_here = [ name
                  for name
                  in heartbeats_by_person.keys()
                  if heartbeats_by_person[name] < 2700 ]

  return people_here

def observe_state_changes():
  # Current presence based on heartbeat.
  people_at_home = who_is_home()

  # Last recorded state.
  known_state = get_all_states()

  initial_state = get_combined_state()

  for row in known_state:
    if row['state'] == 'away' and row['who'] in people_at_home:
      # Has returned home!
      set_state(row['who'], 'home')
      print("%s has returned home!" % row['who'])
      state_changed = True

    elif row['state'] == 'home' and row['who'] not in people_at_home:
      # Has gone away!
      set_state(row['who'], 'away')
      print("%s appears to have left!" % row['who'])
      state_changed = True

    else:
      since = datetime.datetime.fromtimestamp(row['updated'])
      print("No change for %s since %s (%s)." % (row['who'], since, row['state']))

  return (initial_state, get_combined_state())

def get_combined_state():
  states = get_all_states()

  if all(r['state'] == 'away' for r in states):
    return 'away'
  else:
    return 'home'

def main():
  config.load()

  while True:
    print("\n** %s State check:" % time.strftime('%c'))

    state_change = observe_state_changes()
    if state_change[0] != state_change[1]:
      print("Observed state change from %s to %s!" % (state_change[0], state_change[1]))

    time.sleep(5)

if __name__ == "__main__":
    main()
