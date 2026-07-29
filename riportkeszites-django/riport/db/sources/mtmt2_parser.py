'''Ez a modul felel az MTMT2-ből lekért JSON állományok parsolásáért.
   A normál MTMT rekord feldolgozási sorrend:
      - parser
      - validator
      - dbwrite
'''
from tudriport.common.config import getconfig
from tudriport.sqlimport.logfunc import format_pubid_string
from common.constants import M2_OTYPE_CITY, M2_OTYPE_COUNTRY, M2_OTYPE_INSTITUTE, M2_OTYPE_INSTITUTE_CONTAINMENT, M2_OTYPE_MTA_JOURNAL_RATING
from common.constants import COUNTRY_HUNGARY, COUNTRY_ABROAD_UNKNOWN
from common.constants import SOURCENAME_WOS, SOURCENAME_SCOPUS, SOURCENAME_DOI, SOURCENAME_ISBN, SOURCENAME_FULL_DOC_URL, SOURCENAME_OTHER_URL
from common.constants import MTA_RANKING_COMMITTEE_LIST, M2_AFFILIATED_INSTITUTES
from common.constants import EXTRA_BME_GPK_PHD_PREFIX
from common.enum3 import to_enum3, ENUM3_NA
from db.sources.bme_gpk_phd_description_parser import parse_bme_gpk_phd_description
from db.sources.mtmt2_parser_utils import mtmt2_is_journal_mtaListed

from collections import deque
import logging
import json

logger = logging.getLogger(__name__)

