from django.core.management import BaseCommand, CommandError

from riport.models.external import INPUT_QUEUE_TYPE_AUTHOR, INPUT_QUEUE_TYPE_PUBLICATION, INPUT_QUEUE_PRIORITY_DEFAULT
from riport.models.external import ExtAuthorlist
from db.importlib.input_queue import input_queue_write_publications_for_author, input_queue_dbwrite
from tudriport.common.config import getconfig

import logging

logger = logging.getLogger(__name__)

MODULE_NAME = 'input_queue_writer'

class Command(BaseCommand):
    help='Ez a segédprogram az input_queue -ba ír, ami alapján az adatbázis közleményadatainak frissítése később történik.'

    def add_arguments(self, parser):
        parser.add_argument('-s', '--sourceid', required=True, help='Forrásazonosító, pl. mtmt2')
        parser.add_argument('-P', '--priority', type=int, default=INPUT_QUEUE_PRIORITY_DEFAULT, help='Feldolgozási prioritás, 0: legmagasabb, 10: legalacsonyabb')
        parser.add_argument('-a', '--author-id', nargs='*', help='author mtmtid - közvetlen author injektálás. Meg lehet adni többet is, pl. --author-id 1 2 3 5')
        parser.add_argument('-p', '--publication-id', nargs='*',help='publication mtmtid - közvetlen publikáció injektálás. Meg lehet adni többet is, pl. --publication-id 1 2 3 5')
        parser.add_argument('-o', '--org', nargs='*',help='szerzőket injektál adatfrissítésre szervezet (ext_authorlist) alapján. 1-4 közötti string adható meg, ezek sorban: org, unit, subunit, subsubunit.')
        parser.add_argument('--expand-authors', action='store_true', help='a megadott szerzők (l. --author-id) közleményeit írja közvetlenül az input queue-ba')


    def handle(self, *args, **options):
        was_error = False

        sourceid = options['sourceid']
        priority = options['priority']
        expand_authors = options['expand_authors']
        authorid = options['author_id']
        pubid = options['publication_id']
        org = options['org']

        # sourceid ellenőrzése
        if sourceid not in getconfig('input_sources').keys():
            logger.error('Ismeretlen forrásazonosító: %s.'%(sourceid))
            was_error = True

        if expand_authors and not authorid:
            logger.warning('Az expand-authors megadásakor meg kell adni szerzők azonosítóját is az author-id paraméterben.')

        if org and (len(org) == 0 or len(org) > 4):
            logger.error('A szervezet megadásakor legalább 1, legfeljebb 4 szint megadása szükséges. Ez érkezett (%s szint): %s.'%(len(org), ' '.join(org)))
            was_error = True

        if priority < 0 or priority > 10:
            logger.error('A prioritás 0 és 10 közé eshet, 0 a legmagasabb, 10 a legalacsonyabb. Ez érkezett: %s.'%(priority))
            was_error = True

        if not was_error:        
            if authorid:
                if expand_authors:
                    logger.info('Az %s forráshoz szerzőazonosító alapján közlemények beírása: %s'%(sourceid, authorid))
                    for a in authorid:
                        input_queue_write_publications_for_author(sourceid, int(a), client_name=MODULE_NAME, priority=priority)
                else:
                    logger.info('Az %s forráshoz szerzőazonosító beírása: %s'%(sourceid, authorid))
                    for a in authorid:
                        input_queue_dbwrite(sourceid, INPUT_QUEUE_TYPE_AUTHOR, int(a), command_source=MODULE_NAME, priority=priority)

            if pubid:
                logger.info('Az %s forráshoz közleményazonosító beírása: %s'%(sourceid, pubid))
                for p in pubid:
                    input_queue_dbwrite(sourceid, INPUT_QUEUE_TYPE_PUBLICATION, int(p), command_source=MODULE_NAME, priority=priority)

            if org:
                logger.info('Az %s forráshoz szerzői névsor alapján adatfrissítés igénylése, szervezeti egység: %s.'%(sourceid, ' '.join(org)))
                al = ExtAuthorlist.get_valid_objects()
                _org_filter_description = None
                # add filters
                if len(org) >= 1:
                    al = al.filter(org=org[0])
                    _org_filter_description = org[0]
                if len(org) >= 2:
                    al = al.filter(unit=org[1])
                    _org_filter_description = '%s/%s'%(_org_filter_description, org[1])
                if len(org) >= 3:
                    al = al.filter(subunit=org[2])
                    _org_filter_description = '%s/%s'%(_org_filter_description, org[2])
                if len(org) >= 4:
                    al = al.filter(subsub_unit=org[3])
                    _org_filter_description = '%s/%s'%(_org_filter_description, org[3])
                al = al.values('mtmtcode').distinct()

                cnt = 0
                _command_source = '%s (org filter: %s)'%(MODULE_NAME, _org_filter_description or 'None')
                for a in al:
                    input_queue_dbwrite(sourceid, INPUT_QUEUE_TYPE_AUTHOR, a['mtmtcode'], command_source=_command_source, priority=priority)
                    cnt += 1

                logger.info('Adatfrissítés előjegyezve %s szerző számára, forrásrendszer: %s, szervezeti egység: %s.'%(cnt, sourceid, ' '.join(org)))

        if was_error:
            logger.error('A feldolgozo hibával ért véget. =========-')
            raise CommandError()
