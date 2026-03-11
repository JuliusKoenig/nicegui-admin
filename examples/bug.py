# https://github.com/zauberzeug/nicegui/issues/5870

from nicegui import ui

columns = [
    {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True},
    {'name': 'age', 'label': 'Age', 'field': 'age', 'sortable': True},
]

rows = [
    {'name': 'Alice', 'age': 18},
    {'name': 'Bob', 'age': 21},
    {'name': 'Carol', 'age': 42},
]

table = ui.table(columns=columns, rows=rows, row_key='name')

with table.add_slot('header-cell-age'):
    with table.header('age'):
        ui.badge().props('color="blue" :label="props.col.label"')

with table.add_slot('body-cell-age'):
    with table.cell('age'):
        ui.badge().props('''
            :color="props.value < 21 ? 'red' : 'green'"
            :label="props.value"
        ''')

ui.run(port=8000, show=False, prod_js=False)
