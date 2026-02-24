from dataclasses import dataclass, field
from typing import Literal, TYPE_CHECKING

from pydantic.fields import FieldInfo


if TYPE_CHECKING:
    from niceguitools._crud.views.base import BaseView
    from niceguitools._crud.model import CrudModel


@dataclass
class BaseField:
    _model: type["CrudModel"] = field(init=False, repr=False)

    serializer: Literal["text", "list", "json"] = field(default="text",
                                                        metadata={
                                                            "description": "The serializer to use for this field. Determines how the field is rendered in the UI and how the data is sent to the server."})
    hide: bool | list[type["BaseView"]] = field(default=False,
                                                metadata={
                                                    "description": "Whether to hide the field in the UI. Can be set to a list of views to hide the field only in those views."})

    @property
    def model(self) -> type["CrudModel"]:
        return self._model

    @model.setter
    def model(self, value: type["CrudModel"]) -> None:
        if hasattr(self, "_model"):
            raise AttributeError("Model is already set for this field. It can only be set once.")
        self._model = value

    @property
    def field_info(self) -> FieldInfo:
        for field_info in self.model.model_fields.values():
            for metadata in field_info.metadata:
                if metadata is self:
                    return field_info
        raise ValueError("FieldInfo not found for this field.")
