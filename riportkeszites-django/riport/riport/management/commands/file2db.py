from django.core.management import BaseCommand, CommandError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from db.importlib.mtmt import mtmt_stream_processing
from db.sources.mtmt1_parser import mtmt1_parser
from db.sources.mtmt2_parser import mtmt2_parser
from db.sources.validator import publication_validator
from db.dbwrite import dbwrite
from tudriport.common.db import dbconnect

import gzip
import logging
import json
import lzma
import os
from traceback import format_exception_only

# különböző input fájl típusok konstansai
FILETYPE_M1 = 'MTMT1 XML'
FILETYPE_M2 = 'MTMT2 JSON'
FILETYPE_TR = 'Tudriport JSON'

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'MTMT1, MTMT2, vagy saját JSON fájlból közleményeket és idézőik adatait betöltő utility.'

    def add_arguments(self, parser):
        parser.add_argument('-M1', '--m1xmlfile', nargs='*', help='MTMT1 rekordok beolvasása: melyik fájlból vegyük az XML inputot?')
        parser.add_argument('--m1xmldir', help='MTMT1 rekordok beolvasása: melyik mappából vegyük az XML inputot?')
        parser.add_argument('-M2', '--m2jsonfile', nargs='*', help='MTMT2 rekordok beolvasása: melyik fájlból vegyük a JSON inputot?')
        parser.add_argument('--m2jsondir', help='MTMT2 rekordok beolvasása: melyik mappából vegyük a JSON inputot?')
        parser.add_argument('-J', '--jsonfile', nargs='*', help='Tudriport JSON beolvasása: melyik fájlból vegyük a JSON inputot?')
        parser.add_argument('--jsondir', help='Tudriport JSON beolvasása: melyik mappából vegyük a JSON inputot?')
        parser.add_argument('--docfilter', nargs='*', help='Teszteléshez: közleményazonosító, akárhány azonosítót meg lehet adni, pl. --docfilter 1 3 5 7. Csak ezeket tölti be a fájlból..')
        parser.add_argument('-t', '--parsetimestamp', help='Milyen időbélyeggel történjen az import? Formátuma: YYYY-MM-DD HH24:MI:SS')
        parser.add_argument('-T', '--filetimestamp', action='store_true', help='A filenév alapján határozza meg az időbélyeget.')
        parser.add_argument('--trydebug', action='store_true', help='Debugoláshoz. Normál esetben ne használd.')


    def open_and_decompress_file(self, filename, expected_extension):
        """Megnyit egy tömörítetlen, vagy gzip ill. xz tömörítésű fájlt."""
        f = None
        ext = filename.split('.')[-1]
        if ext == expected_extension:
            f = open(filename, 'rb')
        elif ext == 'gz':
            f = gzip.open(filename, 'rb')
        elif ext == 'xz':
            f = lzma.open(filename, 'rb')
        
        return f


    def jsonfile_input(self, db, jsonfile, parsetimestamp_in) -> bool:
        if parsetimestamp_in is None:
            datetime = timezone.now()
        else:
            datetime = parse_datetime(parsetimestamp_in)
            
        logger.info('a %s fájl feldolgozása megkezdődött.'%(jsonfile))

        f = self.open_and_decompress_file(jsonfile, 'json')
        jsonstring = f.read().decode('utf-8')
        f.close()
        jsondata = json.loads(jsonstring)

        err = ['unknown error']
        try:
            err, warn, publication, authors, citations = publication_validator(db, jsondata['publication'], jsondata['authors'], jsondata['citations'])
        except Exception as e:
            _msg = 'a %s közlemény validálása sikertelen. %s'%(jsonfname, format_exception_only(type(e), e))
            logger.exception(_msg)
            if self.TRYDEBUG: raise # látható, hol száll el a kód hibával
            return 1

        if len(err) == 0:
            dbwrite(db, publication, authors, citations, datetime)
        else:
            return 1

        return 0



    def m1_xmlfile_input(self, db, fname, doc_filter, parsetimestamp_in) -> bool:
        logger.info('a %s fájl feldolgozása megkezdődött.'%(fname))

        f = self.open_and_decompress_file(fname, 'xml')
        xmlstring = f.read()
        f.close()

        datetime = None

        if parsetimestamp_in is None:
            historyfile_write = True
        else:
            logger.info('a közlemény (%s.xml) nem lett az xmlhistory-ba másolva, mert időbélyeges.'%(str(parsetimestamp_in)))
            historyfile_write = False

        return mtmt_stream_processing(db, xmlstring, doc_filter, historyfile_write, mtmt1_parser, parsetimestamp_in, fname, self.TRYDEBUG)


    def m2_jsonfile_input(self, db, fname, doc_filter, parsetimestamp_in) -> bool:
        logger.info('a %s fájl feldolgozása megkezdődött.'%(fname))

        f = self.open_and_decompress_file(fname, 'json')
        jsonstring = f.read().decode('utf-8')
        f.close()

        if parsetimestamp_in is None:
            #FIXME: ez True legyen, es akkor a writexmlhistory ellenorizendo
            historyfile_write = False
        else:
            logger.info('a közlemény (%s.json) nem lett az xmlhistory-ba másolva, mert időbélyeges.'%(str(parsetimestamp_in)))
            historyfile_write = False

        return mtmt_stream_processing(db, jsonstring, doc_filter, historyfile_write, mtmt2_parser, parsetimestamp_in, fname, self.TRYDEBUG)


    def handle(self, *args, **options):        
        db = dbconnect()
        logger.debug('A feldolgozo elindult. -=========')

        sumerror = 0
        docfilter = None
        filename_list = []
        filetype = set()
        parsetimestamp = None

        self.TRYDEBUG = options['trydebug']

        if options['docfilter']:
            docfilter = [int(i) for i in options['docfilter']]

        if options['m1xmldir']:
            filetype.add(FILETYPE_M1)
            for root, dirs, files in os.walk(options['m1xmldir']):
                for fn in sorted(files):
                    if fn.find('.xml') >= 0:
                        filename_list.append(os.path.join(root, fn))

        if options['m1xmlfile']:
            filetype.add(FILETYPE_M1)
            filename_list += options['m1xmlfile']

        if options['m2jsondir']:
            filetype.add(FILETYPE_M2)
            for root, dirs, files in os.walk(options['m2jsondir']):
                for fn in sorted(files):
                    if fn.find('.json') >= 0:
                        filename_list.append(os.path.join(root, fn))

        if options['m2jsonfile']:
            filetype.add(FILETYPE_M2)
            filename_list += options['m2jsonfile']

        if options['jsondir']:
            filetype.add(FILETYPE_TR)
            for root, dirs, files in os.walk(options['jsondir']):
                for fn in sorted(files):
                    if fn.find('.json') >= 0:
                        filename_list.append(os.path.join(root, fn))

        if options['jsonfile']:
            filetype.add(FILETYPE_TR)
            filename_list += options['jsonfile']

        if options['parsetimestamp'] and options['filetimestamp']:
            logger.error('-t <időbélyeg> vagy -T, de csak az egyik!')
            sumerror = 1

        if options['parsetimestamp']:
            parsetimestamp = parse_datetime(options['parsetimestamp']), 


        if not filename_list:
            logger.error('MTMT1, MTMT2 vagy Tudriport input fájl vagy azokat tartalmazó könyvtár megadása kell. Lásd --help')
            sumerror = 1

        if len(filetype) > 1:
            logger.error('Egyféle input fáj kell, de a következőket kaptam: {0}'.format(','.join(filetype)))
            sumerror = 1

        # több file feldolgozása
        if not sumerror:
            for filename in filename_list:
                error = 0
                fname = os.path.basename(filename)

                if options['filetimestamp']:
                    parsetimestamp = parse_datetime(fname.split('.')[0])
                    if parsetimestamp is None:
                        logger.error('Hibas idő állománynévben')
                        error = 1

                if parsetimestamp is None and fname[0:4].isdigit() and fname[4] == '-':
                    logger.error('Időt tartalmazó fájlt időértelmezés nélküli importálása - feldolgozás megtagadva.')
                    error = 1

                if error == 0:
                    # már ellenőriztük, hogy egyféle fájltípust kaptunk. Most nézzük, milyet!
                    if FILETYPE_TR in filetype:
                        error = self.jsonfile_input(db, filename, parsetimestamp)
                    elif FILETYPE_M1 in filetype:
                        error = self.m1_xmlfile_input(db, filename, docfilter, parsetimestamp)
                    elif FILETYPE_M2 in filetype:
                        error = self.m2_jsonfile_input(db, filename, docfilter, parsetimestamp)
                sumerror |= error

            if sumerror:
                logger.error('A feldolgozo hibás paraméterek miatt sikertelenül véget ért. =========-')
            else:
                logger.debug('A feldolgozo sikeresen befejezodott. =========-')
            db.close()
            if sumerror > 0:
                raise CommandError(sumerror)

