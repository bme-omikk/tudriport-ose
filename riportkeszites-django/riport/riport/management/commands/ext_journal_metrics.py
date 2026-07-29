from django.core.management import BaseCommand
import re
import pgdb
import csv
import sys
import gzip
import lzma
import bz2
import codecs
import argparse
from riport.models.external import ExtJournalMetrics
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from pandas import read_excel
from os import listdir, mkdir
from os.path import isfile, join, isdir, abspath
VERBOSE = 0

availableModes = ['IF', ]

class Command(BaseCommand):
    help = 'ext_journal_metrics adatok betöltése'
    
    def add_arguments(self, parser):
        subparsers = parser.add_subparsers()
        #CSV FORMÁTUM: id;cím,befoglaló mű címe;issn;eissn;year;metric_value
        #XLS: csak Impact factorhoz implemetálva

        group = parser.add_mutually_exclusive_group(required=True)
        
        group.add_argument('--csvfile', help='Melyik CSV fájlból olvassa be?')
        group.add_argument('--xlsfile', help='Melyik XLS fájlból olvassa be?')
        group.add_argument('--xlsdir', help='Melyik XLS-eket tartalmazó mappából olvassa be?')
        parser.add_argument('-m', '--mode', required=True, help='Melyik metrikát töltse be?')             
        parser.add_argument('--addestimations', action='store_true', help='Ha szerepel a parancsban, akkor további két évre betölti várható értékként')
        parser.add_argument('--keep-estimated-metrics', action='store_true', help='Ha szerepel a parancsban, akkor új év betöltésénél a táblázatból hiányzó közleményekre adott évben (vagy később) meglévő becsléseket megtartja')

    def handle(self, *args, **options):
        if options['mode'] not in availableModes:
            print(f'A lehetséges módok: {availableModes}')
            raise NotImplementedError
        addestimations = options['addestimations']
        delete_estimated_metrics = True
        if 'keep-estimated-metrics' in options:
            delete_estimated_metrics = False  
        if options['csvfile']:            
            metrics_csv_dbwrite(options['csvfile'], options['mode'], addestimations)
        elif options['xlsfile']:            
            xls_data = parse_xls(options['xlsfile'], delete_estimated_metrics)
            year = re.findall('[0-9]{4}', options['xlsfile'])
            if len(year) != 1:
                pass
            data = {}
            data[year[0]] = xls_data
            metrics_xlsx_dbwrite(data, addestimations) 
        elif options['xlsdir']:
            data = parse_all_xls(options['xlsdir'], delete_estimated_metrics)
            metrics_xlsx_dbwrite(data, addestimations)

def load_to_db(title, ISSNs, year, metric_name, metric_value, addestimations):
    defaults={
        'ISSNs': ISSNs,
        'year': int(year),
        'metric_name': metric_name,
        'metric_value': float(metric_value),
        'isestimate': False,
        'journal_title': title
    }
    if ISSNs:
        try:
            existing_metric = ExtJournalMetrics.get_valid_objects().get(ISSNs__overlap=ISSNs, year=year, metric_name=metric_name)
            changed_field_exists = existing_metric.update_if_differs(defaults)
            if changed_field_exists: 
                existing_metric.save()
                estimations = ExtJournalMetrics.get_valid_objects().filter(ISSNs__overlap=ISSNs, year__gte=year, metric_name=metric_name, isestimate=True)
                estimations.delete()
                if addestimations: add_estimations(defaults)
        except ObjectDoesNotExist:
            new_metric = ExtJournalMetrics(**defaults)
            new_metric.save() 
            if addestimations: add_estimations(defaults)

def add_estimations(defaults):
    defaults['isestimate'] = True
    defaults['year'] = defaults['year'] + 1
    estmiate_for_next_year = ExtJournalMetrics(**defaults)
    estmiate_for_next_year.save()
    defaults['year'] = defaults['year'] + 1
    estmiate_for_after_next_year = ExtJournalMetrics(**defaults)
    estmiate_for_after_next_year.save()

def metrics_csv_dbwrite(fname, mode, addestimations): 
    print('loading data...')      
    try:
        ext = fname.split('.')[-1]
        if ext == 'csv':
            fd = open(fname, 'rb')                
        else:
            origext = fname.split('.')[-2]
            if ext == 'gz':
                fd = gzip.open(fname, 'rb')
            elif ext == 'xz':
                fd = lzma.open(fname, 'rb')
            elif ext == 'bz2':
                fd = bz2.BZ2File(fname, 'rb')
    except:
        print ("A fájl (%s) nem nyitható meg."%fname)
        return
    metrics = {}
    new_issns = []
    csvdata = csv.reader(codecs.iterdecode(fd, 'utf-8'), delimiter=';')
    last_year = 0
    for f in csvdata:     
        if len(f) < 3 or f[0] > '9': continue # nem szám
        mval = f[6].strip()
        if mval == '': continue
        try:
            float(mval)
        except:
            print ("nem szám a metric_value (sor: %d): %s"%(ct, f[6]))
            return False
        ISSNs = []
        ISSNs.append(f[3].strip())
        if f[4].strip() != 'NULL': ISSNs.append(f[4].strip())
        ISSNs.sort()
        new_issns.extend(ISSNs)
        load_to_db(f[1].strip(), ISSNs, int(f[5].strip()), mode, float(mval), addestimations)        
    fd.close()
    return True

