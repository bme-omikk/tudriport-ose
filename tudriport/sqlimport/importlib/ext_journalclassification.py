#!/usr/bin/env python3

from ...common.config import getconfig
from ...common.db import dbconnect

import pgdb
import csv
import sys
import argparse


def journclasswrite(db, jclasslist):
    #print (jclasslist)
    sql_ext_jclasscmp_issn = "select id from ext_journal_classification where
                              (org, unit, issn, eissn) is not distinct from (%(org)s, %(unit)s, %(issn)s, %(eissn)s)
                              and valid_to is null"

    sql_ext_jclasscmp_param = """select id from ext_journal_classification
             where (org, unit, issn, eissn) is not distinct from (%(org)s, %(unit)s, %(issn)s, %(eissn)s) and valid_to is null and
             (category, international, shortname, name)
             is distinct from 
             (%(category)s, %(international)s, %(shortname)s, %(name)s)"""

    sql_ext_jclassins = """insert into ext_journal_classification
             (org, unit, issn, eissn, category, international, shortname, name, valid_from)
             VALUES (%(org)s, %(unit)s, %(issn)s, %(eissn)s, %(category)s, %(international)s, %(shortname)s, %(name)s, now())"""

    # Ezzel a "with db:" blokkal nálam 930ms egy 880 tételes folyóiratlista betöltése, nélküle pedig 370ms.
    # Az oka, hogy a "with db:" blokk minden egyes lefutása commitol.
    with db:
        with db.cursor() as cur_select:
            if cur_select.execute(sql_ext_jclasscmp_issn, jclasslist).fetchone() is None: # új
                with db.cursor() as cur_insert:
                    cur_insert.execute(sql_ext_jclassins, jclasslist)
            else:  # van, nézzük meg hogy van-e eltérés a paraméterekben?
                rid = cur_select.execute(sql_ext_jclasscmp_param, jclasslist).fetchone()
                if rid is not None:
                    with db.cursor() as cur_insert:
                        idt = {'sid': rid[0]}
                        cur_insert.execute(sql_ext_jclassins, jclasslist)
                        cur_insert.execute("update ext_journal_classification set valid_to=now() where id=%(sid)s", idt)

    return

# ami nem volt a csv-ben, lezárni
def dbclean(db, org_unit, issnset):
    sql_ext_jclasscmp_all = "select id, issn from ext_journal_classification where (org, unit) is not distinct from (%(org)s, %(unit)s) and valid_to is null"
    with db.cursor() as cur_select:
        allissn = cur_select.execute(sql_ext_jclasscmp_all, org_unit).fetchall()
        for ai in allissn:
            if ai[1] not in issnset:
                print(ai[0], ai[1], "close")
                idt = {'sid': ai[0]}
                with db.cursor() as cur_insert:
                    cur_insert.execute("update ext_journal_classification set valid_to=now() where id=%(sid)s", idt)


def journclassparser(fname, jclasslist_default):
    # itt most nem akartam a tranzakciókezelést rábízni a PyGreSQL-ra
    # és a végén amúgyis volt adatbáziskapcsolat bezárás
    jclasslist_default['org'] = jclasslist_default['org'].upper()
    jclasslist_default['unit'] = jclasslist_default['unit'].upper()
    db = dbconnect()
    try:
        issnset = set()
        for f in csv.reader(open(fname,'r')):
            jclasslist = jclasslist_default
            jclasslist['issn'] = f[0].strip()
            if jclasslist['issn'][0] > '9': continue # comment sor, nem ISSN

            jclasslist['eissn'] = f[3].strip()
            jclasslist['celkozonseg'] = f[6].strip()
            jclasslist['category'] = f[7].strip()
            jclasslist['name'] = f[8].strip()
            jclasslist['shortname'] = f[9].strip()

            # nemzetközi?
            jclasslist['international']= {
                'hazai': 'no',
                'nemzetk': 'yes'
            }.get(jclasslist['celkozonseg'], 'not given')

            issnset.add(jclasslist['issn'])
            journclasswrite(db, jclasslist)
        dbclean(db, jclasslist_default, issnset) # default: org, unit
    finally:
        db.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Folyóirat-osztályozások betöltése (ext_journalclassification tábla feltöltése)')
    parser.add_argument('-f', '--file', required=True, help='Melyik fájlból olvassa be?')
    parser.add_argument('--org', required=True, help='Szervezet neve (pl. BME, BME-kar vagy MTA-osztály)')
    parser.add_argument('--unit', required=True, help='Folyóiratlista neve, (pl. GPK, VIK-PHD vagy PTB (bizottság neve)')
    args = parser.parse_args()

    jclasslist_default = {}
    jclasslist_default['org'] = args.org
    jclasslist_default['unit'] = args.unit
    jclasslist = journclassparser(args.file, jclasslist_default)
