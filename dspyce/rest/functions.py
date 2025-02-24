from getpass import getpass
import logging
import requests


def authenticate_to_rest(rest_api: str, user: str = None, log_level=logging.INFO, log_file: str = None):
    """
    Connect to a given REST-API and ask for username and password via commandline.

    :param rest_api: The url of the REST-API endpoint.
    :param user: A username, if already known. If None, the username will be retrieved from input().
    :param log_level: The log_level used for Logging. Must be string or integer. The strings must be one of
        the following: DEBUG, INFO, WARNING, ERROR, CRITICAL. Default is INFO.
    :param log_file: A possible name and path of the log file. If None provided, all output will be logged to the
        console.
    :return: An object of the class Rest.
    """
    from dspyce.rest.models import RestAPI
    print(
        f'Establishing connection to the REST-API "{rest_api}"' + (f' with user "{user}":' if user is not None else ':')
    )
    authentication = False
    rest_server = None
    while not authentication:
        username = input('\tPlease enter your username: ') if user is None else user
        password = getpass('\tPassword: ')
        try:
            rest_server = RestAPI(rest_api, username, password, log_level, log_file)
        except requests.exceptions.JSONDecodeError:
            print(f'Did not found the api-Endpoint. Are you sure, that {rest_api} is the correct address and the API is'
                  'reachable?')
        authentication = rest_server.authenticated
        if not authentication:
            print('Wrong username or password! Please try again.')
    return rest_server


def json_to_object(json_content: dict):
    from dspyce.models import DSpaceObject, Community, Collection, Item
    from dspyce.bitstreams.models import Bundle, Bitstream
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
    _links = json_content['_links']
    if json_content is None:
        return None
    match doc_type:
        case 'community':
            obj = Community(uuid, handle=handle, name=name)
        case 'collection':
            obj = Collection(uuid, handle=handle, name=name)
        case 'item':
            obj = Item(uuid, handle=handle, name=name)
            if 'inArchive' in json_content.keys():
                obj.inArchive = str(json_content['inArchive']).lower() == 'true'
            if 'discoverable' in json_content.keys():
                obj.discoverable = str(json_content['discoverable']).lower() == 'true'
            if 'withdrawn' in json_content.keys():
                obj.withdrawn = str(json_content['withdrawn']).lower() == 'true'
        case 'bitstream':
            href = _links['content'].get('href') if 'content' in _links else None
            obj = Bitstream('', href, None, uuid, False, json_content.get('sizeBytes'),
                            json_content.get('checkSum').get('value'))
            obj.name = name # Set here to avoid duplicate 'dc.title'
        case 'bundle':
            obj = Bundle('', '', uuid)
            obj.name = name # Set here to avoid duplicate 'dc.title'
        case _:
            obj = DSpaceObject(uuid, handle, name)
    for m in metadata.keys():
        for v in metadata[m]:
            obj.add_metadata(
                tag=m, value=v['value'], language=v.get('language'), authority=v.get('authority'),
                confidence=v.get('confidence')
            )
    return obj