from tudriport.common.config import getconfig
from common.constants import INPUT_SOURCE_MTMT2
from db.sources.mtmt2_parser_utils import mtmt2_is_journal_mtaListed
from utils.enum_types import IntEnumWithDescription
from utils.url_tool import mtmt2_http_read

import logging
import json
import urllib

logger = logging.getLogger(__name__)

class PubLevel(IntEnumWithDescription):
    SUBMITTED = 0, 'beküldve'
    UNDER_FIRST_REVIEW = 1, 'első bírálat alatt'
    REJECTED = 2, 'visszautasítva'
    MAJOR_REVISION_IN_PROGRESS = 3, 'jelentős átdolgozás zajlik'
    MAJOR_REVISION_SUBMITTED = 4, 'jelentős átdolgozás beküldve'
    MINOR_REVISION_IN_PROGRESS = 5, 'kisebb átdolgozás zajlik'
    MINOR_REVISION_SUBMITTED = 6, 'kisebb átdolgozás beküldve'
    ACCEPTED = 7, 'elfogadva'
    EARLY_ACCESS = 8, 'előzetes kiadás'
    PUBLISHED = 9, 'végleges megjelenés'

class ThesisRelated(IntEnumWithDescription):
    NOT_KNOWN = 1, 'még nem tudni'
    NOT_RELATED = 2, 'nem'
    RELATED = 3, 'igen'

def parse_compound( command, key, description ):
    '''parse possible compound description like
        - t2-10002700-t1-30303030
        - s70707070-10101010-20202020-s80808080-30303030

        - command is the character (t and s in the examples, respectively) that introduces the entry
        - key is the name of the key the value given by the command should be placed in
        - description is the hypen-delimited compound string to parse
    '''
    _result = {}
    _elements = description.split('-')
    if len(_elements) == 1:
        _result = { "is_simple": True }
        _result[ key ] = int(_elements[0][len(command):])
    else:
        _result = { "is_simple": False, "entries": [] }
        _current = None
        for _element in _elements:
            if _element.startswith(command):
                _current = {}
                _result['entries'].append(_current)

                _current[key] = int(_element[len(command):])
                _current['authors'] = []
            else:
                _current['authors'].append(int(_element))

    return _result

def get_journal_extrainfo(journal_content, journal_flags_override, sourcedb_publishedYear):
    '''get extra info about the journal based on its ID. journal_content has mtid, and possibly other journal data from source, if journal was assigned to the publication we are processing.
    If a particular key is set in the journal_flags_override dict, its value takes precedence over what is read from the source.

    Returns a dict, with keys:
        - wosdb: bool
        - scopusdb: bool
        - has_impact_factor: bool
        - is_foreign_publication: bool
        - mta_listed_zero: bool
        - peer_reviewed: bool
    '''
    _flag_list = ['wosdb', 'scopusdb', 'has_impact_factor', 'is_foreign_publication', 'mta_listed_zero', 'peer_reviewed']
    _journal_props_to_check = ['sciIndexed', 'scopusIndexed', 'noIF', 'hungarian', 'comment', 'reviewType']
    _journalid = journal_content['mtid']
    _result = {
        'mtmt_journalid': _journalid,
        'warning': [],
    }
    for k, v in journal_flags_override.items():
        if k in _flag_list:
            _result[k] = v

    seen_all_props = True
    for _prop in _journal_props_to_check:
        seen_all_props = seen_all_props and _prop in journal_content

    _journal = None
    if seen_all_props:
        _journal = journal_content
    elif _journalid is not None:
        _url_template_journal = getconfig('input_sources.'+INPUT_SOURCE_MTMT2+'.journal')
        _url = _url_template_journal.replace('@@@', str(_journalid))

        # get data
        try:
            _journal_jsonstring = mtmt2_http_read(_url)
            _journal_root = json.loads(_journal_jsonstring)
            if len(_journal_root['content']) == 1:
                _journal = _journal_root['content'][0]
            else:
                _result['warning'].append('Multiple journals matched. / Az MTMT válaszában a %s azonosítóra nem 1 folyóirat adatai érkeztek, hanem %s.'%(_journalid, len(_journal_root['content'])))
        except urllib.error.HTTPError as e:
            raise e

    _journal_data_from_source = {}
    if _journal:
        if _journal['temporary']:
            # Temporary journal record counts as having no impact factor, but other properties still come from the journal record
            _journal_data_from_source['has_impact_factor'] = False
        else:
            _journal_data_from_source['has_impact_factor'] = not _journal['noIF']

        _journal_data_from_source['wosdb'] = _journal['sciIndexed']
        _journal_data_from_source['scopusdb'] = _journal['scopusIndexed']
        _journal_data_from_source['is_foreign_publication'] = not _journal['hungarian']
        _journal_data_from_source['peer_reviewed'] = 'reviewType' in _journal and _journal['reviewType'] == 'REVIEWED'

        # See if the journal in the publication's year (sourcedb_publishedYear) is listed on the MTA list of journals that engage in objectionable practices
        _journal_data_from_source['mta_listed_zero'] = False
        _url_template_mtaListed = getconfig('input_sources.'+INPUT_SOURCE_MTMT2+'.journal_mtaListed_info')
        _url = _url_template_mtaListed.replace('@@@', str(_journalid))
        # get data
        try:
            _mtaListed_jsonstring = mtmt2_http_read(_url)
            _mtaListed_root = json.loads(_mtaListed_jsonstring)
            if 'content' in _mtaListed_root:
                _journal_data_from_source['mta_listed_zero'] = mtmt2_is_journal_mtaListed(_mtaListed_root['content'], sourcedb_publishedYear)
            else:
                _journal_data_from_source['mta_listed_zero'] = False
        except urllib.error.HTTPError as e:
            raise e

        for _flag in _flag_list:
            # flags not already in result are retrieved from source
            if _flag not in _result:
                _result[_flag] = _journal_data_from_source[_flag]

            if _result[_flag] != _journal_data_from_source[_flag]:
                _result['warning'].append('Journal flag %s mismatch. / A folyoirat %s jellemzője eltér az MTMT (%s) és a BME GPK PhD extrainfo (%s) között.'%(_flag, _flag, _journal_data_from_source[_flag], _result[_flag]))

    return _result

