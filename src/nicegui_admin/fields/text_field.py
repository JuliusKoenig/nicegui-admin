from nicegui import ui

from nicegui_admin.fields.base import BaseField


class TextField(BaseField):
    async def render_list(self, value: str) -> ui.element:
        raise NotImplementedError("Not implemented")

    async def render_get(self, value: str) -> tuple[ui.element, ui.element]:
        label_label = ui.label(text=await self.get_title())
        value_label = ui.label(text=value)
        return label_label, value_label

    async def render_set(self, value: str) -> tuple[ui.element, ui.element]:
        label_label = ui.label(text=await self.get_title())
        value_input = ui.input(value=value)
        return label_label, value_input
