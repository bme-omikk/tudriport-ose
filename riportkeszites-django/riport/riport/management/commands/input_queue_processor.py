from django.core.management import BaseCommand, CommandError
from django.db import connections
from django.db.utils import InterfaceError
from django.utils import timezone

from common.constants import INPUT_SOURCE_MTMT2
from db.importlib.input_queue import input_queue_write_publications_for_author, update_status
from db.importlib.mtmt import mtmt_stream_processing
from db.sources.mtmt2_parser import mtmt2_parser
from db.sources.mtmt2_parser_utils import mtmt2_parse_pubids
from db.sources.validator import ValidationException
from riport.models.external import InputQueue, Publication, Published
from riport.models.external import INPUT_QUEUE_STATUS_NEW, INPUT_QUEUE_STATUS_PROCESSING, INPUT_QUEUE_STATUS_PROCESSED, INPUT_QUEUE_STATUS_FAILED, INPUT_QUEUE_TYPE_AUTHOR, INPUT_QUEUE_TYPE_PUBLICATION
from tudriport.common.config import getconfig
from tudriport.common.db import dbconnect
from utils.url_tool import mtmt2_http_read

import logging
import sys
import time
import traceback
import urllib

logger = logging.getLogger(__name__)

MODULE_NAME = 'input_queue_processor'

