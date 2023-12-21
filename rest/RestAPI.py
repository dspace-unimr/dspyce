import requests
from .. import DSpaceObject, Item, Community, Collection
from ..Relation import Relation
from ..bitstreams import Bundle, ContentFile, IIIFContent
import json
from ..DSpaceObject import parse_metadata_label


def json_to_object(json_content: dict) -> DSpaceObject | Item | Community | Collection | None:
    """
    Converts a dict based on REST-format in to a DSpace Object.

    :param json_content: The json content in a dict format.
    :return: A DSpaceObject object.
    """
    uuid = json_content['uuid']
    name = json_content['name']
    handle = json_content['handle']
    metadata = json_content['metadata']
    doc_type = json_content['type']
    # _links = {}
    # for link in json_content['_links'].keys():
    #    if type(json_content['_links'][link]) is dict and 'href' in json_content['_links'][link].keys():
    #        _links[link] = json_content['_links'][link]['href']
    #    elif type(json_content['_links'][link]) is list:
    #        _links[link] = {li['name']: li['href'] for li in json_content['_links'][link]}
    if json_content is None:
        return None
    match doc_type:
        case 'community':
            obj = Community(uuid, handle=handle, name=name)
        case 'collection':
            obj = Collection(uuid, handle=handle, name=name)
        case 'item':
            obj = Item(uuid, handle=handle, name=name)
        case _:
            obj = DSpaceObject(uuid, handle, name)
    for m in metadata.keys():
        prefix, element, qualifier = parse_metadata_label(m)
        for v in metadata[m]:
            value = v['value']
            lang = v['language'] if 'language' in v.keys() else None
            obj.add_metadata(prefix, element, qualifier, value, lang)
    return obj


