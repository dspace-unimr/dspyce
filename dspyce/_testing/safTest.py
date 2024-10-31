import logging
import os
import unittest

from dspyce import saf
from dspyce import Item, Collection
from dspyce.metadata import MetaDataValue


class SAFTest(unittest.TestCase):
    """
    Test class for saf module.
    """

    def test_saf(self):
        """
        Test method for saf package.
        """
        saf.saf_write.LOG_LEVEL = logging.DEBUG
        created_dir = False
        if 'test_data' not in os.listdir():
            os.mkdir('test_data')
            created_dir = True
        item = Item(handle='123456789/3', collections=[Collection(handle='123456789/1'),
                                                       Collection(handle='123456789/2')])
        item.add_metadata('dc.title', 'Test Publication', 'en')
        item.add_metadata('dc.type', 'article', 'en')
        item.add_metadata('dc.contributor.author', 'Smith, Adam')
        item.enable_entity('Publication')
        item.add_metadata('local.test.field', 'Nothing', 'en')
        saf.create_saf_package(item, 0, './test_data/')
        self.assertIn('archive_directory', os.listdir('./test_data/'))
        self.assertIn('item_0', os.listdir('./test_data/archive_directory'))
        self.assertEqual(
            ['collections', 'dublin_core.xml', 'handle', 'metadata_dspace.xml', 'metadata_local.xml'].sort(),
            os.listdir('./test_data/archive_directory/item_0').sort())
        self.assertRaises(FileExistsError,  saf.create_saf_package, item, 0, './test_data/')

        saf_item = saf.read_saf_packages('test_data/archive_directory/')[0]
        self.assertIn(MetaDataValue('Test Publication', 'en'), saf_item.metadata['dc.title'])
        self.assertIn(MetaDataValue('Nothing', 'en'), saf_item.metadata['local.test.field'])
        self.assertIn(MetaDataValue('Publication'), saf_item.metadata['dspace.entity.type'])
        self.assertTrue(saf_item.is_entity())
        self.assertIn(Collection(handle='123456789/2'), saf_item.collections)
        self.assertEqual(Collection(handle='123456789/1'), saf_item.get_owning_collection())
        self.assertEqual('123456789/3', saf_item.handle)

        for file in os.listdir('./test_data/archive_directory/item_0'):
            logging.debug(f'Remove file: ./test_data/archive_directory/item_0/{file}')
            os.remove(f'./test_data/archive_directory/item_0/{file}')
        os.rmdir('./test_data/archive_directory/item_0')
        logging.debug('Remove directory: ./test_data/archive_directory/item_0')
        os.rmdir('./test_data/archive_directory')
        logging.debug('Remove directory: ./test_data/archive_directory')
        if created_dir:
            os.rmdir('./test_data')
            logging.debug('Remove directory: ./test_data')
