from common.constants import AUTHORTYPE_AUTHOR
from db.sources.bme_gpk_phd_description_parser import PubLevel, ThesisRelated
from riport.models.external import AuthorDb, PublicationDescription, Published, Pubauthors, ExtAuthorlist
from .scoring_token import ScoringToken
from .pub_util import PUB_UTIL
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, Q, ExpressionWrapper
from django.db.models import BooleanField

from datetime import datetime
from math import ceil

# Available scoring modes
SCORING_MODE_PHD = 'PhD'
SCORING_MODE_SUPERVISOR = 'tv'

def thesis_related_to_value(mtmt_id, thesis_related):
    if thesis_related is None:
        return None

    thesis_related_value = None
    if thesis_related['is_simple']:
        thesis_related_value = thesis_related['value']
    else:
        thesis_related_value = next(
            (entry.get('value') for entry in thesis_related['entries'] if mtmt_id in entry['authors']),
            None
        )

    return thesis_related_value

def share_from_url_supervisors(published, author_to_score, default_supervisor, specific_supervisor, authorcount):
    """Calculate share based on author's supervisor omitted from thelist of publication authors.
    Default supervisor is considered, if no specific supervisor is given for this publication and author in specific_supervisor
    """
    count = authorcount
    # alapértelmezett témavezető
    supervisor_mtmt_authid = default_supervisor

    # a közleményre specifikusan megadott témavezető élvez prioritást
    if specific_supervisor:
        if specific_supervisor.get('is_simple'):
            supervisor_mtmt_authid = specific_supervisor.get('supervisor')
        else:
            supervisor_mtmt_authid = next(
                (entry.get('supervisor') for entry in specific_supervisor.get('entries') if author_to_score.mtmtcode in entry.get('authors')),
                supervisor_mtmt_authid
            )

    if supervisor_mtmt_authid is None:
        return 1./count
    else:
        try:
            author = AuthorDb.objects.get(mtmt_authid=supervisor_mtmt_authid)
            if(Pubauthors.objects.filter(publication_id=published.publication.id, author_db_id=author.id, authortype__name=AUTHORTYPE_AUTHOR).exists()):
                count-=1
            return 1./count
        except ObjectDoesNotExist:
            return 1./count

