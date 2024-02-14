import unittest
import dspyce.metadata as md


class MetadataTest(unittest.TestCase):
    """
    Tests for metadata package.
    """
    mdObject = md.MetaData('dc', 'contributor', 'author', 'Smith, Adam', 'en')

    def test_equal(self):
        """
        Test __eq__ method from MetaData class.
        """
        self.assertTrue(self.mdObject == md.MetaData('dc', 'contributor', 'author',
                                                     'Smith, Adam', 'en'))
        self.assertTrue(self.mdObject != md.MetaData('dc', 'contributor', 'author',
                                                     'Smith, Adam'))
        self.assertFalse(self.mdObject == md.MetaData('dc', 'contributor', 'editor',
                                                      'Smith, Adam', 'en'))
        self.assertRaises(TypeError, self.mdObject.__eq__, 'abc')

    def test_compare(self):
        """
        Tests __gt__, __ge__, __lt__ and __le__ methods from MetaData class.
        """
        other = md.MetaData('relation', 'isAuthorOf', 'latestForDiscovery',
                            'xyz', 'de')
        self.assertGreater(other, self.mdObject)
        self.assertLess(self.mdObject, other)
        self.assertRaises(TypeError, self.mdObject.__gt__, 'abc')
        self.assertRaises(TypeError, self.mdObject.__ge__, 'abc')
        self.assertRaises(TypeError, self.mdObject.__lt__, 'abc')
        self.assertRaises(TypeError, self.mdObject.__le__, 'abc')

    def test_to_string(self):
        """
        Tests __str__ method from MetaData class.
        """
        self.assertEqual(str(self.mdObject), 'dc.contributor.author:Smith, Adam[en]')
        self.assertEqual('dc.creator:test', str(md.MetaData('dc', 'creator', None,
                                                            'test')))

    def test_is_field(self):
        """
        Tests is_field method from MetaData class.
        """
        self.assertTrue(self.mdObject.is_field('dc.contributor.author'))
        self.assertFalse(self.mdObject.is_field('dc.creator'))
        self.assertRaises(TypeError, self.mdObject.is_field, 'abc')
        self.assertRaises(TypeError, self.mdObject.is_field, 'abc.abc.abc.abc')

    def test_add_value(self):
        """
        Tests add_value method from MetaData class.
        """
        obj = md.MetaData('dc', 'contributor', 'author', None, 'en')
        obj.add_value('Smith, Adam')
        self.assertEqual('Smith, Adam', obj.value)
        obj.add_value('Test')
        self.assertEqual(['Smith, Adam', 'Test'], obj.value)

    def test_get_tag(self):
        """
        Tests get_tag method from MetaData class.
        """
        self.assertEqual('dc.contributor.author', self.mdObject.get_tag())
        obj = md.MetaData('dc', 'creator', None, None)
        self.assertEqual('dc.creator', obj.get_tag())

    def test_metadata_list(self):
        """
        Tests methods from MetadataList class.
        """
        lst = md.MetaDataList([self.mdObject])
        obj = md.MetaData('dc', 'creator', None, 'Test')
        self.assertRaises(TypeError, lst.__setitem__, 0, 'abc')
        self.assertRaises(TypeError, lst.insert, 0, 'abc')
        self.assertRaises(TypeError, lst.append, 'abc')
        self.assertRaises(TypeError, lst.extend, ['abc'])
        self.assertRaises(TypeError, lst.__add__, ['abc'])
        lst.append(obj)
        self.assertEqual(obj, lst[-1])
        lst.append(md.MetaData('dc', 'creator', None, 'Test2'))
        self.assertEqual(2, len(lst))
        self.assertEqual("dc.contributor.author:Smith, Adam[en], dc.creator:['Test', 'Test2']", str(lst))
        self.assertEqual({'dc'}, lst.get_schemas())
        self.assertEqual([self.mdObject], lst.get('dc.contributor.author'))
        self.assertIsNone(lst.get('dc.title'))


if __name__ == '__main__':
    unittest.main()
