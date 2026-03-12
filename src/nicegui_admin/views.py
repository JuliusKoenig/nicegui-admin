import random
import string
import uuid
from dataclasses import dataclass, field as _field
from ipaddress import IPv4Address, IPv6Address
from typing import Union, TYPE_CHECKING
from abc import abstractmethod
from typing import Any, Sequence

from fastapi import HTTPException
from nicegui import ui

from nicegui_admin.elements.detail_table import DetailTable
from nicegui_admin.fields import BaseField
from nicegui_admin.helpers import Unset, slugify_name, prettify_name, wrapped_method
from nicegui_admin.sub_page import SubPageRouter, sub_page
from nicegui_admin.types import ExportType

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
    title_plural: str | Unset = _field(default=Unset, repr=False)
    icon: str | Unset | None = _field(default=Unset, repr=False)

    def __post_init__(self):
        SubPageRouter.__init__(self)
        self.path: str = Unset.resolve(self.path, slugify_name(self.__class__.__name__))
        if not self.path.startswith("/"):
            self.path = "/" + self.path
        self.title: str = Unset.resolve(self.title, prettify_name(self.__class__.__name__))
        self.title_plural: str = Unset.resolve(self.title_plural, prettify_name(self.__class__.__name__))
        self.icon = Unset.resolve(self.icon, None)

    @property
    def admin(self) -> Union["BaseAdmin", Any, None]:
        return getattr(self, "_admin", None)


# ToDo: implement DropDown
# ToDo: implement Link
# ToDo: implement CustomView

WHERE = dict[str, Any] | None
ORDER_BY = list[str] | None
_list = list


