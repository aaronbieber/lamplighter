#!/usr/bin/env python

from flask import Flask, request, render_template
from pprint import pformat
import db
import time
import config
import sqlite3
import datetime
import lamplighter

app = Flask("Lamplighter")
app.debug = True
config.load()

def get_alias_by_ua(ua):
    """Get a user's alias by matching their User Agent string."""
    for user in config.config['users']:
        if user['user_agent_match'] in ua:
            return user['alias']

    return False

def get_heartbeat_by_alias(alias):
    row = db.query("""
                   SELECT ts
                   FROM   heartbeats
                   WHERE  who = :who""",
                   {"who": alias})
    if len(row):
        return int(row[0][0])

    return False

def create_heartbeat(alias):
    ts = int(time.time())
    res = db.query("""
                   INSERT INTO heartbeats (who, ts)
                   VALUES (:who, :ts)""",
                   {"who": alias, "ts": ts})
    if res != False:
        return ts

    return False

def update_heartbeat(alias):
    ts = int(time.time())
    res = db.query("""
                   UPDATE heartbeats
                   SET ts = :ts
                   WHERE  who = :who""",
                   {"who": alias, "ts": ts})
    if res != False:
        return ts

    return False

@app.route("/heartbeat/set")
def heartbeat_set():
    alias = get_alias_by_ua(str(request.user_agent))
    if alias:
        current_hb = get_heartbeat_by_alias(alias)
        if current_hb:
            ts = update_heartbeat(alias)
        else:
            ts = create_heartbeat(alias)

        if ts:
            return "%s = %s. OK." % (alias, ts)
    else:
        return "User agent not recognized."

@app.route("/heartbeat/get")
def heartbeat_get():
    alias = get_alias_by_ua(str(request.user_agent))
    if alias:
        hb = get_heartbeat_by_alias(alias)
        if hb:
            return str(hb)

    return "User agent not recognized."

@app.route("/who")
def who():
    # Convenience function to format UNIX timestamps.
    t = lambda ts: datetime.datetime.fromtimestamp(ts).strftime('%c')

    # Map user aliases to names
    names_by_alias = {}
    for user in config.config['users']:
        names_by_alias[user['alias']] = user['name']

    # All current states
    all_states = lamplighter.get_all_states()
    people = [ { "name": names_by_alias[s["who"]],
                 "state": s["state"],
                 "since": t(s["updated"]) } for s in all_states ]
    
    return render_template('who.html', people = people)

if __name__ == "__main__":
    app.run()
