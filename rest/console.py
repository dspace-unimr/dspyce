from .Rest import RestAPI
from getpass import getpass


def authenticate_to_rest(rest_api: str) -> RestAPI:
    """
    Connect to a given REST-API and ask for username and password via commandline.

    :param rest_api: The url of the REST-API endpoint.
    :return: An object of the class Rest.
    """
    print(f'Establishing connection to the REST-API "{rest_api}":')
    username = input('\tPlease enter your username: ')
    password = getpass('\tPassword: ')
    return RestAPI(rest_api, username, password)
