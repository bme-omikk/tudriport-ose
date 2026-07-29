''' Konstansokat kezelő modul
'''

# MTMT2 típusok
M2_OTYPE_CITY = 'City'
M2_OTYPE_COUNTRY = 'Country'
M2_OTYPE_RATING = 'RatingType'
M2_OTYPE_PREDATOR_RATING = 'PredatorRating'
M2_OTYPE_MTA_JOURNAL_RATING = 'MtaRating'
M2_OTYPE_INSTITUTE = 'Institute'
M2_OTYPE_INSTITUTE_CONTAINMENT = 'DivisionContainment'

COUNTRY_HUNGARY = 'Magyarország'
COUNTRY_ABROAD_UNKNOWN = '[ismeretlen külföldi ország]'
# dictionary, kulcsa az ország neve, hozzá tartozik városnevek listája,
# amiből COUNTRY_ABROAD_UNKNOWN országot kell generálni.
COUNTRY_ABROAD_UNKNOWN_TRANSLATE = {
    'Nemzetközi': ['Online kiadás', '[s.l.]'],
}
CITY_MISSING = '[hiányzó városnév]'
# városnevek listája, amiból Magyarország esetén CITY_MISSING várost kell generálni
CITY_MISSING_HUNGARY_TRANSLATE = ['h.n.', '[s. l.] - Magyarország']

SOURCENAME_DOI = 'DOI'
SOURCENAME_WOS = 'WoS'
SOURCENAME_SCOPUS = 'Scopus'
SOURCENAME_ISBN = 'ISBN'
SOURCENAME_FULL_DOC_URL = 'Teljes dokumentum'
SOURCENAME_OTHER_URL = 'Egyéb URL'

# szerzőség típusok
AUTHORTYPE_AUTHOR = 'author'
AUTHORTYPE_EDITOR = 'editor'

# MTA folyóiratranking: a feldolgozott bizottságok kódjának listája
MTA_RANKING_COMMITTEE_LIST = ['GMB']

# az MTA listán kifogásolhatóként szerepeltetett folyóiratokra vonatkozó RatingType
MTA_LISTED_ZERO_RATING_CODE = 'norveg'

# Affiliációk kezeléséhez intézmény/szervezeti egység lista: MTMT azonosítókat rendel mezőnévhez (szimbolikus intézményi névhez)
M2_AFFILIATED_INSTITUTES = {
    10256: 'BME_EMK',
    10167: 'BME_EPK',
    10333: 'BME_GPK',
    10435: 'BME_GTK',
    10430: 'BME_KJK',
    14827: 'BME_KJK', # BME Kozlekedesmernoki Kar (2000-2012)
    10329: 'BME_TTK',
    10460: 'BME_VBK',
    14739: 'BME_VBK', # BME Vegyeszmernoki Kar (2000-2006)
    10135: 'BME_VIK',
    119: 'BME',
    14642: 'BME', # Budapesti Muszaki Egyetem (1949-2000)
}

# GPK PhD pontozáshoz extra mezőket tartalmazó URL prefix:
# Ebből töltjük ki az AbstractPublication.bme_gpk_phd_description mezőt
EXTRA_BME_GPK_PHD_PREFIX = 'https://phd.gpk.bme.hu/pub/'

# source id
INPUT_SOURCE_MTMT2 = 'mtmt2'

# ennek a rendszernek a kódneve
TUDRIPORT_SYSTEM_NAME = 'tudriport'

# értékelési módok/nézetek
TUDRIPORT_VIEW_TYPE_LIST = 'list'
TUDRIPORT_VIEW_TYPE_DETAIL = 'detail'
TUDRIPORT_VIEW_TYPE_ADHOC = 'adhoc'

TUDRIPORT_VIEW_TYPES = [TUDRIPORT_VIEW_TYPE_LIST, TUDRIPORT_VIEW_TYPE_DETAIL, TUDRIPORT_VIEW_TYPE_ADHOC]

# tűréshatár a szerzői részesedések összegének vizsgálatakor
EPSILON_AUTHOR_SHARE = 0.001

# párhuzamos névsorok (világok) kezelésekor az alapértelmezett világ neve
EXT_AUTHOR_DEFAULT_WORLD_NAME ='default'