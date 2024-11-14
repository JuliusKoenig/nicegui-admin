from abc import ABC, abstractmethod
from enum import Enum
from types import GenericAlias
from typing import Any, Optional, TYPE_CHECKING, Union

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from nicegui import ui
from nicegui.events import UiEventArguments

if TYPE_CHECKING:
    from nicegui_admin.views.field import FieldView


class FieldMode(Enum):
    LIST = "list"
    GET = "get"
    SET = "set"


class BaseField(ABC):
    # user defined
    enable_title: bool = True
    enable_help: bool = True

    # internal
    abstract: bool = True
    field_annotation: Optional[type] = None
    sub_fields: Union[None, list[type["BaseField"]], dict[str, type["BaseField"]]] = None

    def __init__(self,
                 parent: Union["FieldView", "BaseField"],
                 field_id: Union[str, int]):

        self._parent: Union["FieldView", "BaseField"] = parent
        self._current_fields: list["BaseField"] = []
        self._field_id: Union[str, int] = field_id
        self._frame: Union[None, ui.element, Any] = None
        self._title_section: Union[None, ui.element, Any] = None
        self._title: Union[None, ui.element, Any] = None
        self._body: Union[None, ui.element, Any] = None
        self._help_tooltip: Union[None, ui.element, Any] = None
        self._help: Union[None, ui.element, Any] = None

        # add field to parent
        self.parent.add_field(self)

    @property
    def parent(self) -> Union["FieldView", "BaseField"]:
        return self._parent

    @property
    def current_fields(self) -> tuple["BaseField", ...]:
        if not self._current_fields:
            raise ValueError("Current fields are not set")
        return tuple(self._current_fields)

    @property
    def view(self) -> "FieldView":
        if isinstance(self.parent, BaseField):
            return self.parent.view
        return self.parent

    @property
    def field_id(self) -> Union[str, int]:
        if self._field_id == getattr(self.parent, "field_id", None):
            return self.parent.current_fields.index(self)
        return self._field_id

    @property
    def field_name(self) -> str:
        if type(self.field_id) == int:
            return self.parent.field_name
        return self.field_id

    @property
    def field_full_name_segments(self) -> list[Union[str, int]]:
        full_name_pos = [self.field_id]
        current_parent = self.parent
        while isinstance(current_parent, BaseField):
            full_name_pos.insert(0, current_parent.field_id)
            current_parent = current_parent.parent
        return full_name_pos

    @property
    def field_full_name(self) -> str:
        return ".".join(map(str, self.field_full_name_segments))

    @property
    def field_info(self) -> FieldInfo:
        current_model = self.view.current_model
        if isinstance(self.parent, BaseField):
            if issubclass(type(self.parent.field_info.annotation), GenericAlias):
                if getattr(self.parent.field_info.annotation, '__origin__', None) is list:
                    # get args
                    args = getattr(self.parent.field_info.annotation, '__args__', None)
                    if len(args) != 1:
                        raise ValueError(f"Field {self.field_full_name} not found in model")
                    if issubclass(args[0], BaseModel):
                        current_model = args[0]
            else:
                if issubclass(self.parent.field_info.annotation, BaseModel):
                    current_model = self.parent.field_info.annotation

        field_info = current_model.model_fields.get(self.field_name)
        if field_info is None:
            raise ValueError(f"Field {self.field_name} not found in model")
        return field_info

    @property
    def field_title(self) -> str:
        if self.field_info.title is not None:
            return self.field_info.title
        return "".join(map(str, self.field_full_name_segments[self.field_full_name_segments.index(self.field_name):]))

    @property
    def field_description(self) -> Optional[str]:
        if self.field_info.description is not None:
            return self.field_info.description
        return None

    @property
    def field_examples(self) -> Optional[list[str]]:
        if self.field_info.examples is not None:
            return self.field_info.examples
        return None

    @property
    def field_help(self) -> str:
        if self.field_description is not None:
            help_caption = self.field_description
        else:
            help_caption = self.field_id
        help_html = f"<b>{help_caption}</b>"
        if self.field_examples is not None:
            help_html += "<br>Examples"
            for example in self.field_examples:
                help_html += f"<br>- {example}"
        return help_html

    @property
    def frame(self) -> Union[ui.element, Any]:
        if self._frame is None:
            raise ValueError("Frame is not rendered")
        return self._frame

    @property
    def title_section(self) -> Union[ui.element, Any]:
        if self._title_section is None:
            raise ValueError("Title section is not rendered")
        return self._title_section

    @property
    def title(self) -> Union[ui.element, Any]:
        if self._title is None:
            raise ValueError("Title is not rendered")
        return self._title

    @property
    def body(self) -> Union[ui.element, Any]:
        if self._body is None:
            raise ValueError("Body is not rendered")
        return self._body

    @property
    def help_tooltip(self) -> Union[ui.element, Any]:
        if self._help_tooltip is None:
            raise ValueError("Help tooltip is not rendered")
        return self._help_tooltip

    @property
    def help(self) -> Union[ui.element, Any]:
        if self._help is None:
            raise ValueError("Help is not rendered")
        return self._help

    async def has_help(self) -> bool:
        if self.field_description is not None:
            return self.enable_help
        if self.field_examples is not None:
            return self.enable_help
        return False

    def add_field(self, field: "BaseField"):
        if field in self._current_fields:
            raise ValueError(f"Field {field} is already added")
        self._current_fields.append(field)

    async def clear(self) -> None:
        # clear frame
        if self._frame is not None:
            self._frame.clear()

        # set elements to None
        self._frame = None
        self._title_section = None
        self._title = None
        self._body = None
        self._help = None

        # clear fields
        for field in self._current_fields:
            await field.clear()

    async def render(self, field_mode: FieldMode, value: Any) -> None:
        # clear frame
        await self.clear()

        # render frame
        await self.render_frame()

        # render field
        with self.frame:
            if self.enable_title:
                # render title
                await self.render_title()

            # render value field
            await self.render_body(field_mode=field_mode, value=value)

            # add help to value element
            if await self.has_help():
                # render help
                await self.render_help()

    async def render_frame(self) -> None:
        self._frame = ui.card().classes("w-full")

    async def render_title(self) -> None:
        self._title_section = ui.card_section().classes("p-0")

        with self.title_section:
            self._title = ui.label(text=self.field_title)

    @abstractmethod
    async def render_body(self, field_mode: FieldMode, value: Any) -> None:
        ...

    async def render_help(self) -> None:
        # get value element
        with self.body:
            self._help_tooltip = ui.tooltip()
            with self.help_tooltip:
                self._help = ui.html(self.field_help)

    @abstractmethod
    async def get_value(self) -> Any:
        ...

    async def on_change(self, event: UiEventArguments):
        await self.view.on_change(field_name=self.field_id,
                                  value=await self.get_value(),
                                  event=event)

    @abstractmethod
    async def set_validation_error(self, validation_error: list[dict[str, Any]]):
        ...
