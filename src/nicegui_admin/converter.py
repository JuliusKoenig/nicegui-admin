import inspect
from abc import ABCMeta
from types import GenericAlias
from typing import Optional, Union, Callable, Any

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from nicegui_admin.fields.base import BaseField
from nicegui_admin.fields.base_model_field import BaseModelField
from nicegui_admin.fields.list_field import ListField
from nicegui_admin.fields.text_field import TextField
from nicegui_admin.views.field import FieldView

_CONVERTER_METHODS: dict[type, callable] = {}

# view: FieldView -> BaseField
CONVERTER_METHODS_RESULT = Callable[[FieldView], BaseField]

# field_name: str, field_annotation: type, field_title: Optional[str], field_description: Optional[str], field_examples: Optional[list[Any]] -> CONVERTER_METHODS_RESULT
CONVERTER_METHODS_SIGNATURE = Callable[["Converter", str, type, Optional[str], Optional[str], Optional[list[Any]]], CONVERTER_METHODS_RESULT]


def register_field_converter(types: Union[type, list[type]]):
    if not isinstance(types, list):
        types = [types]

    def decorator(func):
        global _CONVERTER_METHODS

        # get func signature
        signature = inspect.signature(func)

        # check if func takes a str for field_name and a FieldInfo for field_info
        takes_field_name = False
        takes_field_annotation = False
        for param_name, param in signature.parameters.items():
            if param_name == "field_name":
                if param.annotation is not str:
                    raise ValueError("Function must take a str for field_name")
                takes_field_name = True
            if param_name == "field_annotation":
                if param.annotation is not type:
                    raise ValueError("Function must take a type for field_annotation")
                takes_field_annotation = True

        if takes_field_name is None:
            raise ValueError("Function must take a str for field_name")
        if takes_field_annotation is None:
            raise ValueError("Function must take a type for field_annotation")

        # check if type is already registered
        for _type in types:
            if _type in _CONVERTER_METHODS:
                raise ValueError(f"Type '{_type}' is already registered")

            # register type
            _CONVERTER_METHODS[_type] = func

        # # add type to func
        # func.nicegui_admin_field_converter_types = types

        return func

    return decorator


class ConverterMeta(ABCMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        global _CONVERTER_METHODS

        # create cls
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # get _converter_methods
        converter_methods = namespace.get("_converter_methods", {})

        # add all from global _CONVERTER_METHODS
        for type_, func in _CONVERTER_METHODS.items():
            if type_ in converter_methods:
                raise ValueError(f"Type '{type_}' is already registered")
            converter_methods[type_] = func

        # empty global _CONVERTER_METHODS
        _CONVERTER_METHODS = {}

        # add all from base classes
        for base in bases:
            if not issubclass(base, Converter):
                continue
            base_converter_methods = getattr(base, "_converter_methods", {})
            for type_, func in base_converter_methods.items():
                if type_ in converter_methods:
                    continue
                converter_methods[type_] = func

        # set _converter_methods
        cls._converter_methods = converter_methods

        return cls


class Converter(metaclass=ConverterMeta):
    _converter_methods: dict[type, callable]

    def __init__(self):
        ...

    def convert_fields(self, model: type[BaseModel]) -> list[Callable[[FieldView], BaseField]]:
        converted_fields = []
        for field_name, field_info in model.model_fields.items():
            field_info: FieldInfo

            # get converter method
            converter_method = self.get_converter_method(field_info.annotation)
            if converter_method is None:
                raise NotImplementedError(f"Converter method for type '{field_info.annotation}' not found")

            # call converter method
            converted_field = converter_method(self, **{"field_name": field_name,
                                                        "field_annotation": field_info.annotation,
                                                        "field_title": field_info.title,
                                                        "field_description": field_info.description,
                                                        "field_examples": field_info.examples})

            # check if converted_field is a callable
            if not callable(converted_field):
                raise ValueError(f"Converter method for type '{field_info.annotation}' must return a callable")

            # append converted_field
            converted_fields.append(converted_field)

        return converted_fields

    @classmethod
    def _is_list(cls, type_: type) -> bool:
        if issubclass(type_, list):
            return True
        elif issubclass(type(type_), GenericAlias):
            if getattr(type_, '__origin__', None) is list:
                return True
        return False

    def get_converter_method(self, type_: type) -> Optional[CONVERTER_METHODS_SIGNATURE]:
        if self._is_list(type_):  # check if type_ is a kind of list
            return self._converter_methods.get(list)
        elif issubclass(type_, BaseModel):  # check if type_ is a subclass of BaseModel
            return self._converter_methods.get(BaseModel)
        return self._converter_methods.get(type_)

    @register_field_converter(str)
    def text_field_converter(self,
                             field_name: str,
                             field_annotation: type,
                             field_title: Optional[str] = None,
                             field_description: Optional[str] = None,
                             field_examples: Optional[list[str]] = None) -> CONVERTER_METHODS_RESULT:
        # check if field_annotation is str
        if field_annotation is not str:
            raise ValueError(f"Invalid type '{field_annotation}'")

        return lambda view: TextField(view=view,
                                      field_name=field_name,
                                      field_title=field_title,
                                      field_description=field_description,
                                      field_examples=field_examples)

    @register_field_converter(list)
    def list_field_converter(self,
                             field_name: str,
                             field_annotation: type,
                             field_title: Optional[str] = None,
                             field_description: Optional[str] = None,
                             field_examples: Optional[list[str]] = None) -> CONVERTER_METHODS_RESULT:
        args = None
        if issubclass(field_annotation, list):
            args = tuple(Any)
        elif issubclass(type(field_annotation), GenericAlias) and getattr(field_annotation, '__origin__', None) is list:
            # get args
            args = getattr(field_annotation, '__args__', None)
            if len(args) == 0:
                args = tuple(Any)
            else:
                args = tuple(args)
        if args is None:
            raise ValueError(f"Invalid type '{field_annotation}'")

        # get converter methods for args
        converter_methods = []
        for arg in args:
            converter_method = self.get_converter_method(arg)
            if converter_method is None:
                raise NotImplementedError(f"Converter method for type '{arg}' not found")
            converter_methods.append(converter_method)

        return lambda view: ListField(view=view,
                                      field_name=field_name,
                                      converter=self,
                                      converter_methods=converter_methods,
                                      field_title=field_title,
                                      field_description=field_description,
                                      field_examples=field_examples)

    @register_field_converter(BaseModel)
    def base_model_field_converter(self,
                                   field_name: str,
                                   field_annotation: type,
                                   field_title: Optional[str] = None,
                                   field_description: Optional[str] = None,
                                   field_examples: Optional[list[str]] = None) -> CONVERTER_METHODS_RESULT:
        # get model
        model = field_annotation
        if not issubclass(model, BaseModel):
            raise ValueError(f"Model '{model}' must be a subclass of BaseModel")

        # get field_methods from model
        field_methods = self.convert_fields(model=model)

        return lambda view: BaseModelField(view=view,
                                           field_name=field_name,
                                           field_methods=field_methods,
                                           field_title=field_title,
                                           field_description=field_description,
                                           field_examples=field_examples)
