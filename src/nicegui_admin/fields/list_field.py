from typing import Any, Optional, TYPE_CHECKING, Union

from nicegui import ui

from nicegui_admin.fields.base import BaseField, FieldMode

if TYPE_CHECKING:
    from nicegui_admin.views.field import FieldView
    from nicegui_admin.converter import Converter


class ListField(BaseField):
    enable_title = True
    enable_help = False

    def __init__(self,
                 parent: Union["FieldView", "BaseField"],
                 field_id: Union[str, int]):
        super().__init__(parent=parent,
                         field_id=field_id)

    async def render_body(self, field_mode: FieldMode, value: list[Any]) -> None:
        # initialize current fields
        [await self.add_element(field_mode=field_mode, value=v) for v in value]

        if field_mode == FieldMode.LIST:
            raise NotImplementedError("Not implemented")
        elif field_mode == FieldMode.GET:
            raise NotImplementedError("Not implemented")
        elif field_mode == FieldMode.SET:
            with ui.row().classes("w-full"):
                ui.space()
                ui.button("Add")
        else:
            raise ValueError(f"Invalid field mode: {field_mode}")

        # add value element to view
        # self.view.add_element(name=f"field_{self.field_name}_body", element=value_element)

    async def add_element(self, field_mode: FieldMode, value: Any) -> None:
        for field in self.sub_fields:
            # call field method
            field = field(parent=self,
                          field_id=self.field_id)

            # render field
            await field.render(field_mode=field_mode, value=value)

            # get value element
            with field.body_element:
                ui.button("Remove")
            field.body_element.style["flex-wrap"] = "nowrap"

            break
        print()

    async def get_value(self) -> list[Any]:
        print()

    async def set_validation_error(self, validation_error: list[dict[str, Any]]):
        print()
