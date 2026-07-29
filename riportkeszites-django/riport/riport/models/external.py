from django.contrib.postgres.fields import ArrayField
from django.core import validators
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.db import models
from django.db.models import Q
from django.utils import timezone

import math

from tudriport.common.config import getconfig
from utils.misc import get_app_user

MISSING_DIMENSION_ID = getconfig('sqlimport.MISSING_DIMENSION_ID')

ENUM3 = (
    ('yes', 'yes'),
    ('no', 'no'),
    ('not given', 'not given'),
)

SJR_DQ = (
    ('D1', 'D1'),
    ('Q1', 'Q1'),
    ('Q2', 'Q2'),
    ('Q3', 'Q3'),
    ('Q4', 'Q4'),
)

MTA_RANK_ABCD = (
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'C'),
    ('D', 'D'),
)

# Input queue státuszok
INPUT_QUEUE_STATUS_NEW = 'new'
INPUT_QUEUE_STATUS_PROCESSING = 'processing'
INPUT_QUEUE_STATUS_PROCESSED = 'processed'
INPUT_QUEUE_STATUS_FAILED = 'failed'
INPUT_QUEUE_STATUS_DELETED = 'deleted'

# Input queue rekordtípusok
INPUT_QUEUE_TYPE_PUBLICATION = 'publication'
INPUT_QUEUE_TYPE_AUTHOR = 'author'

# INput queue prioritasok
INPUT_QUEUE_PRIORITY_DEFAULT = 5
INPUT_QUEUE_PRIORITY_WEB_REQUEST_MULTIPLE = 4
INPUT_QUEUE_PRIORITY_WEB_REQUEST_SINGLE = 3

input_queue_status_enum = (
    (INPUT_QUEUE_STATUS_NEW, INPUT_QUEUE_STATUS_NEW),
    (INPUT_QUEUE_STATUS_PROCESSING, INPUT_QUEUE_STATUS_PROCESSING),
    (INPUT_QUEUE_STATUS_PROCESSED, INPUT_QUEUE_STATUS_PROCESSED),
    (INPUT_QUEUE_STATUS_FAILED, INPUT_QUEUE_STATUS_FAILED),
    (INPUT_QUEUE_STATUS_DELETED, INPUT_QUEUE_STATUS_DELETED),
)

input_queue_type_enum = (
    (INPUT_QUEUE_TYPE_PUBLICATION, INPUT_QUEUE_TYPE_PUBLICATION),
    (INPUT_QUEUE_TYPE_AUTHOR, INPUT_QUEUE_TYPE_AUTHOR),
)

METRIC_IMPACTFACTOR = 'IF'
journal_metric_enum = (
    (METRIC_IMPACTFACTOR, METRIC_IMPACTFACTOR),
)

class VersionedModel(models.Model):
    # these fields are automatically managed, should not be set manually
    valid_from = models.DateTimeField(blank=True)
    valid_to = models.DateTimeField(blank=True, null=True)

    def is_valid(self, date=None):
        if date is None:
            date = timezone.now()

        return self.valid_from <= date and (self.valid_to is None or date < self.valid_to)

    @classmethod
    def get_valid_objects(cls, querytime=None):
        """return: queryset for objects currently valid according to valid_from and valid_to fields"""
        # run-time default value for querytime, as now() is time-dependent
        if querytime is None:
            querytime = timezone.now()

        return cls.objects.filter(valid_from__lte=querytime).filter(Q(valid_to__gt=querytime) | Q(valid_to=None))

    def __get_manager(self):
        """object Manager is not accessible from model instance, so we need to find out the model class"""
        class_name = type(self).__name__
        return globals()[class_name].objects

    def save(self, versioning=True, force_insert=False, force_update=False, using=None, update_fields=None, effective_datetime=None):
        if effective_datetime is None:
            now = timezone.now()
        else:
            now = effective_datetime

        if self.valid_from is None:
            self.valid_from = now

        if not versioning or self.pk is None:
            return super().save(force_insert, force_update, using, update_fields)

        old = self.__get_manager().get(pk=self.pk)
        if old.valid_to is not None:
            raise MutatingClosedVersionError
        old.valid_to = now
        old.save(versioning=False)

        self.valid_from = old.valid_to
        self.valid_to = None
        self.pk = None

        return super().save()

    def delete(self, effective_datetime=None):
        if effective_datetime is None:
            now = timezone.now()
        else:
            now = effective_datetime

        self.valid_to = now
        return super().save()


    class Meta:
        abstract = True


