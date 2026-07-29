import math

from django.db.models import BooleanField, IntegerField, F, OuterRef, Subquery
from django.db.models.functions import Cast

from common.constants import TUDRIPORT_VIEW_TYPE_LIST, TUDRIPORT_VIEW_TYPE_DETAIL, TUDRIPORT_VIEW_TYPE_ADHOC

from .scoring_token import ScoringToken
from .pub_util import PUB_UTIL

class RIPORT(PUB_UTIL):
    """BME Monitoring pontozó."""
    def __init__(self):
        PUB_UTIL.__init__(self, True, True)
        # extrainfó számításához
        self.extraInfo = {
            'numScientificPublicationsBME': 0,
            'listScientificPublicationsBME': [],
            'numScientificPublicationsNoBME': 0,
            'listScientificPublicationsNoBME': [],
            'numScopusPublicationsBME': 0,
            'listScopusPublicationsBME': [],
            'numScopusPublicationsNoBME': 0,
            'listScopusPublicationsNoBME': [],
            'numSumD1Q1PublicationsBME': 0,
            'listD1Q1PublicationsBME': [],
            'numSumD1Q1PublicationsNoBME': 0,
            'listD1Q1PublicationsNoBME': [],
            'sumShareInD1Q1BME': 0.0,
        }

    TOKENLIST = [
        ScoringToken('TUD,noScopus,BME', 0.0, 'Teljes tudományos publikáció, BME-affiliációval'),
        ScoringToken('TUD,noScopus,NoBME', 0.0, 'Teljes tudományos publikáció, BME affiliáció nélkül'),
        ScoringToken('TUD,Scopus,BME', 0.0, 'Scopus indexált teljes tudományos publikáció, BME-affiliációval'),
        ScoringToken('TUD,Scopus,NoBME', 0.0, 'Scopus indexált teljes tudományos publikáció, BME affiliáció nélkül'),
        ScoringToken('FOLY,D1,BME', 1.0, 'Folyóiratcik (teljes tudományos publikáció): MTMT-ben D1 besorolású folyóiratban, BME-affiliációval'),
        ScoringToken('FOLY,D1,NoBME', 0.0, 'Folyóiratcikk (teljes tudományos publikáció): MTMT-ben D1 besorolású folyóiratban, BME affiliáció nélkül'),
        ScoringToken('FOLY,Q1,BME', 1.0, 'Folyóiratcikk (teljes tudományos publikáció): MTMT-ben Q1 (de nem D1) besorolású folyóiratban, BME-affiliációval'),
        ScoringToken('FOLY,Q1,NoBME', 0.0, 'Folyóiratcikk (teljes tudományos publikáció): MTMT-ben Q1 (de nem D1) besorolású folyóiratban, BME affiliáció nélkül'),
        ScoringToken('FOLY,Q2,BME', 1.0, 'Folyóiratcikk (teljes tudományos publikáció): MTMT-ben Q2 besorolású folyóiratban, BME-affiliációval'),
        ScoringToken('FOLY,Q2,NoBME', 0.0, 'Folyóiratcikk (teljes tudományos publikáció): MTMT-ben Q2 besorolású folyóiratban, BME affiliáció nélkül'),
        ScoringToken('FOLY,Q3,BME', 1.0, 'Folyóiratcikk (teljes tudományos publikáció): MTMT-ben Q3 besorolású folyóiratban, BME-affiliációval'),
        ScoringToken('FOLY,Q3,NoBME', 0.0, 'Folyóiratcikk (teljes tudományos publikáció): MTMT-ben Q3 besorolású folyóiratban, BME affiliáció nélkül'),
        ScoringToken('FOLY,Q4,BME', 1.0, 'Folyóiratcikk (teljes tudományos publikáció): MTMT-ben Q4 besorolású folyóiratban, BME-affiliációval'),
        ScoringToken('FOLY,Q4,NoBME', 0.0, 'Folyóiratcikk (teljes tudományos publikáció): MTMT-ben Q4 besorolású folyóiratban, BME affiliáció nélkül'),
        ScoringToken('SZABADALOM,BME', 1.0, 'Szabadalom, formatervezési minta, BME-affiliációval'),
        ScoringToken('SZABADALOM,NoBME', 0.0, 'Szabadalom, formatervezési minta, BME affiliáció nélkül'),

        #TODO: BME-hez affiliált közleményekre és a BME-hez nem affiliált közleményekre
        ScoringToken('CIT-IND,5YR,WOS,BME', 1.0, 'WoS adatbázisban megtalálható idézet, 5 éves, BME-hez affiliált közleményre'),
        ScoringToken('CIT-IND,5YR,SCOPUS,BME', 1.0, 'Scopus adatbázisban megtalálható idézet, 5 éves, BME-hez affiliált közleményre'),
        ScoringToken('CIT-IND,5YR,W+S,BME', 1.0, 'WoS vagy Scopus adatbázisban megtalálható idézet, 5 éves, BME-hez affiliált közleményre'),
        ScoringToken('CIT-IND,5YR,WOS,NoBME', 1.0, 'WoS adatbázisban megtalálható idézet, 5 éves, BME-hez nem affiliált közleményre'),
        ScoringToken('CIT-IND,5YR,SCOPUS,NoBME', 1.0, 'Scopus adatbázisban megtalálható idézet, 5 éves, BME-hez nem affiliált közleményre'),
        ScoringToken('CIT-IND,5YR,W+S,NoBME', 1.0, 'WoS vagy Scopus adatbázisban megtalálható idézet, 5 éves, BME-hez nem affiliált közleményre'),

        ScoringToken('NEMPONTOZOTT', 0.0, 'A pontozásban nem szerepel'),
        ScoringToken('HIBASARANY', 0.0, 'Közlemények hibás vagy hiányos szerzői részaránnyal'),
        ScoringToken('ERROR', 0.0, 'Hibakezelés'),
    ]

    def set_params_default(self):
        """Set scoring instance parameters' default values"""

        params = super().set_params_default()
        params['year_count'] = 5

        return params

    def set_params(self, _params):
        """Set scoring instance parameters. Returns the params and a list of warnings or empty list is all checks passed."""

        _warnings = []

        # convert parameter types
        year_count = None
        if 'year_count' in _params:
            try:
                year_count = (int)(_params['year_count'])
                _params['year_count'] = year_count
            except ValueError:
                _warnings.append('Az évek száma nem egész számként került megadásra: %s'%(_params['year_count']))
        else:
            year_count = self.params['year_count']

        if 'year' in _params and isinstance(year_count, int):
            try:
                _year = (int)(_params['year'])
                _params['year_from'] = _year - year_count + 1
                _params['year_to'] = _year
            except ValueError:
                _warnings.append('Az értékelés záró éve nem egész számként került megadásra: %s'%(_params['year']))

        (_params_from_parent, _warnings_from_parent) = super().set_params(_params)

        _warnings.extend(_warnings_from_parent)

        return (self.params, _warnings)

    @classmethod
    def check_params(cls, view, params):
        """check the content of params dictionary for scoring view given in view. vies should take one of list/detail/adhoc
        Return the list of error messages or an empty list if no errors found.
        """
        msg = PUB_UTIL.check_params(view, params)

        if view in [TUDRIPORT_VIEW_TYPE_LIST, TUDRIPORT_VIEW_TYPE_DETAIL] and params.get('year') is None:
            msg.append('Nem adta meg az év értékelési paramétert, kérjük, írja be vagy válassza ki az évet (az év megadása az értékelési periódus záróévét jelöli ki).')

        return msg

    # és itt írjuk meg a függvényt, amely egy-egy közleményrekordból részpontszámot számol
    def kategorizalas(self, mtmt_id, published, supervisor_mtmt):
        token = ''
        tokenkieg = ''
        debuginfo = ''
        pubid = published.publication.mtmt_pubid
        type_name = published.publication.type.type_name
        subtype_name = published.publication.typesubtype.subtype_name
        jelleg = published.publication.character.name
        full_scientific = published.publication.is_full_scientific
        authorcount = published.publication.authorcount
        #Szerző típusa
        author_type = published.authortype.name
        #BME affiliáció megvan?
        has_BME_affiliation = published.has_author_affiliation_BME

        wosdb = published.wosdb
        besorolas = published.publication.sjr_rank
        scopusdb =  published.scopusdb or besorolas in ['D1', 'Q1', 'Q2', 'Q3', 'Q4']
        share = 0
        if authorcount == 0:
            share = 0
        else:
            share = 1./authorcount

        affiliationTokenSuffix = 'BME' if has_BME_affiliation else 'NoBME'

        if jelleg == 'tudományos':
            if full_scientific and author_type == 'author':
                self.extraInfo['listScientificPublications%s'%(affiliationTokenSuffix)].append(pubid)
                # itt megadunk tokent, amit a következő részek felülbírálhatnak
                token = 'TUD,noScopus,%s'%(affiliationTokenSuffix)
                if scopusdb:
                    self.extraInfo['listScopusPublications%s'%(affiliationTokenSuffix)].append(pubid)
                    token = 'TUD,Scopus,%s'%(affiliationTokenSuffix)

            # folyóiratcikk, D1, Q1..Q4
            if type_name == 'folyóiratcikk' and full_scientific and author_type == 'author':
                if besorolas in ['D1', 'Q1']:
                    if has_BME_affiliation:
                        self.extraInfo['listSumD1Q1PublicationsBME'].append(pubid)
                        self.extraInfo['sumShareInD1Q1BME'] += share * (2 if besorolas == 'D1' else 1)
                    else:
                        self.extraInfo['listSumD1Q1PublicationsNoBME'].append(pubid)

                if besorolas == 'D1':
                    token = 'FOLY,D1,%s'%(affiliationTokenSuffix)
                elif besorolas == 'Q1':
                    token = 'FOLY,Q1,%s'%(affiliationTokenSuffix)
                elif besorolas == 'Q2':
                    token = 'FOLY,Q2,%s'%(affiliationTokenSuffix)
                elif besorolas == 'Q3':
                    token = 'FOLY,Q3,%s'%(affiliationTokenSuffix)
                elif besorolas == 'Q4':
                    token = 'FOLY,Q4,%s'%(affiliationTokenSuffix)

            # szabadalmak
            elif type_name in ['oltalmi formák'] and subtype_name in ['usa szabadalom', 'európai szabadalom', 'nemzetközi szabadalom', 'mintaoltalom'] and author_type == 'author':
                token = 'SZABADALOM,%s'%(affiliationTokenSuffix)

        else:
            token = 'NEMPONTOZOTT'
        if token == '':
            token = 'NEMPONTOZOTT'

        return (pubid, token, tokenkieg, share, debuginfo)

    def nullCounters(self):
        self.extraInfo['numScientificPublicationsBME'] = 0
        self.extraInfo['listScientificPublicationsBME'] = []
        self.extraInfo['numScientificPublicationsNoBME'] = 0
        self.extraInfo['listScientificPublicationsNoBME'] = []
        self.extraInfo['numScopusPublicationsBME'] = 0
        self.extraInfo['listScopusPublicationsBME'] = []
        self.extraInfo['numScopusPublicationsNoBME'] = 0
        self.extraInfo['listScopusPublicationsNoBME'] = []
        self.extraInfo['numSumD1Q1PublicationsBME'] = 0
        self.extraInfo['listSumD1Q1PublicationsBME'] = []
        self.extraInfo['numSumD1Q1PublicationsNoBME'] = 0
        self.extraInfo['listSumD1Q1PublicationsNoBME'] = []
        self.extraInfo['sumShareInD1Q1BME'] = 0.0

    def citations_monitoring(self, pubrefs):
        citlist = []
        for pubref in pubrefs:
            affiliationTokenSuffix = 'BME' if hasattr(pubref, 'has_author_affiliation_BME') and pubref.has_author_affiliation_BME else 'NoBME'

            citlist.append( (pubref.publication_id, 'CIT-IND,5YR,WOS,%s'%(affiliationTokenSuffix), pubref.independent_wos, 1. if pubref.independent_wos > 0 else 0., pubref.independent_wos_list) )
            citlist.append( (pubref.publication_id, 'CIT-IND,5YR,SCOPUS,%s'%(affiliationTokenSuffix), pubref.independent_scopus, 1. if pubref.independent_scopus > 0 else 0., pubref.independent_scopus_list ) )
            # 'CIT-IND,5YR,W+S,(No)BME': WOS es SCOPUS idezesek unioja
            cit_w_s = set()
            if pubref.independent_wos > 0:
                [cit_w_s.add(c.strip()) for c in pubref.independent_wos_list.split(',')]
            if pubref.independent_scopus > 0:
                [cit_w_s.add(c.strip()) for c in pubref.independent_scopus_list.split(',')]
            citlist.append( (pubref.publication_id, 'CIT-IND,5YR,W+S,%s'%(affiliationTokenSuffix), len(cit_w_s), 1. if len(cit_w_s) > 0 else 0., ','.join(cit_w_s) ) )
        return citlist

    # Fontos egyedi függvény, a pub_util_riportgen() ezt hívja meg
    def riportgen(self, mtmt_id, dbdatetime, publisheds, pubrefs, supervisor_mtmt):
        self.nullCounters()
        mtmt_pubauthorname = publisheds[0].author_db.authorname if len(publisheds) > 0 else ''
        alltoken = []
        for published in publisheds:
            alltoken.append(self.kategorizalas(mtmt_id, published, supervisor_mtmt))
        alltoken += self.citations_monitoring(pubrefs)
        #print (tokendict) # statisztika
        fejlec = {'mtmt_id': mtmt_id, 'mtmt_name': mtmt_pubauthorname }
        return fejlec, alltoken, self.extraInfo.copy()

    def riportgen_publication(self, dbdatetime, published, pubrefs, supervisor_mtmt):
        self.nullCounters()
        alltoken = []
        token = self.kategorizalas(-1, published, supervisor_mtmt)
        alltoken.append(token)
        alltoken += self.citations_monitoring(pubrefs)
        #print (tokendict) # statisztika
        fejlec = {'talalat_token': token[1] }
        return fejlec, alltoken, self.extraInfo.copy()

    def transform_extraInfo(self, extraInfo, totalScore):
        for k in [
            'ScientificPublicationsBME',
            'ScientificPublicationsNoBME',
            'ScopusPublicationsBME',
            'ScopusPublicationsNoBME',
            'SumD1Q1PublicationsBME',
            'SumD1Q1PublicationsNoBME',
        ]:
            extraInfo['num%s'%(k)] = len(extraInfo['list%s'%(k)])

        return extraInfo

    def aggregate(self):
        # For empty aggregation call, we return empty aggregation
        if self.summary is None:
            return None

        # ...NoBME sets in the summary should not contain any items that are for BME for anyone in the detailed list
        for k in [
            'TUD,noScopus',
            'TUD,Scopus',
            'FOLY,D1',
            'FOLY,Q1',
            'FOLY,Q2',
            'FOLY,Q3',
            'FOLY,Q4',
            'SZABADALOM',
            'CIT-IND,5YR,WOS',
            'CIT-IND,5YR,SCOPUS',
            'CIT-IND,5YR,W+S',
        ]:
            _keyNoBME = '%s,NoBME'%(k)
            _keyBME = '%s,BME'%(k)
            _pubSetBME = set(self.summary['reszeredmenyek'][_keyBME]['pubids'])
            _pubSetNoBME = set(self.summary['reszeredmenyek'][_keyNoBME]['pubids'])
            self.summary['reszeredmenyek'][_keyNoBME]['pubids'] = list(_pubSetNoBME.difference(_pubSetBME))

            _citSetBME = set(self.summary['reszeredmenyek'][_keyBME]['citids'])
            _citSetNoBME = set(self.summary['reszeredmenyek'][_keyNoBME]['citids'])
            self.summary['reszeredmenyek'][_keyNoBME]['citids'] = list(_citSetNoBME.difference(_citSetBME))


        for k in [
            'ScientificPublications',
            'ScopusPublications',
            'SumD1Q1Publications',
        ]:
            _setBME = set(self.summary['extraInfo']['list%sBME'%(k)])
            _setNoBME = set(self.summary['extraInfo']['list%sNoBME'%(k)])
            self.summary['extraInfo']['list%sNoBME'%(k)] = list(_setNoBME.difference(_setBME))

        PUB_UTIL.aggregate(self)

        if self.aggregate_extraInfo and 'extraInfo' in self.summary:
            self.summary['extraInfo'] = self.transform_extraInfo(self.summary['extraInfo'], None)

        return self.summary

    def filter_for_year_publisheds(self, year, publisheds):
        if year is not None:
            publisheds = publisheds.filter(pubdate__range=(self.params['year_from'], self.params['year_to']))
        return publisheds

    def filter_for_year_pubrefs(self, year, pubrefs):
        if year is not None:
            pubrefs = pubrefs.filter(year__range=(self.params['year_from'], self.params['year_to']))
        return pubrefs

    def annotate_pubrefs(self, pubrefs, publisheds):
        pubrefs = PUB_UTIL.annotate_pubrefs(self, pubrefs, publisheds)

        related_published = publisheds.all().filter(publication_id=OuterRef("publication_id"))

        return pubrefs.annotate(has_author_affiliation_BME=Subquery(related_published.values("has_author_affiliation_BME")[:1]))
