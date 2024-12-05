from nicegui import ui

from types import GenericAlias
from typing import Optional, Any, Union


class Elements:
    def __init__(self, render_o):

    def clear(self):
        for key, value in self.__dict__.items():
            if isinstance(value, ui.element):
                value.clear()
        print()

if __name__ == '__main__':
    elements = Elements()

    elements.asd = 1
    elements.qwe = "2"

    print(elements.asd)
    print(elements.qwe)

    elements.clear()

    print(elements.asd)
    print(elements.qwe)

    print()