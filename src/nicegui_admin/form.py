from typing import Any, TYPE_CHECKING

from nicegui import binding
from nicegui.elements.mixins.validation_element import ValidationElement

if TYPE_CHECKING:
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
            # self._form_validator_result: None | str = None
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

                # update correctness of form
                correct = True
                for handler in self.form.field_handler.values():
                    if handler.validation_element is not None:
                        if handler.validation_element.error is not None:
                            correct = False
                self.form.correct = correct

            patched_class.error = property(fget=fget, fset=fset)
            self._validation_element.__class__ = patched_class


            value.validate(return_result=False)

    correct: bool = binding.BindableProperty()

    def __init__(self):
        self._field_handler = []
        self.correct = True

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
