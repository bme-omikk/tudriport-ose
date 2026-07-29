from .scoring_token import ScoringToken
from .pub_util import PUB_UTIL

class RIPORT(PUB_UTIL):
    """GPK kari pontozó."""
    def __init__(self):
        PUB_UTIL.__init__(self, True)

    TOKENLIST = [
        ScoringToken('FOLY,D1,ANG', 25.0, 'Folyóiratcikk: MTMT-ben D1 besorolású folyóiratban - angol nyelven'),
        ScoringToken('FOLY,Q1Q2,ANG', 15.0, 'Folyóiratcikk: MTMT-ben Q1 vagy Q2 besorolású folyóiratban - angol nyelven'),
        ScoringToken('FOLY,Q3Q4,ANG', 8.0, 'Folyóiratcikk: MTMT-ben Q3 vagy Q4 besorolású folyóiratban - angol nyelven'),
        ScoringToken('FOLY,LEK,ANG', 4.0, 'Folyóiratcikk: Lektorált (D,Q nélkül) - angol nyelven'),
        ScoringToken('FOLY,NLE,ANG', 2.0, 'Folyóiratcikk: Nem lektorált folyóiratban - angol nyelven'),
        ScoringToken('FOLY,D1,NANG', 25.0, 'Folyóiratcikk: MTMT-ben D1 besorolású folyóiratban cikk - egyéb idegen nyelven vagy magyarul'),
        ScoringToken('FOLY,Q1Q2,NANG', 15.0, 'Folyóiratcikk: MTMT-ben Q1 vagy Q2 besorolású folyóiratban - egyéb idegen nyelven vagy magyarul'),
        ScoringToken('FOLY,Q3Q4,NANG', 8.0, 'Folyóiratcikk: MTMT-ben Q3 vagy Q4 besorolású folyóiratban - egyéb idegen nyelven vagy magyarul '),
        ScoringToken('FOLY,LEK,NANG', 2.0, 'Folyóiratcikk: Lektorált (D,Q nélkül) - egyéb idegen nyelven vagy magyarul'),
        ScoringToken('FOLY,NLE,NANG', 1.0, 'Folyóiratcikk: Nem lektorált folyóiratban - egyéb idegen nyelven vagy magyarul'),

        ScoringToken('KONF,WOS,ANG', 5.0, 'Konferenciacikk: WoS-ban megjelent - angol nyelven'),
        ScoringToken('KONF,OTH,ANG', 2.0, 'Konferenciacikk: Máshol megjelent - angol nyelven'),
        ScoringToken('KONF,WOS,NANG', 2.5, 'Konferenciacikk: WoS-ban megjelent - egyéb idegen nyelven vagy magyarul'),
        ScoringToken('KONF,OTH,NANG', 1.0, 'Konferenciacikk: Máshol megjelent - egyéb idegen nyelven vagy magyarul'),

        ScoringToken('KONYV,SZERZO,ANG', 0.5, 'Könyv: ISBN/DOI számmal, szerzőként, oldalanként - angol nyelven + tokenkieg: oldalszám'),
        ScoringToken('KONYV,SZERK,ANG', 0.05, 'Könyv: ISBN/DOI számmal, szerzőként, oldalanként - angol nyelven + tokenkieg: oldalszám'),        
        ScoringToken('KONYV,SZERZO,NANG', 0.25, 'Könyv: ISBN/DOI számmal, szerkesztőként, oldalanként - egyéb idegen nyelven vagy magyarul + tokenkieg: oldalszám, SZERKESZTŐ'),
        ScoringToken('KONYV,SZERK,NANG', 0.025, 'Könyv: ISBN/DOI számmal, szerkesztőként, oldalanként - egyéb idegen nyelven vagy magyarul + tokenkieg: oldalszám, SZERKESZTŐ'), 

        ScoringToken('CIT-IND,WOS', 5.0, 'SCI adatbázisban megtalálható adott évben idézett'),
        ScoringToken('CIT-IND,SCOPUS', 5.0, 'SCI adatbázisban megtalálható adott évben idézett'),
        ScoringToken('CIT-IND,W+S', 5.0, 'SCI adatbázisban megtalálható adott évben idézett'),
        ScoringToken('NEMPONTOZOTT', 0.0, 'A pontozásban nem szerepel'),
        ScoringToken('ERROR', 0.0, 'Hibakezelés'),
    ]

    @classmethod
    def get_world_name(cls):
        """Return the name of the world where authors are retrieved from."""
        return 'kari'

    # és itt írjuk meg a függvényt, amely egy-egy közleményrekordból részpontszámot számol
    def kategorizalas(self, mtmt_id, published):
        token = ''
        tokenkieg = ''
        debuginfo = ''
        calculation = '' 
        pubid = published.publication.mtmt_pubid
        type_name = published.publication.type.type_name
        subtype_name = published.publication.typesubtype.subtype_name

        idegennyelv = published.publication.language.all_non_hungarian
        lektoralt = published.publication.peerreviewed
        oldalszam = published.publication.pagenum
        if oldalszam is None:
            oldalszam = 0
        impactfactor = published.publication.impactfactor_value
        authorcount = published.publication.authorcount
        editorcount = published.publication.editorcount
        angol = published.publication.language.contains_english
        besorolas = published.publication.sjr_rank
        WOS = published.publication.wosdb
        jelleg = published.publication.character.name
        author_type = published.authortype.name        
        if jelleg == 'tudományos':
        # --- GPK 1. folyóiratcikk? ---
            if type_name in ['folyóiratcikk'] and (subtype_name != 'konferenciaközlemény' or subtype_name is None):
                debuginfo = 'GPK-1 - folyóirat (%s oldal)'%oldalszam
                #TODO Ha egy az egyben jönnek a besorolások, sokkal rövidebb alternatíva a 
                #  következő ~25 sorra:
                #  token  = 'FOLY, ' + besorolas + (',ANG' if angol else ',NANG')
                #
                
                #Folyóirat besorolások
                if besorolas == 'D1':
                    if angol == True:
                        token = 'FOLY,D1,ANG'
                    elif angol == False:
                        token = 'FOLY,D1,NANG'

                elif besorolas in ['Q1', 'Q2']:
                    if angol == True:
                        token = 'FOLY,Q1Q2,ANG'
                    elif angol == False:
                        token = 'FOLY,Q1Q2,NANG'

                elif besorolas in ['Q3', 'Q4']:
                    if angol == True:
                        token = 'FOLY,Q3Q4,ANG'
                    elif angol == False:
                        token = 'FOLY,Q3Q4,NANG'
                
                elif lektoralt:
                    if angol == True:
                        token = 'FOLY,LEK,ANG'
                    elif angol == False:
                        token = 'FOLY,LEK,NANG'
                else:
                    if angol == True:
                        token = 'FOLY,NLE,ANG'
                    elif angol == False:
                        token = 'FOLY,NLE,NANG'        

                if angol is None:
                    token = 'ERROR'
                    tokenkieg = 'angol: NULL'
            # --- GPK 2. Elektronikus ---
            # helye itt lesz .. ha már tudjuk, miből lehet

            # --- GPK 3. konferencia ---
            elif type_name in ['folyóiratcikk', 'könyvrészlet', 'egyéb konferenciaközlemény'] and subtype_name == 'konferenciaközlemény':
                debuginfo = 'GPK-3 - konferencia (%s oldal)'%oldalszam

                if WOS:
                    if angol == True:
                        token = 'KONF,WOS,ANG'
                    elif angol == False:
                        token = 'KONF,WOS,NANG'
                else:
                    if angol == True:
                        token = 'KONF,OTH,ANG'
                    elif angol == False:
                        token = 'KONF,OTH,NANG'

                if angol is None:
                    token = 'ERROR'
                    tokenkieg = 'angol: NULL'
            
            # --- GPK 4. könyv, könyvrészlet, szerzőként ---
            elif author_type == 'author' and ((type_name == 'könyv' and subtype_name in ['szakkönyv', 'monográfia']) or (type_name == 'könyvrészlet' and subtype_name in ['könyvfejezet', 'szaktanulmány'])):
                debuginfo = 'GPK-4 - könyv (%s oldal)'%oldalszam 

                tokenkieg = oldalszam
                if oldalszam:
                    if angol == True:
                        token = 'KONYV,SZERZO,ANG'
                    elif angol == False:
                        token = 'KONYV,SZERZO,NANG'

                if angol is None:
                    token = 'ERROR'
                    tokenkieg = 'angol: NULL'
                if author_type is None:
                    token = 'ERROR'
                    tokenkieg = 'authortype_name: NULL'    

            # --- GPK 5. könyv, könyvrészlet, konferenciakötet szerkesztőként ---
            elif author_type == 'editor' and type_name == 'könyv' and subtype_name in ['szakkönyv', 'monográfia', 'konferenciakötet']:
                debuginfo = 'GPK-5 - könyv (%s oldal)'%oldalszam
                
                tokenkieg = oldalszam
                if oldalszam:
                    if angol == True:
                        token = 'KONYV,SZERK,ANG'
                    elif angol == False:
                        token = 'KONYV,SZERK,NANG'

                if angol is None:
                    token = 'ERROR'
                    tokenkieg = 'angol: NULL'
                if author_type is None:
                    token = 'ERROR'
                    tokenkieg = 'authortype_name: NULL'

        if token.startswith('KONYV,SZERK'):
            if editorcount == 0:
                share = 0
            else:
                share = 1./editorcount
        else:
            if authorcount == 0:
                share = 0
            else:
                share = 1./authorcount
        return (pubid, token, tokenkieg, share, debuginfo)


    def citations_gpk(self, pubrefs):
        # --- GPK 5. SCI adatbázis --> WoS_independent[2017] ---
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
            alltoken.append(self.kategorizalas(mtmt_id, published))            
        
        alltoken += self.citations_gpk(pubrefs) 
        #print (tokendict) # statisztika
        fejlec = {'mtmt_id': mtmt_id, 'mtmt_name': mtmt_pubauthorname }
        return fejlec, alltoken, self.extraInfo.copy()

    def riportgen_publication(self, dbdatetime, published, pubrefs, supervisor_mtmt):
        self.nullCounters()
        alltoken = []
        token = self.kategorizalas(-1, published)
        alltoken.append(token)
        alltoken += self.citations_gpk(pubrefs) 
        #print (tokendict) # statisztika
        fejlec = {'talalat_token': token[1] }        
        return fejlec, alltoken, self.extraInfo.copy()
