import requests
from .. import DSpaceObject, Item, Community, Collection
from ..Relation import Relation
from .converter import object_to_json, json_to_object
from ..bitstreams import Bundle, ContentFile, IIIFContent
import json


class RestAPI:
    api_endpoint: str
    """The address of the api_endpoint."""
    username: str
    """The username of the user communicating to the endpoint."""
    password: str
    """The password of the user communicating with the endpoint."""
    session: requests.sessions.Session
    """The active session."""
    authenticated: bool = False
    """Provides information about the authentication status."""

    def __init__(self, api_endpoint: str, username: str = None, password: str = None):
        """
        Creates a new object of the RestAPI class using
        """
        self.session = requests.Session()
        self.api_endpoint = api_endpoint
        self.username = username
        self.password = password
        self.req_headers = {'Content-type': 'application/json', 'User-Agent': 'Python REST Client'}
        if username is not None and password is not None:
            self.authenticated = self.authenticate_api()

    def update_csrf_token(self, req: requests.models.Request | requests.models.Response):
        """
        Update the csrf_token based on the current requests.

        :param req: The current request to check the token from.
        """
        if 'DSPACE-XSRF-TOKEN' in req.headers:
            csrf = req.headers['DSPACE-XSRF-TOKEN']
            self.session.headers.update({'X-XSRF-Token': csrf})
            self.session.cookies.update({'X-XSRF-Token': csrf})

    def post_api(self, url: str, json_data: dict, params: dict) -> dict:
        req = self.session.post(url)
        self.update_csrf_token(req)
        # print(f'Adding object in "{url}" with params ({params}):\n{json_data}')
        resp = self.session.post(url, json=json_data, headers=self.req_headers, params=params)
        if resp.status_code in (201, 200):
            # Success post request
            json_resp = resp.json()
            print(f'\tSuccessfully added object with uuid: {json_resp["uuid"]}')
            return json_resp
        else:
            raise requests.exceptions.RequestException(f'\nStatuscode: {resp.status_code}\n'
                                                       f'Could not post content: \n{json_data}\nWith params: {params}')

    def authenticate_api(self) -> bool:
        """
        Authenticates to the REST-API

        :return: True, if the authentication worked.
        """
        print('Trying to authenticate against the REST-API:')
        auth_url = f'{self.api_endpoint}/authn/login'
        req = self.session.post(auth_url)
        self.update_csrf_token(req)
        req = self.session.post(auth_url, data={'user': self.username, 'password': self.password})
        if 'Authorization' in req.headers:
            self.session.headers.update({'Authorization': req.headers.get('Authorization')})
        # Check if authentication was successfully:
        auth_status = self.session.get(auth_url.replace('login', 'status')).json()
        if 'authenticated' in auth_status and auth_status['authenticated'] is True:
            print(f'The authentication as "{self.username}" was successfully')
            return True
        else:
            print('The authentication did not work.')
            return False

    def add_object(self, obj: DSpaceObject) -> DSpaceObject | Collection | Item | Community:
        """
        Creates a new object in the DSpace Instance.

        :param obj: The object to create.
        :return: The newly created object.
        """
        if not self.authenticated:
            raise ConnectionRefusedError('Authentication needed.')
        params = {}
        match obj.get_dspace_object_type():
            case 'Item':
                obj: Item
                add_url = f'{self.api_endpoint}/core/items'
                params = {'owningCollection': obj.get_owning_collection().uuid}
            case 'Community':
                obj: Community
                if obj.parent_community is None:
                    add_url = f'{self.api_endpoint}/core/communities'
                else:
                    add_url = f'{self.api_endpoint}/core/communities'
                    params = {'parent': obj.parent_community.uuid}
            case 'Collection':
                obj: Collection
                add_url = f'{self.api_endpoint}/core/collections'
                params = {'parent': obj.community.uuid}
            case _:
                raise ValueError(f'Object type {obj.get_dspace_object_type()} is not allowed as a parameter!')
        obj_json = object_to_json(obj)

        return json_to_object(self.post_api(add_url, json_data=obj_json, params=params))

    def add_bundle(self, bundle: Bundle, item_uuid: str) -> Bundle:
        """
        Creates a new bundle based on a given bundle Object in DSpace and returns the created object.
        :param bundle: The bundle object to create.
        :param item_uuid: The uuid_of the item to create the bundle for.
        :return: The newly created object returned from DSpace.
        """
        if not self.authenticated:
            raise ConnectionRefusedError('Authentication needed.')
        params = {}
        add_url = f'{self.api_endpoint}/core/items/{item_uuid}/bundles'
        obj_json = {'name': bundle.name}
        if bundle.description != '':
            obj_json['metadata'] = {'dc.description': [{'value': bundle.description}]}
        resp = self.post_api(add_url, json_data=obj_json, params=params)
        uuid = resp['uuid']
        name = resp['name']
        return Bundle(name=name, uuid=uuid)

    def add_bitstream(self, bitstream: ContentFile, bundle: Bundle) -> str:
        """
        Creates a new bitstream in a given dspace bundle.
        :param bitstream: The bitstream to upload.
        :param bundle: The bundle to upload the item in.
        :return: The uuid of the newly created bitstream.
        """
        if not self.authenticated:
            raise ConnectionRefusedError('Authentication needed.')
        add_url = f'{self.api_endpoint}/core/bundles/{bundle.uuid}/bitstreams'
        obj_json = {'name': bitstream.file_name, 'metadata': {'dc.title': [{'value': bitstream.file_name}],
                                                              'dc.description': [{'value': bitstream.description}]},
                    'bundleName': bundle.name}
        if isinstance(bitstream, IIIFContent):
            bitstream: IIIFContent
            obj_json['metadata']['iiif.label'] = [{'value': bitstream.iiif['label']}]
            obj_json['metadata']['iiif.toc'] = [{'value': bitstream.iiif['toc']}]
            obj_json['metadata']['iiif.image.width'] = [{'value': bitstream.iiif['w']}]
            obj_json['metadata']['iiif.image.height'] = [{'value': bitstream.iiif['h']}]
        data_file = {'file': (bitstream.file_name, open(bitstream.path + bitstream.file_name, 'rb'))}
        req = self.session.post(add_url)
        self.update_csrf_token(req)
        headers = self.session.headers
        headers.update({'Content-Encoding': 'gzip', 'User-Agent': self.req_headers['User-Agent']})
        req = requests.Request('POST', add_url,
                               data={'properties': json.dumps(obj_json) + ';type=application/json'}, headers=headers,
                               files=data_file)
        resp = self.session.send(self.session.prepare_request(req))
        try:
            return resp.json()['uuid']
        except requests.exceptions.JSONDecodeError | KeyError as e:
            print('\n')
            print(resp)
            print(resp.headers)
            print('\n')
            raise e

    def add_relationship(self, relation: Relation) -> dict:
        """
        Creates a new relationship between to items based on the information in the Relation object.

        :param relation: The relation to create.
        """
        if not self.authenticated:
            raise ConnectionRefusedError('Authentication needed.')
        add_url = f'{self.api_endpoint}/core/relationships?relationshipType={relation.relation_type}'
        if relation.items[0] is None or relation.items[1] is None:
            raise ValueError(f'Could not create Relation because of missing item information in relation: {relation}')
        uuid_1 = relation.items[0].uuid
        uuid_2 = relation.items[1].uuid
        if uuid_1 == '' or uuid_2 == '':
            raise ValueError(f'Relation via RestAPI can only be created by using item-uuids, but found: {relation}')
        req = self.session.post(add_url)
        self.update_csrf_token(req)
        item_url = f'{self.api_endpoint}/core/items'
        headers = self.session.headers
        headers.update({'Content-Type': 'text/uri-list', 'User-Agent': self.req_headers['User-Agent']})
        resp = self.session.post(add_url, f'{item_url}/{uuid_1} \n {item_url}/{uuid_2}', headers=headers)

        if resp.status_code in (201, 200):
            # Success post request
            print(f'\t\tCreated relationship: {relation}')
            return resp.json()
        else:
            raise requests.exceptions.RequestException(f'{resp.status_code}: Could not post relation: \n{relation}\n'
                                                       f'Got headers: {resp.headers}')

    def add_community(self, community: Community | DSpaceObject, create_tree: bool = True) -> Collection:
        """
        Creates a new community in the DSpace instance and its owning community if create_tree is True.

        :param community: The collection object to create in DSpace.
        :param create_tree: If the owning communities shall be created as well.
        :return: Returns the newly created Community.
        """
        parent_community = community.parent_community
        if parent_community is not None and parent_community.uuid == '' and create_tree:
            community.parent_community = self.add_community(parent_community, create_tree)

        return self.add_object(community)

    def add_collection(self, collection: Collection, create_tree: bool = True) -> Collection:
        """
        Creates a new collection in the DSpace instance and its owning communities if create_tree is True.

        :param collection: The collection object to create in DSpace.
        :param create_tree: If the owning communities shall be created as well.
        :return: Returns the newly created Collection.
        """
        community = collection.community
        if community.uuid == '' and create_tree:
            collection.community = self.add_community(community, create_tree)

        return self.add_object(collection)

    def add_item(self, item: Item, create_tree: bool = True) -> Item:
        """
        Adds an item object to DSpace including files and relations. Based on the add_object method.

        :param item: The item to push into DSpace.
        :param create_tree: Creates the owning collections and communities above this item if not yet existing.
        :return: An item object including the new uuid.
        """
        bitstreams = item.contents
        collection_list = item.collections
        if create_tree:
            if collection_list[0].uuid == '':
                col: Collection = self.add_collection(collection_list[0], create_tree)
                collection_list[0] = col
        dso = self.add_object(item)
        bundles = {i.name: i for i in [self.add_bundle(b, dso.uuid) for b in item.get_bundles()]}
        for b in bitstreams:
            self.add_bitstream(b, bundles[b.bundle.name])
        item.uuid = dso.uuid
        relations = item.relations if item.is_entity() else []
        if len(relations) > 0:
            relation_types = {r.relation_key: r.relation_type for r in self.get_relations_by_type(
                item.get_entity_type())}
            try:
                relations = list(map(lambda x: Relation(x.relation_key, x.items, relation_types[x.relation_key]),
                                     relations))
            except KeyError as e:
                print(f'Could not find relation in the list: {relation_types}')
                raise e
        for r in relations:
            self.add_relationship(r)

        return item

    def get_api(self, endpoint: str) -> dict | None:
        """
        Performs a get request to the api based on a given string endpoint returns the JSON response if successfully.

        :param endpoint: The endpoint information: aka https://self.api_endpoint/<endpoint>
        :return: The json response as a dict.
        """
        url = f'{self.api_endpoint}/{endpoint}'
        req = self.session.get(url)
        self.update_csrf_token(req)
        json_resp = req.json()
        if req.status_code in (201, 200):
            return json_resp
        elif req.status_code == 404:
            print('Object behind "{url}" does not exists')
            return None
        else:
            raise requests.exceptions.RequestException(f'Could not get item with from endpoint: {url}')

    def get_dso(self, uuid: str, endpoint: str) -> DSpaceObject | Item | Collection | Community:
        """
        Retrieves a DSpace object from the api based on its uuid and the endpoint information.

        :param uuid: The uuid of the object.
        :param endpoint: The endpoint string. Must be one of ('items', 'collections', 'communities')
        :return: Returns a DSpace object
        """
        url = f'core/{endpoint}/{uuid}'
        if endpoint not in ('items', 'collections', 'communities'):
            raise ValueError(f"The endpoint '{endpoint}' does not exist. endpoint must be one of"
                             "('items', 'collections', 'communities')")
        return json_to_object(self.get_api(url))

    def get_relations_by_type(self, entity_type: str) -> list[Relation]:
        """
        Parses the REST API and returns a list of relationships, which have the given entity on the left or right side.

        :param entity_type: The entity_type to look for.
        :return: Return s a list of relations.
        """
        add_url = f'{self.api_endpoint}/core/relationshiptypes/search/byEntityType?type={entity_type}'
        req = self.session.get(add_url)
        self.update_csrf_token(req)
        json_resp = req.json()
        if req.status_code in (201, 200):
            rel_dict = json_resp['_embedded']['relationshiptypes']
            rel_list = []
            for r in rel_dict:
                rel_list.append(Relation(r['leftwardType'], relation_type=r['id']))
                rel_list.append(Relation(r['rightwardType'], relation_type=r['id']))
            return rel_list
        else:
            raise requests.exceptions.RequestException(f'Could not parse response with header: {req.headers}')

    def get_item_relationships(self, item_uuid: str) -> list[Relation]:
        """
        Retrieves a list of relationships of DSpace entity from the api.

        :param item_uuid: The uuid of the item to retrieve the relationships for.
        :return: A list of relation objects.
        """
        url = f'{self.api_endpoint}/core/items/{item_uuid}/relationships'
        req = self.session.get(url)
        self.update_csrf_token(req)
        json_resp = req.json()
        relations = []
        if req.status_code in (201, 200):
            rel_list = json_resp['_embedded']['relationships']
            for r in rel_list:
                left_item = r['_links']['leftItem']['href'].split('/')[-1]
                right_item = r['_links']['rightItem']['href'].split('/')[-1]
                direction = 'leftwardType' if item_uuid == right_item else 'rightwardType'
                # Retrieve the type information:
                type_req = self.session.get(r['_links']['relationshipType']['href'])
                rel_key = type_req.json()[direction]
                rel_type = type_req.json()['id']
                # Set the correct item order.
                left_item = self.get_item(left_item, False)
                right_item = self.get_item(right_item, False)
                items = (left_item, right_item) if direction == 'rightwardType' else (right_item, left_item)
                relations.append(Relation(rel_key, items, rel_type))
            return relations
        else:
            return []

    def get_item_collections(self, item_uuid: str) -> list[Collection]:
        """
        Retrieves a list of collections from the REST-API based on the uuid of an item. The first will be the owning
        collection.

        :param item_uuid: The uuid of the item.
        """
        url = f'core/items/{item_uuid}/owningCollection'
        owning_collection = json_to_object(self.get_api(url))
        mapped_collections = self.get_api(f'core/items/{item_uuid}/mappedCollections')['_embedded']['mappedCollections']
        return [owning_collection] + list(filter(lambda x: x is not None,
                                                 [json_to_object(m) for m in mapped_collections]))

    def get_item(self, uuid: str, get_related: bool = True) -> Item:
        """
        Retrieves a DSpace-Item by its uuid from the API.

        :param uuid: The uuid of the item to get.
        :param get_related: If true, also retrieves related items from the API.
        :return: An object of the class Item.
        """
        dso: Item
        dso = self.get_dso(uuid, 'items')
        if get_related:
            dso.relations = self.get_item_relationships(dso.uuid)
        dso.collections = self.get_item_collections(uuid)
        return dso

    def update_metadata(self, obj: DSpaceObject):
        if obj.uuid == '' and obj.handle == '':
            raise ValueError('The object must provide identifier information! Could not find those in ' + str(obj))
        pass
