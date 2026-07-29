from copy import deepcopy

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils import timezone
from django.db.models import OuterRef, Subquery
from django.db.models.query import QuerySet

from common.constants import EXT_AUTHOR_DEFAULT_WORLD_NAME, TUDRIPORT_VIEW_TYPES

from riport.models.external import AuthorDb, Container, Pubauthors, Published, Pubref, ExtAuthorlist

class PUB_UTIL:  
    """Pontozókhoz ősosztály."""
    TOKENEK={}

    # alltoken: (pubid, token, tokenkieg, talalatsuly, debuginfo)
    def __init__(self, is_aggregation_aware, aggregate_extraInfo=False):
        self.is_aggregation_aware = is_aggregation_aware
        self.aggregate_extraInfo = aggregate_extraInfo
        self.summary = None
        self.params = self.set_params_default()
        self.create_tokenek()
        # minimumkövetelmények/extrainfó számításához
        self.extraInfo = {
        }

    @classmethod
    def get_world_name(cls):
        """Return the name of the world where authors are retrieved from."""
        return EXT_AUTHOR_DEFAULT_WORLD_NAME

    @classmethod
    def get_author_object_to_score(cls, mtmt_id, dbdatetime):
        """Return the ExtAuthorlist object for the given mtmt_id to be used."""
        # author_to_score:
        #  - TODO: ha kaptunk kívülről, akkor ez egy ExtAuthorlist objektum, akit pontozunk
        #  - ha nem kaptunk kívülről, akkor megkeressük heurisztika szerint a pontozandó ExtAuthorlist objekumot, éz azt táolja, ha találunk.
        #  - ha nem találtunk, akkor csak az 'mtmtcode' mező kerül kitöltésre az értékelt szerző authorid-jével
        try:
            # a pontozóhoz tartozó világ szerzői
            _author_obj = ExtAuthorlist.get_valid_objects(querytime=dbdatetime).filter(world=cls.get_world_name()).filter(mtmtcode=mtmt_id)
            # heurisztika példákat lásd a GPK PhD pontozóban
            # determinisztikus rendezés a végére
            _author_obj = _author_obj.order_by('id')
            author_to_score = _author_obj.first()
        except ObjectDoesNotExist:
            author_to_score = ExtAuthorlist(mtmtcode=mtmt_id)

        return author_to_score

    def set_params_default(self):
        """Set scoring instance parameters' default values"""
        return {}

    def set_params(self, params):
        """Set scoring instance parameters. Returns the params and a list of warnings or empty list is all checks passed."""

        _warnings = []

        for pkey, pvalue in params.items():
            self.params[pkey] = pvalue

        return (self.params, _warnings)

    @classmethod
    def check_params(cls, view, params):
        """check the content of params dictionary for scoring view given in view. vies should take one of list/detail/adhoc
        Return the list of error messages or an empty list if no errors found.
        """
        msg=[]

        if view not in TUDRIPORT_VIEW_TYPES:
            msg.append('Invalid view type: %s'%(view))

        return msg

    def pub_util_pontozas(self, mtmt, dbdatetime, publisheds, pubrefs, weighting, supervisor_mtmt):
        if isinstance(publisheds, QuerySet):
            (fejlec, alltoken, extraInfo) = self.riportgen(mtmt, dbdatetime, publisheds, pubrefs, supervisor_mtmt)
        else:
            (fejlec, alltoken, extraInfo) = self.riportgen_publication(dbdatetime, publisheds, pubrefs, supervisor_mtmt)
        tokendict = {}
        for tok in alltoken:
            token = tok[1]
            if token == '':
                continue
            tokenkieg = tok[2]
            talalatsuly = tok[3]
            debuginfo = tok[4]
            # statisztika
            if token not in tokendict:
                tokendict[token]=[0., None, 0, [], [], []]            
            tokendict[token][0]+=talalatsuly
            tokendict[token][2]+=1
            tokendict[token][3].append(tok[0])            
            if token[:8] == 'CIT-IND,' and len(debuginfo) > 0:
                tokendict[token][4] += list(map(lambda x: int(x), debuginfo.split(',')))

            if type(tokenkieg) == float or type(tokenkieg) == int:
                if tokendict[token][1] is None:
                    tokendict[token][1]=tokenkieg*talalatsuly   
                else:
                    tokendict[token][1]+=tokenkieg*talalatsuly            
                if talalatsuly !=0 and round(1/talalatsuly, 4) == int(1/talalatsuly):
                    tokendict[token][5].append('{0}/{1}*{2}'.format(self.TOKENEK[tok[1]].score, str(int(1/talalatsuly)), str(tokenkieg)))
                else:
                    tokendict[token][5].append('{0}*{1}*{2}'.format(self.TOKENEK[tok[1]].score, str(round(talalatsuly, 2)), str(tokenkieg)))
            else:
                if talalatsuly !=0 and round(1/talalatsuly, 4) == int(1/talalatsuly):                    
                    tokendict[token][5].append('{0}/{1}'.format(self.TOKENEK[tok[1]].score, str(int(1/talalatsuly))))
                else:
                    tokendict[token][5].append('{0}*{1}'.format(self.TOKENEK[tok[1]].score, str(round(talalatsuly, 2))))
        '''if self.VERBOSE > 0: # részletek
            for tok in alltoken:
                print (tok)'''               
        tokendict = self.transform_tokendict(tokendict)        
        #print("\n# Részpontszám: TOKEN [hányszor, tokenkieg] PONT")
        points = 0
        tokenstat = {}  
        calculations = []     
        for tok in tokendict:
            if tok in self.TOKENEK:
                if tokendict[tok][1] is None:
                    pt = self.TOKENEK[tok].score * tokendict[tok][0]
                else:
                    pt = self.TOKENEK[tok].score * tokendict[tok][1]
                #print ("Részpontszám:", tok, tokendict[tok], pt)
                if tok[:8] != 'CIT-IND,':
                    pt = pt * weighting
                    if self.TOKENEK[tok].summable:
                        points += pt
                    citids = ''
                    if self.TOKENEK[tok].summable:       
                        calculations.append('+'.join(tokendict[tok][5]))
                else:
                    citids = tokendict[tok][4] # debuginfo
                tokenstat[tok] = (self.TOKENEK[tok], tokendict[tok], pt, citids, '+'.join(tokendict[tok][5]))

            else:
                print ("ERROR: ismeretlen token: \"%s\""%tok)
        #print ("Összpontszám:", points)
        sumOfCalculations = '+'.join(calculations)
        # részeredmenyek
        tokenstat_as_dict={}
        for tok in self.TOKENEK:
            tokdict={}
            # FIXME: talalat and talalat_kieg seem unused. Possibly remove?
            if tok in tokenstat:
                #tokdict['kategoria'] = tok
                tokdict['suly'] = tokenstat[tok][0].score
                tokdict['sulynev'] = tokenstat[tok][0].description
                tokdict['talalat'] = tokenstat[tok][1][2]
                tokdict['talalat_kieg'] = tokenstat[tok][1][1]
                tokdict['reszpont'] = tokenstat[tok][2]
                tokdict['szamolas'] = tokenstat[tok][4]
                if tok[:8] == 'CIT-IND,':
                    pubset = set()
                    [pubset.add(c) for c in tokenstat[tok][1][3]]
                    pubids = list(pubset)
                else:
                    pubids = tokenstat[tok][1][3]
                tokdict['pubids'] = pubids
                tokdict['citids'] = tokenstat[tok][1][4]
            else:
                tokdict['suly'] = self.TOKENEK[tok].score
                tokdict['sulynev'] = self.TOKENEK[tok].description
                tokdict['talalat'] = 0
                tokdict['talalat_kieg'] = 0
                tokdict['reszpont'] = 0
                tokdict['pubids'] = []
                tokdict['citids'] = []
            tokenstat_as_dict[tok] = tokdict

        # részletek
        alltoken_as_dict=[]
        for tok in alltoken:
            tokdict={}
            tokdict['publication_id']=tok[0]
            tokdict['kategoria']=tok[1]
            tokdict['kiegeszito_pont']=tok[2]
            tokdict['talalatsuly']=tok[3]
            tokdict['debuginfo']=tok[4]
            alltoken_as_dict.append(tokdict)

        extraInfo = self.transform_extraInfo(extraInfo, points)

        return {'fejlec': fejlec, 'osszpontszam': points, 'szamolas': sumOfCalculations, 'reszeredmenyek': tokenstat_as_dict, 'reszletek': alltoken_as_dict, 'extraInfo': extraInfo, 'tokenek':self.TOKENEK}

    def pub_util_riportgen(self, mtmt, dbdatetime, year, weighting=1, supervisor_mtmt=None):
        if dbdatetime is None:
            dbdatetime = timezone.now()

        publisheds = Published.get_valid_objects(querytime=dbdatetime).select_related().filter(author_db__mtmt_authid=mtmt)
        
        copy_of_unfiletered_publisheds = publisheds.all()
        pubrefs = Pubref.objects.filter(publication_id__in=copy_of_unfiletered_publisheds.values_list('publication_id'))

        publisheds = self.filter_for_year_publisheds(year, publisheds)
        pubrefs = self.filter_for_year_pubrefs(year, pubrefs)
        pubrefs = self.annotate_pubrefs(pubrefs, copy_of_unfiletered_publisheds)

        for pub in publisheds:
            _container = Container.get_valid_objects(querytime=dbdatetime).filter(groupid=pub.container_groupid).first()
            if _container:
                pub.ISSNs = _container.ISSNs
            else:
                pub.ISSNs = []

        result = self.pub_util_pontozas(mtmt, dbdatetime, publisheds, pubrefs, weighting, supervisor_mtmt)
        if self.summary is None:
            self.summary = deepcopy(result)
        else:
            self.merge_riports(self.summary, result)
        return result

    def merge_riports(self, summary, new_riport):
        for key, value in summary.items():
            if 0==1 \
                or key not in new_riport \
                or key == 'tokenek' \
                or (key == 'extraInfo' and not self.aggregate_extraInfo):
                    continue
            if new_riport[key] is not None:
                if isinstance(value, list):
                    summary[key].extend(new_riport[key])          
                elif isinstance(value, int): 
                    summary[key] += new_riport[key]               
                elif isinstance(value, float):
                    if key != 'suly':
                        summary[key] += new_riport[key]                  
                elif isinstance(value, dict):
                    self.merge_riports(summary[key], new_riport[key])
            
    def aggregate(self):
        # For empty aggregation call, we return empty aggregation
        if self.summary is None:
            return None

        for key, value in self.summary['reszeredmenyek'].items():
            self.summary['reszeredmenyek'][key]['citids'] = list(set(value['citids']))
            self.summary['reszeredmenyek'][key]['pubids'] = list(set(value['pubids']))
            self.summary['reszeredmenyek'][key]['talalat'] = len(value['pubids'])
            self.summary['reszeredmenyek'][key]['talalat_kieg'] = len(value['citids'])
            if key.startswith('CIT'):
                self.summary['reszeredmenyek'][key]['reszpont'] = len(value['citids']) * value['suly']

        if self.aggregate_extraInfo and 'extraInfo' in self.summary:
            for key, value in self.summary['extraInfo'].items():
                if isinstance(value, list):
                    self.summary['extraInfo'][key] = list(set(value))

        return self.summary

    def nullCounters(self):
        """Initialize(zero) counters in extraInfo, etc.
        Should be overridden in actual scoring classes.
        FIXME: probably this can be removed from all classes
        """
        pass

    def get_supervisor_pubauthor(self, published, supervisor_mtmt):
        try:
            author = AuthorDb.objects.get(mtmt_authid=supervisor_mtmt)
            return Pubauthors.objects.get(publication=published.publication, author_db=author.id)            
        except ObjectDoesNotExist:
            return None  
            
    def get_all_shares(self, published):
        return Pubauthors.objects.filter(publication=published.publication).values_list('share', flat=True)

    def pub_util_riportgen_publication(self, published, dbdatetime, year, supervisor_mtmt=None):
        pubrefs = Pubref.objects.filter(publication_id=published.publication_id)

        if year is not None:
            pubrefs = pubrefs.filter(year=year)
        return self.pub_util_pontozas(published, dbdatetime, published, pubrefs, 1, supervisor_mtmt)

    def create_tokenek(self):
        for scoring_token in self.TOKENLIST:
            self.TOKENEK[scoring_token.token]=scoring_token

    def filter_for_year_publisheds(self, year, publisheds):
        if year is not None:
            publisheds = publisheds.filter(pubdate=year)
        return publisheds

    def filter_for_year_pubrefs(self, year, pubrefs):
        if year is not None:
            pubrefs = pubrefs.filter(year=year)
        return pubrefs
    
    def annotate_pubrefs(self, pubrefs, publisheds):
        """Annotate pubrefs from publisheds, e.g. published_id"""
        related_published = publisheds.all().filter(publication_id=OuterRef("publication_id"))
        return pubrefs.annotate(related_published_id=Subquery(related_published.values("id")[:1]))

    def transform_tokendict(self, tokendict):
        return tokendict

    def transform_extraInfo(self, extraInfo, totalScore):
        """Például minimumkövetelmények számításához használjuk"""
        return extraInfo
