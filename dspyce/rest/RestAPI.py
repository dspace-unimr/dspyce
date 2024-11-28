from concurrent.futures import ThreadPoolExecutor
import json
import logging
import requests
import requests.adapters
from requests.exceptions import InvalidJSONError

from ..DSpaceObject import DSpaceObject
from ..Item import Item
from ..Community import Community
from ..Collection import Collection
from ..Relation import Relation
from ..bitstreams import Bundle, Bitstream, IIIFBitstream
from ..metadata import MetaData


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
        for v in metadata[m]:
            value = v['value']
            lang = v['language'] if 'language' in v.keys() else None
            obj.add_metadata(tag=m, value=value, language=lang)
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
    metadata = {key: [dict(v) for v in obj.metadata[key]] for key in obj.metadata.keys()}

    json_object = {}
    if uuid is not None and uuid != '':
        json_object['uuid'] = uuid
    if handle is not None and handle != '':
        json_object['handle'] = handle
    if name is not None and name != '':
        json_object['name'] = name
    if obj_type is not None and obj_type != '':
        json_object['type'] = obj_type
    if isinstance(obj, Item):
        obj: Item
        json_object['inArchive'] = obj.in_archive
        json_object['discoverable'] = obj.discoverable
        json_object['withdrawn'] = obj.withdrawn
        if obj.is_entity():
            json_object['entityType'] = obj.get_entity_type()
    if obj.handle is not None and obj.handle != '':
        json_object['handle'] = obj.handle
    json_object['metadata'] = metadata
    return json_object


