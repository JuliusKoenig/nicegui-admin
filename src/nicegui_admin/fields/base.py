from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

from nicegui import ui
from nicegui.events import UiEventArguments

from nicegui_admin.views.field import FieldView


class FieldMode(Enum):
    LIST = "list"
    GET = "get"
    SET = "set"


class BaseField(ABC):
    enable_title: bool = True
    enable_help: bool = True

    def __init__(self,
                 view: "FieldView",
                 field_name: str,
                 field_title: Optional[str] = None,
                 field_description: Optional[str] = None,
                 field_examples: Optional[list[str]] = None):

        self._view = view
        self._field_name = field_name
        self._field_title = field_title
        self._field_description = field_description
        self._field_examples = field_examples

    @property
    def view(self) -> "FieldView":
        return self._view

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def field_title(self) -> str:
        if self._field_title is None:
            return self.field_name
        return self._field_title

    @property
    def field_description(self) -> Optional[str]:
        return self._field_description

    @property
    def field_examples(self) -> Optional[list[str]]:
        return self._field_examples

    @property
    def field_help(self) -> str:
        if self.field_description is not None:
            help_caption = self.field_description
        else:
            help_caption = self.field_name
        help_html = f"<b>{help_caption}</b>"
        if self.field_examples is not None:
            help_html += "<br>Examples"
            for example in self.field_examples:
                help_html += f"<br>- {example}"
        return help_html

    async def has_help(self) -> bool:
        if self.field_description is not None:
            return self.enable_help
        if self.field_examples is not None:
            return self.enable_help
        return False

    # @property
    # def field_info(self) -> FieldInfo:
    #     return self._field_info

    async def render(self, field_mode: FieldMode, value: Any) -> None:
        # render frame
        await self.render_frame()

        # render field
        with self.view.get_element(name=f"field_{self.field_name}_frame"):
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
        frame = ui.card().classes("w-full")

        # add frame to view
        self.view.add_element(name=f"field_{self.field_name}_frame", element=frame)

    async def render_title(self) -> None:
        with ui.card_section().classes("p-0") as title_section:
            title_element = ui.label(text=self.field_title)

        # add title section to view
        self.view.add_element(name=f"field_{self.field_name}_title_section", element=title_section)

        # add title element to view
        self.view.add_element(name=f"field_{self.field_name}_title", element=title_element)

    @abstractmethod
    async def render_body(self, field_mode: FieldMode, value: Any) -> None:
        ...

    async def render_help(self) -> None:
        # get value element
        value_element = self.view.get_element(name=f"field_{self.field_name}_body")
        with value_element:
            with ui.tooltip():
                help_element = ui.html(self.field_help)

        # add help element to view
        self.view.add_element(name=f"field_{self.field_name}_help", element=help_element)

    @abstractmethod
    async def get_value(self) -> Any:
        ...

    async def on_change(self, event: UiEventArguments):
        await self.view.on_change(field_name=self.field_name,
                                  value=await self.get_value(),
                                  event=event)

    @abstractmethod
    async def set_validation_error(self, validation_error: list[dict[str, Any]]):
        ...
