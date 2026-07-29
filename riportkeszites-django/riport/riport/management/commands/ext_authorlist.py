#!/usr/bin/env python3
from django.core.management import BaseCommand, CommandError
from riport.models.external import ExtAuthorlist
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from common.constants import EXT_AUTHOR_DEFAULT_WORLD_NAME

import logging

logger = logging.getLogger(__name__)

MODULE_NAME = 'ext_authorlist'
SEPARATOR = ':'
ORGANISATION_LEVEL_COUNT=4
BASIC_FIELD_COUNT = 6


class Command(BaseCommand):
    help = 'ext_authorlist feltöltése'

    def add_arguments(self, parser):       
        parser.add_argument('-f', '--file', required=True, help='Melyik fájlból olvassa be?')
        parser.add_argument('-w', '--world', default=EXT_AUTHOR_DEFAULT_WORLD_NAME, help='Névtér (világ), amin belül a névsort kezeljük.')
        parser.add_argument('--org', nargs='*',help='''Szervezeti hierarchia, ahova a névsor betöltése történjen. 0-4 szint (string) adható meg, ezek sorban:
         - org: szervezet neve (pl. BME vagy MTA),
         - unit: részleg neve, (pl. GPK vagy MTA-osztály),
         - subunit: alrészleg neve, (pl. ATT vagy MTA-???),
         - subsubunit: al-al részleg neve, (pl. laborcsoport, tipikusan hiányzik).
        Kötelező legalább 3 szintet megadni, kivéve ha a fájlban szerepel a szervezeti hierarchia (lásd --hierarchy_included).''')
        parser.add_argument('--hierarchy_included', type=int, default=0, help='Az input fájl első mezőiben szerepeltethető a hierarchia. Lehetséges értékek: 0 1 2 3 vagy 4. Itt azt kell megadni, hogy hány oszlop tartalmazza a hierarchia-információt. Az org/unit/subunit/subsub_unit közül a kitöltöttek után fűződnek hozzá a betöltéskor a fájlban szereplő hierarchia-szintek. Az org/unit/subunit/subsub_unit közül megadottak és a fájlban szereplő szintek száma legalább 3, legfeljebb 4 lehet.')
        parser.add_argument('--use_header', action='store_true', help='Az input fájl első sorában levő sort headerként használja (függetlenül attól, hogy # (komment) jellel kezdődik-e). Ez szolgáltatja a kulcsokat az extrainfo mező kitöltéséhez. Az alapértelmezett mezők után megjelenő mezők kerülnek ide.')
        parser.add_argument('--remove_others', action='store_true', help='Ha meg van adva, eltávolítja a szerzőlistából azokat, akik nem érkeztek az input fájlban. Csak a 4-szintű hierarchia szerint pontosan ide soroltakat vizsgálja az eltávolítás érdekében, az alrészlegekből nem távolít el.')
        parser.add_argument('--dry_run', action='store_true', help='Ha meg van adva, akkor nem történik tényleges módosítás.')

    def handle(self, *args, **options):
        was_error = False
        effective_datetime = timezone.now()
        dry_run = options['dry_run']

        fname = options['file']
        orgcount_in_file=options['hierarchy_included']
        use_header = options['use_header']

        world = options['world']

        # parancssorban érkezett szervezeti szintek száma és listája
        org_prefix=[o.strip() for o in options['org'] if o and o.strip()]
        orgcount_prefix = len(org_prefix)

        if orgcount_prefix + orgcount_in_file < 3 or orgcount_prefix + orgcount_in_file > 4:
            logger.error('A parancssorban (--org) és a fájl sorainak elején (--hierarchy_included) összesen 3 vagy 4 szervezeti hierarchiaszintet kell megadni!')
            was_error = True

        if was_error:
            logger.error('A betöltő hibával ért véget. =========-')
            raise CommandError()

        if orgcount_in_file > 0:
            logger.info('Feldolgozás indul, szervezet: %s.%s'%('/'.join(org_prefix), ' (DRY RUN, nem módosítunk)' if dry_run else ''))
            authors_parse_from_file_w_hierarchy(world, fname, org_prefix, orgcount_in_file, options['remove_others'], effective_datetime, use_header, dry_run)
        else:
            logger.info('Feldolgozás indul, szervezet: %s.%s'%('/'.join(org_prefix), ' (DRY RUN, nem módosítunk)' if dry_run else ''))
            authors_parse_from_file(world, fname, org_prefix, options['remove_others'], effective_datetime, use_header, dry_run)

        logger.info('Feldolgozás vége, szervezet: %s.%s'%('/'.join(org_prefix), ' (DRY RUN, nem módosítunk)' if dry_run else ''))

