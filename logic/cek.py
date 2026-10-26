import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Menu SPC")
root.geometry("500x300")

# Frame utama
main_frame = ttk.Frame(root, padding=20)
main_frame.pack(fill="both", expand=True)

# Judul
title = ttk.Label(
    main_frame,
    text="SPC Analysis Tools",
    font=("Segoe UI", 14, "bold")
)
title.pack(pady=(0, 15))

# Frame menu
menu_frame = ttk.Frame(main_frame)
menu_frame.pack()

# Kolom kiri (4 item)
left_frame = ttk.Frame(menu_frame)
left_frame.grid(row=0, column=0, padx=10)

# Kolom kanan (3 item)
right_frame = ttk.Frame(menu_frame)
right_frame.grid(row=0, column=1, padx=10)

left_buttons = [
    "Histogram",
    "Pareto",
    "Scatter",
    "Fishbone"
]

right_buttons = [
    "Flowchart",
    "Check Sheet",
    "Control Chart"
]

for item in left_buttons:
    ttk.Button(
        left_frame,
        text=item,
        width=22
    ).pack(pady=5)

for item in right_buttons:
    ttk.Button(
        right_frame,
        text=item,
        width=22
    ).pack(pady=5)

root.mainloop()