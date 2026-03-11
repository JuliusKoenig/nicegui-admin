from contextlib import contextmanager
from typing import Generator

from sqlalchemy import Engine
from sqlmodel import create_engine, Session

from nicegui_admin.admin import BaseAdmin
from nicegui_admin.helpers import Unset


class SqlModelAdmin(BaseAdmin):
    """
    Class for implementing Admin interface with SQLModel.
    """

    def __init__(self,
                 debug: bool | Unset = Unset,
                 prefix: str | Unset = Unset,
                 title: str | Unset = Unset,
                 engine: Engine | str = Unset):

        """
        :param title: Admin title.
        :param debug: Enable debug mode. If True, error pages will display detailed error information and stack traces.
        :param prefix: The path prefix for this SubPageApp. Should start with '/' and should not end with '/'.
        """

        super().__init__(debug=debug,
                         prefix=prefix,
                         title=title)

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
