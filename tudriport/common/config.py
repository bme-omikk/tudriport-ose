#!/usr/bin/env python3
# -*- coding: utf8 -*-

''' Konfiguráció kezelő modul.

Másoljuk le a projekt gyökerében található `config.local.json.sample` fájlt `config.local.json` névre
és töltsük ki a `tudriport/common/config.py` fájlban található szerkezet szerint a felülbírálni kívánt kulcsokat.

Használata Pythonból:

   from ..common.config import getconfig
   getconfig('db.SQLHOST')

Használata shellből:

 - Az eredő konfigurációt tesztelhetjük: python3 -m tudriport.common.config.py --print
 - Egy konfigurációs kulcsot lekérdezhetünk (pl. shell scripthez): python3 -m tudriport.common.config.py --key db.SQLHOST

'''

import argparse
from collections.abc import Mapping
import json
from os import path
from pprint import pprint
import sys

_CONFIG_PATH = path.dirname(path.dirname(path.abspath(__file__)))

# A helyi konfigurációs JSON fájl rekurzívan felülírja az alapértelmezett konfigurációt dict kulcs szinten
_LOCAL_CONFIG_FILE = path.join(_CONFIG_PATH, 'config.local.json')

# Az alapértelmezett konfiguráció itt helyben.
# A helyi konfiguráció ennek részeit írja felül, tehát ezt lehet használni.
config = {
    # Adatbázis hozzáférési információ
    'db': {
        'SQLHOST': 'localhost',
        'SQLDB': 'tudriport_db_please_OVERRIDE_in_local_config',
        'SQLUSER': 'tudriport_be_please_OVERRIDE_in_local_config',
        'SQLPASS': 'secret_please_OVERRIDE_in_local_config',

        # alapértelmezett "alkalmazás usernév", pl. a CREATED_USER ill. UPDATED_USER mezőkhöz
        'defaultAppUser': 'anonymous', 
    },

    'sqlimport': {
        'MISSING_DIMENSION_ID': -1, # Ne bántsd, -1
        'MISSING_DIMENSION_NAMES': {
            'GENERAL': '[hiányzó dimenzió]',
            'TYPE': '(nincs típus)',
            'SUBTYPE': '(nincs besorolás)',
            'CHARACTER': '(nincs jelleg)',
            'LANGUAGE': '(nincs nyelv)',
        },

        'VERBOSE': 0,         # 0: csendes, 1, 2: kiirja a parser és az SQL részeredményeket
        'SQLDONTWRITE': 0,    # 0: normal, 1: nincs SQL commit ... azaz nem kerül ki
        'XSDPATH': "test/assets/mycite.xsd",

        'XMLHISTORY': "tudriport/sqlimport/xmlhistory",
        'JSONHISTORY': "tudriport/sqlimport/xmlhistory", # lehet közös az XMLHISTORY mappával
        'MAXFILEPERDIR': 1000,       # JSON: dupla ennyi
        'HISTORYCOMPRESS': 'tar',    # None, 'gz', 'xz' illetve 'tar', 'tar.gz', 'tar.xz'
                                     # tar esetén gyors az összerakás, és időnként futtatható cron-ból egy 'xz *tar'

        'UNIXSYSLOG': 0,             # 0: logfile, 1: syslog()
        'LOGDIR': "tudriport/sqlimport/log",
        #HIDELOGLEVELS = [],
        'HIDELOGLEVELS': ['DEBUG'],
    },

    'riport': {
        'VERBOSE': 1, # 2: JSON formában kiírja a nyers, SQL-ből közleményenként kinyerhető adathalmazt
        'modes': [
            # Különböző pontozási módok, melyeket a felhasználók használhatnak.
            # Az itt felsorolt értékeket a felhasználók azonos néven látják.
            # Minden elemhez szerepelnie kell az alábbi fájloknak:
            #   * tudriport.api.riport_[ELEM].py: pontozási logikát tartalmazó modul
            #   * tudriport.api.riport_[ELEM]_template.html: egy adott szerző pontozási táblázata
            #   * tudriport.api.riport_[ELEM]_list_template.html: listás nézet a szerzőkről
            # a python modulnak a RIPORT().pub_util_riportgen(mtmt, dbdatetime, year) fv-el kell visszaadnia a pontozást.
            # TODO a template jelenleg a django/jinja mappában keresendő, amíg a webapi használatban van
            'bme_monitoring',
            'gpk',
            'gpk_phd',
            'vik_phd',
            'gtk_ter',
            'gtk_ter_eng',
            'gtk_phd',
            'gtk_phd_eng',
            'gtk_temavezeto',
            'gtk_docens',
            'gtk_habil'
        ],
        'extra-fields': {            
            'bme_monitoring': [
                {
                    'id': 'year_count',
                    'label': 'Értékelt évek száma',
                    'hint': 'Hány év publikációs teljesítményét számolja a megadott évszámtól visszafelé? Ha üresen hagyja, 5 évet értékel a program.',
                    'views': ['summary', 'detail']
                }
            ],
            'gpk': [], 
            'gpk_phd': [], 
            'vik_phd': [
                {
                    'id': 'supervisor_mtmt_authid',
                    'label': 'Témavezető MTMT azonosítója',
                    'views': ['detail', 'adhoc']
                }
            ],
            'gtk_ter': [
                {
                    'id': 'year_count',
                    'label': 'Értékelt évek száma',
                    'hint': 'Hány év publikációs teljesítményét számolja a megadott évszámtól visszafelé? Ha üresen hagyja, 3 évet értékel a program.',
                    'views': ['summary', 'detail']
                }
            ],
            'gtk_ter_eng': [
                {
                    'id': 'year_count',
                    'label': 'Year count to score',
                    'hint': 'Number of years to score counting from the given year backwards. If left blank, the program will score 3 years.',
                    'views': ['summary', 'detail']
                }
            ],
            'gtk_phd': [
                {
                    'id': 'supervisor_mtmt_authid',
                    'label': 'Témavezető MTMT azonosítója',
                    'views': ['detail', 'adhoc']
                }
            ],
            'gtk_phd_eng': [
                {
                    'id': 'supervisor_mtmt_authid',
                    'label': 'Supervisor\'s MTMT identifier',
                    'views': ['detail', 'adhoc']
                }
            ],
            'gtk_temavezeto': [],
            'gtk_docens': [],
            'gtk_habil': []
        }
    },

    'webapi': {
        'VERBOSE': 0, # 0: csak táblázat, 2: debug részletek is soronként
    },

    'django': {
        'admins': 'root|root@localhost',  # comma separeted list of [NAME]|[EMAIL] pairs
        'settings_module': 'riport.settings.production',
        'secret_key': 'REPLACE_WITH_A_SECRET_KEY',
        'ALLOWED_HOSTS': '*',  # comma separetad list of allowed hosts.
        'groups': ['User', 'SubUnitAdmin', 'Admin', ],
        'logfile': '/tmp/debug-tudriport.log', # please override in the local configuration
        'logfile-misc': '/tmp/debug-tudriport-misc.log', # catch-all for misc log entries. Please override in the local configuration
    },

    'common': {
        'epoch': '1970-01-01T00:00:00Z', # because of 'Z', this can be parsed to timezone-aware datetime object using django.utils.dateparse.parse_datetime
    },

	'email': {
        'host': 'localhost',
        'port': '25',
		'default_from_email': 'noreply@example.org',
	},

    # adatforrás lekérdezési konfiguráció
    #  - kulcs az adatforrás neve, pl. mtmt1, mtmt2
    #  - az adatforráson belül ismét egy dictionary, amiben link minta van:
    #     - publication: egy közlemény géppel olvasható lekérdezésére (pl. XML vagy JSON)
    #     - author: egy szerző összes közleményének azonosítójára
    #     - author-all: egy szerző összes közleménye a betöltési formátumban (teszteléshez)
    #     - doc_refresh: a frissítendő közlemények azonosítója (egyelőre nincs benne placeholder az MTMT1 esetén)
    #
    # @@@ a placeholder, amit az azonosítóra kell cserélni.
    # Többször is megjelenhet a mintában, ekkor minden előfordulása cserélendő.
    #
    # az mtmt1.author linkből majd szeretnék elegánsabbat, ami csak egy text fájlban közleményazonosítókat ad vissza
    # Figyelem: az o25 kezdetű token ne kerüljön a source tree-be!
    'input_sources': {
        'mtmt1': {
            'publication': 'https://m1.mtmt.hu/www/index.php?mode=xml&DocumentID=@@@&Full=1',
            'author':      'https://m1.mtmt.hu/pubs.php?id=@@@',
            'doc_refresh': '',
        },
        'mtmt2': {
            'publication': 'https://m2.mtmt.hu/api/publication/?&cond=mtid;in;@@@&format=json&fields=type:1,subType:1,category:1,citations:1,identifiers:1,authorships.fullName:0,authorships.author.speciality:0,authorships.organizations.parent.parent.parent.parent.parent.parent.parent.parent.parent.parent:1,publishedAt.partOf:0,book.publishedAt.partOf:0,publishers.cities.partOf:0,book.publishers.cities.partOf:0,journal.publishers.cities.partOf:0,book.seriesMembers.series.issns.issn:0,book.conference:0,journal.comment:0,citations.related.error:0&exFields=authorships.author.affiliations,authorships.author.degrees,authorships.publication,category.typesAllowed,citations.publication,references,type.categories,type.subTypes&page=1&size=1000',
            'author':      'https://m2.mtmt.hu/api/publication/?&cond=authors;in;@@@&format=json&incFields=mtid:1&page=1&size=1000',
            'author-all':  'https://m2.mtmt.hu/api/publication/?&cond=authors;in;@@@&format=json&&fields=type:1,subType:1,category:1,citations:1,identifiers:1,authorships.fullName:0,authorships.author.speciality:0,authorships.organizations.parent.parent.parent.parent.parent.parent.parent.parent.parent.parent:1,publishedAt.partOf:0,book.publishedAt.partOf:0,publishers.cities.partOf:0,book.publishers.cities.partOf:0,journal.publishers.cities.partOf:0,book.seriesMembers.series.issns.issn:0,book.conference:0,journal.comment:0,citations.related.error:0&exFields=authorships.author.affiliations,authorships.author.degrees,authorships.publication,category.typesAllowed,citations.publication,references,type.categories,type.subTypes&page=1&size=1000',
            'doc_refresh': '',
            'journal':     'https://m2.mtmt.hu/api/journal/?cond=mtid;in;@@@&format=json',
            'conference':  'https://m2.mtmt.hu/api/conference/?cond=mtid;in;@@@&format=json',
            'journal_mtaListed_info': 'https://m2.mtmt.hu/api/predatorrating/?cond=periodical.mtid;in;@@@&format=json',
        },
        'default_sourceid': 'mtmt2',
        'max_publication_processing': 100,
        'max_author_processing': 20,
        'sleep_seconds_per_iteration': 5.0,
        'sleep_seconds_per_operation': 1.0,
    },
    # kliens konfiguráció
    # load-time bővítést lásd: _extend_client_config()
    'client_config': {
        'mtmt2': {
            'publication_list_view_url': 'https://m2.mtmt.hu/api/publication/?&format=html&cite_type=2&ty_on=1&st_on=1&com_on=1&la_on=1&sort=publishedYear,desc&sort=firstAuthor,asc&size=100&cond=mtid;in;@@@',
            'citation_list_view_url': 'https://m2.mtmt.hu/api/citation/?&format=html&cite_type=4&ty_on=1&st_on=1&com_on=1&la_on=1&sort=publication.publishedYear,desc&sort=publication.firstAuthor,asc&sort=related,desc&size=100&cond=mtid;in;@@@'
        },
        'doi': 'http://www.doi.org/@@@',
        'gpk_phd_container_urls': {
            'c': 'https://m2.mtmt.hu/api/conference/@@@?format=json',
            'bc': 'https://m2.mtmt.hu/api/publication/@@@?format=json',
            'j': 'https://m2.mtmt.hu/api/journal/@@@?format=json',
        },
        # A felhasználói felületre küldendő üzenetek, pl. tesztrendszerről szóló figyelmeztetés
        # A megfelelő tömbök egy-egy eleme egy-egy üzenetként jelenik meg. AZ üzenet a fleületen bezárható, de nem tűnik el időzítetten.
        'user_interface_notifications': {
            'info': [],
            'warning': [],
            'error': [],
        },
    }
}

