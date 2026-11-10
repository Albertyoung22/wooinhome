import os
import unittest
import json
from app import app, db
from models import RFQQuotation, CaseStudy, Article

class WooinhomeTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_01_public_ssr_routes(self):
        routes = [
            '/',
            '/manage-host',
            '/manage-agent',
            '/spatial-renovation',
            '/works',
            '/calculator',
            '/blog',
            '/faq',
            '/contact',
            '/robots.txt',
            '/sitemap.xml'
        ]
        for r in routes:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 200, f"Route {r} failed with status {res.status_code}")
            print(f"[PASS] SSR Route {r} -> 200 OK")

    def test_02_spa_hybrid_request(self):
        res = self.client.get('/manage-host', headers={'X-Requested-With': 'SPA'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsNotNone(data)
        self.assertIn('html', data)
        self.assertIn('title', data)
        print(f"[PASS] SPA Hybrid Request -> Title: {data['title']}")

    def test_03_health_endpoint(self):
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['db'], 'ok')
        print(f"[PASS] Health Check -> {data}")

    def test_04_ai_chat_endpoint(self):
        res = self.client.post('/api/ai/chat', json={'query': '房東報稅有什麼優惠？', 'lang': 'zh-TW'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('reply', data)
        self.assertTrue('1.5 萬' in data['reply'] or '所得稅' in data['reply'])
        print(f"[PASS] AI Chat -> Received response ({len(data['reply'])} chars)")

    def test_05_rfq_submission_and_crm(self):
        rfq_payload = {
            'customer_name': '張董事長',
            'gender': '先生',
            'phone': '0988-123-456',
            'email': 'investor@example.com',
            'line_id': 'wooinhome_vip',
            'city': '台南市',
            'district': '中西區',
            'property_type': '整棟透天厝',
            'size_ping': '55',
            'current_status': '空屋閒置中',
            'requirements': '預計將三層老透天活化改為日式侘寂精品套房',
            'cart_items': json.dumps([
                {'code': 'manage_host', 'title': '包租代管3年方案', 'specs': {'格局': '5套房'}, 'price': '預估月收$45,000'}
            ])
        }
        res = self.client.post('/api/rfq/submit', data=rfq_payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['rfq_number'].startswith('RFQ-'))
        print(f"[PASS] RFQ Submission -> Generated #{data['rfq_number']}")

        # Verify record in DB
        with app.app_context():
            saved = RFQQuotation.query.filter_by(rfq_number=data['rfq_number']).first()
            self.assertIsNotNone(saved)
            self.assertEqual(saved.customer_name, '張董事長')
            self.assertEqual(len(saved.items), 1)
            print(f"[PASS] DB Verification -> Found {saved.customer_name} with {len(saved.items)} RFQ items")

    def test_06_admin_crm_flow(self):
        # 1. Login with bad password
        res = self.client.post('/admin/login', data={'username': 'admin', 'password': 'wrongpassword'})
        self.assertEqual(res.status_code, 200)

        # 2. Login with correct password
        res = self.client.post('/admin/login', data={'username': 'admin', 'password': 'admin888'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'CRM', res.data)
        print("[PASS] Admin Login -> Succeeded")

        # 3. Access Dashboard
        res = self.client.get('/admin/dashboard')
        self.assertEqual(res.status_code, 200)
        print("[PASS] Admin Dashboard -> 200 OK")

        # 4. Export CSV
        res = self.client.get('/admin/export-csv')
        self.assertEqual(res.status_code, 200)
        self.assertIn('text/csv', res.headers.get('Content-Type', ''))
        print(f"[PASS] Export CSV -> {len(res.data)} bytes")

if __name__ == '__main__':
    unittest.main()
