import customtkinter as ctk
from py_ufo_db.pyufodb import Relative_DB
import tkinter as tk
from tkinter import ttk, messagebox  
from customtkinter import CTkInputDialog  
from tkinter import filedialog


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")

app = ctk.CTk()
app.geometry("1000x700")
app.title("UFO DATABASE")

app.iconbitmap("icon.ico")

db = Relative_DB()

table_frame = ctk.CTkFrame(app)
table_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

entry_frame = ctk.CTkFrame(app)
entry_frame.pack(pady=10, padx=10, fill="x")

table_name_entry = ctk.CTkEntry(entry_frame, placeholder_text="Имя таблицы")
table_name_entry.pack(side="left", padx=5)

attributes_entry = ctk.CTkEntry(entry_frame, placeholder_text="Атрибуты (через запятую)")
attributes_entry.pack(side="left", padx=5)

def clear_table_frame():
    for widget in table_frame.winfo_children():
        widget.destroy()


table_name_label = ctk.CTkLabel(app, text="")  
table_name_label.pack(side="bottom", anchor="se", padx=10, pady=10)  

current_table_name = ""

def display_data(table_name):
    global current_table_name
    current_table_name = table_name 
    clear_table_frame()
    try:
        table = db.tables[table_name]
        
        table_name_label.configure(text=f"Текущая таблица: {table_name}")
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background="gray",
                        foreground="white",
                        fieldbackground="black")
        style.configure("Treeview.Heading",
                        background="black",
                        foreground="white")
        style.map('Treeview', foreground=[('selected', 'black')], background=[('selected', '#3b79e0')])

        tree = ttk.Treeview(table_frame, columns=tuple(table.columns), show="headings")
        tree.tag_configure('odd', background='#000000')
        tree.tag_configure('even', background='#202020')
        
        for col in table.columns:
            tree.heading(col, text=col)
            tree.column(col, width=0)

        for i, record in enumerate(table.records):
            row_values = tuple(record.get_field(col) for col in table.columns)
            tag = 'odd' if i % 2 == 0 else 'even'
            tree.insert("", "end", values=row_values, tags=(tag,))

        for col in table.columns:
            tree.column(col, width=tk.font.Font().measure(col) + 50)

        tree.pack(fill=tk.BOTH, expand=True)
        
        app.update_idletasks()
    except KeyError:
        messagebox.showerror("Ошибка", f"Таблица '{table_name}' не найдена.")


def create_table(table_name, attributes):
    if not table_name or not attributes:
        messagebox.showerror("Ошибка", "Пожалуйста, заполните имя таблицы и атрибуты.")
        return
    attributes_list = [attr.strip() for attr in attributes.split(",")]
    if "id" not in attributes_list:  
        attributes_list.insert(0, "id") 
    try:
        db.create_table(table_name, attributes_list)
        messagebox.showinfo("Успех", f"Таблица '{table_name}' создана.")
        table_name_entry.delete(0, ctk.END)
        attributes_entry.delete(0, ctk.END)
        display_data(table_name)
    except RuntimeError as e:
        messagebox.showerror("Ошибка", f"Ошибка при создании таблицы: {e}")

entry_fields = {}

def create_entry_fields(table_name):
    global entry_fields
    entry_fields.clear()
    try:
        columns = db.tables[table_name].columns
        for col in columns:
            if col != "id": 
                label = ctk.CTkLabel(entry_frame, text=col + ":")
                label.pack(side="left", padx=5)
                entry = ctk.CTkEntry(entry_frame)
                entry.pack(side="left", padx=5)
                entry_fields[col] = entry
    except KeyError:
        messagebox.showerror("Ошибка", f"Таблица '{table_name}' не найдена.")

def add_record():
    global current_table_name 
    if not current_table_name:  
        messagebox.showerror("Ошибка", "Укажите имя таблицы.")
        return

    table_name_entry.delete(0, ctk.END)
    table_name_entry.insert(0, current_table_name)

    if not entry_fields:
        create_entry_fields(current_table_name)
        return
    record = {}
    for col, entry in entry_fields.items():
        value = entry.get()
        if not value:
            messagebox.showerror("Ошибка", f"Заполните поле '{col}'.")
            return
        record[col] = value
    try:
        db.insert(current_table_name, record)  
        messagebox.showinfo("Успех", f"Запись добавлена в таблицу '{current_table_name}'.")
        for entry in entry_fields.values():
            entry.delete(0, ctk.END)
        display_data(current_table_name)  
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при добавлении записи: {e}")

