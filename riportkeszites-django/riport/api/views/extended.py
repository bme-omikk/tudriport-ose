from functools import partial
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import views
from rest_framework.response import Response
from rest_framework import status

import tempfile
from api.external import import_ext_authorlist_parser
from api.permissions import PermissionBasedPermission

from api.serializers.extended import (ExtAuthorListSerializer, MtmtIdSerializer, MtmtIdListSerializer,
    ExtendedUserSerializer)

from db.importlib.input_queue import input_queue_dbwrite
from riport.models.base import ExtendedUser
from riport.models.external import ExtAuthorlist, AuthorDb, Language, Location, Type, Typesubtype, Character, InputQueue, Publication, PublicationDescription
from riport.models.external import INPUT_QUEUE_STATUS_NEW, INPUT_QUEUE_TYPE_AUTHOR, INPUT_QUEUE_TYPE_PUBLICATION
from riport.models.external import INPUT_QUEUE_PRIORITY_WEB_REQUEST_SINGLE, INPUT_QUEUE_PRIORITY_WEB_REQUEST_MULTIPLE
from tudriport.common.config import getconfig

from django.utils import timezone
from django.db.models import F, Q, OuterRef, Subquery
from django.forms.models import model_to_dict
from django.utils.translation import activate
from django.utils.translation import get_language

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

DEFAULT_IMPORT_SOURCE = getconfig('input_sources.default_sourceid')

class AuthenticatedUser(views.APIView):
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                extended_user = ExtendedUser.objects.get(user=request.user)
            except ObjectDoesNotExist:
                extended_user = ExtendedUser.objects.create(user=request.user)

            return Response(ExtendedUserSerializer(extended_user).data)
        else:
            return Response({})


class ImportExtAuthorlist(views.APIView):
    permission_classes = [partial(PermissionBasedPermission, 'riport.add_extauthorlist'), ]
    http_method_names = ['post', ]

    def post(self, request, *args, **kwargs):
        fs = ExtAuthorListSerializer(data=request.data)
        if fs.is_valid():
            file_data = fs.data['file_data']
            fd, path = tempfile.mkstemp()
            with open(fd, 'wt', encoding='utf-8') as f:
                f.write(file_data)

            import_ext_authorlist_parser(path, fs.data['org'], fs.data['unit'], fs.data['subunit'], fs.data['subsub_unit'])
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(fs.errors, status=status.HTTP_400_BAD_REQUEST)


class InputQueueStatusView(views.APIView):
    permission_classes = [partial(PermissionBasedPermission, 'riport.view_inputqueue'), ]
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        objects = InputQueue.objects.filter(status=INPUT_QUEUE_STATUS_NEW)
        author_count = objects.filter(type=INPUT_QUEUE_TYPE_AUTHOR).count()
        all_count = objects.count()
        data = {
            'waitingAuthors': author_count,
            'waitingPublications': all_count - author_count
        }

        return Response(data=data)


class InputQueueAddAuthor(views.APIView):
    permission_classes = [partial(PermissionBasedPermission, 'riport.update_author'), ]
    http_method_names = ['post', ]

    def post(self, request, *args, **kwargs):
        serializer = MtmtIdSerializer(data=request.data)
        if serializer.is_valid():
            input_queue_dbwrite(DEFAULT_IMPORT_SOURCE, INPUT_QUEUE_TYPE_AUTHOR, serializer.data['mtmt_id'], command_source=self.__class__.__name__, priority=INPUT_QUEUE_PRIORITY_WEB_REQUEST_SINGLE)
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InputQueueAddAuthors(views.APIView):
    permission_classes = [partial(PermissionBasedPermission, 'riport.update_author'), ]
    http_method_names = ['post', ]

    def post(self, request, *args, **kwargs):
        serializer = MtmtIdListSerializer(data=request.data)
        if serializer.is_valid():
            for mtmt_id in serializer.data['mtmt_id_list']:
                input_queue_dbwrite(DEFAULT_IMPORT_SOURCE, INPUT_QUEUE_TYPE_AUTHOR, mtmt_id, command_source=self.__class__.__name__, priority=INPUT_QUEUE_PRIORITY_WEB_REQUEST_MULTIPLE)
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InputQueueAddPublication(views.APIView):
    permission_classes = [partial(PermissionBasedPermission, 'riport.update_publication'), ]
    http_method_names = ['post', ]

    def post(self, request, *args, **kwargs):
        serializer = MtmtIdListSerializer(data=request.data)
        if serializer.is_valid():
            for mtmt_id in serializer.data['mtmt_id_list']:
                input_queue_dbwrite(DEFAULT_IMPORT_SOURCE, INPUT_QUEUE_TYPE_PUBLICATION, mtmt_id, command_source=self.__class__.__name__, priority=INPUT_QUEUE_PRIORITY_WEB_REQUEST_MULTIPLE)
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AvailableOrganizations(views.APIView):
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        dbdatetime = self.request.GET.get('dbdatetime') or timezone.now() 
        data = [element['org'] for element in ExtAuthorlist.get_valid_objects(querytime=dbdatetime).values('org').distinct().all()]
        return Response(data=data)


