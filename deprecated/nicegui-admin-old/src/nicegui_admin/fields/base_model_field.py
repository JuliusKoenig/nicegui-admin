from typing import Any, Optional, TYPE_CHECKING, Union

from nicegui_admin.fields.base import BaseField, FieldMode

if TYPE_CHECKING:
    from nicegui_admin.views.field import FieldView


class BaseModelField(BaseField):
    enable_title = True
    enable_help = False

    def __init__(self,
                 parent: Union["FieldView", "BaseField"],
                 field_id: Union[str, int]):
        super().__init__(parent=parent,
                         field_id=field_id)

        for field_id, field in self.sub_fields.items():
            # call field method
            field(parent=self, field_id=field_id)

    async def render_value(self, value: Optional[dict[str, Any]] = None) -> None:
        if self.view.current_field_mode == FieldMode.LIST:
            raise NotImplementedError("Not implemented")
        else:
            for field in self.current_fields:
                # get field value
                value = value[field.field_id]

                # render field
                await field.render(value=value)

    async def get_value(self) -> dict[str, Any]:
        data = {}
        for field in self.current_fields:
            # get value
            value = await field.get_value()
            # set value
            data[field.field_id] = value
        return data

    async def set_validation_error(self, validation_error: list[dict[str, Any]]):
        print()
