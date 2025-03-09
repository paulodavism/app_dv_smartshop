import psycopg2
from src.db.models import Deposito

try:
    conn = psycopg2.connect(
        dbname="dvsmartshop",
        user="postgres",
        password="vDpostdb",
        host="localhost",
        port="5432"
    )
    print("✅ Conexão bem-sucedida!")

    conn.close()
except Exception as e:
    print(f"❌ Erro: {e}")