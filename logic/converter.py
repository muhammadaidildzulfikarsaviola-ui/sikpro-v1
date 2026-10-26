import tkinter as tk
from tkinter import ttk, messagebox


class AttributeConversionEngine:

    @staticmethod
    def clean_numeric(data):

        cleaned = []

        for x in data:

            try:
                cleaned.append(float(x))

            except:
                cleaned.append(None)

        return cleaned

    @staticmethod
    def convert_np_to_p(defectives, sample_sizes):

        result = []

        for d, n in zip(defectives, sample_sizes):

            if d is None or n is None:
                result.append("")
                continue

            if n == 0:
                result.append("")
                continue

            result.append(d / n)

        return result

    @staticmethod
    def convert_p_to_np(proportions, sample_sizes):

        result = []

        for p, n in zip(proportions, sample_sizes):

            if p is None or n is None:
                result.append("")
                continue

            result.append(p * n)

        return result

    @staticmethod
    def convert_c_to_u(defects, units):

        result = []

        for c, u in zip(defects, units):

            if c is None or u is None:
                result.append("")
                continue

            if u == 0:
                result.append("")
                continue

            result.append(c / u)

        return result

    @staticmethod
    def convert_u_to_c(rates, units):

        result = []

        for u, n in zip(rates, units):

            if u is None or n is None:
                result.append("")
                continue

            result.append(u * n)

        return result


