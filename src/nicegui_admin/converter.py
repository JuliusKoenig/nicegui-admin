import inspect
from abc import ABCMeta
from typing import Optional, Union

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from nicegui_admin.fields.base import BaseField
from nicegui_admin.fields.text_field import TextField

_CONVERTER_METHODS: dict[type, callable] = {}


def register_field_converter(types: Union[type, list[type]]):
    if not isinstance(types, list):
        types = [types]

    def decorator(func):
        global _CONVERTER_METHODS

        # get func signature
        signature = inspect.signature(func)

        # check if func takes a str for field_name and a FieldInfo for field_info
        takes_field_name = None
        takes_field_info = None
        for i, param in enumerate(signature.parameters.values()):
            if param.kind == param.VAR_POSITIONAL:
                takes_field_name = i
                takes_field_info = i + 1
                break
            if param.annotation == str:
                takes_field_name = i
            if param.annotation == FieldInfo:
                takes_field_info = i
        if takes_field_name is None:
            raise ValueError("Function must take a str for field_name")
        if takes_field_info is None:
            raise ValueError("Function must take a FieldInfo for field_info")
        if takes_field_info < takes_field_name:
            raise ValueError("FieldInfo parameter must come after field_name parameter")

        # check if type is already registered
        for _type in types:
            if _type in _CONVERTER_METHODS:
                raise ValueError(f"Type '{_type}' is already registered")

            # register type
            _CONVERTER_METHODS[_type] = func

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

    def __init__(self, model: type[BaseModel]):
        self.model = model

    def convert_fields(self) -> list[BaseField]:
        converted_fields = []
        for field_name, field in self.model.model_fields.items():
            # get converter method
            converter_method = self.get_converter_method(field.annotation)
            if converter_method is None:
                raise NotImplementedError(f"Converter method for type '{field.annotation}' not found")

            # call converter method
            converted_field = converter_method(self, *(field_name, field))

            # check if converted_field is a BaseField
            if not isinstance(converted_field, BaseField):
                raise ValueError(f"Converter method for type '{field.annotation}' must return a BaseField")

            # append converted_field
            converted_fields.append(converted_field)

        return converted_fields

    def get_converter_method(self, type_: type) -> Optional[callable]:
        return self._converter_methods.get(type_)

    @register_field_converter(str)
    def text_field_converter(self, field_name: str, field_info: FieldInfo):
        if field_info.annotation == str:
            return TextField(field_info=field_info)
        return None