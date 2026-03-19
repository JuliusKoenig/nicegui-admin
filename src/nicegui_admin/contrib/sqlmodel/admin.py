from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Generator

from sqlalchemy import Engine
from sqlmodel import create_engine, Session

from nicegui_admin.admin import BaseAdmin
from nicegui_admin.helpers import Unset


@dataclass
class SqlModelAdmin(BaseAdmin):
    """
    Class for implementing Admin interface with SQLModel.

    :param engine: SQLAlchemy Engine instance or database URL.
    """

    engine: Engine | str = field(default=Unset, metadata={"immutable": True})

    def __post_init__(self):
        self.engine = Unset.resolve(self.engine, "sqlite:///database.db")
        if type(self.engine) is str:
            self.engine = create_engine(url=self.engine,
                                        echo=True,  # Todo: remove echo=True in production
                                        connect_args={"check_same_thread": False})
        super().__post_init__()

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
