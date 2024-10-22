from abc import ABC, abstractmethod
from enum import Enum

from nicegui import ui
from pydantic.fields import FieldInfo


class BaseField(ABC):
    ui_element_list: ui.element
    ui_element_get: ui.element
    ui_element_set: ui.element

    class Mode(Enum):
        LIST = "list"
        GET = "get"
        SET = "set"

    def __init__(self, field_info: FieldInfo):
        self.field_info = field_info

    @abstractmethod
    def render(self, mode: Mode, *args, **kwargs) -> ui.element:
        ...
