from tests.helpers import FixtureHTTPClient
import unittest

class SmokeTestCase(unittest.TestCase):

    def __init__(self, x):
        super().__init__(x)
        self.client = FixtureHTTPClient()

    def test_smoke(self):
        unauth_res = self.client.unauth_get('/api/site-map')
        self.assertEqual(unauth_res.status_code, 200)
        auth_res = self.client.auth_get('/api/site-map')
        self.assertEqual(auth_res.status_code, 200)