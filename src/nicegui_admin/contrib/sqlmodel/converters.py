import enum
import inspect
from typing import Any, Callable, Dict, Optional, Sequence

from annotated_types import MinLen, MaxLen
from sqlalchemy import ARRAY, Boolean, Column, Float, String, inspect as sqlalchemy_inspect
from sqlalchemy.orm import (
    ColumnProperty,
    InstrumentedAttribute,
    Mapper,
    RelationshipProperty,
)
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.sql.elements import Label
from sqlalchemy.sql.schema import ScalarElementColumnDefault
from sqlmodel.main import FieldInfo, SQLModel

from nicegui_admin.contrib.sqlmodel.exceptions import NotSupportedColumn, InvalidModelError
# from nicegui_admin.contrib.sqla.fields import FileField, ImageField# ToDo: check if needed
from nicegui_admin.converters import BaseFieldConverter, converts
from nicegui_admin.fields import (
    # ArrowField,# ToDo: check if needed
    BaseField,
    BooleanField,
    # CollectionField,# ToDo: check if needed
    # ColorField,# ToDo: check if needed
    # CountryField,# ToDo: check if needed
    # CurrencyField,# ToDo: check if needed
    # DateField,# ToDo: check if needed
    # DateTimeField,# ToDo: check if needed
    DecimalField,  # ToDo: check if needed
    # EmailField,# ToDo: check if needed
    # EnumField,# ToDo: check if needed
    FloatField,
    # HasMany,# ToDo: check if needed
    # HasOne,# ToDo: check if needed
    IntegerField,
    # JSONField,# ToDo: check if needed
    # ListField,# ToDo: check if needed
    # PasswordField,# ToDo: check if needed
    # PhoneField,# ToDo: check if needed
    StringField, IPAddressField, UUIDField,
    # TextAreaField,# ToDo: check if needed
    # TimeField,# ToDo: check if needed
    # TimeZoneField,# ToDo: check if needed
    # URLField,# ToDo: check if needed
)
from nicegui_admin.helpers import slugify_name


class BaseSqlModelFieldConverter(BaseFieldConverter):
    def convert(self,
                *args: Any,
                **kwargs: Any) -> BaseField:
        col_type = kwargs.get("_type")

        converter = self.find_converter_for_col_type(type(col_type))
        if converter is not None:
            return converter(*args, **kwargs)
        raise NotSupportedColumn(f"Column {col_type} can not be converted automatically. "
                                 f"Find the appropriate field manually or provide your custom converter.")

    def find_converter_for_col_type(self,
                                    col_type: Any) -> Optional[Callable[..., BaseField]]:
        types = inspect.getmro(col_type)

        # Search by module + name
        for col_type in types:
            type_string = f"{col_type.__module__}.{col_type.__name__}"
            if type_string in self.converters:
                return self.converters[type_string]

        # Search by name
        for col_type in types:
            if col_type.__name__ in self.converters:
                return self.converters[col_type.__name__]

            # Support for custom types which inherit TypeDecorator
            if hasattr(col_type, "impl"):
                impl = (col_type.impl
                        if callable(col_type.impl)
                        else col_type.impl.__class__)
                return self.find_converter_for_col_type(impl)
        return None

    def convert_fields_list(self,
                            *,
                            fields: Sequence[Any],
                            model: type[SQLModel],
                            **kwargs: Any) -> Sequence[BaseField]:
        # get mapper
        try:
            mapper: Mapper = sqlalchemy_inspect(model)
        except NoInspectionAvailable:
            raise InvalidModelError(f"Class {model.__name__} is not a SQLAlchemy model.")

        # convert fields
        converted_fields = []
        for field in fields:
            if isinstance(field, BaseField):
                # If it's already a BaseField, we assume it's already converted and just add it to the list
                converted_fields.append(field)
            else:
                # If it's not a BaseField, we assume it's a column key or an InstrumentedAttribute and try to find the corresponding column in the mapper
                if isinstance(field, InstrumentedAttribute):
                    attr = mapper.attrs.get(field.key)
                else:
                    attr = mapper.attrs.get(field)
                if attr is None:
                    raise ValueError(f"Can't find column with key {field}")

                if isinstance(attr, RelationshipProperty):
                    raise NotImplemented(f"Relationship property {attr} is not supported yet!")  # ToDo: implement RelationshipProperty
                #     identity = slugify_name(attr.entity.class_.__name__)
                #     if attr.direction.name == "MANYTOONE" or (attr.direction.name == "ONETOMANY" and not attr.uselist):
                #         converted_fields.append(HasOne(attr.key, identity=identity))
                #     else:
                #         converted_fields.append(HasMany(attr.key,
                #                                         identity=identity,
                #                                         collection_class=attr.collection_class or list))
                elif isinstance(attr, ColumnProperty):
                    # get column
                    column = attr.columns[0]

                    # get model field info
                    model_field_info: FieldInfo = model.model_fields[column.key]

                    # Handle inherited primary keys (i.e.: joined table polymorphic inheritance)
                    is_inherited_pk = mapper.inherits is not None and any(col.primary_key for col in attr.columns)
                    if is_inherited_pk:
                        converted_fields.append(self.convert(name=attr.key,
                                                             _type=column.type,
                                                             column=column,
                                                             model_field_info=model_field_info))
                    else:
                        assert (len(attr.columns) == 1), "Multiple-column properties are not supported"
                        if not column.foreign_keys:
                            converted_field = self.convert(name=attr.key,
                                                           _type=column.type,
                                                           column=column,
                                                           model_field_info=model_field_info)
                            converted_fields.append(converted_field)
                else:
                    raise NotSupportedColumn(f"Attribute {attr} of type {type(attr)} is not supported")
        return converted_fields


