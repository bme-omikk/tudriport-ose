from django.core.management import BaseCommand
from riport.models.external import Location
from django.core.exceptions import ObjectDoesNotExist
import pgdb
import csv
import sys

class Command(BaseCommand):
    help = 'Nyelvi beállítások (idegen, fő nyelv) beállítások betöltése ext_journalclassification tábla feltöltése)'
    def add_arguments(self, parser):
        parser.add_argument('-f', '--file', required=True, help='Melyik fájlból olvassa be?')

    def handle(self, *args, **options):
        fname = options['file']        
        for f in csv.reader(open(fname,'r'), delimiter=';'):
            if len(f) < 3: continue
            loc = {}
            loc['country'] = f[0].strip()
            if loc['country'] == 'country': continue
            loc['city'] = f[1].strip()
            loc['interior'] = [False, True][f[2].strip() == 'Y']
            loc['exterior'] = [False, True][f[3].strip() == 'Y']                      
            defaults={
                    'country': loc['country'],
                    'city': loc['city'],
                    'interior': loc['interior'],
                    'exterior': loc['exterior']
                }
            try:      
                location = Location.objects.get(country=loc['country'], city=loc['city']) 
                location.update_if_differs(defaults, save=True)                   
            except ObjectDoesNotExist:
                obj = Location(**defaults)
                obj.save()
