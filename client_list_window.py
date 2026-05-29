import tkinter as tk
from tkinter import ttk, messagebox

from controllers.database import Database
from controllers.client_controller import ClientController

class EditClientWindow:
    def __init__(self, master, client_id):
        self.master = master
        self.client_id = client_id

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
            messagebox.showerror("Error", "No se pudo conectar a la base de datos")

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
        else:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos", parent=self.window)

class ClientListWindow:
    def __init__(self, master):
        self.master = master

        self.window = tk.Toplevel(master)
        self.window.title("Lista de Clientes")
        self.window.geometry("600x400")

        # Crear un frame para la lista de clientes
        client_frame = ttk.Frame(self.window)
        client_frame.pack(padx=10, pady=10, expand=True)

        # Crear una entrada de búsqueda
        search_frame = ttk.Frame(client_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        search_button = ttk.Button(search_frame, text="Buscar", command=self.filter_clients, padding=(5,1))
        search_button.pack(side=tk.RIGHT, padx=5)

        # Crear una tabla para mostrar los clientes
        self.client_table = ttk.Treeview(client_frame, columns=("ID", "Nombre", "Apellido", "Email", "Teléfono"), show="headings")
        self.client_table.heading("ID", text="ID")
        self.client_table.heading("Nombre", text="Nombre")
        self.client_table.heading("Apellido", text="Apellido")
        self.client_table.heading("Email", text="Email")
        self.client_table.heading("Teléfono", text="Teléfono")

        # Configurar el ancho de las columnas
        self.client_table.column("ID", width=50)
        self.client_table.column("Nombre", width=100)
        self.client_table.column("Apellido", width=100)
        self.client_table.column("Email", width=150)
        self.client_table.column("Teléfono", width=100)

        # Añadir la tabla al frame
        self.client_table.pack(fill=tk.BOTH, expand=True)

        # Crear un botón para eliminar cliente
        delete_button = ttk.Button(client_frame, text="Eliminar Cliente", command=self.delete_client)
        delete_button.pack(pady=5)

        # Crear un botón para editar cliente
        edit_button = ttk.Button(client_frame, text="Editar Cliente", command=self.edit_client)
        edit_button.pack(pady=5)

        # Cargar los clientes desde la base de datos
        self.load_clients()

    def load_clients(self):
        """Cargar los clientes desde la base de datos y mostrarlos en la tabla"""
        db = Database()
        if db.connect():
            clients = db.get_all_clients()  # Asumimos que este método existe en la clase Database
            for client in clients:
                self.client_table.insert("", "end", values=client)
        else:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos")

    def filter_clients(self):
        """Filtrar los clientes según el texto ingresado en el campo de búsqueda"""
        search_text = self.search_var.get().lower()
        for item in self.client_table.get_children():
            values = self.client_table.item(item, 'values')
            if any(search_text in str(value).lower() for value in values):
                self.client_table.item(item, open=True)
            else:
                self.client_table.delete(item)

    def delete_client(self):
        """Eliminar el cliente seleccionado"""
        selected_item = self.client_table.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un cliente para eliminar.")
            return

        client_id = self.client_table.item(selected_item)['values'][0]
        client_controller = ClientController()
        if client_controller.delete_client(client_id):
            self.client_table.delete(selected_item)
            messagebox.showinfo("Éxito", "Cliente eliminado correctamente")
        else:
            messagebox.showerror("Error", "No se pudo eliminar el cliente")

    def edit_client(self):
        """Editar el cliente seleccionado"""
        selected_item = self.client_table.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un cliente para editar.")
            return

        client_id = self.client_table.item(selected_item)['values'][0]
        edit_window = EditClientWindow(self.master, client_id)

    def show(self):
        """Mostrar la ventana"""
        self.window.mainloop()
