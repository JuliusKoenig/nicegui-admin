from abc import abstractmethod
from typing import Callable, Optional, Any, TYPE_CHECKING
from types import MappingProxyType

from fastapi.dependencies.utils import ModelField, analyze_param
from pydantic import BaseModel
from nicegui.events import UiEventArguments

from nicegui_admin.layouts.base import BaseLayout
from nicegui_admin.views.base import BaseView, BaseViewMeta
if TYPE_CHECKING:
    from nicegui_admin.fields.base import BaseField


class FieldViewMeta(BaseViewMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        # create cls
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        return cls


class FieldView(BaseView, metaclass=FieldViewMeta):
    def __init__(self,
                 layout: BaseLayout):
        super().__init__(layout=layout)

        self._current_fields: list["BaseField"] = []
        self._current_model: Optional[type[BaseModel]] = None
        self._current_model_validator: Optional[ModelField] = None
        self._current_data: Optional[dict] = None

    @property
    def current_fields(self) -> tuple["BaseField", ...]:
        if not self._current_fields:
            raise ValueError("Current fields are not set")
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

    async def init_fields(self, field_methods: list[Callable[["FieldView"], "BaseField"]], current_model: type[BaseModel], current_data: dict[str, Any]):
        # initialize current fields
        self._current_fields = []

        # set loader text
        await self.layout.loader("log", "Initializing fields")

        for field_method in field_methods:
            # call field method
            field = field_method(self)

            # append field
            self._current_fields.append(field)

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


