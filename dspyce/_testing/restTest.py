import copy
import unittest

from dspyce.bitstreams.models import Bundle, Bitstream
from dspyce.rest.exceptions import RestObjectNotFoundError
from dspyce.rest.models import RestAPI
from dspyce.models import Community, Collection, Item


class RestTest(unittest.TestCase):
    rest_url = 'http://localhost:8080/server/api'
    rest_user = 'dspacedemo+admin@gmail.com'
    rest_pwd = 'dspace'

    def get_rest(self):
        """
        Connects to the rest interface by using the class variables as parameters.
        """
        if RestAPI.get_endpoint_info(self.rest_url) is None:
            return
        return RestAPI(self.rest_url, self.rest_user, self.rest_pwd, 'DEBUG', None, 2)

    def create_test_content(self, rest: RestAPI) -> tuple[Community, Collection, Item] | None:
        """
        Creates a test community, collection and item with bitstream in the test repository.
        :return: The community, collection and item created.
        """
        if rest is None: return None
        community = Community()
        community.add_metadata('dc.title', 'Test Community')
        collection = Collection(community=community)
        collection.add_metadata('dc.title', 'Test Collection')
        item = Item(collections=collection)
        item.add_metadata('dc.title', 'Test Item')
        item.add_content('collections', './test_data/saf_item')
        community.to_rest(rest)
        collection.to_rest(rest)
        item.to_rest(rest)
        values = copy.deepcopy(community), copy.deepcopy(collection), copy.deepcopy(item)
        del community, collection, item
        return values

    def test_rest_connect(self):
        """
        Test the authenticated connection to the REST interface.
        """
        rest = self.get_rest()
        if rest is None: return
        self.assertTrue(rest.authenticated)

    def test_manage_content(self):
        rest = self.get_rest()
        community, collection, item = self.create_test_content(rest)
        self.assertNotEqual('', community.uuid)
        self.assertNotEqual('', collection.uuid)
        self.assertNotEqual('', item.uuid)
        self.assertNotEqual('', item.bundles[0].uuid)
        self.assertNotEqual('', item.bundles[0].get_bitstreams()[0].uuid)
        bundle = item.get_bundles()[0]
        self.assertRaises(AttributeError, bundle.delete, rest)
        bundle.delete(rest, True)
        item.get_bundles_from_rest(rest, True)
        self.assertListEqual([], item.get_bundles())
        objs = rest.get_objects_in_scope(community.uuid)
        self.assertEqual(2, len(objs))
        self.assertRaises(AttributeError, collection.delete, rest)
        collection.delete(rest, True)
        print(collection)
        objs = rest.get_objects_in_scope(community.uuid)
        self.assertEqual(0, len(objs))
        uuid = community.uuid
        community.delete(rest)
        self.assertRaises(RestObjectNotFoundError, Community.get_from_rest, rest, uuid)

    def test_item(self):
        """
        Test the item operations with the restAPI
        """
        rest = self.get_rest()
        community, collection, item = self.create_test_content(rest)
        mapped_collection = Collection(community=community)
        mapped_collection.add_metadata('dc.title', 'Mapped Collection', 'en')
        mapped_collection.to_rest(rest)
        item.add_to_mapped_collections(rest, [mapped_collection])
        self.assertEqual(item, mapped_collection.get_items(rest)[0])
        bundle = Bundle('TEXT', 'Bundle containing text items.')
        bundle.add_bitstream(Bitstream('handle', './test_data/saf_item', bundle, primary=True))
        item.add_bundle(bundle)
        item.add_bundles_to_rest(rest)
        self.assertNotEqual('', item.get_bundle('TEXT').uuid)
        item.remove_collection_mapping(rest, None)
        self.assertEqual(0, len(mapped_collection.get_items(rest)))
        item.move_item(rest, mapped_collection)
        self.assertEqual(mapped_collection, item.get_owning_collection())
        self.assertEqual(item, mapped_collection.get_items(rest)[0])
        community.delete(rest, True)

    def test_metadata(self):
        """
        Test metadata operations with the restAPI.
        """
        rest = self.get_rest()
        community = Community()
        self.assertRaises(AttributeError, community.track_updates)
        community.add_metadata('dc.title', 'Test-Community', 'en')
        community.add_metadata('dc.description', 'Test description for this community', 'en')
        community.add_metadata('dc.description', 'Test description pour ce section.', 'fr')
        community.to_rest(rest)
        self.assertListEqual(
            ['Test description for this community', 'Test description pour ce section.'],
            community.get_metadata_values('dc.description')
        )
        metadata = {'dc.description': [{'value': 'Testbeschreibung fuer diesen Bereich', 'language': 'de'}]}
        rest.add_metadata(metadata, community.uuid, 'community', True)
        community = Community.get_from_rest(rest, community.uuid)
        self.assertListEqual(
            ['Test description for this community', 'Test description pour ce section.',
             'Testbeschreibung fuer diesen Bereich'],
            community.get_metadata_values('dc.description')
        )
        rest.move_metadata('dc.description', 2, 1, community.uuid,
                           'community')
        community = Community.get_from_rest(rest, community.uuid)
        self.assertListEqual(
            ['Test description for this community', 'Testbeschreibung fuer diesen Bereich',
             'Test description pour ce section.'],
            community.get_metadata_values('dc.description')
        )
        rest.delete_metadata('dc.description', community.uuid, 'community', 1)
        community = Community.get_from_rest(rest, community.uuid)
        self.assertListEqual(
            ['Test description for this community', 'Test description pour ce section.'],
            community.get_metadata_values('dc.description')
        )
        rest.replace_metadata({'dc.description': {'value': 'Aucune description!', 'language': 'fr'}},
                              community.uuid, 'community', 1)
        community = Community.get_from_rest(rest, community.uuid)
        self.assertListEqual(
            ['Test description for this community', 'Aucune description!'],
            community.get_metadata_values('dc.description')
        )
        community.track_updates()
        community.add_metadata('dc.rights.uri', 'https://creativecommons.org/licenses/by-sa/4.0/')
        community.add_metadata('dc.rights.uri', 'https://creativecommons.org/licenses/by/4.0/')
        community.add_metadata('dc.rights.uri', 'https://creativecommons.org/licenses/by-nd/4.0/')
        community.add_metadata('dc.rights.uri', 'https://creativecommons.org/licenses/by-nc-sa/4.0/')
        community.replace_metadata('dc.title', 'Great Test Community', 'en')
        community.remove_metadata('dc.rights.uri', 'https://creativecommons.org/licenses/by-sa/4.0/')
        community.move_metadata('dc.rights.uri', 2, 0)
        community.update_metadata_rest(rest, False)
        community.replace_metadata('dc.title', 'Großartiger Testbereich', 'de')
        community.update_metadata_rest(rest)
        community = Community.get_from_rest(rest, community.uuid)
        self.assertListEqual(
            [
                'https://creativecommons.org/licenses/by-nc-sa/4.0/',
                'https://creativecommons.org/licenses/by/4.0/',
                'https://creativecommons.org/licenses/by-nd/4.0/'
            ],
            community.get_metadata_values('dc.rights.uri')

        )
        self.assertListEqual(['Großartiger Testbereich'], community.get_metadata_values('dc.title'))
        community.delete(rest, True)


if __name__ == '__main__':
    unittest.main()

