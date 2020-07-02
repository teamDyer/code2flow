from tests.helpers import FixtureHTTPClient
import unittest

class ResultsTestCase(unittest.TestCase):

    def __init__(self, x):
        super().__init__(x)
        self.client = FixtureHTTPClient()

    def test_smoke(self):
        unauth_res = self.client.unauth_get('/api/results/testname/vrl/apics/100')
        self.assertEqual(unauth_res.status_code, 200)
        unauth_res = self.client.auth_get('/api/results/testname/vrl/apics/100')
        self.assertEqual(unauth_res.status_code, 200)

    def test_testname(self):
        unauth_res = self.client.unauth_get('/api/results/testname/vrl/apics/100')
        self.assertEqual(unauth_res.status_code, 200)
        body = unauth_res.json()
        self.assertTrue(isinstance(body, list))
        self.assertGreaterEqual(100, len(body))

    def test_testinfo(self):
        res = self.client.unauth_get('/api/results/testinfo/vrl/apics')
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(isinstance(body, list))
        self.assertEqual(1, len(body))
        for el in body:
            self.assertIn('id', el)
            self.assertIn('name', el)
            self.assertIn('system', el)

    def test_all_tests(self):
        res = self.client.unauth_get('/api/results/all-tests/vrl')
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(isinstance(body, list))
        for el in body:
            self.assertIn('id', el)
            self.assertIn('name', el)
            self.assertIn('system', el)

    def test_one_results(self):
        res = self.client.unauth_get('/api/results/one/vrl/apics/282090')
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(isinstance(body, dict))

    def test_job_results(self):
        res = self.client.unauth_get('/api/results/job/vrl/apics/original_id/464202007')
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(isinstance(body, dict))

    def test_push_results(self):
        entry = {
            'changelist': '12346578',
            'score': 200,
            'arch': 'sm70'
        }
        res = self.client.unauth_post('/api/results/push/ccv/ccv_push_test', entry)
        self.assertEqual(200, res.status_code)
        body = res.json()
        self.assertIn('id', body)
        rowid = body['id']
        res2 = self.client.unauth_get('/api/results/one/ccv/ccv_push_test/' + str(rowid))
        self.assertEqual(res2.status_code, 200)
        entry['id'] = rowid
        self.assertDictEqual({'blob': {}, **entry}, res2.json())

    def test_push_results2(self):
        entry = {
            'changelist': '12346578',
            'score': 200
        }
        res = self.client.unauth_post('/api/results/push/ccv/ccv_push_test2', entry)
        self.assertEqual(200, res.status_code)
        body = res.json()
        self.assertIn('id', body)
        rowid = body['id']
        res2 = self.client.unauth_get('/api/results/one/ccv/ccv_push_test2/' + str(rowid))
        self.assertEqual(res2.status_code, 200)
        entry['id'] = rowid
        self.assertDictEqual(entry, res2.json())
