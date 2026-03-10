from nicegui import ui

from nicegui_admin.elements.detail_table import DetailTable


@ui.page("/")
async def index():
    with DetailTable(columns=["Attribute",
                              "Value"]).classes("w-full"):
        ui.label('attribute1')
        ui.label('value1')
        ui.label('attribute2')
        ui.label('value2')
        ui.label('attribute3')
        ui.label('value3')
        ui.label('attribute4')
        ui.label('value4')
        ui.label('attribute5')
        ui.label('value5')

    dark = ui.dark_mode()
    ui.label('Switch mode:')
    ui.button('Dark', on_click=dark.enable)
    ui.button('Light', on_click=dark.disable)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8000, show=False, fastapi_docs=True)
