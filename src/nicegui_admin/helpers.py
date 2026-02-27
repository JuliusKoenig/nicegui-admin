import os
import string
from abc import ABCMeta
from dataclasses import dataclass, field
import inspect
from types import FrameType
from typing import Any, TypeVar, Iterable

from nicegui.helpers import is_coroutine_function

from nicegui_admin.types import SyncOrAsyncFunction

T = TypeVar("T")


@dataclass
class SearchTarget:
    name: str | None = field(default=None)
    subtype: type = field(default=None)
    type: type = field(default=None)

    def __hash__(self) -> int:
        return hash((self.name, self.type))


def get_from_stack(*search_targets: SearchTarget,
                   context: int = 1,
                   raise_if_not_found: bool = True,
                   _frame: FrameType | None = None) -> Any:
    if _frame is None:
        _frame = inspect.currentframe()
    if context > 0 and _frame.f_back is not None:
        return get_from_stack(*search_targets,
                              context=context - 1,
                              _frame=_frame.f_back)
    result = {}
    while _frame is not None and search_targets:
        for search_target in search_targets:
            if search_target in result:
                continue
            for f_local in _frame.f_locals:
                if search_target.name is not None and f_local != search_target.name:
                    continue
                if search_target.subtype is not None and not issubclass(type(_frame.f_locals[f_local]),
                                                                        search_target.subtype):
                    continue
                if search_target.type is not None and type(_frame.f_locals[f_local]) != search_target.type:
                    continue
                result[search_target] = _frame.f_locals[f_local]
                break
        _frame = _frame.f_back
    if raise_if_not_found:
        for search_target in search_targets:
            if search_target not in result:
                raise ValueError(f"Could not find {search_target} in stack!")
    result = [result[search_target] for search_target in search_targets if search_target in result]
    return result[0] if len(result) == 1 else result


class Unset:
    @classmethod
    def resolve(cls, unset: T, default: Any = None) -> T:
        return default if unset is cls else unset


def prettify_name(name: str) -> str:
    out = " "
    for i, c in enumerate(name):
        if c not in string.ascii_letters + string.digits and out[-1] != " ":
            c = " "
        if out[-1] == " ":
            c = c.upper()
        out += c
    out = out.strip()
    return out


def slugify_name(name: str) -> str:
    return "".join(["-" + c.lower() if c.isupper() else c for c in name]).lstrip("-")


DECORATED_METHODS: dict[str, dict[str, dict[str, Any]]] = {}


def decorate(context: str,
             **kwargs):
    def decorator(func: SyncOrAsyncFunction) -> SyncOrAsyncFunction:
        add_decorate(func, context, **kwargs)
        return func

    return decorator


def add_decorate(func: SyncOrAsyncFunction, context: str, **kwargs) -> None:
    global DECORATED_METHODS

    if context not in DECORATED_METHODS:
        DECORATED_METHODS[context] = {}
    DECORATED_METHODS[context][func.__name__] = kwargs


