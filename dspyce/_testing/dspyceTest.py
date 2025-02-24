import unittest
import dspyce as ds
from dspyce.metadata import MetaDataValue
from dspyce.models import DSpaceObject, Community, Collection, Item
from dspyce.metadata.models import MetaData


class DSpaceObjectTest(unittest.TestCase):
    """
    Tests for dspyce.DSpaceObject objects.
    """
    obj: DSpaceObject = DSpaceObject('123445-123jljl1-234kjj', 'doc/12345', 'test-name')

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
        self.obj.add_metadata('dc.title', 'hello', 'en')
        self.assertEqual(self.obj.metadata['dc.title'][0].value,
                         'hello')
        self.assertEqual(self.obj.metadata['dc.title'][0].language, 'en')
        self.assertEqual(self.obj.get_first_metadata('dc.title').language, 'en')
        self.assertEqual(self.obj.get_first_metadata('dc.title').confidence, -1)
        self.assertTrue(self.obj.has_metadata('dc.title'))
        self.assertFalse(self.obj.has_metadata('dc.title.alternative'))
        self.assertIsNone(self.obj.get_first_metadata('dc.title').authority)
        self.obj.add_metadata('relation.isAuthorOfPublication.latestForDiscovery',
                              'kidll88-uuid999-duwkke1222', 'en')
        self.assertEqual(self.obj.get_metadata_values('relation.isAuthorOfPublication.latestForDiscovery')[0],
                         'kidll88-uuid999-duwkke1222')
        self.assertEqual(self.obj.get_first_metadata_value('dc.title'), 'hello')
        self.assertIsNone(self.obj.get_first_metadata('dc.title.alternative'))
        self.obj.add_metadata('dc.creator', MetaDataValue('Smith, Adam', 'en',
                                                          'orcid:123456', 2))
        self.assertEqual(self.obj.get_first_metadata_value('dc.creator'), 'Smith, Adam')
        self.assertDictEqual(
            {'value': 'Smith, Adam', 'language': 'en', 'authority': 'orcid:123456', 'confidence': 2},
            dict(self.obj.get_first_metadata('dc.creator'))
        )
        self.obj.metadata = MetaData({})

    def test_remove_metadata(self):
        self.obj.add_metadata('dc.title', 'hello', 'en')
        self.assertEqual(['hello'], self.obj.get_metadata_values('dc.title'))
        self.obj.remove_metadata('dc.title')
        self.assertIsNone(self.obj.get_metadata_values('dc.title'))
        self.obj.add_metadata('dc.title', 'hello', 'en')
        self.obj.add_metadata('dc.title', 'hallo', 'de')
        self.assertEqual(['hello', 'hallo'], self.obj.get_metadata_values('dc.title'))
        self.obj.remove_metadata('dc.title', 'hallo')
        self.assertEqual(['hello'], self.obj.get_metadata_values('dc.title'))
        self.obj.remove_metadata('dc.title')

    def test_replace_metadata(self):
        self.obj.add_metadata('dc.title', 'hello', 'en')
        self.assertEqual(['hello'], self.obj.get_metadata_values('dc.title'))
        self.obj.replace_metadata('dc.title', 'salut')
        self.assertEqual(['salut'], self.obj.get_metadata_values('dc.title'))
        self.obj.remove_metadata('dc.title')

    def test_move_metadata(self):
        self.obj.add_metadata('dc.title', 'hello', 'en')
        self.obj.add_metadata('dc.title', 'salut', 'fr')
        self.obj.add_metadata('dc.title', 'Hallo', 'de')
        self.assertListEqual(['hello', 'salut', 'Hallo'], self.obj.get_metadata_values('dc.title'))
        self.assertEqual('hello', self.obj.get_first_metadata_value('dc.title'))
        self.obj.move_metadata('dc.title', 2, 0)
        self.assertEqual('Hallo', self.obj.get_first_metadata_value('dc.title'))
        self.obj.move_metadata('dc.title', 0, 1)
        self.assertEqual('hello', self.obj.get_first_metadata_value('dc.title'))
        self.obj.move_metadata('dc.title', 2, 0)
        self.assertEqual('salut', self.obj.get_first_metadata_value('dc.title'))
        self.assertRaises(KeyError, self.obj.move_metadata, 'dc.title.alternative', 2, 0)
        self.assertRaises(KeyError, self.obj.move_metadata, 'dc.title', 4, 0)
        self.assertRaises(IndexError, self.obj.move_metadata, 'dc.title', 0, 4)
        self.obj.remove_metadata('dc.title')

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
        self.assertIsNone(Collection().get_identifier())

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
        self.assertEqual({'uuid': '123445-123jljl1-234kjj', 'handle': 'doc/12345', 'name': 'test-name',
                          'metadata': {}}, self.obj.to_dict())
        obj = Community('123445-123jljl1-234kjj', '123456789/1', 'community')
        obj.add_metadata('dc.title', 'hello', 'en')
        self.assertEqual({'uuid': '123445-123jljl1-234kjj', 'handle': '123456789/1', 'name': 'community',
                          'metadata': {'dc.title': [{'value': 'hello', 'language': 'en'}]},
                          'type': 'community'}, obj.to_dict())


    def test_from_dict(self):
        """
        Tests from_dict function from dspyce.__init__()
        """
        dict_obj = {'uuid': '123445-123jljl1-234kjj', 'handle': 'doc/12345', 'name': 'test-name',
                    'dc.title': [{'value': 'test-title', 'language': 'en'}, {'value': 'Test-Titel', 'language': 'de'}]}
        obj = ds.from_dict(dict_obj)
        self.assertEqual('123445-123jljl1-234kjj', obj.uuid)
        self.assertEqual('doc/12345', obj.handle)
        self.assertEqual('test-name', obj.name)
        self.assertTrue(obj.get_metadata_values('dc.title'), ['test-title', 'Test-Titel'])
        self.assertEqual('en', obj.metadata['dc.title'][0].language)
        self.assertEqual('de', obj.metadata['dc.title'][1].language)
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

    def test_rest(self):
        self.assertWarns(DeprecationWarning, ds.rest.object_to_json, self.obj)
        self.assertDictEqual(ds.rest.object_to_json(self.obj), {'handle': 'doc/12345', 'name': 'test-name',
                                                                'uuid': '123445-123jljl1-234kjj', 'metadata': {}})

if __name__ == '__main__':
    unittest.main()
