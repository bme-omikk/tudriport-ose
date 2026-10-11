import math

from riport.models.external import ExtAuthorlist
from .scoring_token import ScoringToken
from .pub_util import PUB_UTIL
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F


class RIPORT(PUB_UTIL):
    """GTK PhD pontozó.
    A GTK docensi és a GTK habilitációs pontozó ennek a paraméterezésével nyerhető.
    """
    def __init__(self, p_publicationPointTreshold=20, p_max3ScoreCap=5.0, p_constraintMultiplier=1, p_ignoreSupervisor=True):
        PUB_UTIL.__init__(self, False)
        # minimumkövetelmények/extrainfó számításához
        self.extraInfo = {
            'numWOSPublications': 0,
            'numScopusPublications': 0,
            'ScopusPublicationPubids': [],
            'numScopusQ1': 0,
            'WosUNIONScopusPublicationPubids': [],
            'publicationPointThreshold': p_publicationPointTreshold,
            'max3ScoreCap': p_max3ScoreCap,
            'constraintMultiplier': p_constraintMultiplier,
            'ignoreSupervisor': p_ignoreSupervisor,
        }

    TOKENLIST = [
        ScoringToken('FOLY,LEK,MAGY,NEMKI', 2.0, 'Folyóiratcikk: Lektorált, Nem kiemelt - magyar nyelven', False),
        ScoringToken('FOLY,LEK,MAGY,A', 7.0, 'Folyóiratcikk: Lektorált, Kiemelt A - magyar nyelven'),
        ScoringToken('FOLY,LEK,MAGY,B', 6.0, 'Folyóiratcikk: Lektorált, Kiemelt B - magyar nyelven'),
        ScoringToken('FOLY,LEK,MAGY,C', 5.0, 'Folyóiratcikk: Lektorált, Kiemelt C - magyar nyelven'),
        ScoringToken('FOLY,LEK,MAGY,D', 4.0, 'Folyóiratcikk: Lektorált, Kiemelt D - magyar nyelven'),

        ScoringToken('FOLY,LEK,IDEG,HAZA,NEMKI', 3.0, 'Folyóiratcikk: Lektorált, Hazai, nem WoS, nem D1,Q1-Q4, Nem kiemelt - idegen nyelven'),
        ScoringToken('FOLY,LEK,IDEG,HAZA,A', 7.0, 'Folyóiratcikk: Lektorált, Hazai, nem WoS, nem D1,Q1-Q2, Kiemelt A - idegen nyelven'),
        ScoringToken('FOLY,LEK,IDEG,HAZA,B', 6.0, 'Folyóiratcikk: Lektorált, Hazai, nem WoS, nem D1,Q1-Q3, Kiemelt B - idegen nyelven'),
        ScoringToken('FOLY,LEK,IDEG,HAZA,C', 5.0, 'Folyóiratcikk: Lektorált, Hazai, nem WoS, nem D1,Q1-Q4, Kiemelt C - idegen nyelven'),
        ScoringToken('FOLY,LEK,IDEG,HAZA,D', 4.0, 'Folyóiratcikk: Lektorált, Hazai, nem WoS, nem D1,Q1-Q4, Kiemelt D - idegen nyelven'),

        ScoringToken('FOLY,LEK,IDEG,KULF,NEMKI', 3.0, 'Folyóiratcikk: Lektorált, Külföldi - idegen nyelven'),
        ScoringToken('FOLY,LEK,IDEG,WOS', 8.0, 'Folyóiratcikk: Lektorált, kiemelt WOS - idegen nyelven (nem D1, nem Q1)'),
        ScoringToken('FOLY,LEK,IDEG,SCOPUS,D1', 12.0, 'Folyóiratcikk: Lektorált, kiemelt SCOPUS D1 - idegen nyelven'),
        ScoringToken('FOLY,LEK,IDEG,SCOPUS,Q1', 10.0, 'Folyóiratcikk: Lektorált, kiemelt SCOPUS Q1 (nem D1) - idegen nyelven'),
        ScoringToken('FOLY,LEK,IDEG,SCOPUS,Q2', 8.0, 'Folyóiratcikk: Lektorált, kiemelt SCOPUS Q2 - idegen nyelven (nem WoS)'),
        ScoringToken('FOLY,LEK,IDEG,SCOPUS,Q3', 6.0, 'Folyóiratcikk: Lektorált, kiemelt SCOPUS Q3 - idegen nyelven (nem WoS)'),
        ScoringToken('FOLY,LEK,IDEG,SCOPUS,Q4', 5.0, 'Folyóiratcikk: Lektorált, kiemelt SCOPUS Q4 - idegen nyelven (nem WoS)'),

        ScoringToken('FOLY,NEMLEK,MAGY', 1.0, 'Folyóiratcikk: Nem lektorált - magyar nyelven', False),
        ScoringToken('FOLY,NEMLEK,IDEG', 1.0, 'Folyóiratcikk: Nem lektorált - idegen nyelven', False),

        ScoringToken('KONF,MAGYAR', 1.0, 'Konferenciacikk - magyar nyelven', False),
        ScoringToken('KONF,IDEG,NEMZ', 3.0, 'Konferenciacikk: Nemzetközileg megjelent - idegen nyelven'),
        ScoringToken('KONF,IDEG,HAZA', 2.0, 'Konferenciacikk: Hazai megjelenésű - idegen nyelven', False),
        ScoringToken('KONF,EGYEB,MAGYAR', 1.0, 'Egyéb Konferenciacikk - magyar nyelven', False),
        ScoringToken('KONF,EGYEB,IDEG,NEMZ', 3.0, 'Egyéb Konferenciacikk: Nemzetközileg megjelent - idegen nyelven'),
        ScoringToken('KONF,EGYEB,IDEG,HAZA', 2.0, 'Egyéb Konferenciacikk: Hazai megjelenésű - idegen nyelven', False),

        ScoringToken('RECENZIO,MAGY', 1.0, 'Recenzió - magyar nyelven', False),
        ScoringToken('RECENZIO,IDEG', 1.0, 'Recenzió - idegen nyelven', False),

        ScoringToken('KONYV,ISBN,MAGY', 0.125, 'Könyv ISBN számmal: Magyar nyelven'),
        ScoringToken('KONYV,ISBN,IDEG,HAZA', 0.125, 'Könyv ISBN számmal: Idegen nyelven'),
        ScoringToken('KONYV,ISBN,IDEG,NEMZ', 0.125, 'Könyv ISBN számmal: Idegen nyelven'),

        ScoringToken('KONYV,NEMISBN,MAGY', 0.125, 'Könyv ISBN szám nélkül: Magyar nyelven'),
        ScoringToken('KONYV,NEMISBN,IDEG,HAZA', 0.125, 'Könyv ISBN szám nélkül: Idegen nyelven'),
        ScoringToken('KONYV,NEMISBN,IDEG,NEMZ', 0.125, 'Könyv ISBN szám nélkül: Idegen nyelven'),

        ScoringToken('TKJEGYZ,ISBN,MAGY', 0.0625, 'Tankönyv, jegyzet ISBN számmal - magyar nyelven'),
        ScoringToken('TKJEGYZ,ISBN,IDEG', 0.0625, 'Tankönyv, jegyzet ISBN számmal - idegen nyelven'),
        ScoringToken('TKJEGYZ,NEMISBN,MAGY', 0.0625, 'Tankönyv, jegyzet ISBN nélkül - magyar nyelven'),
        ScoringToken('TKJEGYZ,NEMISBN,IDEG', 0.0625, 'Tankönyv, jegyzet ISBN nélkül - idegen nyelven'),

        ScoringToken('MAX3->MAX5', 1.0, 'legfeljebb 3 pontos közleményekből elszámolt pontszám (legfeljebb 5)'),

        ScoringToken('CIT-IND,WOS', 5.0, 'SCI adatbázisban megtalálható adott évben idézett'),
        ScoringToken('CIT-IND,SCOPUS', 5.0, 'SCI adatbázisban megtalálható adott évben idézett'),
        ScoringToken('CIT-IND,W+S', 5.0, 'SCI adatbázisban megtalálható adott évben idézett'),
        ScoringToken('NEMPONTOZOTT,KIFOGASOLHATO', 0.0, 'A pontozásban nem szerepel, MTMT kifogásolható gyakorlatot folytató folyóiratban jelentek meg'),
        ScoringToken('NEMPONTOZOTT,UTANKOZLES,IDEG', 0.0, 'A pontozásban nem szerepel, WoS/Scopus indexált, \'Utánközlés\' besorolású, idegen nyelvű folyóiratcikk'),
        ScoringToken('NEMPONTOZOTT,TOVABBI', 0.0, 'A pontozásban nem szereplő, további'),
        ScoringToken('HIBASARANY', 0.0, 'Közlemények hibás vagy hiányos szerzői részaránnyal'),
        ScoringToken('ERROR', 0.0, 'Hibakezelés'),
    ]

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
            # heurisztika: ahol ki van töltve a témavezető MTMT azonosítója, az kerül elölre
            # determinisztikus rendezés a végére
            _author_obj = _author_obj.order_by(F('supervisor_mtmt_authid').asc(nulls_first=False), 'id')
            author_to_score = _author_obj.first()
        except ObjectDoesNotExist:
            author_to_score = ExtAuthorlist(mtmtcode=mtmt_id)

        return author_to_score

    # és itt írjuk meg a függvényt, amely egy-egy közleményrekordból részpontszámot számol
    def kategorizalas(self, mtmt_id, published, supervisor_mtmt):
        token = ''
        tokenkieg = ''
        debuginfo = ''
        pubid = published.publication.mtmt_pubid
        type_name = published.publication.type.type_name
        subtype_name = published.publication.typesubtype.subtype_name
        jelleg = published.publication.character.name        
        lektoralt = published.publication.peerreviewed
        mta_listan_nullas = published.publication.mta_listed_zero
        oldalszam = published.publication.pagenum
        if oldalszam is None:
            oldalszam = 0
        authorcount = published.publication.authorcount
        #Nyelv
        magyar = published.publication.language.is_hungarian
        #Hely
        hazai = not published.publication.is_foreign_publication
        kulfoldi = published.publication.is_foreign_publication
        #Szerző típusa
        author_type = published.authortype.name
        wosdb = published.wosdb       
        besorolas = published.publication.sjr_rank
        scopusdb =  published.scopusdb or besorolas in ['D1', 'Q1', 'Q2', 'Q3', 'Q4']
        has_isbn = published.has_isbn
        MTA = published.publication.mta_rank
        share = 0
        if jelleg == 'tudományos' and not mta_listan_nullas:
            # --- GTK PhD 1. folyóiratcikk
            if type_name == 'folyóiratcikk' and subtype_name in ['szakcikk', 'összefoglaló cikk', 'rövid közlemény', 'sokszerzős vagy csoportos szerzőségű szakcikk', 'forráskiadás', 'műkritika', 'esszé'] and author_type == 'author':                
                debuginfo = 'GTK - folyóirat (%s oldal)'%oldalszam  
                if lektoralt:                
                    if magyar:
                        if MTA == 'A':
                            token = 'FOLY,LEK,MAGY,A'
                        elif MTA == 'B':
                            token = 'FOLY,LEK,MAGY,B'
                        elif MTA == 'C': 
                            token = 'FOLY,LEK,MAGY,C'
                        elif MTA == 'D':
                            token = 'FOLY,LEK,MAGY,D' 
                        else:
                            token = 'FOLY,LEK,MAGY,NEMKI'
                    else:
                        if   hazai and not wosdb and MTA == 'A' and besorolas not in ['D1', 'Q1', 'Q2']:
                            token = 'FOLY,LEK,IDEG,HAZA,A'
                        elif hazai and not wosdb and MTA == 'B' and besorolas not in ['D1', 'Q1', 'Q2', 'Q3']:
                            token = 'FOLY,LEK,IDEG,HAZA,B'
                        elif hazai and not wosdb and MTA == 'C' and besorolas not in ['D1', 'Q1', 'Q2', 'Q3', 'Q4']:
                            token = 'FOLY,LEK,IDEG,HAZA,C'
                        elif hazai and not wosdb and MTA == 'D' and besorolas not in ['D1', 'Q1', 'Q2', 'Q3', 'Q4']:
                            token = 'FOLY,LEK,IDEG,HAZA,D'
                        elif hazai and not wosdb and not MTA and not besorolas:
                            token = 'FOLY,LEK,IDEG,HAZA,NEMKI'
                        elif kulfoldi and not wosdb and not besorolas:
                            token = 'FOLY,LEK,IDEG,KULF,NEMKI'
                        # ha "besorolas not in ['D1', 'Q1']", akkor vagy nem Scopusos a közlemény, vagy ha az, akkor se nem D1, se nem Q1
                        elif wosdb and besorolas not in ['D1','Q1']:
                            token = 'FOLY,LEK,IDEG,WOS'
                        elif scopusdb and besorolas == 'D1':
                            token = 'FOLY,LEK,IDEG,SCOPUS,D1'
                        elif scopusdb and besorolas == 'Q1':
                            token = 'FOLY,LEK,IDEG,SCOPUS,Q1'
                        elif scopusdb and besorolas == 'Q2':
                            token = 'FOLY,LEK,IDEG,SCOPUS,Q2'
                        elif scopusdb and besorolas == 'Q3':
                            token = 'FOLY,LEK,IDEG,SCOPUS,Q3'
                        elif scopusdb and besorolas == 'Q4':
                            token = 'FOLY,LEK,IDEG,SCOPUS,Q4'
                        # a minimumkövetelményeknél a Scopus-os közleményt függetlenül számoljuk attól, hogy a WoS-ban megjelenik-e
                        if wosdb:
                            self.extraInfo['numWOSPublications'] += 1
                        if scopusdb:
                            self.extraInfo['numScopusPublications'] += 1
                            self.extraInfo['ScopusPublicationPubids'].append(pubid)
                            if besorolas in ['D1','Q1']:
                                self.extraInfo['numScopusQ1'] += 1
                        if wosdb or scopusdb:
                            self.extraInfo['WosUNIONScopusPublicationPubids'].append(pubid)
                else:
                    if magyar:
                        token = 'FOLY,NEMLEK,MAGY'
                    else:
                        token = 'FOLY,NEMLEK,IDEG'  

            # --- GTK PhD 2. konferenciaközlemény     
            elif type_name in ['folyóiratcikk', 'könyvrészlet'] and subtype_name == 'konferenciaközlemény' and author_type == 'author':
                if oldalszam >= 4:
                    if magyar:
                        token = 'KONF,MAGYAR'
                    else:
                        if hazai:
                            token = 'KONF,IDEG,HAZA'
                        elif kulfoldi:
                            token = 'KONF,IDEG,NEMZ'    
        
            elif type_name == 'egyéb konferenciaközlemény' and subtype_name == 'konferenciaközlemény' and author_type == 'author':
                if oldalszam >= 4:
                    if magyar:
                        token = 'KONF,EGYEB,MAGYAR'
                    else:
                        if hazai:
                            token = 'KONF,EGYEB,IDEG,HAZA'
                        elif kulfoldi:
                            token = 'KONF,EGYEB,IDEG,NEMZ'   

            # --- GTK PhD 4. Recenzió
            elif type_name in ['folyóiratcikk', 'könyvrészlet'] and subtype_name == 'recenzió/kritika' and author_type == 'author':            
                debuginfo = 'GTK 4.- Recenzió (%s oldal)'%oldalszam
                if magyar:
                    token = 'RECENZIO,MAGY'
                else:
                    token = 'RECENZIO,IDEG'
            # --- GTK PhD 5. Könyv
            elif (type_name == 'könyv' and subtype_name in ['szakkönyv', 'monográfia', 'tanulmánykötet', 'kézikönyv', 'műhelytanulmány'] and author_type == 'author') \
                or (type_name == 'könyvrészlet' and subtype_name in ['szaktanulmány', 'könyvfejezet', 'műhelytanulmány része']) and author_type == 'author':
                    debuginfo = 'GTK 5.- Könyv (%s oldal)'%oldalszam
                    tokenkieg = min(oldalszam, 64*authorcount)
                    if has_isbn:
                        if magyar:
                            token = 'KONYV,ISBN,MAGY'
                        else:
                            if hazai:
                                token = 'KONYV,ISBN,IDEG,HAZA'
                            elif kulfoldi:
                                token = 'KONYV,ISBN,IDEG,NEMZ'
                    else:
                        if magyar:
                            token = 'KONYV,NEMISBN,MAGY'
                        else:
                            if hazai:
                                token = 'KONYV,NEMISBN,IDEG,HAZA'
                            elif kulfoldi:
                                token = 'KONYV,NEMISBN,IDEG,NEMZ'                

        elif jelleg == 'oktatási' and not mta_listan_nullas:
            tokenkieg = min(oldalszam, 64*authorcount)
            if (type_name == 'könyv' and subtype_name in ['felsőoktatási tankönyv', 'oktatási anyag']) \
                or (type_name == 'könyvrészlet' and subtype_name in ['felsőoktatási tankönyv része', 'oktatási anyag része']):
                if author_type == 'author':
                    if has_isbn:
                        if magyar:
                            token = 'TKJEGYZ,ISBN,MAGY'
                        else:
                            token = 'TKJEGYZ,ISBN,IDEG'
                    else:
                        if magyar:
                            token = 'TKJEGYZ,NEMISBN,MAGY'
                        else:
                            token = 'TKJEGYZ,NEMISBN,IDEG'              
            
        if token == '':
            if mta_listan_nullas:
                token = 'NEMPONTOZOTT,KIFOGASOLHATO'
            elif type_name == 'folyóiratcikk' and subtype_name == 'utánközlés' and jelleg == 'tudományos' and author_type == 'author' and not magyar and (wosdb or scopusdb):
                token = 'NEMPONTOZOTT,UTANKOZLES,IDEG'
            else:
                token = 'NEMPONTOZOTT,TOVABBI'


        if self.extraInfo['ignoreSupervisor']:
            supervisor_pubauthor = self.get_supervisor_pubauthor(published, supervisor_mtmt)
            if supervisor_pubauthor:
                authorcount -= 1

        if authorcount == 0:
            share = 0
        else:
            share = 1./authorcount

        return (pubid, token, tokenkieg, share, debuginfo)

    def nullCounters(self):
        self.extraInfo['numWOSPublications'] = 0
        self.extraInfo['numScopusPublications'] = 0
        self.extraInfo['ScopusPublicationPubids'] = []
        self.extraInfo['numScopusQ1'] = 0
        self.extraInfo['WosUNIONScopusPublicationPubids'] = []

    def citations_gtk(self, pubrefs):
        citlist = []
        for pubref in pubrefs:
            citlist.append( (pubref.publication_id, 'CIT-IND,WOS', pubref.independent_wos, 1. if pubref.independent_wos > 0 else 0., pubref.independent_wos_list) )
            citlist.append( (pubref.publication_id, 'CIT-IND,SCOPUS', pubref.independent_scopus, 1. if pubref.independent_scopus > 0 else 0., pubref.independent_scopus_list ) )
            # 'CIT-IND,W+S': WOS es SCOPUS idezesek unioja
            cit_w_s = set()
            if pubref.independent_wos > 0:
                [cit_w_s.add(c.strip()) for c in pubref.independent_wos_list.split(',')]
            if pubref.independent_scopus > 0:
                [cit_w_s.add(c.strip()) for c in pubref.independent_scopus_list.split(',')]
            citlist.append( (pubref.publication_id, 'CIT-IND,W+S', len(cit_w_s), 1. if len(cit_w_s) > 0 else 0., ','.join(cit_w_s) ) )
        return citlist

    # Fontos egyedi függvény, a pub_util_riportgen() ezt hívja meg
    def riportgen(self, mtmt_id, dbdatetime, publisheds, pubrefs, supervisor_mtmt):
        self.nullCounters()
        mtmt_pubauthorname = publisheds[0].author_db.authorname if len(publisheds) > 0 else ''        
        alltoken = []
        for published in publisheds:
            alltoken.append(self.kategorizalas(mtmt_id, published, supervisor_mtmt))            
        alltoken += self.citations_gtk(pubrefs)
        #print (tokendict) # statisztika
        fejlec = {'mtmt_id': mtmt_id, 'mtmt_name': mtmt_pubauthorname }        
        return fejlec, alltoken, self.extraInfo.copy()

    def riportgen_publication(self, dbdatetime, published, pubrefs, supervisor_mtmt):
        self.nullCounters()  
        alltoken = []
        token = self.kategorizalas(-1, published, supervisor_mtmt)
        alltoken.append(token)
        alltoken += self.citations_gtk(pubrefs)
        #print (tokendict) # statisztika
        fejlec = {'talalat_token': token[1] }
        return fejlec, alltoken, self.extraInfo.copy()

    def transform_tokendict(self, tokendict):
        # types in the following list (those with less than 3 points)
        # contribute at most extraInfo['max3ScoreCap'] to the summarized score
        LIST = ['FOLY,LEK,MAGY,NEMKI', 'FOLY,NEMLEK,MAGY', 'FOLY,NEMLEK,IDEG', 'KONF,MAGYAR', 'KONF,IDEG,HAZA', 'KONF,EGYEB,MAGYAR', 'KONF,EGYEB,IDEG,HAZA', 'RECENZIO,MAGY', 'RECENZIO,IDEG']        
        sum = 0.0
        for token_to_transfrom in LIST:
            if token_to_transfrom in tokendict:
                sum+=tokendict[token_to_transfrom][0]*self.TOKENEK[token_to_transfrom].score  
        if sum > 0.0:
            max3ScoreCapped = min(self.extraInfo['max3ScoreCap'],sum)
            tokendict['MAX3->MAX5'] = [max3ScoreCapped, None, 0, [], [], [str(round(max3ScoreCapped,2))]]
        return tokendict

    def transform_extraInfo(self, extraInfo, totalScore):
        """GTK PhD alapú pontozók minimumkövetelmény-teljesülések számítása"""
        cm = extraInfo['constraintMultiplier']

        extraInfo['constraint1Passed'] = extraInfo['numWOSPublications'] >= 1*cm and extraInfo['numScopusPublications'] >= 1*cm and len(extraInfo['WosUNIONScopusPublicationPubids']) >= 2*cm
        extraInfo['constraint2Passed'] = extraInfo['numScopusPublications'] >= 2*cm and extraInfo['numScopusQ1'] >= 1*cm
        extraInfo['constraint3Passed'] = totalScore >= extraInfo['publicationPointThreshold']
        extraInfo['constraintsAllPassed'] = extraInfo['constraint3Passed'] and (extraInfo['constraint1Passed'] or extraInfo['constraint2Passed'])

        return extraInfo
