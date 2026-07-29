import math

from .scoring_token import ScoringToken
from .pub_util import PUB_UTIL
from common.constants import EPSILON_AUTHOR_SHARE

class RIPORT(PUB_UTIL):
    """VIK PhD pontozó."""
    def __init__(self):
        PUB_UTIL.__init__(self, False)
        # minimumkövetelmények/extrainfó számításához
        self.extraInfo = {
            'numAllPublications': 0,
            'numAllPublicationsThreshold': 4,
            'numInForeignPeerreviewedJournal': 0,
            'numInForeignPeerreviewedJournalThreshold': 2,
            'numWosOrScopus': 0,
            'numWosOrScopusThreshold': 1,
            'numforeign50percent': 0,
            'numforeign50percentThreshold': 2,
            'numHungarian': 0,
            'numHungarianThreshold': 1,
            'pointThreshold': 12,
        }

    TOKENLIST = [
        ScoringToken('FOLY,LEK,KMINY', 6.0, 'Folyóiratcikk: Lektorált, Külföldön megjelent - idegen nyelven'),
        ScoringToken('FOLY,LEK,MMINY', 4.0, 'Folyóiratcikk: Lektorált, Magyarországon megjelent - idegen nyelven'),
        ScoringToken('FOLY,LEK,MNY', 2.0, 'Folyóiratcikk: Lektorált, Magyar nyelven'),
        ScoringToken('FOLY,NLE,KMINY', 3.0, 'Folyóiratcikk: Nem lektorált, Külföldön megjelent - idegen nyelven'),
        ScoringToken('FOLY,NLE,MMINY', 2.0, 'Folyóiratcikk: Nem lektorált, Magyarországon megjelent - idegen nyelven'),
        ScoringToken('FOLY,NLE,MNY', 1.0, 'Folyóiratcikk: Nem lektorált, Magyar nyelven'),

        ScoringToken('KONYV,SZERZ,INY', 8.0, 'Könyv: Idegen nyelven'),
        ScoringToken('KONYV,SZERZ,MNY', 5.0, 'Könyv: Magyar nyelven'),
        ScoringToken('KRKF,SZERZ,INY', 6.0, 'Könyvrészlet/Könyvfejezet: idegen nyelven'),
        ScoringToken('KRKF,SZERZ,MNY', 3.0, 'Könyvrészlet/Könyvfejezet: magyar nyelven'),
        ScoringToken('KONYV,SZERK', 4.0, 'Szerkesztett kötetben cikk (legalább 10 oldal)'),

        ScoringToken('JEGYZ25', 3.0, 'Nyomtatott (vagy elektronikus formában közzétett) egyetemi jegyzet (legalább 25 oldal)'),

        ScoringToken('KONF,KMINY', 5.0, 'Konferenciacikk: Külföldön megjelent - idegen nyelven'),
        ScoringToken('KONF,MMINY', 2.0, 'Konferenciacikk: Magyarországon megjelent - idegen nyelven'),
        ScoringToken('KONF,MNY', 2.5, 'Konferenciacikk: Magyar nyelven'),

        ScoringToken('SZABADALOM', 2.0, 'Szabadalom'),

        ScoringToken('RECENZIO', 1.0, 'Recenzió (más szerző művének kinyomtatott értékelése)'),

        ScoringToken('ELEK-PUB', 1.0, 'Elektronikus publikáció'),

        ScoringToken('CIT-IND,WOS', 5.0, 'SCI adatbázisban megtalálható adott évben idézett'),
        ScoringToken('CIT-IND,SCOPUS', 5.0, 'SCI adatbázisban megtalálható adott évben idézett'),
        ScoringToken('CIT-IND,W+S', 5.0, 'SCI adatbázisban megtalálható adott évben idézett'),
        ScoringToken('NEMPONTOZOTT', 0.0, 'A pontozásban nem szerepel'),
        ScoringToken('HIBASARANY', 0.0, 'Közlemények hibás vagy hiányos szerzői részaránnyal'),
        ScoringToken('ERROR', 0.0, 'Hibakezelés'),
    ]

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
        oldalszam = published.publication.pagenum
        if oldalszam is None:
            oldalszam = 0
        authorcount = published.publication.authorcount
        editorcount = published.publication.editorcount
        #Nyelv
        angol = published.publication.language.contains_english
        magyar = published.publication.language.is_hungarian
        #Hely
        magyarorszag = (published.publication.publishinglocation.country == 'Magyarország')  
        #Szerző típusa
        author_type = published.authortype.name
        wosdb = published.wosdb
        scopusdb =   published.scopusdb
        has_doi = published.has_doi
        has_full_document_url = published.has_full_document_url
        has_oa_link = published.has_oa_link
        corrected_share = 0.0

        #has_isbn = published.has_isbn
        self.extraInfo['numAllPublications'] += 1
        # --- VIK_PHD 1. folyóiratcikk? ---
        if type_name == 'folyóiratcikk' and subtype_name in ['szakcikk', 'sokszerzős vagy csoportos szerzőségű szakcikk', 'összefoglaló cikk'] and jelleg == 'tudományos' and author_type == 'author':
            debuginfo = 'VIK-PHD-1 - folyóirat (%s oldal)'%oldalszam              
            
            #Lektorált?
            if lektoralt:
                if not magyar and not magyarorszag:
                    token = 'FOLY,LEK,KMINY'
                    self.extraInfo['numInForeignPeerreviewedJournal'] += 1
                    if wosdb or scopusdb: self.extraInfo['numWosOrScopus'] += 1
                elif not magyar and magyarorszag:
                    token = 'FOLY,LEK,MMINY'
                    self.extraInfo['numInForeignPeerreviewedJournal'] += 1
                    if wosdb or scopusdb: self.extraInfo['numWosOrScopus'] += 1
                else:
                    token = 'FOLY,LEK,MNY'
            else:
                if not magyar and not magyarorszag:
                    token = 'FOLY,NLE,KMINY'
                elif not magyar and magyarorszag:
                    token = 'FOLY,NLE,MMINY'
                else:
                    token = 'FOLY,NLE,MNY'               

            if magyar is None:
                token = 'ERROR'
                tokenkieg = 'is_hungarian: NULL'        

        # --- VIK-PHD 2. könyv ---
        elif type_name == 'könyv' and subtype_name in ['szakkönyv', 'monográfia', 'tanulmánykötet', 'kézikönyv'] and jelleg == 'tudományos' and author_type == 'author':
            debuginfo = 'VIK-PHD-2 - könyv (%s oldal)'%oldalszam

            if not magyar:
                token = 'KONYV,SZERZ,INY'
            else:
                token = 'KONYV,SZERZ,MNY'

            if magyar is None:
                token = 'ERROR'
                tokenkieg = 'is_hungarian: NULL'
        
        # --- VIK-PHD 3.  könyvrészlet, könyvfejezet szerzőként ---
        elif type_name == 'könyvrészlet' and subtype_name in ['szaktanulmány', 'könyvfejezet'] and jelleg == 'tudományos' and author_type == 'author' :
            debuginfo = 'VIK-PHD-3 - könyvrészlet (%s oldal)'%oldalszam 
            
            if not magyar:
                token = 'KRKF,SZERZ,INY'
            else:
                token = 'KRKF,SZERZ,MNY'

            if magyar is None:
                token = 'ERROR'
                tokenkieg = 'is_hungarian: NULL'  

        # -- VIK-PHD 5. szerkesztett kötetben cikk (legalább 10 oldal)
        
            
        # -- VIK-PHD 6. Nyomtatott (vagy elektronikus formában közzétett) egyetemi jegyzet (legalább 25 oldal)
        
        elif ((type_name == 'könyv' and subtype_name == 'felsőoktatási tankönyv') or (type_name == 'könyvrészlet' and subtype_name == 'felsőoktatási tankönyv része')) and jelleg == 'oktatási' and author_type == 'author':
            debuginfo = 'VIK-PHD-6 - jegyzet >=25 oldal (%s oldal)'%oldalszam
            if oldalszam >= 25:
                token = 'JEGYZ25'

        # --- VIK-PHD 7. Konferencia kiadványában megjelent előadás
        elif type_name in ['folyóiratcikk', 'könyvrészlet', 'egyéb konferenciaközlemény'] and subtype_name == 'konferenciaközlemény' and jelleg == 'tudományos' and author_type == 'author':
            debuginfo = 'VIK-PHD-7 - Konferencia kiadványában megjelent előadás (%s oldal)'%oldalszam
            
            if not magyar and not magyarorszag:
                token = 'KONF,KMINY'
            elif not magyar and magyarorszag:
                token = 'KONF,MMINY'
            else:
                token = 'KONF,MNY'

            if author_type is None:
                token = 'ERROR'
                tokenkieg = 'authortype_name: NULL'
                
        # --- VIK-PHD 8. Szabalaom
        elif type_name in ['oltalmi formák']:
            debuginfo = 'VIK-PHD-8 - SZABADLOM (%s oldal)'%oldalszam
            token = 'SZABADALOM'

        # --- VIK-PHD-9. Recenzió (más szerző művének kinyomtatott értékelése)
        elif type_name in ['folyóiratcikk', 'könyvrészlet'] and subtype_name == 'recenzió/kritika' and jelleg == 'tudományos' and author_type == 'author':
            debuginfo = 'VIK-PHD-9 - Recenzió (más szerző művének kinyomtatott értékelése) (%s oldal)'%oldalszam
            token = 'RECENZIO'

        #TODO: DOI és teljes Dokumentum azonosító
        # --- VIK-PHD 10. Elektronikus ---
        elif jelleg == 'tudományos' and (has_doi or has_full_document_url or has_oa_link):
            debuginfo = 'VIK-10 - elektronikus (%s oldal)'%oldalszam
            token = 'ELEK-PUB'

        else:
            token = 'NEMPONTOZOTT'

        supervisor_pubauthor = self.get_supervisor_pubauthor(published, supervisor_mtmt)
        shares = self.get_all_shares(published)
        if sum(shares) >= 1.0 + EPSILON_AUTHOR_SHARE:
            token = 'HIBASARANY'        
        
        elif math.isclose(sum(shares), 0.0, abs_tol=EPSILON_AUTHOR_SHARE):
            if authorcount == 0:
                corrected_share = 0
            else:
                if supervisor_pubauthor:
                    corrected_share = 1./(authorcount-1)
                else:
                    corrected_share = 1./authorcount        
        else:
            if supervisor_pubauthor:
                corrected_share = published.share * (1/(1-supervisor_pubauthor.share))
            else:
                corrected_share = published.share

        if type_name in ['könyv', 'könyvrészlet', 'folyóiratcikk', 'egyéb konferenciaközlemény', 'oltalmi formák'] and author_type == 'author':
            if corrected_share > 0.5 - EPSILON_AUTHOR_SHARE and not magyar:
                self.extraInfo['numforeign50percent'] += 1
            if magyar:
                self.extraInfo['numHungarian'] += 1
                
        return (pubid, token, tokenkieg, corrected_share, debuginfo)

    def nullCounters(self):
        self.extraInfo['numAllPublications'] = 0
        self.extraInfo['numInForeignPeerreviewedJournal'] = 0
        self.extraInfo['numWosOrScopus'] = 0
        self.extraInfo['numforeign50percent'] = 0
        self.extraInfo['numHungarian'] = 0


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
