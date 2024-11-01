import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
import os
from .pyufodb import Relative_DB

class DBEditor(ctk.CTkToplevel):
    def __init__(self, parent, db_file):
        super().__init__(parent)
        self.title("Database Editor")
        self.db_file = db_file
        self.db = Relative_DB()
        if not self.db.load_from_file(self.db_file):
            messagebox.showerror("Error", "Failed to load database file.")
            self.destroy()
            return

        self.table_name = list(self.db.tables.keys())[0] if self.db.tables else None
        if not self.table_name:
            messagebox.showerror("Error", "No tables found in the database.")
            self.destroy()
            return
        
        self.table = self.db.tables[self.table_name]
        self.scale = 5.0
        self.cell_size = 30
        self.create_toolbar()
        self.create_bottombar()
        self.create_canvas_frame()
        self.draw_table()

        self.canvas.bind("<Button-1>", self.on_click)
        self.bind("<Shift-plus>", self.zoom_in)
        self.bind("<Shift-minus>", self.zoom_out)

    def create_toolbar(self):
        self.toolbar = ctk.CTkFrame(self, corner_radius=0)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        self.save_button = ctk.CTkButton(self.toolbar, text="Save", command=self.save_data)
        self.save_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.add_row_button = ctk.CTkButton(self.toolbar, text="Add Row", command=self.add_row)
        self.add_row_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.delete_row_button = ctk.CTkButton(self.toolbar, text="Delete Row", command=self.delete_row)
        self.delete_row_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.add_column_button = ctk.CTkButton(self.toolbar, text="Add Column", command=self.add_column)
        self.add_column_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.delete_column_button = ctk.CTkButton(self.toolbar, text="Delete Column", command=self.delete_column)
        self.delete_column_button.pack(side=tk.LEFT, padx=5, pady=5)

    def create_bottombar(self):
        self.bottombar = ctk.CTkFrame(self, corner_radius=0)
        self.bottombar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_canvas_frame(self):
        self.canvasFrame = ctk.CTkFrame(self, corner_radius=0, bg_color="#302c2c")
        self.canvasFrame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(self.canvasFrame, xscrollincrement=1, yscrollincrement=1, highlightthickness=0) # Important: highlightthickness=0
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1) # Use place for precise positioning

        self.scrollbar_y = ctk.CTkScrollbar(self.canvasFrame, orientation='vertical', command=self.canvas.yview)
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(yscrollcommand=self.scrollbar_y.set)

        self.scrollbar_x = ctk.CTkScrollbar(self.canvasFrame, orientation='horizontal', command=self.canvas.xview)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.config(xscrollcommand=self.scrollbar_x.set)

        self.canvas.bind("<MouseWheel>", self.on_mousewheel)  # Bind mousewheel event
        self.canvas.bind("<Button-4>", self.on_mousewheel)  # For Linux (scroll up)
        self.canvas.bind("<Button-5>", self.on_mousewheel)  # For Linux (scroll down)
        self.canvas.bind("<Control-MouseWheel>", self.on_control_mousewheel) # Bind Ctrl+MouseWheel


    def on_mousewheel(self, event):
        if event.num == 5 or event.delta < 0:  # Scroll down / zoom out
            self.zoom_out(event)
        elif event.num == 4 or event.delta > 0:  # Scroll up / zoom in
            self.zoom_in(event)

    def on_control_mousewheel(self, event): # For finer zoom control
        if event.delta > 0:
            self.zoom_in(event)
        else:
            self.zoom_out(event)

    def on_click(self, event):
        col = int(event.x / (self.cell_size * self.scale))
        row = int(event.y / (self.cell_size * self.scale)) - 1

        if 0 <= row < len(self.table.records) and 0 <= col < len(self.table.columns) + 1:
            columns = ["id"] + self.table.columns
            current_value = self.table.records[row].get_field(columns[col])

            # *** CUSTOM DIALOG ***
            dialog = tk.Toplevel(self)
            dialog.title("Edit Cell")

            label = tk.Label(dialog, text=f"Edit value for {columns[col]}:")
            label.pack(pady=5)

            entry = tk.Entry(dialog)
            entry.insert(0, current_value)
            entry.pack(pady=5)

            def on_ok():
                new_value = entry.get()
                if new_value is not None:
                    self.table.records[row].add(columns[col], new_value)
                    self.db.update(self.table_name, int(self.table.records[row].get_field('id')), {columns[col]: new_value})
                    self.db.save_to_file(self.db_file)
                    self.draw_table()
                dialog.destroy()

            ok_button = tk.Button(dialog, text="OK", command=on_ok)
            ok_button.pack(pady=5)

            dialog.transient(self)
            dialog.grab_set()
            self.wait_window(dialog)


    def save_data(self):
        if self.db.save_to_file(self.db_file):
            messagebox.showinfo("Success", "Database saved successfully.")
        else:
            messagebox.showerror("Error", "Failed to save database.")

    def add_row(self):
        new_record = {}
        for col in self.table.columns:
            new_record[col] = simpledialog.askstring("Input", f"Enter value for {col}:", parent=self)
        self.db.insert(self.table_name, new_record)
        self.table = self.db.tables[self.table_name]  # Update table after insert
        self.draw_table()

    def delete_row(self):
        row_index = simpledialog.askinteger("Input", "Enter row index to delete (starting from 0):", parent=self)
        if row_index is not None and 0 <= row_index < len(self.table.records):
            record_id = int(self.table.records[row_index].fields['id'])
            if self.db.delete_record(self.table_name, record_id):
                self.table = self.db.tables[self.table_name]
                self.draw_table()
            else:
                messagebox.showerror("Error", "Failed to delete row.")
        else:
            messagebox.showerror("Error", "Invalid row index.")


    def add_column(self):
        column_name = simpledialog.askstring("Input", "Enter new column name:", parent=self)
        if column_name:
            if column_name not in self.table.columns and column_name != "id":
                self.table.columns.append(column_name)
                self.db.tables[self.table_name] = self.table  # Update table in db
                self.draw_table() # Redraw the table with the new column.
            else:
                messagebox.showerror("Error", "Column name already exists or is 'id'.")

    def delete_column(self):
        column_index = simpledialog.askinteger("Input", "Enter column index to delete (starting from 0, excluding ID):", parent=self)
        if column_index is not None and 0 <= column_index < len(self.table.columns):
            deleted_column = self.table.columns.pop(column_index)
            self.db.tables[self.table_name] = self.table
            
            for record in self.table.records:
                if deleted_column in record.fields:
                    del record.fields[deleted_column]

            self.draw_table()
        else:
            messagebox.showerror("Error", "Invalid column index.")


    def draw_table(self):
        self.canvas.delete("all")
        columns = ["id"] + self.table.columns
        rows = self.table.records

        # Добавляем прямоугольник для фона
        canvas_width = len(columns) * self.cell_size * self.scale
        canvas_height = (len(rows) + 1) * self.cell_size * self.scale
        self.canvas.create_rectangle(0, 0, canvas_width, canvas_height, fill="#302c2c", outline="")

        for i, col in enumerate(columns):
            x = i * self.cell_size * self.scale
            y = 0
            self.canvas.create_text(x + self.cell_size * self.scale / 2, y + self.cell_size * self.scale / 2, text=col, fill="white")
            self.canvas.create_rectangle(x, y, x + self.cell_size * self.scale, y + self.cell_size * self.scale, outline="white")

        for i, row in enumerate(rows):
            y = (i + 1) * self.cell_size * self.scale
            for j, col in enumerate(columns):
                x = j * self.cell_size * self.scale
                value = row.get_field(col)
                self.canvas.create_text(x + self.cell_size * self.scale / 2, y + self.cell_size * self.scale / 2, text=value, fill="white")
                self.canvas.create_rectangle(x, y, x + self.cell_size * self.scale, y + self.cell_size * self.scale, outline="white")

        self.canvas.config(scrollregion=self.canvas.bbox("all"))


    def on_click(self, event):
        col = int(event.x / (self.cell_size * self.scale))
        row = int(event.y / (self.cell_size * self.scale)) - 1
        if row >= 0:
            columns = ["id"] + self.table.columns
            if col < len(columns):
                current_value = self.table.records[row].get_field(columns[col])
                new_value = ctk.CTkInputDialog(text=f"Edit value for {columns[col]}:", title="Edit Cell", initial_value=current_value).get_input()
                if new_value is not None:
                    self.table.records[row].add(columns[col], new_value)
                    self.db.update(self.table_name, int(self.table.records[row].get_field('id')), {columns[col]: new_value})
                    self.db.save_to_file(self.db_file)
                    self.draw_table()

    def zoom_in(self, event):
        self.scale *= 1.1
        self.draw_table()

    def zoom_out(self, event):
        self.scale *= 0.9
        self.draw_table()