class SqlModelFieldConverter(BaseSqlModelFieldConverter):
    @classmethod
    def _common(cls,
                *,
                name: str,
                column: Column,
                model_field_info: FieldInfo,
                **kwargs: Any) -> Dict[str, Any]:
        field_kwargs = {"type": kwargs["_type"],
                        "name": name}
        if column.nullable:
            field_kwargs["not_none"] = False
        else:
            field_kwargs["not_none"] = True
        if column.default:
            if isinstance(column.default, ScalarElementColumnDefault):
                field_kwargs["default"] = BaseField.Default.STATIC
                field_kwargs["default_value"] = column.default.arg
            else:
                field_kwargs["default"] = BaseField.Default.DYNAMIC
        elif column.server_default:
            field_kwargs["default"] = BaseField.Default.DYNAMIC
        else:
            field_kwargs["default"] = None
        if model_field_info.title:
            field_kwargs["label"] = model_field_info.title
        if model_field_info.description:
            field_kwargs["help_text"] = model_field_info.description
        elif column.comment:
            field_kwargs["help_text"] = column.comment
        elif column.doc:
            field_kwargs["help_text"] = column.doc
        return field_kwargs

    @classmethod
    def _string_common(cls,
                       *,
                       _type: Any,
                       column: Column,
                       model_field_info: FieldInfo,
                       **kwargs: Any) -> Dict[str, Any]:
        field_kwargs = {}
        if column.nullable:
            field_kwargs["empty_is_none"] = True
        if isinstance(_type, String) and isinstance(_type.length, int) and _type.length > 0:
            field_kwargs["maxlength"] = _type.length
        for metadata in model_field_info.metadata:
            if isinstance(metadata, MaxLen):
                if "maxlength" in field_kwargs:
                    field_kwargs["maxlength"] = min(field_kwargs["maxlength"], metadata.max_length) # ensure maxlength is not greater than the one defined in the column type
                else:
                    field_kwargs["maxlength"] = metadata.max_length
            elif isinstance(metadata, MinLen):
                field_kwargs["minlength"] = metadata.min_length
        return field_kwargs

    @classmethod
    def _file_common(cls,
                     *,
                     _type: Any,
                     **kwargs: Any) -> Dict[str, Any]:
        raise NotImplemented()  # ToDo: test file common
        return {"multiple": getattr(_type, "multiple", False)}

    @converts("String",
              "sqlalchemy.dialects.postgresql.base.MACADDR",
              "sqlalchemy.dialects.postgresql.types.MACADDR",
              "sqlalchemy.dialects.postgresql.base.INET",
              "sqlalchemy.dialects.postgresql.types.INET",
              "sqlalchemy_utils.types.locale.LocaleType")  # includes Unicode
    def conv_string(self,
                    *args: Any,
                    **kwargs: Any) -> BaseField:
        return StringField(**self._common(*args, **kwargs),
                           **self._string_common(*args, **kwargs))

    # @converts("Text", "LargeBinary", "Binary")  # includes UnicodeText
    # def conv_text(self,
    #               *args: Any,
    #               **kwargs: Any) -> BaseField:
    #     return TextAreaField(**self._common(*args, **kwargs),
    #                          **self._string_common(*args, **kwargs))

    @converts("Boolean", "BIT")
    def conv_boolean(self,
                     *args: Any,
                     **kwargs: Any) -> BaseField:
        return BooleanField(**self._common(*args, **kwargs))

    @converts("sqlalchemy_utils.types.ip_address.IPAddressType")
    def conv_ip_address(self,
                        *args: Any,
                        **kwargs: Any) -> BaseField:
        return IPAddressField(**self._common(**kwargs))

    @converts("sqlalchemy.sql.sqltypes.Uuid",
              "sqlalchemy.dialects.postgresql.base.UUID",
              "sqlalchemy_utils.types.uuid.UUIDType")
    def conv_uuid(self,
                  *args: Any,
                  **kwargs: Any) -> BaseField:
        return UUIDField(**self._common(**kwargs))

    # @converts("DateTime")
    # def conv_datetime(self,
    #                   *args: Any,
    #                   **kwargs: Any) -> BaseField:
    #     return DateTimeField(**self._common(*args, **kwargs))
    #
    # @converts("Date")
    # def conv_date(self,
    #               *args: Any,
    #               **kwargs: Any) -> BaseField:
    #     return DateField(**self._common(*args, **kwargs))
    #
    # @converts("Time")
    # def conv_time(self,
    #               *args: Any,
    #               **kwargs: Any) -> BaseField:
    #     return TimeField(**self._common(*args, **kwargs))
    #
    # @converts("Enum")
    # def conv_enum(self,
    #               *args: Any,
    #               **kwargs: Any) -> BaseField:
    #     _type = kwargs["_type"]
    #     assert hasattr(_type, "enum_class")
    #     return EnumField(**self._common(*args, **kwargs), enum=_type.enum_class)

    @converts("Integer")  # includes BigInteger and SmallInteger
    def conv_integer(self,
                     *args: Any,
                     **kwargs: Any) -> BaseField:
        unsigned = getattr(kwargs["_type"], "unsigned", False)
        extra = self._common(*args, **kwargs)
        if unsigned:
            extra["min"] = 0
        return IntegerField(**extra)

    @converts("Numeric")  # includes DECIMAL, Float/FLOAT, REAL, and DOUBLE
    def conv_numeric(self,
                     *args: Any,
                     **kwargs: Any) -> BaseField:
        if isinstance(kwargs["_type"], Float) and not kwargs["_type"].asdecimal:
            return FloatField(**self._common(*args, **kwargs))
        return DecimalField(**self._common(*args, **kwargs))

    @converts("sqlalchemy.dialects.mysql.types.YEAR",
              "sqlalchemy.dialects.mysql.base.YEAR")
    def conv_mysql_year(self,
                        *args: Any,
                        **kwargs: Any) -> BaseField:
        return IntegerField(**self._common(*args, **kwargs), min=1901, max=2155)

    # @converts("ARRAY")
    # def conv_array(self,
    #                *args: Any,
    #                **kwargs: Any) -> BaseField:
    #     _type = kwargs["_type"]
    #     if isinstance(_type, ARRAY) and (_type.dimensions is None or _type.dimensions == 1):
    #         kwargs.update({"column": Column(kwargs["name"], _type.item_type),
    #                        "type": _type.item_type})
    #         return ListField(self.convert(*args, **kwargs))
    #     raise NotSupportedColumn("Column ARRAY with dimensions != 1 is not supported")
    #
    # @converts("JSON", "sqlalchemy_utils.types.json.JSONType")
    # def conv_json(self,
    #               *args: Any,
    #               **kwargs: Any) -> BaseField:
    #     return JSONField(**self._common(*args, **kwargs))
    #
    # @converts("sqlalchemy_file.types.FileField")
    # def conv_sqla_filefield(self,
    #                         *args: Any,
    #                         **kwargs: Any) -> BaseField:
    #     return FileField(**self._common(*args, **kwargs),
    #                      **self._file_common(*args, **kwargs))
    #
    # @converts("sqlalchemy_file.types.ImageField")
    # def conv_sqla_imagefield(self,
    #                          *args: Any,
    #                          **kwargs: Any) -> BaseField:
    #     return ImageField(**self._common(*args, **kwargs),
    #                       **self._file_common(*args, **kwargs))
    #
    # @converts("sqlalchemy_utils.types.arrow.ArrowType")
    # def conv_arrow(self,
    #                *args: Any,
    #                **kwargs: Any) -> BaseField:
    #     return ArrowField(**self._common(*args, **kwargs))
    #
    # @converts("sqlalchemy_utils.types.color.ColorType")
    # def conv_color(self,
    #                *args: Any,
    #                **kwargs: Any) -> BaseField:
    #     return ColorField(**self._common(*args, **kwargs))
    #
    # @converts("sqlalchemy_utils.types.email.EmailType")
    # def conv_email(self,
    #                *args: Any,
    #                **kwargs: Any) -> BaseField:
    #     return EmailField(**self._common(*args, **kwargs),
    #                       **self._string_common(*args, **kwargs))
    #
    # @converts("sqlalchemy_utils.types.password.PasswordType")
    # def conv_password(self,
    #                   *args: Any,
    #                   **kwargs: Any) -> BaseField:
    #     return PasswordField(**self._common(*args, **kwargs),
    #                          **self._string_common(*args, **kwargs))
    #
    # @converts("sqlalchemy_utils.types.phone_number.PhoneNumberType")
    # def conv_phonenumbers(self, *args: Any, **kwargs: Any) -> BaseField:
    #     return PhoneField(**self._common(*args, **kwargs),
    #                       **self._string_common(*args, **kwargs))
    #
    # @converts("sqlalchemy_utils.types.scalar_list.ScalarListType")
    # def conv_scalar_list(self,
    #                      *args: Any,
    #                      **kwargs: Any) -> BaseField:
    #     return ListField(StringField(**self._common(*args, **kwargs)))
    #
    # @converts("sqlalchemy_utils.types.url.URLType")
    # def conv_url(self,
    #              *args: Any,
    #              **kwargs: Any) -> BaseField:
    #     return URLField(**self._common(*args, **kwargs))
    #
    # @converts("sqlalchemy_utils.types.timezone.TimezoneType")
    # def conv_timezone(self,
    #                   *args: Any,
    #                   **kwargs: Any) -> BaseField:
    #     return TimeZoneField(**self._common(*args, **kwargs),
    #                          coerce=kwargs["_type"].python_type)
    #
    # @converts("sqlalchemy_utils.types.country.CountryType")
    # def conv_country(self,
    #                  *args: Any,
    #                  **kwargs: Any) -> BaseField:
    #     return CountryField(**self._common(*args, **kwargs))
    #
    # @converts("sqlalchemy_utils.types.currency.CurrencyType")
    # def conv_currency(self,
    #                   *args: Any,
    #                   **kwargs: Any) -> BaseField:
    #     return CurrencyField(**self._common(*args, **kwargs))
    #
    # @converts("sqlalchemy_utils.types.choice.ChoiceType")
    # def conv_choice(self,
    #                 *args: Any,
    #                 **kwargs: Any) -> BaseField:
    #     _type = kwargs["_type"]
    #     choices = _type.choices
    #     if isinstance(choices, type) and issubclass(choices, enum.Enum):
    #         return EnumField(**self._common(*args, **kwargs),
    #                          enum=choices,
    #                          coerce=_type.python_type)
    #     return EnumField(**self._common(*args, **kwargs),
    #                      choices=choices,
    #                      coerce=_type.python_type)
    #
    # @converts("sqlalchemy_utils.types.pg_composite.CompositeType")
    # def conv_composite_type(self,
    #                         *args: Any,
    #                         **kwargs: Any) -> BaseField:
    #     _type = kwargs["_type"]
    #     fields = []
    #     field_common = self._common(*args, **kwargs)
    #     for col in _type.columns:
    #         kwargs.update({"name": col.name, "column": col, "type": col.type})
    #         fields.append(self.convert(*args, **kwargs))
    #     return CollectionField(field_common["name"], fields=fields, required=field_common["required"])
