import unittest
import dspyce as ds
from dspyce.DSpaceObject import DSpaceObject
from dspyce.DSpaceObject import parse_metadata_label
from dspyce.Item import Item
from dspyce.Collection import Collection
from dspyce.Community import Community
from dspyce.metadata import MetaDataList


class DSpaceObjectTest(unittest.TestCase):
    """
    Tests for dspyce.DSpaceObject objects.
    """
    obj: DSpaceObject = DSpaceObject('123445-123jljl1-234kjj', 'doc/12345', 'test-name')

    def test_parse_metadata_label(self):
        """
        Tests function parse_metadata_label from DSpaceObject.py
        """
        self.assertEqual(parse_metadata_label('dc.identifier.uri'), ('dc', 'identifier', 'uri'))
        self.assertEqual(parse_metadata_label('dc.type'), ('dc', 'type', None))
        self.assertRaises(ValueError, parse_metadata_label, 'dc-title')
        self.assertRaises(ValueError, parse_metadata_label, 'dc.identifier.uri.url')
        self.assertRaises(AttributeError, parse_metadata_label, 134)

    def test_init_object(self):
        """
        Tests object initialization from DSpaceObject class.
        """
        self.assertEqual(self.obj, DSpaceObject('123445-123jljl1-234kjj'))
        self.assertEqual(self.obj.uuid, '123445-123jljl1-234kjj')
        self.assertEqual(self.obj.handle, 'doc/12345')
        self.assertEqual(self.obj.name, 'test-name')
        self.assertNotEqual(self.obj, DSpaceObject('dddds2-123jljl1-234kjj'))
        self.assertIsInstance(self.obj, DSpaceObject)

    def test_add_metadata(self):
        """
        Tests add_metadata method from DSpaceObject
        """
        self.obj.add_dc_value('title', None, 'hello', 'en')
        self.assertEqual(list(filter(lambda x: x.schema == 'dc' and x.element == 'title', self.obj.metadata))[0].value,
                         'hello')
        self.assertEqual(list(filter(lambda x: x.schema == 'dc' and x.element == 'title',
                                     self.obj.metadata))[0].language, 'en')
        self.obj.add_metadata('relation', 'isAuthorOfPublication', 'latestForDiscovery',
                              'kidll88-uuid999-duwkke1222', 'en')
        self.assertEqual(self.obj.get_metadata_values('relation.isAuthorOfPublication.latestForDiscovery')[0],
                         'kidll88-uuid999-duwkke1222')
        self.obj.metadata = MetaDataList([])

    def test_object_type(self):
        """
        Test object_type method from DSpaceObject, Item and Community classes.
        """
        self.assertIsNone(self.obj.get_dspace_object_type())
        self.assertEqual(Item().get_dspace_object_type(), 'Item')
        self.assertEqual(Collection().get_dspace_object_type(), 'Collection')
        self.assertEqual(Community().get_dspace_object_type(), 'Community')

    def test_get_identifier(self):
        """
        Tests get_identifier method from DSpaceObject
        """
        self.assertEqual(self.obj.get_identifier(), '123445-123jljl1-234kjj')
        self.assertEqual(Item(handle='doc/12').get_identifier(), 'doc/12')
        self.assertEqual(Collection().get_identifier(), '')

    def test_equality(self):
        """
        Tests __eq__ method from DSpaceObject
        """
        self.assertTrue(self.obj == DSpaceObject('123445-123jljl1-234kjj'))
        self.assertFalse(self.obj == DSpaceObject('12dsf3445-234kjj'))

    def test_to_dict(self):
        """
        Tests to_dict method from DSpaceObject.
        """
        self.assertEqual(self.obj.to_dict(), {'uuid': '123445-123jljl1-234kjj', 'handle': 'doc/12345',
                                              'name': 'test-name'})

    def test_from_dict(self):
        """
        Tests from_dict function from dspyce.__init__()
        """
        dict_obj = {'uuid': '123445-123jljl1-234kjj', 'handle': 'doc/12345', 'name': 'test-name',
                    'dc.title': [{'value': 'test-title', 'language': 'en'}, {'value': 'Test-Titel', 'language': 'de'}]}
        obj = ds.from_dict(dict_obj)
        self.assertEqual(obj.uuid, '123445-123jljl1-234kjj')
        self.assertEqual(obj.handle, 'doc/12345')
        self.assertEqual(obj.name, 'test-name')
        self.assertTrue(obj.get_metadata_values('dc.title'), ['test-title', 'Test-Titel'])
        self.assertEqual(obj.metadata[0].language, 'en')
        self.assertEqual(obj.metadata[1].language, 'de')
        self.assertRaises(TypeError, ds.from_dict, dict_obj, 'test')

    def test_statistics(self):
        """
        Test add_statistic_report and has_statistics methods from DSpaceObject
        """
        self.assertFalse(self.obj.has_statistics())
        self.obj.add_statistic_report({'TotalViews': 0})
        self.obj.add_statistic_report(None)
        self.obj.add_statistic_report({"TotalDownloads": {'uuid': 'lkjlkjl', "views": 12}})
        self.obj.add_statistic_report({"TotalDownloads": {'uuid': '12345', "views": 12}})
        self.obj.add_statistic_report({"TotalDownloads": {'uuid': 'sd3x33', "views": 15}})
        self.assertEqual(2, len(self.obj.statistic_reports))
        self.assertTrue(isinstance(self.obj.statistic_reports['TotalDownloads'], list))
        self.assertTrue(self.obj.has_statistics())


if __name__ == '__main__':
    unittest.main()
