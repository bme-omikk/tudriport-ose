#!/usr/bin/env python3

from ..common.config import getconfig

from .pub_util import PUB_UTIL

class RIPORT(PUB_UTIL):
    VERBOSE = getconfig('riport.VERBOSE')

    TOKENEK = {
        'ELEK-PUB': [1.0, 'Elektronikus publikáció'],

        'KONY-IDEG': [8.0, 'Könyv: Idegen nyelvű könyv'],
        'KONY-IDEG-RESZ': [6.0, 'Könyv: Idegen nyelvű könyvrész'],

        'KONY-MAGY': [5.0, 'Könyv: Magyar nyelvű könyv'],
        'KONY-MAGY-RESZ': [3.0, 'Könyv: Magyar nyelvű könyvrész'],
        'EGYET-JEGY-25+': [3.0, 'Egyetemi jegyzet, 25 oldal+'],

        'FOLY-LEK-IDEG-KK': [6.0, 'Folyóirat: Lektorált, idegen nyelv, külföldi kiadó'],
        'FOLY-LEK-IDEG-MK': [4.0, 'Folyóirat: Lektorált, idegen nyelv, magyar kiadó'],
        'FOLY-LEK-MAGY': [2.0, 'Folyóirat: Lektorált, magyar nyelven megjelent'],

        'FOLY-NLE-IDEG-KK': [3.0, 'Folyóirat: Nem lektorált, idegen nyelv, külföldi kiadó'],
        'FOLY-NLE-IDEG-MK': [2.0, 'Folyóirat: Nem lektorált, idegen nyelv, magyar kiadó'],
        'FOLY-NLE-MAGY': [1.0, 'Folyóirat: Nem lektorált, magyar nyelven megjelent'],

        'KONF-IDEG': [3.0, 'Konferencia: Idegen nyelvű'],
        'KONF-MAGY': [1.0, 'Konferencia: Idegen nyelvű'],

        'SZAB-MAGYAR': [2.0, 'Szabadalom: hazai'],
        'SZAB-KULF':   [2.0, 'Szabadalom: külföldi'],
    }

    def kulfoldon_megjelent(self, record):
        if 'publisher' in record['publication']:
            publisher_country = record['publication']['publisher']['country']
            if publisher_country in ['Magyarország']:
                return False
            else:
                return True
        return None

    # és itt írjuk meg a függvényt, amely egy-egy közleményrekordból részpontszámot számol
    def kategorizalas(self, mtmt_id, record):
        token = ''
        tokenkieg = ''
        debuginfo = ''

        pubid = record['publication']['mtmt_pubid'];
        type_name = record['publication']['type']['type_name']
        subtype_name = record['publication']['typesubtype']['subtype_name']

        idegennyelv = record['publication']['language']['all_non_hungarian']
        lektoralt = record['publication']['peerreviewed']

        oldalszam = record['publication']['pagenum']

        # --- VIK 1. Elektronikus? ---
        if type_name in ['egyeb'] and subtype_name in ['kutatási jelentés (közzétett)']:
            debuginfo = 'VIK-1 - elektronikus (%s oldal)'%oldalszam
            token = 'ELEK-PUB'

        # --- VIK 2. folyóirat ---
        if type_name in ['folyóiratcikk'] and subtype_name != 'konferenciaközlemény':
            debuginfo = 'VIK-2 - folyóirat (%s oldal)'%oldalszam
            if lektoralt:
                if idegennyelv == True:
                    kulf = self.kulfoldon_megjelent(record)
                    if kulf == True:
                        token = 'FOLY-LEK-IDEG-KK'
                    elif kulf == False:
                        token = 'FOLY-LEK-IDEG-MK'
                    else:
                        token = 'Error'
                        tokenkieg = 'Publisher country ismeretlen'
                else:
                    token = 'FOLY-LEK-MAGY'
            else:
                if idegennyelv == True:
                    kulf = self.kulfoldon_megjelent(record)
                    if kulf == True:
                        token = 'FOLY-NLE-IDEG-KK'
                    elif kulf == False:
                        token = 'FOLY-NLE-IDEG-MK'
                    else:
                        token = 'Error'
                        tokenkieg = 'Publisher country ismeretlen'
                else:
                    token = 'FOLY-NLE-MAGY'

            if idegennyelv == None:
                token = 'ERROR'
                tokenkieg = 'idegennyelv: NULL'

        # --- VIK 3. konferencia ---
        elif subtype_name in ['konferenciaközlemény', 'konferenciacikk']:
            debuginfo = 'VIK-3 - konferencia (%s oldal)'%oldalszam
            if idegennyelv == False:
                token = 'KONF-MAGY'
            else:
                token = 'KONF-IDEG'

            if idegennyelv == None:
                token = 'ERROR'
                tokenkieg = 'idegennyelv: NULL'

        # --- VIK 4. könyv ---
        elif type_name in ['könyv', 'könyvrészlet']:
            debuginfo = 'VIK-4 - könyv (%s oldal)'%oldalszam
            if idegennyelv == False:
                token = 'KONY-MAGY'
            elif idegennyelv == True:
                token = 'KONY-IDEG'
            else:
                token = 'ERROR'
                tokenkieg = 'nyelv hiányzik'
            # részlet...
            if type_name == 'könyvrészlet':
                if token[:4] == 'KONY':
                    token += '-RESZ'

        # --- VIK-5 szabadalom ---
        elif type_name in ['oltalmi formák']:
            if subtype_name in ['magyar szabadalom']:
                token = 'SZAB-MAGYAR'
            else:
                token = 'SZAB-KULF'

        return (pubid, token, tokenkieg, 1., debuginfo)

    # Fontos egyedi függvény, a pub_util_riportgen() ezt hívja meg
    def riportgen(self, mtmt_id, recordlist, allcitations):
        alltoken = []
        for record in recordlist:
            alltoken.append(self.kategorizalas(mtmt_id, record))

        #print (tokendict) # statisztika
        fejlec = {'mtmt_id': mtmt_id, 'mtmt_name': record['author']['mtmt_pubauthorname'] }
        return fejlec, alltoken

# ./riport_vik_phd.py --mtmt=10002700
if __name__ == '__main__':
    import json
    rpt = RIPORT()
    riport = rpt.pub_util_riportmain()
    print(json.dumps(riport, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False))
