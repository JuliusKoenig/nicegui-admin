from dataclasses import dataclass, field as _field
from typing import Union, TYPE_CHECKING
from abc import abstractmethod
from typing import Any, Sequence

from nicegui import ui

from nicegui_admin.fields import BaseField
from nicegui_admin.helpers import Unset, slugify_name, prettify_name, wrapped_method
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

    path: str | Unset = _field(default=Unset)
    title: str | Unset = _field(default=Unset)
    icon: str | Unset | None = _field(default=Unset, repr=False)

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

    fields: Sequence[BaseField | str] = _field(default_factory=list)

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

    async def get_fields(self, mode: str) -> Sequence[BaseField]:
        result = []
        for field in self.fields:
            if type(field.exclude) is bool:
                if field.exclude:
                    continue
            elif type(field.exclude) is list:
                if mode in field.exclude:
                    continue
            result.append(field)
        return result

    @sub_page("/list")
    async def ui_list(self,
                      offset: int = 0,
                      limit: int = 100,
                      where: WHERE = None,
                      order_by: ORDER_BY = None) -> None:
        # get fields
        fields = await self.get_fields(mode="list")

        # get data # ToDo: implement pagination, filtering, sorting, with async loading, etc.
        rows = list(await self.list(offset=offset,
                                    limit=limit,
                                    where=where,
                                    order_by=order_by))

        # build table
        table = ui.table(columns=[{"name": field.name,
                                   "label": field.label,
                                   "field": field.key,
                                   "required": field.required,
                                   "sortable": field.orderable,
                                   "align": "left"} for field in fields],
                         rows=rows,
                         row_key='name').classes("w-full")



        # render header cells
        for field in fields:
            render_method = field.get_render_method(mode="list",
                                                    element_name="table_header_cell")
            if render_method is not None:
                with table.add_slot(name=f"header-cell-{field.key}"):
                    await render_method(table=table)


        # render body cells
        for field in fields:
            render_method = field.get_render_method(mode="list",
                                      element_name="table_body_cell")
            if render_method is not None:
                with table.add_slot(name=f"body-cell-{field.key}"):
                    await render_method(table=table)