class Command(BaseCommand):
    help='Ez a segédprogram az input_queue alapján frissíti az adatbázist.'

    def add_arguments(self, parser):
        parser.add_argument('-s', '--sourceid', required=True, help='Forrásazonosító, ami alapján dolgozzon, pl. mtmt2')
        parser.add_argument('-a', '--author', action='store_true',  help='A konfigurációban meghatározott számú szerző közleményeit írja elő frissítésre.')
        parser.add_argument('-p', '--publication', action='store_true',  help='A konfigurációban meghatározott számú közleményt tölt le.')
        parser.add_argument('-c', '--continuous', action='store_true', help='Folyamatos üzemben dolgozik az --author illetve --publication paraméterek szerint.')


    def handle(self, *args, **options):
        was_error = False

        sourceid = options['sourceid']
        process_authors = options['author']
        process_publications = options['publication']
        continuous_mode = options['continuous']

        # sourceid ellenőrzése
        if sourceid not in getconfig('input_sources').keys():
            logger.error('Ismeretlen forrásazonosító: %s.'%(sourceid))
            was_error = True

        if process_publications and sourceid != INPUT_SOURCE_MTMT2:
            logger.error('A publikációk feldolgozása (--publication paraméter) csak MTMT2-re implementált, de a kért sourceid %s volt.'%(sourceid))
            was_error = True

        if not (process_authors or process_publications):
            logger.error('Az --author és a --publication paraméter közül legalább az egyiket meg kell adni.')
            was_error = True

        if was_error:
            logger.error('A feldolgozó hibával ért véget. =========-')
            raise CommandError()

        sleep_seconds_per_iteration = getconfig('input_sources.sleep_seconds_per_iteration')
        sleep_seconds_per_operation = getconfig('input_sources.sleep_seconds_per_operation')

        loop_cnt_author = getconfig('input_sources.max_author_processing')
        loop_cnt_publication = getconfig('input_sources.max_publication_processing')

        url_template_publication = getconfig('input_sources.'+sourceid+'.publication')

        db = dbconnect()

        while True:
            try:
                if not db or db.closed:
                    logger.warning('Adatbáziskapcsolat nem elérhető, újracsatlakozási kísérlet.')
                    # re-open non-Django DB connection
                    db = dbconnect()
                    # Note: Django will automatically re-open DB connection upon next use

                if process_authors:
                    for i in range(0, loop_cnt_author):
                        try:
                            el = InputQueue.objects.filter(source=sourceid, type=INPUT_QUEUE_TYPE_AUTHOR, status=INPUT_QUEUE_STATUS_NEW).order_by('priority', 'status_date')[0]
                            update_status(el, INPUT_QUEUE_STATUS_PROCESSING, save=True)

                            try:
                                logger.info('Feldolgozás: InputQueue, forrásrendszer: %s, szerző: %s'%(sourceid, el.identifier))
                                input_queue_write_publications_for_author(sourceid, el.identifier, client_name=MODULE_NAME, priority=el.priority)
                                update_status(el, INPUT_QUEUE_STATUS_PROCESSED, save=True)
                            except urllib.error.HTTPError as e:
                                _msg = 'HTTP %s hiba a %s szerző feldolgozásakor, forrásrendszer: %s.'%(e.code, el.identifier, sourceid)
                                logger.exception(_msg)
                                update_status(el, INPUT_QUEUE_STATUS_FAILED, status_msg=_msg, save=True)
                            except Exception as e:
                                _msg = 'Feldolgozás: hiba történt: %s'%(traceback.format_exception_only(type(e), e))
                                logger.exception(_msg)
                                update_status(el, INPUT_QUEUE_STATUS_FAILED, status_msg=_msg, save=True)

                        except IndexError:
                            # nincs feldolgozásra váró szerző, kilépünk ebből a ciklusból
                            break
                        time.sleep(sleep_seconds_per_operation)

                if process_publications:
                    # Note: csak MTMT2 -re implementált
                    for i in range(0, loop_cnt_publication):
                        try:
                            el = InputQueue.objects.filter(source=sourceid, type=INPUT_QUEUE_TYPE_PUBLICATION, status=INPUT_QUEUE_STATUS_NEW).order_by('priority','status_date')[0]
                            update_status(el, INPUT_QUEUE_STATUS_PROCESSING, save=True)

                            try:
                                logger.info('Feldolgozás: InputQueue, forrásrendszer: %s, közleményazonosító: %s'%(sourceid, el.identifier))
                                url = url_template_publication.replace('@@@', str(el.identifier))
                                
                                # letöltés
                                pub_jsonstring = mtmt2_http_read(url)

                                # közleményazonosító kinyerése
                                pubids_from_source = mtmt2_parse_pubids(pub_jsonstring)

                                if pubids_from_source is None or len(pubids_from_source) == 0 or pubids_from_source[0] != el.identifier:
                                    # Törölt közleményt lezárni
                                    effective_datetime = timezone.now()
                                    try:
                                        o_publication = Publication.get_valid_objects().get(mtmt_pubid=el.identifier)
                                        Published.get_valid_objects().filter(publication=o_publication).update(valid_to=effective_datetime)
                                        o_publication.delete(effective_datetime)
                                        logger.info('Közlemény lezárása: %s, forrásrendszer: %s.'%(el.identifier, sourceid))
                                    except Publication.DoesNotExist:
                                        # ha nem létezik az adatbázisban, nincs mit lezárni
                                        None
                                else:
                                    mtmt_stream_processing(db, pub_jsonstring, doc_filter=None, historyfile_write=False, mtmt_parser=mtmt2_parser, parsetimestamp_in=None, stream_info='sourceid: %s doc id:%s'%(sourceid, el.identifier), trydebug=True)
                                
                                update_status(el, INPUT_QUEUE_STATUS_PROCESSED, save=True)
                            except urllib.error.HTTPError as e:
                                _msg = 'HTTP %s hiba a %s közlemény feldolgozásakor, forrásrendszer: %s.'%(e.code, el.identifier, sourceid)
                                logger.exception(_msg)
                                update_status(el, INPUT_QUEUE_STATUS_FAILED, status_msg=_msg, save=True)
                            except ValidationException as e:
                                # validációs hiba esetén lezárjuk az eredeti közleményt, ha van
                                effective_datetime = timezone.now()
                                try:
                                    o_publication = Publication.get_valid_objects().get(mtmt_pubid=el.identifier)
                                    Published.get_valid_objects().filter(publication=o_publication).update(valid_to=effective_datetime)
                                    o_publication.delete(effective_datetime)
                                    logger.info('Közlemény lezárása: %s, forrásrendszer: %s.'%(el.identifier, sourceid))
                                except Publication.DoesNotExist:
                                    # ha nem létezik az adatbázisban, nincs mit lezárni
                                    None

                                _msg = 'Validációs hiba történt: %s a %s közlemény feldolgozásakor, forrásrendszer: %s.'%(traceback.format_exception_only(type(e), e), el.identifier, sourceid)
                                logger.exception(_msg)
                                update_status(el, INPUT_QUEUE_STATUS_FAILED, status_msg=_msg, save=True)
                            except Exception as e:
                                _msg = 'Feldolgozás: hiba történt: %s'%(traceback.format_exception_only(type(e), e))
                                logger.exception(_msg)
                                update_status(el, INPUT_QUEUE_STATUS_FAILED, status_msg=_msg, save=True)

                        except IndexError:
                            # nincs feldolgozásra váró szerző, kilépünk ebből a ciklusból
                            break
                        time.sleep(sleep_seconds_per_operation)

            except KeyboardInterrupt:
                sys.exit(0)
            except InterfaceError as e:
                if db.closed or str(e) == 'connection already closed':
                    logger.warning('Valamely adatbáziskapcsolat bezáródott, bezárjuk mindet...')
                    # close non-Django DB connection
                    if not db.closed:
                        db.close()
                    # close Django DB connections
                    for conn in connections.all():
                        conn.close_if_unusable_or_obsolete()
                else:
                    logger.error('Hiba történt: %s'%(traceback.format_exception_only(type(e), e)))
            except Exception as e:
                logger.error('Hiba történt: %s'%(traceback.format_exception_only(type(e), e)))
            else:
                # ha folytatódhat tovább a feldolgozás, és folyamatos módban fut a feldolgozó, akkor szünetet tartunk az iterációk között
                if not continuous_mode:
                    break
                time.sleep(sleep_seconds_per_iteration)

