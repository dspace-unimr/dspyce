import unittest
import dspyce.metadata as md


class MetadataTest(unittest.TestCase):
    """
    Tests for metadata package.
    """
    mdValue = md.MetaDataValue('Hello World', 'en')
    mdList = md.MetaData({'dc.title': [mdValue]})

    def test_equal(self):
        """
        Test __eq__ method from MetaData class.
        """
        self.assertTrue(self.mdValue == md.MetaDataValue('Hello World', 'en'))
        self.assertFalse(self.mdValue == md.MetaDataValue('Smith, Adam', 'en'))
        self.assertRaises(TypeError, self.mdValue.__eq__, 'abc')

    def test_to_string(self):
        """
        Tests __str__ method from MetaData class.
        """
        self.assertEqual('en:\tHello World', str(self.mdValue))
        self.assertEqual('dc.title:\n\ten:\tHello World', str(self.mdList))

    def test_add_value(self):
        """
        Tests add_value method from MetaData class.
        """
        self.mdValue.set_value('Smith, Adam')
        self.assertEqual('Smith, Adam', self.mdValue.value)
        self.mdValue.set_value('Hello World')
        self.mdList['dc.contributor.author'] = md.MetaDataValue('Smith, Adam')
        self.assertEqual('Smith, Adam', self.mdList['dc.contributor.author'][0].value)
        self.mdList.pop('dc.contributor.author')
        self.assertIsNone(self.mdList.get('dc.contributor.author'))
        self.assertRaises(TypeError, self.mdList.__setitem__, 'dc.title', 'xyz')
        self.assertRaises(KeyError, self.mdList.__setitem__, 'hello', md.MetaDataValue('test'))

    def test_to_dict(self):
        """
        Test the dict() implementation of the MetaDataValue class.
        """
        self.assertEqual({'value': 'Hello World', 'language': 'en'}, dict(self.mdValue))

    def test_pop_value(self):
        """
        Test the pop method from MetaData class.
        """
        obj = md.MetaData({'dc.title': [md.MetaDataValue('Hello World', 'en')]})
        self.assertEqual(md.MetaDataValue('Hello World', 'en'), obj['dc.title'][0])
        obj.pop('dc.title')
        self.assertIsNone(obj.get('dc.title'))


if __name__ == '__main__':
    unittest.main()
