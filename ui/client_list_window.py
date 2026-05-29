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
        self.window.title("Perfil de Cliente - Panel de Gestión")
        self.window.geometry("550x550")
        self.window.configure(bg="#f0f2f5")
        self.window.transient(master)

        # --- ESTILOS LOCALES ---
        style = ttk.Style(self.window)
        style.configure("EditHeader.TFrame", background="#2c3e50")
        style.configure("EditContent.TFrame", background="#f0f2f5")
        style.configure("EditSection.TLabelframe", font=("Segoe UI", 10, "bold"), background="white")
        style.configure("EditAction.TButton", font=("Segoe UI", 10, "bold"), padding=12)

        # --- ENCABEZADO ---
        header_frame = tk.Frame(self.window, bg="#2c3e50", height=70)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=f"👤 PERFIL DEL CLIENTE #{client_id}", font=("Segoe UI", 14, "bold"), 
                 bg="#2c3e50", fg="#ecf0f1").pack(side=tk.LEFT, padx=30, pady=18)

        # --- CONTENIDO ---
        main_frame = ttk.Frame(self.window, padding=30, style="EditContent.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Tarjeta de Datos
        sec_form = tk.LabelFrame(main_frame, text=" INFORMACIÓN PERSONAL ", font=("Segoe UI", 9, "bold"), 
                                bg="white", fg="#2c3e50", padx=25, pady=25, relief=tk.FLAT, highlightbackground="#e0e0e0", highlightthickness=1)
        sec_form.pack(fill=tk.X, pady=10)
        sec_form.columnconfigure(1, weight=1)

        # Campos del formulario
        self.fields = {
            "documento": tk.StringVar(),
            "nombre": tk.StringVar(),
            "apellido": tk.StringVar(),
            "email": tk.StringVar(),
            "telefono": tk.StringVar()
        }

        fields_order = [
            ("DOCUMENTO:", "documento"),
            ("NOMBRE:", "nombre"),
            ("APELLIDO:", "apellido"),
            ("CORREO ELECTRÓNICO:", "email"),
            ("TELÉFONO DE CONTACTO:", "telefono")
        ]

        for i, (label_text, field_name) in enumerate(fields_order):
            tk.Label(sec_form, text=label_text, bg="white", font=("Segoe UI", 9, "bold")).grid(row=i, column=0, sticky=tk.W, pady=12, padx=(0, 15))
            ttk.Entry(sec_form, textvariable=self.fields[field_name], font=("Segoe UI", 10)).grid(row=i, column=1, sticky=tk.EW, pady=12)

        # Cargar los datos del cliente
        self.load_client_data()

        # Barra de Botones Inferior
        btn_container = tk.Frame(self.window, bg="#f0f2f5", pady=25, padx=30)
        btn_container.pack(fill=tk.X)
        
        ttk.Button(btn_container, text="CANCELAR", command=self.window.destroy).pack(side=tk.LEFT)
        ttk.Button(btn_container, text="GUARDAR CAMBIOS", style="EditAction.TButton", 
                   command=self.save_changes).pack(side=tk.RIGHT)

    def load_client_data(self):
        """Cargar los datos del cliente desde la base de datos"""
        db = Database()
        if db.connect():
            query = "SELECT nombre, apellido, email, telefono, documento FROM clientes WHERE id_clientes = %s"
            cursor = db.connection.cursor()
            cursor.execute(query, (self.client_id,))
            result = cursor.fetchone()
            if result:
                self.fields["nombre"].set(result[0])
                self.fields["apellido"].set(result[1])
                self.fields["email"].set(result[2])
                self.fields["telefono"].set(result[3])
                self.fields["documento"].set(result[4] if result[4] else "")
        else:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos", parent=self.window)

    def save_changes(self):
        """Guardar los cambios en la base de datos"""
        if not self.fields["nombre"].get() or not self.fields["apellido"].get() or not self.fields["email"].get() or not self.fields["telefono"].get() or not self.fields["documento"].get():
            messagebox.showerror("Error", "Todos los campos son obligatorios", parent=self.window)
            return

        client_data = (
            self.fields["nombre"].get(),
            self.fields["apellido"].get(),
            self.fields["email"].get(),
            self.fields["telefono"].get(),
            self.fields["documento"].get()
        )

        db = Database()
        if db.connect():
            query = "UPDATE clientes SET nombre=%s, apellido=%s, email=%s, telefono=%s, documento=%s WHERE id_clientes=%s"
            cursor = db.connection.cursor()
            cursor.execute(query, client_data + (self.client_id,))
            db.connection.commit()
            messagebox.showinfo("Éxito", "Cliente actualizado exitosamente", parent=self.window)
            self.window.destroy()
            self.client_list_window.refresh_clients()
        else:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos", parent=self.window)

class ClientListWindow:
    def __init__(self, master, select_callback=None):
        self.master = master
        self.select_callback = select_callback
        self.cards = []
        self.selected_id = None
        self.client_data_map = {}

        self.window = tk.Toplevel(master)
        self.window.title("Directorio de Clientes - Gestión Hotelera")
        self.window.geometry("1000x800")
        self.window.configure(bg="#f0f2f5")

        # --- ESTILOS LOCALES ---
        style = ttk.Style(self.window)
        style.configure("ClDashboard.TFrame", background="#f0f2f5")
        style.configure("ClAction.TButton", font=("Segoe UI", 10, "bold"), padding=12)

        # --- ENCABEZADO DASHBOARD ---
        header_frame = tk.Frame(self.window, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="👥 DIRECTORIO DE CLIENTES", font=("Segoe UI", 16, "bold"), 
                 bg="#2c3e50", fg="#ecf0f1").pack(side=tk.LEFT, padx=30, pady=20)
        
        self.lbl_total_clients = tk.Label(header_frame, text="Cargando...", font=("Segoe UI", 10), 
                                         bg="#2c3e50", fg="#95a5a6")
        self.lbl_total_clients.pack(side=tk.RIGHT, padx=30)

        main_container = ttk.Frame(self.window, padding=30, style="ClDashboard.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True)

        # --- ÁREA DE BÚSQUEDA (CARD) ---
        search_card = tk.Frame(main_container, bg="white", highlightbackground="#e0e0e0", highlightthickness=1, padx=20, pady=20)
        search_card.pack(fill=tk.X, pady=(0, 25))
        
        tk.Label(search_card, text="🔎 FILTRAR DIRECTORIO:", font=("Segoe UI", 9, "bold"), bg="white", fg="#2c3e50").pack(side=tk.LEFT, padx=(0, 15))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_card, textvariable=self.search_var, font=("Segoe UI", 11))
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_entry.bind("<KeyRelease>", lambda e: self.filter_cards())

        ttk.Button(search_card, text="RECARGAR LISTA", command=self.refresh_clients).pack(side=tk.RIGHT, padx=(15, 0))

        # --- LISTADO (SCROLL) ---
        canvas_frame = ttk.Frame(main_container, style="ClDashboard.TFrame")
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="#f0f2f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable = tk.Frame(self.canvas, bg="#f0f2f5")

        self.scrollable.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable, anchor="nw", width=920)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- BARRA DE ACCIONES INFERIOR ---
        actions_frame = ttk.Frame(main_container, style="ClDashboard.TFrame")
        actions_frame.pack(fill=tk.X, pady=(25, 0))

        if self.select_callback:
            ttk.Button(actions_frame, text="✅ SELECCIONAR CLIENTE PARA RESERVA", 
                       style="ClAction.TButton", command=self.select_client_and_close).pack(side=tk.RIGHT)
            ttk.Button(actions_frame, text="🔄 ACTUALIZAR DATOS", command=self.edit_client).pack(side=tk.RIGHT, padx=10)
        else:
            ttk.Button(actions_frame, text="🗑️ ELIMINAR SELECCIONADO", command=self.delete_client).pack(side=tk.LEFT)
            ttk.Button(actions_frame, text="👤 GESTIONAR PERFIL", style="ClAction.TButton", command=self.edit_client).pack(side=tk.RIGHT)

        # Cargar los clientes
        self.load_clients()

    def bind_select(self, widget, client_id):
        widget.bind("<Button-1>", lambda e, i=client_id: self.select_card(i))
        if self.select_callback:
             widget.bind("<Double-Button-1>", lambda e: self.select_client_and_close())
        for child in widget.winfo_children():
            self.bind_select(child, client_id)

    def create_card(self, c):
        # c = (id, documento, nombre, apellido, email, telefono)
        client_id = c[0]
        full_name = f"{c[2]} {c[3]}".upper()
        doc = c[1]
        email = c[4]
        phone = c[5]

        card = tk.Frame(self.scrollable, bg="white", bd=0, highlightbackground="#d1d8e0", highlightthickness=1)
        card.pack(fill=tk.X, padx=5, pady=8)
        self.bind_select(card, client_id)

        inner = tk.Frame(card, bg="white", padx=15, pady=15)
        inner.pack(fill=tk.X)
        self.bind_select(inner, client_id)

        # Izquierda: Avatar e Info Principal
        info_f = tk.Frame(inner, bg="white")
        info_f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.bind_select(info_f, client_id)

        avatar_f = tk.Frame(info_f, bg="#f4f6f7", width=40, height=40)
        avatar_f.pack_propagate(False)
        avatar_f.pack(side=tk.LEFT, padx=(0, 15))
        tk.Label(avatar_f, text="👤", font=("Segoe UI", 16), bg="#f4f6f7").pack(expand=True)
        self.bind_select(avatar_f, client_id)

        text_f = tk.Frame(info_f, bg="white")
        text_f.pack(side=tk.LEFT, fill=tk.BOTH)
        self.bind_select(text_f, client_id)

        tk.Label(text_f, text=full_name, font=("Segoe UI", 12, "bold"), bg="white", fg="#2c3e50").pack(anchor="w")
        tk.Label(text_f, text=f"Documento: {doc}", font=("Segoe UI", 9, "bold"), bg="white", fg="#7f8c8d").pack(anchor="w")

        # Derecha: Contacto
        contact_f = tk.Frame(inner, bg="white")
        contact_f.pack(side=tk.RIGHT, fill=tk.Y)
        self.bind_select(contact_f, client_id)

        tk.Label(contact_f, text=f"✉️ {email}", font=("Segoe UI", 10), bg="white", fg="#34495e").pack(anchor="e")
        tk.Label(contact_f, text=f"📞 {phone}", font=("Segoe UI", 10, "bold"), bg="white", fg="#2980b9").pack(anchor="e")
        tk.Label(contact_f, text=f"ID #{client_id}", font=("Segoe UI", 8), bg="white", fg="#bdc3c7").pack(anchor="e", pady=(5,0))

        card.client_id = client_id
        card.search_data = f"{full_name} {doc} {email} {phone} {client_id}".lower()
        self.cards.append(card)
        self.client_data_map[client_id] = c

    def select_card(self, client_id):
        self.selected_id = client_id
        for c in self.cards:
            is_sel = c.client_id == client_id
            c.configure(highlightbackground="#3498db" if is_sel else "#d1d8e0", highlightthickness=2 if is_sel else 1)
            bg_color = "#f1f9ff" if is_sel else "white"
            self._update_bg_recursive(c, bg_color)

    def _update_bg_recursive(self, widget, color):
        try:
            current_bg = str(widget.cget("background"))
            if current_bg != "#f4f6f7":
                widget.configure(bg=color)
        except: pass
        for child in widget.winfo_children():
            self._update_bg_recursive(child, color)

    def select_client_and_close(self):
        """Selecciona el cliente y llama al callback"""
        if not self.selected_id:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un cliente.", parent=self.window)
            return
        
        client_data = self.client_data_map[self.selected_id]
        self.select_callback(client_data) 
        self.window.destroy()

    def load_clients(self):
        """Cargar los clientes desde la base de datos y mostrarlos en tarjetas"""
        for w in self.scrollable.winfo_children(): w.destroy()
        self.cards = []
        self.client_data_map = {}
        self.selected_id = None
        self.search_var.set("")

        db = Database()
        if db.connect():
            clients = db.get_all_clients()
            self.lbl_total_clients.config(text=f"TOTAL: {len(clients)} CLIENTES")
            for client in clients:
                self.create_card(client)
            self.filter_cards()
        else:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos", parent=self.window)

    def filter_cards(self):
        """Filtrar las tarjetas de clientes en tiempo real"""
        query = self.search_var.get().lower()
        visible_count = 0
        for card in self.cards:
            if query in card.search_data:
                card.pack(fill=tk.X, padx=5, pady=8)
                visible_count += 1
            else:
                card.pack_forget()
        self.lbl_total_clients.config(text=f"MOSTRANDO: {visible_count} / TOTAL: {len(self.cards)} CLIENTES")

    def delete_client(self):
        """Eliminar el cliente seleccionado"""
        if not self.selected_id:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un cliente para eliminar.", parent=self.window)
            return

        client_name = self.client_data_map[self.selected_id][2] + " " + self.client_data_map[self.selected_id][3]

        if messagebox.askyesno("Confirmación", f"¿Está seguro de eliminar a {client_name}?", parent=self.window):
            client_controller = ClientController()
            success = client_controller.delete_client(self.selected_id)
            
            if success:
                messagebox.showinfo("Éxito", "Cliente eliminado correctamente", parent=self.window)
                self.refresh_clients()
            else:
                # Si falló, probablemente sea por integridad referencial (reservas activas)
                self._handle_deletion_error(client_name)

    def _handle_deletion_error(self, client_name):
        """Maneja el error de eliminación ofreciendo fusionar con otro cliente."""
        msg = f"No se puede eliminar a '{client_name}' porque tiene reservas o cotizaciones asociadas.\n\n"
        msg += "¿Desea transferir sus datos a otro cliente (Fusionar) antes de borrarlo?"
        
        if messagebox.askyesno("Conflicto de Datos", msg, parent=self.window):
            # Pedir ID del cliente destino
            from tkinter import simpledialog
            target_id = simpledialog.askstring("Fusionar Clientes", 
                                             f"Ingrese el ID del cliente que desea CONSERVAR\n(Donde se enviarán las reservas de {client_name}):",
                                             parent=self.window)
            
            if target_id and target_id.isdigit():
                target_id = int(target_id)
                if target_id == self.selected_id:
                    messagebox.showerror("Error", "El ID de destino no puede ser el mismo que el de origen.")
                    return
                
                db = Database()
                if db.connect():
                    # Verificar que el destino existe
                    dest_client = db.get_client_by_id(target_id)
                    if not dest_client:
                        messagebox.showerror("Error", f"No se encontró el cliente con ID #{target_id}")
                        return
                    
                    # Confirmar fusión
                    dest_name = f"{dest_client[1]} {dest_client[2]}"
                    confirm_msg = f"¿Confirmar transferencia de todas las reservas de {client_name} hacia {dest_name}?\n\nAl terminar, {client_name} será ELIMINADO."
                    
                    if messagebox.askyesno("Confirmar Fusión", confirm_msg, parent=self.window):
                        if db.reassign_client_data(self.selected_id, target_id):
                            # Ahora intentar borrar de nuevo
                            if db.delete_client(self.selected_id):
                                messagebox.showinfo("Éxito", "Fusión completada. El cliente duplicado ha sido eliminado.")
                                self.refresh_clients()
                            else:
                                messagebox.showerror("Error", "Los datos fueron transferidos pero no se pudo eliminar el perfil original.")
                        else:
                            messagebox.showerror("Error", "Fallo al transferir los datos entre clientes.")
            elif target_id:
                messagebox.showerror("Error", "ID inválido.")

    def edit_client(self):
        """Editar el cliente seleccionado"""
        if not self.selected_id:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un cliente para editar.", parent=self.window)
            return

        EditClientWindow(self.window, self.selected_id, self)

    def refresh_clients(self):
        """Refrescar la lista de clientes"""
        self.load_clients()

    def show(self):
        pass
