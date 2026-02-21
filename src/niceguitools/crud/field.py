import re
from functools import wraps
from typing import Any, overload, Callable, Literal

import annotated_types
from pydantic import Field as PydanticField, AliasPath, AliasChoices, types
from pydantic.config import JsonDict
from pydantic.fields import _Unset, FieldInfo, Deprecated, _EmptyKwargs
from pydantic_core import PydanticUndefined
from typing_extensions import Unpack

from niceguitools.crud.fields.base import BaseField


# noinspection PyPep8Naming, PyOverloads
@overload
def Field(  # noqa: C901
        default: Any = PydanticUndefined,
        *,
        default_factory: Callable[[], Any] | Callable[[dict[str, Any]], Any] | None = _Unset,
        alias: str | None = _Unset,
        alias_priority: int | None = _Unset,
        validation_alias: str | AliasPath | AliasChoices | None = _Unset,
        serialization_alias: str | None = _Unset,
        title: str | None = _Unset,
        field_title_generator: Callable[[str, FieldInfo], str] | None = _Unset,
        description: str | None = _Unset,
        examples: list[Any] | None = _Unset,
        exclude: bool | None = _Unset,
        exclude_if: Callable[[Any], bool] | None = _Unset,
        discriminator: str | types.Discriminator | None = _Unset,
        deprecated: Deprecated | str | bool | None = _Unset,
        json_schema_extra: JsonDict | Callable[[JsonDict], None] | None = _Unset,
        frozen: bool | None = _Unset,
        validate_default: bool | None = _Unset,
        repr: bool = _Unset,
        init: bool | None = _Unset,
        init_var: bool | None = _Unset,
        kw_only: bool | None = _Unset,
        pattern: str | re.Pattern[str] | None = _Unset,
        strict: bool | None = _Unset,
        coerce_numbers_to_str: bool | None = _Unset,
        gt: annotated_types.SupportsGt | None = _Unset,
        ge: annotated_types.SupportsGe | None = _Unset,
        lt: annotated_types.SupportsLt | None = _Unset,
        le: annotated_types.SupportsLe | None = _Unset,
        multiple_of: float | None = _Unset,
        allow_inf_nan: bool | None = _Unset,
        max_digits: int | None = _Unset,
        decimal_places: int | None = _Unset,
        min_length: int | None = _Unset,
        max_length: int | None = _Unset,
        union_mode: Literal['smart', 'left_to_right'] = _Unset,
        fail_fast: bool | None = _Unset,
        crud_field: BaseField | None = _Unset,
        **extra: Unpack[_EmptyKwargs],
) -> Any: ...


# noinspection PyPep8Naming
@wraps(PydanticField)
def Field(*args, **kwargs) -> Any:
    return PydanticField(*args, **kwargs)
