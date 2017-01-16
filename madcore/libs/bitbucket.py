from __future__ import print_function, unicode_literals

import json

import requests
import requests.exceptions

API_BASE_URL = 'https://api.bitbucket.org/2.0/{api}'
DEFAULT_TIMEOUT = 10


class Error(Exception):
    pass


class AuthError(Error):
    pass


class Response(object):
    def __init__(self, body):
        self.raw = body
        self.body = json.loads(body)
        self.successful = True  # self.body['ok']
        self.error = ''  # self.body.get('error')


class BaseAPI(object):
    def __init__(self, username, password, timeout=DEFAULT_TIMEOUT):
        self.username = username
        self.password = password
        self.timeout = timeout

    def _request(self, method, api, **kwargs):
        if self.username and self.password:
            kwargs.setdefault('auth', (self.username, self.password))

        response = method(API_BASE_URL.format(api=api),
                          timeout=self.timeout,
                          **kwargs)

        response.raise_for_status()

        response = Response(response.text)
        if not response.successful:
            raise Error(response.error)

        return response

    def get(self, api, **kwargs):
        return self._request(requests.get, api, **kwargs)

    def post(self, api, **kwargs):
        return self._request(requests.post, api, **kwargs)


class Auth(BaseAPI):
    def check_auth(self):
        try:
            return self.get('user')
        except requests.exceptions.RequestException as req_error:
            raise AuthError(req_error)


class Teams(BaseAPI):
    def get_teams(self, role='member'):
        return self.get('teams', params={'role': role})

    def get_teams_username(self):
        teams = self.get_teams().body

        return [team['username'] for team in teams['values']]


class User(BaseAPI):
    def user_emails(self):
        return self.get('user/emails')

    def get_primary_email(self):
        for item in self.user_emails().body['values']:
            if item['is_primary']:
                return item['email']


class Bitbucket(object):
    def __init__(self, username, password, timeout=DEFAULT_TIMEOUT):
        self.auth = Auth(username, password, timeout=timeout)
        self.teams = Teams(username, password, timeout=timeout)
        self.user = User(username, password, timeout=timeout)
