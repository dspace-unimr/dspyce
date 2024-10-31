from getpass import getpass
import logging
import requests
from .RestAPI import RestAPI


def authenticate_to_rest(rest_api: str, user: str = None, log_level=logging.INFO, log_file: str = None) -> RestAPI:
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