class RestAPI:
    """
    The class RestAPI represents the REST API of a DSpace 7 backend. It helps to get, push, update or remove Objects,
    Bitstreams, Relations, MetaData and other from a DSpace Instance.
    """
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
    dspace_version: str
    """The dspace version used by the API endpoint."""
    workers: int
    """The number of worker threads used by the ThreadPoolExecutor."""

    def __init__(self, api_endpoint: str, username: str = None, password: str = None,
                 log_level: int | str = logging.INFO, log_file: str = None, workers: int = 0):
        """
        Creates a new object of the RestAPI class using

        :param api_endpoint: The api endpoint to connect to. (For example https://demo.dspace.org/server/api)
        :param username: The username of the user for authentication.
        :param password: The password of the user for authentication.
        :param log_level: The log_level used for Logging. Must be string or integer. The strings must be one of
            the following: DEBUG, INFO, WARNING, ERROR, CRITICAL. Default is INFO.
        :param log_file: A possible name and path of the log file. If None provided, all output will be logged to the
            console.
        :param workers: The number of worker threads to use, if this value equals 0 no ThreadPoolExecutor is used.
            Default is 0.
        """
        log_level_types = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING,
                           'ERROR': logging.ERROR, 'CRITICAL': logging.CRITICAL}
        if isinstance(log_level, str) and log_level.upper() not in log_level_types.keys():
            raise TypeError(f"Invalid log level: {log_level}. Must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL.")
        elif isinstance(log_level, str):
            log_level = log_level_types[log_level]
        logging.basicConfig(level=log_level, filename=log_file, encoding='utf8',
                            format='%(asctime)s - %(levelname)s: %(message)s')
        self.session = requests.Session()
        self.api_endpoint = api_endpoint
        endpoint_info = RestAPI.get_endpoint_info(api_endpoint)
        if endpoint_info is None:
            logging.critical(f'Couldn\'t reach the api_endpoint with the address "{api_endpoint}".')
            raise requests.exceptions.ConnectionError(f'Could not reach the endpoint {api_endpoint}.')
        else:
            self.dspace_version = endpoint_info['dspaceVersion']
        self.username = username
        self.password = password
        self.req_headers = {'Content-type': 'application/json', 'User-Agent': 'Python REST Client'}
        if username is not None and password is not None:
            self.authenticated = self.authenticate_api()
        self.set_workers(workers)

    @staticmethod
    def get_endpoint_info(api: str) -> dict[str, str] | None:
        """
        Checks if the request endpoint is reachable and returns name, ui_address, server_address and dspace-Version

        :param api: The url of the API endpoint.
        """
        logging.debug(f'Checking endpoint status.')
        req = requests.get(api)
        if req.status_code in (204, 201, 200):
            try:
                logging.debug(f'Established connection with the endpoint. Status code: {req.status_code}')
                resp = req.json()
                logging.info(f'Connection with endpoint "{api}" established. Instance-name: "{resp["dspaceName"]}",'
                             f'UI-address: "{resp["dspaceUI"]}", Server-address: "{resp["dspaceServer"]}",'
                             f'DSpace-Version: "{resp["dspaceVersion"]}"')
                return resp
            except json.decoder.JSONDecodeError:
                logging.critical('The reponse could not be parsed. Are you sure, that you\'ve provided the url of a '
                                 'valid dspace 7.x endpoint?')
                return None
        else:
            logging.warning(f'Problems with establishing a connection to the endpoint. Status code: {req.status_code}')
            return None

    def update_csrf_token(self, req: requests.models.Request | requests.models.Response):
        """
        Update the csrf_token based on the current requests.

        :param req: The current request to check the token from.
        """
        if 'DSPACE-XSRF-TOKEN' in req.headers:
            csrf = req.headers['DSPACE-XSRF-TOKEN']
            self.session.headers.update({'X-XSRF-Token': csrf})
            self.session.cookies.update({'X-XSRF-Token': csrf})

    def set_workers(self, workers: int):
        """
        Set the number of workers to be used by the TreadPoolExecutor.

        :param workers: The number of worker threads to use.
        """
        self.workers = workers
        logging.debug('Initializing with %i workers.' % workers)
        if self.workers > requests.adapters.DEFAULT_POOLSIZE:
            adapter = requests.adapters.HTTPAdapter(pool_maxsize=self.workers)
            logging.info('The number of workers (%i) exceeds the number of default connections. '
                         'Increasing the number of default connections.' % workers)
            self.session.mount(self.api_endpoint, adapter)

    def authenticate_api(self) -> bool:
        """
        Authenticates to the REST-API

        :return: True, if the authentication worked.
        """
        logging.info(f'Trying to authenticate against the REST-API "{self.api_endpoint}", with user {self.username}')
        auth_url = f'{self.api_endpoint}/authn/login'
        req = self.session.post(auth_url)
        self.update_csrf_token(req)
        req = self.session.post(auth_url, data={'user': self.username, 'password': self.password})
        if 'Authorization' in req.headers:
            self.session.headers.update({'Authorization': req.headers.get('Authorization')})
        # Check if authentication was successfully:
        auth_session = self.session.get(auth_url.replace('login', 'status'))
        try:
            auth_status = auth_session.json()
            if 'authenticated' in auth_status and auth_status['authenticated'] is True:
                logging.info(f'The authentication as "{self.username}" was successfully')
                return True
        except requests.exceptions.JSONDecodeError as e:
            logging.error('Problem with authenticating to the api.')
            logging.error(auth_session)
            logging.exception(e)

        logging.critical('The authentication was unsuccessful.')
        return False

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
        if req.status_code in (204, 201, 200):
            logging.debug(f'Successfully performed GET request to endpoint {endpoint}')
            return req.json()
        if req.status_code == 404:
            logging.warning(f'Object behind "{url}" does not exists.')
            logging.warning(req.json())
            return None
        logging.error(f'Problem with performing GET request to endpoint {endpoint}.')
        logging.error(req)

        raise requests.exceptions.RequestException(f'Could not get item with from endpoint: {url}')

    def post_api(self, url: str, json_data: dict, params: dict) -> dict:
        """
        Performs a post action on the RestAPI endpoint.
        """
        req = self.session.post(url)
        self.update_csrf_token(req)
        logging.debug(f'Performing POST request in "{url}" with params({params}):{json_data}')
        try:
            resp = self.session.post(url, json=json_data, headers=self.req_headers, params=params)
        except InvalidJSONError as e:
            logging.error(f'Invalid json format in the query data: {json_data}')
            raise e
        if resp.status_code in (201, 200):
            # Success post request
            json_resp = resp.json()
            logging.info(f'Successfully added object with uuid: {json_resp["uuid"]}')
            return json_resp
        logging.error(f'Could not POST content: {json_data}.\n\tWith params: {params}\n\tOn endpoint: {url}')
        logging.error(f'Statuscode: {resp.status_code}')
        raise requests.exceptions.RequestException(f'\nStatuscode: {resp.status_code}\n'
                                                   f'Could not post content: \n\t{json_data}'
                                                   f'\nWith params: {params}\nOn endpoint:\n\t{url}')

    def patch_api(self, url: str, json_data: list, params: dict = None) -> dict | None:
        """
        Sends a patch request to the api in order to update, add or remove metadata information.

        :param url: The url of the api, where to replace the metadata.
        :param json_data: The data object containing action information.
        :param params: Additional params for the operation.
        :return: The JSON response of the server, if the operation was successfully.
        :raise RequestException: If the JSON response doesn't have the status code 200 or 201
        """
        url = f'{self.api_endpoint}/{url}' if self.api_endpoint not in url else url
        logging.debug(f'Performing PATCH request in "{url}" with params({params}):{json_data}')
        req = self.session.patch(url)
        self.update_csrf_token(req)
        resp = self.session.patch(url, json=json_data, headers=self.req_headers)

        if resp.status_code in (201, 200):
            # Success post request
            json_resp = resp.json()
            logging.info(f'Successfully updated object with uuid: {json_resp["uuid"]}.')
            return json_resp

        if resp.status_code == 204:
            operation = [int((i['op'] if 'op' in i.keys() else '') == 'remove') - 1 for i in json_data]
            if sum(operation) == 0:
                logging.info('Successfully deleted objects.')
                return None

        logging.error(f'Could not PATCH content: {json_data}.\n\tWith params: {params}\n\tOn endpoint: {url}')
        logging.error(f'Statuscode: {resp.status_code}')
        raise requests.exceptions.RequestException(f'\nStatuscode: {resp.status_code}\n'
                                                   f'Could not put content: \n\t{json_data}'
                                                   f'\nWith params: {params}\nOn endpoint:\n\t{url}')

    def put_api(self, url: str, data: list | dict | str, params: dict = None, content_type: str = None) -> None:
        """
        Sends a PUT request to the api.

        :param url: The path in the api.
        :param data: The data object containing action information.
        :param params: Additional params for the operation.
        :param content_type: The content_type of the data. The default ist self.request.headers['Content-Type']
        :raise RequestException: If the JSON response doesn't have the status code 200 or 201
        """
        url = f'{self.api_endpoint}/{url}' if self.api_endpoint not in url else url
        logging.debug(f'Performing PUT request in "{url}" with params({params}):{data}')
        req = self.session.put(url)
        self.update_csrf_token(req)
        headers = self.req_headers
        if content_type != headers['Content-type']:
            headers['Content-type'] = content_type
        resp = self.session.put(url, data=data, headers=headers)

        if resp.status_code in (204, 200):
            # Success put request
            logging.info(f'Successfully performed put request on endpoint {url}.')
            return

        logging.error(f'Could not PUT content: {data}.\n\tWith params: {params}\n\tOn endpoint: {url}')
        logging.error(f'Statuscode: {resp.status_code}')
        raise requests.exceptions.RequestException(f'\nStatuscode: {resp.status_code}\n'
                                                   f'Could not put content: \n\t{data}'
                                                   f'\nWith params: {params}\nOn endpoint:\n\t{url}')

    def delete_api(self, url: str, params: dict = None, content_type: str = None) -> None:
        """
        Sends a DELETE request to the api.

        :param url: The path in the api.
        :param params: Additional params for the operation.
        :param content_type: The content_type of the data. The default ist self.request.headers['Content-Type']
        :raise RequestException: If the JSON response doesn't have the status code 200 or 201
        """
        url = f'{self.api_endpoint}/{url}' if self.api_endpoint not in url else url
        logging.debug(f'Performing DELETE request in "{url}" with params({params})')
        params = {} if params is None else params
        req = self.session.delete(url)
        self.update_csrf_token(req)
        headers = self.req_headers
        if content_type != headers['Content-type']:
            headers['Content-type'] = content_type
        resp = self.session.delete(url, params=params, headers=headers)

        if resp.status_code in (204, 200):
            # Success DELETE request
            logging.info(f'Successfully performed DELETE request on endpoint {url}.')
            return

        logging.error(f'Could not DELETE on endpoint: {url} With params: {params}')
        logging.error(f'Statuscode: {resp.status_code}')
        exception = requests.exceptions.RequestException(f'\nStatuscode: {resp.status_code}\n'
                                                         f'\nWith params: {params}\nOn endpoint:\n\t{url}')
        raise exception

    def add_object(self, obj: DSpaceObject) -> DSpaceObject | Collection | Item | Community:
        """
        Creates a new object in the DSpace Instance.

        :param obj: The object to create.
        :return: The newly created object.
        """
        if not self.authenticated:
            logging.critical('Could not add object, authentication required!')
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
            logging.critical('Could not add object, authentication required!')
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

    def add_bitstream(self, bitstream: Bitstream, bundle: Bundle) -> str:
        """
        Creates a new bitstream in a given dspace bundle.
        :param bitstream: The bitstream to upload.
        :param bundle: The bundle to upload the item in.
        :return: The uuid of the newly created bitstream.
        """
        if not self.authenticated:
            logging.critical('Could not add object, authentication required!')
            raise ConnectionRefusedError('Authentication needed.')
        add_url = f'{self.api_endpoint}/core/bundles/{bundle.uuid}/bitstreams'
        obj_json = {'name': bitstream.file_name, 'metadata': {'dc.title': [{'value': bitstream.file_name}],
                                                              'dc.description': [{'value': bitstream.description}]},
                    'bundleName': bundle.name}
        if isinstance(bitstream, IIIFBitstream):
            bitstream: IIIFBitstream
            obj_json['metadata']['iiif.label'] = [{'value': bitstream.iiif['label']}]
            obj_json['metadata']['iiif.toc'] = [{'value': bitstream.iiif['toc']}]
            obj_json['metadata']['iiif.image.width'] = [{'value': bitstream.iiif['w']}]
            obj_json['metadata']['iiif.image.height'] = [{'value': bitstream.iiif['h']}]
        logging.debug(f'Adding bitstream: {obj_json}')
        bitstream_file = bitstream.get_bitstream_file()
        data_file = {'file': (bitstream.file_name, bitstream_file)} if bitstream_file is not None else None
        req = self.session.post(add_url)
        self.update_csrf_token(req)
        headers = self.session.headers
        headers.update({'Content-Encoding': 'gzip', 'User-Agent': self.req_headers['User-Agent']})
        req = requests.Request('POST', add_url,
                               data={'properties': json.dumps(obj_json) + ';type=application/json'}, headers=headers,
                               files=data_file)
        resp = self.session.send(self.session.prepare_request(req))
        try:
            uuid = resp.json()['uuid']
            logging.info(f'Successfully added bitstream with uuid "{uuid}"')
            return uuid
        except KeyError as e:
            logging.error(f'Problem with adding bitstream:\n{resp}\n\t{resp.headers}')
            raise e

    def add_relationship(self, relation: Relation) -> dict:
        """
        Creates a new relationship between to items based on the information in the Relation object.

        :param relation: The relation to create.
        """
        if not self.authenticated:
            logging.critical('Could not add object, authentication required!')
            raise ConnectionRefusedError('Authentication needed.')
        if relation.relation_type is None:
            logging.info('No relation type specified, trying to find relation-type via the rest endpoint.')
            left_item_type = relation.items[0].get_entity_type()
            rels = self.get_relations_by_type(left_item_type)
            rels = list(filter(lambda x: x.relation_key == relation.relation_key, rels))
            if len(rels) != 1:
                if len(rels) > 1:
                    logging.critical('Something went wrong with on the rest-endpoint: found more than one relation with'
                                     f' the name {relation.relation_key}')
                else:
                    logging.error(f'Didn\'t find relation with name {relation.relation_key}')
            else:
                relation.relation_type = rels[0].relation_type
                logging.debug(f'Found relationtype "{relation.relation_type}" for the name "{relation.relation_key}"')
        add_url = f'{self.api_endpoint}/core/relationships?relationshipType={relation.relation_type}'
        if relation.items[0] is None or relation.items[1] is None:
            logging.error(f'Could not create Relation because of missing item information in relation: {relation}')
            raise ValueError(f'Could not create Relation because of missing item information in relation: {relation}')
        uuid_1 = relation.items[0].uuid
        uuid_2 = relation.items[1].uuid
        if uuid_1 == '' or uuid_2 == '':
            logging.error(f'Relation via RestAPI can only be created by using item-uuids, but found: {relation}')
            raise ValueError(f'Relation via RestAPI can only be created by using item-uuids, but found: {relation}')
        req = self.session.post(add_url)
        self.update_csrf_token(req)
        item_url = f'{self.api_endpoint}/core/items'
        headers = self.session.headers
        headers.update({'Content-Type': 'text/uri-list', 'User-Agent': self.req_headers['User-Agent']})
        resp = self.session.post(add_url, f'{item_url}/{uuid_1} \n {item_url}/{uuid_2}', headers=headers)

        if resp.status_code in (201, 200):
            # Success post request
            logging.info(f'Created relationship: {relation}')
            return resp.json()

        raise requests.exceptions.RequestException(f'{resp.status_code}: Could not post relation: \n{relation}\n'
                                                   f'Got headers: {resp.headers}')

    def add_community(self, community: Community | DSpaceObject, create_tree: bool = False) -> Community:
        """
        Creates a new community in the DSpace instance and its owning community if create_tree is True.

        :param community: The collection object to create in DSpace.
        :param create_tree: If the owning communities shall be created as well.
        :return: Returns the newly created Community.
        """
        parent_community = community.parent_community
        if parent_community is not None and parent_community.uuid == '' and create_tree:
            community.parent_community = self.add_community(parent_community, create_tree)
        logging.debug(f'Adding community: {community}')
        return self.add_object(community)

    def add_collection(self, collection: Collection, create_tree: bool = False) -> Collection:
        """
        Creates a new collection in the DSpace instance and its owning communities if create_tree is True.

        :param collection: The collection object to create in DSpace.
        :param create_tree: If the owning communities shall be created as well.
        :return: Returns the newly created Collection.
        """
        community = collection.community
        if community.uuid == '' and create_tree:
            collection.community = self.add_community(community, create_tree)
        logging.debug(f'Adding collection: {collection}')
        return self.add_object(collection)

    def add_item(self, item: Item, create_tree: bool = False) -> Item:
        """
        Adds an item object to DSpace including files and relations. Based on the add_object method.

        :param item: The item to push into DSpace.
        :param create_tree: Creates the owning collections and communities above this item if not yet existing.
        :return: An item object including the new uuid.
        """
        bitstreams = item.contents
        collection_list = item.collections
        if create_tree:
            if len(collection_list) > 0 and collection_list[0].uuid == '':
                col: Collection = self.add_collection(collection_list[0], create_tree)
                collection_list[0] = col
        elif len(collection_list) == 0:
            raise ValueError('Can not push an Item into the restAPI without information about the owning collections.')
        elif len(collection_list) > 0 and collection_list[0].get_identifier() is None:
            raise ValueError('Can not push an Item into the restAPI without a owning collections. Set create_tree to'
                             'True or provide an identifier of the owning collection.')
        else:
            for c in collection_list:
                if c.uuid == '' and c.handle != '':
                    logging.debug(f'Could not find uuid for collection with handle "{c.handle}".'
                                  'Retrieving uuid from api.')
                    c.uuid = self.get_dso(identifier=c.handle).uuid
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
                logging.error(f'Could not find relation in the list: {relation_types}')
                raise e
        for r in relations:
            self.add_relationship(r)
        logging.debug(f'Created item {item}')
        return item

    def move_item(self, item: Item, new_collection: Collection | str):
        """
        Moves an item to a new collection (completely replacing the old one).

        :param item: The item to move.
        :param new_collection: The new collection to put the item. This can eather be a Collection object or a string
            containing the uuid of the collection.
        """
        endpoint = f'core/items/{item.uuid}/owningCollection'
        new_collection = new_collection.uuid if isinstance(new_collection, Collection) else new_collection
        logging.info(f'Moving item with uuid {item.uuid} into new owning collection {new_collection}.')
        self.put_api(endpoint, f'{self.api_endpoint}/core/collections/{new_collection}',
                     content_type='text/uri-list')

    def get_dso(self, uuid: str = '', endpoint: str = '',
                identifier: str = None) -> DSpaceObject | Item | Collection | Community:
        """
        Retrieves a DSpace object from the api based on its uuid and the endpoint information.

        :param uuid: The uuid of the object.
        :param endpoint: The endpoint string. Must be one of ('items', 'collections', 'communities')
        :param identifier: An optional other identifier to retrieve a DSpace Object. Can be used instead of uuid. Must
            be a handle or doi.
        :return: Returns a DSpace object
        """
        if identifier is None:
            if uuid == '' or not isinstance(uuid, str):
                raise ValueError(f'If no other identifier is used, the uuid must be provided. "{uuid}" is not correct.')
            params = {}
            url = f'core/{endpoint}/{uuid}'
            if endpoint not in ('items', 'collections', 'communities'):
                raise ValueError(f"The endpoint '{endpoint}' does not exist. endpoint must be one of"
                                 "('items', 'collections', 'communities')")
        else:
            url = 'pid/find'
            params = {'id': identifier}
        try:
            obj = json_to_object(self.get_api(url, params))
            logging.debug(f'Retrieved DSpaceObject: {obj}')
        except TypeError:
            obj = None
            logging.warning('The object could not be found!')
        return obj

    def get_paginated_objects(self, endpoint: str, object_key: str, query_params: dict = None, page: int = -1,
                              size: int = 20) -> list[dict]:
        """
        Retrieves a paginated list of objects from the remote dspace endpoint and returns them as a list.

        :param endpoint: The endpoint to retrieve the objects from.
        :param object_key: The dict key to get the object list from the json-response. For example "bundles" or
            "bitstreams"
        :param query_params: Additional query parameters to add to the request.
        :param page: The page number to retrieve. Must be set to -1 to retrieve all pages. Default -1.
        :param size: The page size, aka the number of objects per page.
        :return: The list of retrieved objects.
        """
        query = {} if query_params is None else dict(query_params)
        if size > -1:
            query.update({'size': size})
        if page > -1:
            query.update({'page': page})
        endpoint_json = self.get_api(endpoint, params=query)
        if 'discover/search/objects' in endpoint:
            endpoint_json = endpoint_json['_embedded']['searchResult']
        try:
            object_list = endpoint_json["_embedded"][object_key]
        except KeyError as e:
            logging.error(f'Problems with parsing paginated object list. A Key-Error occurred.\n{endpoint_json}')
            raise e
        if page == -1:
            page_info = endpoint_json['page']
            if self.workers == 0:
                for p in range(1, page_info['totalPages']):
                    object_list += self.get_paginated_objects(endpoint, object_key, query, p, size)
            else:
                pool = ThreadPoolExecutor(max_workers=self.workers if self.workers > 0 else None)
                pool_threads = [pool.submit(self.get_paginated_objects, endpoint, object_key, query, p, size) for
                                p in range(1, page_info['totalPages'])]
                pool.shutdown(wait=True)
                for p in pool_threads:
                    object_list += p.result()
        return object_list

    def get_item_bitstreams(self, item_uuid: str) -> list[Bitstream]:
        """
        Retrieves the bitstreams connected to a DSpace Object. And returns them as a list.

        :param item_uuid: The uuid of the item to retrieve the bitstreams from.
        :return: A list of Bitstream objects.
        """
        bitstreams = []
        bundles = self.get_item_bundles(item_uuid, True)

        for b in bundles:
            bitstreams += b.bitstreams
        return bitstreams

    def get_bitstreams_in_bundle(self, bundle: Bundle) -> Bundle:
        """
        Retrieves all bitstreams in a given bundle by the bundle uuid.

        :param bundle: The bundle object to retrieve the bitstreams to.
        :return: The updated bundle object containing the bitstreams associated.
        """
        bitstream_link = f"/core/bundles/{bundle.uuid}/bitstreams"
        logging.debug(f'Retrieving bitstreams for bundle({bundle.name}) with uuid: {bundle.uuid}')
        for o in self.get_paginated_objects(bitstream_link, 'bitstreams'):
            description = o['metadata']['dc.description'][0]['value'] if ('dc.description'
                                                                          in o['metadata'].keys()) else ''
            bitstream = Bitstream(o['name'], o['_links']['content']['href'],
                                  bundle=bundle, uuid=o['uuid'])
            bitstream.add_description(description)
            bundle.add_bitstream(bitstream)
            logging.debug(f'Retrieved bitstreams: {bitstream}')
        logging.debug(f'Retrieved {len(bundle.bitstreams)} bitstreams.')
        return bundle

    def get_item_bundles(self, item_uuid: str, include_bitstreams: bool = True) -> list[Bundle]:
        """
        Retrieves the bundles connected to a DSpaceObject and returns them as list.

        :param item_uuid: The uuid of the item to retrieve the bundles from.
        :param include_bitstreams: Whether bitstreams should be downloaded as well. Default: True
        :return: The list of Bundle objects.
        """
        bundle_json = self.get_paginated_objects(f'/core/items/{item_uuid}/bundles', 'bundles')
        bundles = [Bundle(b['name'],
                          b['metadata']['dc.description'][0]['value'] if 'dc.description' in b['metadata'].keys() else '',
                          b['uuid']) for b in bundle_json]
        if not include_bitstreams:
            return bundles

        return [self.get_bitstreams_in_bundle(b) for b in bundles]

    def get_relations_by_type(self, entity_type: str) -> list[Relation]:
        """
        Parses the REST API and returns a list of relationships, which have the given entity on the left or right side.

        :param entity_type: The entity_type to look for.
        :return: Return s a list of relations.
        """
        add_url = f'/core/relationshiptypes/search/byEntityType'
        params = {'type': entity_type}
        rel_list = []
        relations = self.get_paginated_objects(add_url, 'relationshiptypes', params)
        for r in relations:
            rel_list.append(Relation(r['leftwardType'], relation_type=r['id']))
            rel_list.append(Relation(r['rightwardType'], relation_type=r['id']))
            logging.debug(f'Got relation {r} from RestAPI')
        return rel_list

    def get_item_relationships(self, item_uuid: str) -> list[Relation]:
        """
        Retrieves a list of relationships of DSpace entity from the api.

        :param item_uuid: The uuid of the item to retrieve the relationships for.
        :return: A list of relation objects.
        """
        url = f'/core/items/{item_uuid}/relationships'

        rel_list = self.get_paginated_objects(url, 'relationships')
        relations = []
        for r in rel_list:
            left_item_uuid = r['_links']['leftItem']['href'].split('/')[-1]
            right_item_uuid = r['_links']['rightItem']['href'].split('/')[-1]
            direction = 'leftwardType' if item_uuid == right_item_uuid else 'rightwardType'
            # Retrieve the type information:
            type_req = self.session.get(r['_links']['relationshipType']['href'])
            rel_key = type_req.json()[direction]
            rel_type = type_req.json()['id']
            # Set the correct item order.
            try:
                left_item = self.get_item(left_item_uuid, False)
                right_item = self.get_item(right_item_uuid, False)
                items = (left_item, right_item) if direction == 'rightwardType' else (right_item, left_item)
                relation = Relation(rel_key, items, rel_type)
                relations.append(relation)
                logging.debug(f'Added relation {relation} to Item.')
            except requests.exceptions.RequestException:
                logging.warning(f'Could not retrieve relationship({rel_key}) between {left_item_uuid} and'
                                f' {right_item_uuid}')
        return relations

    def get_item_collections(self, item_uuid: str) -> list[Collection]:
        """
        Retrieves a list of collections from the REST-API based on the uuid of an item. The first will be the owning
        collection.

        :param item_uuid: The uuid of the item.
        """
        url = f'core/items/{item_uuid}/owningCollection'
        get_result = self.get_api(url)
        if get_result is None:
            logging.warning(f'Problems with getting owning Collection for item with uuid "{item_uuid}"')
            return []
        owning_collection = json_to_object(get_result)
        mapped_collections = self.get_paginated_objects(f'core/items/{item_uuid}/mappedCollections',
                                                        'mappedCollections')
        return [owning_collection] + list(filter(lambda x: x is not None,
                                                 [json_to_object(m) for m in mapped_collections]))

    def get_parent_community(self, dso: Collection | Community) -> Community | None:
        """
        Retrieves the parent community of a given collection or Community.

        :param dso: The object to get the parent community from. Must be either Collection or Community
        """
        url = f'core/{"collections" if isinstance(dso, Collection) else "communities"}/{dso.uuid}/parentCommunity'
        try:
            get_result = self.get_api(url)
        except requests.exceptions.RequestException:
            return None
        if get_result is None:
            logging.warning(f'Problems with getting parent communities for DSpaceObject {dso}')
            return None
        owning_community = json_to_object(get_result)
        return owning_community

    def get_item(self, uuid: str = '', get_related: bool = True, get_bitstreams: bool = True,
                 pre_downloaded_item: Item = None, identifier: str = None) -> Item | None:
        """
        Retrieves a DSpace-Item by its uuid (or other identifieres) from the API.

        :param uuid: The uuid of the item to get.
        :param get_related: If true, also retrieves related items from the API.
        :param get_bitstreams: If true, also retrieves bitstreams of the item from the API.
        :param pre_downloaded_item: If a pre downloaded item is provided (aka blank dso), then only additional
            information such as relationships, owning collection, bundles and bitstreams will be provided.
        :param identifier: The identifier of the item to get. Can be used to retrieve items with ids other than uuid.
            Must be doi or handle
        :return: An object of the class Item.
        """
        dso = self.get_dso(uuid, 'items', identifier) if pre_downloaded_item is None else pre_downloaded_item
        if dso is None:
            logging.warning(f'The item with uuid "{uuid}" could not be found.')
            return None
        if get_related:
            dso.relations = self.get_item_relationships(dso.uuid)
        if get_bitstreams:
            dso.bundles = self.get_item_bundles(dso.uuid, True)
            for b in dso.bundles:
                dso.contents += b.bitstreams

        dso.collections = self.get_item_collections(dso.uuid)
        logging.debug(f'Successfully retrieved item {dso} from endpoint.')
        return dso

    def get_community(self, uuid) -> Community | None:
        """
        Retrieves a DSpace-Community object from the API.

        :param uuid: The UUID of the community to get.
        """
        dso = self.get_dso(uuid, 'communities')
        dso: Community
        dso.parent_community = self.get_parent_community(dso)
        logging.debug(f'Successfully retrieved community {dso} from endpoint.')
        return dso

    def get_collection(self, uuid) -> Collection | None:
        """
        Retrieves a DSpace-Community object from the API.

        :param uuid: The UUID of the community to get.
        """
        dso = self.get_dso(uuid, 'collections')
        dso: Collection
        dso.community = self.get_parent_community(dso)
        logging.debug(f'Successfully retrieved collection {dso} from endpoint.')
        return dso

    def get_bundle(self, uuid: str) -> Bundle | None:
        """
        Retrieves a DSpace-Bundel object from the API.

        :param uuid: The UUID of the bundle to get.
        :return: The bundle found.
        """
        bundle_json = self.get_api(f'core/bundles/{uuid}')
        bundle: Bundle = Bundle(bundle_json['name'], uuid=bundle_json['uuid'])
        bundle = self.get_bitstreams_in_bundle(bundle)
        logging.debug(f'Successfully retrieved bundle {bundle} including {len(bundle.bitstreams)} bitstreams from'
                      f'endpoint.')
        return bundle

    def get_objects_in_scope(self, scope_uuid: str, query: dict = None, size: int = 20, full_item: bool = False,
                           get_bitstreams: bool = False) -> list[DSpaceObject]:
        """
        Returns a list of DSpace Objects in a given collection or community. Can be further reduced by query parameter.

        :param scope_uuid: The uuid of the collection to retrieve the items from.
        :param query: Additional query parameters for the request.
        :param size: The number of objects per page. Use -1 to select the default.
        :param full_item: If the full item information should be downloaded (Including relationships, bundles and
            bitstreams. This can be slower due to additional api calls).
        :param get_bitstreams: If true, also the bitstreams of the item will be connected. Not needed if full_item is
            True. Default: False.
        :return: A list of Item objects.
        """
        query_params = {'scope': scope_uuid}
        if query is not None:
            query_params.update(query)
        return self.search_items(query_params, size, full_item, get_bitstreams)

    def search_items(self, query_params: dict = None, size: int = 20, full_item: bool = False,
                     get_bitstreams: bool = False) -> list[DSpaceObject]:
        """
        Search items via rest-API using solr-base query parameters. Uses the endpoint /discover/search/objects. If no
        query_params are provided, the whole repository will be retrieved.

        :param query_params: A dictionary with query parameters to filter the search results.
        :param size: The number of objects to retrieve per page.
        :param full_item: If the full items (including relations and bitstreams) shall be downloaded or not.
            Default false.
        :param get_bitstreams: If true, also the bitstreams of the item will be connected. Not needed if full_item is
            True. Default: False.
        :return: The list of found DSpace objects.
        """
        object_list = self.get_paginated_objects('/discover/search/objects', 'objects', query_params,
                                                 size=size)
        dspace_objects = [json_to_object(obj['_embedded']['indexableObject']) for obj in object_list]
        if not full_item and not get_bitstreams:
            logging.info(f'Found {len(dspace_objects)} DSpace Objects.')
            return dspace_objects

        for o in dspace_objects:
            if o.get_dspace_object_type() == 'Item':
                o: Item
                if full_item:
                    o.collections = self.get_item_collections(o.uuid)
                    o.relations = self.get_item_relationships(o.uuid)
                o.bundles = self.get_item_bundles(o.uuid, True)
            if full_item:
                if o.get_dspace_object_type() == 'Collection':
                    o: Collection
                    o.community = self.get_parent_community(o)
                if o.get_dspace_object_type() == 'Community':
                    o: Community
                    o.parent_community = self.get_parent_community(o)
        logging.info(f'Found {len(dspace_objects)} DSpace Objects.')
        return dspace_objects

    def get_all_items(self, page_size: int = 20, full_item: bool = False,
                      get_bitstreams: bool = False) -> list[DSpaceObject]:
        """
        Retrieves all Items from the REST-API. This method simply refers to the `search_items()` method without using
        query_params, thus getting all items.

        :param page_size: The number of objects to retrieve per page.
        :param full_item: Whether the full_item including related items and bitstreams shall be downloaded.
        :param get_bitstreams: If true, also the bitstreams of the item will be connected. Not needed if full_item is
            True. Default: False.
        :return: A list of all found DSpaceObjects
        """
        return self.search_items(None, page_size, full_item, get_bitstreams)

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
            scopeNote: <scopeNote>, schema: {id: <schema-id>, prefix: <prefix>, namespace: <namespace>}
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

        url = 'core/metadatafields/'
        if field_id > -1:
            url += f'/{field_id}'
            json_get = self.get_api(url)
            return [] if json_get is None else [parse_json_resp(json_get)]

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
            params['page'] = p
            results.append(self.get_api(url, params))
        field_objects = []
        for r in results:
            field_objects += [parse_json_resp(i) for i in r['_embedded']['metadatafields']]
            logging.debug(f'Found metadata field {field_objects[-1]}')
        logging.info(f'Found {len(field_objects)} metadata fields.')
        return field_objects

    def update_metadata(self, metadata: dict[str, (list[dict] | dict[str, dict])], object_uuid: str, obj_type: str,
                        operation: str, position: int = -1) -> DSpaceObject:
        """
        Update a new metadata value information to a DSpace object, identified by its uuid.

        :param metadata: A list of metadata to update as a MetaData object or dict object in the REST form, aka
            {<tag> : [{"value": <value>, "language": <language>...}]}. May also contain position information. For
            "remove"- operation the form must be {<tag>: [{postion: <position>}] | []}
        :param object_uuid: The uuid of the object to add the metadata to.
        :param obj_type: The type of DSpace object. Must be one of item, collection or community
        :param operation: The selected update operation. Must be one off (add, replace, remove).
        :param position: The position of the metadata value to add. Only possible if metadata is of type dict[dict[]]
        :return: The updated DSpace object.
        :raises ValueError: If a not existing objectType is used or wrong operation type.
        """
        if obj_type not in ('item', 'collection', 'community'):
            logging.error(f'Wrong object type information "{obj_type}" must be one of item, collection or community')
            raise ValueError(f'Wrong object type information "{obj_type}" must be one of item, collection or community')
        if operation not in ('add', 'replace', 'remove'):
            logging.error(f'Wrong update operation "{operation}" must be one off (add, replace, remove).')
            raise ValueError(f'Wrong update operation "{operation}" must be one off (add, replace, remove).')

        patch_json = []
        # Form: [{"op": "<operation>",
        #            "path": "/metadata/<tag>",
        #            "value": [{"value": <value>, "language": <language>}]}]

        if operation in ('add', 'replace'):
            for k in metadata.keys():
                values = metadata[k]
                rank = ''
                if isinstance(metadata[k], dict):
                    metadata[k]: dict
                    rank = f'/{metadata[k]["position"]}' if 'position' in metadata[k].keys() else ''
                    rank = f'/{position}' if rank == '' and str(position) != '-1' else rank
                    values = {'value': metadata[k]['value']}
                    if 'language' in metadata[k].keys():
                        values.update({'language': metadata[k]['language']})
                patch_json.append({'op': operation, 'path': f'/metadata/{k}' + rank, 'value': values})
        else:
            for k in metadata.keys():
                rank = [i['position'] for i in metadata[k]]
                if len(rank) > 0:
                    patch_json += [{'op': operation, 'path': f'/metadata/{k}/{r}'} for r in rank]
                else:
                    patch_json.append({'op': operation, 'path': f'/metadata/{k}' +
                                                                (f'/{position}' if str(position) != '-1' else '')})

        url = 'core/' + (f'{obj_type}s' if obj_type in ('item', 'collection') else 'communities')
        json_resp = self.patch_api(f'{url}/{object_uuid}', patch_json)
        return json_to_object(json_resp)

    def add_metadata(self, metadata: MetaData | dict[str, list[dict]], object_uuid: str,
                     obj_type: str, position_end: bool = False) -> DSpaceObject:
        """
        Add a new metadata value information to a DSpace object, identified by its uuid.

        :param metadata: A list of metadata to update as a MetaData object or dict object in the REST form, aka
            {<tag> : [{"value": <value>, "language": <language>...}]}
        :param object_uuid: The uuid of the object to add the metadata to.
        :param obj_type: The type of DSpace object. Must be one of item, collection or community.
        :param position_end: Whether the new metadata field should be placed at the end of the existing metadata.
        :return: The updated DSpace object.
        :raises ValueError: If a not existing objectType is used.
        """

        if isinstance(metadata, MetaData):
            metadata = {key: [dict(v) for v in metadata[key]] for key in metadata.keys()}
        else:
            # Checks if there is only one metadata key with only one value.
            if len(metadata.keys()) == 1 and position_end and len(metadata[list(metadata.keys())[0]]) == 1:
                metadata = {list(metadata.keys())[0]: metadata[list(metadata.keys())[0]][0]}
        return self.update_metadata(metadata, object_uuid, obj_type, 'add',
                                    position='-' if position_end else -1)

    def replace_metadata(self, metadata: MetaData | dict[str, list[dict] | dict], object_uuid: str,
                         obj_type: str, position: int = -1) -> DSpaceObject:
        """
        Add a new metadata value information to a DSpace object, identified by its uuid.

        :param metadata: A list of metadata to update as a MetaData object or dict object in the REST form, aka
            {<tag> : [{"value": <value>, "language": <language>...}]}
        :param object_uuid: The uuid of the object to add the metadata to.
        :param obj_type: The type of DSpace object. Must be one of item, collection or community.
        :param position: The position of the metadata value to replace.
        :return: The updated DSpace object.
        :raises ValueError: If a not existing objectType is used.
        """
        if isinstance(metadata, MetaData):
            metadata: MetaData
            patch_data = {key: [dict(v) for v in metadata[key]] for key in metadata.keys()}
        else:
            metadata: dict[str, list[dict] | dict]
            # Check if position argument is not used correctly
            if len(metadata.keys()) > 1 and str(position) != '-1':
                logging.warning('Could not set same position metadata for more than one metadata tag.')
                raise Warning('Could not set same position metadata for more than one metadata tag.')
            if (len(metadata.keys()) == 1 and isinstance(metadata[list(metadata.keys())[0]], list)
                    and str(position) != '-1'):
                logging.warning('Could not use one position argument for more than one metadata-value.')
                raise Warning('Could not use one position argument for more than one metadata-value.')

            patch_data = {k: (metadata[k][0] if (isinstance(metadata[k], list)
                                                 and len(metadata[k]) == 1) else metadata[k])for k in metadata.keys()}

        return self.update_metadata(patch_data, object_uuid, obj_type, 'replace', position=position)

    # Delete section. Be carefully, when using it!

    def delete_metadata(self, tag: str | list[str], object_uuid: str,
                        obj_type: str, position: int | str = -1) -> DSpaceObject:
        """
        Deletes a specific metadata-field or value of a DSpace Item. Can delete a list of fields as well as only one.

        :param tag: A tag or list of tags wich shall be deleted.
        :param object_uuid: The uuid of the DSpace Item to delete the metadata from.
        :param position: The position of the metadata value to delete. Can only be used, if only one tag is provided.
        :param obj_type: The type of DSpace object. Must be one of item, collection or community.
        :return: The updated DSpace object.
        :raises ValueError: If a not existing objectType is used. Or a position is given, when tag is a list.
        """
        if str(position) != '-1' and isinstance(tag, list):
            raise ValueError('Can not use position parameter if more than one tag is provided.')
        tag = [tag] if not isinstance(tag, list) else tag
        return self.update_metadata({t: [] for t in tag}, object_uuid, obj_type, operation='remove', position=position)

    def delete_bitstream(self, bitstream_uuid: str | list[str]):
        """
        Permanently removes a bitstream of a list of bitstreams from the repository. Handle be carefully when using the
        method, there won't be a confirmation step.

        :param bitstream_uuid: The uuid of the bitstream to delete
        """
        bitstream_uuid = [bitstream_uuid] if isinstance(bitstream_uuid, str) else bitstream_uuid
        patch_call = [{'op': 'remove', 'path': f'/bitstreams/{uuid}'} for uuid in bitstream_uuid]
        self.patch_api('core/bitstreams', patch_call)
        logging.info(f'Successfully deleted bitstream with uuid "{bitstream_uuid}".')

    def delete_bundles(self, bundle_uuid: str | list[str], include_bitstreams: bool = False):
        """
        Permanently removes a bundle or a list of bundles from the repository. Handle carefully when using the method,
        there won't be a confirmation step. Can not delete a bundle with bitstreams still included, unless
        include_bitstreams is set to true.

        :param bundle_uuid: The uuid or list of uuids of the bundles to be deleted.
        :param include_bitstreams: Default: False. WARNING! If this is set to true all bitsreams in the bundle will be
            deleted as well.
        """
        bundles = bundle_uuid if isinstance(bundle_uuid, list) else [bundle_uuid]
        for b in bundles:
            if not include_bitstreams:
                bundle = self.get_bitstreams_in_bundle(Bundle(uuid=b))
                if len(bundle.bitstreams) > 0:
                    logging.error(f'Could not delete bundle with uuid "{b}" because there are still '
                                  f'{len(bundle.bitstreams)} bitstreams.')
                    continue
            self.delete_api(f'core/bundles/{b}')
            logging.info(f'Successfully deleted bundle with uuid "{b}"')
