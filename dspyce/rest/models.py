from concurrent.futures import ThreadPoolExecutor
import json
import logging
from warnings import warn

import requests
import requests.adapters
from requests.exceptions import InvalidJSONError

from dspyce.rest.exceptions import RestObjectNotFoundError


def deprecated(message):
    def decorator(func):
        def wrapper(*args, **kwargs):
            warn(message, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator


@deprecated('The function "object_to_json is deprecated. Call the obj.to_dict() method of the DSpace Object instead."')
def object_to_json(obj: any) -> dict:
    """
    Converts a DSpaceObject class into dict based on a DSpace-Rest format
    :param obj: The object to convert.
    :return: A dictionary in the REST-format.
    """
    return obj.to_dict()


class RestAPI:
    """
    The class RestAPI represents the REST API of a DSpace 7+ backend. It helps to get, push, update or remove Objects,
    Bitstreams, Relations, MetaData and other from a DSpace Instance.
    """
    from dspyce.models import DSpaceObject, Community, Collection, Item
    from dspyce.entities.models import Relation
    from dspyce.bitstreams.models import Bundle, Bitstream
    from dspyce.metadata import MetaData
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
        :raises RestObjectNotFoundError: If the object does not exist in the given endpoint.
        """
        endpoint = endpoint if endpoint[0] != '/' else endpoint[1:]
        url = f'{self.api_endpoint}/{endpoint}'
        req = self.session.get(url, params=params if params is not None else {})
        self.update_csrf_token(req)
        if req.status_code in (204, 201, 200):
            logging.debug(f'Successfully performed GET request to endpoint {endpoint}')
            return req.json()
        if req.status_code == 404:
            logging.error(f'Object behind "{url}" does not exists.')
            logging.error(req.json())
            raise RestObjectNotFoundError(f'The object with url "{url}" could not be found.')
        logging.error(f'Problem with performing GET request to endpoint {endpoint}.')
        logging.error(req)

        raise requests.exceptions.RequestException(f'Could not get item with from endpoint: {url}')

    def post_api(self, url: str, data: dict | list | str, params: dict, content_type: str = 'application/json') -> dict:
        """
        Performs a post action on the RestAPI endpoint.
        """
        req = self.session.post(url)
        self.update_csrf_token(req)
        logging.debug(f'Performing POST request in "{url}" with params({params}):{data}')
        if content_type == 'application/json':
            try:
                resp = self.session.post(url, json=data, headers=self.req_headers, params=params)
            except InvalidJSONError as e:
                logging.error(f'Invalid json format in the query data: {data}')
                raise e
            if resp.status_code in (201, 200):
                # Success post request
                json_resp = resp.json()
                logging.info(f'Successfully added object with uuid: {json_resp["uuid"]}')
                return json_resp
        else:
            headers = self.req_headers.copy()
            headers['Content-Type'] = content_type
            resp = self.session.post(url, data=data, headers=headers, params=params)
            if resp.status_code in (200, 201, 204):
                return {}
        logging.error(f'Could not POST content({content_type}): {data}.\n\tWith params: {params}\n\tOn endpoint: {url}')
        logging.error(f'Statuscode: {resp.status_code}')
        raise requests.exceptions.RequestException(f'\nStatuscode: {resp.status_code}\n'
                                                   f'Could not post content: \n\t{data}'
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

    def delete_api(self, url: str, params: any = None, content_type: str = None, retry: bool = False) -> None:
        """
        Sends a DELETE request to the api.

        :param url: The path in the api.
        :param params: Additional params for the operation.
        :param content_type: The content_type of the data. The default ist self.request.headers['Content-Type']
        :param retry: Use this, if csrf token has to be updated.
        :raise RequestException: If the JSON response doesn't have the status code 200 or 201
        """
        url = f'{self.api_endpoint}/{url}' if self.api_endpoint not in url else url
        logging.debug(f'Performing DELETE request in "{url}" with params({params})')
        params = {} if params is None else params
        headers = self.req_headers
        if content_type != headers['Content-type']:
            headers['Content-type'] = content_type
        resp = self.session.delete(url, params=params, headers=self.req_headers)
        self.update_csrf_token(resp)
        if resp.status_code == 403:
            if retry:
                logging.warning('To many retries updating csrf token.')
            else:
                logging.debug('Retry request wit updated csrf token.')
                return self.delete_api(url, params, content_type, True)
        elif resp.status_code in (204, 200):
            # Success DELETE request
            logging.debug(f'Successfully performed DELETE request on endpoint {url}.')
            return

        logging.error(f'Could not DELETE on endpoint: {url} With params: {params}')
        logging.error(f'Statuscode: {resp.status_code}')
        exception = requests.exceptions.RequestException(f'\nStatuscode: {resp.status_code}\n'
                                                         f'\nWith params: {params}\nOn endpoint:\n\t{url}')
        raise exception

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
        from dspyce.rest.functions import json_to_object
        object_list = self.get_paginated_objects('/discover/search/objects', 'objects', query_params,
                                                 size=size)
        dspace_objects = [json_to_object(obj['_embedded']['indexableObject']) for obj in object_list]
        if not full_item and not get_bitstreams:
            logging.info(f'Found {len(dspace_objects)} DSpace Objects.')
            return dspace_objects

        for o in dspace_objects:
            if o.get_dspace_object_type() == 'Item':
                if full_item:
                    o.collections = self.get_item_collections(o.uuid)
                    o.relations = self.get_item_relationships(o.uuid)
                o.bundles = self.get_item_bundles(o.uuid, True)
            if full_item:
                if o.get_dspace_object_type() == 'Collection':
                    o.community = self.get_parent_community(o)
                if o.get_dspace_object_type() == 'Community':
                    o.parent_community = self.get_parent_community(o)
        logging.info(f'Found {len(dspace_objects)} DSpace Objects.')
        return dspace_objects

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

    def update_metadata(self, metadata: dict[str, (list[dict] | dict[str, dict])], object_uuid: str,
                        obj_type: str, operation: str, position: int = -1) -> DSpaceObject:
        """
        Update a new metadata value information to a DSpace object, identified by its uuid.

        :param metadata: A list of metadata to update as a MetaData object or dict object in the REST form, aka
            {<tag> : [{"value": <value>, "language": <language>...}]}. May also contain position information. For
            "remove"- operation the form must be {<tag>: [{postion: <position>}] | []}. For move this is a dict
            containing the metadata tag and a dict with the 'from' and 'path' values.
        :param object_uuid: The uuid of the object to add the metadata to.
        :param obj_type: The type of DSpace object. Must be one of item, collection or community
        :param operation: The selected update operation. Must be one off (add, replace, remove, move).
        :param position: The position of the metadata value to add. Only possible if metadata is of type dict[dict[]]
        :return: The updated DSpace object.
        :raises ValueError: If a not existing objectType is used or wrong operation type.
        """
        from dspyce.rest.functions import json_to_object
        if obj_type not in self.DSpaceObject.TYPES:
            logging.error(f'Wrong object type information "{obj_type}" must be one of {self.DSpaceObject.TYPES}')
            raise ValueError(f'Wrong object type information "{obj_type}" must be one of {self.DSpaceObject.TYPES}')
        if operation not in ('add', 'replace', 'remove', 'move'):
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
        elif operation == 'move':
            for m in metadata.keys():
                from_pos = metadata[m].get('from')
                path_pos = metadata[m].get('path')
                if from_pos is None or path_pos is None:
                    raise AttributeError('Can not use move operation without dictionary containing from and path values'
                                         ', bot got %s' % str(metadata[m]))
                patch_json.append({
                    'op': 'move',
                    'from': f'/metadata/{m}/{from_pos}',
                    'path': f'/metadata/{m}/{path_pos}',
                })
        else:
            for k in metadata.keys():
                rank = [i['position'] for i in metadata[k]]
                if len(rank) > 0:
                    patch_json += [{'op': operation, 'path': f'/metadata/{k}/{r}'} for r in rank]
                else:
                    patch_json.append({'op': operation, 'path': f'/metadata/{k}' +
                                                                (f'/{position}' if str(position) != '-1' else '')})

        url = 'core/' + (f'{obj_type}s' if obj_type != 'community' else 'communities')
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

        if isinstance(metadata, self.MetaData):
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
        if isinstance(metadata, self.MetaData):
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

    def move_metadata(self, tag: str, current_position: int, target_position: int, object_uuid: str,
                       obj_type: str):
        """
        Reorders metadata fields of the given metadata tag.
        :param tag: The tag of the field, which should be reordered.
        :param current_position: The current position of the metadata field.
        :param target_position: The target position of the metadata field.
        :param object_uuid: The uuid of the DSpace Object to work with.
        :param obj_type: The DSpace obj type.
        :return: The updated DSpace object.
        :raises ValueError: If a not existing objectType is used.
        """
        update_dict = { tag: {
            'from': current_position,
            'path': target_position,
        }}
        return self.update_metadata(update_dict, object_uuid, obj_type, 'move')


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

    def delete_collection(self, collection: Collection, all_items: bool = False):
        """
        Deletes the given collection from the rest_api. Raises an error, if the collection still includes items and
        all_items is set to false.
        :param collection: The collection to delete.
        :param all_items: Whether to delete all items in the collection as well.
        :raises AttributeError: If collection still includes items and all_items is set to false.
        """
        def delete_item_owned(it, coll):
            """Delete the item, if owned by the given collection."""
            if not isinstance(it, self.Item):
                return
            it.get_collections_from_rest(self)
            cols = it.collections
            if cols[0].uuid == coll.uuid:
                it.delete(self)

        items = self.get_objects_in_scope(collection.uuid)
        if not all_items and len(items) > 0:
            raise AttributeError(f'Collection {collection.uuid} has {len(items)} items and all_items is set to False.')
        elif len(items) > 0:
            if self.workers > 1:
                with ThreadPoolExecutor(max_workers=self.workers) as pool:
                    pool_threads = [pool.submit(delete_item_owned, i, collection) for i in items]
                for p in pool_threads:
                    p.result()
            else:
                for i in items:
                    delete_item_owned(i, collection)
            logging.info('Successfully deleted %i items from the collection.' % len(items))
        self.delete_api(f'core/collections/{collection.uuid}')
        logging.info('Successfully deleted collection with uuid "%s".' % collection.uuid)

    def delete_community(self, community: Community, all_objects: bool = False):
        """
        Deletes the given community from the rest_api. Raises an error, if the community still includes items or
        collections and all_objects is set to false.
        :param community: The community to delete.
        :param all_objects: Whether to delete all items and collections in the community as well.
        :raises AttributeError: If community still includes items or collections and all_objects is set to false.
        """
        sub_communities = community.get_subcommunities_from_rest(self, False)
        sub_collections = community.get_subcollections_from_rest(self, False)
        sub_objs = len(sub_communities) + len(sub_collections)
        if not all_objects and sub_objs > 0:
            raise AttributeError(f'Community {community.uuid} has {sub_objs} objects and all_objects is set to False.')
        else:
            for c in sub_collections:
                self.delete_collection(c, all_objects)
            for c in sub_communities:
                self.delete_community(c, all_objects)
            logging.info('Successfully deleted %i objects from the community.' % sub_objs)
        self.delete_api(f'core/communities/{community.uuid}')
        logging.info('Successfully deleted community with uuid "%s".' % community.uuid)

    @deprecated(
        'The method "add_object" is deprecated. Call the to_rest() method of the DSpaceObject class '
        'instead.'
    )
    def add_object(self, obj: DSpaceObject) -> DSpaceObject | Collection | Item | Community:
        """
        Creates a new object in the DSpace Instance.

        :param obj: The object to create.
        :return: The newly created object.
        """
        obj.to_rest(self)
        return obj

    @deprecated(
        'The method "add_bundle" is deprecated. Call the to_rest() method of the Bundle class instead.'
    )
    def add_bundle(self, bundle: Bundle, item_uuid: str, add_bitstreams: bool = True) -> Bundle | None:
        """
        Creates a new bundle based on a given bundle Object in DSpace and returns the created object.
        :param bundle: The bundle object to create.
        :param item_uuid: The uuid_of the item to create the bundle for.
        :param add_bitstreams: Whether all bitstreams appended to this bundle should be added.
        :return: The newly created object returned from DSpace.
        """
        bundle.to_rest(self, item_uuid, add_bitstreams)
        return bundle

    @deprecated(
        'The method "add_bitstream" is deprecated. Call the to_rest() method of the Bitstream class instead.'
    )
    def add_bitstream(self, bitstream: Bitstream, bundle: Bundle) -> str:
        """
        Creates a new bitstream in a given dspace bundle.
        :param bitstream: The bitstream to upload.
        :param bundle: The bundle to upload the item in.
        :return: The uuid of the newly created bitstream.
        """
        bitstream.bundle = bundle
        bitstream.to_rest(self)
        return bitstream.uuid

    @deprecated(
        'The method "add_relationship" is deprecated. Call the to_rest() method of the Relation class instead.'
    )
    def add_relationship(self, relation: Relation) -> dict:
        """
        Creates a new relationship between to items based on the information in the Relation object.

        :param relation: The relation to create.
        """
        relation.to_rest(self)
        return {}

    @deprecated(
        'The method "add_community" is deprecated. Call the to_rest() method of the Community class instead. If you '
        'want to create all parent objects as well, run add_parent_communities_to_rest first.'
    )
    def add_community(self, community: Community | DSpaceObject, create_tree: bool = False) -> Community:
        """
        Creates a new community in the DSpace instance and its owning community if create_tree is True.

        :param community: The collection object to create in DSpace.
        :param create_tree: If the owning communities shall be created as well.
        :return: Returns the newly created Community.
        """
        if create_tree:
            community.add_parent_communities_to_rest(self)
        community.to_rest(self)
        return community

    @deprecated(
        'The method "add_collection" is deprecated. Call the to_rest() method of the Collection class instead. If you '
        'want to create all parent objects as well, run add_parent_communities_to_rest first.'
    )
    def add_collection(self, collection: Collection, create_tree: bool = False) -> Collection:
        """
        Creates a new collection in the DSpace instance and its owning communities if create_tree is True.

        :param collection: The collection object to create in DSpace.
        :param create_tree: If the owning communities shall be created as well.
        :return: Returns the newly created Collection.
        """
        if create_tree:
            collection.add_parent_communities_to_rest(self)
        collection.to_rest(self)
        return collection

    @deprecated(
        'The method "add_item" is deprecated. Call the to_rest() method of the Item class instead. If you '
        'want to create all parent objects as well, run add_parent_collections_to_rest first.'
    )
    def add_item(self, item: Item, create_tree: bool = False) -> Item:
        """
        Adds an item object to DSpace including files and relations. Based on the add_object method.

        :param item: The item to push into DSpace.
        :param create_tree: Creates the owning collections and communities above this item if not yet existing.
        :return: An item object including the new uuid.
        """
        if create_tree:
            item.add_parent_collections_to_rest(self)
        item.to_rest(self)
        return item

    @deprecated(
        'The method "add_mapped_collections" is deprecated. Call the add_to_mapped_collections() method of the Item '
        'Object instead.'
    )
    def add_mapped_collections(self, item: Item, collections: list[Collection]):
        """
        Add new mapped collections between item and collections. Changes the collection list of the given item in-place.
        :param item: The item to add mapped collection to.
        :param collections: The collections to map the item to.
        """
        item.collections = [item.collections[0]] + collections
        item.add_to_mapped_collections(self)

    @deprecated(
        'The method "move_item" is deprecated. Call the Item.move_item() method of the Item class instead.'
    )
    def move_item(self, item: Item, new_collection: Collection | str):
        """
        Moves an item to a new collection (completely replacing the old one).

        :param item: The item to move.
        :param new_collection: The new collection to put the item. This can eather be a Collection object or a string
            containing the uuid of the collection.
        """
        new_collection = self.Collection(new_collection) if isinstance(new_collection, str) else new_collection
        item.move_item(self, new_collection)

    @deprecated(
        'The method "get_dso" is deprecated. Call the DSpaceObject.get_from_rest() method of the DSpace Object instead.'
    )
    def get_dso(self, uuid: str = '', endpoint: str = '',
                identifier: str = None) -> DSpaceObject | Item | Collection | Community | Bitstream | Bundle:
        """
        Retrieves a DSpace object from the api based on its uuid and the endpoint information.

        :param uuid: The uuid of the object.
        :param endpoint: The endpoint string. Must be one of ('items', 'collections', 'communities', 'bitstreams',
            'bundles')
        :param identifier: An optional other identifier to retrieve a DSpace Object. Can be used instead of uuid. Must
            be a handle or doi.
        :return: Returns a DSpace object
        """
        return self.DSpaceObject.get_from_rest(self, uuid, endpoint, identifier)

    @deprecated(
        'The method "get_item_bitstreams" is deprecated. Call the get_bundles_from_rest() method of the Item class '
        'instead and set include_bitstreams to True, then use the get_bitsreams() method of the item.'
    )
    def get_item_bitstreams(self, item_uuid: str) -> list[Bitstream]:
        """
        Retrieves the bitstreams connected to a DSpace Object. And returns them as a list.

        :param item_uuid: The uuid of the item to retrieve the bitstreams from.
        :return: A list of Bitstream objects.
        """
        item = self.Item(item_uuid)
        item.get_bundles_from_rest(self)
        return item.get_bitstreams()

    @deprecated(
        'The method "get_bitstreams_in_bundle" is deprecated. Call the get_bitstreams_from_rest() method of the'
        'Bundle Object instead.'
    )
    def get_bitstreams_in_bundle(self, bundle: Bundle) -> Bundle:
        """
        Retrieves all bitstreams in a given bundle by the bundle uuid.

        :param bundle: The bundle object to retrieve the bitstreams to.
        :return: The updated bundle object containing the bitstreams associated.
        """
        bundle.get_bitstreams_from_rest(self)
        return bundle

    @deprecated(
        'The method "get_item_bundles" is deprecated. Call the get_bundles_from_rest() method of the'
        'Item Object instead.'
    )
    def get_item_bundles(self, item_uuid: str, include_bitstreams: bool = True) -> list[Bundle]:
        """
        Retrieves the bundles connected to a DSpaceObject and returns them as list.

        :param item_uuid: The uuid of the item to retrieve the bundles from.
        :param include_bitstreams: Whether bitstreams should be downloaded as well. Default: True
        :return: The list of Bundle objects.
        """
        item = self.Item(item_uuid)
        item.get_bundles_from_rest(self, include_bitstreams)
        return item.bundles

    @deprecated(
        'The method "get_relations_by_type" is deprecated. Call the get_by_type_from_rest() method of the'
        'Relation Object instead.'
    )
    def get_relations_by_type(self, entity_type: str) -> list[Relation]:
        """
        Parses the REST API and returns a list of relationships, which have the given entity on the left or right side.

        :param entity_type: The entity_type to look for.
        :return: Return s a list of relations.
        """
        return self.Relation.get_by_type_from_rest(self, entity_type)

    @deprecated(
        'The method "get_item_relationships" is deprecated. Call the get_relations_from_rest() method of the Item Object'
        ' instead.'
    )
    def get_item_relationships(self, item_uuid: str) -> list[Relation]:
        """
        Retrieves a list of relationships of DSpace entity from the api.

        :param item_uuid: The uuid of the item to retrieve the relationships for.
        :return: A list of relation objects.
        """
        item = self.Item(item_uuid)
        item.get_relations_from_rest(self)
        return item.relations

    @deprecated(
        'The method "get_item_collections" is deprecated. Call the get_collections_from_rest() method of the Item Object'
        ' instead.'
    )
    def get_item_collections(self, item_uuid: str) -> list[Collection]:
        """
        Retrieves a list of collections from the REST-API based on the uuid of an item. The first will be the owning
        collection.

        :param item_uuid: The uuid of the item.
        """
        item = self.Item(item_uuid)
        item.get_collections_from_rest(self)
        return item.collections

    @deprecated(
        'The method "get_parent_community" is deprecated. Call the get_parent_community_from_rest() method of the '
        'Community or collection Object instead.'
    )
    def get_parent_community(self, dso: Collection | Community) -> Community | None:
        """
        Retrieves the parent community of a given collection or Community.

        :param dso: The object to get the parent community from. Must be either Collection or Community
        """
        dso.get_parent_community_from_rest(self)
        if isinstance(dso, self.Community):
            return dso.parent_community
        elif isinstance(dso, self.Collection):
            return dso.community

        return None

    @deprecated(
        'The method "get_item" is deprecated. Call the Item.get_from_rest() method of the Item Object  instead.'
    )
    def get_item(self, uuid: str = '', get_related: bool = True, get_bitstreams: bool = True,
                 pre_downloaded_item: Item = None, identifier: str = None) -> Item | None:
        """
        Retrieves a DSpace-Item by its uuid (or other identifiers) from the API.

        :param uuid: The uuid of the item to get.
        :param get_related: If true, also retrieves related items from the API.
        :param get_bitstreams: If true, also retrieves bitstreams of the item from the API.
        :param pre_downloaded_item: If a pre downloaded item is provided (aka blank dso), then only additional
            information such as relationships, owning collection, bundles and bitstreams will be provided.
        :param identifier: The identifier of the item to get. Can be used to retrieve items with ids other than uuid.
            Must be doi or handle
        :return: An object of the class Item.
        """
        return self.Item.get_from_rest(self, uuid, 'item', identifier)

    @deprecated(
        'The method "get_community" is deprecated. Call the Community.get_from_rest() method of the Community Object '
        'instead.'
    )
    def get_community(self, uuid) -> Community | None:
        """
        Retrieves a DSpace-Community object from the API.

        :param uuid: The UUID of the community to get.
        """
        return self.Community.get_from_rest(self, uuid)

    @deprecated(
        'The method "get_collection" is deprecated. Call the Collection.get_from_rest() method of the Collection Object'
        ' instead.'
    )
    def get_collection(self, uuid) -> Collection | None:
        """
        Retrieves a DSpace-Community object from the API.

        :param uuid: The UUID of the community to get.
        """
        return self.Collection.get_from_rest(self, uuid)

    @deprecated(
        'The method "get_bundle" is deprecated. Call the Bundle.get_from_rest() method of the Bundle Object instead.'
    )
    def get_bundle(self, uuid: str) -> Bundle | None:
        """
        Retrieves a DSpace-Bundle object from the API.
        :param uuid: The UUID of the bundle to get.
        :return: The bundle found.
        """
        return self.Bundle.get_from_rest(self, uuid)

    @deprecated(
        'The method "get_bitstream" is deprecated. Call the Bitstream.get_from_rest() method of the Bitsream Object '
        'instead.'
    )
    def get_bitstream(self, uuid: str) -> Bitstream | None:
        """
        Retrieves a DSpace bitstream from the API.
        :param uuid: The UUID of the bitstream to get.
        :return: The bitstream found.
        """
        return self.Bitstream.get_from_rest(self, uuid)

    @deprecated(
        'The method "get_bundle_for_bitstream" is deprecated. Call the get_bundle_from_rest() method of the Bitstream '
        'Object instead.'
    )
    def get_bundle_for_bitstream(self, bitstream: Bitstream) -> Bundle:
        """
        Retrieves the bundle of a given bitstream.
        :param bitstream: The bitstream to retrieve the bundle for.
        """
        bitstream.get_bundle_from_rest(self)
        return bitstream.bundle

    @deprecated(
        'The method "get_subcommunities" is deprecated. Call the get_subcommunities_from_rest() method of the Community '
        'Object instead.'
    )
    def get_subcommunities(self, community: Community) -> list[Community]:
        """
        Returns all sub communities from a given community.
        :param community: The community to retrieve sub communities from.
        :return: A list of sub communities
        """
        return community.get_subcommunities_from_rest(self, False)

    @deprecated(
        'The method "get_subcollections" is deprecated. Call the get_subcollections_from_rest() method of the Community '
        'Object instead.'
    )
    def get_subcollections(self, community: Community) -> list[Collection]:
        """
        Returns all sub collections from a given community.
        :param community: The community to retrieve sub collections from.
        :return: A list of sub collections
        """
        return community.get_subcollections_from_rest(self, False)

    @deprecated(
        'The method "delete_bitstream" is deprecated. Call the delete() method of the Bitstream Object instead.'
    )
    def delete_bitstream(self, bitstream_uuid: str | list[str]):
        """
        Permanently removes a bitstream of a list of bitstreams from the repository. Handle be carefully when using the
        method, there won't be a confirmation step.

        :param bitstream_uuid: The uuid of the bitstream to delete
        """
        bitstream_uuid = [bitstream_uuid] if isinstance(bitstream_uuid, str) else bitstream_uuid
        for b in bitstream_uuid:
            self.Bitstream.get_from_rest(self, b).delete(self)

    @deprecated(
        'The method "delete_bundles" is deprecated. Call the delete() method of the Bundle Object instead.'
    )
    def delete_bundles(self, bundle_uuid: str | list[str], include_bitstreams: bool = False):
        """
        Permanently removes a bundle or a list of bundles from the repository. Handle carefully when using the method,
        there won't be a confirmation step. Can not delete a bundle with bitstreams still included, unless
        include_bitstreams is set to true.

        :param bundle_uuid: The uuid or list of uuids of the bundles to be deleted.
        :param include_bitstreams: Default: False. WARNING! If this is set to true all bitsreams in the bundle will be
            deleted as well.
        """
        bundle_uuid = [bundle_uuid] if isinstance(bundle_uuid, str) else bundle_uuid
        for b in bundle_uuid:
            self.Bundle.get_from_rest(self, b).delete(self, include_bitstreams)

    @deprecated(
        'The method "remove_mapped_collection" is deprecated. Call the remove_collection_mapping() method of the Item '
        'Object instead.'
    )
    def remove_mapped_collection(self, item: Item, collection: Collection | str):
        """
        Removes the mapped collection of a given Item.
        :param item: The item to remove mapped collection from.
        :param collection: The mapped collection to remove. Can be either a collection object or the uuid of the
        collection.
        """
        collection = self.Collection(collection) if isinstance(collection, str) else collection
        item.remove_collection_mapping(self, collection)

    @deprecated(
        'The method "delete_item" is deprecated. Call the delete() method of the Item Object instead.'
    )
    def delete_item(self, item: Item, copy_virtual_metadata: bool = False,
                    by_relationships: Relation | list[Relation] = None):
        """
        Deletes an item from the rest API by using its uuid. If you delete an item, you can request to transform
        possible virtual metadata fields for related items to real metadata fields. If you want to only transform
        virtual metadata fields of specific relations, you can add those relations.
        :param item: The item to delete.
        :param copy_virtual_metadata: Whether to copy virtual metadata of related items. Default: False.
        :param by_relationships: Relationships to copy the metadata for. If none provided and `copy_virtual_metadata` is
            True, all metadata will be copied.
        """
        item.delete(self, copy_virtual_metadata, by_relationships)