add_record_button = ctk.CTkButton(entry_frame, text="Добавить запись", command=add_record)
add_record_button.pack(side="left", padx=5)

sidebar_frame = ctk.CTkFrame(app, width=200, corner_radius=0)
sidebar_frame.pack(side="left", fill="y")

create_table_button = ctk.CTkButton(entry_frame, text="Создать таблицу", fg_color="red", text_color="white", command=lambda: create_table(table_name_entry.get(), attributes_entry.get()))
create_table_button.pack(side="left", padx=5)

def update_record():
    table_name = table_name_entry.get()
    if not table_name:
        messagebox.showerror("Ошибка", "Укажите имя таблицы.")
        return

    try:
        record_id_dialog = CTkInputDialog(title="Обновить запись", text="Введите ID записи для обновления:")
        record_id_str = record_id_dialog.get_input() 
        if record_id_str is None:
            return
        record_id = int(record_id_str)
    except ValueError:
        messagebox.showerror("Ошибка", "Неверный формат ID. Введите число.")
        return

    try:
        table = db.tables[table_name]
        if not any(record.get_field("id") == str(record_id) for record in table.records):
            messagebox.showerror("Ошибка", f"Запись с ID {record_id} не найдена.")
            return

        updates = {}
        for col in table.columns:
            if col != "id":
                value = CTkInputDialog(title="Обновить запись", text=f"Введите новое значение для {col} (или оставьте пустым для пропуска):").get_input()
                if value is not None:
                    updates[col] = value

        if updates:
            db.update(table_name, record_id, updates)
            messagebox.showinfo("Успех", f"Запись с ID {record_id} обновлена.")
            display_data(table_name)
        else:
            messagebox.showinfo("Информация", "Нет изменений для обновления.")

    except KeyError:
        messagebox.showerror("Ошибка", f"Таблица '{table_name}' не найдена.")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при обновлении записи: {e}")

def delete_record():
    table_name = table_name_entry.get()
    if not table_name:
        messagebox.showerror("Ошибка", "Укажите имя таблицы.")
        return

    try:
        record_id_dialog = CTkInputDialog(title="Удалить запись", text="Введите ID записи для удаления:")
        record_id_str = record_id_dialog.get_input()
        if record_id_str is None:
            return
        record_id = int(record_id_str)
    except ValueError:
        messagebox.showerror("Ошибка", "Неверный формат ID. Введите число.")
        return

    try:
        table = db.tables[table_name]  

        if db.delete_record(table_name, record_id):
            messagebox.showinfo("Успех", f"Запись с ID {record_id} удалена.")

            new_id = 1
            for record in table.records:
                record.fields["id"] = str(new_id)  
                new_id += 1
            table.next_id = new_id  

            display_data(table_name)
        else:
            messagebox.showerror("Ошибка", f"Запись с ID {record_id} не найдена.")

    except KeyError:
        messagebox.showerror("Ошибка", f"Таблица '{table_name}' не найдена.")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при удалении записи: {e}")


def save_to_file():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".ufo",
        filetypes=[("UFO Database files", "*.ufo"), ("All files", "*.*")]
    )
    if file_path:  
        try:
            db.save_to_file(file_path)
            messagebox.showinfo("Успех", f"Данные сохранены в файл '{file_path}'.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении файла: {e}")

def load_from_file():
    file_path = filedialog.askopenfilename(
        filetypes=[("UFO Database files", "*.ufo"), ("All files", "*.*")]
    )
    if file_path:  
        try:
            db.load_from_file(file_path)
            messagebox.showinfo("Успех", f"Данные загружены из файла '{file_path}'.")

            if db.tables:
                first_table_name = list(db.tables.keys())[0]
                display_data(first_table_name) 
                table_name_entry.delete(0, ctk.END)
                table_name_entry.insert(0, first_table_name)
            else:
                messagebox.showwarning("Внимание", "Загруженный файл не содержит таблиц.")

        except FileNotFoundError:
            messagebox.showerror("Ошибка", f"Файл '{file_path}' не найден.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке файла: {e}")




ctk.CTkButton(sidebar_frame, text="Обновить запись", command=update_record).pack(pady=10)
ctk.CTkButton(sidebar_frame, text="Удалить запись", command=delete_record).pack(pady=10)
ctk.CTkButton(sidebar_frame, text="Сохранить в файл", command=save_to_file).pack(pady=10)
ctk.CTkButton(sidebar_frame, text="Загрузить из файла", command=load_from_file).pack(pady=10)

app.mainloop()
