import importlib

from riport.management.commands import ext_authorlist

def get_author_points(mode, mtmt, year=None, dbdatetime=None):
    modul = importlib.import_module('scoring.riport_%s' % mode)
    return modul.RIPORT().pub_util_riportgen(mtmt, dbdatetime, year, 1)

def get_publications_points(mode, publisheds, year=None, dbdatetime=None):
    modul = importlib.import_module('scoring.riport_%s' % mode)
    return modul.RIPORT().pub_util_riportgen_publications(publisheds, dbdatetime, year, 1)

def import_ext_authorlist_parser(fname, org, unit, subunit, subsub_unit):
    ext_authorlist.authors_parse_from_file_wrapper(fname, org, unit, subunit, subsub_unit)
