import math
from decimal import Decimal
from typing import Any, Callable, Sequence

from sqlalchemy import String, and_, cast, false, not_, or_, true
from sqlalchemy.orm import (
    InstrumentedAttribute,
    RelationshipProperty,
)
from sqlalchemy.orm.attributes import ScalarObjectAttributeImpl
from sqlalchemy.sql import ClauseElement
from sqlalchemy.sql.type_api import TypeEngine


def __is_null(latest_attr: InstrumentedAttribute) -> Any:
    if isinstance(latest_attr.property, RelationshipProperty):
        if isinstance(latest_attr.impl, ScalarObjectAttributeImpl):
            return ~latest_attr.has()
        return ~latest_attr.any()
    return latest_attr.is_(None)


def __is_not_null(latest_attr: InstrumentedAttribute) -> Any:
    if isinstance(latest_attr.property, RelationshipProperty):
        if isinstance(latest_attr.impl, ScalarObjectAttributeImpl):
            return latest_attr.has()
        return latest_attr.any()
    return latest_attr.is_not(None)


OPERATORS: dict[str, Callable[[InstrumentedAttribute, Any], ClauseElement]] = {
    "eq": lambda f, v: f == v,
    "neq": lambda f, v: f != v,
    "lt": lambda f, v: f < v,
    "gt": lambda f, v: f > v,
    "le": lambda f, v: f <= v,
    "ge": lambda f, v: f >= v,
    "in": lambda f, v: f.in_(v),
    "not_in": lambda f, v: f.not_in(v),
    "startswith": lambda f, v: cast(f, String).startswith(v),
    "not_startswith": lambda f, v: not_(cast(f, String).startswith(v)),
    "endswith": lambda f, v: cast(f, String).endswith(v),
    "not_endswith": lambda f, v: not_(cast(f, String).endswith(v)),
    "contains": lambda f, v: cast(f, String).contains(v),
    "not_contains": lambda f, v: not_(cast(f, String).contains(v)),
    "is_false": lambda f, v: f == false(),
    "is_true": lambda f, v: f == true(),
    "is_null": lambda f, v: __is_null(f),
    "is_not_null": lambda f, v: __is_not_null(f),
    "between": lambda f, v: f.between(*v),
    "not_between": lambda f, v: not_(f.between(*v)),
}


def build_query(where: dict[str, Any],
                model: Any,
                latest_attr: InstrumentedAttribute | None = None) -> Any:
    filters = []
    for key, _ in where.items():
        if key == "or":
            filters.append(or_(*[build_query(v, model, latest_attr) for v in where[key]]))
        elif key == "and":
            filters.append(and_(*[build_query(v, model, latest_attr) for v in where[key]]))
        elif key in OPERATORS:
            filters.append(OPERATORS[key](latest_attr, where[key]))
        else:
            attr: InstrumentedAttribute | None = getattr(model, key, None)
            if attr is not None:
                filters.append(build_query(where[key], model, attr))
    if len(filters) == 1:
        return filters[0]
    if filters:
        return and_(*filters)
    return and_(True)


def normalize_list(arr: Sequence[Any] | None,
                   is_default_sort_list: bool = False) -> Sequence[str] | None:
    """
    This methods will convert all InstrumentedAttribute into str

    :param arr: list of str or InstrumentedAttribute or Tuple[str | InstrumentedAttribute, bool] (if is_default_sort_list is True)
    :param is_default_sort_list: if True, it will also support Tuple[str | InstrumentedAttribute, bool] for fields_default_sort
    :return: list of str or None
    """

    if arr is None:
        return None
    _new_list = []
    for v in arr:
        if isinstance(v, InstrumentedAttribute):
            _new_list.append(v.key)
        elif isinstance(v, str):
            _new_list.append(v)
        elif isinstance(v, tuple) and is_default_sort_list:  # Support for fields_default_sort:
            if len(v) == 2 and isinstance(v[0], (str, InstrumentedAttribute)) and isinstance(v[1], bool):
                _new_list.append((v[0].key if isinstance(v[0], InstrumentedAttribute) else v[0],  # type: ignore[arg-type]
                                  v[1]))
            else:
                raise ValueError("Invalid argument, Expected Tuple[str | InstrumentedAttribute, bool]")
        else:
            raise ValueError(f"Expected str or InstrumentedAttribute, got {type(v).__name__}")
    return _new_list


def extract_column_python_type(attr: InstrumentedAttribute) -> type:
    try:
        return attr.type.python_type
    except NotImplementedError:
        return str


def get_python_type_from_sa_type(sa_type: TypeEngine) -> type[Any] | None:
    """
    Try to resolve the Python type from a SQLAlchemy type.

    This supports plain SQLAlchemy types as well as many TypeDecorator-based types.

    :param sa_type: SQLAlchemy type to resolve.
    :return: Python type or None if not supported.
    """

    candidates = [sa_type]

    impl = getattr(sa_type, "impl", None)
    if impl is not None:
        candidates.append(impl)

    for candidate in candidates:
        try:
            return candidate.python_type
        except (NotImplementedError, AttributeError):
            pass

    return None


def exclusive_min(value: int | float | Decimal,
                  python_type: type[Any] | None) -> int | float | Decimal:
    """
    Convert an exclusive lower bound to an inclusive lower bound.

    Example:
    - Gt(5) for int -> 6
    - Gt(5.0) for float -> next float > 5.0

    :param value: The value to convert.
    :param python_type: The type of the value.
    :return: The converted value.
    """

    if python_type is float:
        return math.nextafter(float(value), math.inf)

    if python_type is Decimal:
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        return value.next_plus()

    return value + 1


def exclusive_max(value: int | float | Decimal,
                  python_type: type[Any] | None) -> int | float | Decimal:
    """
    Convert an exclusive upper bound to an inclusive upper bound.

    Example:
    - Lt(5) for int -> 4
    - Lt(5.0) for float -> next float < 5.0

    :param value: The value to convert.
    :param python_type: The type of the value.
    :return: The converted value.
    """

    if python_type is float:
        return math.nextafter(float(value), -math.inf)

    if python_type is Decimal:
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        return value.next_minus()

    return value - 1