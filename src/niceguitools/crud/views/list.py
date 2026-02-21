from nicegui import ui
from fastapi import Request

from niceguitools.crud.views.base import BaseView


class ListView(BaseView):
    async def builder(self, request: Request, asd: str) -> dict | None:
        ui.label(f"ListView for model '{self.model.__name__}' with argument 'asd' = '{asd}'")

        fields = self.fields

        print()
