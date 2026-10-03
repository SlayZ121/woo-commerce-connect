import unittest

from connector import WooCommerceConnector
from mock_woocommerce_server import start_test_server


class WooCommerceConnectorTests(unittest.TestCase):
    def setUp(self):
        self.server = start_test_server()
        self.connector = WooCommerceConnector(
            base_url="http://127.0.0.1:8765",
            consumer_key="ck_demo_key",
            consumer_secret="cs_demo_secret",
        )

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_authenticate_and_list_orders(self):
        self.assertTrue(self.connector.authenticate())
        orders = self.connector.list_orders(per_page=2)
        self.assertEqual(len(orders), 2)
        self.assertEqual(orders[0]["id"], 101)

    def test_get_order_and_search_products(self):
        order = self.connector.get_order(101)
        self.assertEqual(order["id"], 101)
        self.assertEqual(order["status"], "pending")

        products = self.connector.search_products("espresso")
        self.assertGreater(len(products), 0)
        self.assertEqual(products[0]["name"], "Espresso Beans")

    def test_list_inventory_includes_stock(self):
        inventory = self.connector.list_inventory(per_page=5)
        self.assertGreater(len(inventory), 0)
        self.assertIn("stock_quantity", inventory[0])

    def test_retries_after_rate_limit(self):
        result = self.connector._request("/wp-json/wc/v3/orders/rate-limit-check")
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["id"], 999)


if __name__ == "__main__":
    unittest.main()
