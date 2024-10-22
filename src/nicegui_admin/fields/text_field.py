from nicegui import ui

from nicegui_admin.fields.base import BaseField


class TextField(BaseField):
    ui_element_list: ui.label
    ui_element_get: ui.label
    ui_element_set: ui.input

    def render(self, mode: BaseField.Mode, *args, **kwargs) -> ui.element:
        print()
