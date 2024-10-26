from typing import Any

from nicegui import ui

from nicegui_admin.fields.base import BaseField, FieldMode


class TextField(BaseField):
    enable_label_element = False

    async def render_value(self, field_mode: FieldMode, value: str) -> ui.element:
        if field_mode == FieldMode.LIST:
            raise NotImplementedError("Not implemented")
        elif field_mode == FieldMode.GET:
            value_element = ui.label(text=value)
        elif field_mode == FieldMode.SET:
            value_element = ui.input(label=await self.get_title(), value=value)
            value_element.on("change", self.on_change).props("clearable")
            value_element.validation = {"test": lambda v: False}
        else:
            raise ValueError(f"Invalid field mode: {field_mode}")
        return value_element

    async def get_value(self, value_element: ui.input) -> str:
        return value_element.value

    async def set_validation_error(self, validation_error: list[dict[str, Any]]):
        print()
