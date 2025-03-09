import requests

class AmazonAPI:
    def __init__(self, access_key, secret_key, associate_tag):
        self.access_key = access_key
        self.secret_key = secret_key
        self.associate_tag = associate_tag
        self.base_url = "https://api.amazon.com"

    def buscar_produtos(self, termo_busca):
        """Busca produtos na Amazon com base em um termo de busca."""
        endpoint = f"{self.base_url}/products"
        params = {
            'search': termo_busca,
            'access_key': self.access_key,
            'secret_key': self.secret_key,
            'associate_tag': self.associate_tag
        }
        response = requests.get(endpoint, params=params)
        return response.json()

    def obter_dados_estoque(self, sku):
        """Obtém dados de estoque para um produto específico."""
        endpoint = f"{self.base_url}/inventory"
        params = {
            'sku': sku,
            'access_key': self.access_key,
            'secret_key': self.secret_key,
            'associate_tag': self.associate_tag
        }
        response = requests.get(endpoint, params=params)
        return response.json()

    def registrar_venda(self, sku, quantidade):
        """Registra uma venda de um produto na Amazon."""
        endpoint = f"{self.base_url}/sales"
        data = {
            'sku': sku,
            'quantity': quantidade,
            'access_key': self.access_key,
            'secret_key': self.secret_key,
            'associate_tag': self.associate_tag
        }
        response = requests.post(endpoint, json=data)
        return response.json()