class RIPORT(PUB_UTIL):
    """GPK PHD pontozó."""
    def __init__(self):
        PUB_UTIL.__init__(self, True)

    @classmethod
    def get_world_name(cls):
        """Return the name of the world where authors are retrieved from."""
        return 'kari'

    @classmethod
    def get_author_object_to_score(cls, mtmt_id, dbdatetime):
        """Return the ExtAuthorlist object for the given mtmt_id to be used."""
        # author_to_score:
        #  - TODO: ha kaptunk kívülről, akkor ez egy ExtAuthorlist objektum, akit pontozunk
        #  - ha nem kaptunk kívülről, akkor megkeressük heurisztika szerint a pontozandó ExtAuthorlist objekumot, éz azt táolja, ha találunk.
        #  - ha nem találtunk, akkor csak az 'mtmtcode' mező kerül kitöltésre az értékelt szerző authorid-jével
        try:
            # a pontozóhoz tartozó világ szerzői
            _author_obj = ExtAuthorlist.get_valid_objects(querytime=dbdatetime).filter(world=cls.get_world_name()).filter(mtmtcode=mtmt_id)
            # heurisztika1: a BME/GPK/DI-hez tartozó rekord kerül elölre
            _author_obj = _author_obj.annotate(
                priority1=ExpressionWrapper(Q(org='BME') & Q(unit='GPK') & Q(subunit='DI'), output_field=BooleanField()),
                )
            # heurisztika2: ahol ki van töltve a témavezető MTMT azonosítója, az a következő szempont
            # determinisztikus rendezés a végére
            _author_obj = _author_obj.order_by(F('priority1').desc(), F('supervisor_mtmt_authid').asc(nulls_first=False), 'id')
            author_to_score = _author_obj.first()
        except ObjectDoesNotExist:
            author_to_score = ExtAuthorlist(mtmtcode=mtmt_id)

        return author_to_score


    TOKENLIST = [
        ScoringToken('BESZ', 0.0, 'Beszámítható'),
        ScoringToken('TOV', 0.0, 'További'),
        ScoringToken('ERROR', 0.0, 'Hibakezelés'),
    ]

    def nullCounters(self):
        self.extraInfo['creditPoint_1_condition_1'] = []
        self.extraInfo['creditPoint_1_condition_2'] = []
        self.extraInfo['creditPoint_2_condition_1'] = []
        self.extraInfo['creditPoint_2_condition_2'] = []
        self.extraInfo['creditPoint_2_condition_3'] = []
        self.extraInfo['creditPoint_2_condition_4'] = []
        self.extraInfo['creditPoint_2_condition_5'] = []
        self.extraInfo['creditPoint_3_condition_1'] = 0
        self.extraInfo['creditPoint_3_condition_1_pubids'] = []
        self.extraInfo['creditPoint_4_condition_1_1'] = 0
        self.extraInfo['creditPoint_4_condition_1_1_pubids'] = []
        self.extraInfo['creditPoint_4_condition_1_2'] = []
        self.extraInfo['creditPoint_4_condition_2'] = 0
        self.extraInfo['creditPoint_4_condition_2_pubids'] = []
        self.extraInfo['creditPoint_4_condition_3'] = 0
        self.extraInfo['creditPoint_4_condition_3_pubids'] = []
        self.extraInfo['creditPoint_4_condition_4'] = []
        self.extraInfo['publication_table_data'] = []
        self.extraInfo['studies_lang_is_hungarian'] = None
        self.extraInfo['all_pubids'] = ''

    # és itt írjuk meg a függvényt, amely egy-egy közleményrekordból részpontszámot számol
    # NOTE: other scoring modules use mtmt_id instead author_to_score
    def kategorizalas(self, author_to_score, published, supervisor_mtmt):
        token = ''
        tokenkieg = 'url'
        debuginfo = ''
        pubid = published.publication.mtmt_pubid
        type_name = published.publication.type.type_name
        subtype_name = published.publication.typesubtype.subtype_name

        idegennyelv = published.publication.language.all_non_hungarian
        oldalszam = published.publication.pagenum
        if oldalszam is None:
            oldalszam = 0
        authorcount = published.publication.authorcount
        angol = published.publication.language.contains_english
        besorolas = published.publication.sjr_rank
        magyar = published.publication.language.is_hungarian
        jelleg = published.publication.character.name
        author_type = published.authortype.name
        elsoszerzo = published.isfirst
        token = ''
        has_isbn = published.has_isbn
        has_issn = published.has_issn

        # tartozik hozzá BME GPK PhD extraInfo?
        # ha változik is az erre vonatkozó feltétel, a True érték esetén feltételezzük, hogy a published.bme_gpk_phd_description lekérdezhető
        has_basic_bme_gpk_description = isinstance(published.bme_gpk_phd_description, dict)
        # tartozik hozzá teljesen kitöltött BME GPK PhD extraInfó, ami a PhD módban kell?
        has_valid_bme_gpk_description = (
                has_basic_bme_gpk_description
            and published.bme_gpk_phd_description.get('raw') is not None
            # 'level' kitöltött és egész szám
            and isinstance(published.bme_gpk_phd_description.get('level'), int)
            # 'thesis_related' kitöltött és egy dict
            # később ellenőrizzük, hogy adott szerzőre valóban van-e érvényes értéke
            and isinstance(published.bme_gpk_phd_description.get('thesis_related'), dict)
        )

        thesis_related_value = None
        if self.is_phd_mode:
            thesis_related_value = thesis_related_to_value(author_to_score.mtmtcode, published.bme_gpk_phd_description.get('thesis_related')) if has_valid_bme_gpk_description else None
        elif self.is_supervisor_mode:
            # támavezető módban tézisponthoz kapcsolódóként kezelünk minden közleményt
            thesis_related_value = ThesisRelated.RELATED

        # adott szerzőre érvényes értéke van-e a tézisponthoz kapcsolódásnak?
        has_valid_bme_gpk_description = has_valid_bme_gpk_description and (thesis_related_value is not None)

        if authorcount == 0:
            share = 0
        elif has_valid_bme_gpk_description:
            share = share_from_url_supervisors(published, author_to_score, supervisor_mtmt, published.bme_gpk_phd_description.get('supervisor'), authorcount)
        else:
            share = 1./authorcount

        # 4 tizedesjegyre felfele kerekitve kell vegezni a reszesedesre vonatkozo szamitasokat
        share = ceil(share*10000)/10000

        # flagek beallitasa GPK PhD extraInfo alapjan (ha van) vagy az alap rekordbol
        if has_basic_bme_gpk_description and 'journal_info' in published.bme_gpk_phd_description:
            impactfactor = published.bme_gpk_phd_description['journal_info'].get('has_impact_factor')
            wosdb = published.bme_gpk_phd_description['journal_info'].get('wosdb')
            scopusdb = published.bme_gpk_phd_description['journal_info'].get('scopusdb')
            kulfoldi = published.bme_gpk_phd_description['journal_info'].get('is_foreign_publication')
            mta_listan_nullas = published.bme_gpk_phd_description['journal_info'].get('mta_listed_zero')
            lektoralt = published.bme_gpk_phd_description['journal_info'].get('peer_reviewed')
        else:
            impactfactor = False
            wosdb = published.publication.wosdb
            scopusdb = published.publication.scopusdb
            kulfoldi = published.publication.is_foreign_publication
            mta_listan_nullas = published.publication.mta_listed_zero
            lektoralt = published.publication.peerreviewed

        # az értékelés során figyelembe vett típus neve, ami elsősorban az extrainfo-ban szereplő típusnévből számított
        effective_type_name = None
        #ha eredetileg egyéb típusú közlemény, akkor tipikusan nem vizsgáljuk a subtype értékét
        had_mtmt_other_type = False
        if type_name == 'egyéb':
            had_mtmt_other_type = True
        if has_basic_bme_gpk_description:
            if published.bme_gpk_phd_description.get('pubtype') == 'j':
                effective_type_name = 'folyóiratcikk'
            elif published.bme_gpk_phd_description.get('pubtype') == 'c':
                effective_type_name = 'konferenciaközlemény'
            elif published.bme_gpk_phd_description.get('pubtype') == 'bc':
                effective_type_name = 'könyvrészlet'
            elif published.bme_gpk_phd_description.get('pubtype') == 'b':
                effective_type_name = 'könyv'
        if effective_type_name is None:
            effective_type_name = type_name

        # közlemény beszámíthatóságának szükséges feltétele
        if (has_basic_bme_gpk_description
            # PhD módban elvárás, hogy nem auto-generált volt az Egyéb URL, és z etljesen kitöltött
            and (not self.is_phd_mode or (has_valid_bme_gpk_description and not published.bme_gpk_phd_description.get('auto_generated')))
            and jelleg == 'tudományos'
            and oldalszam >= 4
            and author_type=='author'
            and not mta_listan_nullas
            # témavezetői módban szükséges feltétel, hogy a közlemény az elmúlt 5 lezárult évből vagy a jelen futó vagy jövőbeli évből származzon
            and (not self.is_supervisor_mode or published.publication.pubdate >= self.supervisor_mode_min_publication_year)
            and published.bme_gpk_phd_description.get('pubtype') in ['b', 'bc', 'c', 'j']
            # c vagy j típus esetén ki kell derülni a befoglaló azonosítójának (konferencia vagy folyóirat)
            and (published.bme_gpk_phd_description.get('pubtype') not in ['c', 'j'] or isinstance(published.bme_gpk_phd_description.get('pubtype_container_id'), int))
            ):
            # a szükséges feltételek teljesülése esetén kategoizálás és kritériumvizsgálatok
            counts_as_folyoiratcikk = effective_type_name == 'folyóiratcikk' and lektoralt and any([
                                            type_name == 'folyóiratcikk' and subtype_name in ['szakcikk', 'összefoglaló cikk', 'sokszerzős vagy csoportos szerzőségű', 'rövid közlemény'],
                                            had_mtmt_other_type and subtype_name in ['nem besorolt', 'csak repozitóriumban hozzáférhető közlemény'],
                                        ])
            counts_as_konferenciacikk = effective_type_name == 'konferenciaközlemény' and any([
                                            has_isbn and type_name == 'könyvrészlet' and subtype_name in ['konferenciaközlemény', 'szaktanulmány', 'könyvfejezet'],
                                            has_issn and type_name == 'könyvrészlet' and subtype_name in ['konferenciaközlemény', 'szaktanulmány', 'könyvfejezet'],
                                            has_isbn and type_name == 'egyéb konferenciaközlemény' and subtype_name in ['konferenciaközlemény'],
                                            has_issn and type_name == 'egyéb konferenciaközlemény' and subtype_name in ['konferenciaközlemény'],
                                            has_issn and type_name == 'folyóiratcikk' and subtype_name in ['konferenciaközlemény'],
                                            had_mtmt_other_type and subtype_name in ['nem besorolt', 'csak repozitóriumban hozzáférhető közlemény'],
                                        ])
            counts_as_konyvfejezet = effective_type_name == 'könyvrészlet' and any([
                                            has_isbn and type_name == 'könyvrészlet' and subtype_name in ['könyvfejezet', 'szaktanulmány'],
                                            had_mtmt_other_type and subtype_name in ['nem besorolt', 'csak repozitóriumban hozzáférhető közlemény'],
                                        ])
            counts_as_konyv = effective_type_name == 'könyv' and any([
                                            has_isbn and type_name == 'könyv' and subtype_name in ['szakkönyv', 'monográfia', 'kézikönyv', 'tanulmánykötet'],
                                            had_mtmt_other_type and subtype_name in ['nem besorolt', 'csak repozitóriumban hozzáférhető közlemény'],
                                        ])

            # --- GPK PHD Publikáció I kreditponthoz ---
            if  magyar and (counts_as_folyoiratcikk or counts_as_konferenciacikk or counts_as_konyv or counts_as_konyvfejezet) and published.bme_gpk_phd_description.get('level') >= PubLevel.ACCEPTED :
                token = 'BESZ'
                self.extraInfo['creditPoint_1_condition_1'].append(published.mtmt_pubid)
            if  idegennyelv and (counts_as_folyoiratcikk or counts_as_konferenciacikk or counts_as_konyv or counts_as_konyvfejezet) and published.bme_gpk_phd_description.get('level') >= PubLevel.ACCEPTED :
                token = 'BESZ'
                self.extraInfo['creditPoint_1_condition_2'].append(published.mtmt_pubid)
            # --- GPK PHD Publikáció II kreditponthoz ---
            if impactfactor and angol and counts_as_folyoiratcikk and published.bme_gpk_phd_description.get('level') >= PubLevel.ACCEPTED:
                token = 'BESZ'
                self.extraInfo['creditPoint_2_condition_1'].append(published.mtmt_pubid)
            if (counts_as_folyoiratcikk or counts_as_konferenciacikk or counts_as_konyv or counts_as_konyvfejezet) and published.bme_gpk_phd_description.get('level') >= PubLevel.ACCEPTED:
                token = 'BESZ'
                # előírás: "további"
                # nem vizsgáljuk, hogy "további", helyette ekvivalens módon azt várjuk el, hogy az előző, erősebb kritériumban előírtnál 1-el több legyen
                #if published.mtmt_pubid not in self.extraInfo['creditPoint_2_condition_1']:
                self.extraInfo['creditPoint_2_condition_2'].append(published.mtmt_pubid)
            if (impactfactor
                and angol
                and counts_as_folyoiratcikk
                and published.bme_gpk_phd_description.get('level') in [
                        PubLevel.UNDER_FIRST_REVIEW,
                        PubLevel.MAJOR_REVISION_IN_PROGRESS,
                        PubLevel.MAJOR_REVISION_SUBMITTED,
                        PubLevel.MINOR_REVISION_IN_PROGRESS,
                        PubLevel.MINOR_REVISION_SUBMITTED,
                        PubLevel.ACCEPTED,
                    ]
                ):
                # Publ.II. cond 3 fulfilled
                token = 'BESZ'
                self.extraInfo['creditPoint_2_condition_3'].append(published.mtmt_pubid)
            if scopusdb and (counts_as_folyoiratcikk or counts_as_konferenciacikk or counts_as_konyv or counts_as_konyvfejezet) and published.bme_gpk_phd_description.get('level') >= PubLevel.ACCEPTED:
                token = 'BESZ'
                self.extraInfo['creditPoint_2_condition_4'].append(published.mtmt_pubid)
            if (counts_as_folyoiratcikk or counts_as_konferenciacikk or counts_as_konyv or counts_as_konyvfejezet) and published.bme_gpk_phd_description.get('level') >= PubLevel.ACCEPTED:
                token = 'BESZ'
                # előírás: "további"
                # nem vizsgáljuk, hogy "további", helyette ekvivalens módon azt várjuk el, hogy az előző, erősebb kritériumban előírtnál 1-el több legyen
                #if published.mtmt_pubid not in self.extraInfo['creditPoint_2_condition_3'] + self.extraInfo['creditPoint_2_condition_4']:
                self.extraInfo['creditPoint_2_condition_5'].append(published.mtmt_pubid)
            # --- GPK PHD Publikáció III kreditponthoz ---
            if impactfactor and counts_as_folyoiratcikk and kulfoldi and published.bme_gpk_phd_description.get('level') >= PubLevel.ACCEPTED:
                token = 'BESZ'
                self.extraInfo['creditPoint_3_condition_1'] += share
                self.extraInfo['creditPoint_3_condition_1_pubids'].append(published.mtmt_pubid)
            # --- GPK PHD Publikáció IV kreditponthoz ---
            if thesis_related_value == ThesisRelated.RELATED and (wosdb or scopusdb) and angol and counts_as_folyoiratcikk and published.bme_gpk_phd_description.get('level') >= PubLevel.ACCEPTED:
                token = 'BESZ'
                self.extraInfo['creditPoint_4_condition_1_1'] += share
                self.extraInfo['creditPoint_4_condition_1_1_pubids'].append(published.mtmt_pubid)
                if elsoszerzo:
                    self.extraInfo['creditPoint_4_condition_1_2'].append(published.mtmt_pubid)
            if thesis_related_value == ThesisRelated.RELATED and impactfactor and counts_as_folyoiratcikk and kulfoldi and angol and published.bme_gpk_phd_description.get('level') >= PubLevel.ACCEPTED:
                token = 'BESZ'
                self.extraInfo['creditPoint_4_condition_2'] += share
                self.extraInfo['creditPoint_4_condition_2_pubids'].append(published.mtmt_pubid)
            if thesis_related_value == ThesisRelated.RELATED and magyar and (counts_as_folyoiratcikk or counts_as_konferenciacikk or counts_as_konyv or counts_as_konyvfejezet) and published.bme_gpk_phd_description.get('level') >= PubLevel.ACCEPTED:
                token = 'BESZ'
                self.extraInfo['creditPoint_4_condition_3'] += share
                self.extraInfo['creditPoint_4_condition_3_pubids'].append(published.mtmt_pubid)
            if thesis_related_value == ThesisRelated.RELATED and published.bme_gpk_phd_description.get('level') >= PubLevel.ACCEPTED and (counts_as_folyoiratcikk or counts_as_konferenciacikk or counts_as_konyv or counts_as_konyvfejezet):
                token = 'BESZ'
                self.extraInfo['creditPoint_4_condition_4'].append(published.mtmt_pubid)
        if token == '':
            token = 'TOV'

        self.extraInfo['publication_table_data'].append({
            'token': token,
            'label_html': published.description['label_html'],
            'mtmt_pubid': published.mtmt_pubid,
            'typesubtype': {
                'effective_type_name': effective_type_name,
                'type_name': type_name,
                'subtype_name': subtype_name,
                'had_mtmt_other_type': had_mtmt_other_type,
            },
            'share': share,
            'publish_info': {
                'wosdb_string': 'WoS' if wosdb else '',
                'scopusdb_string': 'Scopus' if scopusdb else '',
                'sjr': besorolas if besorolas else '',
                'if_string' : 'IF' if impactfactor else '',
                'isxn_string': ' '.join([ _s for _s in ['ISBN' if has_isbn else None, 'ISSN' if has_issn else None] if _s]),
                'is_foreign_string': 'külföldi' if kulfoldi else 'hazai',
                'lektoralt_string': 'lektorált' if lektoralt else '',
                'mta_listan_nullas' : mta_listan_nullas,
            },
            'url_based_data' : {
                'level_string': PubLevel(published.bme_gpk_phd_description.get('level')).description if has_basic_bme_gpk_description and 'level' in published.bme_gpk_phd_description else None,
                'pubtype': published.bme_gpk_phd_description.get('pubtype') if has_basic_bme_gpk_description else None,
                'pubtype_container_id': published.bme_gpk_phd_description.get('pubtype_container_id') if has_basic_bme_gpk_description else None,
                'thesis_related_value': thesis_related_value,
                'thesis_related_string': ThesisRelated(thesis_related_value).description if thesis_related_value is not None else None,
                'raw_url': published.bme_gpk_phd_description.get('raw') if has_basic_bme_gpk_description else None,
                'has_valid_bme_gpk_description': not self.is_phd_mode or has_valid_bme_gpk_description,
                'warning': published.bme_gpk_phd_description.get('warning') if has_basic_bme_gpk_description else None,
            }
        })
        self.extraInfo['all_pubids'] += str(pubid) + ','
        published.token = token
        self.extraInfo['publication_table_data'].sort(key=lambda pub: pub['token'])
        return (pubid, token, tokenkieg, share, debuginfo)


    def citations_gpk(self, pubrefs):
        return []

    # Fontos egyedi függvény, a pub_util_riportgen() ezt hívja meg
    def riportgen(self, mtmt_id, dbdatetime, publisheds, pubrefs, supervisor_mtmt):
        self.nullCounters()
        author_to_score = self.get_author_object_to_score(mtmt_id, dbdatetime)

        mode_data = {}
        # Ha ki van töltve és 'hu', akkor magyar képzéses doktorandusz.
        # Ha nincs kitöltve, akkor a témavezetői módban értékelünk. Ilyenkor úgy kell viselkedni, mintha angol képzéses lenne. Ref. #244
        self.studies_lang_is_hungarian = author_to_score.extrainfo.get('bme_gpk_phd_studies_lang') == 'hu'
        mode_data['studies_lang_is_hungarian'] = self.studies_lang_is_hungarian

        # mode kiválasztása
        effective_mode = SCORING_MODE_SUPERVISOR if author_to_score.extrainfo.get('bme_gpk_phd_studies_lang') is None else SCORING_MODE_PHD
        self.is_phd_mode = (effective_mode == SCORING_MODE_PHD)
        self.is_supervisor_mode = (effective_mode == SCORING_MODE_SUPERVISOR)
        self.supervisor_mode_min_publication_year = datetime.now().year - 5
        mode_data['is_phd_mode'] = self.is_phd_mode
        mode_data['is_supervisor_mode'] = self.is_supervisor_mode
        mode_data['supervisor_mode_min_publication_year'] = self.supervisor_mode_min_publication_year

        for published in publisheds:
            published.description = PublicationDescription.objects.values().get(id=published.publication_description_id)
        mtmt_pubauthorname = publisheds[0].author_db.authorname if len(publisheds) > 0 else ''
        alltoken = []
        for published in publisheds:
            alltoken.append(self.kategorizalas(author_to_score, published, supervisor_mtmt))

        alltoken += self.citations_gpk(pubrefs)
        #print (tokendict) # statisztika
        fejlec = {'mtmt_id': mtmt_id, 'mtmt_name': mtmt_pubauthorname, 'mode_data': mode_data.copy() }
        return fejlec, alltoken, self.extraInfo.copy()

    def riportgen_publication(self, dbdatetime, ublished, pubrefs, supervisor_mtmt):
        self.nullCounters()
        alltoken = []
        token = self.kategorizalas(ExtAuthorlist(mtmtcode=-1), published, supervisor_mtmt)
        alltoken.append(token)
        #alltoken += self.citations_gpk(pubrefs)
        #print (tokendict) # statisztika
        fejlec = {'talalat_token': token[1] }
        return fejlec, alltoken, self.extraInfo.copy()

    def transform_extraInfo(self, extraInfo, totalScore):
        """GPK PhD alapú pontozók minimumkövetelmény-teljesülések számítása"""
        creditPoint1Condition1Treshold = 1 #≥1 magyar nyelvű folyóiratcikk, konferenciacikk vagy könyv(fejezet)
        creditPoint1Condition2Treshold = 1 #≥1 idegen nyelvű konferenciacikk
        creditPoint2Condition1Treshold = 1 #≥1 IF-os, angol nyelvű folyóiratcikk
        # itt a "további"-val ekvivalens módon azt várjuk el, hogy az előző, erősebb kritériumban előírtnál 1-el több legyen
        creditPoint2Condition2Treshold = creditPoint2Condition1Treshold + 1 #≥1 további folyóiratcikk, konferenciacikk vagy könyv(fejezet)
        creditPoint2Condition3Treshold = 1 #≥1 IF-os folyóiratnál bírálatra befogadott angol nyelvű kézirat
        creditPoint2Condition4Treshold = 1 #≥1 Scopus-ban szereplő folyóiratcikk vagy konferenciacikk
        # itt a "további"-val ekvivalens módon azt várjuk el, hogy az előző, erősebb kritériumban előírtnál 1-el több legyen
        creditPoint2Condition5Treshold = creditPoint2Condition4Treshold + 1 #≥1 további folyóiratcikk, konferenciacikk vagy könyv(fejezet)
        creditPoint3Condition1Treshold = 0.5  #≥50% szerzőhányadnyi, IF-os folyóiratcikk külföldi kiadású folyóiratban -> ≥0.5 share
        creditPoint4Condition1_1Treshold = 2 #≥200% szerzőhányadnyi, WoS-ban vagy Scopus-ban szereplő, angol nyelvű folyóiratcikk vagy konferenciacikk -> ≥2 share
        creditPoint4Condition1_2Treshold = 1 #közülük ≥1 első szerzős
        creditPoint4Condition2Treshold = 0.5 #≥50% szerzőhányadnyi, IF-os folyóiratcikk külföldi kiadású folyóiratban -> megegyezik a pub III-ban lévő feltétellel
        creditPoint4Condition3Treshold = 1 #magyar nyelvű képzés esetén: ≥100% szerzőhányadnyi magyar nyelvű folyóiratcikk, konferenciacikk vagy könyv(fejezet) -> ≥1 share
        creditPoint4Condition4Treshold = 3 #≥3 darab
        extraInfo['Pub1Fulfilled'] = len(extraInfo['creditPoint_1_condition_1']) >= creditPoint1Condition1Treshold or len(extraInfo['creditPoint_1_condition_2']) >= creditPoint1Condition2Treshold
        extraInfo['Pub2Fulfilled'] = any([
                                            all([
                                                len(extraInfo['creditPoint_2_condition_1']) >= creditPoint2Condition1Treshold,
                                                len(extraInfo['creditPoint_2_condition_2']) >= creditPoint2Condition2Treshold,
                                            ]),
                                            all([
                                                len(extraInfo['creditPoint_2_condition_3']) >= creditPoint2Condition3Treshold,
                                                len(extraInfo['creditPoint_2_condition_4']) >= creditPoint2Condition4Treshold,
                                                len(extraInfo['creditPoint_2_condition_2']) >= creditPoint2Condition5Treshold,
                                            ]),
                                        ])
        extraInfo['Pub3Fulfilled'] = extraInfo['Pub2Fulfilled'] and extraInfo['creditPoint_3_condition_1'] >= creditPoint3Condition1Treshold
        extraInfo['Pub4Fulfilled'] = all([
                                            extraInfo['Pub1Fulfilled'],
                                            extraInfo['Pub2Fulfilled'],
                                            extraInfo['Pub3Fulfilled'],
                                            extraInfo['creditPoint_4_condition_1_1'] >= creditPoint4Condition1_1Treshold,
                                            not self.is_phd_mode or len(extraInfo['creditPoint_4_condition_1_2']) >= creditPoint4Condition1_2Treshold,
                                            extraInfo['creditPoint_4_condition_2'] >= creditPoint4Condition2Treshold,
                                            not self.studies_lang_is_hungarian or extraInfo['creditPoint_4_condition_3'] >= creditPoint4Condition3Treshold,
                                            len(extraInfo['creditPoint_4_condition_4']) >= creditPoint4Condition4Treshold,
                                        ])
        # a legmagasabb teljesített szintet megkeressük
        if extraInfo['Pub4Fulfilled']:
            extraInfo['MaxPubNFulfilled'] = 4
        elif extraInfo['Pub3Fulfilled']:
            extraInfo['MaxPubNFulfilled'] = 3
        elif extraInfo['Pub2Fulfilled']:
            extraInfo['MaxPubNFulfilled'] = 2
        elif extraInfo['Pub1Fulfilled']:
            extraInfo['MaxPubNFulfilled'] = 1
        else:
            extraInfo['MaxPubNFulfilled'] = 0

        return extraInfo
