from typing import Any

from nicegui import ui
from typing_extensions import Optional

from nicegui_admin.fields.base import BaseField, FieldMode


class TextField(BaseField):
    enable_title = False
    enable_help = True

    async def render_value(self, value: Optional[str] = None) -> None:
        if self.view.current_field_mode == FieldMode.LIST:
            raise NotImplementedError("Not implemented")
        elif self.view.current_field_mode == FieldMode.GET:
            self._value_element = ui.label(text=value)
        elif self.view.current_field_mode == FieldMode.SET:
            self._value_element = ui.input(label=self.field_title, value=value).classes("w-full")
            self.value_element.on("change", self.on_change).props("clearable")
            self.value_element.validation = {"test": lambda v: False}

    async def get_value(self) -> str:
        # get value element
        value_element: ui.input = self.value_element

        # get value
        value = value_element.value

        # cast value to str
        value_str = str(value)

        return value_str

    async def set_validation_error(self, validation_error: list[dict[str, Any]]):
        print()
