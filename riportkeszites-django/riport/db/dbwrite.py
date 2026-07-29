'''Ez a modul felel az adatok adatbázisszerverbe való beleírásáért.
   A normál XML feldolgozási sorrend:
      - parser
      - validator
      - dbwrite
'''

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import F, Q

from tudriport.common.config import getconfig
from tudriport.sqlimport.logfunc import format_pubid_string
from common.enum3 import bool_to_enum3
from riport.models.external import *

import logging

logger = logging.getLogger(__name__)

VERBOSE = getconfig('sqlimport.VERBOSE')
SQLDONTWRITE = getconfig('sqlimport.SQLDONTWRITE')
MISSING_DIMENSION_ID = getconfig('sqlimport.MISSING_DIMENSION_ID')

def citations_per_year(citations):
    cit_ordered = {}
    for cit in citations:
        if cit['date'] not in cit_ordered:
            cit_ordered[cit['date']] = {
                'independent': 0,
                'independent_list': [],
                'independent_wos': 0,
                'independent_wos_list': [],
                'independent_scopus': 0,
                'independent_scopus_list': [],
                'notindependent': 0,
                'notindependent_list': []
            }
        if cit['independent']:
            cit_ordered[cit['date']]['independent']+=1
            cit_ordered[cit['date']]['independent_list'].append(cit['mtmt_identifier'])
        else:
            cit_ordered[cit['date']]['notindependent']+=1
            cit_ordered[cit['date']]['notindependent_list'].append(cit['mtmt_identifier'])

        if cit['independent'] and cit['WoS']:
            cit_ordered[cit['date']]['independent_wos']+=1
            cit_ordered[cit['date']]['independent_wos_list'].append(cit['mtmt_identifier'])

        if cit['independent'] and cit['Scopus']:
            cit_ordered[cit['date']]['independent_scopus']+=1
            cit_ordered[cit['date']]['independent_scopus_list'].append(cit['mtmt_identifier'])

    for cityear in cit_ordered:
        for listtype in ['independent_list', 'notindependent_list', 'independent_wos_list', 'independent_scopus_list']:
            cit_ordered[cityear][listtype] = ', '.join(map(str, cit_ordered[cityear][listtype]))

    return cit_ordered

def citations_differ(cit_ordered, pubref_set):
    """Compare data of citations, and return True iff they differ in their count, year-set or attributes for any year."""
    if len(cit_ordered) != pubref_set.count():
        return True
    else:
        for pr in pubref_set.all():
            if pr.year not in cit_ordered:
                return True
            else:
                if pr.differs(cit_ordered[pr.year]):
                    return True
    return False

def pubauthors_differ(authors, pubauthors_set):
    """Compare data of pubauthors, and return True iff they differ in their count, or any of the attributes"""
    if len(authors) != pubauthors_set.count():
        return True
    else:
        authors_dict = {}
        for a in authors:
            if a['authortype'] not in authors_dict:
                authors_dict[a['authortype']] = {}
            authors_dict[ a['authortype'] ][ a['mtmt_authid'] ] = a
        for pa in pubauthors_set.all():
            if pa.authortype.name in authors_dict and pa.author_db.mtmt_authid in authors_dict[pa.authortype.name]:
                a = authors_dict[pa.authortype.name][pa.author_db.mtmt_authid]
                if (pa.mtmt_pubauthorname != a['pubname']
                    # the following 2 were already checked
                    #or pa.author_db.mtmt_authid != a['mtmt_authid']
                    #or pa.authortype.name != a['authortype']
                    or pa.share != a['share']
                    or pa.position != a['position']
                    or pa.isfirst != a['isfirst']
                    or pa.islast != a['islast']
                    or pa.has_author_affiliation_BME_EMK != ('BME_EMK' in a['affiliations'])
                    or pa.has_author_affiliation_BME_EPK != ('BME_EPK' in a['affiliations'])
                    or pa.has_author_affiliation_BME_GPK != ('BME_GPK' in a['affiliations'])
                    or pa.has_author_affiliation_BME_GTK != ('BME_GTK' in a['affiliations'])
                    or pa.has_author_affiliation_BME_KJK != ('BME_KJK' in a['affiliations'])
                    or pa.has_author_affiliation_BME_TTK != ('BME_TTK' in a['affiliations'])
                    or pa.has_author_affiliation_BME_VBK != ('BME_VBK' in a['affiliations'])
                    or pa.has_author_affiliation_BME_VIK != ('BME_VIK' in a['affiliations'])
                    or pa.has_author_affiliation_BME != ('BME' in a['affiliations'])
                ):
                    return True
            else:
                return True
    return False

