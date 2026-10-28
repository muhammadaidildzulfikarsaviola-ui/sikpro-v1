from tksheet import Sheet as TkSheet


class Sheet:

    def __init__(self, main):

        self.main = main

        self.sheet = None
        self._column_headers = None
        self._generated_column_headers = None
        self._removed_column_header_flags = {}

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
        # These are tksheet's emitted event names (the shorter ``*_cols``
        # names are silently ignored by supported tksheet versions).
        self.sheet.extra_bindings([
            ("end_insert_columns", self._column_changed),
            ("end_add_columns", self._column_changed),
            ("end_delete_columns", self._column_changed),
            ("end_insert_rows", self._rows_changed),
            ("end_delete_rows", self._rows_changed),
            ("end_undo", lambda event: self._undo_redo_changed(event, "undo")),
            ("end_redo", lambda event: self._undo_redo_changed(event, "redo")),
            ("end_edit_header", self._header_edited),
        ])

        self.update_headers()

    def update_headers(self):

        total_cols = self.sheet.total_columns()
        if self._column_headers is None or len(self._column_headers) != total_cols:
            self._column_headers = [f"C{i+1}" for i in range(total_cols)]
            self._generated_column_headers = [True] * total_cols
        elif self._generated_column_headers is None or len(self._generated_column_headers) != total_cols:
            self._generated_column_headers = [False] * total_cols
        for index, generated in enumerate(self._generated_column_headers):
            if generated:
                self._column_headers[index] = f"C{index + 1}"
        # tksheet may mutate its internal header list during structural edits;
        # do not share the list that carries our generated/custom metadata.
        self.sheet.headers(newheaders=list(self._column_headers))

        self.sheet.refresh()

    def _column_changed(self, event=None, history_action=None):
        total_cols = self.sheet.total_columns()
        event_data = event if isinstance(event, dict) else {}
        old_headers = list(self._column_headers or [])
        old_flags = list(self._generated_column_headers or [])
        if len(old_flags) != len(old_headers):
            old_flags = [False] * len(old_headers)
        if not old_headers:
            old_headers = [f"C{i + 1}" for i in range(total_cols)]
            old_flags = [True] * total_cols

        deleted = event_data.get("deleted", {}).get("columns", {})
        added = event_data.get("added", {}).get("columns", {})
        # Undo/redo invert the original operation into an add/delete event.
        deleted_indexes = sorted(deleted) if isinstance(deleted, dict) else []
        added_columns = added.get("table", {}) if isinstance(added, dict) else {}
        added_indexes = sorted(added_columns) if isinstance(added_columns, dict) else []
        if deleted_indexes:
            removed = set(deleted_indexes)
            deleted_headers = event_data.get("deleted", {}).get("header", {})
            for index in deleted_indexes:
                if 0 <= index < len(old_flags) and index < len(old_headers):
                    header = str(deleted_headers.get(index, old_headers[index]))
                    self._removed_column_header_flags[(index, header)] = (old_headers[index], old_flags[index])
            old_flags = [flag for index, flag in enumerate(old_flags) if index not in removed]
            old_headers = [header for index, header in enumerate(old_headers) if index not in removed]
        elif added_indexes:
            added_headers = added.get("header", {}) if isinstance(added, dict) else {}
            for index in added_indexes:
                index = max(0, min(int(index), len(old_headers)))
                header = str(added_headers.get(index, "")) if isinstance(added_headers, dict) else ""
                if history_action:
                    restored = self._removed_column_header_flags.pop((index, header), None)
                    if restored is None:
                        label, generated = (header or f"C{index + 1}"), True
                    else:
                        label, generated = restored
                else:
                    label, generated = f"C{index + 1}", True
                    self._removed_column_header_flags.clear()
                old_headers.insert(index, label)
                old_flags.insert(index, generated)

        if len(old_headers) < total_cols:
            old_headers.extend(f"C{i + 1}" for i in range(len(old_headers), total_cols))
            old_flags.extend([True] * (total_cols - len(old_flags)))
        self._column_headers = old_headers[:total_cols]
        self._generated_column_headers = old_flags[:total_cols]
        self.update_headers()

    def _rows_changed(self, event=None):
        if not self.sheet:
            return
        count = self.sheet.total_rows()
        self.sheet.row_index([str(index + 1) for index in range(count)])
        self.sheet.refresh()

    def _undo_redo_changed(self, event=None, action=None):
        self._column_changed(event, history_action=action)
        self._rows_changed(event)

    def _header_edited(self, event=None):
        if not self.sheet:
            return
        event_data = event if isinstance(event, dict) else {}
        edited = event_data.get("cells", {}).get("header", {})
        if not self._generated_column_headers:
            self._generated_column_headers = [True] * self.sheet.total_columns()
        for index in edited:
            if 0 <= index < len(self._generated_column_headers):
                self._generated_column_headers[index] = False
        current = self.sheet.headers()
        if isinstance(current, (list, tuple)):
            self._column_headers = [str(value) for value in current]

    def get_sheet_data(self):

        return self.sheet.get_sheet_data()

    def set_sheet_data(self, data):

        self.sheet.set_sheet_data(data)
        self._column_headers = None
        self._generated_column_headers = None
        self._removed_column_header_flags.clear()

        self.update_headers()
        self._rows_changed()

    def set_sheet_data_with_headers(self, data, headers, generated_headers=None):
        """Replace worksheet contents while preserving imported/project labels."""
        self.sheet.set_sheet_data(data)
        self._removed_column_header_flags.clear()
        total_cols = self.sheet.total_columns()
        normalized = [str(value).strip() for value in headers[:total_cols]]
        normalized.extend(f"C{i+1}" for i in range(len(normalized), total_cols))
        self._column_headers = normalized
        if generated_headers is None:
            # Legacy project files cannot distinguish an imported "C3" from
            # an automatically generated label; infer the historical pattern.
            self._generated_column_headers = [
                index >= len(headers) or not str(headers[index]).strip()
                or str(headers[index]).strip() == f"C{index + 1}"
                for index in range(total_cols)
            ]
        else:
            self._generated_column_headers = list(generated_headers[:total_cols])
            self._generated_column_headers.extend(
                [True] * (total_cols - len(self._generated_column_headers))
            )
        self.update_headers()
        self._rows_changed()

    def get_generated_header_flags(self):
        total_cols = self.sheet.total_columns()
        if self._generated_column_headers is None or len(self._generated_column_headers) != total_cols:
            self._generated_column_headers = [True] * total_cols
        return list(self._generated_column_headers)

    def get_column_names(self):

        total_cols = self.sheet.total_columns()
        if self._column_headers is None or len(self._column_headers) != total_cols:
            self._column_headers = [f"C{i+1}" for i in range(total_cols)]
            self._generated_column_headers = [True] * total_cols
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
        self._generated_column_headers = None
        self._removed_column_header_flags.clear()

        self.update_headers()
        self._rows_changed()

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
