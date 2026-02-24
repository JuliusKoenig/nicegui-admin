from abc import ABC, abstractmethod
from enum import Enum
from types import GenericAlias, MappingProxyType
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
        self._frame_element: Union[None, ui.element, Any] = None
        self._header_element: Union[None, ui.element, Any] = None
        self._title_element: Union[None, ui.element, Any] = None
        self._body_element: Union[None, ui.element, Any] = None
        self._value_element: Union[None, ui.element, Any] = None
        self._footer_element: Union[None, ui.element, Any] = None
        self._help_tooltip_element: Union[None, ui.element, Any] = None
        self._help_element: Union[None, ui.element, Any] = None
        self._custom_elements: dict[str, ui.element] = {}

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
    def frame_element(self) -> Union[ui.element, Any]:
        if self._frame_element is None:
            raise ValueError("Frame is not rendered")
        return self._frame_element

    @property
    def header_element(self) -> Union[ui.element, Any]:
        if self._header_element is None:
            raise ValueError("Header is not rendered")
        return self._header_element

    @property
    def title_element(self) -> Union[ui.element, Any]:
        if self._title_element is None:
            raise ValueError("Title is not rendered")
        return self._title_element

    @property
    def body_element(self) -> Union[ui.element, Any]:
        if self._body_element is None:
            raise ValueError("Body is not rendered")
        return self._body_element

    @property
    def value_element(self) -> Union[ui.element, Any]:
        if self._value_element is None:
            raise ValueError("Value is not rendered")
        return self._value_element

    @property
    def footer_element(self) -> Union[ui.element, Any]:
        if self._footer_element is None:
            raise ValueError("Footer is not rendered")
        return self._footer_element

    @property
    def help_tooltip_element(self) -> Union[ui.element, Any]:
        if self._help_tooltip_element is None:
            raise ValueError("Help tooltip is not rendered")
        return self._help_tooltip_element

    @property
    def help_element(self) -> Union[ui.element, Any]:
        if self._help_element is None:
            raise ValueError("Help is not rendered")
        return self._help_element

    @property
    def custom_elements(self) -> MappingProxyType[str, ui.element]:
        return MappingProxyType(self._custom_elements)

    def add_custom_element(self, key: str, element: ui.element):
        if key in self._custom_elements:
            raise ValueError(f"Element {key} is already added")
        self._custom_elements[key] = element

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
        if self._frame_element is not None:
            self._frame_element.clear()

        # set elements to None
        self._frame_element = None
        self._header_element = None
        self._title_element = None
        self._body_element = None
        self._value_element = None
        self._footer_element = None
        self._help_element = None
        self._custom_elements = {}

        # clear fields
        for field in self._current_fields:
            await field.clear()

    async def render(self, value: Any) -> None:
        # clear frame
        await self.clear()

        # render frame
        await self.render_frame()

        # render field
        with self.frame_element:
            # render header
            await self.render_header()

            # render title
            with self.header_element:
                if self.enable_title:
                    await self.render_title()

            # render body
            await self.render_body()

            # render value
            with self.body_element:
                await self.render_value(value=value)

            # render footer
            await self.render_footer()

            # add help to value element
            if await self.has_help():
                # render help
                await self.render_help()

    async def render_frame(self) -> None:
        self._frame_element = ui.card()
        self.frame_element.tight()
        self.frame_element.props("flat")
        self.frame_element.props("bordered")
        self.frame_element.classes("w-full m-0 p-3")

    async def render_header(self) -> None:
        self._header_element = ui.row().classes("w-full items-center")

    async def render_title(self) -> None:
        self._title_element = ui.label(text=self.field_title)

    async def render_body(self) -> None:
        self._body_element = ui.row().classes("w-full items-center")

    @abstractmethod
    async def render_value(self, value: Any = None) -> None:
        ...

    async def render_footer(self) -> None:
        self._footer_element = ui.row().classes("w-full items-center")

    async def render_help(self) -> None:
        # get value element
        with self.value_element:
            self._help_tooltip_element = ui.tooltip()
            with self.help_tooltip_element:
                self._help_element = ui.html(self.field_help)

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
