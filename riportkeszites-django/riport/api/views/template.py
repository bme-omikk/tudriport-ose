import importlib
import logging

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.forms.models import model_to_dict
from django.http import Http404
from django.utils import timezone
from rest_framework import views
from rest_framework.response import Response

from common.constants import TUDRIPORT_VIEW_TYPE_LIST, TUDRIPORT_VIEW_TYPE_DETAIL, TUDRIPORT_VIEW_TYPE_ADHOC

from api.utils import render_with_jinja
from riport.models.external import ExtAuthorlist, AuthorDb, Published, PublicationDescription
# Actual scoring module is imported using importlib.import_module call
#import scoring
from tudriport.common.config import getconfig
from django.utils.translation import activate
logger = logging.getLogger(__name__)

class BaseTemplateView(views.APIView):
    http_method_names = ['get', ]

    # view_type property should be given in descendant classes using a constant from TUDRIPORT_VIEW_TYPE_* 
    #view_type

    @classmethod
    def create_initial_context(cls, request, *args, **kwargs):
        """Create and return initial context."""
        context = {
            'params': {},
            'error_messages': [],
            'mode': kwargs.get('mode'),
        }

        # whitelisted parameters are passed from here
        # as defined for the scoring module in use
        _paramkeys = [ _e['id'] for _e in getconfig('riport.extra-fields')[context['mode']] ]
        # FIXME: 'year' is added by hardcoding, but should be removed once it becomes a definable parameter
        _paramkeys.append('year')
        for _key in _paramkeys:
            if _key in kwargs:
                context['params'][_key] = kwargs.get(_key)
            else:
                # list view passes some parameters in request not in URL template
                _value = request.GET.get(_key, None)
                if _value is not None:
                    context['params'][_key] = _value

        return context

    def get_context_data(self, context_received, *args, **kwargs):
        return context_received

    def get_additional_data(self):
        return {}

    def get_template_name(self):
        raise NotImplementedError

    @classmethod
    def validate(self, request, *args, **kwargs):
        if not kwargs.get('mode') in getconfig('riport.modes'):
            raise Http404

    def get(self, request, *args, **kwargs):
        self.validate(request, *args, **kwargs)
        context = self.create_initial_context(request, *args, **kwargs)
        #FIXME: remove this
        self.mode = context['mode']

        self.riport = importlib.import_module('scoring.riport_%s' % context['mode']).RIPORT()
        (_params, _warnings) = self.riport.set_params( context['params'] )
        context['error_messages'].extend(_warnings)
        context['params'] = _params

        context['error_messages'].extend(self.riport.check_params(self.view_type, context['params']))

        #FIXME: validate language code
        if self.request.GET.get('language_code'):
            activate(self.request.GET.get('language_code'))

        self.world = self.riport.get_world_name()

        data = {
            'language_code' : self.request.GET.get('language_code'),
            'additionalData': self.get_additional_data(),
            'htmlData': render_with_jinja(self.get_template_name(), self.get_context_data(context, *args, **kwargs))
        }
        return Response(data=data)

class AuthorListView(BaseTemplateView):

    view_type = TUDRIPORT_VIEW_TYPE_LIST

    def get_template_name(self):
        mode = self.mode
        # gtk_phd, gtk_habil, gtk_docens and gtk_temavezeto have a common template
        if mode in ['gtk_habil', 'gtk_docens', 'gtk_temavezeto', 'gtk_phd_eng']:
            mode = 'gtk_phd'
        if mode in ['gtk_ter_eng']:
            mode = 'gtk_ter'
        return 'jinja/riport_%s_list_template.html' % mode

    def get_queryset(self, world):
        org = self.kwargs.get('org') or ''
        unit = self.kwargs.get('unit') or ''
        subunit = self.kwargs.get('subunit') or ''
        subsub_unit = self.kwargs.get('subsub_unit') or ''
        dbdatetime = self.request.GET.get('dbdatetime') or timezone.now() 
        authors_at_hierarchy = ExtAuthorlist.get_valid_objects(querytime=dbdatetime).filter(world=world, org=org, unit=unit, subunit=subunit, subsub_unit=subsub_unit)
        authors_below_for_rollup = ExtAuthorlist.get_valid_objects(querytime=dbdatetime).filter(world=world, for_rollup=True)
        if unit == '':
            authors_below_for_rollup = authors_below_for_rollup.filter(org=org)
        elif subunit == '':
            authors_below_for_rollup = authors_below_for_rollup.filter(org=org, unit=unit)
        elif subsub_unit == '':
            authors_below_for_rollup = authors_below_for_rollup.filter(org=org, unit=unit, subunit=subunit)           

        return (authors_at_hierarchy | authors_below_for_rollup).order_by('personname').all()

    def get_context_data(self, context_received, *args, **kwargs):
        context = super().get_context_data(context_received, *args, **kwargs)

        year = self.request.GET.get('year', None)
        dbdatetime = self.request.GET.get('dbdatetime') or timezone.now()      

        context['object_list'] = []
        context['is_aggregation_aware'] = self.riport.is_aggregation_aware
        if not context['error_messages']:
            _empty=True
            for a in self.get_queryset(world=self.world):
                supervisor = None
                if a.supervisor_mtmt_authid is not None:
                    supervisor = AuthorDb.objects.filter(mtmt_authid=a.supervisor_mtmt_authid).first()
                context['object_list'].append({"author": a, "supervisor": supervisor, "points": self.riport.pub_util_riportgen(a.mtmtcode, dbdatetime, year, a.weighting, a.supervisor_mtmt_authid)})
                _empty = False
            if _empty:
                context['error_messages'].append("A feltételeknek megfelelő szerzők nem találhatók az adatbázisban.")
            if self.riport.is_aggregation_aware:
                context['summary'] = self.riport.aggregate()
        return context


