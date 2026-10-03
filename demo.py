from connector import WooCommerceConnector
from mock_woocommerce_server import start_test_server


if __name__ == "__main__":
    server = start_test_server()
    try:
        connector = WooCommerceConnector(
            base_url="http://127.0.0.1:8765",
            consumer_key="ck_demo_key",
            consumer_secret="cs_demo_secret",
        )

        print("Authentication:", connector.authenticate())
        print("Orders:", connector.list_orders(per_page=2))
        print("Order 101:", connector.get_order(101))
        print("Search product 'espresso':", connector.search_products("espresso"))
        print("Inventory:", connector.list_inventory(per_page=5))
    finally:
        server.shutdown()
        server.server_close()
