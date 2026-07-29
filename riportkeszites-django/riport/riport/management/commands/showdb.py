#!/usr/bin/env python3
from django.core.management import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils import timezone
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from riport.models.external import Publication, Type, Typesubtype, Character, Language, Location, Container, Pubauthors, Authortype, Pubref
from django.core import serializers
import json

class Command(BaseCommand):
    help='XML parse és betöltő utility'

    def add_arguments(self, parser):
        parser.add_argument('--mtmt', required=True, help='Melyik közleményazonosítót keressük?')
        parser.add_argument('--datetime', help='Mikori állapot szerint')

    def handle(self, *args, **options):
        if options['datetime'] is None:
            datetime = timezone.now()
        else:
            datetime = options['datetime']

        print (datetime)
        record = publication_detail(options['mtmt'], datetime)
        if record:
            print (json.dumps(record, indent=4, sort_keys=True, ensure_ascii=False, cls=DjangoJSONEncoder))

#publication_detail(1000nnn, '2019-03-12 23:25:02.627331')
def publication_detail(mtmt_id, datestr):
    record={}
    try:
        publication = Publication.get_valid_objects(querytime=datestr).select_related().get(mtmt_pubid=mtmt_id)   
    except ObjectDoesNotExist:
        print ('Nincs a kérésnek megfelelő publikáció')
        return None 
    except MultipleObjectsReturned: 
        print ('Hiba: több találat.')
        return None
    record['publication'] = model_to_dict(publication) 
    record['publication']['Type'] = model_to_dict(publication.type)
    record['publication']['Typesubtype'] = model_to_dict(publication.typesubtype)
    record['publication']['Typesubtype']['Type'] = model_to_dict(publication.typesubtype.type)
    record['publication']['Character'] = model_to_dict(publication.character)
    record['publication']['Language'] = model_to_dict(publication.language)
    record['publication']['Publisher'] = model_to_dict(publication.publisherlocation)
    record['publication']['Publishing'] = model_to_dict(publication.publishinglocation)    
    #container
    if publication.container_groupid is not None:
        try:
            record['publication']['Container'] = model_to_dict(Container.get_valid_objects(querytime=datestr).get(groupid=publication.container_groupid))
        except ObjectDoesNotExist:
            print('Hiba: üres container err a groupid-re.')
            return
        except MultipleObjectsReturned:
            print('Hiba: több találat a container-ben.')
            return
        del record['publication']['Container']['id']
        del record['publication']['Container']['groupid']
    #authors
    authors = Pubauthors.objects.filter(publication_id=publication.id).select_related('authortype')
    record['authors']=[]
    for author in authors.all():
        auth_dict = model_to_dict(author)
        auth_dict['authortype_name'] = author.authortype.name
        record['authors'].append(auth_dict) 
    #citations  
    pubrefs = Pubref.objects.filter(publication_id=publication.id)
    record['citations']=[]
    for pubref in pubrefs:
        record['citations'].append(model_to_dict(pubref))
    
    del record['publication']['id']
    del record['publication']['Type']['id']
    del record['publication']['Typesubtype']['id']
    del record['publication']['Typesubtype']['Type']['id']
    del record['publication']['Character']['id']
    del record['publication']['Language']['id']
    if 'publisher' in record['publication']:
        del record['publication']['Publisher']['id']

    #delete IDs
    del record['publication']['type']
    del record['publication']['Typesubtype']['type']
    del record['publication']['typesubtype']
    del record['publication']['character']
    del record['publication']['language']
    del record['publication']['publisherlocation']
    del record['publication']['publishinglocation']
    for auth in record['authors']:
        del auth['id']
        del auth['author_db']
        del auth['authortype']
        del auth['publication']
    for cit in record['citations']:
        del cit['id']
        del cit['publication']
    
    return record
