from typing import Any, Dict, Union


class NiceGuiAdminException(Exception):
    pass


# ToDo: check if needed
class FormValidationError(NiceGuiAdminException):
    def __init__(self, errors: Dict[Union[str, int], Any]) -> None:
        self.errors = errors

    def has(self, name: str) -> bool:
        return self.errors.get(name, None) is not None

    def msg(self, name: str) -> Any:
        return self.errors.get(name, None)
#
# # ToDo: check if needed
# class LoginFailed(NiceGuiAdminException):
#     def __init__(self, msg: str) -> None:
#         super().__init__(msg)
#         self.msg = msg
#
# # ToDo: check if needed
# class ActionFailed(NiceGuiAdminException):
#     def __init__(self, msg: str) -> None:
#         super().__init__(msg)
#         self.msg = msg


class NotSupportedAnnotation(NiceGuiAdminException):
    pass
