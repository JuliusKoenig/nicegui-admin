from abc import ABC, abstractmethod
from typing import Any

from nicegui import ui
from pydantic.fields import FieldInfo


class BaseField(ABC):
    def __init__(self, field_name: str, field_info: FieldInfo):
        self.field_name = field_name
        self.field_info = field_info

    async def get_title(self) -> str:
        title = self.field_info.title
        if title is None:
            title = self.field_name
        return title

    @abstractmethod
    async def render_list(self, value: Any) -> ui.element:
        ...

    @abstractmethod
    async def render_get(self, value: Any) -> tuple[ui.element, ui.element]:
        ...

    @abstractmethod
    async def render_set(self, value: Any) -> tuple[ui.element, ui.element]:
        ...
