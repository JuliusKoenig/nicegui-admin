import os
import re
from abc import ABCMeta
from dataclasses import dataclass, field
import inspect
from types import FrameType
from typing import Any, TypeVar, Callable, Awaitable

from nicegui.helpers import is_coroutine_function


@dataclass
class SearchTarget:
    name: str | None = field(default=None)
    type: type = field(default=None)

    def __hash__(self) -> int:
        return hash((self.name, self.type))


def get_from_stack(*search_targets: SearchTarget,
                   context: int = 1,
                   raise_if_not_found: bool = True,
                   _frame: FrameType | None = None) -> Any:
    if _frame is None:
        _frame = inspect.currentframe()
    if context > 1 and _frame.f_back is not None:
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
    def resolve(cls, unset: Any, default: Any = None) -> Any:
        return default if unset is cls else unset


def prettify_class_name(name: str) -> str:
    return re.sub(r"(?<=.)([A-Z])", r" \1", name)


def slugify_class_name(name: str) -> str:
    return "".join(["-" + c.lower() if c.isupper() else c for c in name]).lstrip("-")

WRAPPED_METHODS = []

def wrapped_method(func: Callable[..., Any] | Callable[..., Awaitable[Any]]) -> Callable[..., Any] | Callable[..., Awaitable[Any]]:
    global WRAPPED_METHODS
    if func.__name__.startswith("before_"):
        raise ValueError("Method name cannot start with 'before_'!")
    if func.__name__.startswith("after_"):
        raise ValueError("Method name cannot start with 'after_'!")
    if func.__name__ not in WRAPPED_METHODS:
        WRAPPED_METHODS.append(func.__name__)
    return func

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
                    args, kwargs = await before(*args, **kwargs) if inspect.iscoroutinefunction(before) else before(*args, **kwargs)
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


T = TypeVar("T")  # ToDo: check if needed


# ToDo: check if needed
def not_none(value: T | None) -> T:
    """
    Safely retrieve a value that might be None and raise a ValueError if it is None.

    Args:
        value (Optional[T]): The value that might be None.

    Returns:
        T: The value if it is not None.

    Raises:
        ValueError: If the value is None.
    """

    if value is not None:
        return value
    raise ValueError("Value can not be None")  # pragma: no cover
