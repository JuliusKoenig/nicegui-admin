from nicegui import ui
from fastapi import Request

from niceguitools._crud.views.base import BaseView


class ListView(BaseView):
    async def builder(self, request: Request, asd: str) -> dict | None:
        ui.label(f"ListView for model '{self.model.__name__}' with argument 'asd' = '{asd}'")

        fields = self.fields

        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name'},
            {'name': 'age', 'label': 'Age', 'field': 'age'},
        ]
        rows = [
            {'name': 'Alice', 'age': 18},
            {'name': 'Bob', 'age': 21},
            {'name': 'Carol'},
        ]

        table = ui.table(columns=columns, rows=rows, row_key='name').classes('w-72')
        table.add_slot('header', r'''
            <q-tr :props="props">
                <q-th auto-width />
                <q-th v-for="col in props.cols" :key="col.name" :props="props">
                    {{ col.label }}
                </q-th>
            </q-tr>
        ''')
        table.add_slot('body', r'''
            <q-tr :props="props">
                <q-td auto-width>
                    <q-btn size="sm" color="accent" round dense
                        @click="props.expand = !props.expand"
                        :icon="props.expand ? 'remove' : 'add'" />
                </q-td>
                <q-td v-for="col in props.cols" :key="col.name" :props="props">
                    {{ col.value }}
                </q-td>
            </q-tr>
            <q-tr v-show="props.expand" :props="props">
                <q-td colspan="100%">
                    <div class="text-left">This is {{ props.row.name }}.</div>
                </q-td>
            </q-tr>
        ''')
