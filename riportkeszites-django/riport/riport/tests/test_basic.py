from unittest import TestCase
from riport.models.external import (Publication, AuthorDb, AuthorDbIdentifier, Authortype, Character, Container, ExtAuthorlist,
                                    ExtJournalClassification, InputQueue, Language, Location, Type, Typesubtype, Pubauthors, Pubref)


class BasicModelTesting(TestCase):

    def test_db_schema(self):
        Publication.objects.all()
        AuthorDb.objects.all()
        AuthorDbIdentifier.objects.all()
        Authortype.objects.all()
        Character.objects.all()
        Container.objects.all()
        ExtAuthorlist.objects.all()
        ExtJournalClassification.objects.all()
        InputQueue.objects.all()
        Language.objects.all()
        Location.objects.all()
        Type.objects.all()
        Typesubtype.objects.all()
        Pubauthors.objects.all()
        Pubref.objects.all()

    def test_modifiable_models(self):
        Language.objects.create()
        Location.objects.create()

    def test_readonly_models(self):
        with self.assertRaises(NotImplementedError):
            AuthorDbIdentifier.objects.create()
        with self.assertRaises(NotImplementedError):
            ExtJournalClassification.objects.create()