# B***** E***:Oktató:1:mtmt:100****
def authorline_parser(line_default, line_raw, extrainfo_headers):
    line_parsed = line_default.copy()
    f = line_raw.rstrip().split(SEPARATOR)
    if f[3] == 'mtmt':
        line_parsed['personname'] = f[0]
        line_parsed['role'] = f[1]
        line_parsed['weighting'] = float(f[2])

        try:
            line_parsed['mtmtcode'] = int(f[4])
        except ValueError as e:
            logger.warning('Hibás vagy hiányzó MTMT azonosító miatt nem feldolgozott sor: "%s".'%(line_raw))
            return None

        if len(f)>5 and f[5] != '':
            line_parsed['supervisor_mtmt_authid'] = int(f[5])

        line_parsed['extrainfo'] = {}
        for i in range(0, len(extrainfo_headers)):
            _field_idx = BASIC_FIELD_COUNT+i
            if len(f) > _field_idx:
                _value = f[BASIC_FIELD_COUNT+i].strip()
                if _value:
                    line_parsed['extrainfo'][extrainfo_headers[i]]=_value
            else:
                break
    
        return line_parsed
    else:
        logger.warning('Nem felismert forrásadatbázis (%s) miatt nem feldolgozott sor: "%s".'%(f[3], line_raw))
        return None

def parse_extrainfo_header(header_line, skip_field_count):
    f = header_line.strip().split(SEPARATOR)
    return f[skip_field_count:]


def authorline_writer(world, authorline, dry_run):
    if not dry_run:
        try:
            author = ExtAuthorlist.get_valid_objects().get(world=world, org=authorline['org'], unit=authorline['unit'], subunit=authorline['subunit'], subsub_unit=authorline['subsub_unit'], mtmtcode=authorline['mtmtcode'])
            changed_fields_exist = author.update_if_differs(authorline, save=True)
        except ObjectDoesNotExist:
            new_author = ExtAuthorlist(world=world, **authorline)
            new_author.save()
            return

# API kompatibilitási wrapper, az első nem üres és nem None szervezeti szintig dolgozzuk fel
def authors_parse_from_file_wrapper(fname, org, unit, subunit, subsub_unit='', remove_others=False, effective_datetime=timezone.now(), use_header=False, dry_run=False):
    org_prefix = []
    for o in [org, unit, subunit, subsub_unit]:
        if o:
            org_prefix.append(o.strip())
        else:
            break

    authors_parse_from_file(fname, org_prefix, remove_others, effective_datetime, use_header, dry_run)


def authors_parse_from_file(world, fname, org_prefix, remove_others, effective_datetime, use_header, dry_run):
    authorlist = []

    extrainfo_headers = []
    header_seen = False

    for row in open(fname, 'r', encoding='utf-8'):
        if use_header and not header_seen:
            extrainfo_headers = parse_extrainfo_header(row, BASIC_FIELD_COUNT)
            header_seen = True
            continue
        if row[0] == '#':
            continue
        authorlist.append(row.rstrip())

    authors_parse_from_list(world, authorlist, org_prefix, remove_others, effective_datetime, extrainfo_headers, dry_run)

