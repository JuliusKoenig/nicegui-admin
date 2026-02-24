from typing import Any

from pydantic import BaseModel
from pydantic._internal._generics import PydanticGenericMetadata
from pydantic._internal._model_construction import ModelMetaclass
from pydantic.fields import FieldInfo

from niceguitools._crud.fields.base import BaseField
from niceguitools._crud.fields.text import TextField


class CrudModelMeta(ModelMetaclass):
    def __new__(
            mcs,
            cls_name: str,
            bases: tuple[type[Any], ...],
            namespace: dict[str, Any],
            __pydantic_generic_metadata__: PydanticGenericMetadata | None = None,
            __pydantic_reset_parent_namespace__: bool = True,
            _create_model_module: str | None = None,
            **kwargs: Any,
    ) -> type:
        cls: type[CrudModel] | type = super().__new__(
            mcs,
            cls_name,
            bases,
            namespace,
            __pydantic_generic_metadata__=__pydantic_generic_metadata__,
            __pydantic_reset_parent_namespace__=__pydantic_reset_parent_namespace__,
            _create_model_module=_create_model_module,
            **kwargs,
        )
        for field_name, field_info in cls.model_fields.items():
            field_info: FieldInfo

            # get crud_field from field_info.json_schema_extra if it exists, otherwise generate it using field_generator
            crud_field = None
            if field_info.json_schema_extra is not None:
                if "crud_field" in field_info.json_schema_extra:
                    # skip if crud_field is explicitly set to None
                    if field_info.json_schema_extra["crud_field"] is None:
                        continue
                    crud_field = field_info.json_schema_extra.pop("crud_field")
            if crud_field is None:
                crud_field = cls.field_generator(field_name=field_name, field_info=field_info)

            # if crud_field is still None, skip it
            if crud_field is None:
                continue

            # add model to crud_field so it can be accessed later
            crud_field.model = cls

            # add crud_field to field_info.metadata so it can be accessed later
            for metadata in field_info.metadata:
                if issubclass(type(metadata), BaseField):
                    raise ValueError(f"Field '{field_name}' already has a crud_field assigned: {metadata}")
            field_info.metadata.append(crud_field)

        return cls


class CrudModel(BaseModel, metaclass=CrudModelMeta):
    @classmethod
    def field_generator(cls, field_name: str, field_info: FieldInfo) -> BaseField | None:
        # ToDo: implement a default field generator that generates a crud_field based on the field_info
        return TextField()

    @classmethod
    def get_crud_fields(cls) -> dict[str, BaseField]:
        crud_fields = {}
        for field_name, field_info in cls.model_fields.items():
            for metadata in field_info.metadata:
                if issubclass(type(metadata), BaseField):
                    crud_fields[field_name] = metadata
        return crud_fields

    @classmethod
    def get_crud_field(cls, field_name: str) -> BaseField | None:
        field_info = cls.model_fields[field_name]
        for metadata in field_info.metadata:
            if not isinstance(type(metadata), BaseField):
                continue
            return metadata
        return None