class AuthorDetailView(BaseTemplateView):

    view_type = TUDRIPORT_VIEW_TYPE_DETAIL

    def get_template_name(self):
        mode = self.mode
        # gtk_phd, gtk_habil, gtk_docens and gtk_temavezeto have a common template
        if mode in ['gtk_habil', 'gtk_docens', 'gtk_temavezeto', 'gtk_phd_eng']:
            mode = 'gtk_phd'
        if mode in ['gtk_ter_eng']:
            mode = 'gtk_ter'
        return 'jinja/riport_%s_template.html' % mode

    def get_context_data(self, context_received, *args, **kwargs):
        context = super().get_context_data(context_received, *args, **kwargs)
        
        mtmt_id = self.kwargs.get('mtmt_id') or None           
        year = self.kwargs.get('year') or None            
        dbdatetime = self.request.GET.get('dbdatetime') or timezone.now() 
        supervisor_mtmt = self.request.GET.get('supervisor_mtmt_authid') or None

        if mtmt_id:
            author = AuthorDb.objects.filter(mtmt_authid=mtmt_id).first()
            ext_author = self.riport.get_author_object_to_score(mtmt_id, dbdatetime)
            if supervisor_mtmt is None and ext_author is not None:
                supervisor_mtmt = ext_author.supervisor_mtmt_authid
            if author is None and ext_author is None:
                context['error_messages'].append("Az értékelt szerző nem található az adatbázisban (id: %s)."%(mtmt_id))
            elif len(context['error_messages']) == 0:
                context.update({
                    'issummary': False,
                    'points': self.riport.pub_util_riportgen(mtmt_id, dbdatetime, year, 1, supervisor_mtmt)
                })
                # author data for the template based on AothorDb object, but filled from ExtAuthorlist object as needed
                _author_data_for_template = model_to_dict(author) if author is not None else { 'mtmt_authid': mtmt_id }
                if ext_author is not None:
                    _author_data_for_template['role'] = ext_author.role
                    if 'authorname' not in _author_data_for_template:
                        _author_data_for_template['authorname'] = ext_author.personname
                context.update({'author': _author_data_for_template})
                # supervisor data for the template from its AuthorDb object
                context.update({'supervisor': AuthorDb.objects.filter(mtmt_authid=supervisor_mtmt).first()})
                if any(weighting != 1.0 for weighting in ExtAuthorlist.get_valid_objects(querytime=dbdatetime).filter(mtmtcode=mtmt_id).values_list('weighting', flat=True)):
                    context.update({
                        'isriportcomment': True
                    })
        else:
            world = self.world
            org = self.kwargs.get('org') or ''
            unit = self.kwargs.get('unit') or ''
            subunit = self.kwargs.get('subunit') or ''
            subsub_unit = self.kwargs.get('subsub_unit') or ''
            dbdatetime = self.request.GET.get('dbdatetime') or timezone.now()
            authors_at_hierarchy = ExtAuthorlist.get_valid_objects(querytime=dbdatetime).filter(world=world, org=org, unit=unit, subunit=subunit, subsub_unit=subsub_unit)
            authors_below_for_rollup = ExtAuthorlist.get_valid_objects(querytime=dbdatetime).filter(world=world, for_rollup=True)
            if unit == '':
                authors_below_for_rollup = authors_below_for_rollup.filter(org=org)
            elif subunit == '':
                authors_below_for_rollup = authors_below_for_rollup.filter(org=org, unit=unit)
            elif subsub_unit == '':
                authors_below_for_rollup = authors_below_for_rollup.filter(org=org, unit=unit, subunit=subunit)  

            if len(authors_at_hierarchy | authors_below_for_rollup) == 0:
                context['error_messages'].append("Az értékelt szervezet nem található az adatbázisban.")
            elif len(context['error_messages']) == 0:
                for a in (authors_at_hierarchy | authors_below_for_rollup):
                    self.riport.pub_util_riportgen(a.mtmtcode, dbdatetime, year, a.weighting, a.supervisor_mtmt_authid)
                context.update({
                    'issummary': True,
                    'points': self.riport.aggregate()
                })
        return context

