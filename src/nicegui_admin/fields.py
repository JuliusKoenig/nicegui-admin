import logging
from dataclasses import dataclass, field
from enum import Enum
from ipaddress import IPv4Address, IPv6Address
from typing import Any, TYPE_CHECKING
from uuid import UUID

from nicegui import ui
from nicegui.element import Element

from nicegui_admin.helpers import Unset

if TYPE_CHECKING:
    from nicegui_admin.form import Form

logger = logging.getLogger(__name__)
_type = type


@dataclass
class BaseField:
    """
    Base class for fields

    :param name: The name of the field, used to identify the field. It should be unique within a model.
    :param type: The type of the field.
    :param label: The label of the field, used for display purposes. If not provided, it will be generated from the name.
    :param icon: The icon of the field, used to display an icon next to the label.
    :param help_text: The help text of the field, used to provide additional information about the field in the UI.
    :param key: The key for data binding, if not provided, it will be the same as name
    :param not_none: Indicate if the field is not nullable.
    :param default: Indicate if the field has a default value. It can be either a static value or a dynamic value that is determined at runtime(python or database).
    :param default_value: The static default value of the field. Only used for display purposes.
    :param align: The alignment of the field in the list table. It can be "left", "center" or "right". Default is "left".
    :param searchable: Indicate if the fields is searchable
    :param orderable: Indicate if the fields is orderable
    :param exclude: Control field visibility in list page.
    :param exportable: Indicate if the fields is exportable
    :param cast_type: A type or tuple of types to cast the value from the database to ui or from ui to database. If the value is not of the specified type(s), it will be casted to the first type in the tuple. If casting fails, an exception will be raised.
    :param data_from_model_cast_type: A type or tuple of types to cast the value from the database to the ui. Default is the same as `cast_type`. If the value is not of the specified type(s), it will be casted to the first type in the tuple. If casting fails, an exception will be raised.
    :param data_to_model_cast_type: A type or tuple of types to cast the value from the ui to the database. Default is the same as `cast_type`. If the value is not of the specified type(s), it will be casted to the first type in the tuple. If casting fails, an exception will be raised.
    """

    name: str = field()
    type: type = field()
    label: str | Unset = field(default=Unset)
    icon: str | None = field(default=None)
    help_text: str | None = field(default=None)
    key: str | Unset = field(default=Unset)
    not_none: bool = field(default=False)

    class Default(str, Enum):
        STATIC = "static"
        DYNAMIC = "dynamic"

    default: Default | None = field(default=None)
    default_value: Any | None = field(default=None)
    align: str | None = field(default="left")
    searchable: bool = field(default=True)  # ToDo: implement searchable
    orderable: bool = field(default=True)
    exclude: list[str] = field(default_factory=list)
    exportable: bool = field(default=True)  # ToDo: implement searchable
    cast_type: tuple[_type] | None = field(default=None)
    data_from_model_cast_type: tuple[_type] | Unset | None = field(default=Unset)
    data_to_model_cast_type: tuple[_type] | Unset | None = field(default=Unset)

    def __post_init__(self) -> None:
        if self.name.startswith("_"):
            raise ValueError("Field name cannot start with an underscore")
        self.label = Unset.resolve(self.label, self.name.replace("_", " ").capitalize())
        self.key = Unset.resolve(self.key, self.name)
        self.data_from_model_cast_type = Unset.resolve(self.data_from_model_cast_type, self.cast_type)
        self.data_to_model_cast_type = Unset.resolve(self.data_to_model_cast_type, self.cast_type)

    async def data_from_model_none(self) -> Any:
        return None

    async def data_from_model(self,
                              data: dict[str, Any]) -> tuple[bool, Any]:
        is_none = False
        value = data.get(self.key, None)
        if value is None:
            is_none = True
            value = await self.data_from_model_none()
        else:
            if self.data_from_model_cast_type is not None:
                if type(value) not in self.data_from_model_cast_type:
                    for i, cast_type in enumerate(self.data_from_model_cast_type):
                        try:
                            value = cast_type(value)
                            break
                        except Exception as e:
                            if i < len(self.data_from_model_cast_type) - 1:
                                continue
                            raise e
        return is_none, value

    async def data_to_model_is_none(self,
                                    value: Any) -> bool:
        if value is None:
            return True
        return False

    async def data_to_model(self,
                            data: dict[str, Any]) -> Any:
        value = data.get(self.name, None)

        if await self.data_to_model_is_none(value=value):
            value = None
        else:
            if self.data_to_model_cast_type is not None:
                if type(value) not in self.data_to_model_cast_type:
                    for i, cast_type in enumerate(self.data_to_model_cast_type):
                        try:
                            value = cast_type(value)
                            break
                        except Exception as e:
                            if i < len(self.data_to_model_cast_type) - 1:
                                continue
                            raise e
        return value

    async def list_table_header_cell(self,
                                     table: ui.table) -> dict[str, Element]:
        elements = {}
        with table.header(column_name=self.name) as elements["header"]:
            if self.icon:
                elements["icon"] = ui.icon(name=self.icon).classes("field-label-header-icon mr-1")
            elements["label"] = ui.label(text=self.label).classes("field-label-header-text")
        if self.help_text:
            elements["header"].tooltip(self.help_text)
        return elements

    async def list_table_body_cell(self,
                                   table: ui.table) -> dict[str, Element]:
        elements = {}
        with table.cell(column_name=self.name) as elements["cell"]:
            elements["label"] = ui.label().props(":innerHTML=\"props.row." + self.name + "\"")
        return elements

    async def detail_label(self) -> dict[str, Element]:
        elements = {}
        with ui.row(align_items="center", wrap=False) as elements["row"]:
            if self.icon:
                elements["icon"] = ui.icon(name=self.icon).classes("field-label-header-icon")
            # noinspection PyAssignmentToLoopOrWithParameter
            with ui.column().classes("gap-0") as elements["column"]:
                elements["label"] = ui.label(text=self.label).classes("field-label-header-text")
                if self.help_text:
                    elements["help_text"] = ui.label(self.help_text).classes("field-label-sub-header-text")
        return elements

    async def detail_value(self,
                           value: Any) -> dict[str, Element]:
        return {"label": ui.label(text=value)}

    async def form_label(self,
                         field_handler: "Form.FieldHandler") -> dict[str, Element]:
        elements = {}
        with ui.row(align_items="center", wrap=False) as elements["row"]:
            if self.icon:
                elements["icon"] = ui.icon(name=self.icon).classes("field-label-header-icon")
            # noinspection PyAssignmentToLoopOrWithParameter
            with ui.column().classes("gap-0") as elements["column"]:
                # noinspection PyAssignmentToLoopOrWithParameter
                with ui.row(align_items="start", wrap=False).classes("gap-1") as elements["column_row"]:
                    elements["label"] = ui.label(text=self.label).classes("field-label-header-text")
                    if self.not_none:
                        elements["not_none"] = ui.label(text="(not none)").classes("field-form-label-not-none-text")
                    if self.default:
                        elements["use_default"] = ui.checkbox(text=f"Use default",
                                                  value=field_handler.use_default).classes("field-form-label-default-text").props("dense size=xs")
                        if self.default == self.Default.STATIC:
                            elements["use_default"].text += ": "
                            if type(self.default_value) == str:
                                elements["use_default"].text += f'"{self.default_value}"'
                            else:
                                elements["use_default"].text += str(self.default_value)
                        elif self.default == self.Default.DYNAMIC:
                            elements["use_default"].text += " factory"
                        elements["use_default"].bind_value(field_handler, "use_default")
                        elements["use_default"].on_value_change(
                            lambda: field_handler.validation_element.validate(return_result=False) if field_handler.validation_element is not None else None)
                if self.help_text:
                    elements["help_text"] = ui.label(self.help_text).classes("field-label-sub-header-text")
            return elements

    async def form_value(self,
                         field_handler: "Form.FieldHandler") -> dict[str, Element]:
        return {"label": ui.label(text=field_handler.original_value).bind_text(field_handler, "value")}

    async def form_value_validator(self,
                                   value: Any) -> None | str:
        if self.not_none:
            if await self.data_to_model_is_none(value=value):
                return "This field cannot be None"
        try:
            await self.data_to_model(data={self.name: value})
        except Exception as e:
            return f"Invalid value: {e}"
        return None


