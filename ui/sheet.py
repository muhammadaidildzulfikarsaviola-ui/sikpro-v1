from tksheet import Sheet as TkSheet


class Sheet:

    def __init__(self, main):

        self.main = main

        self.sheet = None
        self._column_headers = None

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
        if self._column_headers is None or len(self._column_headers) != total_cols:
            self._column_headers = [f"C{i+1}" for i in range(total_cols)]
        self.sheet.headers(newheaders=self._column_headers)

        self.sheet.refresh()

    def _column_changed(self, event=None):
        total_cols = self.sheet.total_columns()
        current = self.sheet.headers()
        if isinstance(current, (list, tuple)) and len(current) == total_cols:
            self._column_headers = [str(value) for value in current]
        else:
            self._column_headers = [f"C{i+1}" for i in range(total_cols)]
        self.update_headers()

    def get_sheet_data(self):

        return self.sheet.get_sheet_data()

    def set_sheet_data(self, data):

        self.sheet.set_sheet_data(data)
        self._column_headers = None

        self.update_headers()

    def set_sheet_data_with_headers(self, data, headers):
        """Replace worksheet contents while preserving imported/project labels."""
        self.sheet.set_sheet_data(data)
        total_cols = self.sheet.total_columns()
        normalized = [str(value).strip() for value in headers[:total_cols]]
        normalized.extend(f"C{i+1}" for i in range(len(normalized), total_cols))
        self._column_headers = normalized
        self.update_headers()

    def get_column_names(self):

        total_cols = self.sheet.total_columns()
        if self._column_headers is None or len(self._column_headers) != total_cols:
            self._column_headers = [f"C{i+1}" for i in range(total_cols)]
        return list(self._column_headers)

    def clear(self):

        current_data = self.sheet.get_sheet_data()

        rows = len(current_data) if current_data else 201

        cols = len(current_data[0]) if current_data and current_data[0] else 200

        empty_data = [
            ["" for _ in range(cols)]
            for _ in range(rows)
        ]

        self.sheet.set_sheet_data(empty_data)
        self._column_headers = None

        self.update_headers()

    def get_column_data(self, col_index):

        data = self.sheet.get_sheet_data()
        if col_index < 0:
            raise ValueError("Column index must be nonnegative")

        last_nonempty = -1
        for row_index, row in enumerate(data):
            value = row[col_index] if col_index < len(row) else ""
            if value is not None and str(value).strip() != "":
                last_nonempty = row_index

        if last_nonempty < 0:
            return []

        # Preserve interior blank cells so numeric validation can report their
        # original row instead of silently shifting later observations upward.
        return [
            row[col_index] if col_index < len(row) else ""
            for row in data[:last_nonempty + 1]
        ]

    def get_column_data_with_rows(self, col_index):
        """Return cells through the last used row with their 1-based row numbers."""
        values = self.get_column_data(col_index)
        return list(enumerate(values, start=1))