class ConfigurationException(Exception):
    '''Konfigurációs hiba, pl. nincs ilyen kulcs'''

def getconfig(key):
    '''Melyik konfigurációs kulcs értékét adja vissza. Pl. db.SQLHOST a config struktúrában a db dict SQLHOST kulcsát írja ki.'''
    _cnf = config
    for e in key.split('.'):
        if e in _cnf:
            _cnf = _cnf.get(e)
        else:
            raise ConfigurationException('A {} konfigurációs kulcs nem található, a kért útvonal: {}\n'.format(e, key))
    return _cnf

def _extend_client_config():
    '''A klienskonfigurációt kibóvíti másolással, hogy ne kelljen duplikálni az elemeit.'''
    config['client_config']['mtmt2']['publication'] = config['input_sources']['mtmt2']['publication']

# _dict_merge copied from https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
# created by @angstwad (https://github.com/angstwad)
def _dict_merge(dct, merge_dct):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    """
    for k, v in merge_dct.items():
        if (k in dct and isinstance(dct[k], dict)
                and isinstance(merge_dct[k], Mapping)):
            _dict_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]

# Helyi konfigurációval az alapértelmezett felülírása
if path.exists(_LOCAL_CONFIG_FILE):
    with open(_LOCAL_CONFIG_FILE, encoding='utf-8') as f:
        _local_config = json.load(f)
        _dict_merge(config, _local_config)

# kliens konfiguráció kibővítése
_extend_client_config()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Konfigurációs modul és konfigurációkezelő utility')
    parser.add_argument('-p', '--print', action='store_true', help='Az eredő konfiguráció kiírása: az alapértelmezett, beledolgozva a helyi konfigurációval.')
    parser.add_argument('-k', '--key', help='Melyik konfigurációs kulcs értékét írja ki. Pl. db.SQLHOST a config struktúrában a db dict SQLHOST kulcsát írja ki. FIGYELEM: csak elemi, newline nélküli értéket írassunk ki!')
    args = parser.parse_args()

    if args.print and args.key:
        sys.stderr.write('A --print és a --key közül csak az egyik használható!\n')
        sys.exit(2)

    if args.print:
        pprint(config)

    if args.key:
        pprint(getconfig(args.key))
