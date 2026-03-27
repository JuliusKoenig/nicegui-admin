from dataclasses import dataclass, field as _field
from pathlib import Path
from typing import Union
from abc import abstractmethod
from typing import Any, Sequence

from fastapi import HTTPException
from nicegui import ui

from nicegui_admin.exceptions import FormValidationError
from nicegui_admin.fields import BaseField
from nicegui_admin.form import Form
from nicegui_admin.helpers import Unset, slugify_name, prettify_name, wrapped_method, DecoratedMethodClass
from nicegui_admin.admin import BaseAdmin, sub_page
from nicegui_admin.types import ExportType, SyncOrAsyncMethod


@dataclass
class BaseView(DecoratedMethodClass):
    """
    Base class for all views.

    :param path: Path to the view. Should start with '/' and should not end with '/'. If not provided, it will be inferred from the class name.
    :param title: Title of the view to be displayed. If not provided, it will be inferred from the class name.
    :param icon: Icon to be displayed for this view.
    """

    path: str | Unset = _field(default=Unset)
    title: str | Unset = _field(default=Unset)
    title_plural: str | Unset = _field(default=Unset, repr=False)
    icon: str | Unset | None = _field(default=Unset, repr=False)

    def __post_init__(self):
        self.path: str = Unset.resolve(self.path, slugify_name(self.__class__.__name__))
        if not self.path.startswith("/"):
            self.path = "/" + self.path
        if self.path.endswith("/"):
            self.path = self.path[:-1]
        if self.path == "":
            raise ValueError("path cannot be empty")
        self.title: str = Unset.resolve(self.title, prettify_name(self.__class__.__name__))
        self.title_plural: str = Unset.resolve(self.title_plural, prettify_name(self.__class__.__name__))
        self.icon = Unset.resolve(self.icon, None)

    @property
    def admin(self) -> Union[BaseAdmin, Any, None]:
        return getattr(self, "_admin", None)

    @property
    def sub_pages(self) -> dict[str, dict[str, Any]]:
        """
        All SubPages added to this SubPageRouter using the @sub_page decorator or the add_sub_page method.
        :return: A dictionary where the keys are the paths of the SubPages and the values
         are dictionaries containing the builder function and attributes of the SubPages, such as title and icon.
        """

        sub_pages = {}
        for builder, kwargs in self.__decorated_methods__.get("sub_page", {}).items():
            path = self.path + kwargs["path"]
            if path.endswith("/"):
                path = path[:-1]
            title = Unset.resolve(kwargs["title"], prettify_name(builder.__name__))
            icon = kwargs["icon"]
            sub_pages[path] = {"builder": builder,
                               "title": title,
                               "icon": icon}

        return sub_pages

    def sub_page(self,
                 path: str,
                 *,
                 title: str | None = Unset,
                 icon: str | Path | None = None) -> SyncOrAsyncMethod:
        """
        Decorator for adding a SubPage to the SubPage router.
        Use this decorator after instantiating the SubPage router to add builder functions for the SubPages.

        :param path: Path of the SubPage. Should be unique among all SubPages added to the SubPage router.
        :param title: Title of the SubPage. If not provided, the title will be inferred from the builder function name.
        :param icon: Icon of the SubPage. Can be either a URL or a local file path. If not provided, no icon will be set for the SubPage.
        :return: Decorator function that takes a builder function and adds it as a SubPage to the SubPage router.
        """

        return self.__decorate__("sub_page",
                                 path=path,
                                 title=title,
                                 icon=icon)

    # rename favicon to icon
    def add_sub_page(self,
                     builder: SyncOrAsyncMethod,
                     path: str,
                     *,
                     title: str | None = Unset,
                     icon: str | Path | None = None) -> None:
        """
        Add a SubPage to the SubPage router.

        :param builder: Builder function for the SubPage. Can be either a regular function or an async function that builds the page content when called.
        :param path: Path of the SubPage. Should be unique among all SubPages added to the SubPage router.
        :param title: Title of the SubPage. If not provided, the title will be inferred from the builder function name.
        :param icon: Icon of the SubPage. Can be either a URL or a local file path. If not provided, no icon will be set for the SubPage.
        :return: None
        """

        self.__add_decoration__(builder,
                                "sub_page",
                                path=path,
                                title=title,
                                icon=icon)


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
                               fields: Sequence[BaseField]) -> dict[str, Any]:
        # add hidden _pk to serialized data for reference
        serialized_data = {"_pk": (await self.pk_field.data_from_model(data=data))[1]}

        # map data to field.name's'
        for field in fields:
            is_none, value = await field.data_from_model(data=data)
            serialized_data[field.name] = value

        return serialized_data

    async def _data_to_model(self,
                             data: dict[str, Any],
                             fields: Sequence[BaseField]) -> dict[str, Any]:
        deserialized_data = {}

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
                   fields: Sequence[BaseField],
                   offset: int = 0,
                   limit: int = 100,
                   where: WHERE = None,
                   order_by: ORDER_BY = None) -> _list[dict[str, Any]]:
        raise NotImplementedError()

    @wrapped_method
    async def detail(self,
                     fields: Sequence[BaseField],
                     pk: str) -> dict[str, Any] | None:
        raise NotImplementedError()

    @abstractmethod
    async def create(self,
                     form: Form) -> dict[str, Any]:
        raise NotImplementedError()

    @abstractmethod
    async def edit(self,
                   pk: str,
                   form: Form) -> dict[str, Any]:
        raise NotImplementedError()

    @abstractmethod
    async def delete(self,
                     pk: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    async def form_validate(self,
                            form: Form) -> None:
        raise NotImplementedError()

    def handle_exception(self,
                         exc: Exception,
                         form: Form) -> None:
        if isinstance(exc, FormValidationError):
            message = "An error occurred while processing your request:\n"
            for field_name, error_message in exc.errors.items():
                message += f"{field_name}: {error_message}\n"
                form.field_handler[field_name].validation_element.error = error_message
            ui.notify(message,
                      type="negative",
                      multi_line=True)
            return
        error_message = "An error occurred while processing your request."
        if self.admin.debug:
            error_message += f"  Details:\n{str(exc)}"
        ui.notify(error_message,
                  type="negative")
        raise exc

    async def get_fields(self, mode: str) -> _list[BaseField]:
        result = []
        for field in self.fields:
            if mode in field.exclude:
                continue
            result.append(field)
        return result

    @sub_page("/list")
    async def list_page(self,
                        offset: int = 0,
                        limit: int = 100,
                        where: WHERE = None,
                        order_by: ORDER_BY = None) -> None:
        ui.button("Create", on_click=lambda e: ui.navigate.to(f"{self.admin.path}{self.path}/create"))

        # ToDo: remove after testing
        # await self.create(
        #     fields=await self.get_fields(mode="create"),
        #     data={"boolean_attr1": True,
        #           # "boolean_attr2": False,
        #           "integer_attr1": 100,
        #           # "integer_attr2": 0,
        #           "float_attr1": 6.9,
        #           # "float_attr2": 0.0,
        #           "string_attr1": "test",
        #           # "string_attr2": "",
        #           "uuid_attr1": uuid.uuid4(),
        #           # "uuid_attr2": None
        #           "ip_v4_address_attr1": "1.2.3.4",
        #           # "ip_v4_address_attr2": None,
        #           "ip_v6_address_attr1": "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        #           # "ip_v6_address_attr2": None,
        #           })

        # get fields
        fields = await self.get_fields(mode="list")

        # get data # ToDo: implement pagination, filtering, sorting, with async loading, etc.
        rows = await self.list(fields=fields,
                               offset=offset,
                               limit=limit,
                               where=where,
                               order_by=order_by)

        # build table
        table = ui.table(columns=[{"name": field.name,
                                   "label": field.label,
                                   "field": field.name,
                                   "required": field.not_none,
                                   "sortable": field.orderable,
                                   "align": field.align} for field in fields],
                         rows=rows,
                         row_key='name').classes("w-full table-sticky-header").props("flat bordered")

        # render label cells
        for field in fields:
            with table.add_slot(name=f"header-cell-{field.key}"):
                await field.list_table_header_cell(table=table)

        # render value cells
        for field in fields:
            with table.add_slot(name=f"body-cell-{field.key}"):
                await field.list_table_body_cell(table=table)

        # setup event handlers
        table.on("row-click", lambda e: ui.navigate.to(f"{self.admin.path}{self.path}/detail/{e.args[1]['_pk']}"))

    @sub_page("/detail/{pk}")
    async def detail_page(self,
                          pk: str) -> None:
        ui.button("Back", on_click=lambda e: ui.navigate.to(f"{self.admin.path}{self.path}/"))
        ui.button("Edit", on_click=lambda e: ui.navigate.to(f"{self.admin.path}{self.path}/edit/{pk}"))

        # get fields
        fields = await self.get_fields(mode="detail")

        # get data
        data = await self.detail(fields=fields,
                                 pk=pk)

        if data is None:
            raise HTTPException(status_code=404, detail=f"{self.title} with pk '{pk}' not found!")

        with ui.card(align_items="stretch").classes("detail-table table-sticky-header w-full").props("flat bordered").tight():
            with ui.element().classes("q-table__middle scroll"):
                with ui.element(tag="table").classes("q-table"):
                    with ui.element(tag="thead"):
                        with ui.element(tag="tr"):
                            with ui.element(tag="th").classes("text-left"), ui.row(align_items="center", wrap=False):
                                ui.icon(name="label_outline").classes("field-label-header-icon")
                                ui.label(text="Attribute").classes("field-label-header-text")
                            with ui.element(tag="th").classes("text-left"), ui.row(align_items="center", wrap=False):
                                ui.icon(name="toc").classes("field-label-header-icon")
                                ui.label(text="Value").classes("field-label-header-text")
                    tbody = ui.element(tag="tbody")

        with tbody:
            for field in fields:
                with ui.element(tag="tr"):
                    with ui.element(tag="td").classes("text-left"):
                        # render label
                        await field.detail_label()

                    with ui.element(tag="td").classes("text-left"):
                        # render value
                        await field.detail_value(value=data.get(field.name))

    @sub_page("/create")
    async def create_page(self) -> None:
        # get fields
        fields = await self.get_fields(mode="form")

        # create form
        form = Form(view=self)

        async def save():
            _data = await self.create(form=form)
            if _data is not None:
                ui.notify("Saved!",
                          type="positive")
                ui.navigate.to(f"{self.admin.path}{self.path}/edit/{_data.get('_pk')}")

        async def back():
            ui.navigate.back()

        async def save_and_back():
            _data = await self.create(form=form)
            if _data is not None:
                ui.notify("Saved!",
                          type="positive")
                ui.navigate.to(f"{self.admin.path}{self.path}/detail/{_data.get('_pk')}")

        # buttons
        with ui.button("Save", on_click=save).bind_enabled_from(form, "errors", backward=lambda v: not bool(v)):
            with ui.tooltip().classes("bg-red").bind_visibility_from(form, "errors", backward=lambda v: bool(v)):
                ui.html().bind_content_from(form, "errors", backward=lambda v: "".join(f"<div>{line}</div>" for line in v))
        with ui.button("Save and back", on_click=save_and_back).bind_enabled_from(form, "errors", backward=lambda v: not bool(v)):
            with ui.tooltip().classes("bg-red").bind_visibility_from(form, "errors", backward=lambda v: bool(v)):
                ui.html().bind_content_from(form, "errors", backward=lambda v: "".join(f"<div>{line}</div>" for line in v))
        ui.button("Back", on_click=back)

        # render fields
        for field in fields:
            with ui.card(align_items="stretch").classes("w-full").props("flat bordered").tight() as card:
                field_handler = form.add_field_handler(field=field)

                with ui.card_section().classes("p-0 mx-4 my-2 items-stretch") as label_section:
                    # render label
                    await field.form_label(field_handler=field_handler)

                ui.separator().bind_visibility_from(field_handler, "use_default", backward=lambda v: not v)

                with ui.card_section().classes("p-0 mx-4 my-2 items-stretch") as value_section:
                    # render value
                    await field.form_value(field_handler=field_handler)

                value_section.bind_visibility_from(field_handler, "use_default", backward=lambda v: not v)

        # form ready
        form.ready()

    @sub_page("/edit/{pk}")
    async def edit_page(self,
                        pk: str | None = None) -> None:
        if pk is None:
            raise NotImplementedError("create page is not implemented yet")

        # get fields
        fields = await self.get_fields(mode="form")

        # get data
        data = await self.detail(fields=fields,
                                 pk=pk)
        if data is None:
            raise HTTPException(status_code=404, detail=f"{self.title} with pk '{pk}' not found!")

        # create form
        form = Form(view=self)

        async def save():
            _data = await self.edit(form=form,
                                    pk=pk)
            if _data is not None:
                ui.notify("Saved!",
                          type="positive")
                old_path = ui.context.client.request.url.path
                new_path = f"{self.admin.path}{self.path}/edit/{_data.get('_pk')}"
                if old_path != new_path:
                    ui.navigate.to(new_path)
                else:
                    ui.navigate.reload()

        async def back():
            ui.navigate.back()

        async def save_and_back():
            _data = await self.edit(form=form,
                                    pk=pk)
            if _data is not None:
                ui.notify("Saved!",
                          type="positive")
                ui.navigate.to(f"{self.admin.path}{self.path}/detail/{_data.get('_pk')}")

        # buttons
        with ui.button("Save", on_click=save).bind_enabled_from(form, "errors", backward=lambda v: not bool(v)):
            with ui.tooltip().classes("bg-red").bind_visibility_from(form, "errors", backward=lambda v: bool(v)):
                ui.html().bind_content_from(form, "errors", backward=lambda v: "".join(f"<div>{line}</div>" for line in v))
        with ui.button("Save and back", on_click=save_and_back).bind_enabled_from(form, "errors", backward=lambda v: not bool(v)):
            with ui.tooltip().classes("bg-red").bind_visibility_from(form, "errors", backward=lambda v: bool(v)):
                ui.html().bind_content_from(form, "errors", backward=lambda v: "".join(f"<div>{line}</div>" for line in v))
        ui.button("Back", on_click=back)

        # render fields
        for field in fields:
            with ui.card(align_items="stretch").classes("w-full").props("flat bordered").tight() as card:
                field_handler = form.add_field_handler(field=field, value=data.get(field.name))

                with ui.card_section().classes("p-0 mx-4 my-2 items-stretch") as label_section:
                    # render label
                    await field.form_label(field_handler=field_handler)

                ui.separator().bind_visibility_from(field_handler, "use_default", backward=lambda v: not v)

                with ui.card_section().classes("p-0 mx-4 my-2 items-stretch") as value_section:
                    # render value
                    await field.form_value(field_handler=field_handler)

                value_section.bind_visibility_from(field_handler, "use_default", backward=lambda v: not v)

        # form ready
        form.ready()
