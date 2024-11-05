from typing import Any, Optional, TYPE_CHECKING

from nicegui_admin.views.field import FieldView
from nicegui_admin.fields.base import BaseField, FieldMode

if TYPE_CHECKING:
    from nicegui_admin.converter import CONVERTER_METHODS_RESULT


class BaseModelField(BaseField):
    enable_title = True
    enable_help = False

    def __init__(self,
                 view: "FieldView",
                 field_name: str,
                 field_methods: list["CONVERTER_METHODS_RESULT"],
                 field_title: Optional[str] = None,
                 field_description: Optional[str] = None,
                 field_examples: Optional[list[str]] = None):
        super().__init__(view=view,
                         field_name=field_name,
                         field_title=field_title,
                         field_description=field_description,
                         field_examples=field_examples)

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

    async def render_body(self, field_mode: FieldMode, value: dict[str, Any]) -> None:
        if field_mode == FieldMode.LIST:
            raise NotImplementedError("Not implemented")
        elif field_mode == FieldMode.GET or field_mode == FieldMode.SET:
            for field in self.current_fields:
                # get field value
                value = value[field.field_name]

                # render field
                await field.render(field_mode=field_mode, value=value)

            # get frame element as value element
            value_element = self.view.get_element(f"field_{self.field_name}_frame")
        else:
            raise ValueError(f"Invalid field mode: {field_mode}")

        # add value element to view
        self.view.add_element(name=f"field_{self.field_name}_body", element=value_element)

    async def get_value(self) -> dict[str, Any]:
        data = {}
        for field in self.current_fields:
            # get value
            value = await field.get_value()
            # set value
            data[field.field_name] = value
        return data

    async def set_validation_error(self, validation_error: list[dict[str, Any]]):
        print()
