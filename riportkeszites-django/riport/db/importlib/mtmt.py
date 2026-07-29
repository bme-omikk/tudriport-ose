from django.utils import timezone

from db.dbwrite import dbwrite
from db.sources.validator import publication_validator, ValidationException
from tudriport.sqlimport.logfunc import writexmlhistory, writejsonhistory, format_pubid_string

import json
import logging
from traceback import format_exception_only


logger = logging.getLogger(__name__)

def mtmt_stream_processing(db, data_str, doc_filter, historyfile_write, mtmt_parser, parsetimestamp_in, stream_info, trydebug):
    if parsetimestamp_in is None:
        datetime = timezone.now()
    else:
        datetime = parsetimestamp_in

    if historyfile_write:
        # FIXME: a data_str lehet MTMT1 XML ill. MTMT2 JSON is, ezért nem writexmlhistory...
        writexmlhistory(db, data_str, str(datetime)) # ha nem adatujraimport, hanem uj xml, akkor LOG allomanyba tesszuk

    try:
        records = mtmt_parser(db, data_str, doc_filter)
    except Exception as e:
        _msg = 'a közlemény parsolása sikertelen. %s'%(format_exception_only(type(e), e))
        logger.exception(_msg)
        if trydebug: raise # látható, hol száll el a kód hibával
        return 1

    if len(records) == 0:
        logger.warning('A feldolgozandó forrásközlemények halmaza üres a stream-ben. Stream info: %s .'%(stream_info))

    recordsnum = 1 # xml lesz a 0000 sorrendi okokból
    error_count = 0
    for publication, authors, citations in records:
        logger.debug("""
Közlemény:
--> publication: %s
--> authors: %s
--> citations: %s
"""%        (
json.dumps(publication, sort_keys=False, indent=4, separators=(',', ': '), ensure_ascii=False)
, json.dumps(authors, sort_keys=False, indent=4, separators=(',', ': '), ensure_ascii=False)
, json.dumps(citations, sort_keys=False, indent=4, separators=(',', ': '), ensure_ascii=False)
        )
        )


        #FIXME: debugging
        #continue

        writejsonhistory(db, publication, authors, citations, str(datetime), recordsnum)
        recordsnum+=1
        err = ['unknown error']
        try:
            err, warn, publication, authors, citations = publication_validator(db, publication, authors, citations)
        except ValidationException as e:
            # FIXME: egyelőre a publication_validator nem dob ValidationException -t.
            _msg = 'a %s közlemény validálása sikertelen. Stream info: %s . %s'%(( ' (docfilter: %s)'%(doc_filter) if doc_filter else ''), stream_info, format_exception_only(type(e), e))
            logger.exception(format_pubid_string(publication)+ _msg)
            if trydebug: raise # látható, hol száll el a kód hibával
        except Exception as e:
            _msg = 'a %s közlemény validálása sikertelen. Stream info: %s . %s'%(( ' (docfilter: %s)'%(doc_filter) if doc_filter else ''), stream_info, format_exception_only(type(e), e))
            logger.exception(format_pubid_string(publication)+ _msg)
            if trydebug: raise ValidationException(_msg) from e # látható, hol száll el a kód hibával

        if len(err) > 0:
            _msg = 'a %s közlemény validálása sikertelen. Stream info: %s . Hibaüzenetek: %s '%(( ' (docfilter: %s)'%(doc_filter) if doc_filter else ''), stream_info, ';'.join(err))
            logger.error(format_pubid_string(publication)+ _msg)
            if trydebug: raise ValidationException('%s %s'%(format_pubid_string(publication), ';'.join(err))) # látható, hol száll el a kód hibával


        if len(err) == 0:
            try:
                dbwrite(db, publication, authors, citations, datetime)
            except Exception as e:
                db.rollback()
                _msg = 'a %s közlemény SQL-be írása sikertelen. Stream info: %s . %s'%(( ' (docfilter: %s)'%(doc_filter) if doc_filter else ''), stream_info, format_exception_only(type(e), e))
                logger.exception(format_pubid_string(publication)+ _msg)
                if trydebug: raise # látható, hol száll el a kód hibával
                error_count += 1
        else:
            _msg = 'Ismeretlen hiba a közlemény feldolgozása során. További információ az előző sorokban. Stream info: %s .'%(stream_info)
            logger.error(format_pubid_string(publication)+ _msg)
            error_count += 1

    if error_count:
        return 1
    else:
        return 0
