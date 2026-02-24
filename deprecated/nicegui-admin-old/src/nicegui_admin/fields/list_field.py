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

        self._add_button_element: Union[None, ui.button] = None

    @property
    def add_button_element(self) -> ui.button:
        if self._add_button_element is None:
            raise ValueError("Add button element not rendered")
        return self._add_button_element

    async def clear(self) -> None:
        await super().clear()
        self._add_button_element = None

    async def render(self, value: Optional[list[Any]] = None) -> None:
        await super().render(value=value)

        # initialize current fields
        [await self.add_element(value=v) for v in value]

        if self.view.current_field_mode == FieldMode.SET:
            await self.render_add_button()

    async def render_value(self, value: Optional[list[Any]] = None) -> None:
        ...

    async def render_add_button(self) -> None:
        with self.footer_element:
            ui.space()
            self._add_button_element = ui.button(icon="add")
            self.add_button_element.props("outline")
            self.add_button_element.classes("p-0")
            self.add_button_element.style["min-width"] = "0em"
            self.add_button_element.style["min-height"] = "0em"
            self.add_button_element.tooltip("Add")
            self.add_button_element.on("click", lambda e: self.add_element())

    async def render_remove_button(self, field: BaseField) -> None:
        with field.body_element:
            field.add_custom_element("remove_button", ui.button(icon="remove"))
            field.custom_elements["remove_button"].props("outline")
            field.custom_elements["remove_button"].props("color=negative")
            field.custom_elements["remove_button"].classes("p-0")
            field.custom_elements["remove_button"].style["min-width"] = "0em"
            field.custom_elements["remove_button"].style["min-height"] = "0em"
            field.custom_elements["remove_button"].tooltip("Remove")
            field.custom_elements["remove_button"].on("click", lambda e: self.remove_element(field=field))
        field.body_element.style["flex-wrap"] = "nowrap"

    async def add_element(self, value: Any = None) -> None:
        # get field class
        field_cls = self.sub_fields[0]
        if len(self.sub_fields) > 1:
            # TODO: support multiple field classes
            raise NotImplementedError("Multiple field classes not supported")

        # call field method
        field = field_cls(parent=self, field_id=self.field_id)

        # render field
        with self.body_element:
            await field.render(value=value)

        # draw remove button
        if self.view.current_field_mode == FieldMode.SET:
            await self.render_remove_button(field=field)

    async def remove_element(self, field: BaseField) -> None:
        self.frame_element.remove(field.frame_element)
        # await field.clear()

    async def get_value(self) -> list[Any]:
        print()

    async def set_validation_error(self, validation_error: list[dict[str, Any]]):
        print()
