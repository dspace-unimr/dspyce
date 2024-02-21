from getpass import getpass
from .RestAPI import RestAPI
import requests


def authenticate_to_rest(rest_api: str) -> RestAPI:
    """
    Connect to a given REST-API and ask for username and password via commandline.

    :param rest_api: The url of the REST-API endpoint.
    :return: An object of the class Rest.
    """
    print(f'Establishing connection to the REST-API "{rest_api}":')
    authentication = False
    rest_server = None
    while not authentication:
        username = input('\tPlease enter your username: ')
        password = getpass('\tPassword: ')
        try:
            rest_server = RestAPI(rest_api, username, password)
        except requests.exceptions.JSONDecodeError:
            print(f'Did not found the api-Endpoint. Are you sure, that {rest_api} is the correct address and the API is'
                  'reachable?')
        authentication = rest_server.authenticated
        if not authentication:
            print('Wrong username or password! Please try again.')
    return rest_server
