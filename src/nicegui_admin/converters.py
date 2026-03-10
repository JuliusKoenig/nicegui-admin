import datetime
import decimal
import enum
import inspect
import typing
from abc import abstractmethod, ABC
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Sequence,
    get_args,
    get_origin,
)

from nicegui_admin.exceptions import NotSupportedAnnotation
from nicegui_admin.fields import (
    BaseField,
    BooleanField,
    # DateField, # ToDo: check if needed
    # DateTimeField, # ToDo: check if needed
    DecimalField,
    # EnumField, # ToDo: check if needed
    FloatField,
    IntegerField,
    # JSONField, # ToDo: check if needed
    # ListField, # ToDo: check if needed
    StringField,
    # TimeField, # ToDo: check if needed
)


def converts(*args: Any) -> Callable[[Callable[..., BaseField]], Callable[..., BaseField]]:
    def wrap(func: Callable[..., BaseField]) -> Callable[..., BaseField]:
        func._converter_for = frozenset(args)
        return func

    return wrap


class BaseFieldConverter(ABC):
    def __init__(self, converters: Optional[Dict[Any, Callable[..., BaseField]]] = None):
        if converters is None:
            converters = {}

        for _method_name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, "_converter_for"):
                for arg in getattr(method, "_converter_for"):
                    converters[arg] = method

        self.converters = converters

    @abstractmethod
    def convert(self, *args: Any, **kwargs: Any) -> BaseField:
        """
        Search for the appropriate `nicegui_admin.BaseField` that corresponds to a specific model attribute
        and performs the conversion.
        """

    @abstractmethod
    def convert_fields_list(self,
                            *,
                            fields: Sequence[Any],
                            model: type[Any],
                            **kwargs: Any) -> Sequence[BaseField]:
        """
        Override this method to convert non-BaseField instances in your defined fields list into corresponding
        starlette_admin.BaseField objects.
        """


class BasePythonFieldConverter(BaseFieldConverter):
    """
    Converters for python built-in types
    """

    def get_converter(self, _type: Any) -> Callable[..., BaseField]:
        # If there is a converter for the specified type, use it.
        if _type in self.converters:
            return self.converters[_type]

        # If the type is a generic type, search the origin type.
        _origin = get_origin(_type)
        _args = get_args(_type)
        if _origin is not None and _origin in self.converters:
            return self.converters[_origin]

        # Otherwise, try to find a converter for any of the type's base classes.
        for cls, converter in self.converters.items():
            if inspect.isclass(cls) and inspect.isclass(_type) and _origin is None and issubclass(_type, cls):
                return converter
            if inspect.isclass(cls) and isinstance(_type, cls):
                return converter

        raise NotSupportedAnnotation(f"Cannot automatically convert '{_type}'. Find the appropriate field"
                                     " manually or provide your own converter")

    def convert(self, *args: Any, **kwargs: Any) -> BaseField:
        return self.get_converter(kwargs.get("_type"))(*args, **kwargs)

    def get_type(self, model: Any, value: Any) -> Any:
        return model.__annotations__[value]

    def convert_fields_list(self, *, fields: Sequence[Any], model: type[Any], **kwargs: Any) -> Sequence[BaseField]:
        converted_fields = []
        for value in fields:
            if isinstance(value, BaseField):
                converted_fields.append(value)
            else:
                converted_fields.append(self.convert(name=value,
                                                     _type=self.get_type(model, value),
                                                     model=model))
        return converted_fields


class PythonFieldConverter(BasePythonFieldConverter):
    """
    Converters for python built-in types
    """

    @classmethod
    def _ensure_get_args_is_not_null(cls, *args: Any, **kwargs: Any) -> None:
        if not get_args or not get_origin:
            raise ImportError(f"'typing_extensions' package is required to convert '{kwargs.get('type')}'")

    @classmethod
    def _standard_type_common(cls, *, name: str, required: Optional[bool] = True, **kwargs: Any) -> Dict[str, Any]:
        return {"name": name, "required": required}

    @converts(str, bytes, typing.Pattern)
    def conv_standard_str(self, *args: Any, **kwargs: Any) -> BaseField:
        return StringField(**self._standard_type_common(**kwargs))

    @converts(int, datetime.timedelta)
    def conv_standard_int(self, *args: Any, **kwargs: Any) -> BaseField:
        return IntegerField(**self._standard_type_common(**kwargs))

    @converts(float)
    def conv_standard_float(self, *args: Any, **kwargs: Any) -> BaseField:
        return FloatField(**self._standard_type_common(**kwargs))

    @converts(decimal.Decimal)
    def conv_standard_decimal(self, *args: Any, **kwargs: Any) -> BaseField:
        return DecimalField(**self._standard_type_common(**kwargs))

    @converts(bool)
    def conv_standard_bool(self, *args: Any, **kwargs: Any) -> BaseField:
        return BooleanField(**self._standard_type_common(**kwargs))

    # @converts(datetime.datetime)
    # def conv_standard_datetime(self, *args: Any, **kwargs: Any) -> BaseField:
    #     return DateTimeField(**self._standard_type_common(**kwargs))
    #
    # @converts(datetime.date)
    # def conv_standard_date(self, *args: Any, **kwargs: Any) -> BaseField:
    #     return DateField(**self._standard_type_common(**kwargs))
    #
    # @converts(datetime.time)
    # def conv_standard_time(self, *args: Any, **kwargs: Any) -> BaseField:
    #     return TimeField(**self._standard_type_common(**kwargs))
    #
    # @converts(dict)
    # def conv_standard_dict(self, *args: Any, **kwargs: Any) -> BaseField:
    #     return JSONField(**self._standard_type_common(**kwargs))
    #
    # @converts(enum.Enum)
    # def conv_standard_enum(self, *args: Any, **kwargs: Any) -> BaseField:
    #     return EnumField(**self._standard_type_common(*args, **kwargs),
    #                      enum=kwargs.get("_type"),
    #                      multiple=kwargs.get("multiple", False))
    #
    # @converts(list, set)
    # def conv_standard_list(self, *args: Any, **kwargs: Any) -> BaseField:
    #     """
    #     Converter for `list` annotation (eg. `list[str]`, `list[int]`)
    #     `list` will be treated as `list[str]`
    #     """
    #
    #     self._ensure_get_args_is_not_null(*args, **kwargs)
    #     subtypes = get_args(kwargs.get("_type"))
    #     subtype = subtypes[0] if len(subtypes) > 0 else str
    #     if inspect.isclass(subtype) and issubclass(subtype, enum.Enum):
    #         kwargs.update({"type": subtype, "multiple": True})
    #         return self.convert(*args, **kwargs)
    #     kwargs.update({"_type": subtype})
    #     return ListField(required=kwargs.get("required", True), field=self.convert(*args, **kwargs))
    #
    # @converts(typing.Union)
    # def conv_standard_optional(self, *args: Any, **kwargs: Any) -> BaseField:
    #     """
    #     Support for Optional[type], Union[type, None] or Union[None, type]
    #     """
    #
    #     self._ensure_get_args_is_not_null(*args, **kwargs)
    #     type_args = get_args(kwargs.get("_type"))
    #     if len(type_args) == 2 and type(None) in type_args:
    #         _sub_type = type_args[0] if type_args[1] is type(None) else type_args[1]
    #         kwargs.update({"_type": _sub_type, "required": False})
    #         return self.convert(*args, **kwargs)
    #     raise NotSupportedAnnotation(f"Cannot convert {kwargs.get('_type')}. Only annotations of the form Optional[type], Union[type, None], "
    #                                  f"or Union[None, type] are supported.")
