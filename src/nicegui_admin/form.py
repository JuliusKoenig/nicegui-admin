from typing import Any, TYPE_CHECKING

from nicegui import binding
from nicegui.elements.mixins.validation_element import ValidationElement

from nicegui_admin.exceptions import FormValidationError

if TYPE_CHECKING:
    from nicegui_admin.views import BaseCrudView
    from nicegui_admin.fields import BaseField


class Form:
    class FieldHandler:
        value: Any = binding.BindableProperty()
        use_default: bool = binding.BindableProperty()

        def __init__(self,
                     form: "Form",
                     field: "BaseField",
                     value: Any = None):
            self._form: Form = form
            self._field: "BaseField" = field
            self._original_value: Any = value
            self.value = value
            if self.value is None:
                self.use_default = True
            else:
                self.use_default = False
            self._validation_element: ValidationElement | None = None

        @property
        def form(self) -> "Form":
            return self._form

        @property
        def field(self) -> "BaseField":
            return self._field

        @property
        def original_value(self) -> Any:
            return self._original_value

        @property
        def validation_element(self) -> ValidationElement | None:
            return self._validation_element

        @validation_element.setter
        def validation_element(self, value: ValidationElement | None) -> None:
            if not isinstance(value, ValidationElement):
                raise TypeError(f"validation_element must be a ValidationElement, not {type(value)}")
            self._validation_element = value

            # patch validation_element error property
            parent_class = type(self._validation_element)
            patched_class = type(
                f"Form{parent_class.__name__}",
                (parent_class,),
                {},
            )

            def fget(_self) -> str | None:
                return parent_class.error.fget(_self)

            def fset(_self, error: str | None) -> None:
                parent_class.error.fset(_self, error)

                # update errors of form
                errors = []
                for handler in self.form.field_handler.values():
                    if handler.validation_element is not None:
                        if handler.validation_element.error is not None:
                            errors.append(f"Field '{handler.field.name}': {handler.validation_element.error}")
                self.form.errors = errors

            patched_class.error = property(fget=fget, fset=fset)
            self._validation_element.__class__ = patched_class

            async def validator(_value: Any) -> None | str:
                if self.use_default:  # disable validation for default values
                    return None
                form_field_result = None
                try:
                    await self.form.validate()
                except FormValidationError as exc:
                    form_field_result = exc.errors.get(self._field.name)
                field_result = await self._field.form_value_validator(value=_value)
                if field_result is not None:
                    return field_result
                return form_field_result

            self._validation_element.validation = validator

    errors: list[str] = binding.BindableProperty()

    def __init__(self, view: "BaseCrudView"):
        self._view = view
        self._field_handler = []
        self.errors = []

    @property
    def view(self) -> "BaseCrudView":
        return self._view

    @property
    def data(self) -> dict[str, Any]:
        result = {}
        for field_name, field_handler in self.field_handler.items():
            if not field_handler.use_default:
                if field_handler.value != field_handler.original_value:
                    result[field_name] = field_handler.value
                else:
                    result[field_name] = field_handler.original_value
        return result

    @property
    def field_handler(self) -> dict[str, "Form.FieldHandler"]:
        return {handler.field.name: handler for handler in self._field_handler}

    @property
    def fields(self) -> list["BaseField"]:
        fields = []
        for handler in self._field_handler:
            if handler.use_default:
                continue
            fields.append(handler.field)
        return fields

    def add_field_handler(self,
                          field: "BaseField",
                          value: Any = None) -> "Form.FieldHandler":
        if field.name in self.field_handler:
            raise RuntimeError(f"Field {field} already exists")
        handler = Form.FieldHandler(form=self,
                                    field=field,
                                    value=value)
        self._field_handler.append(handler)
        return handler

    async def validate(self) -> None:
        try:
            await self.view.form_validate(form=self)
        except FormValidationError as exc:
            for fn, error_message in exc.errors.items():
                if self.field_handler[fn].validation_element is not None:
                    self.field_handler[fn].validation_element.error = error_message
            raise exc
