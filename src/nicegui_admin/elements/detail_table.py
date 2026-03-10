from typing_extensions import Self

from nicegui import ui

ui.add_css("""
           body.body--light {
               --detail-table-border-color: rgba(31, 41, 55, 0.2);
               --detail-table-header-background: rgba(246, 248, 251, 1);
               --detail-table-header-font-color: rgba(108, 122, 145, 1);
               --detail-table-header-font-weight: 600;
               --detail-table-body-background: transparent;
               --detail-table-body-font-color: rgba(0, 0, 0, 1);
               --detail-table-body-font-weight: 50;
           }

           body.body--dark {
               --detail-table-border-color: rgba(246, 248, 251, 0.2);
               --detail-table-header-background: rgba(31, 41, 55, 1);
               --detail-table-header-font-color: rgba(158, 172, 195, 1);
               --detail-table-header-font-weight: 600;
               --detail-table-body-background: transparent;
               --detail-table-body-font-color: rgba(255, 255, 255, 1);
               --detail-table-body-font-weight: 50;
           }

           .detail-table {
               margin-bottom: 0;
               vertical-align: top;
           }

           .detail-table > :not(caption) > * {
               border-width: 1px;
           }

           .detail-table > :not(caption) > * > * {
               padding: 0.75rem 0.75rem;
               background-color: var(--detail-table-body-background);
               color: var(--detail-table-body-font-color);
               vertical-align: middle;
               border-width: 1px;
               border-color: var(--detail-table-border-color);
           }

           .detail-table > tbody {
               vertical-align: inherit;
           }

           .detail-table > thead {
               vertical-align: bottom;
           }

           .detail-table thead th {
               background: var(--detail-table-header-background);
               font-size: 0.75rem;
               font-weight: var(--detail-table-header-font-weight);
               text-transform: uppercase;
               letter-spacing: 0.04em;
               text-align: start;
               line-height: 1rem;
               color: var(--detail-table-header-font-color);
               padding-top: 0.5rem;
               padding-bottom: 0.5rem;
               white-space: nowrap;
           }

           @media (max-width: 767.98px) {
               .detail-table {
                   display: block;
               }

               .detail-table thead {
                   display: none;
               }

               .detail-table tbody,
               .detail-table tr {
                   display: flex;
                   flex-direction: column;
               }

               .detail-table td {
                   display: block;
                   padding: 0.75rem 0.75rem !important;
                   border: none;
                   color: var(--detail-table-body-font-color) !important;
               }

               .detail-table td[data-label]:before {
                   font-size: 0.75rem;
                   font-weight: var(--detail-table-header-font-weight);
                   text-transform: uppercase;
                   letter-spacing: 0.04em;
                   line-height: 1rem;
                   color: var(--detail-table-header-font-color);
                   content: attr(data-label);
                   display: block;
               }

               .detail-table tr {
                   border: none;
                   border-top: 1px solid var(--detail-table-border-color);
                   border-bottom: 1px solid var(--detail-table-border-color);
               }
           }""", shared=True)


class DetailTable(ui.element):
    def __init__(self, columns: list[str]):
        super().__init__(tag="table")
        self.classes("detail-table")

        self._columns = columns

        self._thead = ui.element(tag="thead")
        self._thead.move(self)
        self._tbody = ui.element(tag="tbody")
        self._tbody.move(self)

        with self._thead:
            self._thead_tr = ui.element(tag="tr")

        with self._thead_tr:
            for column in self._columns:
                ui.html(tag="th", content=column)

        self._current_slot_children = None

    @property
    def columns(self) -> tuple[str, ...]:
        return tuple(self._columns)

    def __enter__(self) -> Self:
        self.default_slot.__enter__()
        self._current_slot_children = len(self.default_slot.children)
        return self

    def __exit__(self, *_) -> None:
        self.default_slot.__exit__(*_)
        new_children = self.default_slot.children[self._current_slot_children:]
        if len(new_children) > 0:
            self.add_row(*new_children)
        self._current_slot_children = None

    def add_row(self, *elements: ui.element) -> None:
        fridge = list(elements)
        while len(fridge) > 0:
            tr = ui.element(tag="tr")
            for column in self.columns:
                td = ui.element(tag="td").props(f"data-label=\"{column}\"")
                if len(fridge) > 0:
                    fridge.pop(0).move(td)
                td.move(tr)
            tr.move(self._tbody)