class TrackedModel(models.Model):
    """
    An abstract base class that provides created and updated fields.
    These fields are managed by Django, do not modify manually.
    """
    created_date = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    created_user = models.CharField(max_length=50, blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True, auto_now=True)
    updated_user = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self._state.adding:
            self.created_user=get_app_user()

        self.updated_user=get_app_user()

        return super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def update_if_differs(self, new_values, save=False):
        changed_field_exists = False
        for field, value in new_values.items():
            if isinstance(self.__getattribute__(field), float):
                # field holds a float number. New value differs if it is None or not close enough
                # Note: if old value is None, it if of type NoneType, so "else" will handle that
                if value is None or not math.isclose(self.__getattribute__(field), new_values[field], rel_tol=1e-9):
                    changed_field_exists = True        
                    self.__setattr__(field, value)  
            else:    
                if self.__getattribute__(field) != new_values[field]: 
                    changed_field_exists = True        
                    self.__setattr__(field, value)                
        if changed_field_exists and save:
            self.save()
        return changed_field_exists

    def differs(self, new_values):
        changed_field_exists = False
        for field, value in new_values.items():
            if isinstance(self.__getattribute__(field), float):
                # field holds a float number. New value differs if it is None or not close enough
                # Note: if old value is None, it if of type NoneType, so "else" will handle that
                if value is None or not math.isclose(self.__getattribute__(field), new_values[field], rel_tol=1e-9):
                    changed_field_exists = True        
            else:    
                if self.__getattribute__(field) != new_values[field]: 
                    changed_field_exists = True        
        return changed_field_exists


class OptionalModel(models.Model):
    """
    An abstract base class that provides the MISSING model instance for optional models.
    """

    class Meta:
        abstract = True

    @classmethod
    def get_missing_instance(cls):
        return cls.objects.get(id=MISSING_DIMENSION_ID)


class ReadonlyModel(models.Model):
    """
    Readonly models. Modifications happen from other sources.
    """

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        raise NotImplementedError("This model is readonly for django.")

    def delete(self, using=None, keep_parents=False):
        raise NotImplementedError("This model is readonly for django.")

    class Meta:
        abstract = True


class WarningModel(models.Model):
    """
    Sets 'warning' field True if one or more fields listed in 'warning_fields' is None
    """
    # FIXME: NOT NULL legyen, amikor majd az sqlimport is Django modellen dolgozik.
    warning = models.BooleanField(default=True, null=True)
    # list of watched fields
    warning_fields = ()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        try:
            self.warning = None in [getattr(self, f) for f in self.warning_fields]
        except AttributeError as e:
            raise ImproperlyConfigured(e)

        super().save(force_insert, force_update, using, update_fields)

    class Meta:
        abstract = True


class AuthorDb(TrackedModel):
    id = models.AutoField(primary_key=True)
    mtmt_authid = models.IntegerField(blank=True, null=True)
    authorname = models.CharField(max_length=100)
    authorcomment = models.CharField(max_length=200, null=True)

    class Meta:
        db_table = 'author_db'
        indexes = [
            models.Index(fields=['mtmt_authid'], name='author_db_mtmt_authid_key'),
        ]



class AuthorDbIdentifier(ReadonlyModel, VersionedModel, TrackedModel):
    id = models.AutoField(primary_key=True)
    identifier = models.CharField(max_length=50)
    # TODO on_delete
    author_db = models.ForeignKey(AuthorDb, models.DO_NOTHING, related_name='+')

    class Meta:
        db_table = 'author_db_identifier'


class Authortype(TrackedModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)

    class Meta:
        db_table = 'authortype'


