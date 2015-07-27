#!/usr/bin/env python

import sqlite3
import logger
from pprint import pformat

def query(sql, params = {}, attempt = 1):
    conn = sqlite3.connect("lamplighter.db")
    c = conn.cursor()
    try:
        logger.log("Executing: %s" % sql, logger.LOG_DEBUG)
        logger.log("Params:\n%s" % pformat(params, indent = 2), logger.LOG_DEBUG)
        c.execute(sql, params)
        conn.commit()
        row = c.fetchall()
        conn.close()
        return row
    except sqlite3.OperationalError:
        logger.log("Big trouble in little China.")
        return False
