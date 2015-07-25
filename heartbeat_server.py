#!/usr/bin/env python

from flask import Flask
from flask import request
from pprint import pformat
import db
import time
import config
import sqlite3

app = Flask("Lamplighter")
config.load()

def get_alias_by_ua(ua):
    """Get a user's alias by matching their User Agent string."""
    for user in config.config['users']:
        if user['user_agent_match'] in ua:
            return user['alias']

    return False

def get_heartbeat_by_alias(alias):
    return db.query(db.HB,
                    """
                    SELECT ts
                    FROM   heartbeats
                    WHERE  who = :who""",
                    {"who": alias})

def create_heartbeat(alias):
    ts = int(time.time())
    res = db.query(db.HB,
                   """
                   INSERT INTO heartbeats (who, ts)
                   VALUES (:who, :ts)""",
                   {"who": alias, "ts": ts})
    if res != False:
        return ts

    return False

def update_heartbeat(alias):
    ts = int(time.time())
    res = db.query(db.HB,
                   """
                   UPDATE heartbeats
                   SET ts = :ts
                   WHERE  who = :who""",
                   {"who": alias, "ts": ts})
    if res != False:
        return ts

    return False

@app.route("/")
def hello():
    return "Hello, world."

@app.route("/heartbeat/set")
def heartbeat_set():
    alias = get_alias_by_ua(str(request.user_agent))
    if alias:
        current_hb = get_heartbeat_by_alias(alias)
        if len(current_hb):
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
        return pformat(get_heartbeat_by_alias(alias))

    return "User agent not recognized."

if __name__ == "__main__":
    app.run()
