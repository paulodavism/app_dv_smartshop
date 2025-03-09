# filepath: app_dv_smartshop/src/api/mercadolivre.py

import requests

class MercadoLivreAPI:
    BASE_URL = "https://api.mercadolivre.com"

    def __init__(self, access_token):
        self.access_token = access_token

    def get_product(self, product_id):
        url = f"{self.BASE_URL}/items/{product_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def search_products(self, query):
        url = f"{self.BASE_URL}/sites/MLB/search"
        params = {"q": query}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def update_inventory(self, product_id, quantity):
        url = f"{self.BASE_URL}/items/{product_id}/stock"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "available_quantity": quantity
        }
        response = requests.put(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()

    def create_product(self, product_data):
        url = f"{self.BASE_URL}/items"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=product_data, headers=headers)
        response.raise_for_status()
        return response.json()