class AvailableUnits(views.APIView):
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        dbdatetime = self.request.GET.get('dbdatetime') or timezone.now() 
        objects = ExtAuthorlist.get_valid_objects(querytime=dbdatetime).filter(org=kwargs['org']).values('unit').order_by('unit').distinct().all()        
        data = [element['unit'] for element in objects]
        return Response(data=data)


class AvailableSubUnits(views.APIView):
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        dbdatetime = self.request.GET.get('dbdatetime') or timezone.now() 
        objects = ExtAuthorlist.get_valid_objects(querytime=dbdatetime).filter(org=kwargs['org']).filter(unit=kwargs['unit']).values('subunit').order_by('subunit').distinct().all()        
        data = [element['subunit'] for element in objects]
        return Response(data=data)


class AvailableSubSubUnits(views.APIView):
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        dbdatetime = self.request.GET.get('dbdatetime') or timezone.now() 
        objects = ExtAuthorlist.get_valid_objects(querytime=dbdatetime)\
            .filter(org=kwargs['org'])\
            .filter(unit=kwargs['unit'])\
            .filter(subunit=kwargs['subunit'])\
            .values('subsub_unit').order_by('subsub_unit').distinct().all()
        data = [element['subsub_unit'] for element in objects]
        return Response(data=data)        

class AvailableAuthors(views.APIView):
    http_method_names = ['get', ]   

    def get(self, request, *args, **kwargs):
        dbdatetime = self.request.GET.get('dbdatetime') or timezone.now() 
        objects = ExtAuthorlist.get_valid_objects(querytime=dbdatetime)
        if 'org' in kwargs:
            objects = ExtAuthorlist.get_valid_objects().filter(org=kwargs['org'])
        if 'unit' in kwargs:
            objects = objects.filter(unit=kwargs['unit']) 
        if 'subunit' in kwargs:
            objects = objects.filter(subunit=kwargs['subunit'])
        if 'subsubunit' in kwargs:
            objects = objects.filter(subsubunit=kwargs['subsubunit'])
        objects = objects.order_by('mtmtcode', F('supervisor_mtmt_authid').asc(nulls_first=False), 'personname').distinct('mtmtcode').values('id')
        objects = ExtAuthorlist.objects.filter(id__in=Subquery(objects)).values().order_by('personname')
        authorcomment_subquery = AuthorDb.objects.filter(mtmt_authid=OuterRef('mtmtcode')).values('authorcomment')[:1]
        objects = objects.annotate(authorcomment=Subquery(authorcomment_subquery)).values()

        return Response(data=list(objects))

class ManageExtAuthor(views.APIView):
    http_method_names = ['post', 'delete', ]
    permission_classes = [partial(PermissionBasedPermission, 'riport.view_admin_page'), ]
    def post(self, request, *args, **kwargs):      
        if 'id' in request.data:
            newauthor = ExtAuthorlist.get_valid_objects().get(id=request.data['id'])
            newauthor.update_if_differs(request.data, save=True)
            return Response(status=status.HTTP_200_OK, data=model_to_dict(newauthor))             
        else:
            newauthor = ExtAuthorlist(**request.data)
            newauthor.save()
            return Response(status=status.HTTP_201_CREATED, data=model_to_dict(newauthor))
                   
                    
    def delete(self, request, *args, **kwargs):
        try:
            to_delete = ExtAuthorlist.get_valid_objects().get(id=kwargs['id'])
            to_delete.delete()
            return Response(status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class AvailableTypes(views.APIView):
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):        
        objects = Type.objects.values('id', 'type_name')
        return Response(data=list(objects))    

