import tkinter as tk
from tkinter import ttk, messagebox

from controllers.database import Database
from controllers.client_controller import ClientController

class EditClientWindow:
    def __init__(self, master, client_id, client_list_window):
        self.master = master
        self.client_id = client_id
        self.client_list_window = client_list_window

        self.window = tk.Toplevel(master)
        self.window.title("Editar Cliente")
        self.window.geometry("450x300")

        # Frame principal del formulario
        form_frame = ttk.Frame(self.window)
        form_frame.pack(padx=10, pady=10, expand=True)

        # Mensaje para notificaciones
        message_label = ttk.Label(form_frame, text="Ingrese los datos del cliente", font=('Arial', 14))
        message_label.pack(side=tk.TOP, padx=5, pady=5)

        # Campos del formulario
        self.fields = {
            "nombre": tk.StringVar(),
            "apellido": tk.StringVar(),
            "email": tk.StringVar(),
            "telefono": tk.StringVar()
        }

        fields_order = [
            ("Nombre:", "nombre"),
            ("Apellido:", "apellido"),
            ("Correo electrónico:", "email"),
            ("Teléfono:", "telefono")
        ]

        for label_text, field_name in fields_order:
            row = ttk.Frame(form_frame)
            row.pack(fill=tk.X, padx=5, pady=2)

            label = ttk.Label(row, text=label_text, width=15)
            label.pack(side=tk.LEFT)

            entry = ttk.Entry(row, textvariable=self.fields[field_name])
            entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

        # Cargar los datos del cliente
        self.load_client_data()

        # Botón para guardar cambios
        save_button = ttk.Button(
            form_frame,
            text="Guardar Cambios",
            command=self.save_changes,
            style="TButton"
        )
        save_button.pack(pady=10, side=tk.BOTTOM)

    def load_client_data(self):
        """Cargar los datos del cliente desde la base de datos"""
        db = Database()
        if db.connect():
            query = "SELECT nombre, apellido, email, telefono FROM clientes WHERE id_clientes = %s"
            cursor = db.connection.cursor()
            cursor.execute(query, (self.client_id,))
            result = cursor.fetchone()
            if result:
                self.fields["nombre"].set(result[0])
                self.fields["apellido"].set(result[1])
                self.fields["email"].set(result[2])
                self.fields["telefono"].set(result[3])
        else:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos", parent=self.window)

    def save_changes(self):
        """Guardar los cambios en la base de datos"""
        # Validación de entradas
        if not self.fields["nombre"].get() or not self.fields["apellido"].get() or not self.fields["email"].get() or not self.fields["telefono"].get():
            messagebox.showerror("Error", "Todos los campos son obligatorios", parent=self.window)
            return

        client_data = (
            self.fields["nombre"].get(),
            self.fields["apellido"].get(),
            self.fields["email"].get(),
            self.fields["telefono"].get()
        )

        db = Database()
        if db.connect():
            query = "UPDATE clientes SET nombre=%s, apellido=%s, email=%s, telefono=%s WHERE id_clientes=%s"
            cursor = db.connection.cursor()
            cursor.execute(query, client_data + (self.client_id,))
            db.connection.commit()
            messagebox.showinfo("Éxito", "Cliente actualizado exitosamente", parent=self.window)
            self.window.destroy()
            self.client_list_window.refresh_clients()  # Refrescar la lista de clientes
        else:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos", parent=self.window)
