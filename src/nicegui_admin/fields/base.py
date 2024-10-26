from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

from nicegui import ui
from nicegui.events import UiEventArguments

from pydantic.fields import FieldInfo

from nicegui_admin.views.field import FieldView


class FieldMode(Enum):
    LIST = "list"
    GET = "get"
    SET = "set"


class BaseField(ABC):
    enable_label_element: bool = True

    def __init__(self, view: "FieldView", field_name: str, field_info: FieldInfo):
        assert isinstance(view, FieldView), f"view must be a FieldView, not {type(view)}"
        assert isinstance(field_name, str), f"field_name must be a str, not {type(field_name)}"
        assert isinstance(field_info, FieldInfo), f"field_info must be a FieldInfo, not {type(field_info)}"
        self._view = view
        self._field_name = field_name
        self._field_info = field_info

    @property
    def view(self) -> "FieldView":
        return self._view

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def field_info(self) -> FieldInfo:
        return self._field_info

    async def render(self, field_mode: FieldMode, value: Any) -> None:
        if not self.enable_label_element:
            ui.space()
        else:
            # render label
            label_element = await self.render_label()

            # add label element to view
            self.view.add_element(name=f"field_{self.field_name}_label", element=label_element)

            # add help to label element
            if await self.has_help():
                with label_element:
                    # render help
                    help_element = await self.render_help()

                    # add help element to view
                    self.view.add_element(name=f"field_{self.field_name}_label_help", element=help_element)

        # render value field
        value_element = await self.render_value(field_mode=field_mode, value=value)

        # add value element to view
        self.view.add_element(name=f"field_{self.field_name}_value", element=value_element)

        # add help to value element
        if await self.has_help():
            with value_element:
                # render help
                help_element = await self.render_help()

                # add help element to view
                self.view.add_element(name=f"field_{self.field_name}_value_help", element=help_element)

    async def get_title(self) -> str:
        title = self.field_info.title
        if title is None:
            title = self.field_name
        return title

    async def render_label(self) -> Optional[ui.label]:
        return ui.label(text=await self.get_title())

    @abstractmethod
    async def render_value(self, field_mode: FieldMode, value: Any) -> ui.element:
        ...

    async def has_help(self) -> bool:
        if self.field_info.description is not None:
            return True
        if self.field_info.examples is not None:
            return True
        return False

    async def render_help(self) -> ui.html:
        if self.field_info.description is not None:
            help_caption = self.field_info.description
        else:
            help_caption = self.field_name
        help_html = f"<b>{help_caption}</b>"
        if self.field_info.examples is not None:
            help_html += "<br>Examples"
            for example in self.field_info.examples:
                help_html += f"<br>- {example}"

        with ui.tooltip():
            help_element = ui.html(help_html)

        return help_element

    @abstractmethod
    async def get_value(self, value_element: ui.element) -> Any:
        ...

    async def on_change(self, event: UiEventArguments):
        await self.view.on_change(field_name=self.field_name,
                                  value=await self.get_value(event.sender),
                                  event=event)

    @abstractmethod
    async def set_validation_error(self, validation_error: list[dict[str, Any]]):
        ...
