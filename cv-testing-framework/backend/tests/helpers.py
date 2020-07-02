# Helpers for creating a fixture

import os
import requests

# Allow running the backend tests against any instance of the compiler hub.
BASE_URL = os.getenv('COMPHUB_TEST_BASEURL') or 'http://localhost:8000'

class FixtureHTTPClient:
    """
    An HTTP client for testing against a test instance of our backend.
    Requires the backend to be running at http://localhost:8000/
    """

    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.authSession = requests.Session()
        self.unauthSession = requests.Session()
        self.auth_post('/api/auth/login', {
            "username": "testuser",
            "password": "testpassword"
        })

    def __del__(self):
        self.unauthSession.close()
        self.authSession.close()

    def check_exists(self, url):
        return self.authSession.options(self.base_url + url)

    def unauth_get(self, url):
        return self.unauthSession.get(self.base_url + url)

    def unauth_post(self, url, data):
        return self.unauthSession.post(self.base_url + url, json=data)

    def auth_get(self, url):
        return self.authSession.get(self.base_url + url)

    def auth_post(self, url, data):
        return self.authSession.post(self.base_url + url, json=data)