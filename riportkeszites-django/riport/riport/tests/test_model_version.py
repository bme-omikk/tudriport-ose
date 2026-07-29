from unittest import TestCase
from riport.models.external import Container


class ModelVersioningTest(TestCase):
    def test_Container(self):
        container = Container.objects.create(
            ISSNs=['123123123'],
            peerreviewed="no",
            groupid=123
        )
        # created instance is valid
        self.assertTrue(container.is_valid())

        original_pk = container.pk
        container.ISSNs = ['567567567']
        container.save()

        original_object = Container.objects.get(id=original_pk)
        # we have two different pk
        self.assertNotEqual(original_object.pk, container)
        # new object has changed data
        self.assertEqual(container.ISSNs, ['567567567'])
        # old object has original data
        self.assertEqual(original_object.ISSNs, ['123123123'])
        self.assertEqual(original_object.peerreviewed, "no")
        # other attributes didn't change
        self.assertEqual(container.groupid, original_object.groupid)
        # new object is valid, old one is not
        self.assertTrue(container.is_valid())
        self.assertFalse(original_object.is_valid())
