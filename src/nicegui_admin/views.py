from typing import Union, TYPE_CHECKING
from abc import abstractmethod
from typing import Any, Sequence

from nicegui_admin.helper import Unset, slugify_name, prettify_name, WrappedMethodClass, wrapped_method
from nicegui_admin.sub_page import SubPageHandler

if TYPE_CHECKING:
    from nicegui_admin.admin import BaseAdmin


class BaseView(WrappedMethodClass, SubPageHandler):
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

        SubPageHandler.__init__(self)

        self.path: str = Unset.resolve(path, slugify_name(self.__class__.__name__))
        if not self.path.startswith("/"):
            self.path = "/" + self.path
        self.title: str = Unset.resolve(title, prettify_name(self.__class__.__name__))
        self.icon = Unset.resolve(icon, None)

    def __str__(self) -> str:
        attrs_str = ", ".join(
            f"{attr}={getattr(self, attr)!r}"
            for attr in self.ATTRS_VISIBLE_IN_STR
        )
        return f"{self.__class__.__name__}({attrs_str})"

    @property
    def admin(self) -> Union["BaseAdmin", Any]:
        return self._admin

    async def builder(self):
        self.sub_page_cls()


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
