import requests

class MercadoLivreAPI:
    BASE_URL = "https://api.mercadolivre.com"

    def __init__(self, access_token):
        self.access_token = access_token

    def get_product_info(self, sku):
        """Obtém informações de um produto pelo SKU."""
        url = f"{self.BASE_URL}/items/{sku}"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erro ao obter informações do produto: {response.status_code} - {response.text}")

    def get_stock_info(self, sku):
        """Obtém informações de estoque de um produto pelo SKU."""
        url = f"{self.BASE_URL}/items/{sku}/stock"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erro ao obter informações de estoque: {response.status_code} - {response.text}")

    def search_products(self, query):
        """Busca produtos com base em uma consulta."""
        url = f"{self.BASE_URL}/sites/MLB/search?q={query}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('results', [])
        else:
            raise Exception(f"Erro ao buscar produtos: {response.status_code} - {response.text}")