@dataclass
class BooleanField(BaseField):
    """
    This field displays the `true/false` value of a boolean property.
    """

    icon: str | None = field(default="adjust")
    cast_type: tuple[_type] | None = field(default=(bool,))

    async def list_table_body_cell(self,
                                   table: ui.table) -> dict[str, Element]:
        elements = {}
        with table.cell(column_name=self.name) as elements["cell"]:
            elements["badge"] = ui.badge().props(''':label="props.value ? 'true' : 'false'" :color="props.value ? 'green' : 'red'"''').classes("text-bold")
        return elements

    async def detail_value(self,
                           value: Any) -> dict[str, Element]:
        return {"badge": ui.badge(text="true" if value else "false", color="green" if value else "red").classes("text-bold")}

    async def form_value(self,
                         field_handler: "Form.FieldHandler") -> dict[str, Element]:
        return {"switch": ui.switch(value=field_handler.original_value).bind_value(field_handler, "value")}


@dataclass
class BaseStringField(BaseField):
    """
    A base class for fields that represent string values.

    :param content_type: The content type defines the
    :param empty_is_none: If True, an empty string is considered None.
    :param label_form_value: The value to use for the label in the form. Can be either None, "label", "help_text" or a string.
    If None, no label is displayed.
    If "label", the label is taken from the `label` attribute.
    If "help_text", the help text is taken from the `help_text` attribute.
    If a string is provided, it is used as the label.
    :param placeholder: Placeholder text for the input field in the UI.
    :param clearable: Whether the input field can be cleared by clicking the clear button.
    :param prefix: A prefix to prepend to the displayed value.
    :param suffix: A suffix to append to the displayed value.
    :param autocomplete: A list of strings representing the autocomplete options for the input field.
    """

    class ContentType(str, Enum):
        TEXT = "text"
        PASSWORD = "password"
        TEXTAREA = "textarea"
        EMAIL = "email"
        SEARCH = "search"
        TEL = "tel"
        FILE = "file"
        NUMBER = "number"
        URL = "url"
        TIME = "time"
        DATE = "date"
        DATETIME_LOCAL = "datetime-local"
        MONTH = "month"

    content_type: ContentType = field(default=ContentType.TEXT)
    empty_is_none: bool = field(default=False)

    class LabelFormValue(str, Enum):
        LABEL = "label"
        HELP_TEXT = "help_text"

    label_form_value: None | LabelFormValue | str = field(default=None)
    placeholder: str | None = field(default=None)
    clearable: bool = field(default=True)
    prefix: str | None = field(default=None)
    suffix: str | None = field(default=None)
    autocomplete: list[str] | None = field(default=None)
    cast_type: tuple[_type] | None = field(default=(str,))

    async def data_from_model_none(self) -> str:
        return ""

    async def data_to_model_is_none(self,
                                    value: Any) -> bool:
        if await super().data_to_model_is_none(value):
            return True
        if self.empty_is_none and isinstance(value, str) and value.strip() == "":
            return True
        return False

    async def form_value(self,
                         field_handler: "Form.FieldHandler") -> dict[str, Element]:
        elements = {}
        value_label = None
        if self.label_form_value is not None:
            if self.label_form_value == StringField.LabelFormValue.LABEL:
                value_label = self.label
            elif self.label_form_value == StringField.LabelFormValue.HELP_TEXT:
                value_label = self.help_text
            else:
                value_label = self.label_form_value
        elements["input"] = ui.input(value=field_handler.original_value,
                                 label=value_label,
                                 placeholder=self.placeholder,
                                 prefix=self.prefix,
                                 suffix=self.suffix,
                                 autocomplete=self.autocomplete)
        elements["input"].bind_value(field_handler,
                                 "value",
                                 forward=lambda value: "" if value is None else value)  # hint: forward is required because clearable sets value to None
        elements["input"].props(f"type='{self.content_type.value}'")
        if self.clearable:
            elements["input"].props("clearable")
        field_handler.validation_element = elements["input"]
        return elements


