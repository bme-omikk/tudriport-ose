from django.core.management import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from riport.models.external import Language
import csv

class Command(BaseCommand):
    help = 'Nyelvi beállítások (idegen, fő nyelv) beállítások betöltés tábla feltöltése)'

    def add_arguments(self, parser):
        parser.add_argument('-f', '--file', required=True, help='Melyik fájlból olvassa be?')

    def handle(self, *args, **options):        
        #self.write(self.style.INFO("Importing languages from input file: %s" % options['file']))
        try:
            with open(options['file'], 'rt') as csvfile:
                for row in csv.reader(csvfile, delimiter=';'):
                    if len(row) < 3: continue

                    l_name = row[0].strip()
                    # skip header row
                    if l_name == 'language name': continue

                    l_is_hungarian = row[1].strip() == 'Y'
                    l_all_non_hungarian = row[2].strip() == 'Y'
                    l_all_main_lang = row[3].strip() == 'Y'
                    l_is_english = row[4].strip() == 'Y'
                    l_contains_hungarian = row[5].strip() == 'Y'
                    l_contains_english = row[6].strip() == 'Y'                    
                    defaults={
                        'name':l_name,
                        'is_hungarian':l_is_hungarian,
                        'contains_hungarian' : l_contains_hungarian,
                        'is_english' : l_is_english,
                        'contains_english' : l_contains_english,
                        'all_non_hungarian' : l_all_non_hungarian,
                        'all_main_lang' : l_all_main_lang }
                    try:      
                        language = Language.objects.get(name=l_name) 
                        language.update_if_differs(defaults, save=True)                   
                    except ObjectDoesNotExist:
                        obj = Language(**defaults)
                        obj.save()



        except FileNotFoundError:
            self.write(self.style.ERROR("No such file: %s" % options['file']))