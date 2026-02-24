from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from nicegui_admin.helper import Unset
from nicegui_admin.views import CRUD_MODES


@dataclass
class BaseField(ABC):
    """
    Base class for fields

    :param name: The name of the field, used to identify the field. It should be unique within a model.
    :param label: The label of the field, used for display purposes. If not provided, it will be generated from the name.
    :param description: The description of the field, used for tooltips and form field descriptions
    :param key: The key for data binding, if not provided, it will be the same as name
    :param required: Indicate if the fields is required
    :param searchable: Indicate if the fields is searchable
    :param orderable: Indicate if the fields is orderable
    :param disabled: Indicate if the field is disabled. Can be a boolean or a list of CRUD modes in which the field is disabled.
    :param read_only: Indicate if the field is read-only. Can be a boolean or a list of CRUD modes in which the field is read-only.
    :param exclude: Control field visibility in list page. Can be a boolean or a list of CRUD modes in which the field is excluded.
    """

    name: str
    label: str | Unset = Unset
    description: str | None = None
    key: str | Unset = Unset
    required: bool = False
    searchable: bool = True
    orderable: bool = True
    disabled: bool | list[CRUD_MODES] = False
    read_only: bool | list[CRUD_MODES] = False
    exclude: bool | list[CRUD_MODES] = False

    def __post_init__(self) -> None:
        self.label = Unset.resolve(self.label, self.name.replace("_", " ").capitalize())
        self.key = Unset.resolve(self.key, self.name)

    async def serialize_none(self) -> Any:
        """
        Defines the value to be used when the field is None during serialization.
        This can be overridden in subclasses to provide a specific value for None cases.

        :return: The value to be used when the field is None. By default, it returns None.
        """

        return None

    async def serialize(self,
                        data: dict[str, Any]) -> tuple[bool, Any]:
        """
        Extracts the value of this field from submitted data.

        :param data: The submitted data.
        :return: A tuple where the first element indicates whether the value is None and the second element is the value itself.
        """

        is_none = False
        value = data.get(self.key, None)
        if value is None:
            is_none = True
            value = await self.serialize_none()
        return is_none, value

    async def deserialize_is_none(self,
                                  value: Any) -> Any:
        """
        Determines if the given value should be considered as None during deserialization.

        :param value: The value to be checked.
        :return: A boolean indicating whether the value should be considered as None. By default, it returns True if the value is None, otherwise False.
        """

        if value is None:
            return True
        return False

    async def deserialize(self,
                          data: dict[str, Any],
                          value: Any) -> None:
        """
        Updates the data dictionary with the deserialized value for this field.

        :param data:
        :param value:
        :return:
        """

        if await self.deserialize_is_none(value=value):
            value = None
        data[self.key] = value


@dataclass
class StringField(BaseField):
    """
    This field is used to represent any kind of short text content.

    :param maxlength: Maximum length of the string. If provided, it can be used for validation and UI hints.
    :param minlength: Minimum length of the string. If provided, it can be used for validation and UI hints.
    :param placeholder: Placeholder text for the input field in the UI.
    """

    maxlength: int | None = None
    minlength: int | None = None
    placeholder: str | None = None

    async def serialize_none(self) -> str:
        return ""

    async def serialize(self,
                        data: dict[str, Any]) -> tuple[bool, str]:
        is_none, value = await super().serialize(data)
        if not is_none:
            value = str(value)
        return is_none, value

    async def deserialize_is_none(self,
                                  value: Any) -> bool:
        if await super().deserialize_is_none(value):
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        return False
