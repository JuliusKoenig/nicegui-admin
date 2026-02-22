from contextlib import contextmanager
from typing import Generator

from sqlalchemy import Engine
from sqlmodel import create_engine, Session

from niceguitools.admin.admin import BaseAdmin
from niceguitools.admin.helper import Unset


class SqlModelAdmin(BaseAdmin):
    """
    Class for implementing Admin interface with SQLModel.
    """

    def __init__(self,
                 title: str = Unset,
                 engine: Engine | str = Unset,
                 **kwargs):
        """
        :param title: Admin title.
        :param kwargs: Other keyword arguments to be passed to the APIRouter constructor.
        """

        super().__init__(title=title,
                         **kwargs)

        engine = Unset.resolve(engine, "sqlite:///database.db")
        if type(engine) is str:
            engine = create_engine(url=engine,
                                   echo=True,  # Todo: remove echo=True in production
                                   connect_args={"check_same_thread": False})
        self._engine = engine

    @property
    def engine(self) -> Engine:
        """
        SQLAlchemy Engine instance used for database connection.

        :return: SQLAlchemy Engine instance.
        """

        return self._engine

    def get_session(self) -> Session:
        """
        Get a new SQLAlchemy Session instance.

        :return: SQLAlchemy Session instance.
        """

        return Session(self.engine,
                       expire_on_commit=False)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        Context manager for SQLAlchemy Session.

        :return: Generator yielding a SQLAlchemy Session instance.
        """

        session: Session = self.get_session()
        try:
            yield session
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
