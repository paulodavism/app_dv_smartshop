import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

# Configuração do Neon
DATABASE_URL = os.getenv("DATABASE_URL")

# Verificação obrigatória
if not DATABASE_URL:
    raise ValueError("""
    ⚠️ Variável de ambiente DATABASE_URL não configurada corretamente!
    Verifique seu arquivo .env e certifique-se que contém:
    DATABASE_URL=postgres://user:password@host:port/database
    """)

# SQL para criar tabelas (mantenha o mesmo que você já tem)
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
    tipo VARCHAR(50) NOT NULL DEFAULT 'Entrada',
    data_hora TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    observacoes VARCHAR(200),
    saldo INTEGER NOT NULL DEFAULT 0
);
"""

def create_schema():
    try:
        # Conexão ao banco de dados usando a URL do Neon
        conn = psycopg2.connect(DATABASE_URL)
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