from django.core.management import BaseCommand, CommandError

from common.constants import INPUT_SOURCE_MTMT2
from riport.models.external import InputQueue
from riport.models.external import INPUT_QUEUE_STATUS_NEW, INPUT_QUEUE_TYPE_AUTHOR, INPUT_QUEUE_TYPE_PUBLICATION
from tudriport.common.config import getconfig

import logging
import sys
import traceback

logger = logging.getLogger(__name__)

MODULE_NAME = 'input_queue_processor'

class Command(BaseCommand):
    help='Ez a segédprogram az input_queue -ban feldolgozásra váró tételek számát írja ki "<publikáció> <szerző>" formában..'

    def add_arguments(self, parser):
        parser.add_argument('-s', '--sourceid', required=False, default=INPUT_SOURCE_MTMT2, help='Forrásazonosító, ami alapján dolgozzon, pl. mtmt2')

    def handle(self, *args, **options):
        was_error = False

        sourceid = options['sourceid']

        # sourceid ellenőrzése
        if sourceid not in getconfig('input_sources').keys():
            logger.error('Ismeretlen forrásazonosító: %s.'%(sourceid))
            was_error = True

        if was_error:
            logger.error('A feldolgozó hibával ért véget. =========-')
            raise CommandError()

        try:
            num_publication = InputQueue.objects.filter(source=sourceid, type=INPUT_QUEUE_TYPE_PUBLICATION, status=INPUT_QUEUE_STATUS_NEW).count()
            num_author = InputQueue.objects.filter(source=sourceid, type=INPUT_QUEUE_TYPE_AUTHOR, status=INPUT_QUEUE_STATUS_NEW).count()

            print('%s %s'%(num_publication, num_author))

        except Exception as e:
            logger.error('Hiba történt: %s'%(traceback.format_exception_only(type(e), e)))
            sys.exit(-1)

