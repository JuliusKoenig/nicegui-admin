import decimal
import logging
from dataclasses import dataclass, field
from typing import Any

from nicegui import ui
from nicegui.element import Element

from nicegui_admin.helpers import Unset, DecoratedMethodClass, decorate
from nicegui_admin.types import AsyncFunction

logger = logging.getLogger(__name__)
_type = type


def render_method(mode: str, element_name: str | None = None):
    return decorate(context="render_method",
                    mode=mode,
                    element_name=element_name)


@dataclass
class BaseField(DecoratedMethodClass):
    """
    Base class for fields

    :param name: The name of the field, used to identify the field. It should be unique within a model.
    :param type: The type of the field.
    :param label: The label of the field, used for display purposes. If not provided, it will be generated from the name.
    :param help_text: The help text of the field, used to provide additional information about the field in the UI.
    :param key: The key for data binding, if not provided, it will be the same as name
    :param required: Indicate if the fields is required
    :param searchable: Indicate if the fields is searchable
    :param orderable: Indicate if the fields is orderable
    :param disabled: Indicate if the field is disabled. Can be a boolean or a list of CRUD modes in which the field is disabled.
    :param read_only: Indicate if the field is read-only. Can be a boolean or a list of CRUD modes in which the field is read-only.
    :param exclude: Control field visibility in list page. Can be a boolean or a list of CRUD modes in which the field is excluded.
    """

    name: str = field()
    type: type = field()
    label: str | Unset = field(default=Unset)
    help_text: str | None = field(default=None)
    key: str | Unset = field(default=Unset)
    required: bool = field(default=False)
    align: str | None = field(default="right")
    searchable: bool = field(default=True)
    orderable: bool = field(default=True)
    disabled: list[str] = field(default_factory=list)
    read_only: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    exportable: bool = field(default=True)
    cast_type: _type | None = field(default=None)
    serialization_cast_type: _type | Unset | None = field(default=Unset)
    serialization_mute_errors: Exception | tuple[Exception] = field(default_factory=tuple)
    deserialization_cast_type: _type | Unset | None = field(default=Unset)
    deserialization_mute_errors: Exception | tuple[Exception] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.name.startswith("_"):
            raise ValueError("Field name cannot start with an underscore")
        self.label = Unset.resolve(self.label, self.name.replace("_", " ").capitalize())
        self.key = Unset.resolve(self.key, self.name)
        self.serialization_cast_type = Unset.resolve(self.serialization_cast_type, self.cast_type)
        self.deserialization_cast_type = Unset.resolve(self.deserialization_cast_type, self.cast_type)

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
        else:
            if self.serialization_cast_type is not None:
                try:
                    value = self.serialization_cast_type(value)
                except self.serialization_mute_errors as e:
                    logger.exception(f"Error in serializing field '{self.name}' with value '{value}' to {self.serialization_cast_type}: {e}")
                    value = self.serialize_none()
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
        else:
            if self.deserialization_cast_type is not None:
                try:
                    value = self.deserialization_cast_type(value)
                except self.deserialization_mute_errors as e:
                    logger.exception(f"Error in deserializing field '{self.name}' with value '{value}' to {self.deserialization_cast_type}: {e}")
                    value = None
        data[self.key] = value

    def get_render_method(self,
                          mode: str,
                          element_name: str | None = None) -> AsyncFunction | None:
        for method, kwargs in self.__decorated_methods__.get("render_method", {}).items():
            if kwargs["mode"] != mode:
                continue
            if kwargs["element_name"] != element_name:
                continue
            return method
        return None

    # @render_method(mode="list", element_name="label") #ToDo: implement custom header cell rendering, with sorting, filtering, etc.
    # async def list_table_header_cell(self,
    #                                  table: ui.table,
    #                                  **kwargs) -> Element:
    #     table.header(column_name=self.key)
    # ui.icon("thumb_up", size="1.5em")
    # ui.html(content=self.label)

    @render_method(mode="list", element_name="value")
    async def list_table_body_cell(self,
                                   table: ui.table,
                                   **kwargs) -> FieldRenderFunctionResult:
        with table.cell(column_name=self.name):
            return ui.label().props(":innerHTML=\"props.row." + self.key + "\"")

    @render_method(mode="detail", element_name="label")
    async def detail_label(self,
                           **kwargs) -> FieldRenderFunctionResult:
        return ui.label(text=self.label).classes("text-bold")

    @render_method(mode="detail", element_name="value")
    async def detail_value(self,
                           value: Any,
                           **kwargs) -> FieldRenderFunctionResult:
        return ui.label(text=value)

    @render_method(mode="form", element_name="label")
    async def form_label(self,
                         **kwargs) -> FieldRenderFunctionResult:
        return ui.label(text=self.label).classes("text-bold")

    @render_method(mode="form", element_name="value")
    async def form_value(self,
                         value: Any,
                         **kwargs) -> FieldRenderFunctionResult:
        return ui.label(text=value)


