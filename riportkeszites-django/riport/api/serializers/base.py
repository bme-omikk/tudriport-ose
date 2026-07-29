from django.contrib import auth
from django.contrib.auth.models import User
from rest_framework import serializers
from riport.models.external import (Publication, AuthorDb, AuthorDbIdentifier, Authortype, Character, Container,
                                    ExtAuthorlist, ExtJournalClassification, InputQueue, Language, Location, Type, Typesubtype,
                                    Pubauthors, Pubref)


class UserSerializer(serializers.ModelSerializer):
    groups = serializers.StringRelatedField(many=True)
    permissions = serializers.SerializerMethodField()

    def get_permissions(self, instance):
        permissions = set()
        for backend in auth.get_backends():
          if hasattr(backend, "get_all_permissions"):
            permissions.update(backend.get_all_permissions(instance))
        return permissions

    class Meta:
        model = User
        fields = ('pk', 'username', 'first_name', 'last_name', 'email', 'groups', 'permissions', )


class AuthorDbSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AuthorDb
        fields = ('mtmt_authid', 'authorname', 'authorcomment', 'url', )


class AuthorDbIdentifierSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AuthorDbIdentifier
        fields = ('identifier', 'author_db', 'url', )


class AuthortypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Authortype
        fields = ('name', 'url', )


class CharacterSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Character
        fields = ('chid_mtmt', 'name', 'url', )


class ContainerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Container
        fields = ('issn1', 'issn2', 'peerreviewed', 'groupid', 'url', )


class ExtAuthorlistSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ExtAuthorlist
        fields = ('org', 'unit', 'subunit', 'subsub_unit', 'personname', 'role', 'neptuncode', 'supervisor_mtmt_authid',
                  'weighting', 'mtmtcode', 'url', )


class ExtJournalClassificationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ExtJournalClassification
        fields = ('org', 'unit', 'issn', 'eissn', 'category', 'international', 'shortname', 'name', 'url', )


class InputQueueSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = InputQueue
        fields = ('source', 'type', 'identifier', 'status', 'status_date', 'processed_date', 'url', )


class LanguageSerializer(serializers.HyperlinkedModelSerializer):
    # override NullBooleanFields
    is_hungarian = serializers.BooleanField()
    contains_hungarian = serializers.BooleanField()
    is_english = serializers.BooleanField()
    contains_english = serializers.BooleanField()
    all_non_hungarian = serializers.BooleanField()
    all_main_lang = serializers.BooleanField()

    class Meta:
        model = Language
        fields = ('name', 'is_hungarian', 'is_english', 'contains_hungarian', 'contains_english', 'all_non_hungarian', 'all_main_lang', 'warning', 'url', )
        read_only_fields = ('warning', )


class LocationSerializer(serializers.HyperlinkedModelSerializer):
    # override NullBooleanFields
    interior = serializers.BooleanField()
    exterior = serializers.BooleanField()

    class Meta:
        model = Location
        fields = ('country', 'city', 'interior', 'exterior', 'warning', 'url', )
        read_only_fields = ('warning', )


class TypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Type
        fields = ('type_mtmt', 'type_name', 'url', )


class TypesubtypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Typesubtype
        fields = ('type', 'subtype_mtmt', 'subtype_name', 'url', )


class PublicationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Publication
        fields = ('typesubtype', 'container_groupid', 'character', 'impactfactor', 'pubdate', 'language',
                  'peerreviewed', 'publisherlocation', 'publishinglocation', 'pagenum', 'wosdb', 'scopusdb',
                  'authorcount', 'editorcount', 'refcount', 'mtmt_pubid', 'url', )


class PubauthorsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Pubauthors
        fields = ('mtmt_pubauthorname', 'author_db', 'authortype', 'publication', 'share', 'position',
                  'isfirst', 'islast', 'url', )


class PubrefSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Pubref
        fields = ('publication', 'year', 'independent', 'independent_list', 'independent_wos', 'independent_wos_list',
                  'independent_scopus', 'independent_scopus_list', 'notindependent', 'notindependent_list', 'url', )