@dataclass
class StringField(BaseStringField):
    """
    ToDo

    :param maxlength: Maximum length of the string. If provided, it can be used for validation and UI hints.
    :param minlength: Minimum length of the string. If provided, it can be used for validation and UI hints.
    :param allowed_characters: A string of allowed characters. If provided, it can be used for validation and UI hints.
    :param mask: A string representing the mask to apply to the input field.
    Only available if the content_type is one of ‘text’, ‘search’, ‘url’, ‘tel’, or ‘password’.
    Examples:

    | Token | Description                                        |
    |-------|----------------------------------------------------|
    | #     | Numeric                                            |
    | S     | Letter, a to z, case insensitive                   |
    | N     | Alphanumeric, case insensitive for letters         |
    | A     | Letter, transformed to uppercase                   |
    | a     | Letter, transformed to lowercase                   |
    | X     | Alphanumeric, transformed to uppercase for letters |
    | x     | Alphanumeric, transformed to lowercase for letters |
    _See the full list of [token types](https://github.com/quasarframework/quasar/blob/dev/ui/src/components/input/use-mask.js#L6)._
    :param fill_mask: If True, the mask will be initially filled with the tokens and the user has to fill the form.
    If False, the mask will be filled with the tokens by typing.
    :param unmasked_value: If True, the value sent to the server will be the unmasked value. If False, the value sent to the server will be the masked value.
    """

    maxlength: int | None = field(default=None)
    minlength: int | None = field(default=None)
    allowed_characters: str | None = field(default=None)
    mask: str | None = field(default=None)
    fill_mask: bool = field(default=True)
    unmasked_value: bool = field(default=True)

    icon: str | None = field(default="short_text")

    async def form_value(self,
                         field_handler: "Form.FieldHandler") -> dict[str, Element]:
        elements = await super().form_value(field_handler=field_handler)
        if self.mask is not None:
            elements["input"].props(f"mask='{self.mask}'")
            if self.fill_mask:
                elements["input"].props("fill-mask")
            if self.unmasked_value:
                elements["input"].props("unmasked-value")
        return elements

    async def form_value_validator(self,
                                   value: Any) -> None | str:
        result = await super().form_value_validator(value=value)
        if result is not None:
            return result
        if self.minlength is not None:
            if len(value) < self.minlength:
                return f"Minimum length is {self.minlength}"
        if self.maxlength is not None:
            if len(value) > self.maxlength:
                return f"Maximum length is {self.maxlength}"
        if self.allowed_characters is not None:
            if any(c not in self.allowed_characters for c in value):
                return f"Only the following characters are allowed: {self.allowed_characters}"
        return None


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
#                 "not_none": self.not_none,
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

    icon: str | None = field(default="numbers")
    max: int | None = None
    min: int | None = None
    step: int | None = None
    placeholder: str | None = None
    # clearable
    # prefix:	a prefix to prepend to the displayed value
    # suffix:	a suffix to append to the displayed value
    # format:	a string like "%.2f" to format the displayed value


