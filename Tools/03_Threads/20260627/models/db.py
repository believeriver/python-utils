import sys
import os
import datetime
import logging

from sqlalchemy import Column, DateTime, Integer, create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

from config import Config, setup_logger

class Database(object):
    def __init__(self) -> None:
        self.url = Config.DB_URL
        self.engine = create_engine(self.url, echo=False)
        self.log = self._set_logger(level=Config.LOGGER_LEVEL)
        # logger.info({'action': 'db.py', 'db': self.url})
        self.connect_db()

    def connect_db(self) -> sessionmaker:
        Base.metadata.create_all(self.engine)
        session = sessionmaker(self.engine)
        return session()

    @staticmethod
    def _set_logger(level):
        return setup_logger("Database", level)


Base = declarative_base()
database = Database()


class BaseDatabase(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)