def object_to_json(obj: DSpaceObject) -> dict:
    """
    Converts a DSpaceObject class into dict based on a DSpace-Rest format
    :param obj: The object to convert.
    :return: A dictionary in the REST-format.
    """
    uuid = obj.uuid
    handle = obj.handle
    name = obj.name
    obj_type = obj.get_dspace_object_type().lower()
    metadata = {}
    for m in obj.metadata:
        value = m.value if type(m.value) is list else [m.value]
        values = []
        for v in value:
            tmp = {'value': v}
            if m.language is not None and m.language != '':
                tmp['language'] = m.language
            values.append(tmp)
        metadata[m.get_tag()] = values if m.get_tag() not in metadata.keys() else metadata[m.get_tag()] + values

    json_object = {}
    if uuid is not None and uuid != '':
        json_object['uuid'] = uuid
    if handle is not None and handle != '':
        json_object['handle'] = handle
    if name is not None and name != '':
        json_object['name'] = name
    if obj_type is not None and obj_type != '':
        json_object['type'] = obj_type
    if type(obj) is Item:
        obj: Item
        json_object['inArchive'] = obj.in_archive
        json_object['discoverable'] = obj.discoverable
        json_object['withdrawn'] = obj.withdrawn
        if obj.is_entity():
            json_object['entityType'] = obj.metadata.get('dspace.entity.type')
    if obj.handle is not None and obj.handle != '':
        json_object['handle'] = obj.handle
    json_object['metadata'] = metadata
    return json_object


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

    def add_community(self, community: Community | DSpaceObject, create_tree: bool = True) -> Community:
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

    def get_api(self, endpoint: str, params: dict = None) -> dict | None:
        """
        Performs a get request to the api based on a given string endpoint returns the JSON response if successfully.

        :param endpoint: The endpoint information: aka https://self.api_endpoint/<endpoint>
        :param params: A list of additional parameters to pass to the endpoint.
        :return: The json response as a dict.
        """
        endpoint = endpoint if endpoint[0] != '/' else endpoint[1:]
        url = f'{self.api_endpoint}/{endpoint}'
        req = self.session.get(url, params=params if params is not None else {})
        self.update_csrf_token(req)
        json_resp = req.json()
        if req.status_code in (201, 200):
            return json_resp
        elif req.status_code == 404:
            print(req.json())
            print(f'Object behind "{url}" does not exists')
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
        try:
            obj = json_to_object(self.get_api(url))
        except TypeError:
            obj = None
            print('An object could not be found!')
        return obj

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
        get_result = self.get_api(url)
        if get_result is None:
            print('Problems with getting owning Collection!')
            return []
        owning_collection = json_to_object(get_result)
        mapped_collections = self.get_api(f'core/items/{item_uuid}/mappedCollections')['_embedded']['mappedCollections']
        return [owning_collection] + list(filter(lambda x: x is not None,
                                                 [json_to_object(m) for m in mapped_collections]))

    def get_item(self, uuid: str, get_related: bool = True, pre_downloaded_item: Item = None) -> Item | None:
        """
        Retrieves a DSpace-Item by its uuid from the API.

        :param uuid: The uuid of the item to get.
        :param get_related: If true, also retrieves related items from the API.
        :param pre_downloaded_item: If a pre downloaded item is provided (aka blank dso), then only additional
        information such as relationships, owning collection, bundles and bitstreams will be provided.
        :return: An object of the class Item.
        """
        dso: Item
        dso = self.get_dso(uuid, 'items') if pre_downloaded_item is None else pre_downloaded_item
        if dso is None:
            print(f'The item with uuid "{uuid}" could not be found.')
            return None
        if get_related:
            dso.relations = self.get_item_relationships(dso.uuid)
        dso.collections = self.get_item_collections(uuid)
        return dso

    def get_items_in_scope(self, scope_uuid: str, query: str = '', size: int = -1, page: int = -1,
                           full_item: bool = True) -> list[Item]:
        """
        Returns a list of DSpace items in a given collection or community. Can be further reduced by query parameter.

        :param scope_uuid: The uuid of the collection to retrieve the items from.
        :param query: Additional query parameters for the request.
        :param size: The number of objects per page. Use -1 to select the default.
        :param page: The page to retrieve if a paginated list is returned. Use -1 to retrieve all.
        :param full_item: If the full item information should be downloaded (Including relationships, bundles and
        bitstreams. This can be slower due to additional api calls).
        :return: A list of Item objects.
        """
        query_params = {'scope': scope_uuid}
        if query != '':
            query_params.update({'query': query})
        if page > -1:
            query_params.update({'page': page})

        search_req = self.get_api('discover/search/objects', query_params)
        json_res = search_req['_embedded']['searchResult']
        try:
            item_list = [json_to_object(i['_embedded']['indexableObject']) for i in json_res['_embedded']['objects']]
            item_list = list(filter(lambda x: isinstance(x, Item), item_list))
            if full_item:
                item_list = [self.get_item(i.uuid, True, i) for i in item_list]
        except KeyError as e:
            print(f'Problems with the following answer:\n{json_res}\n')
            raise e

        if page == -1:
            number_pages = json_res['page']['totalPages']
            for n in range(1, number_pages):
                item_list += self.get_items_in_scope(scope_uuid, query, size, n, full_item)

        return list(filter(lambda x: x is not None, item_list))

    def get_metadata_field(self, schema: str = '', element: str = '', qualifier: str = '',
                           field_id: int = -1) -> list[dict]:
        """
        Checks if given metadata field exists in the DSpace instance. Returns one or more found metadata fields in a
        list of dict.

        :param schema: The schema of the field, if empty this field won't be taken in account for the search request.
        :param element: The element of the field, if empty this field won't be taken in account for the search request.
        :param qualifier: The qualifier of the field, if empty this field won't be taken in account for the search
        request.
        :param field_id: The exact metadata field id to look for. If the correct fields is already known.
        :return: A list of dictionaries in the following form: {id: <id>, element: <element>, qualifier: <qualifier>,
        scopeNote: <scopeNote>, schema: {id: <schema-id>, prefix: <prefix>, namespace: <namespace>]}
        """

        def parse_json_resp(json_resp: dict) -> dict:
            """
            Parses the answer of the REST-API response and returns it into the wanted format.
            """
            schema_resp = json_resp['_embedded']['schema']
            return {'id': json_resp['id'],
                    'element': json_resp['element'],
                    'qualifier': json_resp['qualifier'],
                    'scopeNote': json_resp['scopeNote'],
                    'schema': {'id': schema_resp['id'], 'prefix': schema_resp['prefix'],
                               'namespace': schema_resp['namespace']}
                    }

        url = f'core/metadatafields/'
        if field_id > -1:
            url += f'/{field_id}'
            json_get = self.get_api(url)
            return [] if json_get is None else [parse_json_resp(json_get)]
        else:
            url += 'search/byFieldName'
            params = {}
            if schema != '':
                params.update({'schema': schema})
            if element != '':
                params.update({'element': element})
            if qualifier != '':
                params.update({'qualifier': qualifier})
            json_get = self.get_api(url, params)
            if json_get is None:
                return []
            pages = json_get['page']['totalPages']
            current_page = json_get['page']['number'] + 1
            results = [json_get]
            for p in range(current_page, pages):
                params['page'] = current_page
                results.append(self.get_api(url, params))
            field_objects = []
            for r in results:
                field_objects += [parse_json_resp(i) for i in r['_embedded']['metadatafields']]
            return field_objects

    def update_metadata(self, obj: DSpaceObject):
        if obj.uuid == '' and obj.handle == '':
            raise ValueError('The object must provide identifier information! Could not find those in ' + str(obj))
        pass
