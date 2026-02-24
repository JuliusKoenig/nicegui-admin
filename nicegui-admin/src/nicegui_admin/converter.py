from abc import ABCMeta
from types import GenericAlias
from typing import Union, Any

from pydantic import BaseModel

from nicegui_admin.fields.base import BaseField
from nicegui_admin.fields.base_model_field import BaseModelField
from nicegui_admin.fields.list_field import ListField
from nicegui_admin.fields.text_field import TextField

_CONVERTER_METHODS: dict[type, callable] = {}



def register_field_converter(types: Union[type, list[type]]):
    if not isinstance(types, list):
        types = [types]

    def decorator(func):
        global _CONVERTER_METHODS

        # # get func signature
        # signature = inspect.signature(func)
        #
        # # check if func takes a str for field_name and a FieldInfo for field_info
        # takes_field_name = False
        # takes_field_annotation = False
        # for param_name, param in signature.parameters.items():
        #     if param_name == "field_name":
        #         if param.annotation is not str:
        #             raise ValueError("Function must take a str for field_name")
        #         takes_field_name = True
        #     if param_name == "field_annotation":
        #         if param.annotation is not type:
        #             raise ValueError("Function must take a type for field_annotation")
        #         takes_field_annotation = True
        #
        # if takes_field_name is None:
        #     raise ValueError("Function must take a str for field_name")
        # if takes_field_annotation is None:
        #     raise ValueError("Function must take a type for field_annotation")

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

    def convert_fields(self, model: type[BaseModel]) -> dict[str, type[BaseField]]:
        # convert fields
        converted_fields = {}
        for field_name, field_info in model.model_fields.items():
            converted_fields[field_name] = self.convert_field(annotation=field_info.annotation)

        return converted_fields

    def convert_field(self, annotation: type) -> type[BaseField]:
        # get field type
        annotation_base = annotation
        if self._is_list(annotation_base):  # check if type_ is a kind of list
            annotation_base = list
        elif issubclass(annotation_base, BaseModel):  # check if type_ is a subclass of BaseModel
            annotation_base = BaseModel
        converter_method = self._converter_methods.get(annotation_base)
        if converter_method is None:
            raise NotImplementedError(f"Converter method for type '{annotation_base}' not found")

        # get field_type_base
        result = converter_method(self=self, annotation=annotation)

        # check if result is a tuple
        if isinstance(result, tuple):
            field_type_base, sub_fields = result
        else:
            field_type_base = result
            sub_fields = None

        # check if field_type is a subclass of BaseField
        if not issubclass(field_type_base, BaseField):
            raise ValueError(f"Converter method for type '{annotation}' must return a subclass of '{BaseField.__name__}'")

        # create dynamic field type
        field_type = type(field_type_base.__name__,
                          (field_type_base,),
                          {"abstract": False,
                           "field_annotation": annotation,
                           "sub_fields": sub_fields})

        # check if field_type is a subclass of BaseModelField
        if not issubclass(field_type, BaseField):
            raise ValueError(f"Converter method for type '{annotation}' must return a subclass of '{BaseField.__name__}'")

        return field_type

    @classmethod
    def _is_list(cls, type_: type) -> bool:
        if issubclass(type_, list):
            return True
        elif issubclass(type(type_), GenericAlias):
            if getattr(type_, '__origin__', None) is list:
                return True
        return False

    @register_field_converter(str)
    def text_field_converter(self, annotation: type) -> type[TextField]:
        # check if annotation is a subclass of str
        if not issubclass(annotation, str):
            raise ValueError(f"Annotation '{annotation}' must be a subclass of '{str.__name__}'")

        return TextField

    @register_field_converter(list)
    def list_field_converter(self, annotation: type) -> tuple[type[ListField], list[type[BaseField]]]:
        args = None
        if issubclass(annotation, list):
            args = tuple(Any)
        elif issubclass(type(annotation), GenericAlias) and getattr(annotation, '__origin__', None) is list:
            # get args
            args = getattr(annotation, '__args__', None)
            if len(args) == 0:
                args = tuple(Any)
            else:
                args = tuple(args)
        if args is None:
            raise ValueError(f"Invalid type '{annotation}'")

        # get sub fields from args
        sub_fields = []
        for arg in args:
            sub_field = self.convert_field(annotation=arg)
            if sub_field is None:
                raise NotImplementedError(f"Converter method for type '{arg}' not found")
            sub_fields.append(sub_field)

        return ListField, sub_fields

    @register_field_converter(BaseModel)
    def base_model_field_converter(self, annotation: type) -> tuple[type[BaseModelField], dict[str, type[BaseField]]]:
        # get model
        if not issubclass(annotation, BaseModel):
            raise ValueError(f"Annotation '{annotation}' must be a subclass of BaseModel")

        # get sub fields from model
        sub_fields = self.convert_fields(model=annotation)

        return BaseModelField, sub_fields
