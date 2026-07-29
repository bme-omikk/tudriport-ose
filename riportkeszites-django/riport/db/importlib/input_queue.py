from django.core.management import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from common.constants import INPUT_SOURCE_MTMT2, TUDRIPORT_SYSTEM_NAME
from db.sources.mtmt2_parser_utils import mtmt2_parse_pubids
from riport.models.external import INPUT_QUEUE_STATUS_NEW, INPUT_QUEUE_TYPE_PUBLICATION, INPUT_QUEUE_PRIORITY_DEFAULT
from riport.models.external import InputQueue, Published
from tudriport.common.config import getconfig
from utils.url_tool import mtmt2_http_read


import logging

logger = logging.getLogger(__name__)

def input_queue_dbwrite(sourceid, typeid, identifier, command_source=None, priority=INPUT_QUEUE_PRIORITY_DEFAULT):
    payload={
            'source': sourceid,
            'type': typeid,
            'identifier': identifier,
            'priority': priority,
            'status': INPUT_QUEUE_STATUS_NEW,
            'status_date': timezone.now()
          , 'command_count': 1
        }
    try:
        input_queue_element = InputQueue.objects.get(source=sourceid, type=typeid, identifier=identifier, status=INPUT_QUEUE_STATUS_NEW)  
        input_queue_element.command_count += 1
        if priority < input_queue_element.priority:
            input_queue_element.priority = priority
        if command_source:
            input_queue_element.command_source.append(command_source)
        input_queue_element.save()
    except ObjectDoesNotExist:
        obj = InputQueue(**payload)
        if command_source:
            obj.command_source.append(command_source)
        obj.save()

def input_queue_write_publications_for_author(sourceid, author_id, client_name=None, priority=INPUT_QUEUE_PRIORITY_DEFAULT):
    """A szerző azonosítója alapján a közleményeinek azonosítóját írja az input queue-ba."""

    if sourceid == INPUT_SOURCE_MTMT2:
        logger.info('Start: a %s forrásrendszerből szerzői azonosító %s kifejtése közleményazonosítókra.'%(sourceid, author_id))
        pubids_from_source = []
        url = getconfig('input_sources.'+sourceid+'.author').replace('@@@', str(author_id))

        pubids_from_source = mtmt2_parse_pubids(mtmt2_http_read(url))

        pubids_from_db = Published.get_valid_objects().select_related().filter(author_db__mtmt_authid=author_id).values_list('mtmt_pubid', flat=True)

        # a közlemény frissítési parancs forrását megkülönböztetjük: a forrásrendszer adta,
        # vagy a saját adatbázisunkból jött azon felül (a saját adatbázisban még létező, de a forrásrendszerben törölt rekord vagy a szerzőségi kapcsolat szűnt meg a szerzővel)
        _src_external = 'author-expand: %s, expand-from: %s'%(author_id, sourceid)
        _src_mydb = 'author-expand: %s, expand-from: %s'%(author_id, TUDRIPORT_SYSTEM_NAME)
        if client_name:
            _src_external = '%s, client-name: %s'%(_src_external, client_name)
            _src_mydb = '%s, client-name: %s'%(_src_mydb, client_name)

        for p in set(pubids_from_source):
            input_queue_dbwrite(sourceid, INPUT_QUEUE_TYPE_PUBLICATION, p, _src_external, priority)
        for p in set(pubids_from_db).difference(pubids_from_source):
            input_queue_dbwrite(sourceid, INPUT_QUEUE_TYPE_PUBLICATION, p, _src_mydb, priority)
        
        logger.info('Kész: a %s forrásrendszerből szerzői azonosító %s kifejtése közleményazonosítókra. Forrásrendszerből %s, helyi adatbázisból %s, ezek uniója: %s közlemény frissítésre előjegyezve.'%(sourceid, author_id, len(pubids_from_source), len(pubids_from_db), len(set(pubids_from_source).union(pubids_from_db))))

    else:
        raise NotImplementedError('Csak MTMT2-re implementált, de a kért sourceid %s volt.'%(sourceid))

def update_status(element, new_status, status_msg=None, save = False):
    element.status = new_status
    element.status_msg = status_msg
    element.status_date = timezone.now()
    if save:
        element.save()
