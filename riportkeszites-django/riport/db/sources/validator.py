'''Ez a modul felel a parsolt adatok adattartalmának ellenőrzéséért.
   A normál XML feldolgozási sorrend:
      - parser
      - validator
      - dbwrite
'''
from tudriport.common.config import getconfig
from tudriport.sqlimport.logfunc import format_pubid_string
from common.constants import CITY_MISSING, CITY_MISSING_HUNGARY_TRANSLATE, COUNTRY_ABROAD_UNKNOWN, COUNTRY_ABROAD_UNKNOWN_TRANSLATE, COUNTRY_HUNGARY, MTA_RANKING_COMMITTEE_LIST

from collections import Counter
import logging
import json

logger = logging.getLogger(__name__)

VALIDATOR_DEBUG = 0
MISSING_DIMENSION_ID = getconfig('sqlimport.MISSING_DIMENSION_ID')


class ValidationException(Exception):
    '''Validációs hiba'''

def publication_validator(db, publication, authors, citations):
    """Egy közleményrekordot validál, a kapcsolódó szerzőség és idéző adatokkal együtt."""
    err = [] # ha üres, mehet az SQL íráshoz, hiva esetén nem
    warn = []

    if not 'pubdate' in publication:
        _msg = 'Nincs pubdate.'
        err.append(_msg)
        logger.error(format_pubid_string(publication)+ _msg)

    # a language kötelező, és kisbetűsen, betűrendbe rendezve, vesszővel és szóközzel elválasztott stringet készítünk
    if 'language' in publication and publication['language']:
        # MTMT2-ből lista érkezik
        if isinstance(publication['language'], list):
            _langlist = publication['language']
        # MTMT1-ből string érkezik, amiben az elválasztó jelek lehetnek "és", "," illetve ";"
        else:
            _langlist = publication['language'].replace(' és ', '#').replace('; ', '#').replace(', ', '#').split('#')

        publication['language'] = ', '.join(sorted([x.strip().lower() for x in _langlist]))
    else:
        _msg = 'Hiányzik a közlemény nyelve.'
        warn.append(_msg)
        logger.warning(format_pubid_string(publication)+ _msg)

    if 'is_foreign_language' not in publication:
        _msg = 'Hiányzik a nyelv besorolása flag: idegen nyelv vagy magyar.'
        warn.append(_msg)
        logger.warning(format_pubid_string(publication)+ _msg)

    if 'type_id' not in publication:
        _msg = 'Nincs type_id (mtid: %s)'%(publication['mtmt_pubid'])
        warn.append(_msg)
        logger.warning(_msg)

    if 'subtype_id' not in publication:
        _msg = 'Nincs subtype_id (mtid: %s, type_id: %s)'%(publication['mtmt_pubid'], publication.get('type_id'))
        warn.append(_msg)
        logger.warning(_msg)

    if 'character_id' not in publication:
        _msg = 'Nincs character_id (mtid: %s, type_id: %s, subtype_id: %s)'%(publication['mtmt_pubid'], publication.get('type_id'), publication.get('subtype_id'))
        warn.append(_msg)
        logger.warning(_msg)

    if 'is_full_scientific' not in publication:
        _msg = 'Nincs teljes tudomanyos megjeloles (mtid: %s, type_id: %s, subtype_id: %s, character_id: %s)'%(publication['mtmt_pubid'], publication.get('type_id'), publication.get('subtype_id'), publication.get('character_id'))
        warn.append(_msg)
        logger.warning(_msg)

    if 'is_published' not in publication:
        _msg = 'Nincs publikalva megjeloles (mtid: %s, type_id: %s, subtype_id: %s, character_id: %s)'%(publication['mtmt_pubid'], publication.get('type_id'), publication.get('subtype_id'), publication.get('character_id'))
        warn.append(_msg)
        logger.warning(_msg)

    if 'is_foreign_publication' not in publication:
        _msg = 'Hiányzik a kiadás hazai/külföldi flag.'
        warn.append(_msg)
        logger.warning(format_pubid_string(publication)+ _msg)

    for k in ['type', 'subtype', 'character']:
        if k in publication:
            publication[k] = publication[k].lower()

    # publishinglocation, publisherlocation: ismeretlen külföldi ország, hiányzó város kezelése
    for loc in ['publisherlocation', 'publishinglocation']:
        if loc in publication and publication[loc] is not None:
            if 'city' not in publication[loc] or publication[loc]['city'] == '' or publication[loc]['city'] is None:
                publication[loc]['city'] = CITY_MISSING

            _country = publication[loc]['country']
            _city = publication[loc]['city']

            if _country == COUNTRY_HUNGARY and _city in CITY_MISSING_HUNGARY_TRANSLATE:
                publication[loc]['city'] = CITY_MISSING
            elif _country in COUNTRY_ABROAD_UNKNOWN_TRANSLATE and _city in COUNTRY_ABROAD_UNKNOWN_TRANSLATE[_country]:
                publication[loc]['country'] = COUNTRY_ABROAD_UNKNOWN
                publication[loc]['city'] = CITY_MISSING

    # Ranking/minőségi mérőszámok
    if not 'impactfactor' in publication:
        publication['impactfactor'] = None

    if not 'sjr_rank' in publication:
        publication['sjr_rank'] = None
        publication['sjr_isestimate'] = None
        publication['sjr_value'] = None

    # MTA folyóiratranking: a legjobb érték ill. a feldolgozott bizottságok specifikus értékei
    for _field_name in ['mta_rank', 'mta_rank_full']:
        if _field_name not in publication:
            publication[_field_name] = None
    for _code in MTA_RANKING_COMMITTEE_LIST:
        _field_name_short = 'mta_%s_rank' % (_code.lower())
        _field_name_full  = 'mta_%s_rank_full' % (_code.lower())
        if _field_name_short not in publication:
            publication[_field_name_short] = None
            publication[_field_name_full] = None

    if 'mta_listed_zero' not in publication:
        publication['mta_listed_zero'] = False

    # authors ...
    publication['authorcount']=0
    publication['editorcount']=0
    if len(authors) == 0:
        _msg = 'Nincs szerzoje.'
        err.append(_msg)
        logger.error(format_pubid_string(publication)+ _msg)
    else:
        var_authfirst = True
        var_authlast = -1
        var_editfirst = True
        var_editlast = -1

        for authct in range(len(authors)):
            if 'affiliations' not in authors[authct]:
                authors[authct]['affiliations'] = []

            if authors[authct]['authortype'] == 'author':
                publication['authorcount'] += 1
                authors[authct]['isfirst'] = var_authfirst # első true
                authors[authct]['islast'] = False
                var_authfirst = False
                var_authlast = authct
            elif authors[authct]['authortype'] == 'editor':
                publication['editorcount'] += 1
                authors[authct]['isfirst'] = var_editfirst    # első true
                authors[authct]['islast'] = False
                var_editfirst = False
                var_editlast = authct

        if var_authlast >= 0:
            authors[var_authlast]['islast'] = True
        if var_editlast >= 0:
            authors[var_editlast]['islast'] = True

        # count duplicate author/editor entries.
        author_counter = {}

        for auth in authors[:]:   # a benti remove miatt [:]:
            if 'mtmt_authid' not in auth:
                authors.remove(auth)
            else:
                if auth['authortype'] not in author_counter:
                    author_counter[ auth['authortype'] ] = []
                author_counter[ auth['authortype'] ].append( auth['mtmt_authid'] )

                if 'share' not in auth:
                    _msg = 'Share parameter nem szerepel valamelyik szerzonel: %s.'%(auth['mtmt_authorid'])
                    warn.append(_msg)
                    logger.warning(format_pubid_string(publication)+ _msg)
                    auth['share'] = None

        duplicate_author_err_msg = []
        for at in ['author', 'editor']:
            if at in author_counter:
                dups = [ str(k) for k,v in Counter( author_counter[at] ).items() if v>1 ]
                if len(dups):
                    duplicate_author_err_msg.append( 'duplum a(z) %s szerepben: %s'%(at, ', '.join(dups)) )
        if len(duplicate_author_err_msg):
            _msg = 'Többszörös szerzőhozzárendelés az MTMT-ben: %s.'%( '; '.join(duplicate_author_err_msg) )
            err.append(_msg)
            logger.error(format_pubid_string(publication)+ _msg)

    # authors vége

    if 'page_number' not in publication:
        if 'page_from' in publication and 'page_to' in publication:
            if publication['page_from'].isdigit() and publication['page_to'].isdigit():
                publication['page_number'] = int(publication['page_to']) - int(publication['page_from']) + 1
            else:
                #print('!!!! pubid: %s -- nem arab számot tartalmaz a page_from (%s) page_to (%s) mezőkben'%(publication['mtmt_pubid'], publication['page_from'], publication['page_to']))
                _msg = 'Nem arab számot tartalmaz a page_from (%s) page_to (%s) mezőkben.'%(publication['page_from'], publication['page_to'])
                warn.append(_msg)
                logger.warning(format_pubid_string(publication)+ _msg)
                publication['page_number'] = None
        else:
            _msg = 'Se page_number, se page_from és page_to nincs.'
            warn.append(_msg)
            logger.warning(format_pubid_string(publication)+ _msg)
            publication['page_number'] = None

    # kulonbozo link-informaciok ellenorzese
    for k in ['has_doi', 'has_isbn', 'has_issn', 'has_full_document_url', 'has_oa_link']:
        if k not in publication:
            publication[k] = False

    # GPK PhD extra mezo ellenorzese
    if 'bme_gpk_phd_description' not in publication:
        publication['bme_gpk_phd_description'] = None

    # publication description adatok ellenorzese
    for k in ['pubdesc_label_txt', 'pubdesc_label_html']:
        if k not in publication:
            publication[k] = '[%s], metadata unavailable for publication'%(publication['mtmt_pubid'])
            logger.debug(format_pubid_string(publication)+ 'Hiányzó közleményleíró mező: %s.'%(k))

    # idéződuplum-keresés DOI ismétlődések alapján
    publication['citation_duplicate_DOI_info'] = []
    if 'citation_DOI_info' not in publication:
        publication['citation_DOI_info'] = {}
    for (k, v) in publication['citation_DOI_info'].items():
        if 'citingDocList' in v and len(v['citingDocList']) > 1:
            v['doi'] = k
            publication['citation_duplicate_DOI_info'].append(v)
    publication['has_citation_duplicate_DOI'] = len(publication['citation_duplicate_DOI_info']) > 0

    # idéződuplum-keresés az idéző közlemény cím ismétlődések alapján
    publication['citation_duplicate_title_info'] = []
    if 'citation_title_info' not in publication:
        publication['citation_title_info'] = {}
    for (k, v) in publication['citation_title_info'].items():
        if 'citingDocList' in v and len(v['citingDocList']) > 1:
            v['title'] = k
            publication['citation_duplicate_title_info'].append(v)
    publication['has_citation_duplicate_title'] = len(publication['citation_duplicate_title_info']) > 0

    # idézőkapcsolat listák (tipikusan hibalisták)
    for k in [
        'not_published', # nem nyilvános idézőkapcsolatok
        'citingdoc_not_published', # nyilvános idézőkapcsolatok nem nyilvános idéző közleménnyel
        'citingdoc_w_error', # nyilvános idézőkapcsolatok hibás/hiányos idéző közleménnyel
        'unknown_external', # nyilvános idézőkapcsolatok jelöletlen függő/független státusszal
        ]:
        _key_list = 'citation_list_' + k
        _key_flag = 'has_citation_' + k

        if _key_list not in publication:
            publication[_key_list] = []
        else:
            publication[_key_list] = sorted(publication[_key_list])
        publication[_key_flag] = len(publication[_key_list]) > 0

    if VALIDATOR_DEBUG:
        logger.info("""
VALIDÁLT közlemény:
--> publication: %s
--> authors: %s
--> citations: %s
"""%        (
    json.dumps(publication, sort_keys=False, indent=4, separators=(',', ': '), ensure_ascii=False)
  , json.dumps(authors, sort_keys=False, indent=4, separators=(',', ': '), ensure_ascii=False)
  , json.dumps(citations, sort_keys=False, indent=4, separators=(',', ': '), ensure_ascii=False)
            )
        )

    return err, warn, publication, authors, citations
