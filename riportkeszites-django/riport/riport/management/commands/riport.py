import importlib
import json
import logging

from django.core.management import BaseCommand, CommandError

from tudriport.common.config import getconfig
from utils.json_encoder import TudriportJSONEncoder

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    #VERBOSE = getconfig('riport.VERBOSE')
    help='Parancssori riportáló'

    def add_arguments(self, parser):
        parser.add_argument('-m', '--mode', required=True, help='Riportálási mód: %s'%(', '.join(getconfig('riport.modes'))))
        parser.add_argument('-a', '--author-id', default=None, help='Author mtmt ID')
        parser.add_argument('-p', '--publication-id', nargs='*', help='Publication mtmt ID-k. Meg lehet adni többet is, pl. --publication 1 2 3 5')
        parser.add_argument('--supervisor-id', default=None, help='Témavezető mtmt ID')
        parser.add_argument('--dbdatetime', default=None, help='Mikori állapot szerint')
        parser.add_argument('--year', default=None, help='Opcionális: melyik évi munkát? (default: teljes eddigi)')

    def handle(self, *args, **options):
        was_error = False

        mode = options['mode']
        authorid = options['author_id']
        pubid = options['publication_id']
        supervisorid = options['supervisor_id']
        dbdatetime = options['dbdatetime']
        year = options['year']

        if mode not in getconfig('riport.modes'):
            logger.error('Ismeretlen hívási mód: %s.'%(mode))
            was_error = True

        if (authorid and pubid) or not (authorid or pubid):
            logger.error('Author ID és Publication ID közül pontosan az egyiket kell megadni.')
            was_error = True

        extra_field_ids = [ f.get('id') for f in getconfig('riport.extra-fields').get(mode) ]
        if bool(supervisorid) and ('supervisor_mtmt_authid' not in extra_field_ids):
                logger.error('Témavezetőt a %s módban nem szabad megadni.'%(mode))
                was_error = True

        if was_error:
            logger.error('A riportáló hibával ért véget. =========-')
            raise CommandError()

        #dbdatetime = self.request.GET.get('dbdatetime') or timezone.now()
        riport = importlib.import_module('scoring.riport_%s' % mode).RIPORT()

        if authorid:
            riport_result = riport.pub_util_riportgen(authorid, dbdatetime, year, supervisor_mtmt=supervisorid)
        else:
            raise NotImplementedError()
            #riport_result = riport.pub_util_riportgen_publications(pubid, dbdatetime, year, supervisor_mtmt=supervisorid)

        print(json.dumps(riport_result, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False, cls=TudriportJSONEncoder))
