from sqlmodel import create_engine, Session
from config import Config

engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI, 
    connect_args={"check_same_thread": False}
)

def get_session():
    with Session(engine) as session:
        yield session
