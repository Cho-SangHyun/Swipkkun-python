from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
# from starlette.config import Config
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# config = Config(".env")
# DB_URL = config("DATABASE_URL")

DB_URL = str(os.environ.get("DATABASE_URL"))


class EngineConn:
    def __init__(self):
        self.engine = create_engine(DB_URL, pool_recycle=500)

    def sessionmaker(self):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        return session

    def connection(self):
        conn = self.engine.connect()
        return conn