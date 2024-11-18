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
        view_get_model_fields = cls.converter.convert_fields(model=view_get_model)

        # set view get model fields
        cls._get_model_fields = view_get_model_fields

        # convert view set model fields
        view_set_model_fields = cls.converter.convert_fields(model=view_set_model)

        # set view set model fields
        cls._set_model_fields = view_set_model_fields

        return cls

    @classmethod
    def get_normalized_view_path_and_path_parameters(mcs, view_path: str) -> tuple[str, dict[str, bool]]:
        if not view_path.endswith("/{action}") or view_path.endswith("/{action}/"):
            view_path += "/{action}"
        return super().get_normalized_view_path_and_path_parameters(view_path=view_path)


class GetSetViewActions(Enum):
    GET = "get"
    SET = "set"


class GetSetView(FieldView, metaclass=GetSetViewMeta):
    # user defined variables
    converter: type[Converter]
    get_model: type[BaseModel]
    set_model: type[BaseModel]

    # internal variables
    _get_model_fields: dict[str, type[BaseField]]
    _set_model_fields: dict[str, type[BaseField]]

    def __init__(self,
                 layout: BaseLayout):
        super().__init__(layout=layout)

        self._current_action: Optional[GetSetViewActions] = None
        # self._current_data: Optional[BaseModel] = None
        self._cancel_button_element: Optional[ui.button] = None
        self._submit_and_continue_button_element: Optional[ui.button] = None
        self._submit_button_element: Optional[ui.button] = None

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

    @property
    def cancel_button_element(self) -> ui.button:
        if self._cancel_button_element is None:
            raise ValueError("Cancel button is not rendered")
        return self._cancel_button_element

    @property
    def submit_and_continue_button_element(self) -> ui.button:
        if self._submit_and_continue_button_element is None:
            raise ValueError("Submit and continue button is not rendered")
        return self._submit_and_continue_button_element

    @property
    def submit_button_element(self) -> ui.button:
        if self._submit_button_element is None:
            raise ValueError("Submit button is not rendered")
        return self._submit_button_element

    async def render(self, action: GetSetViewActions = GetSetViewActions.GET):
        # set current action
        self._current_action = action

        if action == GetSetViewActions.GET:
            # initialize current fields
            await self.init_fields(fields=self._get_model_fields,
                                   current_model=self.get_model,
                                   current_data=await self.get())

            # render get
            await self.render_get()
        elif action == GetSetViewActions.SET:
            # initialize current fields
            await self.init_fields(fields=self._set_model_fields,
                                   current_model=self.set_model,
                                   current_data=await self.get())

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
            self._cancel_button_element = ui.button(text="Cancel", on_click=self.cancel, icon="close")
            self.cancel_button_element.props("outline")
            self.cancel_button_element.props("color=negative")

            # render submit and continue button
            self._submit_and_continue_button_element = ui.button(text="Submit and Continue", on_click=self.submit, icon="check")
            self.submit_and_continue_button_element.props("outline")
            self.submit_and_continue_button_element.props("color=positive")

            # render submit button
            self._submit_button_element = ui.button(text="Submit", on_click=self.submit, icon="check")
            self.submit_button_element.props("color=positive")

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
