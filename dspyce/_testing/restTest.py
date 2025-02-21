import unittest

from dspyce.rest import RestObjectNotFoundError
from dspyce.rest.models import RestAPI
from dspyce.models import DSpaceObject, Community, Collection, Item


class RestTest(unittest.TestCase):
    rest_url = 'http://localhost:8080/server/api'
    rest_user = 'dspacedemo+admin@gmail.com'
    rest_pwd = 'dspace'

    def get_rest(self):
        if RestAPI.get_endpoint_info(self.rest_url) is None:
            return
        return RestAPI(self.rest_url, self.rest_user, self.rest_pwd, 'DEBUG', None, 2)

    def test_rest_connect(self):
        rest = self.get_rest()
        if rest is None: return
        self.assertTrue(rest.authenticated)

    def test_manage_content(self):
        rest = self.get_rest()
        if rest is None: return
        community = Community()
        community.add_metadata('dc.title', 'Test Community')
        collection = Collection(community=community)
        collection.add_metadata('dc.title', 'Test Collection')
        item = Item(collections=collection)
        item.add_metadata('dc.title', 'Test Item')
        item.add_content('collections', './test_data/saf_item')
        community.to_rest(rest)
        self.assertNotEqual('', community.uuid)
        collection.to_rest(rest)
        self.assertNotEqual('', collection.uuid)
        item.to_rest(rest)
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


if __name__ == '__main__':
    unittest.main()

