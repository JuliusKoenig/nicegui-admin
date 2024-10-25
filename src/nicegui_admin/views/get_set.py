from abc import abstractmethod
from enum import Enum
from typing import Optional

from nicegui import ui
from pydantic import BaseModel

from nicegui_admin.converter import Converter
from nicegui_admin.fields.base import BaseField
from nicegui_admin.views.base import BaseViewMeta, BaseView
from nicegui_admin.layouts.base import BaseLayout


class GetSetViewMeta(BaseViewMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        # create cls
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # check if cls is abstract
        if cls._abstract:
            return cls

        # if converter is not set, use default converter
        view_converter = namespace.get("converter")
        if view_converter is None:
            view_converter = Converter

        # set view converter
        cls.converter = view_converter

        # if get_model is not set, raise error
        view_get_model = namespace.get("get_model")
        if view_get_model is None:
            raise ValueError(f"get_model must be set in {cls}")

        # set view get model
        cls.get_model = view_get_model

        # if set_model is not set, use get_model
        view_set_model = namespace.get("set_model")
        if view_set_model is None:
            view_set_model = view_get_model

        # set view set model
        cls.set_model = view_set_model

        # convert view get model fields
        view_get_model_fields = mcs.convert_view_fields(model=view_get_model, converter=view_converter)

        # set view get model fields
        cls._get_model_fields = view_get_model_fields

        # convert view set model fields
        view_set_model_fields = mcs.convert_view_fields(model=view_set_model, converter=view_converter)

        # set view set model fields
        cls._set_model_fields = view_set_model_fields

        return cls

    @classmethod
    def get_normalized_view_path_and_path_parameters(mcs, view_path: str) -> tuple[str, dict[str, bool]]:
        if not view_path.endswith("/{action}") or view_path.endswith("/{action}/"):
            view_path += "/{action}"
        return super().get_normalized_view_path_and_path_parameters(view_path=view_path)

    @classmethod
    def convert_view_fields(mcs, model: type[BaseModel], converter: type[Converter]):  # ToDo: add return type
        converter_instance = converter(model=model)
        return converter_instance.convert_fields()

class GetSetViewActions(Enum):
    GET = "get"
    SET = "set"


class GetSetView(BaseView, metaclass=GetSetViewMeta):
    # user defined variables
    converter: type[Converter]
    get_model: type[BaseModel]
    set_model: type[BaseModel]

    # internal variables
    _get_model_fields: list[BaseField]
    _set_model_fields: list[BaseField]



    def __init__(self,
                 layout: BaseLayout):
        super().__init__(layout=layout)

        self._current_action: Optional[GetSetViewActions] = None

    @property
    def current_action(self) -> GetSetViewActions:
        if self._current_action is None:
            raise ValueError("Current action is not set")
        return self._current_action

    async def render(self, action: GetSetViewActions):
        if action == GetSetViewActions.GET:
            # set current action
            self._current_action = action
            # get model
            model = await self.get()
            # render get
            await self.render_get(model=model)
        elif action == GetSetViewActions.SET:
            # set current action
            self._current_action = action
            # get model
            model = await self.get()
            # render set
            await self.render_set(model=model)
        else:
            raise ValueError(f"Invalid action: {action}")

    async def render_get(self, model: BaseModel):
        with ui.grid(columns=2):
            for field in self._get_model_fields:
                # get field value
                value = getattr(model, field.field_name)
                # render field
                label_element, value_element = await field.render_get(value=value)
                # add elements to view
                if label_element is not None:
                    self.add_element(name=f"field_{field.field_name}_label", element=label_element)
                if value_element is not None:
                    self.add_element(name=f"field_{field.field_name}_value", element=value_element)

    async def render_set(self, model: BaseModel):
        with ui.grid(columns=2):
            for field in self._set_model_fields:
                # get field value
                value = getattr(model, field.field_name)
                # render field
                label_element, value_element = await field.render_set(value=value)
                # add elements to view
                if label_element is not None:
                    self.add_element(name=f"field_{field.field_name}_label", element=label_element)
                if value_element is not None:
                    self.add_element(name=f"field_{field.field_name}_value", element=value_element)

    @abstractmethod
    async def get(self) -> BaseModel:
        ...

    @abstractmethod
    async def set(self, value: BaseModel) -> None:
        ...
