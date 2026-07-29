from unittest import TestCase
from scoring.riport_gpk import RIPORT
from riport.models.external import ExtAuthorlist, Published
from django.utils import timezone
import importlib
import json
class ScoringTestCases(TestCase):
    #12345678-as közlemény pontozása Teszt Elek szerzővel
    def test_12345678_publication_scoring_with_author_10002700(self):
        riport = RIPORT()
        published = Published.get_valid_objects().get(mtmt_pubid=12345678, mtmt_pubauthorname='Teszt E')
        result = riport.pub_util_riportgen_publication(published, timezone.now(), None, None)
        self.assertAlmostEqual(result['osszpontszam'], 5.33333333333)

    #Teszt Elek 2018-as közleményeinek pontozása
    def test_teszt_elek_2018(self):
        riport = RIPORT()
        result = riport.pub_util_riportgen(10002700, timezone.now(), 2018, 1, None)
        self.assertAlmostEqual(result['osszpontszam'], 25.55833333333334) 
        self.assertAlmostEqual(result['reszeredmenyek']['FOLY,D1,ANG']['reszpont'], 8.33333333333333)        

    #Teszt Elek 2020-as közleményeinek pontozása
    def test_teszt_elek_2020(self):
        riport = RIPORT()
        result = riport.pub_util_riportgen(10002700, timezone.now(), 2020, 1, None)
        self.assertAlmostEqual(result['osszpontszam'], 11.5) 
        self.assertAlmostEqual(result['reszeredmenyek']['FOLY,D1,ANG']['reszpont'], 0.0)        
        self.assertAlmostEqual(result['reszeredmenyek']['FOLY,D1,NANG']['reszpont'], 0.0)

    #Teszt an organisation scoring
    def test_bme_gpk_egr_2020(self):
        riport = RIPORT()
        authors = ExtAuthorlist.get_valid_objects().filter(org='EXAMPLE', unit='FACULTY1', subunit='DEPT1')  
        for a in authors:
            riport.pub_util_riportgen(a.mtmtcode, timezone.now(), 2020, a.weighting, None)
        result = riport.aggregate()
        self.assertAlmostEqual(result['osszpontszam'], 31.25) 
        self.assertAlmostEqual(result['reszeredmenyek']['FOLY,D1,ANG']['reszpont'], 0.0)        
        self.assertAlmostEqual(result['reszeredmenyek']['FOLY,D1,NANG']['reszpont'], 0.0)
        self.assertAlmostEqual(result['reszeredmenyek']['FOLY,Q1Q2,ANG']['reszpont'], 31.25)

