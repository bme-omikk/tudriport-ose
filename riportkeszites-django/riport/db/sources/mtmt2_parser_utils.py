'''Ez a modul segédfüggvényeket definiál az MTMT2-ből lekért JSON állományok parsolásához
'''
from common.constants import M2_OTYPE_PREDATOR_RATING, M2_OTYPE_RATING, MTA_LISTED_ZERO_RATING_CODE

import logging
import json

logger = logging.getLogger(__name__)

def mtmt2_parse_pubids(jsonstring):
    """A jsonstring string-paraméterből beolvassa a közlemények MTMT azonosítóit, és listában visszaadja.
    """
    root = json.loads(jsonstring)
    records = []
    for c in root['content']:
        records.append(c['mtid'])
    return records

def mtmt2_is_journal_mtaListed(ratings, year):
    """A ratings listából kiolvassa, hogy a year paraméterben megadott évre szerepel-e MTA-listás megjelölés.
    """
    for r in ratings:
        if (r['otype'] == M2_OTYPE_PREDATOR_RATING and 'ratingType' in r and r['ratingType']['otype'] == M2_OTYPE_RATING
                and 'code' in r['ratingType'] and r['ratingType']['code'] == MTA_LISTED_ZERO_RATING_CODE):
            if r.get('validFromYear', year) <= year and year <= r.get('validToYear', year):
                return True

    return False