@dataclass
class IntegerField(BaseNumberField):
    """
    ToDo
    """

    cast_type: tuple[_type] | None = field(default=(int,))


@dataclass
class DecimalField(BaseNumberField):
    """
    ToDo
    """

    # precision:	the number of decimal places allowed (default: no limit, negative: decimal places before the dot)
    data_from_model_cast_type: tuple[_type] | Unset | None = field(default=(float,))


@dataclass
class FloatField(BaseNumberField):
    """
    ToDo
    """

    cast_type: tuple[_type] | None = field(default=(float,))


@dataclass
class IPAddressField(StringField):
    """
    ToDo
    """

    icon: str | None = field(default="location_on")
    data_from_model_cast_type: tuple[_type] | Unset | None = field(default=(str,))
    data_to_model_cast_type: tuple[_type] | Unset | None = field(default=(IPv4Address, IPv6Address))


@dataclass
class UUIDField(StringField):
    """
    ToDo
    """

    icon: str | None = field(default="fingerprint")
    data_from_model_cast_type: tuple[_type] | Unset | None = field(default=(str,))
    data_to_model_cast_type: tuple[_type] | Unset | None = field(default=(UUID,))


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
#                 "not_none": self.not_none,
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
#         self.not_none = not_none
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
#         self.not_none = not_none
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


@dataclass
class DummyField(BaseField):
    ...
    # ToDo: remove this if it is not needed anymore
