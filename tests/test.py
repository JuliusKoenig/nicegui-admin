from types import GenericAlias
from typing import Optional, Any, Union


def is_list(type_: type) -> tuple[bool, Optional[type]]:
    if issubclass(type_, list):
        return True, Any
    elif issubclass(type(type_), GenericAlias):
        # get origin type
        origin_type = getattr(type_, '__origin__', None)
        if origin_type is list:
            # get args
            args = getattr(type_, '__args__', None)
            if args is None:
                return False, None
            if len(args) == 0:
                return True, Any
            elif len(args) > 1:
                return False, None
            return True, args[0]
    return False, None

if __name__ == '__main__':
    list_ = list
    list_str = list[Union[str, float]]
    list_int = list[int]
    list_float = list[float]
    list_bool = list[bool]
    list_list_str = list[list[str]]

    t_list = type(list_)
    t_list_str = type(list_str)
    t_list_int = type(list_int)
    t_list_float = type(list_float)
    t_list_bool = type(list_bool)
    t_list_list_str = type(list_list_str)

    # test if the type is a kind of list
    r_list, args_list = is_list(list_)
    r_list_str, args_list_str = is_list(list_str)
    r_list_int, args_list_int = is_list(list_int)
    r_list_float, args_list_float = is_list(list_float)
    r_list_bool, args_list_bool = is_list(list_bool)
    r_list_list_str, args_list_list_str = is_list(list_list_str)

    print()