class Character(TrackedModel, OptionalModel):
    id = models.AutoField(primary_key=True)
    chid_mtmt = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'character'


# Note: container_groupid_seq has been created in a RunSQL migration step
class Container(VersionedModel, TrackedModel, OptionalModel):
    id = models.AutoField(primary_key=True)
    groupid = models.IntegerField()
    ISSNs = ArrayField(base_field=models.CharField(max_length=9), default=list, db_column="issns")
    peerreviewed = models.CharField(max_length=9, choices=ENUM3)

    def save(self, versioning=True, force_insert=False, force_update=False, using=None, update_fields=None, effective_datetime=None):
        if self.groupid is None:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT nextval('container_groupid_seq')""")
                self.groupid = cursor.fetchone()[0]

        return super().save(versioning=versioning, force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields, effective_datetime=effective_datetime)

    class Meta:
        db_table = 'container'
        indexes = [
            models.Index(fields=['groupid'], name='container_groupid_key'),
        ]


class ExtAuthorlist(VersionedModel, TrackedModel):
    id = models.AutoField(primary_key=True)
    world = models.CharField(max_length=20)
    org = models.CharField(max_length=100)
    unit = models.CharField(max_length=100)
    subunit = models.CharField(max_length=100)
    subsub_unit = models.CharField(max_length=100)
    personname = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    mtmtcode = models.IntegerField()
    neptuncode = models.CharField(max_length=7)
    supervisor_mtmt_authid = models.IntegerField(default=None, null=True)
    # key/value dictionary to store extrainfo about authors
    extrainfo = models.JSONField(default=dict)
    weighting = models.FloatField()
    # Each record count always for the given (org, unit, subunit, subsub_unit).
    # If for_rollup
    for_rollup = models.BooleanField(help_text='When set to True, the record count also for parents in the organization hierarchy. When set to False, only count for the given (org, unit, subunit, subsub_unit) combination.', default=True)

    class Meta:
        db_table = 'ext_authorlist'


class ExtJournalClassification(ReadonlyModel, VersionedModel, TrackedModel):
    id = models.AutoField(primary_key=True)
    org = models.CharField(max_length=100)
    unit = models.CharField(max_length=100)
    issn = models.CharField(max_length=9)
    eissn = models.CharField(max_length=9)
    category = models.CharField(max_length=30)
    international = models.CharField(max_length=9, choices=ENUM3)
    shortname = models.CharField(max_length=20)
    name = models.CharField(max_length=250)

    class Meta:
        db_table = 'ext_journal_classification'


class ExtJournalMetrics(VersionedModel, TrackedModel):
    id = models.AutoField(primary_key=True)
    ISSNs = ArrayField(base_field=models.CharField(max_length=9), default=list, db_column="issns")
    year = models.IntegerField()
    isestimate = models.BooleanField(blank=True, null=True)
    metric_name = models.CharField(max_length=30, choices=journal_metric_enum)
    metric_value = models.FloatField()
    journal_title = models.CharField(max_length=250, blank=True, null=True)

    class Meta:
        db_table = 'ext_journal_metrics'

#TODO: az InputQueue save (update) során:
# IF TG_TABLE_NAME = 'input_queue' AND TG_OP = 'UPDATE' THEN
#     IF OLD.status IS DISTINCT FROM NEW.status THEN
#         NEW.status_date := l_current_date;
#
#         IF NEW.status = 'processed' THEN
#             NEW.processed_date := l_current_date;
#         END IF;
#     END IF;
# END IF;
class InputQueue(TrackedModel):
    id = models.AutoField(primary_key=True)
    source = models.CharField(max_length=50)
    type = models.CharField(max_length=11, choices=input_queue_type_enum)
    # processing priority: 0: highest, 10: lowest
    priority = models.SmallIntegerField(default=INPUT_QUEUE_PRIORITY_DEFAULT, validators=[validators.MaxValueValidator(10), validators.MinValueValidator(0)])
    identifier = models.IntegerField()
    status = models.CharField(blank=True, max_length=10, choices=input_queue_status_enum)
    status_date = models.DateTimeField(blank=True)
    status_msg = models.CharField(blank=True, null=True, max_length=500)
    processed_date = models.DateTimeField(blank=True, null=True)
    # information fields
    command_source = ArrayField(base_field=models.CharField(max_length=100), default=list)
    # tracks if a command has been received multiple times
    command_count = models.IntegerField(default=1)

    class Meta:
        db_table = 'input_queue'
        indexes = [
            models.Index(
                name='input_queue_processing_idx',
                fields=['status', 'priority', 'type', 'status_date', 'source'],
                # for Django 3.2 or later
                #include=['identifier', 'status_date']
            ),
        ]
        permissions = (
            ('update_publication', 'Can schedule publication update from datasource'),
            ('update_author', 'Can schedule author update from datasource'),
            # ('view_inputqueue', 'Can view inputqueue'),
        )
        ordering = ('created_date', )


class Language(WarningModel, TrackedModel, OptionalModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    is_hungarian = models.BooleanField(help_text='Denote the single langugage Hungarian.', null=True)
    contains_hungarian = models.BooleanField(help_text='Among the langugages, Hungarian appears.', null=True)
    is_english = models.BooleanField(help_text='Denote the single language English.', null=True)
    contains_english = models.BooleanField(help_text='Among the langugages, English appears.', null=True)
    all_non_hungarian = models.BooleanField(help_text='All the langugages in the set are non-Hungarian.', null=True)
    all_main_lang = models.BooleanField(help_text='All the langugages in the set are one of the main langugages English, French, German, Russian. I.e. this langugage set is a subset of (English, French, German, Russian)', null=True)

    warning_fields = ('is_hungarian', 'contains_hungarian', 'is_english', 'contains_english', 'all_non_hungarian', 'all_main_lang')

    class Meta:
        db_table = 'language'
        # permissions = (
        #     ('view_language', 'Can view language'),
        # )


class Location(WarningModel, TrackedModel, OptionalModel):
    id = models.AutoField(primary_key=True)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True, null=True)
    interior = models.BooleanField(null=True)
    exterior = models.BooleanField(null=True)

    warning_fields = ('interior', 'exterior', )

    class Meta:
        db_table = 'location'
        # permissions = (
        #     ('view_location', 'Can view location'),
        # )


class Type(TrackedModel, OptionalModel):
    id = models.AutoField(primary_key=True)
    type_mtmt = models.IntegerField(blank=True, null=True, unique=True)
    type_name = models.CharField(max_length=30)

    class Meta:
        db_table = 'type'


class Typesubtype(TrackedModel, OptionalModel):
    id = models.AutoField(primary_key=True)
    subtype_mtmt = models.IntegerField(blank=True, null=True)
    subtype_name = models.CharField(max_length=100)
    type = models.ForeignKey(Type, models.DO_NOTHING, related_name='+')

    class Meta:
        db_table = 'typesubtype'
        constraints = [
            models.UniqueConstraint(fields=['subtype_mtmt', 'type'], name='typesubtype__type_subtype__uq'),
        ]

class PublicationDescription(TrackedModel):
    #FIXME: force this model to be append-only
    """
    Additional descriptive info on publications. This is treated as an append only model.
    
    Put metadata here that possibly involve large amount of data, but not needed for counting points.
    """
    id = models.AutoField(primary_key=True)
    # store MTMT pubid only for lookup performance reasons.
    mtmt_pubid = models.IntegerField()
    label_txt = models.TextField()
    label_html = models.TextField()
    # a list of dictionaries, to show duplicated DOId among the citations.
    # Each dictionary has the following keys:
    #  - doi: the DOI itself
    #  - citingDocYear: the publishing year of the citing document (i.e. related document)
    #  - citingDocList: the list of MTIDs of the citing publications (i.e. related document)
    #  - citationList: the list of MTIDs of the citation objects (i.e. the relation between a source publication and a citing publication)
    #  Note: the two lists above are ordered as matching indices form a pair of citation object and citing publication.
    citation_duplicate_doi_info = models.JSONField(default=list)
    # a list of dictionaries, to show duplicated titles among the citations.
    # Each dictionary has the following keys:
    #  - title: the citing publication title
    #  - citingDocList: the list of MTIDs of the citing publications (i.e. related document)
    #  - citationList: the list of MTIDs of the citation objects (i.e. the relation between a source publication and a citing publication)
    #  Note: the two lists above are ordered as matching indices form a pair of citation object and citing publication.
    citation_duplicate_title_info = models.JSONField(default=list)
    # a list of citation IDs  that are not published
    citation_list_not_published = ArrayField(base_field=models.IntegerField(), default=list)
    # a list of citation IDs that are published, but citing document is unpublished
    citation_list_citingdoc_not_published = ArrayField(base_field=models.IntegerField(), default=list, db_column="citation_list_cdoc_not_public")
    # a list of citation IDs where the citing doc has error(s)
    citation_list_citingdoc_w_error = ArrayField(base_field=models.IntegerField(), default=list, db_column="citation_list_cdoc_w_error")
    # a list of citation IDs citations w/ unknown "external flag"
    citation_list_unknown_external = ArrayField(base_field=models.IntegerField(), default=list)

    class Meta:
        db_table = 'publication_description'
        indexes = [
            models.Index(fields=['mtmt_pubid'], name='pub_description_mtmt_pubid_idx'),
        ]

class AbstractPublication(models.Model):
    type = models.ForeignKey(Type, models.DO_NOTHING, related_name='+')
    typesubtype = models.ForeignKey(Typesubtype, models.DO_NOTHING, related_name='+')
    container_groupid = models.IntegerField()  # todo: join based on this
    character = models.ForeignKey(Character, models.DO_NOTHING, related_name='+')
    # is full scientific publication?
    # Data source reports this as True/False for all publications, thus
    # should be "NOT NULL" and reports can regard this as such.
    # In the model, it is not defined as "NOT NULL" because records loaded before implementing this field lack this field.
    is_full_scientific = models.BooleanField(blank=True, null=True)
    # False, if publication pending ("Megjelenés előtt") as reported by data source
    is_published = models.BooleanField(blank=True, null=True)
    publication_description = models.ForeignKey(PublicationDescription, models.DO_NOTHING, related_name='+', null=True)
    impactfactor_value = models.FloatField(blank=True, null=True)
    impactfactor_isestimate = models.BooleanField(blank=True, null=True)
    citescore_value = models.FloatField(blank=True, null=True)
    citescore_isestimate = models.BooleanField(blank=True, null=True)
    sjr_value = models.FloatField(blank=True, null=True)
    sjr_rank = models.CharField(max_length=2, choices=SJR_DQ, null=True)
    sjr_isestimate = models.BooleanField(blank=True, null=True)
    snip_value = models.FloatField(blank=True, null=True)
    snip_isestimate = models.BooleanField(blank=True, null=True)
    # MTA rating
    # ..._rank      holds values A,B,C,D
    # ..._rank_full holds full string value from datasource, like "B hazai", "C nemzetközi"
    # Fields named like mta_XXX_rank and mta_XXX_rank_full stand for the specific committee's list.
    # while mta_rank and mta_rank_full holds the best rank, i.e. the first in alphabetical order.
    mta_rank = models.CharField(max_length=1, choices=MTA_RANK_ABCD, null=True)
    mta_rank_full = models.CharField(max_length=20, null=True)
    mta_gmb_rank = models.CharField(max_length=1, choices=MTA_RANK_ABCD, null=True)
    mta_gmb_rank_full = models.CharField(max_length=20, null=True)
    # if the publication's journal is listed on the MTA list as zero ("kifogasolhato") for the year of the publication
    mta_listed_zero =  models.BooleanField(default=False)
    # year
    pubdate = models.IntegerField()
    language = models.ForeignKey(Language, models.DO_NOTHING, related_name='+')
    # shows if foreign language publication as reported by the data source
    is_foreign_language = models.BooleanField(blank=True, null=True)
    peerreviewed = models.BooleanField(blank=True)
    publisherlocation = models.ForeignKey(Location, models.DO_NOTHING, related_name='+')
    publishinglocation = models.ForeignKey(Location, models.DO_NOTHING, related_name='+')
    # shows if it is a foreign publication (edition) as reported by the data source
    is_foreign_publication = models.BooleanField(blank=True, null=True)
    pagenum = models.IntegerField(blank=True, null=True)
    wosdb = models.BooleanField(blank=True)
    scopusdb = models.BooleanField(blank=True)
    authorcount = models.IntegerField()
    editorcount = models.IntegerField()
    refcount = models.IntegerField()
    mtmt_pubid = models.IntegerField()
    # if a DOI appears more than once among the citations
    has_citation_duplicate_doi = models.BooleanField(null=True)
    # if a publication title appears more than once among the citations
    has_citation_duplicate_title = models.BooleanField(null=True)
    # if there are not published citations
    has_citation_not_published = models.BooleanField(null=True)
    # if there are published citations with unpublished citing document
    has_citation_citingdoc_not_published = models.BooleanField(null=True)
    # if there are published citations where citing document has error(s)
    has_citation_citingdoc_w_error = models.BooleanField(null=True)
    # if there are citations w/ unknown "external flag"
    has_citation_unknown_external = models.BooleanField(null=True)
    # if the publication has DOI
    has_doi = models.BooleanField(null=True)
    # if the publication or its book container has ISBN
    has_isbn = models.BooleanField(default=False)
    # if the publication's journal container or the conference series has ISSN
    has_issn = models.BooleanField(default=False)
    # if the publication has a full document URL (aka. "Teljes dokumentum")
    has_full_document_url = models.BooleanField(null=True)
    # if the publication has an OpenAccess version linked
    has_oa_link = models.BooleanField(null=True)
    # a dictionary holding descriptive fields special to the GPK PhD scoring system (or None if not available)
    # The dictionary has the following keys:
    #  - raw: the raw data we were parsing. This is an "Egyéb URL" in MTMT of the form https://phd.gpk.bme.hu/pub/s12345678/j1183/l4/t1
    #  - auto_generated: True/False, indicating if "raw" was empty in the source, thus data here was auto generated based on publication metadata
    #  - warning: list of textual descriptions of the warnings if any, or empty list ([]) if no warnings found.
    #  - level: the level of th epublicationm integer, from 1 to 8
    #  - thesis_related: dictionary, describing if the publication is related to PhD theses. Valid values: 1, 2, 3 (as integers)
    #          "is_simple" key distinguishes between simple and compound entry.
    #          { "is_simple": True, "value": 1 } states that the value field applies to all authors, i.e. thesis_related is regarded as 1.
    #          { "is_simple": False, "entries": [ { "value": 1, "authors": [50505050, 60606060] } ... ] } states that for the given authors, the thesis_related field has value as given.
    #              When scoring a given author A, its ID is searched for in the "authors" lists. The first matching dictionary gives the value in case of duplicate entries.
    #
    #  - pubtype: the type of publication. j/c/p/b/bc standing for journal article/conference article/poster/book/book chapter
    #  - pubtype_container_id: the ID of the MTMT container record.
    #    - for pubtype j, this is a journal ID
    #    - for pubtype c, p, this is a conference ID
    #    - for pubtype b, this is not relevant
    #    - for pubtype bc, this is a book ID
    #  - journal_info: dictionary, in casse pubtype is j, holds data about the effective journal.
    #    - mtmt_journalid: int, the ID of the effective journal
    #    - warning: string[], the warnings from journal info processing. They are merged into the parent' warning list.and deleted from here.
    #    - wosdb: bool, if the journal is in WoS
    #    - scopusdb: bool, if the journal is in Scopus
    #    - has_impact_factor: bool, if the journal has impact factor. Note: this should reflect if the journal had impact factor in the publication year, but this is not implemented yet.
    #    - is_foreign_publication: bool, if the journal is published abroad
    #    - mta_listed_zero: bool, is the journal is listed on the MTA list of "bad" journals in the publication year.
    #    - peer_reviewed: bool, if the journal is peer reviewed
    #  - supervisor: dictionary, describing supervisor-students relationships.
    #          "is_simple" key distinguishes between simple and compound entry.
    #          { "is_simple": True, "supervisor": 12345678 } states that the supervisor field applies to all authors, i.e. supervisor's id is 12345678.
    #          { "is_simple": False, "entries": [ { "supervisor": 12345678, "authors": [50505050, 60606060] } ... ] } states that author and supervisor relationships are given in the dictionary.
    #              When scoring a given author A, its ID is searched for in the "authors" lists. The first matching dictionary gives the value in case of duplicate entries.
    bme_gpk_phd_description = models.JSONField(null=True, default=None)

    class Meta:
        abstract = True

class Publication(AbstractPublication, VersionedModel, TrackedModel):
    id = models.AutoField(primary_key=True)

    class Meta:
        db_table = 'publications'
        indexes = [
            models.Index(fields=['mtmt_pubid'], name='publications_mtmt_pubid_idx'),
        ]

class AbstractPubauthors(models.Model):
    mtmt_pubauthorname = models.CharField(max_length=250)
    # todo check on_delete
    author_db = models.ForeignKey(AuthorDb, models.DO_NOTHING, related_name='+')
    # todo check on_delete
    authortype = models.ForeignKey(Authortype, models.DO_NOTHING, related_name='+')
    # todo check on_delete
    publication = models.ForeignKey(Publication, models.DO_NOTHING)
    share = models.FloatField(blank=True, null=True)
    position = models.IntegerField()
    isfirst = models.BooleanField(blank=True)
    islast = models.BooleanField(blank=True)
    has_author_affiliation_BME_EMK = models.BooleanField(blank=True, null=True, db_column='has_author_affiliation_bme_emk')
    has_author_affiliation_BME_EPK = models.BooleanField(blank=True, null=True, db_column='has_author_affiliation_bme_epk')
    has_author_affiliation_BME_GPK = models.BooleanField(blank=True, null=True, db_column='has_author_affiliation_bme_gpk')
    has_author_affiliation_BME_GTK = models.BooleanField(blank=True, null=True, db_column='has_author_affiliation_bme_gtk')
    has_author_affiliation_BME_KJK = models.BooleanField(blank=True, null=True, db_column='has_author_affiliation_bme_kjk')
    has_author_affiliation_BME_TTK = models.BooleanField(blank=True, null=True, db_column='has_author_affiliation_bme_ttk')
    has_author_affiliation_BME_VBK = models.BooleanField(blank=True, null=True, db_column='has_author_affiliation_bme_vbk')
    has_author_affiliation_BME_VIK = models.BooleanField(blank=True, null=True, db_column='has_author_affiliation_bme_vik')
    has_author_affiliation_BME = models.BooleanField(blank=True, null=True, db_column='has_author_affiliation_bme')
    class Meta:
        abstract = True


class Pubauthors(AbstractPubauthors, TrackedModel):
    id = models.AutoField(primary_key=True)

    class Meta:
        db_table = 'pubauthors'


class Published(AbstractPublication, AbstractPubauthors, VersionedModel, TrackedModel):
    '''Published fact table: authors' participation in a publication.'''
    id = models.AutoField(primary_key=True)

    class Meta:
        db_table = 'published'
        indexes = [
            models.Index(fields=['mtmt_pubid'], name='published_mtmt_pubid_idx'),
        ]


class Pubref(TrackedModel):
    id = models.AutoField(primary_key=True)
    publication = models.ForeignKey(Publication, models.DO_NOTHING)
    year = models.IntegerField()
    independent = models.IntegerField()
    independent_list = models.TextField()
    independent_wos = models.IntegerField()
    independent_wos_list = models.TextField()
    independent_scopus = models.IntegerField()
    independent_scopus_list = models.TextField()
    notindependent = models.IntegerField()
    notindependent_list = models.TextField()

    class Meta:
        db_table = 'pubref'

class MutatingClosedVersionError(Exception):
    """A closed instance of a VersionedModel is prohibited to mutate"""
    pass
