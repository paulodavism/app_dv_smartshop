from sqlmodel import SQLModel, create_engine, Session

# URL de conexão com o banco de dados
DATABASE_URL = "sqlite:///./database.db"  # Altere para a URL do seu banco de dados

# Criação do motor de conexão
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def create_db_and_tables():
    """Cria o banco de dados e as tabelas se não existirem."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Retorna uma nova sessão do banco de dados."""
    return Session(engine)