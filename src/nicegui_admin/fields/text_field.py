from typing import Any

from nicegui import ui

from nicegui_admin.fields.base import BaseField, FieldMode


class TextField(BaseField):
    enable_title = False
    enable_help = True

    async def render_body(self, field_mode: FieldMode, value: str) -> None:
        if field_mode == FieldMode.LIST:
            raise NotImplementedError("Not implemented")
        elif field_mode == FieldMode.GET:
            self._body = ui.label(text=value)
        elif field_mode == FieldMode.SET:
            self._body = ui.input(label=self.field_title, value=value).classes("w-full")
            self.body.on("change", self.on_change).props("clearable")
            self.body.validation = {"test": lambda v: False}
        else:
            raise ValueError(f"Invalid field mode: {field_mode}")

    async def get_value(self) -> str:
        # get value element
        value_element: ui.input = self.body

        # get value
        value = value_element.value

        # cast value to str
        value_str = str(value)

        return value_str

    async def set_validation_error(self, validation_error: list[dict[str, Any]]):
        print()