@dataclass
class BooleanField(BaseField):
    """
    This field displays the `true/false` value of a boolean property.
    """

    cast_type = bool


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
    cast_type = str

    async def serialize_none(self) -> str:
        return ""

    async def deserialize_is_none(self,
                                  value: Any) -> bool:
        if await super().deserialize_is_none(value):
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        return False


# @dataclass
# class TextAreaField(StringField):
#     """This field is used to represent any kind of long text content.
#     For short text contents, use [StringField][starlette_admin.fields.StringField]"""
#
#     rows: int = 6
#     class_: str = "field-textarea form-control"
#     form_template: str = "forms/textarea.html"
#     display_template: str = "displays/textarea.html"
#
#     def input_params(self) -> str:
#         return html_params(
#             {
#                 "rows": self.rows,
#                 "minlength": self.minlength,
#                 "maxlength": self.maxlength,
#                 "placeholder": self.placeholder,
#                 "required": self.required,
#                 "disabled": self.disabled,
#                 "readonly": self.read_only,
#             }
#         )
#
#
# @dataclass
# class TinyMCEEditorField(TextAreaField):
#     """A field that provides a WYSIWYG editor for long text content using the
#      [TinyMCE](https://www.tiny.cloud/) library.
#
#     This field can be used as an alternative to the [TextAreaField][starlette_admin.fields.TextAreaField]
#     to provide a more sophisticated editor for user input.
#
#     Parameters:
#         version_tinymce: TinyMCE version
#         version_tinymce_jquery: TinyMCE jQuery version
#         height: Height of the editor
#         menubar: Show/hide the menubar in the editor
#         statusbar: Show/hide the statusbar in the editor
#         toolbar: Toolbar options to show in the editor
#         content_style: CSS style to apply to the editor content
#         extra_options: Other options to pass to TinyMCE
#     """
#
#     class_: str = "field-tinymce-editor form-control"
#     display_template: str = "displays/tinymce.html"
#     version_tinymce: str = "6.4"
#     version_tinymce_jquery: str = "2.0"
#     height: int = 300
#     menubar: Union[bool, str] = False
#     statusbar: bool = False
#     toolbar: str = (
#         "undo redo | formatselect | bold italic backcolor | alignleft aligncenter"
#         " alignright alignjustify | bullist numlist outdent indent | removeformat"
#     )
#     content_style: str = (
#         "body { font-family: -apple-system, BlinkMacSystemFont, San Francisco, Segoe"
#         " UI, Roboto, Helvetica Neue, sans-serif; font-size: 14px;"
#         " -webkit-font-smoothing: antialiased; }"
#     )
#     extra_options: Dict[str, Any] = dc_field(default_factory=dict)
#     """For more options, see the [TinyMCE | Documentation](https://www.tiny.cloud/docs/tinymce/6/)"""
#
#     def additional_js_links(self, request: Request, action: RequestAction) -> List[str]:
#         if action.is_form():
#             return [
#                 f"https://cdn.jsdelivr.net/npm/tinymce@{self.version_tinymce}/tinymce.min.js",
#                 f"https://cdn.jsdelivr.net/npm/@tinymce/tinymce-jquery@{self.version_tinymce_jquery}/dist/tinymce-jquery.min.js",
#             ]
#         return []
#
#     def input_params(self) -> str:
#         _options = {
#             "height": self.height,
#             "menubar": self.menubar,
#             "statusbar": self.statusbar,
#             "toolbar": self.toolbar,
#             "content_style": self.content_style,
#             **self.extra_options,
#         }
#
#         return (
#                 super().input_params()
#                 + " "
#                 + html_params({"data-options": json.dumps(_options)})
#         )


@dataclass
class BaseNumberField(BaseField):
    """
    This is the base class for fields that represent numeric values, such as integers and decimals.

    :param max: The maximum value allowed for the field. If provided, it can be used for validation and UI hints.
    :param min: The minimum value allowed for the field. If provided, it can be used for validation and UI hints.
    :param step: The step value for the field, which indicates the allowed increments between values. If provided, it can be used for validation and UI hints.
    :param placeholder: Placeholder text for the input field in the UI.
    """

    max: int | None = None
    min: int | None = None
    step: int | None = None
    placeholder: str | None = None


@dataclass
class IntegerField(BaseNumberField):
    """
    This field is used to represent the value of properties that store integer numbers.
    Erroneous input is ignored and will not be accepted as a value.
    """

    cast_type = int
    deserialization_mute_errors = ValueError, TypeError


