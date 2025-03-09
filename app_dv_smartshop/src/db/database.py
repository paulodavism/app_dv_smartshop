from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "postgresql://username:password@hostname:port/dbname"

engine = create_engine(DATABASE_URL)

def get_session():
    """Create a new database session."""
    return Session(engine)

def init_db():
    """Create the database tables."""
    SQLModel.metadata.create_all(engine)