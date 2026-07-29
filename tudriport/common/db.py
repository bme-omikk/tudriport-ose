#!/usr/bin/env python3
import os

import pgdb
from .config import getconfig

def dbconnect():
    """Csatlakozik az adatbázishoz, és visszaadja a kapcsolat-objektumot."""
    db = pgdb.connect(host=getconfig('db.SQLHOST'), dbname=getconfig('db.SQLDB'), user=getconfig('db.SQLUSER'), password=getconfig('db.SQLPASS'))

    return db

def getsqlutc(db=dbconnect()):
    with db:
        with db.cursor() as cursor:
            sqlutc=cursor.execute("select now() at time zone 'utc'").fetchone()
    return str(sqlutc[0])
