from dataclasses import dataclass
from typing import Any, Sequence

from starlette.requests import Request

from nicegui_admin.fields import StringField
from nicegui_admin.helpers import iterencode


@dataclass(init=False)
class MultiplePKField(StringField):
    """Virtual field to represent multiple primary keys as a single field.

    This field joins the values of multiple primary key columns into a
    single string, encoding/decoding each value.
    """

    def __init__(self,
                 pk_attrs: Sequence[str], _type: tuple[type, ...]):
        self.pk_attrs = pk_attrs
        super().__init__(name=",".join(pk_attrs),
                         type=_type,
                         exclude=["list", "detail", "edit", "create"])

    async def serialize(self,
                        data: dict[str, Any]) -> tuple[bool, Any]:
        """
        Encode the primary keys values into a single string
        """

        return False, iterencode(str(data[n]) for n in self.key.split(","))

# @dataclass
# class FileField(BaseFileField):
#     """This field will automatically work with sqlalchemy_file.FileField"""
#
#     async def serialize_value(
#             self, request: Request, value: Any, action: RequestAction
#     ) -> Any:
#         try:
#             return _serialize_sqlalchemy_file_library(
#                 request, value, action, self.multiple
#             )
#         except (
#                 ImportError,
#                 ModuleNotFoundError,
#                 NotSupportedValue,
#         ):  # pragma: no cover
#             return super().serialize_value(request, value, action)
#
#
# @dataclass
# class ImageField(BaseImageField):
#     """This field will automatically work with sqlalchemy_file.ImageField"""
#
#     async def serialize_value(
#             self, request: Request, value: Any, action: RequestAction
#     ) -> Any:
#         try:
#             return _serialize_sqlalchemy_file_library(
#                 request, value, action, self.multiple
#             )
#         except (
#                 ImportError,
#                 ModuleNotFoundError,
#                 NotSupportedValue,
#         ):  # pragma: no cover
#             return super().serialize_value(request, value, action)
#
#
# def _serialize_sqlalchemy_file_library(
#         request: Request, value: Any, action: RequestAction, is_multiple: bool
# ) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any]]]:
#     from sqlalchemy_file import File
#
#     if isinstance(value, File) or (
#             isinstance(value, list) and all(isinstance(f, File) for f in value)
#     ):
#         data = []
#         for item in value if isinstance(value, list) else [value]:
#             path = item["path"]
#             if (
#                     action == RequestAction.LIST
#                     and getattr(item, "thumbnail", None) is not None
#             ):
#                 """Use thumbnail on list page if available"""
#                 path = item["thumbnail"]["path"]
#             storage, file_id = path.split("/")
#             data.append(
#                 {
#                     "content_type": item["content_type"],
#                     "filename": item["filename"],
#                     "url": str(
#                         request.url_for(
#                             request.app.state.ROUTE_NAME + ":api:file",
#                             storage=storage,
#                             file_id=file_id,
#                             )
#                     ),
#                 }
#             )
#         return data if is_multiple else data[0]
#     raise NotSupportedValue  # pragma: no cover
