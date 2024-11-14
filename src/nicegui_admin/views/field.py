from abc import abstractmethod
from typing import Callable, Optional, Any, TYPE_CHECKING
from types import MappingProxyType

from fastapi.dependencies.utils import ModelField, analyze_param
from pydantic import BaseModel
from nicegui import ui
from nicegui.events import UiEventArguments

from nicegui_admin.layouts.base import BaseLayout
from nicegui_admin.views.base import BaseView, BaseViewMeta
from nicegui_admin.converter import Converter

if TYPE_CHECKING:
    from nicegui_admin.fields.base import FieldMode, BaseField


class FieldViewMeta(BaseViewMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        # create cls
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # check if cls is abstract
        if cls._abstract:
            return cls

        # if field_margin is not set, set it to 4
        field_margin = namespace.get("field_margin")
        if field_margin is None:
            field_margin = 4
        cls.field_margin = field_margin

        # if converter is not set, use default converter
        view_converter = namespace.get("converter")
        if view_converter is None:
            view_converter = Converter

        # set view converter
        cls.converter = view_converter()

        return cls


class FieldView(BaseView, metaclass=FieldViewMeta):
    # user defined
    field_margin: int

    # internal
    converter: Converter

    def __init__(self,
                 layout: BaseLayout):
        super().__init__(layout=layout)

        self._current_fields: list["BaseField"] = []
        self._current_model: Optional[type[BaseModel]] = None
        self._current_model_validator: Optional[ModelField] = None
        self._current_data: Optional[dict] = None

    @property
    def current_fields(self) -> tuple["BaseField", ...]:
        return tuple(self._current_fields)

    @property
    def current_model(self) -> type[BaseModel]:
        if self._current_model is None:
            raise ValueError("Current model is not set")
        return self._current_model

    @property
    def current_data(self) -> MappingProxyType[str, Any]:
        if self._current_data is None:
            raise ValueError("Current data is not set")
        return MappingProxyType(self._current_data)

    async def init_fields(self, fields: dict[str, type["BaseField"]], current_model: type[BaseModel], current_data: dict[str, Any]):
        # set loader text
        await self.layout.loader("log", "Initializing fields")

        # initialize current fields
        self._current_fields = []

        # set current model
        self._current_model = current_model

        # analyze model
        self._current_model_validator = analyze_param(
            param_name="model",
            annotation=self.current_model,
            value=None,
            is_path_param=False,
        ).field

        # set current data
        self._current_data = current_data

        for field_id, field in fields.items():
            # call field method
            field(parent=self, field_id=field_id)

    def add_field(self, field: "BaseField"):
        if field in self._current_fields:
            raise ValueError(f"Field {field} is already added")
        self._current_fields.append(field)

    async def render_fields(self, field_mode: "FieldMode"):
        for i, field in enumerate(self.current_fields):
            # get field value
            value = self.current_data[field.field_id]

            # render field
            await field.render(field_mode=field_mode, value=value)
            if i < len(self.current_fields) - 1:
                await self.render_field_separator()
        await self.render_field_separator()

    async def render_field_separator(self) -> ui.separator:
        return ui.separator().classes(f"mb-{self.field_margin}")

    async def on_change(self, field_name: str, value: Any, event: UiEventArguments):
        # copy current data
        current_data = self.current_data.copy()

        # set value
        current_data[field_name] = value

        # parse current data
        current_data_model, validation_errors = await self.parse_current_data(current_data)

        # set validation errors

        print()

    async def parse_current_data(self, current_data: dict[str, Any]) -> tuple[BaseModel, Optional[list[dict[str, Any]]]]:
        return self._current_model_validator.validate(current_data)
