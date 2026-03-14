import random
import string
from dataclasses import dataclass

from nicegui import ui


@dataclass
class Field:
    async def render(self, value):
        async def validate(_value):
            return await self.validate(value=_value, elements=elements)

        elements = {}
        elements["input"] = ui.input(value=value, validation=validate)
        elements["label"] = ui.label("UNSET")
        return elements

    async def validate(self, value, elements) -> str | None:
        # ui.notify(value)

        elements["label"].text = value

        return "".join(random.choices(string.ascii_letters, k=10))


field = Field()


@ui.page("/")
async def main():
    ui.switch().bind_value(field, "VALIDATION")

    value = "qwerty"
    await field.render(value=value)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8000, show=False, prod_js=False)
