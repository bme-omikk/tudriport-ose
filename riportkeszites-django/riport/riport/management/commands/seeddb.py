from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from os import path

from common.enum3 import bool_to_enum3
from riport.models.external import Type, Typesubtype, Character, Location, Container, Language
from tudriport.common.config import getconfig

MISSING_DIMENSION_ID = getconfig('sqlimport.MISSING_DIMENSION_ID')

class Command(BaseCommand):
    help='Adatbázis feltöltése induló adatokkal (seed)'

    def add_arguments(self, parser):
        parser.add_argument('-t', '--effective_timestamp', help='Milyen időbélyeggel történjen az inicializálás? Default: most. Formátuma: YYYY-MM-DD HH24:MI:SS')

    def handle(self, *args, **options):
        if options['effective_timestamp']:
            effective_timestamp = timezone.make_aware(parse_datetime(options['effective_timestamp']))
        else:
            effective_timestamp = timezone.now()

        self.seed_optional_models()

        # import languages data
        call_command('import_languages', file=path.join(settings.SITE_ROOT, 'resources', 'language.csv'))
        # import location data
        call_command('location_setting_parser', file=path.join(settings.SITE_ROOT, 'resources', 'location.csv'))

    def seed_optional_models(self):
        "Seed dimensions with MISSING_DIMENSION_ID"
        o_type, _created = Type.objects.get_or_create(
            id=MISSING_DIMENSION_ID,
            defaults={
                'type_name': getconfig('sqlimport.MISSING_DIMENSION_NAMES.TYPE'),
            }
        )

        o_typesubtype, _created = Typesubtype.objects.get_or_create(
                id=MISSING_DIMENSION_ID,
                defaults={
                    'subtype_name': getconfig('sqlimport.MISSING_DIMENSION_NAMES.SUBTYPE'),
                    'type': o_type,
                }
        )

        o_character, _created = Character.objects.get_or_create(
                id=MISSING_DIMENSION_ID,
                defaults={
                    'name': getconfig('sqlimport.MISSING_DIMENSION_NAMES.CHARACTER'),
                }
        )

        o_location, _created = Location.objects.get_or_create(
                id=MISSING_DIMENSION_ID,
                defaults={
                    'country': getconfig('sqlimport.MISSING_DIMENSION_NAMES.GENERAL'),
                    'city': getconfig('sqlimport.MISSING_DIMENSION_NAMES.GENERAL'),
                    'interior': False,
                    'exterior': False,
                }
        )

        o_language, _created = Language.objects.get_or_create(
                id=MISSING_DIMENSION_ID,
                defaults={
                    'name': getconfig('sqlimport.MISSING_DIMENSION_NAMES.LANGUAGE'),
                    'is_hungarian': False,
                    'contains_hungarian': False,
                    'is_english': False,
                    'contains_english': False,
                    'all_non_hungarian': False,
                    'all_main_lang': False,
                }
        )

        try:
            o_container = Container.objects.get_or_create(id=MISSING_DIMENSION_ID)
        except ObjectDoesNotExist:
            o_container = Container(
                    id=MISSING_DIMENSION_ID,             
                    groupid=MISSING_DIMENSION_ID,
                    ISSNs=[],
                    peerreviewed=bool_to_enum3(False),
                    valid_from=parse_datetime(getconfig('common.epoch')),
            )
            o_container.save(versioning=False)
