import requests
from .. import DSpaceObject, Item, Community, Collection, Relation
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
        print(f'Adding object in "{url}" with params ({params}):\n{json_data}')
        resp = self.session.post(url, json=json_data, headers=self.req_headers, params=params)
        if resp.status_code in (201, 200):
            # Success post request
            return resp.json()
        else:
            raise requests.exceptions.RequestException(f'Could not post content: \n{json_data}\nWith params: {params}')

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
            print(f'The authentication as "{self.username}" was successfull')
            return True
        else:
            print('The authentication did not work.')
            return False

    def add_object(self, obj: DSpaceObject) -> DSpaceObject:
        """

        :param obj:
        :return:
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
                    'dc.description': [{'value': bitstream.description}]}, 'bundleName': bundle.name}
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

    def add_relationship(self, item: Item, relation: Relation):
        pass

    def add_item(self, item: Item) -> Item:
        """
        Adds an item object to DSpace including files and relations. Based on the add_object method.

        :param item: The item to push into DSpace.
        :return: An item object including the new uuid.
        """
        bitstreams = item.contents
        relations = item.relations if item.is_entity() else []
        dso = self.add_object(item)
        bundles = {i.name: i for i in [self.add_bundle(b, dso.uuid) for b in item.get_bundles()]}
        for b in bitstreams:
            self.add_bitstream(b, bundles[b.bundle.name])
        item.uuid = dso.uuid
        return item

    def update_metadata(self, obj: DSpaceObject):
        if obj.uuid == '' and obj.handle == '':
            raise ValueError('The object must provide identifier information! Could not find those in ' + str(obj))
        pass