def authors_parse_from_file_w_hierarchy(world, fname, org_prefix, orgcount_in_file, remove_others, effective_datetime, use_header, dry_run):
    orgcount_prefix = len(org_prefix)
    authorlist_by_hierarchy = {}

    extrainfo_headers = []
    header_seen = False

    # generate name list for each organisation
    for row in open(fname, 'r', encoding='utf-8'):
        row = row.strip()
        if use_header and not header_seen:
            extrainfo_headers = parse_extrainfo_header(row, orgcount_prefix+BASIC_FIELD_COUNT)
            header_seen = True
            continue
        if row[0] == '#':
            continue
        f = [e.strip() for e in row.split(SEPARATOR)]
        if '' in f[:orgcount_in_file] or None in f[:orgcount_in_file]:
            logger.warning('Hiányos szervezet infó miatt kihagyott sor: "%s".'%(row))
            continue

        hierarchy_key = SEPARATOR.join(f[:orgcount_in_file])
        authorline = SEPARATOR.join(f[orgcount_in_file:])
        if hierarchy_key not in authorlist_by_hierarchy:
            authorlist_by_hierarchy[hierarchy_key] = []
        authorlist_by_hierarchy[hierarchy_key].append(authorline)

    # process each organisation
    orgs_seen=[]
    for org_key, authorlist in authorlist_by_hierarchy.items():
        org = org_prefix.copy()
        org.extend(org_key.split(SEPARATOR))
        orgs_seen.append([o.strip() for o in org])

        authors_parse_from_list(world, authorlist, org, remove_others, effective_datetime, extrainfo_headers, dry_run)

    if remove_others:
        # Nem látottakat lezárni
        notseen = ExtAuthorlist.get_valid_objects().filter(world=world)
        if len(org_prefix)>3:
            notseen = notseen.filter(subsub_unit=org_prefix[3])
        if len(org_prefix)>2:
            notseen = notseen.filter(subunit=org_prefix[2])
        if len(org_prefix)>1:
            notseen = notseen.filter(unit=org_prefix[1])
        if len(org_prefix)>0:
            notseen = notseen.filter(org=org_prefix[0])

        for o in orgs_seen:
            if (len(o)==1):
                notseen = notseen.exclude(org=o[0])            
            if (len(o)==2):
                notseen = notseen.exclude(org=o[0], unit=o[1])            
            if (len(o)==3):
                notseen = notseen.exclude(org=o[0], unit=o[1], subunit=o[2])            
            if (len(o)==4):
                notseen = notseen.exclude(org=o[0], unit=o[1], subunit=o[2], subsub_unit=o[3])            

        logger.info('A betöltendő névsorban nem látott alintézményekhez tartozó szerzők eltávolításra kerülnek a %s szervezetből: %s.'%(org_prefix, ','.join([str(x.mtmtcode)+'('+(','.join([x.org, x.unit, x.subunit, x.subsub_unit]))+')' for x in notseen]) or 'nem történt ilyen'))
        if not dry_run:
            notseen.update(valid_to=effective_datetime)

def authors_parse_from_list(world, authorlist, org_prefix, remove_others, effective_datetime, extrainfo_headers, dry_run):
    org = org_prefix.copy()
    while len(org) < ORGANISATION_LEVEL_COUNT:
        org.append('')
    author_default = {
        'org': org[0].strip(),
        'unit': org[1].strip(),
        'subunit': org[2].strip(),
        'subsub_unit': org[3].strip(),
        'supervisor_mtmt_authid': None,
        'neptuncode': ''
    }

    org_string = '%s/%s/%s/%s'%(author_default['org'], author_default['unit'], author_default['subunit'], author_default['subsub_unit'])

    logger.info('Betöltendő %s szerző, world: %s, szervezet: %s'%(len(authorlist), world, org_string))

    author_ids_seen = []

    for row in authorlist:
        author_data = authorline_parser(author_default, row, extrainfo_headers)
        if author_data:
            if author_data['mtmtcode'] in author_ids_seen:
                logger.warning('Duplán szerepel a %s szervezetben (world: %s): %s, az adatait frissítjük (többedszer).'%(org_string, world, author_data['mtmtcode']))
            author_ids_seen.append(author_data['mtmtcode'])
            authorline_writer(world, author_data, dry_run)

    if remove_others:
        # Nem látottakat lezárni
        notseen = ExtAuthorlist.get_valid_objects().filter(world=world, org=org[0], unit=org[1], subunit=org[2], subsub_unit=org[3]).exclude(mtmtcode__in=author_ids_seen)
        logger.info('Nem látottak, eltávolításra kerülnek a %s szervezetből: %s.'%(org_string, ','.join([str(x) for x in notseen.values_list('mtmtcode', flat=True)]) or 'nem történt ilyen'))
        if not dry_run:
            notseen.update(valid_to=effective_datetime)
