# filepath: app_dv_smartshop/src/api/amazon.py

import requests

class AmazonAPI:
    def __init__(self, access_key, secret_key, region):
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.base_url = "https://api.amazon.com"

    def fetch_product_data(self, sku):
        """Fetch product data from Amazon using SKU."""
        endpoint = f"{self.base_url}/products/{sku}"
        response = requests.get(endpoint, headers=self._get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching product data: {response.status_code} - {response.text}")

    def manage_inventory(self, sku, quantity):
        """Update inventory for a specific product SKU."""
        endpoint = f"{self.base_url}/inventory/{sku}"
        data = {"quantity": quantity}
        response = requests.put(endpoint, json=data, headers=self._get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error managing inventory: {response.status_code} - {response.text}")

    def _get_headers(self):
        """Generate headers for API requests."""
        return {
            "Authorization": f"Bearer {self.access_key}",
            "Content-Type": "application/json"
        }