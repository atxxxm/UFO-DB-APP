from customtkinter import *
from tkinter import messagebox, simpledialog
import os
from .commands import execute_command
from .pyufodb import Relative_DB


class DBEditor(CTkToplevel):
    def __init__(self, parent, db_file):
        super().__init__(parent)
        self.title("DB Editor")
        self.db_file = db_file
        self.db = Relative_DB()
        if not self.db.load_from_file(self.db_file):
            messagebox.showerror("Error", "Failed to load database file.")
            self.destroy()
            return
        self.table_name = list(self.db.tables.keys())[0]
        self.table = self.db.tables[self.table_name]
        self.create_toolbar()
        self.create_table_frame()
        self.populate_table()
        self.create_bottombar()

    def create_toolbar(self):
        toolbar = CTkFrame(self)
        toolbar.pack(fill=X, padx=5, pady=5)
        CTkButton(toolbar, text="Save", command=self.save_changes).pack(side=LEFT, padx=5)
        CTkButton(toolbar, text="Add Row", command=self.add_row).pack(side=LEFT, padx=5)
        CTkButton(toolbar, text="Remove Row", command=self.remove_row).pack(side=LEFT, padx=5)
        CTkButton(toolbar, text="Add Column", command=self.add_column).pack(side=LEFT, padx=5)  # Add Column button



    def add_column(self):
        new_column_name = simpledialog.askstring("Add Column", "Enter new column name:")
        if new_column_name:
            if new_column_name in self.table.columns:
                messagebox.showwarning("Column Exists", "A column with that name already exists.")
                return

            self.table.columns.append(new_column_name) # Add to table's columns

            # Update the database file (important!)
            self.db.tables[self.table_name] = self.table  # Update the table in the database
            self.db.save_to_file(self.db_file) # Save to ensure it remains consistent

            self.populate_table() # Refresh display

    def create_table_frame(self):
        self.TableFrame = CTkScrollableFrame(self)
        self.TableFrame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        self.entry_grid = {}


    def populate_table(self):
        for child in self.TableFrame.winfo_children():
            child.destroy()

        columns = self.table.columns + ["id"]

        # Add header row (column names)
        for j, col in enumerate(columns):
            textbox = CTkTextbox(self.TableFrame, width=100, height=25, wrap="word")
            textbox.insert("0.0", col)  # Insert column name
            textbox.grid(row=0, column=j, padx=2, pady=2, sticky="nsew")  # Row 0 for header
            self.entry_grid[(-1, j)] = textbox # Store header textboxes with negative row index


        # Add data rows
        for i, record in enumerate(self.table.records):
            for j, col in enumerate(columns):
                textbox = CTkTextbox(self.TableFrame, width=100, height=25, wrap="word")
                textbox.insert("0.0", record.get_field(col))
                textbox.grid(row=i + 1, column=j, padx=2, pady=2, sticky="nsew") # Row i+1 to account for header
                self.entry_grid[(i, j)] = textbox


        # Configure grid weights (include header row)
        for i in range(len(self.table.records) + 1):  # +1 for header
            self.TableFrame.columnconfigure(i, weight=1)
        for j in range(len(columns)):
            self.TableFrame.rowconfigure(j, weight=1)

    def save_changes(self):
        # Save column names (header row)
        updated_columns = []
        for j, col in enumerate(self.table.columns + ["id"]):  # Include "id"
            new_col_name = self.entry_grid[(-1, j)].get("1.0", "end-1c") #get column name
            updated_columns.append(new_col_name)

        #Check for duplicate and empty column names after edit
        seen = set()
        for name in updated_columns:
            if name == "" or name in seen:
                messagebox.showwarning("Error", "Column names cannot be empty or duplicated.")
                return # Stop saving if there are issues
            seen.add(name)
        # Proceed with saving column names and data if there are no errors
        self.table.columns = updated_columns[:-1] # Update column list (exclude "id")

        for i, record in enumerate(self.table.records):
            updates = {}
            for j, col in enumerate(self.table.columns):
                 value = self.entry_grid.get((i,j)).get("1.0", "end-1c")
                 updates[col] = value

            try:
                self.db.update(self.table_name, int(record.get_field('id')), updates)
            except (ValueError, RuntimeError) as e:
                messagebox.showerror("Error saving changes:", str(e))
                return

        self.db.tables[self.table_name] = self.table  # Very important: update table in DB
        self.db.save_to_file(self.db_file)
        messagebox.showinfo("Success", "Changes saved successfully.")

    def add_row(self):
        new_record_data = {col: "" for col in self.table.columns}
        self.db.insert(self.table_name, new_record_data)
        self.populate_table()

    def remove_row(self):
        try:
            selected_row = self.TableFrame.focus_get().grid_info()['row']
            record_id = int(self.entry_grid[(selected_row, len(self.table.columns))].get())
            if self.db.delete_record(self.table_name, record_id):
                self.populate_table()
                messagebox.showinfo("Success", "Record deleted successfully.")
            else:
                messagebox.showerror("Error", "Failed to delete record.")
        except (AttributeError, KeyError, ValueError):
            messagebox.showwarning("No Row Selected", "Please select a row to delete.")


    def create_bottombar(self):  # New method to create the bottombar
        bottombar = CTkFrame(self)
        bottombar.pack(side=BOTTOM, fill=X, padx=5, pady=5)

        self.result_label = CTkLabel(bottombar, text="") # For displaying the result
        self.result_label.pack(side=LEFT, padx=5)

        self.command_entry = CTkEntry(bottombar)
        self.command_entry.pack(side=LEFT, fill=X, expand=True, padx=5)
        self.command_entry.bind("<Return>", self.execute_bottombar_command) # Bind Enter key


    def execute_bottombar_command(self, event=None):
        command = self.command_entry.get()
        try:
            result = execute_command(command, self.table) # Pass the table to the command executor
            self.result_label.configure(text=str(result))
        except (ValueError, TypeError, Exception) as e:  # Catch potential errors during command execution
            self.result_label.configure(text="Error: " + str(e))