@dataclass
class BaseCrudView(BaseView):
    """
    Base class for all CRUD views.
    """

    fields: Sequence[BaseField | str] = _field(default_factory=list)
    pk_field: BaseField | None = _field(default=None, init=False)
    exclude_pk: bool = _field(default=False)
    exclude_fields_from_list: list[str] = _field(default_factory=list)
    exclude_fields_from_detail: list[str] = _field(default_factory=list)
    exclude_fields_from_create: list[str] = _field(default_factory=list)
    exclude_fields_from_edit: list[str] = _field(default_factory=list)
    searchable_fields: list[str] | None = _field(default=None)
    sortable_fields: list[str] | None = _field(default=None)
    export_types: list[ExportType] = _field(default_factory=lambda: [ExportType.CSV,
                                                                     ExportType.EXCEL,
                                                                     ExportType.PDF,
                                                                     ExportType.PRINT])
    export_fields: list[str] | None = _field(default=None)

    def __post_init__(self):
        fringe = list(self.fields)
        while len(fringe) > 0:
            field = fringe.pop(0)
            # if not hasattr(field, "_name"):
            #     field._name = field.name  # type: ignore
            # if isinstance(field, CollectionField): #  ToDo: check if need implement Collection Field first
            #     for f in field.fields:
            #         f._name = f"{field._name}.{f.name}"  # type: ignore
            #     fringe.extend(field.fields)
            # name = field._name  # type: ignore
            if field.name in self.pk_attrs and self.exclude_pk:
                if "list" not in field.exclude:
                    field.exclude.append("list")
                if "detail" not in field.exclude:
                    field.exclude.append("detail")
                if "create" not in field.exclude:
                    field.exclude.append("create")
                if "edit" not in field.exclude:
                    field.exclude.append("edit")
            if field.name in self.exclude_fields_from_list:
                if "list" not in field.exclude:
                    field.exclude.append("list")
            if field.name in self.exclude_fields_from_detail:
                if "detail" not in field.exclude:
                    field.exclude.append("detail")
            if field.name in self.exclude_fields_from_create:
                if "create" not in field.exclude:
                    field.exclude.append("create")
            if field.name in self.exclude_fields_from_edit:
                if "edit" not in field.exclude:
                    field.exclude.append("edit")
            # if not isinstance(field, CollectionField): # ToDo: check if need implement Collection Field first
            #     all_field_names.append(name)
            #     field.searchable = (self.searchable_fields is None) or (
            #             name in self.searchable_fields
            #     )
            #     field.orderable = (self.sortable_fields is None) or (
            #             name in self.sortable_fields
            #     )

            if self.searchable_fields is not None:
                if field.name in self.searchable_fields:
                    field.searchable = True
                else:
                    field.searchable = False
            if self.sortable_fields is not None:
                if field.name in self.sortable_fields:
                    field.orderable = True
                else:
                    field.orderable = False
            if self.export_fields is not None:
                if field.name in self.export_fields:
                    field.exportable = True
                else:
                    field.exportable = False

        super().__post_init__()

    @property
    def pk_attr(self) -> str:
        if self.pk_field is None:
            raise AttributeError("pk_field is not defined")
        return self.pk_field.name

    @property
    def pk_attrs(self) -> list[str]:
        if self.pk_field is None:
            raise AttributeError("pk_field is not defined")
        return self.pk_field.name.split(",")

    async def _data_from_model(self,
                               data: dict[str, Any],
                               fields: Sequence[BaseField] | None = None) -> dict[str, Any]:
        # add hidden _pk to serialized data for reference
        serialized_data = {"_pk": (await self.pk_field.data_from_model(data=data))[1]}

        # find fields by key if not provided
        if fields is None:
            fields = []
            for field_key in data.keys():
                field = None
                for field in self.fields:
                    if field.key == field_key:
                        break
                if field is None:
                    raise ValueError(f"Field with key '{field_key}' not found in fields.")
                fields.append(field)

        # map data to field.name's'
        for field in fields:
            is_none, value = await field.data_from_model(data=data)
            serialized_data[field.name] = value

        return serialized_data

    async def _data_to_model(self,
                             data: dict[str, Any],
                             fields: Sequence[BaseField] | None = None) -> dict[str, Any]:
        deserialized_data = {}

        # find fields by name if not provided
        if fields is None:
            fields = []
            for field_name in data.keys():
                field = None
                for field in self.fields:
                    if field.name == field_name:
                        break
                if field is None:
                    raise ValueError(f"Field with name '{field_name}' not found in fields.")
                fields.append(field)

        # map data to field.key's
        for field in fields:
            deserialized_data[field.key] = await field.data_to_model(data=data)

        return deserialized_data

    @abstractmethod
    async def count(self,
                    where: WHERE = None) -> int:
        raise NotImplementedError()

    @abstractmethod
    async def list(self,
                   offset: int = 0,
                   limit: int = 100,
                   where: WHERE = None,
                   order_by: ORDER_BY = None,
                   serialization_fields: Sequence[BaseField] | None = None) -> _list[dict[str, Any]]:
        raise NotImplementedError()

    @wrapped_method
    async def detail(self,
                     pk: str,
                     serialization_fields: Sequence[BaseField] | None = None) -> dict[str, Any] | None:
        raise NotImplementedError()

    @abstractmethod
    async def create(self,
                     *data: dict[str, Any],
                     deserialization_fields: Sequence[BaseField] | None = None) -> dict[str, Any] | _list[dict[str, Any]]:
        raise NotImplementedError()

    @abstractmethod
    async def edit(self,
                   *pks: str,
                   data: dict[str, Any],
                   deserialization_fields: Sequence[BaseField] | None = None) -> dict[str, Any] | _list[dict[str, Any]]:
        raise NotImplementedError()

    @abstractmethod
    async def delete(self,
                     *pks: str) -> bool | _list[bool]:
        raise NotImplementedError()

    async def get_fields(self, mode: str) -> _list[BaseField]:
        result = []
        for field in self.fields:
            if mode in field.exclude:
                continue
            result.append(field)
        return result

    @sub_page("/")
    async def list_page(self,
                        offset: int = 0,
                        limit: int = 100,
                        where: WHERE = None,
                        order_by: ORDER_BY = None) -> None:
        # ToDo: remove after testing
        await self.create({
            "boolean_attr1": True,
            # "boolean_attr2": False,
            "integer_attr1": 100,
            # "integer_attr2": 0,
            "float_attr1": 6.9,
            # "float_attr2": 0.0,
            "string_attr1": "test",
            # "string_attr2": "",
            "uuid_attr1": uuid.uuid4(),
            # "uuid_attr2": None
            "ip_v4_address_attr1": "1.2.3.4",
            # "ip_v4_address_attr2": None,
            "ip_v6_address_attr1": "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            # "ip_v6_address_attr2": None,
        })

        # get fields
        fields = await self.get_fields(mode="list")

        # get data # ToDo: implement pagination, filtering, sorting, with async loading, etc.
        rows = await self.list(offset=offset,
                               limit=limit,
                               where=where,
                               order_by=order_by,
                               serialization_fields=fields)

        # build table
        table = ui.table(columns=[{"name": field.name,
                                   "label": field.label,
                                   "field": field.name,
                                   "required": field.required,
                                   "sortable": field.orderable,
                                   "align": "left"} for field in fields],
                         rows=rows,
                         row_key='name').classes("w-full")

        # render label cells
        for field in fields:
            render_method = field.get_render_method(mode="list",
                                                    element_name="label")
            if render_method is not None:
                with table.add_slot(name=f"header-cell-{field.key}"):
                    await render_method(table=table)

        # render value cells
        for field in fields:
            render_method = field.get_render_method(mode="list",
                                                    element_name="value")
            if render_method is not None:
                with table.add_slot(name=f"body-cell-{field.key}"):
                    await render_method(table=table)

        # setup event handlers
        table.on("row-click",
                 lambda e: ui.navigate.to(f"{self.prefix}/detail/{e.args[1]['_pk']}"))

    @sub_page("/detail/{pk}")
    async def detail_page(self,
                          pk: str) -> None:
        # get fields
        fields = await self.get_fields(mode="detail")

        # get data
        data = await self.detail(pk=pk,
                                 serialization_fields=fields)
        if data is None:
            raise HTTPException(status_code=404, detail=f"{self.title} with pk '{pk}' not found!")

        with DetailTable(columns=["Attribute",
                                  "Value"]).classes("w-full"):
            for field in fields:
                # render label
                label_render_method = field.get_render_method(mode="detail",
                                                              element_name="label")
                if label_render_method is not None:
                    await label_render_method()

                # render value
                value_render_method = field.get_render_method(mode="detail",
                                                              element_name="value")
                if value_render_method is not None:
                    await value_render_method(value=data.get(field.name))

        ui.button("Back", on_click=lambda e: ui.navigate.back())
        ui.button("Edit", on_click=lambda e: ui.navigate.to(f"{self.prefix}/edit/{pk}"))

    @sub_page("/edit/{pk}")
    async def edit_page(self,
                        pk: str) -> None:
        # get fields
        fields = await self.get_fields(mode="form")

        # get data
        data = await self.detail(pk=pk,
                                 serialization_fields=fields)
        if data is None:
            raise HTTPException(status_code=404, detail=f"{self.title} with pk '{pk}' not found!")

        with ui.column().classes("w-full"):
            for field in fields:
                # render label
                label_render_method = field.get_render_method(mode="form",
                                                              element_name="label")
                if label_render_method is not None:
                    await label_render_method()

                # render value
                value_render_method = field.get_render_method(mode="form",
                                                              element_name="value")
                if value_render_method is not None:
                    await value_render_method(value=data.get(field.name))

        ui.button("Back", on_click=lambda e: ui.navigate.back())