class AvailableTypesubtypes(views.APIView):
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        objects = Typesubtype.objects.values('id', 'type', 'subtype_name')
        if 'type' in kwargs:
            objects = objects.filter(type=kwargs['type'])
        return Response(data=list(objects))

class AvailableCharacters(views.APIView):
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        objects = Character.objects.exclude(id=0).values('id', 'name')
        return Response(data=list(objects))

class DashboardGeneral(views.APIView):
    permission_classes = [partial(PermissionBasedPermission, 'riport.general_admin'), ]
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        data = {"LangWarningsCount": Language.objects.filter(warning=True).count(),
                "LocationWarningsCount": Location.objects.filter(warning=True).count()}
        return Response(data=data)


class ToggleUserGroup(views.APIView):
    permission_classes = [partial(PermissionBasedPermission, 'riport.change_extendeduser'), ]
    http_method_names = ['post', ]

    def post(self, request, *args, **kwargs):
        try:
            user = User.objects.get(id=kwargs.get('user'))
            group = Group.objects.get(name=kwargs.get('group'))
        except User.DoesNotExist:
            return Response("User does not exits.", status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response("Group does not exits.", status=status.HTTP_404_NOT_FOUND)

        if group in user.groups.all():
            user.groups.remove(group)
        else:
            user.groups.add(group)

        return Response(status=status.HTTP_200_OK)


class AvailablePointModes(views.APIView):
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        return Response(data=getconfig('riport.modes'))


class AvailableGroups(views.APIView):
    permission_classes = [partial(PermissionBasedPermission, 'riport.change_extendeduser'), ]
    http_method_names = ['get', ]

    def get(self, request, *args, **kwargs):
        return Response(data=getconfig('django.groups'))

class CitationDuplums(views.APIView):
    http_method_names = ['get', ]
    permission_classes = [partial(PermissionBasedPermission, 'riport.view_admin_page'), ]
    def get(self, request, *args, **kwargs):
        dbdatetime = self.kwargs.get('dbdatetime') or timezone.now()
        duplums = Publication.get_valid_objects(dbdatetime).filter(Q(has_citation_duplicate_doi=True) | Q(has_citation_duplicate_title=True) | Q(has_citation_not_published=True) | Q(has_citation_citingdoc_not_published=True) | Q(has_citation_citingdoc_w_error=True) | Q(has_citation_unknown_external=True)).values_list('publication_description_id', flat=True)
        descriptions = PublicationDescription.objects.filter(id__in=duplums).values('mtmt_pubid', 'label_txt', 'citation_duplicate_doi_info', 'citation_duplicate_title_info',
         'citation_list_not_published', 'citation_list_citingdoc_not_published', 'citation_list_citingdoc_w_error', 'citation_list_unknown_external').order_by('mtmt_pubid')
        return Response(data=list(descriptions))

#Egyes pontozási módokhoz szükséges plusz mezők
class ExtraFields(views.APIView):
    http_method_names = ['get', ]
    def get(self, request, *args, **kwargs):
        return Response(data=getconfig('riport.extra-fields')[kwargs['mode']])

@method_decorator(ensure_csrf_cookie, name='dispatch')
class ClientConfig(views.APIView):
    http_method_names = ['get', ]
    def get(self, request, *args, **kwargs):
        return Response(data={
            'config' : getconfig('client_config'),
            'currentLanguage': get_language()
            })

class SwitchLanguage(views.APIView):
    http_method_names = ['get', ]
    def get(self, request, *args, **kwargs):   
        activate(self.kwargs.get('language_code'))       
        
        return Response(data='activated langugage: ' + self.kwargs.get('language_code') + ' currentLanugage:' + get_language())