mapping_conf = {
    'full journal title': 'journal',
    'issn': 'issn',
    'journal impact factor': 'if',
}
mapping_conf_with_eissn = {
    'full journal title': 'journal',
    'issn': 'issn',
    'eissn': 'eissn',
    'journal impact factor': 'if',
}

def metrics_xlsx_dbwrite(data, addestimations):
    last_year = max(data)
    print('loading data...')
    for year in data:
        for journal in data[year]:
            ISSNs = []            
            issn = journal.pop('issn')
            if issn is not None: ISSNs.append(issn)
            if 'eissn' in journal: 
                eissn = journal.pop('eissn')
                if eissn is not None: ISSNs.append(eissn)
            if year == last_year: 
                load_to_db(journal.pop('journal'), ISSNs, year, 'IF', float(journal.pop('if')), addestimations)  
            else:
                load_to_db(journal.pop('journal'), ISSNs, year, 'IF', float(journal.pop('if')), False)         

def validate_row(file_path, row_data, found_issns):
    # all-nan raw can happen due to footnotes
    if list(row_data.values()).count('nan') == len(row_data):
        return False

    # check ISSNs
    issn_valid = True
    if not re.match(r'^[0-9]{4}-[0-9]{3}[0-9xX]$', row_data['issn']):
        print("%s: Issn '%s' is invalid" % (file_path, row_data['issn']))
        row_data['issn'] = None
        issn_valid = False

    eissn_valid = True
    if 'eissn' in row_data and not re.match(r'^[0-9]{4}-[0-9]{3}[0-9xX]$', row_data['eissn']):
        print("%s: eIssn '%s' is invalid" % (file_path, row_data['eissn']))
        row_data['eissn'] = None
        eissn_valid = False
    
    if not issn_valid and not eissn_valid:        
        return False


    # check if value
    try:
        float(row_data['if'])
    except ValueError:
        print("%s: Journal (issn: %s) dropped as '%s' is not a valid impact factor." % (file_path, row_data['issn'], row_data['if']))
        return False

    # check duplicates
    if row_data['issn'] in found_issns:
        print("%s: Duplication for a journal (issn: %s)" % (file_path, row_data['issn']))
        return False

    # check year (if available)
    if 'year' in row_data and not re.match(r'^[0-9]{4}$', row_data['year']):
        print("%s: Record dropped, as '%s' is not a valid year" % (file_path, row_data['issn']))
        return False

    return True

def parse_xls(path, delete_estiamted_metrics):
    excel = read_excel(path)

    mapping = {}
    data = []
    found_issns = []
    year = re.findall('[0-9]{4}', path)
    for row_index, row in excel.iterrows():
        row = [str(e).lower() for e in row.values]

        # first let's identify headers
        if not mapping:
            for key, value in mapping_conf_with_eissn.items():
                if key not in row:
                    break

                mapping[value] = row.index(key)

            # save column indexes if all headers found
            if mapping:
                if len(mapping) != len(mapping_conf_with_eissn):
                    for key, value in mapping_conf.items():
                        if key not in row:
                            break

                        mapping[value] = row.index(key)
                    if len(mapping) != len(mapping_conf):
                        print('Could not find headers in file (%s). %s != %s' % (path, mapping, mapping_conf))
                        break
        else:
            # process data
            row_data = {name: row[index] for name, index in mapping.items()}

            if validate_row(path, row_data, found_issns):
                if row_data['issn'] is not None: found_issns.append(row_data['issn'])
                if 'eissn' in row_data and row_data['eissn'] is not None: found_issns.append(row_data['eissn'])
                data.append(row_data)
    if delete_estiamted_metrics: delete_old_estimations(found_issns, year[0])
    return data


def parse_all_xls(directory, delete_estiamted_metrics):
    if not isdir(directory):
        print('Given directory "%s" does not exists.' % directory)
        exit(1)

    data = {}
    for path in listdir(directory):
        abs_path = join(directory, path)
        if isfile(abs_path) and path.split('.')[-1] in ['xls', 'xlsx']:
            xls_data = parse_xls(abs_path, delete_estiamted_metrics)
            year = re.findall('[0-9]{4}', path)
            if len(year) != 1:
                pass
                # todo log
            data[year[0]] = xls_data

    return data

#Ha egy új év betöltésénél nem szerepel egy közlemény, akkor az ahhoz tartozó régi becslést törölni kell.
def delete_old_estimations(new_issns, year):
    old_estimations = ExtJournalMetrics.get_valid_objects().filter(isestimate=True, year__gte=year).exclude(ISSNs__overlap=new_issns)
    old_estimations.delete()
