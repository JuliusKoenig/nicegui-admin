from typing import Any, Optional, TYPE_CHECKING

from nicegui import ui

from nicegui_admin.fields.base import BaseField, FieldMode

if TYPE_CHECKING:
    from nicegui_admin.views.field import FieldView
    from nicegui_admin.converter import Converter


class ListField(BaseField):
    enable_title = True
    enable_help = False

    def __init__(self,
                 view: "FieldView",
                 field_name: str,
                 parent: Optional["BaseField"] = None,
                 field_title: Optional[str] = None,
                 field_description: Optional[str] = None,
                 field_examples: Optional[list[str]] = None):
        super().__init__(view=view,
                         field_name=field_name,
                            parent=parent,
                         field_title=field_title,
                         field_description=field_description,
                         field_examples=field_examples)

        self._current_fields: list["BaseField"] = []

    @property
    def current_fields(self) -> tuple["BaseField", ...]:
        if not self._current_fields:
            raise ValueError("Current fields are not set")
        return tuple(self._current_fields)

    async def render_body(self, field_mode: FieldMode, value: list[Any]) -> None:
        # initialize current fields
        [await self.add_element(v) for v in value]

        if field_mode == FieldMode.LIST:
            raise NotImplementedError("Not implemented")
        elif field_mode == FieldMode.GET:
            raise NotImplementedError("Not implemented")
        elif field_mode == FieldMode.SET:
            ui.button("Add")
        else:
            raise ValueError(f"Invalid field mode: {field_mode}")

        # add value element to view
        # self.view.add_element(name=f"field_{self.field_name}_body", element=value_element)

    async def add_element(self, value: Any) -> None:
        for field in self.sub_fields:
            # call field method
            field = field(view=self.view,
                          field_name=str(len(self._current_fields)),
                          parent=self)

            print()
        print()

    async def get_value(self) -> list[Any]:
        print()

    async def set_validation_error(self, validation_error: list[dict[str, Any]]):
        print()
