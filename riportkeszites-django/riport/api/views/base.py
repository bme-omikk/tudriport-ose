from rest_framework import viewsets
from api.permissions import ExtendedDjangoModelPermissions
from api.serializers.base import (LanguageSerializer, AuthorDbSerializer, AuthorDbIdentifierSerializer,
                                  AuthortypeSerializer, CharacterSerializer, ExtAuthorlistSerializer,
                                  ExtJournalClassificationSerializer, InputQueueSerializer, LocationSerializer,
                                  TypeSerializer, TypesubtypeSerializer, PublicationSerializer, PubauthorsSerializer,
                                  PubrefSerializer, ContainerSerializer)
from api.serializers.extended import ExtendedUserSerializer
from riport.models.base import ExtendedUser
from riport.models.external import (Publication, AuthorDb, AuthorDbIdentifier, Authortype, Character, Container,
                                    ExtAuthorlist, ExtJournalClassification, InputQueue, Language, Location, Type, Typesubtype,
                                    Pubauthors, Pubref)


class AuthorDbViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuthorDb.objects.all()
    serializer_class = AuthorDbSerializer
    ordering = ("authorname", )
    search_fields = ('mtmt_authid', 'authorname', 'authorcomment')


class AuthorDbIdentifierViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuthorDbIdentifier.objects.all()
    serializer_class = AuthorDbIdentifierSerializer
    search_fields = ('identifier', 'author_db', )


class AuthortypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Authortype.objects.all()
    serializer_class = AuthortypeSerializer
    ordering = ("name", )
    search_fields = ('name', )


class CharacterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Character.objects.all()
    serializer_class = CharacterSerializer
    ordering = ("name", )
    search_fields = ('chid_mtmt', 'name', )


class ContainerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Container.objects.all()
    serializer_class = ContainerSerializer
    ordering = ("issn1", )
    search_fields = ('issn1', 'issn2', 'peerreviewed', 'groupid', )


class ExtAuthorlistViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExtAuthorlist.objects.all()
    serializer_class = ExtAuthorlistSerializer
    ordering = ('org', 'unit', 'subunit', 'subsub_unit', 'personname', )
    search_fields = ('org', 'unit', 'subunit', 'subsub_unit', 'personname', 'role', 'neptuncode', 'supervisor_mtmt_authid',
                     'weighting', 'mtmtcode', )


class ExtJournalClassificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExtJournalClassification.objects.all()
    serializer_class = ExtJournalClassificationSerializer
    ordering = ('org', 'unit', 'name', )
    search_fields = ('org', 'unit', 'issn', 'eissn', 'category', 'international', 'shortname', 'name', )


class InputQueueViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InputQueue.objects.all()
    serializer_class = InputQueueSerializer
    ordering = ('status_date', )
    filterset_fields = ("status", )
    search_fields = ('source', 'type', 'identifier', 'status', 'status_date', 'processed_date', )


class LanguageViewSet(viewsets.ModelViewSet):
    permission_classes = [ExtendedDjangoModelPermissions, ]

    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    ordering = ("name", )
    search_fields = ('name', 'is_hungarian', 'is_english', 'contains_hungarian', 'contains_english', 'all_non_hungarian', 'all_main_lang', 'warning', )
    filterset_fields = ('warning', 'name')


class LocationViewSet(viewsets.ModelViewSet):
    permission_classes = [ExtendedDjangoModelPermissions, ]

    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    ordering = ('country', 'city', )
    search_fields = ('country', 'city', 'interior', 'exterior', 'warning', )
    filterset_fields = ('warning', )


class TypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Type.objects.all()
    serializer_class = TypeSerializer
    search_fields = ('type_mtmt', 'type_name', )


class TypesubtypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Typesubtype.objects.all()
    serializer_class = TypesubtypeSerializer
    search_fields = ('type', 'subtype_mtmt', 'subtype_name', )


class PublicationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    ordering = ('mtmt_pubid', )
    search_fields = ('typesubtype', 'container_groupid', 'character', 'impactfactor_value', 'impactfactor_isestimate',
                     'citescore_value', 'citescore_isestimate', 'sjr_value', 'sjr_rank', 'sjr_isestimate', 'sjr_isestimate', 'snip_isestimate',
                     'pubdate', 'language',
                     'peerreviewed', 'publisherlocation', 'publishinglocation', 'pagenum', 'wosdb', 'scopusdb',
                     'authorcount', 'editorcount', 'refcount', 'mtmt_pubid',)


class PubauthorsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pubauthors.objects.all()
    serializer_class = PubauthorsSerializer
    ordering = ('mtmt_pubauthorname', )
    search_fields = ('mtmt_pubauthorname', 'author_db', 'authortype', 'publication', 'share', 'position',
                     'isfirst', 'islast',)


class PubrefViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pubref.objects.all()
    serializer_class = PubrefSerializer
    ordering = ('mtmt_pubauthorname', )
    search_fields = ('mtmt_pubauthorname', 'author_db', 'authortype', 'publication', 'share', 'position',
                     'isfirst', 'islast', )


class ExtendedUsersViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExtendedUser.objects.all()
    serializer_class = ExtendedUserSerializer
    ordering = ("user", )
    search_fields = ('orgId', 'affiliation', 'user__first_name', 'user__last_name', 'user__email', )
