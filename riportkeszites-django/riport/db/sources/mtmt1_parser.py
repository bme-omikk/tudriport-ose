'''Ez a modul felel az MTMT-ből lekért xml állományok parsolásáért.
   A normál XML feldolgozási sorrend:
      - parser
      - validator
      - dbwrite
'''
from tudriport.common.config import getconfig
from tudriport.sqlimport.logfunc import format_pubid_string

import xml.etree.ElementTree as ET
import lxml.etree

import logging

logger = logging.getLogger(__name__)

VERBOSE = getconfig('sqlimport.VERBOSE')
XSDPATH = getconfig('sqlimport.XSDPATH')

def mtmt1_parser(db, xmlstring, filter=None):
    """Az fname fájlból beolvassa a közlemény és idézőadatokat. A filter debugoláshoz való csak!

    Ha "filter is not None", akkor egy lista, és csak az abban szereplő azonosítójú
    közleményeket próbálja importálni.
    Az import fájlból az azonosítót a /records/record[./technical_data/filesource/@identifier] helyről nézzük.
    """
    xmlschema = lxml.etree.XMLSchema(lxml.etree.parse(XSDPATH))
    try:
        xmlschema.assertValid(lxml.etree.fromstring(xmlstring))
    except Exception as e:
        logger.exception('XMLerror: %s'%e)
        return []

    root = ET.fromstring(xmlstring)
    records = []
    if filter is not None:
        logger.debug('Közlemény filter a parse során: %s'%(filter))
    for ch in root:
        #print('->',ch.tag, ch.attrib, 'TEXT:', ch.text)
        if ch.tag == 'xsd_version':
            if ch.text != '2.4.':
                logger.error('2.4. -tol eltero xsd verzio')

        if ch.tag == 'record':
            if filter is not None:
                _id = ch.find('technical_data').find('filesource').attrib['identifier']
                if int(_id) not in filter:
                    logger.debug('Filterezés miatt átugrott közlemény a parse során, MTID: %s.'%(_id))
                    continue
            publication = {}
            authors = []
            citations = []
            for c in ch.find('technical_data'):
                if c.tag == 'filesource':
                    publication['mtmt_pubid'] = c.attrib['identifier']
            for c in ch.find('publication/classifications/'):
                if c.tag == 'type':
                    publication['type_id'] = c.attrib['identifier']
                    publication['type'] = c.text
                if c.tag == 'subtype':
                    publication['subtype_id'] = c.attrib['identifier']
                    publication['subtype'] = c.text
                if c.tag == 'character':
                    publication['character_id'] = c.attrib['identifier']
                    publication['character'] = c.text

            issn = ch.find('publication/container/identifiers')
            if issn:
                for c in issn:
                    if c.tag == 'identifier' and 'type' in c.attrib:
                        if c.attrib['type'] == 'issn':
                            publication['issn'] = c.text
                        if c.attrib['type'] == 'eissn':
                            publication['eissn'] = c.text

            position = 1
            for c in ch.find('publication/authors'):
                if c.tag == 'author':
                    author = {'comment': None}
                    author['authortype'] = 'author'
                    for c2 in c:
                        if c2.tag == 'name':
                            if 'first' in c2.attrib:
                                author['name'] = c2.attrib['last'] + ' ' + c2.attrib['first']
                                author['pubname'] = c2.text
                                if 'share' in c2.attrib:
                                    author['share'] = c2.attrib['share']
                        if c2.tag == 'identifiers':
                            for c3 in c2:
                                if c3.attrib['type'] == 'Éles MTMT felület.':
                                    author['mtmt_authid'] = c3.text
                        if c2.tag == 'comment':
                            author['comment'] = c2.text
                    author['position'] = position
                    position += 1
                    authors.append(author)
            position = 1
            for c in ch.find('publication/editors'):
                if c.tag == 'editor':
                    author = {'comment': None}
                    author['authortype'] = 'editor'
                    for c2 in c:
                        if c2.tag == 'name':
                            if 'first' in c2.attrib:
                                author['name'] = c2.attrib['first'] + ' ' + c2.attrib['last']
                                author['pubname'] = c2.text
                                if 'share' in c2.attrib:
                                    author['share'] = c2.attrib['share']
                                author['position'] = position
                                position += 1
                        if c2.tag == 'identifiers':
                            for c3 in c2:
                                if c3.attrib['type'] == 'Éles MTMT felület.':
                                    author['mtmt_authid'] = c3.text
                        if c2.tag == 'comment':
                            author['comment'] = c2.text
                    authors.append(author)

            pub = ch.find('publication/container/impactfactor')
            #print('-'+pub.tag+'-')
            if pub is not None and pub.tag == 'impactfactor':
                publication['impactfactor'] = pub.text

            pub = ch.find('publication/date')
            if pub is not None and pub.tag == 'date' and 'year' in pub.attrib:
                publication['pubdate'] = pub.attrib['year']

            pub = ch.find('publication/language')
            if pub is not None and pub.tag == 'language':
                publication['language'] = pub.text

            pub = ch.find('publication/container')
            if pub:
                for c in pub:
                    if c.tag == 'publisher' and 'publisher-country' in c.attrib:
                        publication['publisher'] = {
                            'country': c.attrib['publisher-country'],
                            'city': None
                        }
                        if 'city' in c.attrib:
                            publication['publisher']['city'] = c.attrib['city'],

            pub = ch.find('publication/container/peerreviewed')
            publication['peerreviewed'] = False
            if pub is not None and pub.tag == 'peerreviewed':
                publication['peerreviewed'] = True

            publication['publishinglocation'] = None
            # (1) Először itt keressük. Lásd: issue#27
            pub = ch.find('publication/published')
            if pub is not None and pub.tag == 'published' and 'country' in pub.attrib:
                publication['publishinglocation'] = {
                    'country': pub.attrib['country'],
                    'city': pub.attrib['city']
                }
            # ha az (1)-ből megvan, már nem keressük
            if publication['publishinglocation'] == None:
                pub = ch.find('publication/container/published')
                if pub is not None and pub.tag == 'published' and 'country' in pub.attrib:
                    publication['publishinglocation'] = {
                        'country': pub.attrib['country'],
                        'city': pub.attrib['city']
                    }
            if publication['publishinglocation'] == None:
                pub = ch.find('publication/published_abroad')
                if pub is not None and pub.tag == 'published_abroad':
                    if pub.text == 'true':
                        publication['publishinglocation'] = {
                            'country': '[ismeretlen külföldi ország]',
                            'city': ''
                        }
                    if pub.text == 'false':
                        publication['publishinglocation'] = {
                            'country': 'Magyarország',
                            'city': ''
                        }
            if publication['publishinglocation'] == None:
                pub = ch.find('publication/container/published_abroad')
                if pub is not None and pub.tag == 'published_abroad':
                    if pub.text == 'true':
                        publication['publishinglocation'] = {
                            'country': '[ismeretlen külföldi ország]',
                            'city': ''
                        }
                    if pub.text == 'false':
                        publication['publishinglocation'] = {
                            'country': 'Magyarország',
                            'city': ''
                        }



            publication['publisherlocation'] = None
            # (1) Először itt keressük. Lásd: issue#27
            pub = ch.find('publication/publisher')
            if pub is not None and pub.tag == 'publisher' and 'country' in pub.attrib:
                publication['publisherlocation'] = {
                    'country': pub.attrib['country'],
                    'city': pub.attrib['city']
                }
                # ha az (1)-ből megvan, már nem keressük
                if publication['publisherlocation'] == None:
                   if pub is not None and pub.tag == 'publisher' and 'publisher-country' in pub.attrib:
                       publication['publisherlocation'] = {
                           'country': pub.attrib['publisher-country'],
                           'city': ''
                       }
            if publication['publisherlocation'] == None:
                pub = ch.find('publication/container/publisher')
                if pub is not None and pub.tag == 'publisher' and 'country' in pub.attrib:
                    publication['publisherlocation'] = {
                        'country': pub.attrib['country'],
                        'city': pub.attrib['city']
                    }
                    # ha az (1)-ből megvan, már nem keressük
                    if publication['publisherlocation'] == None:
                       if pub is not None and pub.tag == 'publisher' and 'publisher-country' in pub.attrib:
                           publication['publisherlocation'] = {
                               'country': pub.attrib['publisher-country'],
                               'city': ''
                           }



            pub = ch.find('publication/length/entry')
            if pub is not None and pub.tag == 'entry':
                if 'page_number' in pub.attrib:
                    publication['page_number'] = pub.attrib['page_number']
                if 'page_from' in pub.attrib:
                    publication['page_from'] = pub.attrib['page_from']
                if 'page_to' in pub.attrib:
                    publication['page_to'] = pub.attrib['page_to']

            pub = ch.find('publication/identifiers/identifier')
            publication['identifier_WoS'] = False
            publication['identifier_Scopus'] = False
            if pub is not None and 'name' in pub.attrib:
                if pub.attrib['name'] == 'WoS' and pub.attrib['identifier']:
                    publication['identifier_WoS'] = True
                if pub.attrib['name'] == 'Scopus' and pub.attrib['identifier']:
                    publication['identifier_Scopus'] = True

            publication['refcount'] = 0
            for c in ch.find('citations'):
                if c.tag == 'citation':
                    cit = {}
                    cit['independent'] = False
                    cit['WoS'] = False
                    cit['Scopus'] = False
                    for c2 in c:
                        if c2.tag == 'date':
                            if 'year' in c2.attrib:
                                cit['date'] = c2.attrib['year']
                            else:
                                cit['date'] = '0'
                        if c2.tag == 'independent':
                            if c2.text == 'true':
                                cit['independent'] = True
                            #else:
                            #    cit['independent'] = False
                        if c2.tag == 'identifiers':
                            for c3 in c2:
                                if c3.tag == 'identifier':
                                    if 'name' in c3.attrib:
                                        if c3.attrib['name'] == 'WoS':
                                            cit['WoS'] = True
                                        if c3.attrib['name'] == 'Scopus':
                                            cit['Scopus'] = True
                                    if 'type' in c3.attrib and c3.attrib['type'] == "Éles MTMT felület.":
                                        cit['mtmt_identifier'] = c3.text

                    citations.append(cit)
                    publication['refcount'] += 1
            records.append([publication, authors, citations])
    logger.debug('Az MTMT1 xmlparsolas sikeresen lefutott.')
    return records
