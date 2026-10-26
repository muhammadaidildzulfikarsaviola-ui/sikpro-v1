from tksheet import Sheet as TkSheet


class Sheet:

    def __init__(self, main):

        self.main = main

        self.sheet = None

    def build(self, parent):

        self.sheet = TkSheet(parent)

        self.sheet.pack(fill="both", expand=True)

        rows = 201
        cols = 200

        data = [
            ["" for _ in range(cols)]
            for _ in range(rows)
        ]

        row_index = [str(i + 1) for i in range(rows)]

        self.sheet.set_sheet_data(data)

        self.sheet.row_index(row_index)

        self.sheet.set_column_widths([120] * cols)

        self.sheet.set_row_heights([22] * rows)

        self.sheet.enable_bindings((
            "single_select",
            "row_select",
            "column_select",
            "drag_select",

            "column_width_resize",
            "row_height_resize",

            "double_click_column_resize",
            "double_click_row_resize",

            "arrowkeys",

            "copy",
            "paste",
            "delete",
            "undo",

            "edit_cell",
            "edit_header",

            "rc_select",

            "rc_insert_column",
            "rc_delete_column",

            "rc_insert_row",
            "rc_delete_row",

            "rc_popup_menu",

            "select_all"
        ))
        self.sheet.after(
            100,
            self.update_headers
        )

        # AUTO UPDATE HEADER
        self.sheet.extra_bindings([
            ("end_insert_cols", self._column_changed),
            ("end_delete_cols", self._column_changed),
        ])

        self.update_headers()

    def update_headers(self):

        total_cols = self.sheet.total_columns()

        headers = [
            f"C{i+1}"
            for i in range(total_cols)
        ]

        self.sheet.headers(newheaders=headers)

        self.sheet.refresh()

    def _column_changed(self, event=None):

        self.update_headers()

    def get_sheet_data(self):

        return self.sheet.get_sheet_data()

    def set_sheet_data(self, data):

        self.sheet.set_sheet_data(data)

        self.update_headers()

    def get_column_names(self):

        total_cols = self.sheet.total_columns()

        return [
            f"C{i+1}"
            for i in range(total_cols)
        ]

    def clear(self):

        current_data = self.sheet.get_sheet_data()

        rows = len(current_data)

        cols = len(current_data[0])

        empty_data = [
            ["" for _ in range(cols)]
            for _ in range(rows)
        ]

        self.sheet.set_sheet_data(empty_data)

        self.update_headers()

    def get_column_data(self, col_index):

        data = self.sheet.get_sheet_data()

        values = []

        for row in data:

            if not row:
                continue

            if col_index >= len(row):
                continue

            value = row[col_index]

            if value is None:
                continue

            if str(value).strip() != "":

                values.append(value)

        return values