class AttributeConverterPopup(tk.Toplevel):

    def __init__(self, main, sheet):

        super().__init__(main.root)

        self.main = main
        self.sheet = sheet

        self.title("Attribute Converter")

        self.geometry("850x600")

        self.numeric_columns = {}

        self.create_ui()

    def create_ui(self):

        main_frame = ttk.Frame(self)

        main_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

        ttk.Label(
            main_frame,
            text="Conversion Type",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        self.mode_var = tk.StringVar(
            value="np_to_p"
        )

        modes_frame = ttk.Frame(main_frame)

        modes_frame.pack(
            fill="x",
            pady=(5, 15)
        )

        ttk.Radiobutton(
            modes_frame,
            text="NP → P",
            variable=self.mode_var,
            value="np_to_p"
        ).pack(anchor="w")

        ttk.Radiobutton(
            modes_frame,
            text="P → NP",
            variable=self.mode_var,
            value="p_to_np"
        ).pack(anchor="w")

        ttk.Radiobutton(
            modes_frame,
            text="C → U",
            variable=self.mode_var,
            value="c_to_u"
        ).pack(anchor="w")

        ttk.Radiobutton(
            modes_frame,
            text="U → C",
            variable=self.mode_var,
            value="u_to_c"
        ).pack(anchor="w")

        columns = self.sheet.get_column_names()

        for i, col in enumerate(columns):

            data = AttributeConversionEngine.clean_numeric(
                self.sheet.get_column_data(i)
            )

            valid = [
                x for x in data
                if x is not None
            ]

            if len(valid) == 0:
                continue

            self.numeric_columns[col] = i

        ttk.Label(
            main_frame,
            text="Source Column",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        self.source_column_var = tk.StringVar()

        self.source_combo = ttk.Combobox(
            main_frame,
            textvariable=self.source_column_var,
            values=list(self.numeric_columns.keys()),
            state="readonly"
        )

        self.source_combo.pack(
            fill="x",
            pady=(5, 15)
        )

        ttk.Label(
            main_frame,
            text="Sample / Unit Column",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        self.sample_column_var = tk.StringVar()

        self.sample_combo = ttk.Combobox(
            main_frame,
            textvariable=self.sample_column_var,
            values=list(self.numeric_columns.keys()),
            state="readonly"
        )

        self.sample_combo.pack(
            fill="x",
            pady=(5, 15)
        )

        ttk.Label(
            main_frame,
            text="Output Column",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        headers = self.sheet.get_column_names()

        self.output_name_var = tk.StringVar()

        self.output_combo = ttk.Combobox(
            main_frame,
            textvariable=self.output_name_var,
            values=headers,
            state="readonly"
        )

        self.output_combo.pack(
            fill="x",
            pady=(5, 15)
        )

        for col in headers:

            col_index = headers.index(col)

            col_data = self.sheet.get_column_data(col_index)

            valid_data = [
                x for x in col_data
                if str(x).strip() != ""
            ]

            if len(valid_data) == 0:

                self.output_name_var.set(col)

                break

        ttk.Button(
            main_frame,
            text="Convert",
            command=self.convert
        ).pack(
            fill="x",
            ipady=6,
            pady=(10, 0)
        )

    def convert(self):

        source_col = self.source_column_var.get()

        sample_col = self.sample_column_var.get()

        if source_col == "" or sample_col == "":

            messagebox.showerror(
                "Error",
                "Select source and sample column"
            )

            return

        source_idx = self.numeric_columns[
            source_col
        ]

        sample_idx = self.numeric_columns[
            sample_col
        ]

        source_data = AttributeConversionEngine.clean_numeric(
            self.sheet.get_column_data(source_idx)
        )

        sample_data = AttributeConversionEngine.clean_numeric(
            self.sheet.get_column_data(sample_idx)
        )

        mode = self.mode_var.get()

        if mode == "np_to_p":

            result = AttributeConversionEngine.convert_np_to_p(
                source_data,
                sample_data
            )

        elif mode == "p_to_np":

            result = AttributeConversionEngine.convert_p_to_np(
                source_data,
                sample_data
            )

        elif mode == "c_to_u":

            result = AttributeConversionEngine.convert_c_to_u(
                source_data,
                sample_data
            )

        else:

            result = AttributeConversionEngine.convert_u_to_c(
                source_data,
                sample_data
            )

        output_name = self.output_name_var.get().strip()

        AttributePreviewPopup(
            self.main,
            self.sheet,
            result,
            output_name
        )


class AttributePreviewPopup(tk.Toplevel):

    def __init__(
        self,
        main,
        sheet,
        result_data,
        column_name
    ):

        super().__init__(main.root)

        self.main = main
        self.sheet = sheet

        self.result_data = result_data

        self.column_name = column_name

        self.title("Conversion Preview")

        self.geometry("700x600")

        self.create_ui()

    def create_ui(self):

        main_frame = ttk.Frame(self)

        main_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

        ttk.Label(
            main_frame,
            text=self.column_name,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")

        stats_frame = ttk.LabelFrame(
            main_frame,
            text="Statistics",
            padding=10
        )

        stats_frame.pack(
            fill="x",
            pady=(10, 10)
        )

        valid = [
            x for x in self.result_data
            if isinstance(x, (int, float))
        ]

        if len(valid) > 0:

            mean_val = round(sum(valid) / len(valid), 6)

            min_val = round(min(valid), 6)

            max_val = round(max(valid), 6)

        else:

            mean_val = "-"
            min_val = "-"
            max_val = "-"

        ttk.Label(
            stats_frame,
            text=f'Total Rows : {len(self.result_data)}'
        ).pack(anchor="w")

        ttk.Label(
            stats_frame,
            text=f'Mean : {mean_val}'
        ).pack(anchor="w")

        ttk.Label(
            stats_frame,
            text=f'Min : {min_val}'
        ).pack(anchor="w")

        ttk.Label(
            stats_frame,
            text=f'Max : {max_val}'
        ).pack(anchor="w")

        preview_frame = ttk.LabelFrame(
            main_frame,
            text="Preview",
            padding=10
        )

        preview_frame.pack(
            fill="both",
            expand=True
        )

        preview_container = ttk.Frame(
            preview_frame
        )

        preview_container.pack(
            fill="both",
            expand=True
        )

        scrollbar = ttk.Scrollbar(
            preview_container,
            orient="vertical"
        )

        self.listbox = tk.Listbox(
            preview_container,
            yscrollcommand=scrollbar.set
        )

        scrollbar.config(
            command=self.listbox.yview
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.listbox.pack(
            side="left",
            fill="both",
            expand=True
        )

        for i, value in enumerate(self.result_data):

            self.listbox.insert(
                "end",
                f'{i + 1} : {value}'
            )

        ttk.Button(
            main_frame,
            text="Insert to Datasheet",
            command=self.insert_to_sheet
        ).pack(
            fill="x",
            ipady=6,
            pady=(15, 0)
        )

    def insert_to_sheet(self):

        try:

            headers = self.sheet.sheet.headers()

            target_col = headers.index(
                self.column_name
            )

            data = self.sheet.sheet.get_sheet_data()

            max_rows = len(data)

            new_column = self.result_data[:]

            while len(new_column) < max_rows:

                new_column.append("")

            for row in range(max_rows - 1):

                while len(data[row + 1]) <= target_col:

                    data[row + 1].append("")

                value = new_column[row]

                if isinstance(value, float):

                    value = round(value, 3)

                data[row + 1][target_col] = value

            self.sheet.sheet.set_sheet_data(data)

            self.sheet.sheet.refresh()

            self.sheet.sheet.redraw()

        except Exception as e:

            messagebox.showerror(
                "Error",
                str(e)
            )

            return

        messagebox.showinfo(
            "Success",
            f'{self.column_name} inserted'
        )

        self.destroy()