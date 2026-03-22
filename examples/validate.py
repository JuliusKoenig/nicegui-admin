import random
import string
from dataclasses import dataclass

from nicegui import ui

async def validate_input(value):
    return "".join(random.choices(string.ascii_letters, k=10))



@ui.page("/")
async def main():
    def set_validation_message():
        elm.error = "".join(random.choices(string.ascii_letters, k=10))

    elm = ui.input(value="test", validation=validate_input)
    ui.button("Validate", on_click=set_validation_message)



if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8000, show=False, prod_js=False)
