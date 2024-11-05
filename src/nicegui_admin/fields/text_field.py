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
            value_element = ui.label(text=value)
        elif field_mode == FieldMode.SET:
            value_element = ui.input(label=self.field_title, value=value).classes("w-full")
            value_element.on("change", self.on_change).props("clearable")
            value_element.validation = {"test": lambda v: False}
        else:
            raise ValueError(f"Invalid field mode: {field_mode}")

        # add value element to view
        self.view.add_element(name=f"field_{self.field_name}_body", element=value_element)

    async def get_value(self) -> str:
        # get value element
        value_element: ui.input = self.view.get_element(f"field_{self.field_name}_body")

        # get value
        value = value_element.value

        # cast value to str
        value_str = str(value)

        return value_str

    async def set_validation_error(self, validation_error: list[dict[str, Any]]):
        print()