@dataclass
class DecimalField(BaseNumberField):
    """
    This field is used to represent the value of properties that store decimal numbers.
    Erroneous input is ignored and will not be accepted as a value.
    """

    serialization_cast_type = str
    deserialization_cast_type = decimal.Decimal
    deserialization_mute_errors = decimal.InvalidOperation, ValueError


@dataclass
class FloatField(StringField):
    """
    A text field, except all input is coerced to an float.
     Erroneous input is ignored and will not be accepted as a value.
    """

    cast_type = int
    deserialization_mute_errors = ValueError

# @dataclass
# class TagsField(BaseField):
#     """
#     This field is used to represent the value of properties that store a list of
#     string values. Render as `select2` tags input.
#     """
#
#     form_template: str = "forms/tags.html"
#     form_js: str = "js/field/forms/tags.js"
#     class_: str = "field-tags form-control form-select"
#
#     async def parse_form_data(
#             self, request: Request, form_data: FormData, action: RequestAction
#     ) -> List[str]:
#         return form_data.getlist(self.id)  # type: ignore
#
#     def additional_css_links(
#             self, request: Request, action: RequestAction
#     ) -> List[str]:
#         if action.is_form():
#             return [
#                 str(
#                     request.url_for(
#                         f"{request.app.state.ROUTE_NAME}:statics",
#                         path="css/select2.min.css",
#                     )
#                 )
#             ]
#         return []
#
#     def additional_js_links(self, request: Request, action: RequestAction) -> List[str]:
#         if action.is_form():
#             return [
#                 str(
#                     request.url_for(
#                         f"{request.app.state.ROUTE_NAME}:statics",
#                         path="js/vendor/select2.min.js",
#                     )
#                 )
#             ]
#         return []
#
#
# @dataclass
# class EmailField(StringField):
#     """This field is used to represent a text content
#     that stores a single email address."""
#
#     input_type: str = "email"
#     render_function_key: str = "email"
#     class_: str = "field-email form-control"
#     display_template: str = "displays/email.html"
#
#
# @dataclass
# class URLField(StringField):
#     """This field is used to represent a text content that stores a single URL."""
#
#     input_type: str = "url"
#     render_function_key: str = "url"
#     class_: str = "field-url form-control"
#     display_template: str = "displays/url.html"
#
#
# @dataclass
# class PhoneField(StringField):
#     """A StringField, except renders an `<input type="phone">`."""
#
#     input_type: str = "phone"
#     class_: str = "field-phone form-control"
#
#
# @dataclass
# class ColorField(StringField):
#     """A StringField, except renders an `<input type="color">`."""
#
#     input_type: str = "color"
#     class_: str = "field-color form-control form-control-color"
#
#
# @dataclass
# class PasswordField(StringField):
#     """A StringField, except renders an `<input type="password">`."""
#
#     input_type: str = "password"
#     class_: str = "field-password form-control"
#
#
# @dataclass
# class EnumField(StringField):
#     """
#     Enumeration Field.
#     It takes a python `enum.Enum` class or a list of *(value, label)* pairs.
#     It can also be a list of only values, in which case the value is used as the label.
#     Example:
#         ```python
#         class Status(str, enum.Enum):
#             NEW = "new"
#             ONGOING = "ongoing"
#             DONE = "done"
#
#         class MyModel:
#             status: Optional[Status] = None
#
#         class MyModelView(ModelView):
#             fields = [EnumField("status", enum=Status)]
#         ```
#
#         ```python
#         class MyModel:
#             language: str
#
#         class MyModelView(ModelView):
#             fields = [
#                 EnumField(
#                     "language",
#                     choices=[("cpp", "C++"), ("py", "Python"), ("text", "Plain Text")],
#                 )
#             ]
#         ```
#     """
#
#     multiple: bool = False
#     enum: Optional[Type[Enum]] = None
#     choices: Union[Sequence[str], Sequence[Tuple[Any, str]], None] = None
#     choices_loader: Optional[
#         Callable[[Request], Union[Sequence[str], Sequence[Tuple[Any, str]]]]
#     ] = dc_field(default=None, compare=False)
#     form_template: str = "forms/enum.html"
#     class_: str = "field-enum form-control form-select"
#     coerce: Callable[[Any], Any] = str
#     select2: bool = True
#
#     def __post_init__(self) -> None:
#         if self.choices and not isinstance(self.choices[0], (list, tuple)):
#             self.choices = list(zip(self.choices, self.choices))  # type: ignore
#         elif self.enum:
#             self.choices = [(e.value, e.name.replace("_", " ")) for e in self.enum]
#             self.coerce = int if issubclass(self.enum, IntEnum) else str
#         elif not self.choices and self.choices_loader is None:
#             raise ValueError(
#                 "EnumField required a list of choices, enum class or a choices_loader for dynamic choices"
#             )
#         super().__post_init__()
#
#     async def parse_form_data(
#             self, request: Request, form_data: FormData, action: RequestAction
#     ) -> Any:
#         return (
#             list(map(self.coerce, form_data.getlist(self.id)))
#             if self.multiple
#             else (
#                 self.coerce(form_data.get(self.id)) if form_data.get(self.id) else None
#             )
#         )
#
#     def _get_choices(self, request: Request) -> Any:
#         return (
#             self.choices
#             if self.choices_loader is None
#             else self.choices_loader(request)
#         )
#
#     def _get_label(self, value: Any, request: Request) -> Any:
#         for v, label in self._get_choices(request):
#             if value == v:
#                 return label
#         raise ValueError(f"Invalid choice value: {value}")
#
#     async def serialize_value(
#             self, request: Request, value: Any, action: RequestAction
#     ) -> Any:
#         if isinstance(value, Enum):
#             value = value.value
#         labels = [
#             (self._get_label(v, request) if action != RequestAction.EDIT else v)
#             for v in (value if self.multiple else [value])
#         ]
#         return labels if self.multiple else labels[0]
#
#     def additional_css_links(
#             self, request: Request, action: RequestAction
#     ) -> List[str]:
#         if self.select2 and action.is_form():
#             return [
#                 str(
#                     request.url_for(
#                         f"{request.app.state.ROUTE_NAME}:statics",
#                         path="css/select2.min.css",
#                     )
#                 )
#             ]
#         return []
#
#     def additional_js_links(self, request: Request, action: RequestAction) -> List[str]:
#         if self.select2 and action.is_form():
#             return [
#                 str(
#                     request.url_for(
#                         f"{request.app.state.ROUTE_NAME}:statics",
#                         path="js/vendor/select2.min.js",
#                     )
#                 )
#             ]
#         return []
#
#     @classmethod
#     def from_enum(
#             cls,
#             name: str,
#             enum_type: Type[Enum],
#             multiple: bool = False,
#             **kwargs: Dict[str, Any],
#     ) -> "EnumField":
#         warnings.warn(
#             f'This method is deprecated. Use EnumField("name", enum={enum_type.__name__}) instead.',
#             DeprecationWarning,
#             stacklevel=1,
#         )
#         return cls(name, enum=enum_type, multiple=multiple, **kwargs)  # type: ignore
#
#     @classmethod
#     def from_choices(
#             cls,
#             name: str,
#             choices: Union[Sequence[str], Sequence[Tuple[str, str]], None],
#             multiple: bool = False,
#             **kwargs: Dict[str, Any],
#     ) -> "EnumField":
#         warnings.warn(
#             f'This method is deprecated. Use EnumField("name", choices={choices}) instead.',
#             DeprecationWarning,
#             stacklevel=1,
#         )
#         return cls(name, choices=choices, multiple=multiple, **kwargs)  # type: ignore
#
#
# @dataclass
# class TimeZoneField(EnumField):
#     """This field is used to represent the name of a timezone (eg. Africa/Porto-Novo)"""
#
#     def __post_init__(self) -> None:
#         if self.choices is None:
#             self.choices = [
#                 (self.coerce(x), x.replace("_", " ")) for x in common_timezones
#             ]
#         super().__post_init__()
#
#
# @dataclass
# class CountryField(EnumField):
#     """This field is used to represent the name that corresponds to the country code stored in your database"""
#
#     def __post_init__(self) -> None:
#         try:
#             import babel  # noqa
#         except ImportError as err:
#             raise ImportError(
#                 "'babel' package is required to use 'CountryField'. Install it with `pip install starlette-admin[i18n]`"
#             ) from err
#         self.choices_loader = lambda request: get_countries_list()
#         super().__post_init__()
#
#
# @dataclass
# class CurrencyField(EnumField):
#     """
#     This field is used to represent a value that stores the
#     [3-letter ISO 4217](https://en.wikipedia.org/wiki/ISO_4217) code of currency
#     """
#
#     def __post_init__(self) -> None:
#         try:
#             import babel  # noqa
#         except ImportError as err:
#             raise ImportError(
#                 "'babel' package is required to use 'CurrencyField'. Install it with `pip install starlette-admin[i18n]`"
#             ) from err
#         self.choices_loader = lambda request: get_currencies_list()
#         super().__post_init__()
#
#
# @dataclass
# class DateTimeField(NumberField):
#     """
#     This field is used to represent a value that stores a python datetime.datetime object
#     Parameters:
#         search_format: moment.js format to send for searching. Use None for iso Format
#         output_format: display output format
#     """
#
#     input_type: str = "datetime-local"
#     class_: str = "field-datetime form-control"
#     search_builder_type: str = "moment-LL LT"
#     output_format: Optional[str] = None
#     search_format: Optional[str] = None
#     form_alt_format: Optional[str] = "F j, Y  H:i:S"
#
#     def input_params(self) -> str:
#         return html_params(
#             {
#                 "type": self.input_type,
#                 "min": self.min,
#                 "max": self.max,
#                 "step": self.step,
#                 "data_alt_format": self.form_alt_format,
#                 "data_locale": get_locale(),
#                 "placeholder": self.placeholder,
#                 "required": self.required,
#                 "disabled": self.disabled,
#                 "readonly": self.read_only,
#             }
#         )
#
#     async def parse_form_data(
#             self, request: Request, form_data: FormData, action: RequestAction
#     ) -> Union[datetime, None]:
#         try:
#             dt = datetime.fromisoformat(form_data.get(self.id))  # type: ignore
#         except (TypeError, ValueError):
#             return None
#
#         # Preserve pre-timezone conversion behaviour
#         if not is_timezone_conversion_enabled():
#             return dt
#
#         if dt.tzinfo is not None:
#             database_tz = get_database_tzinfo()
#             return dt.astimezone(database_tz).replace(tzinfo=None)
#
#         # Native datetime, assume it's in the user's timezone
#         user_tz = get_tzinfo()
#         database_tz = get_database_tzinfo()
#
#         return dt.replace(tzinfo=user_tz).astimezone(database_tz).replace(tzinfo=None)
#
#     async def serialize_value(
#             self, request: Request, value: Any, action: RequestAction
#     ) -> str:
#         assert isinstance(value, datetime), f"Expected datetime, got {type(value)}"
#
#         # Preserve pre-timezone conversion behaviour
#         if not is_timezone_conversion_enabled():
#             if action != RequestAction.EDIT:
#                 return format_datetime(value, self.output_format)
#             return value.isoformat()
#
#         user_tz = get_tzinfo()
#
#         if value.tzinfo is None:
#             # native datetime from db, assume it's in database timezone
#             database_tz = get_database_tzinfo()
#             value = value.replace(tzinfo=database_tz)
#
#         if action != RequestAction.EDIT:
#             return format_datetime(value, self.output_format, user_tz)
#
#         # For EDIT action, convert to user timezone and return as naive datetime for datetime-local input
#         converted_value = value.astimezone(user_tz)
#         return converted_value.replace(tzinfo=None).isoformat()
#
#     def additional_css_links(
#             self, request: Request, action: RequestAction
#     ) -> List[str]:
#         if action.is_form():
#             return [
#                 str(
#                     request.url_for(
#                         f"{request.app.state.ROUTE_NAME}:statics",
#                         path="css/flatpickr.min.css",
#                     )
#                 )
#             ]
#         return []
#
#     def additional_js_links(self, request: Request, action: RequestAction) -> List[str]:
#         _links = [
#             str(
#                 request.url_for(
#                     f"{request.app.state.ROUTE_NAME}:statics",
#                     path="js/vendor/flatpickr.min.js",
#                 )
#             )
#         ]
#         if get_locale() != "en":
#             _links.append(
#                 str(
#                     request.url_for(
#                         f"{request.app.state.ROUTE_NAME}:statics",
#                         path=f"i18n/flatpickr/{get_locale()}.js",
#                     )
#                 )
#             )
#         if action.is_form():
#             return _links
#         return []
#
#
# @dataclass
# class DateField(DateTimeField):
#     """
#     This field is used to represent a value that stores a python datetime.date object
#     Parameters:
#         search_format: moment.js format to send for searching. Use None for iso Format
#         output_format: Set display output format
#     """
#
#     input_type: str = "date"
#     class_: str = "field-date form-control"
#     output_format: Optional[str] = None
#     search_format: str = "YYYY-MM-DD"
#     search_builder_type: str = "moment-LL"
#     form_alt_format: Optional[str] = "F j, Y"
#
#     async def parse_form_data(
#             self, request: Request, form_data: FormData, action: RequestAction
#     ) -> Any:
#         try:
#             return date.fromisoformat(form_data.get(self.id))  # type: ignore
#         except (TypeError, ValueError):
#             return None
#
#     async def serialize_value(
#             self, request: Request, value: Any, action: RequestAction
#     ) -> str:
#         assert isinstance(value, date), f"Expect date, got  {type(value)}"
#         if action != RequestAction.EDIT:
#             return format_date(value, self.output_format)
#         return value.isoformat()
#
#
# @dataclass
# class TimeField(DateTimeField):
#     """
#     This field is used to represent a value that stores a python datetime.time object
#     Parameters:
#         search_format: Format to send for search. Use None for iso Format
#         output_format: Set display output format
#     """
#
#     input_type: str = "time"
#     class_: str = "field-time form-control"
#     search_builder_type: str = "moment-LTS"
#     output_format: Optional[str] = None
#     search_format: str = "HH:mm:ss"
#     form_alt_format: Optional[str] = "H:i:S"
#
#     async def parse_form_data(
#             self, request: Request, form_data: FormData, action: RequestAction
#     ) -> Any:
#         try:
#             return time.fromisoformat(form_data.get(self.id))  # type: ignore
#         except (TypeError, ValueError):
#             return None
#
#     async def serialize_value(
#             self, request: Request, value: Any, action: RequestAction
#     ) -> str:
#         assert isinstance(value, time), f"Expect time, got  {type(value)}"
#         if action != RequestAction.EDIT:
#             return format_time(value, self.output_format)
#         return value.isoformat()
#
#
# @dataclass
# class ArrowField(DateTimeField):
#     """
#     This field is used to represent sqlalchemy_utils.types.arrow.ArrowType
#     """
#
#     def __post_init__(self) -> None:
#         if not arrow:  # pragma: no cover
#             raise ImportError("'arrow' package is required to use 'ArrowField'")
#         super().__post_init__()
#
#     async def parse_form_data(
#             self, request: Request, form_data: FormData, action: RequestAction
#     ) -> Any:
#         # Preserve pre-timezone conversion behaviour
#         if not is_timezone_conversion_enabled():
#             try:
#                 return arrow.get(form_data.get(self.id))  # type: ignore
#             except (TypeError, arrow.parser.ParserError):  # pragma: no cover
#                 return None
#
#         dt = await super().parse_form_data(request, form_data, action)
#         if dt is None:
#             return None
#
#         return arrow.get(dt)
#
#     async def serialize_value(
#             self, request: Request, value: Any, action: RequestAction
#     ) -> str:
#         assert isinstance(value, arrow.Arrow), f"Expected Arrow, got  {type(value)}"
#
#         # Preserve pre-timezone conversion behaviour
#         if not is_timezone_conversion_enabled():
#             if action != RequestAction.EDIT:
#                 return value.humanize(locale=get_locale())
#
#             return value.isoformat()
#
#         if action != RequestAction.EDIT:
#             user_tz = get_tzinfo()
#             return value.to(user_tz).humanize(locale=get_locale())
#
#         return await super().serialize_value(request, value.datetime, action)
#
#
# @dataclass
# class JSONField(BaseField):
#     """
#     This field render jsoneditor and represent a value that stores python dict object.
#     Erroneous input is ignored and will not be accepted as a value."""
#
#     height: str = "20em"
#     modes: Optional[Sequence[str]] = None
#     render_function_key: str = "json"
#     form_template: str = "forms/json.html"
#     display_template: str = "displays/json.html"
#
#     def __post_init__(self) -> None:
#         if self.modes is None:
#             self.modes = ["view"] if self.read_only else ["tree", "code"]
#         super().__post_init__()
#
#     async def parse_form_data(
#             self, request: Request, form_data: FormData, action: RequestAction
#     ) -> Optional[Dict[str, Any]]:
#         try:
#             value = form_data.get(self.id)
#             return json.loads(value) if value is not None else None  # type: ignore
#         except JSONDecodeError:
#             return None
#
#     def additional_css_links(
#             self, request: Request, action: RequestAction
#     ) -> List[str]:
#         if action.is_form():
#             return [
#                 str(
#                     request.url_for(
#                         f"{request.app.state.ROUTE_NAME}:statics",
#                         path="css/jsoneditor.min.css",
#                     )
#                 )
#             ]
#         return []
#
#     def additional_js_links(self, request: Request, action: RequestAction) -> List[str]:
#         if action.is_form():
#             return [
#                 str(
#                     request.url_for(
#                         f"{request.app.state.ROUTE_NAME}:statics",
#                         path="js/vendor/jsoneditor.min.js",
#                     )
#                 )
#             ]
#         return []
#
#
# @dataclass
# class FileField(BaseField):
#     """
#     Renders a file upload field.
#     This field is used to represent a value that stores starlette UploadFile object.
#     For displaying value, this field wait for three properties which is `filename`,
#     `content-type` and `url`. Use `multiple=True` for multiple file upload
#     When user ask for delete on editing page, the second part of the returned tuple is True.
#     """
#
#     accept: Optional[str] = None
#     multiple: bool = False
#     render_function_key: str = "file"
#     form_template: str = "forms/file.html"
#     display_template: str = "displays/file.html"
#
#     async def parse_form_data(
#             self, request: Request, form_data: FormData, action: RequestAction
#     ) -> Tuple[Union[UploadFile, List[UploadFile], None], bool]:
#         should_be_deleted = form_data.get(f"_{self.id}-delete") == "on"
#         if self.multiple:
#             files = form_data.getlist(self.id)
#             return [f for f in files if not is_empty_file(f.file)], should_be_deleted  # type: ignore
#         file = form_data.get(self.id)
#         return (
#             None if (file and is_empty_file(file.file)) else file  # type: ignore
#         ), should_be_deleted
#
#     def _isvalid_value(self, value: Any) -> bool:
#         return value is not None and all(
#             (
#                     hasattr(v, "url")
#                     or (isinstance(v, dict) and v.get("url", None) is not None)
#             )
#             for v in (value if self.multiple else [value])
#         )
#
#     def input_params(self) -> str:
#         return html_params(
#             {
#                 "accept": self.accept,
#                 "disabled": self.disabled,
#                 "readonly": self.read_only,
#                 "multiple": self.multiple,
#             }
#         )
#
#
# @dataclass
# class ImageField(FileField):
#     """
#     FileField with `accept="image/*"`.
#     """
#
#     accept: Optional[str] = "image/*"
#     render_function_key: str = "image"
#     form_template: str = "forms/image.html"
#     display_template: str = "displays/image.html"
#
#
# @dataclass
# class RelationField(BaseField):
#     """
#     A field representing a relation between two data models.
#
#     This field should not be used directly; instead, use either the [HasOne][starlette_admin.fields.HasOne]
#     or [HasMany][starlette_admin.fields.HasMany] fields to specify a relation
#     between your models.
#
#     !!! important
#
#         It is important to add both models in your admin interface.
#
#     Parameters:
#         identity: Foreign ModelView identity
#
#
#     ??? Example
#
#         ```py
#         class Author:
#             id: Optional[int]
#             name: str
#             books: List["Book"]
#
#         class Book:
#             id: Optional[int]
#             title: str
#             author: Optional["Author"]
#
#         class AuthorView(ModelView):
#             fields = [
#                 IntegerField("id"),
#                 StringField("name"),
#                 HasMany("books", identity="book"),
#             ]
#
#         class BookView(ModelView):
#             fields = [
#                 IntegerField("id"),
#                 StringField("title"),
#                 HasOne("author", identity="author"),
#             ]
#         ...
#         admin.add_view(AuthorView(Author, identity="author"))
#         admin.add_view(BookView(Book, identity="book"))
#         ...
#         ```
#     """
#
#     identity: Optional[str] = None
#     multiple: bool = False
#     render_function_key: str = "relation"
#     form_template: str = "forms/relation.html"
#     display_template: str = "displays/relation.html"
#
#     async def parse_form_data(
#             self, request: Request, form_data: FormData, action: RequestAction
#     ) -> Any:
#         if self.multiple:
#             return form_data.getlist(self.id)
#         return form_data.get(self.id)
#
#     def additional_css_links(
#             self, request: Request, action: RequestAction
#     ) -> List[str]:
#         if action.is_form():
#             return [
#                 str(
#                     request.url_for(
#                         f"{request.app.state.ROUTE_NAME}:statics",
#                         path="css/select2.min.css",
#                     )
#                 )
#             ]
#         return []
#
#     def additional_js_links(self, request: Request, action: RequestAction) -> List[str]:
#         if action.is_form():
#             return [
#                 str(
#                     request.url_for(
#                         f"{request.app.state.ROUTE_NAME}:statics",
#                         path="js/vendor/select2.min.js",
#                     )
#                 )
#             ]
#         return []
#
#
# @dataclass
# class HasOne(RelationField):
#     """
#     A field representing a "has-one" relation between two models.
#     """
#
#
# @dataclass
# class HasMany(RelationField):
#     """A field representing a "has-many" relationship between two models."""
#
#     multiple: bool = True
#     collection_class: Union[Type[Collection[Any]], Callable[[], Collection[Any]]] = list
#
#
# @dataclass(init=False)
# class CollectionField(BaseField):
#     """
#     This field represents a collection of others fields. Can be used to represent embedded mongodb document.
#     !!! usage
#
#     ```python
#      CollectionField("config", fields=[StringField("key"), IntegerField("value", help_text="multiple of 5")]),
#     ```
#     """
#
#     fields: Sequence[BaseField] = dc_field(default_factory=list)
#     render_function_key: str = "json"
#     form_template: str = "forms/collection.html"
#     display_template: str = "displays/collection.html"
#
#     def __init__(
#             self, name: str, fields: Sequence[BaseField], required: bool = False
#     ) -> None:
#         self.name = name
#         self.fields = fields
#         self.required = required
#         super().__post_init__()
#         self._propagate_id()
#
#     def get_fields_list(
#             self,
#             request: Request,
#             action: RequestAction = RequestAction.LIST,
#     ) -> Sequence[BaseField]:
#         return extract_fields(self.fields, action)
#
#     def _propagate_id(self) -> None:
#         """Will update fields id by adding his id as prefix (ex: category.name)"""
#         for field in self.fields:
#             field.id = self.id + ("." if self.id else "") + field.name
#             if isinstance(field, type(self)):
#                 field._propagate_id()
#
#     async def parse_form_data(
#             self, request: Request, form_data: FormData, action: RequestAction
#     ) -> Any:
#         value = {}
#         for field in self.get_fields_list(request, action):
#             value[field.name] = await field.parse_form_data(request, form_data, action)
#         return value
#
#     async def serialize_value(
#             self, request: Request, value: Any, action: RequestAction
#     ) -> Any:
#         serialized_value: Dict[str, Any] = {}
#         for field in self.get_fields_list(request, action):
#             name = field.name
#             serialized_value[name] = None
#             if hasattr(value, name) or (isinstance(value, dict) and name in value):
#                 field_value = (
#                     getattr(value, name) if hasattr(value, name) else value[name]
#                 )
#                 if field_value is not None:
#                     serialized_value[name] = await field.serialize_value(
#                         request, field_value, action
#                     )
#         return serialized_value
#
#     def additional_css_links(
#             self, request: Request, action: RequestAction
#     ) -> List[str]:
#         _links = []
#         for f in self.get_fields_list(request, action):
#             _links.extend(f.additional_css_links(request, action))
#         return _links
#
#     def additional_js_links(self, request: Request, action: RequestAction) -> List[str]:
#         _links = []
#         for f in self.get_fields_list(request, action):
#             _links.extend(f.additional_js_links(request, action))
#         return _links
#
#
# @dataclass(init=False)
# class ListField(BaseField):
#     """
#     Encapsulate an ordered list of multiple instances of the same field type,
#     keeping data as a list.
#
#     !!! usage
#
#         ```python
#         class MyModel:
#             id: Optional[int]
#             values: List[str]
#
#         class ModelView(BaseModelView):
#             fields = [IntegerField("id"), ListField(StringField("values")]
#         ```
#     """
#
#     form_template: str = "forms/list.html"
#     display_template: str = "displays/list.html"
#     search_builder_type: str = "array"
#     field: BaseField = dc_field(default_factory=lambda: BaseField(""))
#
#     def __init__(self, field: BaseField, required: bool = False) -> None:
#         self.field = field
#         self.name = field.name
#         self.required = required
#         self.__post_init__()
#
#     def __post_init__(self) -> None:
#         super().__post_init__()
#         self.field.id = ""
#         if isinstance(self.field, CollectionField):
#             self.field._propagate_id()
#
#     async def parse_form_data(
#             self, request: Request, form_data: FormData, action: RequestAction
#     ) -> Any:
#         indices = self._extra_indices(form_data)
#         value = []
#         for index in indices:
#             self.field.id = f"{self.id}.{index}"
#             if isinstance(self.field, CollectionField):
#                 self.field._propagate_id()
#             value.append(await self.field.parse_form_data(request, form_data, action))
#         return value
#
#     async def serialize_value(
#             self, request: Request, value: Any, action: RequestAction
#     ) -> Any:
#         serialized_value = []
#         for item in value:
#             serialized_item_value = None
#             if item is not None:
#                 serialized_item_value = await self.field.serialize_value(
#                     request, item, action
#                 )
#             serialized_value.append(serialized_item_value)
#         return serialized_value
#
#     def _extra_indices(self, form_data: FormData) -> List[int]:
#         """
#         Return list of all indices.  For example, if field id is `foo` and
#         form_data contains following keys ['foo.0.bar', 'foo.1.baz'], then the indices are [0,1].
#         Note that some numbers can be skipped. For example, you may have [0,1,3,8]
#         as indices.
#         """
#         indices = set()
#         for name in form_data:
#             if name.startswith(self.id):
#                 idx = name[len(self.id) + 1 :].split(".", maxsplit=1)[0]
#                 if idx.isdigit():
#                     indices.add(int(idx))
#         return sorted(indices)
#
#     def _field_at(self, idx: Optional[int] = None) -> BaseField:
#         if idx is not None:
#             self.field.id = self.id + "." + str(idx)
#         else:
#             """To generate template string to be used in javascript"""
#             self.field.id = ""
#         if isinstance(self.field, CollectionField):
#             self.field._propagate_id()
#         return self.field
#
#     def additional_css_links(
#             self, request: Request, action: RequestAction
#     ) -> List[str]:
#         return self.field.additional_css_links(request, action)
#
#     def additional_js_links(self, request: Request, action: RequestAction) -> List[str]:
#         return self.field.additional_js_links(request, action)
#
