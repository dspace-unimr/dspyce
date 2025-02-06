import unittest

import dspyce as ds
from dspyce.bitstreams import Bundle


class ItemTest(unittest.TestCase):
    """
    Test class for the item class.
    """

    item: ds.Item = ds.Item('xyz', '123456789/1', 'test', ds.Collection('abc'))

    def test_entity(self):
        """
        Tests all entity related methods.
        """
        self.item.enable_entity('Publication')
        self.assertTrue(self.item.is_entity())
        self.assertEqual('Publication', self.item.get_metadata_values('dspace.entity.type')[0])
        self.assertEqual('Publication', self.item.get_entity_type())
        self.item.add_relation('isAuthorOfPublication', 'xyz-uuid')
        self.assertRaises(TypeError, ds.Item('').add_relation, 'isContributionOfPublication', 'xyz-uuid')
        self.assertEqual(ds.Item(uuid='xyz-uuid'), self.item.get_related()[0])

    def test_object_type(self):
        """
        Tests object_type method.
        """
        self.assertEqual('Item', self.item.get_dspace_object_type())

    def test_bitstreams(self):
        """
        Tests bitstream related methods.
        """
        self.item.add_content('TEST-FILE', '/test/path/to/file.txt', 'description')
        self.item.add_content('TEST-FILE-2', '/test/path/to/file.txt', 'description',
                              bundle=Bundle('TEST'))
        self.assertEqual([Bundle('ORIGINAL'), Bundle('TEST')], self.item.get_bundles())

    def test_collections(self):
        """
        Tests collection related methods.
        """
        self.assertEqual(ds.Collection('abc'), self.item.get_owning_collection())
        self.item.add_collection(ds.Collection('dfg'))
        self.assertEqual(ds.Collection('dfg'), self.item.collections[-1])


if __name__ == '__main__':
    unittest.main()