class DecoratedMethodClassMeta(ABCMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        decorated_methods = {}

        # get decorated methods from bases
        for base in bases:
            if hasattr(base, "___decorated_methods___"):
                for context, methods in base.___decorated_methods___.items():
                    if context not in decorated_methods:
                        decorated_methods[context] = {}
                    for method_name, method_kwargs in methods.items():
                        decorated_methods[context][method_name] = method_kwargs

        # get global DECORATED_METHODS
        global DECORATED_METHODS
        for context, methods in DECORATED_METHODS.items():
            if context not in decorated_methods:
                decorated_methods[context] = {}
            for method_name, method_kwargs in methods.items():
                decorated_methods[context][method_name] = method_kwargs
        DECORATED_METHODS.clear()

        namespace["___decorated_methods___"] = decorated_methods

        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        return cls


class DecoratedMethodClass(metaclass=DecoratedMethodClassMeta):
    ___decorated_methods___: dict[str, dict[str | SyncOrAsyncFunction, Any]]

    @property
    def __decorated_methods__(self) -> dict[str, dict[SyncOrAsyncFunction, Any]]:
        decorated_methods = {}
        for context, methods in self.___decorated_methods___.items():
            decorated_methods[context] = {}
            for method_or_method_name, method_kwargs in methods.items():
                if isinstance(method_or_method_name, str):
                    method = getattr(self, method_or_method_name)
                else:
                    method = method_or_method_name
                decorated_methods[context][method] = method_kwargs
        return decorated_methods

    def __decorate__(self,
                     context: str,
                     **kwargs):
        def decorator(func: SyncOrAsyncFunction) -> SyncOrAsyncFunction:
            self.__add_decoration__(func,
                                    context,
                                    **kwargs)
            return func

        return decorator

    def __add_decoration__(self, func: SyncOrAsyncFunction, context: str, **kwargs) -> None:
        if context not in self.___decorated_methods___:
            self.___decorated_methods___[context] = {}
        self.___decorated_methods___[context][func] = kwargs


WRAPPED_METHODS = []


# ToDo: check if needed
def wrapped_method(func: SyncOrAsyncFunction) -> SyncOrAsyncFunction:
    global WRAPPED_METHODS
    if func.__name__.startswith("before_"):
        raise ValueError("Method name cannot start with 'before_'!")
    if func.__name__.startswith("after_"):
        raise ValueError("Method name cannot start with 'after_'!")
    if func.__name__ not in WRAPPED_METHODS:
        WRAPPED_METHODS.append(func.__name__)
    return func


# ToDo: check if needed
class WrappedMethodClassMeta(ABCMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        wrapped_methods = []

        # get wrapped methods from bases
        for base in bases:
            if hasattr(base, "__wrapped_methods__"):
                for wm in base.__wrapped_methods__:
                    if wm in wrapped_methods:
                        continue
                    wrapped_methods.append(wm)

        # get global WRAPPED_METHODS
        global WRAPPED_METHODS
        for wm in WRAPPED_METHODS:
            if wm in wrapped_methods:
                continue
            wrapped_methods.append(wm)
        WRAPPED_METHODS.clear()

        namespace["__wrapped_methods__"] = wrapped_methods

        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        return cls


# ToDo: check if needed, if so use DecoratedMethodClassMeta instead of WrappedMethodClassMeta
class WrappedMethodClass(metaclass=WrappedMethodClassMeta):
    def __getattribute__(self, item):
        if item not in super().__getattribute__("__wrapped_methods__"):
            return super().__getattribute__(item)

        # get method
        method = super().__getattribute__(item)

        if is_coroutine_function(method):
            async def wrapper(*args, **kwargs):
                if hasattr(self, f"before_{item}"):
                    before = self.__getattribute__(f"before_{item}")
                    args, kwargs = await before(*args, **kwargs) if inspect.iscoroutinefunction(before) else before(
                        *args, **kwargs)
                result = await method(*args, **kwargs)
                if hasattr(self, f"after_{item}"):
                    after = self.__getattribute__(f"after_{item}")
                    result = await after(result) if inspect.iscoroutinefunction(after) else after(result)
                return result
        else:
            def wrapper(*args, **kwargs):
                if hasattr(self, f"before_{item}"):
                    before = self.__getattribute__(f"before_{item}")
                    args, kwargs = before(*args, **kwargs)
                result = method(*args, **kwargs)
                if hasattr(self, f"after_{item}"):
                    after = self.__getattribute__(f"after_{item}")
                    result = after(result)
                return result
        return wrapper


# ToDo: check if needed
def is_empty_file(file: Any) -> bool:
    pos = file.tell()
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(pos)
    return size == 0


# ToDo: check if needed
def get_file_icon(mime_type: str) -> str:
    mapping = {
        "image": "fa-file-image",
        "audio": "fa-file-audio",
        "video": "fa-file-video",
        "application/pdf": "fa-file-pdf",
        "application/msword": "fa-file-word",
        "application/vnd.ms-word": "fa-file-word",
        "application/vnd.oasis.opendocument.text": "fa-file-word",
        "application/vnd.openxmlformatsfficedocument.wordprocessingml": "fa-file-word",
        "application/vnd.ms-excel": "fa-file-excel",
        "application/vnd.openxmlformatsfficedocument.spreadsheetml": "fa-file-excel",
        "application/vnd.oasis.opendocument.spreadsheet": "fa-file-excel",
        "application/vnd.ms-powerpoint": "fa-file-powerpoint",
        "application/vnd.openxmlformatsfficedocument.presentationml": (
            "fa-file-powerpoint"
        ),
        "application/vnd.oasis.opendocument.presentation": "fa-file-powerpoint",
        "text/plain": "fa-file-text",
        "text/html": "fa-file-code",
        "text/csv": "fa-file-csv",
        "application/json": "fa-file-code",
        "application/gzip": "fa-file-archive",
        "application/zip": "fa-file-archive",
    }
    if mime_type:
        for key, _ in mapping.items():
            if key in mime_type:
                return mapping[key]
    return "fa-file"


def not_none(value: T | None) -> T:
    """
    Safely retrieve a value that might be None and raise a ValueError if it is None.

    :param value: The value that might be None.
    :return: The value if it is not None.
    :raises ValueError: If the value is None.
    """

    if value is not None:
        return value
    raise ValueError("Value can not be None")


CHAR_ESCAPE = "."
CHAR_SEPARATOR = ","


# ToDo: check if needed
def escape(value: str) -> str:
    """
    Escape a string using custom escaping rules.

    :param value: The string to escape.
    :return: The escaped string.
    """

    return value.replace(CHAR_ESCAPE, CHAR_ESCAPE + CHAR_ESCAPE).replace(CHAR_SEPARATOR, CHAR_ESCAPE + CHAR_SEPARATOR)


# ToDo: check if needed
def iterencode(i: Iterable[str]) -> str:
    """
    Encode a sequence of strings into a single string. Each value in the sequence is escaped before being joined
    with the separator character.

    :param i: The sequence of strings to encode.
    :return: The encoded string.
    """

    return CHAR_SEPARATOR.join(escape(value) for value in i)


def iterdecode(value: str) -> tuple[str, ...]:
    """
    Decode an encoded string back to a tuple of string values.

    :param value: The encoded string to decode.
    :return: The decoded tuple of strings.
    """

    result = []
    accumulator = ""

    escaped = False

    for char in value:
        if not escaped:
            if char == CHAR_ESCAPE:
                escaped = True
                continue
            if char == CHAR_SEPARATOR:
                result.append(accumulator)
                accumulator = ""
                continue
        else:
            escaped = False

        accumulator += char

    result.append(accumulator)

    return tuple(result)