#FIXME: amikor az ext_journal_metrics importja következik, ezt is rendbe kell tenni
def update_from_ext_journal_metrics(cursor, publication_id, issn1, issn2, year):
    None
    # seldata = {
    #    'issn1': issn1,
    #    'issn2': issn2,
    #    'year': year
    # }
    # res = cursor.execute("""select metric_name, metric_value, isestimate from ext_journal_metrics where
    #               (issn = %(issn1)s or issn = %(issn2)s or eissn = %(issn1)s or eissn = %(issn2)s)
    #                and year = %(year)s and valid_to isnull""", seldata).fetchall()
    # for r in res:
    #     if r[0] in ['citescore', 'sjr', 'snip']:
    #         cursor.execute("update publication set %s_value = '%s', %s_isestimate = '%s' where id = %s"%(r[0], r[1], r[0], r[2], publication_id))

def dbwrite(db, publication, authors, citations, effective_datetime):
    if effective_datetime is None:
        effective_datetime = timezone.now()

    publication['gen_datetimeutc']=str(effective_datetime)
    cursor = db.cursor()

    with transaction.atomic():
        logging.info('---->  uj sql ellenorzes: %s <----'%publication['mtmt_pubid'])

        # keressük a Type bejegyzést a publikációhoz.
        if 'type_id' in publication:
            o_type, _created = Type.objects.get_or_create(
                type_mtmt=publication['type_id'],
                defaults={
                    'type_name': publication['type'],
                }
            )
        else:
            o_type = Type.get_missing_instance()

        # keressük a Typesubtype bejegyzést a publikációhoz.
        # Note: ha nincs subtype, akkor is a típuson belüli '(nincs besorolás)' bejegyzést kapja, ha van típusa
        if 'type_id' in publication:
            o_typesubtype, _created = Typesubtype.objects.get_or_create(
                type=o_type,
                subtype_mtmt=publication.get('subtype_id'),
                defaults={
                    'subtype_name': publication.get('subtype', getconfig('sqlimport.MISSING_DIMENSION_NAMES.SUBTYPE')),
                }
            )
        else:
            o_typesubtype = Typesubtype.get_missing_instance()

        # keressük a Character bejegyzést a publikációhoz.
        if 'character_id' in publication:
            o_character, _created = Character.objects.get_or_create(
                chid_mtmt=publication['character_id'],
                defaults={
                    'name': publication['character'],
                }
            )
        else:
            o_character = Character.get_missing_instance()

        publication['gen_container_groupid'] = Container.get_missing_instance().groupid
        # ISSNs = []
        # for i in ['issn', 'eissn']:
        #     if i in publication and publication.get(i) is not None:
        #         ISSNs.append(publication.get(i))
        #     ISSNs.sort()
        # if ISSNs:
        #     #FIXME: add ISSN-based lookups here

        # van-e language_id a publications táblához?
        if 'language' in publication and publication['language']:
            o_language, _created = Language.objects.get_or_create(
                name=publication['language'].lower(),
                defaults={
                }
            )
        else:
            o_language = Language.get_missing_instance()

        # van-e publisher a publications táblához? ... feltéve hogy van publisherünk.
        if 'publisherlocation' in publication and publication['publisherlocation'] is not None:
            o_publisherlocation, _created = Location.objects.get_or_create(
                country=publication['publisherlocation']['country'],
                city=publication['publisherlocation']['city'],
                defaults={
                }
            )
        else:
            o_publisherlocation = Location.get_missing_instance()

        # van-e (publishing) location a publications táblához? ... feltéve hogy van publisherünk.
        if 'publishinglocation' in publication and publication['publishinglocation'] is not None:
            o_publishinglocation, _created = Location.objects.get_or_create(
                country=publication['publishinglocation']['country'],
                city=publication['publishinglocation']['city'],
                defaults={
                }
            )
        else:
            o_publishinglocation = Location.get_missing_instance()

        # Megkeressük/felvesszük a PublicationDescription rekordot
        o_publicationDescription, _created = PublicationDescription.objects.get_or_create(
            mtmt_pubid=publication['mtmt_pubid'],
            label_txt=publication['pubdesc_label_txt'],
            label_html=publication['pubdesc_label_html'],
            citation_duplicate_doi_info=publication['citation_duplicate_DOI_info'],
            citation_duplicate_title_info=publication['citation_duplicate_title_info'],
            citation_list_not_published=publication['citation_list_not_published'],
            citation_list_citingdoc_not_published=publication['citation_list_citingdoc_not_published'],
            citation_list_citingdoc_w_error=publication['citation_list_citingdoc_w_error'],
            citation_list_unknown_external=publication['citation_list_unknown_external'],
            defaults={
            }
        )

        publication_payload = {
            'type': o_type,
            'typesubtype': o_typesubtype,
            #TODO: remove 'container_groupid' field and also Container model
            'container_groupid': publication['gen_container_groupid'],
            'character': o_character,
            'is_full_scientific': publication.get('is_full_scientific'),
            'is_published': publication.get('is_published'),
            'publication_description': o_publicationDescription,
            'impactfactor_value': publication['impactfactor'],
            #TODO: 'impactfactor_isestimate': None,
            #TODO: 'citescore_value': None,
            #TODO: 'citescore_isestimate': None,
            'sjr_value': publication['sjr_value'],
            'sjr_rank': publication['sjr_rank'],
            'sjr_isestimate': publication['sjr_isestimate'],
            #TODO: 'snip_value': publication[''],
            #TODO: 'snip_isestimate': publication[''],
            'mta_rank': publication['mta_rank'],
            'mta_rank_full': publication['mta_rank_full'],
            'mta_gmb_rank': publication['mta_gmb_rank'],
            'mta_gmb_rank_full': publication['mta_gmb_rank_full'],
            'mta_listed_zero': publication['mta_listed_zero'],
            'pubdate': publication['pubdate'],
            'language': o_language,
            'is_foreign_language': publication.get('is_foreign_language'),
            'peerreviewed': publication['peerreviewed'],
            'publisherlocation': o_publisherlocation,
            'publishinglocation': o_publishinglocation,
            'is_foreign_publication': publication.get('is_foreign_publication'),
            'pagenum': publication['page_number'],
            'wosdb': publication['identifier_WoS'],
            'scopusdb': publication['identifier_Scopus'],
            'authorcount': publication['authorcount'],
            'editorcount': publication['editorcount'],
            'refcount': publication['refcount'],
            'mtmt_pubid': publication['mtmt_pubid'],
            'has_citation_duplicate_doi': publication['has_citation_duplicate_DOI'],
            'has_citation_duplicate_title': publication['has_citation_duplicate_title'],
            'has_citation_not_published': publication['has_citation_not_published'],
            'has_citation_citingdoc_not_published': publication['has_citation_citingdoc_not_published'],
            'has_citation_citingdoc_w_error': publication['has_citation_citingdoc_w_error'],
            'has_citation_unknown_external': publication['has_citation_unknown_external'],
            'has_doi': publication['has_doi'],
            'has_isbn': publication['has_isbn'],
            'has_issn': publication['has_issn'],
            'has_full_document_url': publication['has_full_document_url'],
            'has_oa_link': publication['has_oa_link'],
            'bme_gpk_phd_description': publication['bme_gpk_phd_description'],
        }
        cit_ordered = citations_per_year(citations)

        # mtmt pubid exist?
        create_publication = False
        try:
            o_publication = Publication.get_valid_objects(effective_datetime).get(mtmt_pubid=publication['mtmt_pubid'])

            # check changes in the publication record itself or in the related lists
            chk_publication_differs = o_publication.differs(publication_payload)
            chk_pubauthors_differ = pubauthors_differ(authors, o_publication.pubauthors_set)
            chk_citations_differ = citations_differ(cit_ordered, o_publication.pubref_set)

            if chk_publication_differs or chk_pubauthors_differ or chk_citations_differ:
                logger.info(format_pubid_string(publication)+ 'A rekord különbözik az adatbázisban levőtől. Különbözik? közlemény: %s, szerzők: %s, idézők: %s'%(chk_publication_differs, chk_pubauthors_differ, chk_citations_differ) )
                # close Published records. Note: .update bypasses the save() method which is OK for now
                Published.get_valid_objects().filter(publication=o_publication).update(valid_to=effective_datetime)
                # update this publication itself. VersionedModel takes care of closing and creating new records
                o_publication.update_if_differs(publication_payload)
                logger.info('Lezártuk a Publication.id=%s rekordot %s időbélyeggel.'%(o_publication.id, str(effective_datetime)))
                o_publication.save(effective_datetime=effective_datetime)
            else:
                logger.info(format_pubid_string(publication)+ 'Letezik ugyanilyen tartalmu SQL rekord, vége.')
                logger.debug(format_pubid_string(publication)+ 'Az SQL iro modul befejezodott.')
                cursor.close()
                db.rollback()
                transaction.set_rollback(True)
                return

        except Publication.DoesNotExist:
            o_publication = Publication(**publication_payload)
            o_publication.valid_from = effective_datetime
            o_publication.save()

        update_from_ext_journal_metrics(cursor, o_publication.id,
                    publication.get('gen_issn1', None), publication.get('gen_issn2', None), publication['pubdate'])    # citescore_* sjr_*, snip_*

        for author in authors:
            # Ha nincs az authdb-ben
            o_authordb, _created = AuthorDb.objects.get_or_create(
                mtmt_authid = author['mtmt_authid'],
                defaults = {
                    'authorname': author['name'],
                    'authorcomment': author['comment'],
                }
            )
            # ha nincs pubname, atvesszuk az Authordb szerinti nevet
            if author['pubname'] is None:
                author['pubname'] = o_authordb.authorname

            # van-e authortype a pubauthors táblához?
            o_authortype, _created = Authortype.objects.get_or_create(
                name = author['authortype'],
                defaults = {
                }
            )

            pubauthor_payload = {
                # ha itt új mező jön be, akkor a pubauthors_differ is kiegészítendő
                'mtmt_pubauthorname': author['pubname'],
                'author_db': o_authordb,
                'authortype': o_authortype,
                'publication': o_publication,
                'share': author['share'],
                'position': author['position'],
                'isfirst': author['isfirst'],
                'islast': author['islast'],
                'has_author_affiliation_BME_EMK': 'BME_EMK' in author['affiliations'],
                'has_author_affiliation_BME_EPK': 'BME_EPK' in author['affiliations'],
                'has_author_affiliation_BME_GPK': 'BME_GPK' in author['affiliations'],
                'has_author_affiliation_BME_GTK': 'BME_GTK' in author['affiliations'],
                'has_author_affiliation_BME_KJK': 'BME_KJK' in author['affiliations'],
                'has_author_affiliation_BME_TTK': 'BME_TTK' in author['affiliations'],
                'has_author_affiliation_BME_VBK': 'BME_VBK' in author['affiliations'],
                'has_author_affiliation_BME_VIK': 'BME_VIK' in author['affiliations'],
                'has_author_affiliation_BME': 'BME' in author['affiliations'],
            }

            o_pubauthor = Pubauthors(**pubauthor_payload)
            o_pubauthor.save()

            # write Published entry for the publication and author pair
            o_published = Published(**publication_payload, **pubauthor_payload)
            o_published.valid_from = effective_datetime
            o_published.save()

        for cityear in cit_ordered:
            o_citation = Pubref(
                publication = o_publication,
                year = cityear,
                independent = cit_ordered[cityear]['independent'],
                independent_list = cit_ordered[cityear]['independent_list'],
                independent_wos = cit_ordered[cityear]['independent_wos'],
                independent_wos_list = cit_ordered[cityear]['independent_wos_list'],
                independent_scopus = cit_ordered[cityear]['independent_scopus'],
                independent_scopus_list = cit_ordered[cityear]['independent_scopus_list'],
                notindependent = cit_ordered[cityear]['notindependent'],
                notindependent_list = cit_ordered[cityear]['notindependent_list'],
            )
            o_citation.save()

        # end: transaction commit
        cursor.close()
        if SQLDONTWRITE:
            logger.warning(format_pubid_string(publication)+ 'VIGYÁZZ: NINCS KIÍRVA AZ SQL-be! Lásd: SQLDONTWRITE')
        else:
            db.commit()
            logger.info(format_pubid_string(publication)+ 'Az SQL rekord kiírva, vége.')

        logger.debug(format_pubid_string(publication)+ 'Az SQL iro modul befejezodott.')


def dbwrite_closerecord(db, mtmt_pubid, close_datetime):
    upd_data = {
        'mtmt_pubid': mtmt_pubid,
        'close_datetime': str(close_datetime),
    }
    upd = """update publications set valid_to = %(close_datetime)s::timestamp at time zone 'utc'
        where (mtmt_pubid) is not distinct from (%(mtmt_pubid)s) and valid_to isnull"""
    with db:
        with db.cursor() as cursor:
            cursor.execute(upd, upd_data)

    logger.info('A %s publikáció lezárása megtörtént.'%(mtmt_pubid))
