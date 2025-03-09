import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

# Configurações do arquivo .env
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Verificação obrigatória
if None in (DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT):
    raise ValueError("""
    ⚠️ Variáveis de ambiente não configuradas corretamente!
    Verifique seu arquivo .env e certifique-se que contém:
    DB_NAME=...
    DB_USER=...
    DB_PASS=...
    DB_HOST=...
    DB_PORT=...
    """)

# SQL para criar tabelas
SQL_SCHEMA = """
CREATE TABLE IF NOT EXISTS deposito (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) UNIQUE NOT NULL,
    tipo VARCHAR(50) NOT NULL DEFAULT 'Próprio',
    observacoes VARCHAR(200)
);
CREATE TABLE IF NOT EXISTS produto (
    sku VARCHAR(50) PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    descricao VARCHAR(500)
);
CREATE TABLE IF NOT EXISTS estoque (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) REFERENCES produto(sku) ON DELETE CASCADE,
    deposito_id INTEGER REFERENCES deposito(id) ON DELETE CASCADE,
    quantidade INTEGER NOT NULL CHECK (quantidade >= 0),
    tipo VARCHAR(50) NOT NULL DEFAULT 'Entrada', -- Alterado para VARCHAR(50)
    data_hora TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    observacoes VARCHAR(200),
    saldo INTEGER NOT NULL DEFAULT 0 -- Adicionado coluna saldo
);
"""

def create_schema():
    try:
        # Conexão ao banco de dados
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Executa DDL
        cur.execute(SQL_SCHEMA)
        print("✅ Tabelas criadas/atualizadas com sucesso!")
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_schema()