def get_effective_type_code( publication_content ):
    """Based on the publication type and subtype in the publication content, returns the effective type code like j, c, bc, b.
        - publication_content is an MTMT2 publication data structure
    """
    type_name = None
    subtype_name = None
    if 'type' in publication_content:
        type_name = publication_content['type'].get('name')
        if type_name:
            type_name = type_name.lower()
    if 'subType' in publication_content:
        subtype_name = publication_content['subType'].get('name')
        if subtype_name:
            subtype_name = subtype_name.lower()

    effective_type_code = None

    if type_name == 'folyóiratcikk' and subtype_name == 'konferenciaközlemény':
        effective_type_code = 'c'
    elif type_name == 'folyóiratcikk':
        effective_type_code = 'j'
    elif type_name == 'könyvrészlet':
        # Ha a befoglalónak van konferenciája
        if 'book' in publication_content and 'conference' in publication_content['book']:
            effective_type_code = 'c'
        else:
            effective_type_code = 'bc'
    elif type_name == 'egyéb konferenciaközlemény':
        effective_type_code = 'c'
    elif type_name == 'könyv':
        effective_type_code = 'b'

    return effective_type_code

def parse_bme_gpk_phd_description( description, publication_content ):
    """Parses GPK PhD additional info.
        - description: the raw form of additional info. If None, it will be regarded as "a/l"
        - publication_content: the content received from source publication database (e.g. MTMT2)
    """
    auto_generated_description = description is None
    if description is None:
        description = "a/l"

    # remove the optional query string part, i.e. ?timestamp
    description = description.split('?')[0]

    # we suppress all warnings for some special cases
    # note that in some cases, URL might need amending with e.g. l
    suppress_warnings = False
    if description == 'j-in':
        suppress_warnings = True
        # add l to auto-recognize level
        description = '%s/l'%(description)
    elif description == 'j-in/l':
        suppress_warnings = True

    # initialize description dict
    _bme_gpk_phd_description_dict = { "raw": description, "auto_generated": auto_generated_description, "warning": [] }

    # type code based on pzblication metadata
    effective_type_code = get_effective_type_code( publication_content )

    type_codes_seen_in_url = []

    for _element in description.split('/'):
        _cmd = _element[0:1]
        _value = _element[1:]
        # exception handling for the longer commands
        if _element.startswith('bc'):
            _cmd = _element[0:2]
            _value = _element[2:]

        if _cmd == 'a' and _value != '':
            _bme_gpk_phd_description_dict['warning'].append('Unexpected argument for "a" command. / Az "a" típusjelzőshez nem várt paraméter érkezett.')
            continue

        try:
            if _cmd == 'l':
                if _value != '':
                    _bme_gpk_phd_description_dict['level'] = int(_value)
                elif 'publicationPending' in publication_content:
                    # üres "l" esetén az állapot (level)
                    # bepipált 'Megjelenés előtti' rubrikájú közlemény esetén l8 ("előzetes kiadás"), bepipálatlan esetén l9 ("végleges megjelenés")
                    _bme_gpk_phd_description_dict['level'] = PubLevel.EARLY_ACCESS if publication_content['publicationPending'] else PubLevel.PUBLISHED
                elif auto_generated_description:
                    # ha nincs 'Megjelenés előtti' mező, és nincs is Egyéb URL megadva, akkor a közlemény megjelent.
                    _bme_gpk_phd_description_dict['level'] = PubLevel.PUBLISHED
                else:
                    # ha nincs 'Megjelenés előtti' mező, üres 'l' nem elfogadható
                    # hibaüzenet lejjebb generálódik hiányzó vagy érvénytelen 'l' esetén.
                    pass
            elif _cmd == 't' and _value != '':
                _bme_gpk_phd_description_dict['thesis_related'] = parse_compound(_cmd, 'value', _element)
            elif _cmd == 's' and _value != '':
                _bme_gpk_phd_description_dict['supervisor'] = parse_compound(_cmd, 'supervisor', _element)
            elif _cmd == 'j' or _cmd == 'a' and effective_type_code == 'j':
                # _value holds a structure like: j1183-wn-in-sy-fy-m0

                _bme_gpk_phd_description_dict['pubtype'] = 'j'
                type_codes_seen_in_url.append(_cmd)

                _values_list = _value.split('-')
                _value_int = int(_values_list[0]) if _values_list[0] != '' else None

                _journal_flags_override = {}
                for _flag_element in _values_list[1:]:
                    _flag_cmd = _flag_element[0:1]
                    _flag_value = _flag_element[1:]

                    _flag_translate = {
                        'w': 'wosdb',
                        's': 'scopusdb',
                        'i': 'has_impact_factor',
                        'f': 'is_foreign_publication',
                        'm': 'mta_listed_zero',
                        # not part of the extra info, thus commented here
                        #'r': 'peer_reviewed',
                    }
                    _flag_key = _flag_translate.get(_flag_cmd)
                    if _flag_key is not None:
                        if _flag_key == 'mta_listed_zero':
                            _journal_flags_override[_flag_key] = _flag_value == '0'
                        else:
                            _journal_flags_override[_flag_key] = _flag_value == 'y'

                # journal ID from URL takes precedence and emit warning if it doesn't match the one from MTMT
                _journal_id = None
                if _value_int is not None:
                    _journal_id = _value_int
                if 'journal' in publication_content:
                    if _journal_id is None:
                        _journal_id = publication_content['journal']['mtid']
                    elif _journal_id != publication_content['journal']['mtid']:
                        _bme_gpk_phd_description_dict['warning'].append('Journal ID mismatch. / A folyóirat azonosítója eltér az MTMT (%s) és a BME GPK PhD extrainfo (%s) között.'%(_journal_id, publication_content['journal']['mtid']))

                if _journal_id is not None:
                    _bme_gpk_phd_description_dict['pubtype_container_id'] = _journal_id

                    _journal_info = get_journal_extrainfo(
                        # journal ID from URL takes precedence
                        publication_content['journal'] if _value_int is None and 'journal' in publication_content else { 'mtid': _value_int }
                        , _journal_flags_override
                        , publication_content.get('publishedYear')
                        )
                    if 'warning' in _journal_info:
                        _bme_gpk_phd_description_dict['warning'].extend(_journal_info['warning'])
                        del _journal_info['warning']
                    _bme_gpk_phd_description_dict['journal_info'] = _journal_info
            elif _cmd == 'bc' or _cmd == 'a' and effective_type_code == 'bc':
                _bme_gpk_phd_description_dict['pubtype'] = 'bc'
                type_codes_seen_in_url.append(_cmd)
                if 'book' in publication_content:
                    _bme_gpk_phd_description_dict['pubtype_container_id'] = publication_content['book']['mtid']
                elif _value != '':
                    _bme_gpk_phd_description_dict['pubtype_container_id'] = int(_value)
            elif _cmd == 'b' or _cmd == 'a' and effective_type_code == 'b':
                _bme_gpk_phd_description_dict['pubtype'] = 'b'
                type_codes_seen_in_url.append(_cmd)
            elif _cmd == 'c' or _cmd == 'a' and effective_type_code == 'c':
                _bme_gpk_phd_description_dict['pubtype'] = 'c'
                type_codes_seen_in_url.append(_cmd)

                # conference ID from URL takes precedence and emit warning if it doesn't match the one from MTMT
                _conference_id = None
                if _value != '':
                    _conference_id = int(_value)

                    # check if conference id exists
                    _url_template_conference = getconfig('input_sources.'+INPUT_SOURCE_MTMT2+'.conference')
                    _url = _url_template_conference.replace('@@@', str(_conference_id))

                    # get data
                    try:
                        _conference_jsonstring = mtmt2_http_read(_url)
                        _conference_root = json.loads(_conference_jsonstring)
                        if len(_conference_root['content']) != 1:
                            _bme_gpk_phd_description_dict['warning'].append('Conference ID in URL is invalid. Skipping. / A konferencia azonosító érvénytelen, ami a BME GPK PhD extrainfoban szerepel (%s), ezért nem használjuk.'%(_conference_id,))
                            _conference_id = None
                    except urllib.error.HTTPError as e:
                        raise e

                _conference_id_from_publication_content = None
                if 'book' in publication_content and 'conference' in publication_content['book']:
                    _conference_id_from_publication_content = publication_content['book']['conference']['mtid']
                elif 'conference' in publication_content:
                    # The following types in MTMT might have conference linked directly: Egyeb/Nem besorol, Folyoiratcikk/konferenciakozlemeny 
                    _conference_id_from_publication_content = publication_content['conference']['mtid']
                if _conference_id_from_publication_content is not None:
                    if _conference_id is None:
                        _conference_id = _conference_id_from_publication_content
                    elif _conference_id != _conference_id_from_publication_content:
                        _bme_gpk_phd_description_dict['warning'].append('Conference ID mismatch. / A konferencia azonosítója eltér az MTMT (%s) és a BME GPK PhD extrainfo (%s) között.'%(_conference_id, _conference_id_from_publication_content))

                if _conference_id is not None:
                    _bme_gpk_phd_description_dict['pubtype_container_id'] = _conference_id

        except ValueError:
            _msg = 'Missing or invalid number parameter for command %s. Hiányzó vagy hibás szám paraméter a BME GPK PhD extrainfo %s parancs feldolgozásakor. Nyers adat: %s.' % (_cmd, _cmd, _element)
            _bme_gpk_phd_description_dict['warning'].append(_msg)
            logger.error(_msg)
            raise
        except urllib.error.HTTPError as e:
            _msg = 'HTTP %s hiba a feldolgozáskor.'%(e.code)
            _bme_gpk_phd_description_dict['warning'].append()

    # checks
    try:
        _level = PubLevel(_bme_gpk_phd_description_dict.get('level'))
    except ValueError as e:
        if 'level' in _bme_gpk_phd_description_dict:
            del _bme_gpk_phd_description_dict['level']
        if not auto_generated_description:
            _msg = 'Missing or invalid level for the publication. / Hiányzik vagy hibás a közlemény állapotszintje: %s.'%(str(e))
            _bme_gpk_phd_description_dict['warning'].append(_msg)

    _thesis_related_OK = True
    _thesis_related_msg = None
    if 'thesis_related' in _bme_gpk_phd_description_dict and isinstance(_bme_gpk_phd_description_dict['thesis_related'], dict):
        _thesis_related = _bme_gpk_phd_description_dict['thesis_related']
        try:
            if _thesis_related['is_simple']:
                _thesis_related_value = ThesisRelated(_thesis_related['value'])
            else:
                for _e in _thesis_related['entries']:
                    _thesis_related_value = ThesisRelated(_e['value'])
        except ValueError as e:
            _thesis_related_msg = str(e)
            _thesis_related_OK = False
    else:
        _thesis_related_OK = False
    if not _thesis_related_OK:
        if not auto_generated_description:
            _msg = 'Missing or invalid thesis relation given for the publication. / Hiányzik vagy hibás a közlemény állapotszintje: %s.'%(_thesis_related_msg or str(_bme_gpk_phd_description_dict.get('thesis_related')))
            _bme_gpk_phd_description_dict['warning'].append(_msg)
        if 'thesis_related' in _bme_gpk_phd_description_dict:
            del _bme_gpk_phd_description_dict['thesis_related']

    if len(type_codes_seen_in_url) > 1 or not auto_generated_description and len(type_codes_seen_in_url) == 0:
        _msg = 'Missing or multiple types given in URL for the publication. / Hiányzik vagy többszörös a közlemény típusmegjelölése az URL-ben: %s.'%(','.join(type_codes_seen_in_url))
        _bme_gpk_phd_description_dict['warning'].append(_msg)
        if 'pubtype' in _bme_gpk_phd_description_dict:
            del _bme_gpk_phd_description_dict['pubtype']

    if suppress_warnings:
        _bme_gpk_phd_description_dict['warning'] = {}

    return _bme_gpk_phd_description_dict
