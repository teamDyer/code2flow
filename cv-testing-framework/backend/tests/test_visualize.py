from tests.helpers import FixtureHTTPClient
import unittest

class VisualizeTestCase(unittest.TestCase):

    def __init__(self, x):
        super().__init__(x)
        self.client = FixtureHTTPClient()

    def test_existence(self):
        res = self.client.check_exists('/api/visualize/visualizations/vrl/apics')
        self.assertEqual(res.status_code, 200)
        res = self.client.check_exists('/api/visualize/available-queries/vrl/apics')
        self.assertEqual(res.status_code, 200)
        res = self.client.check_exists('/api/visualize/vrl/apics/simple')
        self.assertEqual(res.status_code, 200)
        res = self.client.check_exists('/api/visualize/vrl/apics/simple/params')
        self.assertEqual(res.status_code, 200)

    def test_unauth(self):
        res = self.client.unauth_get('/api/visualize/visualizations/vrl/apics')
        self.assertEqual(res.status_code, 200)
        res = self.client.unauth_get('/api/visualize/available-queries/vrl/apics')
        self.assertEqual(res.status_code, 200)
        res = self.client.unauth_get('/api/visualize/vrl/apics/simple/params')
        self.assertEqual(res.status_code, 200)
        res = self.client.unauth_get('/api/visualize/vrl/apics/simple')
        self.assertEqual(res.status_code, 200)

    def test_available_queries(self):
        res = self.client.unauth_get('/api/visualize/available-queries/vrl/apics')
        body = res.json()
        self.assertTrue(isinstance(body, list))
        for el in body:
            self.assertTrue(isinstance(el, dict))
            self.assertIn('query', el)
        self.assertEqual(res.status_code, 200)

    def test_params(self):
        res = self.client.unauth_get('/api/visualize/vrl/apics/apic/params')
        body = res.json()
        self.assertIn('params', body)
        self.assertTrue(isinstance(body['params'], list))
        for el in body['params']:
            self.assertTrue(isinstance(el, dict))
            self.assertIn('type', el)
        self.assertEqual(res.status_code, 200)

    def test_results(self):
        res = self.client.unauth_get('/api/visualize/vrl/apics/apic?limit=40&branch=gpu_drv_module_compiler')
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(isinstance(body, dict))
        self.assertIn('data', body)
        data = body['data']
        self.assertEqual(len(data), 40)
        for el in data:
            self.assertIn('branch', el)
            self.assertEqual(el['branch'], 'gpu_drv_module_compiler')

    def test_not_exist(self):
        res = self.client.unauth_get('/api/visualize/vrl/apics/apikollo?limit=40&branch=gpu_drv_module_compiler')
        self.assertEqual(res.status_code, 400)
        res = self.client.unauth_get('/api/visualize/brl/apics/apic?limit=40&branch=gpu_drv_module_compiler')
        self.assertEqual(res.status_code, 400)
        res = self.client.unauth_get('/api/visualize/vrl/bapics/apic?limit=40&branch=gpu_drv_module_compiler')
        self.assertEqual(res.status_code, 400)

    def test_apic_query(self):
        res = self.client.unauth_get('/api/visualize/vrl/apics/apic?limit=31&subtest=3dmark_Dandia_GT1_2560x1600_1xAA_16xAF_30s&gpu=gm107')
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(isinstance(body, dict))
        self.assertIn('data', body)
        data = body['data']
        self.assertGreaterEqual(31, len(data))
        for el in data:
            self.assertIn('x', el)
            self.assertIn('y', el)
            self.assertIn('label', el)
            self.assertIn('machine', el)
            self.assertIn('branch', el)
            self.assertIn('changelist', el)
            self.assertIn('gpu', el)
            self.assertEqual(el['gpu'], 'gm107')

    def test_apic_query2(self):
        # Invalid limit
        res = self.client.unauth_get('/api/visualize/vrl/apics/apic?limit=-1&subtest=3dmark_Dandia_GT1_2560x1600_1xAA_16xAF_30s&gpu=gm107')
        self.assertEqual(res.status_code, 400)

    def test_apic_query3(self):
        # Ignore extra parameters
        res = self.client.unauth_get('/api/visualize/vrl/apics/apic?extra=hi&limit=31&subtest=3dmark_Dandia_GT1_2560x1600_1xAA_16xAF_30s&gpu=gm107')
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(isinstance(body, dict))
        self.assertIn('data', body)
        data = body['data']
        self.assertGreaterEqual(31, len(data))
        for el in data:
            self.assertIn('x', el)
            self.assertIn('y', el)
            self.assertIn('label', el)
            self.assertIn('machine', el)
            self.assertIn('branch', el)
            self.assertIn('changelist', el)
            self.assertIn('gpu', el)
            self.assertEqual(el['gpu'], 'gm107')

    def test_sql_query(self):
        res = self.client.unauth_get('/api/visualize/vrl/apics/sql?sql=select%20*%20from%20$table%20limit%20100')
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(isinstance(body, dict))
        self.assertIn('data', body)
        data = body['data']
        self.assertGreaterEqual(100, len(data))
        for el in data:
            self.assertIn('machine', el)
            self.assertIn('branch', el)
            self.assertIn('changelist', el)
            self.assertIn('gpu', el)

    def test_sql_query2(self):
        # no required sql parameter
        res = self.client.unauth_get('/api/visualize/vrl/apics/sql')
        self.assertEqual(res.status_code, 400)

    def test_simple_query(self):
        res = self.client.unauth_get('/api/visualize/vrl/apics/simple?limit=100')
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(isinstance(body, dict))
        self.assertIn('data', body)
        data = body['data']
        self.assertGreaterEqual(100, len(data))
        for el in data:
            self.assertIn('machine', el)
            self.assertIn('branch', el)
            self.assertIn('changelist', el)
            self.assertIn('gpu', el)

    def test_simple_query2(self):
        # invalid limit
        res = self.client.unauth_get('/api/visualize/vrl/apics/simple?limit=-1')
        self.assertEqual(res.status_code, 400)

    def test_params_with_only(self):
        res = self.client.unauth_get('/api/visualize/vrl/apics/apic/params/branch+gpu')
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(isinstance(body, dict))
        self.assertIn('params', body)
        params = body['params']
        self.assertEqual(len(params), 2)
