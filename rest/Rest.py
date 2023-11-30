import requests


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