def mtmt2_parser(db, jsonstring, filter=None):
    """A jsonstring string-paraméterből beolvassa a közlemény és idézőadatokat. A filter debugoláshoz való csak!

    Ha "filter is not None", akkor egy lista, és csak az abban szereplő azonosítójú
    közleményeket próbálja importálni.
    Az import fájlból az azonosítót a /records/record[./technical_data/filesource/@identifier] helyről nézzük.
    """
    root = json.loads(jsonstring)
    records = []
    if filter is not None:
        logger.debug('Közlemény filter a parse során: %s'%(filter))
    for c in root['content']:
        #print('->',ch.tag, ch.attrib, 'TEXT:', ch.text)

        if filter is not None:
            _id = c['mtid']
            if _id not in filter:
                logger.debug('Filterezés miatt átugrott közlemény a parse során, MTID: %s.'%(_id))
                continue
        publication = {}
        authors = []
        citations = []

        publication['mtmt_pubid'] = c['mtid']

        if 'type' in c:
            publication['type_id'] = c['type']['mtid']
            publication['type'] = c['type']['name']
        if 'subType' in c:
            publication['subtype_id'] = c['subType']['mtid']
            publication['subtype'] = c['subType']['name']
        if 'category' in c:
            publication['character_id'] = c['category']['mtid']
            publication['character'] = c['category']['name']

        if 'fullPublication' in c:
            publication['is_full_scientific'] = c['fullPublication']
        if 'publicationPending' in c:
            publication['is_published'] = not c['publicationPending']

        publication['has_issn'] = False
        if 'journal' in c:
            j = c['journal']
            if 'pIssn' in j:
                publication['issn'] = j.get('pIssn')
                publication['has_issn'] = True
            if 'eIssn' in j:
                publication['eissn'] = j.get('eIssn')
                publication['has_issn'] = True

        if not publication['has_issn']:
            if 'book' in c and 'seriesMembers' in c['book']:
                for _member in  c['book']['seriesMembers']:
                    if 'series' in _member and 'issns' in _member['series']:
                        for _issn in _member['series']['issns']:
                            if _issn.get('issn'):
                                publication['has_issn'] = True

        author_cnt = 0
        editor_cnt = 0
        # Előfordulhat, hogy nincs megadva szerzőség, pl. befoglaló könyv esetén.
        # Az ilyet is kell, hogy kezelje a parser (pl. közleményazonosító alapján kért adatffrissítés vagy korábbi betöltött rekord frissítésekor kerülhet sorra.)
        for a in c.get('authorships', []):
            author = {'comment': None}
            # AuthorshipType/mtid=1 is author
            if a['type']['otype'] == 'AuthorshipType' and a['type']['mtid'] == 1:
                author_cnt += 1
                author['authortype'] = 'author'
                author['position'] = author_cnt
            # AuthorshipType/mtid=2 is editor
            elif a['type']['otype'] == 'AuthorshipType' and a['type']['mtid'] == 2:
                editor_cnt += 1
                author['authortype'] = 'editor'
                author['position'] = editor_cnt
            else:
                # az esetleges egyéb szerzőséget átugorjuk
                continue

            # MTMT-ben azonosított szerző
            if 'author' in a:
                author['name'] = a['author']['familyName'] + ' ' + a['author']['givenName']
                author['comment'] = a['author'].get('auxName')
                author['mtmt_authid'] = a['author']['mtid']
                # keressük az affiliációit egy BFS bejárással a szülők között
                if 'organizations' in a:
                    # halmazként a kezelt affiliációk közül az ennél a szerzőnél megadottak
                    _author_affiliations = set()
                    _affiliations_fifo = deque(a['organizations'])

                    while _affiliations_fifo:
                        _i = _affiliations_fifo.popleft()
                        if _i['otype'] == M2_OTYPE_INSTITUTE:
                            if _i['mtid'] in M2_AFFILIATED_INSTITUTES:
                                _author_affiliations.add(M2_AFFILIATED_INSTITUTES[_i['mtid']])
                            if 'parent' in _i:
                                for p in _i['parent']:
                                    _affiliations_fifo.append(p)
                        elif _i['otype'] == M2_OTYPE_INSTITUTE_CONTAINMENT and 'parent' in _i:
                            _affiliations_fifo.append(_i['parent'])

                    author['affiliations'] = list(_author_affiliations)

            if a['otype'] == 'PersonAuthorship':
                author['pubname'] = a['fullName']
            else:
                # pl. OrgAuthorship
                author['pubname'] = a['label']
            author['share'] = a['share']

            authors.append(author)
            
        # pub = ch.find('publication/container/impactfactor')
        # #print('-'+pub.tag+'-')
        # if pub is not None and pub.tag == 'impactfactor':
        #     publication['impactfactor'] = pub.text

        if 'publishedYear' in c:
            publication['pubdate'] = c['publishedYear']


        if 'foreignLanguage' in c:
            publication['is_foreign_language'] = c['foreignLanguage']
        publication['language'] = []
        for l in c.get('languages', []):
            publication['language'].append(l['name'])


        if 'journal' in c:
            publication['peerreviewed'] = c['journal'].get('reviewType') == 'REVIEWED'
        else:
            publication['peerreviewed'] = False


        # Kiadás helye
        if 'foreignEdition' in c:
            publication['is_foreign_publication'] = c['foreignEdition']
        # publishinglocation kinyerése, Lásd: issue#27
        # Kiadás helyét tartalmazó elem megkeresése
        if 'publishedAt' in c:
            publishinglocationParent = c
        elif 'book' in c:
            publishinglocationParent = c['book']
        else:
            publishinglocationParent = {}

        if 'publishedAt' in publishinglocationParent and len(publishinglocationParent['publishedAt']) > 0:
            if len(publishinglocationParent['publishedAt']) > 1:
                logger.warning(format_pubid_string(publication)+'Több, mint 1 kiadási hely, csak az elsőt dolgoztuk fel az összesen %d bejegyzés közül.' % (len(publishinglocationParent['publishedAt'])))

            publishedAt = publishinglocationParent['publishedAt'][0]
            # continue here
            if publishedAt['otype'] == M2_OTYPE_CITY:
                publication['publishinglocation'] = {
                    'country': publishedAt['partOf']['label'],
                    'city': publishedAt['label'].split(',')[0]
                }
            elif publishedAt['otype'] == M2_OTYPE_COUNTRY:
                publication['publishinglocation'] = {
                    'country': publishedAt['label'],
                    'city': ''
                }
            else:
                logger.warning(format_pubid_string(publication)+'Ismeretlen otype a publishedAt bejegyzésnél: %s'%(publishedAt['otype']))
        else:
            if 'foreignEdition' in c:
                if c['foreignEdition']:
                    publication['publishinglocation'] = {
                         'country': COUNTRY_ABROAD_UNKNOWN,
                         'city': ''
                    }
                else:
                    publication['publishinglocation'] = {
                         'country': COUNTRY_HUNGARY,
                         'city': ''
                    }
        # End: kiadás helye

        # Kiadó székhelye (publisherlocation) kinyerése, Lásd: issue#27
        # Kiadót tartalmazó elem megkeresése
        if 'publishers' in c:
            publishersParent = c
        elif 'journal' in c:
            publishersParent = c['journal']
        elif 'book' in c:
            publishersParent = c['book']
        else:
            publishersParent = {}

        if 'publishers' in publishersParent and len(publishersParent['publishers']) > 0:
            if len(publishersParent['publishers']) > 1:
                logger.warning(format_pubid_string(publication)+'Több, mint 1 publisher, csak az elsőt dolgoztuk fel az összesen %d bejegyzés közül.' % (len(publishersParent['publishers'])))

            publisher = publishersParent['publishers'][0]

            if 'cities' in publisher and len(publisher['cities']) > 0:
                if len(publisher['cities']) > 1:
                    logger.warning(format_pubid_string(publication)+ 'Több, mint 1 city, csak az elsőt dolgoztuk fel az összesen %d bejegyzés közül.' % (len(publisher['cities'])))
                for city in publisher['cities']:
                    if 'partOf' in city and city['partOf']['otype'] == M2_OTYPE_COUNTRY:
                        publication['publisherlocation'] = {
                            'country': city['partOf']['label'],
                            'city': city['name']
                        }
            else:
                # ha van "csak ország" típusú hely, akkor azt kezelni kell ebben az else ágban
                logger.warning(format_pubid_string(publication)+ 'Hiányzik a város bejegyzés a kiadónál. FIXME: lehet, hogy van csak ország típusú hely?.')
        # End: Kiadó székhelye

        if 'pageLength' in c:
            publication['page_number'] = c['pageLength']

        publication['identifier_WoS'] = False
        publication['identifier_Scopus'] = False
        publication['has_doi'] = False
        publication['has_isbn'] = False
        publication['has_full_document_url'] = False
        publication['has_oa_link'] = False
        _bme_gpk_phd_description_raw = None
        _bme_gpk_phd_description_raw_timestamp = None
        for _id in c.get('identifiers', []):
            if _id['source']['name'] == SOURCENAME_WOS and 'idValue' in _id:
                publication['identifier_WoS'] = True
            if _id['source']['name'] == SOURCENAME_SCOPUS and 'idValue' in _id:
                publication['identifier_Scopus'] = True
            if _id['source']['name'] == SOURCENAME_DOI and 'idValue' in _id:
                publication['has_doi'] = True
            if _id['source']['name'] == SOURCENAME_ISBN and 'idValue' in _id:
                publication['has_isbn'] = True
            if _id['source']['name'] == SOURCENAME_FULL_DOC_URL and 'idValue' in _id:
                publication['has_full_document_url'] = True
            if _id['source']['name'] == SOURCENAME_OTHER_URL and 'idValue' in _id and _id['idValue'].startswith(EXTRA_BME_GPK_PHD_PREFIX):
                if _bme_gpk_phd_description_raw is None or ('lastModified' in _id and _id['lastModified'] > _bme_gpk_phd_description_raw_timestamp):
                    _bme_gpk_phd_description_raw = _id['idValue'][len(EXTRA_BME_GPK_PHD_PREFIX):]
                    _bme_gpk_phd_description_raw_timestamp = _id['lastModified']
            if 'oaFree' in _id and _id['oaFree']:
                publication['has_oa_link'] = True

        # Parse the BME GPK PhD URL.
        # If there were no BME GPK PhD URL (_bme_gpk_phd_description_raw is None), then data will be based on publication data in c.
        publication['bme_gpk_phd_description'] = parse_bme_gpk_phd_description( _bme_gpk_phd_description_raw, c )

        if publication['bme_gpk_phd_description']['warning']:
            logger.warning(format_pubid_string(publication) + ' '.join(publication['bme_gpk_phd_description']['warning']))

        # if the document didn't have ISBN, look for that in the book container
        if not publication['has_isbn'] and 'book' in c:
            for _id in c['book'].get('identifiers', []):
                if _id['source']['name'] == SOURCENAME_ISBN and 'idValue' in _id:
                    publication['has_isbn'] = True

        publication['mta_listed_zero'] = False
        _best_mta_rank_full = None
        if 'ratings' in c:
            publication['mta_listed_zero'] = mtmt2_is_journal_mtaListed(c['ratings'], publication.get('pubdate'))
            for r in c['ratings']:
                # az első SJR rangot dolgozzuk fel, mert az a legjobb
                if r['otype'] == 'SjrRating' and 'sjr_rank' not in publication:
                    publication['sjr_rank'] = r['ranking']
                    publication['sjr_isestimate'] = r['calculation'] != 'DIRECT'
                    publication['sjr_value'] = r['rankValue']
                if r['otype'] == M2_OTYPE_MTA_JOURNAL_RATING and 'ratingType' in r and 'code' in r['ratingType']:
                    _code = r['ratingType']['code']
                    if _best_mta_rank_full is None or r['val'] < _best_mta_rank_full:
                        _best_mta_rank_full = r['val']
                    if _code in MTA_RANKING_COMMITTEE_LIST:
                        _field_name_short = 'mta_%s_rank' % (_code.lower())
                        _field_name_full  = 'mta_%s_rank_full' % (_code.lower())
                        publication[_field_name_short] = r['val'][0]
                        publication[_field_name_full] = r['val']
        if _best_mta_rank_full is not None:
            publication['mta_rank'] = _best_mta_rank_full[0]
            publication['mta_rank_full'] = _best_mta_rank_full

        if 'label' in c:
            publication['pubdesc_label_txt'] = c['label']
        if 'template' in c:
            publication['pubdesc_label_html'] = c['template']

        publication['refcount'] = 0
        publication['citation_DOI_info'] = {}
        publication['citation_title_info'] = {}
        publication['citation_list_not_published'] = []
        publication['citation_list_citingdoc_not_published'] = []
        publication['citation_list_citingdoc_w_error'] = []
        publication['citation_list_unknown_external'] = []
        for _c in c.get('citations', []):
            # Csak a nem törölt idézőkapcsolatokat dolgozzuk fel.
            #
            # A közlemény idézettségi számaiba csak a 'nem törölt és nyilvános' idézők kerülnek beszámításra,
            # de minden 'nem törölt' idézőkapcsolat részt vesz a 'citation_*_info' mezők képzésében,
            # amiből az adminisztrátor számára hibalista készül.
            if not _c['deleted']:
                cit = {}
                cit['independent'] = False
                cit['WoS'] = False
                cit['Scopus'] = False

                # ez az Idézőkapcsolat azonosítója, nem pedig az idéző közlemény azonosítója
                cit['mtmt_identifier'] = _c['mtid']

                cit_doc = _c['related']
                cit['date'] = cit_doc.get('publishedYear', '0')
                if _c['externalCitation']:
                    cit['independent'] = True

                for _id in cit_doc.get('identifiers', []):
                    if _id['source']['name'] == SOURCENAME_WOS and 'idValue' in _id:
                        cit['WoS'] = True
                    if _id['source']['name'] == SOURCENAME_SCOPUS and 'idValue' in _id:
                        cit['Scopus'] = True

                    # összegyűjtjük a DOI-kat azért, hogy támogassuk az idézőkapcsolat és idéző közlemény duplumok keresését DOI alapján
                    if _id['source']['name'] == SOURCENAME_DOI and 'idValue' in _id:
                        _doi = _id['idValue']
                        if _doi not in publication['citation_DOI_info']:
                            publication['citation_DOI_info'][_doi] = {}
                            publication['citation_DOI_info'][_doi]['citingDocYear'] = cit['date']
                            publication['citation_DOI_info'][_doi]['citingDocList'] = []
                            publication['citation_DOI_info'][_doi]['citationList'] = []
                        publication['citation_DOI_info'][_doi]['citingDocList'].append(_c['relatedMtid'])
                        publication['citation_DOI_info'][_doi]['citationList'].append(_c['mtid'])

                # összegyűjtjük a DOI-kat azért, hogy támogassuk az idézőkapcsolat és idéző közlemény duplumok keresését DOI alapján
                if 'title' in cit_doc:
                    _title = cit_doc['title']
                    if _title not in publication['citation_title_info']:
                        publication['citation_title_info'][_title] = {}
                        publication['citation_title_info'][_title]['citingDocList'] = []
                        publication['citation_title_info'][_title]['citationList'] = []
                    publication['citation_title_info'][_title]['citingDocList'].append(_c['relatedMtid'])
                    publication['citation_title_info'][_title]['citationList'].append(_c['mtid'])

                # A közlemény idézettségi számaiba csak a 'nem törölt és nyilvános' idézők kerülnek beszámításra
                if _c['published']:
                    citations.append(cit)
                    publication['refcount'] += 1

                    # hibalisták
                    if not cit_doc['published']:
                        publication['citation_list_citingdoc_not_published'].append(_c['mtid'])
                    if 'error' in cit_doc and cit_doc['error']:
                        publication['citation_list_citingdoc_w_error'].append(_c['mtid'])
                    if _c['externalCitation'] is None:
                        publication['citation_list_unknown_external'].append(_c['mtid'])
                else:
                    publication['citation_list_not_published'].append(_c['mtid'])

        records.append([publication, authors, citations])
    logger.debug('Az MTMT2 json parsolas sikeresen lefutott.')
    return records

