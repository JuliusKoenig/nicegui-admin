from abc import abstractmethod
from enum import Enum
from typing import Optional, Any, Callable

from nicegui import ui
from pydantic import BaseModel

from nicegui_admin.converter import Converter
from nicegui_admin.fields.base import BaseField, FieldMode
from nicegui_admin.layouts.base import BaseLayout
from nicegui_admin.views.field import FieldViewMeta, FieldView


class GetSetViewMeta(FieldViewMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        # set allow_path_parameter_defaults to True
        namespace["allow_path_parameter_defaults"] = True

        # create cls
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # check if cls is abstract
        if FieldView in bases:
            cls._abstract = True
            return cls
        cls._abstract = False
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
    def convert_view_fields(mcs, model: type[BaseModel], converter: type[Converter]) -> list[Callable[[FieldView], BaseField]]:
        converter_instance = converter()
        return converter_instance.convert_fields(model=model)


class GetSetViewActions(Enum):
    GET = "get"
    SET = "set"


class GetSetView(FieldView, metaclass=GetSetViewMeta):
    # user defined variables
    converter: type[Converter]
    get_model: type[BaseModel]
    set_model: type[BaseModel]

    # internal variables
    _get_model_fields: list[Callable[[FieldView], BaseField]]
    _set_model_fields: list[Callable[[FieldView], BaseField]]

    def __init__(self,
                 layout: BaseLayout):
        super().__init__(layout=layout)

        self._current_action: Optional[GetSetViewActions] = None
        # self._current_data: Optional[BaseModel] = None

    @property
    def current_action(self) -> GetSetViewActions:
        if self._current_action is None:
            raise ValueError("Current action is not set")
        return self._current_action

    # @property
    # def current_data(self) -> BaseModel:
    #     if self._current_data is None:
    #         raise ValueError("Current data is not set")
    #     return self._current_data.model_copy()
    #
    # @current_data.setter
    # def current_data(self, data: BaseModel):
    #     self._current_data = data.model_copy()

    async def render(self, action: GetSetViewActions = GetSetViewActions.GET):
        if action == GetSetViewActions.GET:
            # initialize current fields
            await self.init_fields(field_methods=self._get_model_fields,
                                   current_model=self.get_model,
                                   current_data=await self.get())

            # set current action
            self._current_action = action

            # render get
            await self.render_get()
        elif action == GetSetViewActions.SET:
            # initialize current fields
            await self.init_fields(field_methods=self._set_model_fields,
                                   current_model=self.set_model,
                                   current_data=await self.get())

            # set current action
            self._current_action = action

            # render set
            await self.render_set()
        else:
            raise ValueError(f"Invalid action: {action}")

    async def render_get(self):
        # render fields
        await self.render_fields(field_mode=FieldMode.GET)

    async def render_set(self):
        # render fields
        await self.render_fields(field_mode=FieldMode.SET)

        # render controls
        with ui.row().classes("w-full"):
            ui.space()

            # render cancel button
            cancel_button = ui.button(text="Cancel", on_click=self.cancel, icon="close").props("color=negative")
            self.add_element(name="cancel_button", element=cancel_button)

            # render submit button
            submit_button = ui.button(text="Submit", on_click=self.submit, icon="check").props("color=positive")
            self.add_element(name="submit_button", element=submit_button)

    async def submit(self, event):
        data = {}
        for field in self.current_fields:
            # get value
            value = await field.get_value()
            # set value
            data[field.field_name] = value

        # set model
        await self.set(data=data)

    async def cancel(self, event):
        print()

    @abstractmethod
    async def get(self) -> dict[str, Any]:
        ...

    # async def parse_set_model(self, **data: dict[str, Any]) -> BaseModel:
    #     set_model = self.set_model(**data)
    #     return set_model

    @abstractmethod
    async def set(self, data: dict[str, Any]) -> None:
        ...