class AuthorAdhocView(BaseTemplateView):

    view_type = TUDRIPORT_VIEW_TYPE_ADHOC

    def get_template_name(self):
        mode = self.mode
        # gtk_phd, gtk_habil, gtk_docens and gtk_temavezeto have a common template
        if mode in ['gtk_habil', 'gtk_docens', 'gtk_temavezeto', 'gtk_phd_eng']:
            mode = 'gtk_phd'
        if mode in ['gtk_ter_eng']:
            mode = 'gtk_ter'
        return 'jinja/riport_%s_adhoc_template.html' % mode

    def get_queryset(self, world):
        try:                      
            mode = self.mode
            yearFrom = self.request.GET.get('year_from') or None
            yearTo = self.request.GET.get('year_to') or None
            typeId = self.request.GET.get('type') or None
            subTypeId = self.request.GET.get('subtype') or None
            characterId = self.request.GET.get('character') or None
            dbdatetime = self.request.GET.get('dbdatetime') or timezone.now()            
            author_mtid = self.request.GET.get('mtmt') or None
            pubids = self.request.GET.get('pubids') or None  
            org = self.request.GET.get('org') or None
            unit = self.request.GET.get('unit') or None
            subunit = self.request.GET.get('subunit') or None
            subsub_unit = self.request.GET.get('subsub_unit') or None 
            author_dbs = AuthorDb.objects
            if org or unit or subunit or subsub_unit:
                authors = ExtAuthorlist.get_valid_objects(querytime=dbdatetime).filter(world=world)
                if org:
                    authors = authors.filter(org=org)
                if unit:
                    authors = authors.filter(unit=unit)
                if subunit:
                    authors = authors.filter(subunit=subunit)
                if subsub_unit:
                    authors = authors.filter(subsub_unit=subsub_unit) 
                author_dbs = author_dbs.filter(mtmt_authid__in=authors.values_list('mtmtcode', flat=True))
            if author_mtid:
                author_dbs = author_dbs.filter(mtmt_authid=author_mtid) 
            publisheds = Published.get_valid_objects(querytime=dbdatetime)  
            if org or unit or subunit or subsub_unit or author_mtid:         
                publisheds = publisheds.filter(author_db__in=author_dbs.values_list('id', flat=True))
            if pubids:
                publisheds = publisheds.filter(mtmt_pubid__in=pubids.split(','))
            if yearFrom:
                publisheds = publisheds.filter(pubdate__gte=yearFrom)
            if yearTo:
                publisheds = publisheds.filter(pubdate__lte=yearTo)
            if typeId:
                publisheds = publisheds.filter(type_id=typeId)           
            if subTypeId:
                publisheds = publisheds.filter(typesubtype_id=subTypeId)
            if characterId:
                publisheds = publisheds.filter(character_id=characterId)
            publisheds = publisheds.distinct('publication_id')
            for published in publisheds:                
                published.description = PublicationDescription.objects.values().get(id=published.publication_description_id)                
            return publisheds

        except AuthorDb.DoesNotExist:
            raise Http404()
        except MultipleObjectsReturned:
            logger.error("Multiple objects returned at AuthorDetailView. Is more then one object valid at the same time??")
            raise
        except ObjectDoesNotExist:
            raise 
    

    def get_context_data(self, context_received, *args, **kwargs):
        context = super().get_context_data(context_received, *args, **kwargs)

        year = self.request.GET.get('year', None)
        dbdatetime = self.request.GET.get('dbdatetime', timezone.now())
        supervisor_mtmt = self.request.GET.get('supervisor_mtmt_authid') or None

        context['object_list'] = []
        if not context['error_messages']:
            _empty=True
            for published in self.get_queryset(self.world):
                context['object_list'].append({"publication": published, "points": self.riport.pub_util_riportgen_publication(published, dbdatetime, year, supervisor_mtmt)})
                _empty = False
            if _empty:
                context['error_messages'].append("A feltételeknek megfelelő közlemények nem találhatók az adatbázisban.")

        return context

    def get_additional_data(self):
        return ', '.join(map(str, self.get_queryset(self.world).values_list('mtmt_pubid', flat=True)))
