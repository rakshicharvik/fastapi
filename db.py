from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings
 
 
engine = create_engine(str(settings.DATABASE_URL))
 
def get_db_session():
    return sessionmaker(bind=engine)()