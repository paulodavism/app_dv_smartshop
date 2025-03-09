from sqlmodel import SQLModel, Session, create_engine
from dotenv import load_dotenv
import os
from urllib.parse import urlparse

# Carrega variáveis do .env
load_dotenv()

# Configuração do engine
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("A variável DATABASE_URL não foi encontrada no arquivo .env")

# Ajuste para o Neon
parsed_url = urlparse(DATABASE_URL)
if parsed_url.scheme == "postgres":
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    """Cria todas as tabelas no banco de dados"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    Retorna uma nova sessão de banco de dados.
    Use um bloco 'with' para garantir que a sessão seja fechada automaticamente.
    """
    return Session(engine)