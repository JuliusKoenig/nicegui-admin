from typing import Any, Callable

from nicegui import ui
from pydantic.fields import FieldInfo

from nicegui_admin.views.field import FieldView
from nicegui_admin.fields.base import BaseField, FieldMode


class BaseModelField(BaseField):
    enable_label_element = True

    def __init__(self, view: "FieldView", field_name: str, field_info: FieldInfo, field_methods: list[Callable[[FieldView], BaseField]]):
        super().__init__(view=view, field_name=field_name, field_info=field_info)

        self._current_fields: list["BaseField"] = []
        for field_method in field_methods:
            # call field method
            field = field_method(self.view)

            # append field
            self._current_fields.append(field)

    @property
    def current_fields(self) -> tuple["BaseField", ...]:
        if not self._current_fields:
            raise ValueError("Current fields are not set")
        return tuple(self._current_fields)

    async def render_value(self, field_mode: FieldMode, value: dict[str, Any]) -> ui.element:
        if field_mode == FieldMode.LIST:
            raise NotImplementedError("Not implemented")
        elif field_mode == FieldMode.GET or field_mode == FieldMode.SET:
            with ui.grid(columns=2) as value_element:
                for field in self.current_fields:
                    # get field value
                    value = value[field.field_name]

                    # render field in set mode
                    await field.render(field_mode=field_mode, value=value)
        else:
            raise ValueError(f"Invalid field mode: {field_mode}")
        return value_element

    async def get_value(self, value_element: ui.input) -> str:
        return value_element.value

    async def set_validation_error(self, validation_error: list[dict[str, Any]]):
        print()
