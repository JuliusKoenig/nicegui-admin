from pathlib import Path
from typing import Union, TYPE_CHECKING, Callable
from abc import abstractmethod
from typing import Any, Sequence

from niceguitools.admin.helper import Unset, slugify_name, prettify_name, WrappedMethodClass, wrapped_method

if TYPE_CHECKING:
    from niceguitools.admin.admin import BaseAdmin


class BaseView(WrappedMethodClass):
    """
    Base class for all views.
    """

    ATTRS_VISIBLE_IN_STR = {"path", "title", "is_active", "is_accessible"}

    def __init__(self,
                 *,
                 path: str = Unset,
                 title: str = Unset,
                 icon: str | None = Unset):
        """
        :param path: Path to the view. If not provided, it will be generated from the class name.
        :param title: Title of the view to be displayed.
        :param icon: Icon to be displayed for this view.
        """

        self._path: str = Unset.resolve(path, slugify_name(self.__class__.__name__))
        if not self._path.startswith("/"):
            self._path = "/" + self._path
        self._title: str = Unset.resolve(title, prettify_name(self.__class__.__name__))
        self._icon = Unset.resolve(icon, None)

    def __str__(self) -> str:
        attrs_str = ", ".join(
            f"{attr}={getattr(self, attr)!r}"
            for attr in self.ATTRS_VISIBLE_IN_STR
        )
        return f"{self.__class__.__name__}({attrs_str})"

    @property
    def admin(self) -> Union["BaseAdmin", Any]:
        return self._admin

    @property
    def path(self) -> str:
        return self._path

    @property
    def title(self) -> str:
        return self._title

    @property
    def icon(self) -> str | None:
        return self._icon

    @property
    def is_active(self) -> bool:
        return False

    @property
    def is_accessible(self) -> bool:
        return True

    def page(self,
             path: str, *,
             title: str | None = None,
             viewport: str | None = None,
             favicon: str | Path | None = None,
             dark: bool | None = ...,  # type: ignore
             response_timeout: float = 3.0,
             _direct: bool = False,
             **kwargs) -> Callable:
        """
        Decorator for creating a new page for view.
        Creates a new page at the given route.
        Each user will see a new instance of the page.
        This means it is private to the user and not shared with others.

        :param path: route of the new page (path must start with '/')
        :param title: optional page title
        :param viewport: optional viewport meta tag content
        :param favicon: optional relative filepath or absolute URL to a favicon (default: `None`, NiceGUI icon will be used)
        :param dark: whether to use Quasar's dark mode (defaults to `dark` argument of `run` command)
        :param response_timeout: maximum time for the decorated function to build the page (default: 3.0)
        :param kwargs: additional keyword arguments passed to FastAPI's @app.get method
        """

        return self.admin.page(path=path,
                               title=title,
                               viewport=viewport,
                               favicon=favicon,
                               dark=dark,
                               response_timeout=response_timeout,
                               **kwargs)


# ToDo: implement DropDown
# ToDo: implement Link
# ToDo: implement CustomView

WHERE = dict[str, Any] | None
ORDER_BY = list[str] | None


class CrudView(BaseView):
    """
    Base class for all CRUD views.
    """

    def __init__(self,
                 *,
                 path: str = Unset,
                 title: str = Unset,
                 icon: str | None = Unset):
        """
        :param path: Path to the view. If not provided, it will be generated from the class name.
        :param title: Title of the view to be displayed.
        :param icon: Icon to be displayed for this view.
        """

        super().__init__(path=path,
                         title=title,
                         icon=icon)

        self._methods = []

    @wrapped_method
    @abstractmethod
    async def count(self,
                    where: WHERE = None) -> int:
        raise NotImplementedError()

    @wrapped_method
    @abstractmethod
    async def list(self,
                   offset: int = 0,
                   limit: int = 100,
                   where: WHERE = None,
                   order_by: ORDER_BY = None) -> Sequence[dict[str, Any]]:
        raise NotImplementedError()

    @wrapped_method
    async def get(self,
                  pk: Any) -> dict[str, Any] | None:
        result = await self.list(limit=1,
                                 where={"pk": pk})
        return result[0] if result else None

    @wrapped_method
    @abstractmethod
    async def create(self,
                     *data: dict[str, Any]) -> dict[str, Any] | Sequence[dict[str, Any]]:
        raise NotImplementedError()

    @wrapped_method
    @abstractmethod
    async def edit(self,
                   *pks: Any,
                   data: dict[str, Any]) -> dict[str, Any] | Sequence[dict[str, Any]]:
        raise NotImplementedError()

    @wrapped_method
    @abstractmethod
    async def delete(self,
                     *pks: Any) -> bool | Sequence[bool]:
        raise NotImplementedError()
