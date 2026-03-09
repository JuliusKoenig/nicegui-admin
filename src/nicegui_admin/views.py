import json
import random
import string
from dataclasses import dataclass, field
from typing import Union, TYPE_CHECKING, Literal
from abc import abstractmethod, ABC
from typing import Any, Sequence

from nicegui import ui

from nicegui_admin.fields import BaseField
from nicegui_admin.helpers import Unset, slugify_name, prettify_name, WrappedMethodClass, wrapped_method, DecoratedMethodClass
from nicegui_admin.sub_page import SubPageRouter, sub_page

if TYPE_CHECKING:
    from nicegui_admin.admin import BaseAdmin


@dataclass
class BaseView(SubPageRouter):
    """
    Base class for all views.

    :param path: Path to the view. If not provided, it will be generated from the class name.
    :param title: Title of the view to be displayed.
    :param icon: Icon to be displayed for this view.
    """

    path: str | Unset = field(default=Unset)
    title: str | Unset = field(default=Unset)
    icon: str | Unset | None = field(default=Unset, repr=False)

    def __post_init__(self):
        SubPageRouter.__init__(self)
        self.path: str = Unset.resolve(self.path, slugify_name(self.__class__.__name__))
        if not self.path.startswith("/"):
            self.path = "/" + self.path
        self.title: str = Unset.resolve(self.title, prettify_name(self.__class__.__name__))
        self.icon = Unset.resolve(self.icon, None)

    @property
    def admin(self) -> Union["BaseAdmin", Any, None]:
        return getattr(self, "_admin", None)


# ToDo: implement DropDown
# ToDo: implement Link
# ToDo: implement CustomView

WHERE = dict[str, Any] | None
ORDER_BY = list[str] | None


@dataclass
class BaseCrudView(BaseView):
    """
    Base class for all CRUD views.
    """

    fields: Sequence[BaseField | str] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()

    @abstractmethod
    async def count(self,
                    where: WHERE = None) -> int:
        raise NotImplementedError()

    @abstractmethod
    async def list(self,
                   offset: int = 0,
                   limit: int = 100,
                   where: WHERE = None,
                   order_by: ORDER_BY = None) -> Sequence[dict[str, Any]]:
        raise NotImplementedError()

    @wrapped_method
    async def detail(self,
                     pk: Any) -> dict[str, Any] | None:
        result = await self.list(limit=1,
                                 where={"pk": pk})
        return result[0] if result else None

    @abstractmethod
    async def create(self,
                     *data: dict[str, Any]) -> dict[str, Any] | Sequence[dict[str, Any]]:
        raise NotImplementedError()

    @abstractmethod
    async def edit(self,
                   *pks: Any,
                   data: dict[str, Any]) -> dict[str, Any] | Sequence[dict[str, Any]]:
        raise NotImplementedError()

    @abstractmethod
    async def delete(self,
                     *pks: Any) -> bool | Sequence[bool]:
        raise NotImplementedError()

    @sub_page("/list")
    async def ui_list(self) -> None:
        await self.create({"asd": "".join(random.choices(string.ascii_letters + string.digits, k=10))})
        result = await self.list()
        for i, item in enumerate(result):
            item_json = json.dumps(item, indent=4)
            ui.label(f"Item {i}:\n{item_json}")
