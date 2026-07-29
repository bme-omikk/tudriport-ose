import math

from django.core.exceptions import ObjectDoesNotExist

from common.constants import TUDRIPORT_VIEW_TYPE_LIST, TUDRIPORT_VIEW_TYPE_DETAIL, TUDRIPORT_VIEW_TYPE_ADHOC

from .scoring_token import ScoringToken
from .pub_util import PUB_UTIL
from riport.models.external import Published, AuthorDb, Pubauthors, Container

class RIPORT(PUB_UTIL):
    """GTK TÉR (teljesítményértékelés) pontozó."""
    def __init__(self):
        PUB_UTIL.__init__(self, True)

    TOKENLIST = [
        ScoringToken('KONF,HAZA,MAGY', 1.0, 'Konferencia, kongresszusi előadás, poszterkivonatok - Hazai rendezvényen - magyar nyelven'),
        ScoringToken('KONF,HAZA,IDEG', 2.0, 'Konferencia, kongresszusi előadás, poszterkivonatok - Hazai rendezvényen - idegen nyelven'),
        ScoringToken('KONF,KULF,IDEG', 3.0, 'Konferencia, kongresszusi előadás, poszterkivonatok - Nemzetközi rendezvényen - idegen nyelven'),

        ScoringToken('FOLY,LEK,MAGY,NEMKI', 2.0, 'Folyóiratcikk: Lektorált, Nem kiemelt - magyar nyelven'),
        ScoringToken('FOLY,LEK,MAGY,A', 7.0, 'Folyóiratcikk: Lektorált, Kiemelt A - idegen nyelven'),
        ScoringToken('FOLY,LEK,MAGY,B', 6.0, 'Folyóiratcikk: Lektorált, Kiemelt B - idegen nyelven'),
        ScoringToken('FOLY,LEK,MAGY,C', 5.0, 'Folyóiratcikk: Lektorált, Kiemelt C - idegen nyelven'),
        ScoringToken('FOLY,LEK,MAGY,D', 4.0, 'Folyóiratcikk: Lektorált, Kiemelt D - idegen nyelven'),

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

        ScoringToken('FOLY,NEMLEK,MAGY', 1.0, 'Folyóiratcikk: Nem lektorált - magyar nyelven'),
        ScoringToken('FOLY,NEMLEK,IDEG', 1.0, 'Folyóiratcikk: Nem lektorált - idegen nyelven'),

        ScoringToken('FOLY,LEK,NEMTELJ,MAGY', 1.0, 'Folyóiratcikk: Lektorált, nem teljes - magyar nyelven'), 
        ScoringToken('FOLY,LEK,NEMTELJ,IDEG', 2.0, 'Folyóiratcikk: Lektorált, nem teljes - idegen nyelven'),  

        ScoringToken('KONF,MAGYAR', 1.0, 'Konferenciacikk - magyar nyelven'),
        ScoringToken('KONF,IDEG,NEMZ', 3.0, 'Konferenciacikk: Nemzetközileg megjelent - idegen nyelven'),
        ScoringToken('KONF,IDEG,HAZA', 2.0, 'Konferenciacikk: Hazai megjelenésű - idegen nyelven'),
        ScoringToken('KONF,EGYEB,MAGYAR', 1.0, 'Egyéb Konferenciacikk - magyar nyelven'),
        ScoringToken('KONF,EGYEB,IDEG,NEMZ', 3.0, 'Egyéb Konferenciacikk: Nemzetközileg megjelent - idegen nyelven'),
        ScoringToken('KONF,EGYEB,IDEG,HAZA', 2.0, 'Egyéb Konferenciacikk: Hazai megjelenésű - idegen nyelven'),

        ScoringToken('RECENZIO,MAGY', 1.0, 'Recenzió - magyar nyelven'),
        ScoringToken('RECENZIO,IDEG', 1.0, 'Recenzió - idegen nyelven'),

        ScoringToken('KONYV,ISBN,MAGY', 2.0, 'Könyv ISBN számmal: Magyar nyelven'),
        ScoringToken('KONYV,ISBN,IDEG,HAZA', 2.0, 'Könyv ISBN számmal: Idegen nyelven'),
        ScoringToken('KONYV,ISBN,IDEG,NEMZ', 2.0, 'Könyv ISBN számmal: Idegen nyelven'),

        ScoringToken('KONYV,NEMISBN,MAGY', 2.0, 'Könyv ISBN szám nélkül: Magyar nyelven'),
        ScoringToken('KONYV,NEMISBN,IDEG,HAZA', 2.0, 'Könyv ISBN szám nélkül: Idegen nyelven'),
        ScoringToken('KONYV,NEMISBN,IDEG,NEMZ', 2.0, 'Könyv ISBN szám nélkül: Idegen nyelven'),

        ScoringToken('SZERK,MAGY', 1.0, 'Szerkesztett közlemények - magyar nyelven'),
        ScoringToken('SZERK,IDEG', 2.0, 'Szerkesztett közlemények - idegen nyelven'),


        ScoringToken('TKJEGYZ,ISBN,MAGY', 1.0, 'Tankönyv, jegyzet ISBN számmal - magyar nyelven'),
        ScoringToken('TKJEGYZ,ISBN,IDEG', 1.0, 'Tankönyv, jegyzet ISBN számmal - idegen nyelven'),
        ScoringToken('TKJEGYZ,NEMISBN,MAGY', 1.0, 'Tankönyv, jegyzet ISBN nélkül - magyar nyelven'),
        ScoringToken('TKJEGYZ,NEMISBN,IDEG', 1.0, 'Tankönyv, jegyzet ISBN nélkül - idegen nyelven'),

        ScoringToken('FOLY,NEMTUD,MAGY', 1.0, 'Nem tudományos folyóiratcikk - magyar nyelven'),
        ScoringToken('FOLY,NEMTUD,IDEG', 2.0, 'Nem tudományos folyóiratcikk - idegen nyelven'),

        ScoringToken('CIT-IND,WOS', 5.0, 'SCI adatbázisban megtalálható adott évben idézett'),
        ScoringToken('CIT-IND,SCOPUS', 5.0, 'SCI adatbázisban megtalálható adott évben idézett'),
        ScoringToken('CIT-IND,W+S', 5.0, 'SCI adatbázisban megtalálható adott évben idézett'),
        ScoringToken('NEMPONTOZOTT,GTK,KIFOGASOLHATO', 0.0, 'A pontozásban nem szereplő, GTK-hoz affiliált közlemények, MTMT kifogásolható gyakorlatot folytató folyóiratban jelentek meg'),
        ScoringToken('NEMPONTOZOTT,GTK,NEM-KIFOGASOLHATO', 0.0, 'A pontozásban nem szereplő, GTK-hoz affiliált közlemények'),
        ScoringToken('NEMPONTOZOTT,NEM-GTK,KIFOGASOLHATO', 0.0, 'GTK-hoz nem affiliált közlemények, MTMT kifogásolható gyakorlatot folytató folyóiratban jelentek meg'),
        ScoringToken('NEMPONTOZOTT,NEM-GTK,NEM-KIFOGASOLHATO', 0.0, 'GTK-hoz nem affiliált közlemények'),
        ScoringToken('ERROR', 0.0, 'Hibakezelés'),
    ]

    def set_params_default(self):
        """Set scoring instance parameters' default values"""

        params = super().set_params_default()
        params['year_count'] = 3

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

    @classmethod
    def get_world_name(cls):
        """Return the name of the world where authors are retrieved from."""
        return 'kari'

    # és itt írjuk meg a függvényt, amely egy-egy közleményrekordból részpontszámot számol
    def kategorizalas(self, mtmt_id, published, supervisor_mtmt):
        token = ''
        tokenkieg = ''
        debuginfo = ''
        calculation = '' 
        pubid = published.publication.mtmt_pubid
        type_name = published.publication.type.type_name
        subtype_name = published.publication.typesubtype.subtype_name
        jelleg = published.publication.character.name        
        idegennyelv = published.publication.language.all_non_hungarian
        lektoralt = published.publication.peerreviewed
        mta_listan_nullas = published.publication.mta_listed_zero
        oldalszam = published.publication.pagenum
        if oldalszam is None:
            oldalszam = 0
        authorcount = published.publication.authorcount
        editorcount = published.publication.editorcount
        #Nyelv
        angol = published.publication.language.contains_english
        magyar = published.publication.language.is_hungarian
        #Hely
        hazai = not published.publication.is_foreign_publication
        kulfoldi = published.publication.is_foreign_publication
        #Szerző típusa
        author_type = published.authortype.name
        wosdb = published.wosdb
        has_doi = published.has_doi
        has_full_document_url = published.has_full_document_url
        has_oa_link = published.has_oa_link
        besorolas = published.publication.sjr_rank
        scopusdb =   published.scopusdb or besorolas in ['D1', 'Q1', 'Q2', 'Q3', 'Q4']
        has_isbn = published.has_isbn
        MTA = published.publication.mta_rank
        share = 0
        if published.has_author_affiliation_BME_GTK and not mta_listan_nullas:
            if jelleg == 'tudományos':
                # --- GTK 1. konferencia, kongresszusi előadás, poszterkivonatok ---
                if type_name == 'egyéb' and subtype_name == 'nem besorolt':
                    debuginfo = 'GTK 1. konferencia, kongresszusi előadás, poszterkivonatok (%s oldal)'%oldalszam 
                    if hazai:
                        if magyar:
                            token = 'KONF,HAZA,MAGY'
                        else:
                            token = 'KONF,HAZA,IDEG'
                    elif kulfoldi:
                        token = 'KONF,KULF,IDEG'
                # --- GTK 2. folyóiratcikk
                elif type_name == 'folyóiratcikk' and subtype_name in ['szakcikk', 'összefoglaló cikk', 'rövid közlemény', 'sokszerzős vagy csoportos szerzőségű szakcikk', 'forráskiadás', 'műkritika', 'esszé'] and author_type == 'author':                
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
                    else:
                        if magyar:
                            token = 'FOLY,NEMLEK,MAGY'
                        else:
                            token = 'FOLY,NEMLEK,IDEG'

                elif type_name == 'folyóiratcikk' and subtype_name in ['nem besorolt', 'jelentés', 'hozzászólás', 'helyreigazítás', 'ismertetés', 'bibliográfia', 'repertórium', 'absztrakt/kivonat', 'personalia', 'alkalmi megemlékezés', 'utánközlés'] and author_type == 'author':
                    if magyar:
                        token = 'FOLY,LEK,NEMTELJ,MAGY'
                    else:
                        token = 'FOLY,LEK,NEMTELJ,IDEG'             


                # --- GTK 3. konferenciaközlemény     
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

                # --- GTK 4. Recenzió
                elif type_name in ['folyóiratcikk', 'könyvrészlet'] and subtype_name == 'recenzió/kritika' and author_type == 'author':            
                    debuginfo = 'GTK 4.- Recenzió (%s oldal)'%oldalszam
                    if magyar:
                        token = 'RECENZIO,MAGY'
                    else:
                        token = 'RECENZIO,IDEG'
                # --- GTK 5. Könyv
                elif (type_name == 'könyv' and subtype_name in ['szakkönyv', 'monográfia', 'tanulmánykötet', 'kézikönyv', 'műhelytanulmány'] and author_type == 'author') \
                    or (type_name == 'könyvrészlet' and subtype_name in ['szaktanulmány', 'könyvfejezet', 'műhelytanulmány része']) and author_type == 'author':
                        debuginfo = 'GTK 5.- Könyv (%s oldal)'%oldalszam
                        tokenkieg = math.floor(oldalszam/16)
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
                # --- GTK 6. Szerkesztőként
                elif author_type == 'editor':
                    debuginfo = 'GTK 6. Szerkesztőként (%s oldal)'%oldalszam
                    tokenkieg = math.floor(oldalszam/16)
                    if magyar:
                        token = 'SZERK,MAGY'
                    else:
                        token = 'SZERK,IDEG'

            elif jelleg == 'oktatási':
                tokenkieg = math.floor(oldalszam/16)
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

            elif jelleg in ['oktatási', 'nem besorolt', 'műszaki', 'művészeti', 'ismeretterjesztő', 'közérdekű'] and type_name == 'folyóiratcikk':
                if magyar:
                    token = 'FOLY,NEMTUD,MAGY'
                else:
                    token = 'FOLY,NEMTUD,IDEG'
                
            else:
                token = 'NEMPONTOZOTT,GTK,NEM-KIFOGASOLHATO'

            if token.startswith('SZERK'):
                if editorcount == 0:
                    share = 0
                else:
                    share = 1./editorcount
            else:
                if authorcount == 0:
                    share = 0
                else:
                    share = 1./authorcount

            if token == '':
                token = 'NEMPONTOZOTT,GTK,NEM-KIFOGASOLHATO'

        elif published.has_author_affiliation_BME_GTK and mta_listan_nullas:
            token = 'NEMPONTOZOTT,GTK,KIFOGASOLHATO'

        else:
            if mta_listan_nullas:
                token = 'NEMPONTOZOTT,NEM-GTK,KIFOGASOLHATO'
            else:
                token = 'NEMPONTOZOTT,NEM-GTK,NEM-KIFOGASOLHATO'

        return (pubid, token, tokenkieg, share, debuginfo)

    # Fontos egyedi függvény, a pub_util_riportgen() ezt hívja meg
    def riportgen(self, mtmt_id, dbdatetime, publisheds, pubrefs, supervisor_mtmt):
        self.nullCounters()
        mtmt_pubauthorname = publisheds[0].author_db.authorname if len(publisheds) > 0 else ''        
        alltoken = []
        for published in publisheds:
            alltoken.append(self.kategorizalas(mtmt_id, published, supervisor_mtmt))            
        
        #print (tokendict) # statisztika
        fejlec = {'mtmt_id': mtmt_id, 'mtmt_name': mtmt_pubauthorname }        
        return fejlec, alltoken, self.extraInfo.copy()

    def riportgen_publication(self, dbdatetime, published, pubrefs, supervisor_mtmt):
        self.nullCounters()
        alltoken = []
        token = self.kategorizalas(-1, published, supervisor_mtmt)
        alltoken.append(token)
        #print (tokendict) # statisztika
        fejlec = {'talalat_token': token[1] }
        return fejlec, alltoken, self.extraInfo.copy()

    def filter_for_year_publisheds(self, year, publisheds):
        if year is not None:
            publisheds = publisheds.filter(pubdate__range=(self.params['year_from'], self.params['year_to']))
        return publisheds

    def filter_for_year_pubrefs(self, year, pubrefs):
        if year is not None:
            pubrefs = pubrefs.filter(year__range=(self.params['year_from'], self.params['year_to']))
        return pubrefs
