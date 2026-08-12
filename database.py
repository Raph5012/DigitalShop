from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tables import Base
from contextlib import contextmanager


class Database:
    def __init__(self, url: str = "sqlite:///base.db"):
        self.engine = create_engine(url)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session_scope(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
