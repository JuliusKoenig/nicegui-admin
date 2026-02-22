from typing import Union, TYPE_CHECKING
from abc import abstractmethod
from typing import Any, Sequence

from niceguitools.admin.helper import Unset, slugify_class_name, prettify_class_name, WrappedMethodClass, wrapped_method

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

        self._path: str = Unset.resolve(path, slugify_class_name(self.__class__.__name__))
        if not self._path.startswith("/"):
            self._path = "/" + self._path
        self._title: str = Unset.resolve(title, prettify_class_name(self.__class__.__name__))
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
