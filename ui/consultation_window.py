import tkinter as tk
from tkinter import ttk, messagebox
import calendar
import os
from datetime import date, datetime, timedelta
from controllers.database import Database
from PIL import Image, ImageTk
from utils.email_sender import send_quotation_email
from utils.whatsapp_sender import send_whatsapp_quotation
from ui.advanced_search_window import AdvancedSearchWindow
from ui.gallery_window import GalleryWindow

class ConsultationWindow:
    def __init__(self, master, reservation_controller):
        self.master = master
        self.controller = reservation_controller
        self.db = Database()
        self.db.connect()
        
        self.window = tk.Toplevel(master)
        self.window.title("Consulta de Disponibilidad Interactiva")
        self.window.geometry("1200x900")
        self.window.configure(bg="#f0f2f5")
        self.window.transient(master)
        
        # Esperar visibilidad para evitar TclError en grab_set
        self.window.wait_visibility()
        self.window.grab_set()

        self.selected_property = None
        self.reserved_ranges = []
        self.start_date = None
        self.end_date = None
        
        self.now = date.today()
        self.year = self.now.year
        self.month = self.now.month
        
        # Estados de visibilidad
        self.discount_visible = True
        self.lead_visible = False

        # Campos para captación de leads
        self.lead_fields = {
            "nombre": tk.StringVar(),
            "telefono": tk.StringVar(),
            "email": tk.StringVar(),
            "include_photos": tk.BooleanVar(value=False)
        }
        
        self.setup_ui()
        self.load_properties()

    def toggle_discount_section(self):
        """Muestra u oculta la sección de negociación."""
        if self.discount_visible:
            self.discount_card.pack_forget()
            self.btn_toggle_discount.config(text="💰 NEGOCIACIÓN ▼")
            self.discount_visible = False
        else:
            # Reinsertar después de su cabecera y antes de la cabecera de captación
            self.discount_card.pack(fill=tk.X, pady=(0, 20), after=self.discount_header)
            self.btn_toggle_discount.config(text="💰 NEGOCIACIÓN ▲")
            self.discount_visible = True

    def toggle_lead_section(self):
        """Muestra u oculta la sección de captación/cotización."""
        if self.lead_visible:
            self.lead_card.pack_forget()
            self.btn_toggle_lead.config(text="📋 COTIZACIÓN ▼")
            self.lead_visible = False
        else:
            # Reinsertar después de su cabecera y antes del botón reservar
            self.lead_card.pack(fill=tk.X, pady=(0, 20), after=self.lead_header)
            self.btn_toggle_lead.config(text="📋 COTIZACIÓN ▲")
            self.lead_visible = True

    def send_quotation(self):
        """Prepara el envío de cotización por EMAIL."""
        self._prepare_quotation(mode="email")

    def send_quotation_whatsapp(self):
        """Prepara el envío de cotización por WHATSAPP."""
        self._prepare_quotation(mode="whatsapp")

    def _prepare_quotation(self, mode="email"):
        """Lógica común de validación y preparación antes de enviar."""
        nombre = self.lead_fields["nombre"].get().strip()
        email = self.lead_fields["email"].get().strip().lower()
        tel = self.lead_fields["telefono"].get().strip()
        
        if not (nombre and tel):
            messagebox.showerror("Error", "Por favor completa Nombre y Teléfono para enviar la cotización.", parent=self.window)
            return
            
        if mode == "email" and not email:
            messagebox.showerror("Error", "Por favor completa el Email para enviar la cotización por correo.", parent=self.window)
            return

        if not self.start_date or not self.end_date or not self.selected_property:
            messagebox.showwarning("Atención", "Selecciona fechas e inmueble antes de enviar una cotización.", parent=self.window)
            return

        # Si quiere incluir fotos (solo aplica a email por ahora), abrir selector
        if self.lead_fields["include_photos"].get() and mode == "email":
            # Obtener imagen principal
            main_img = self.selected_property[8] if len(self.selected_property) > 8 else ""
            # Obtener galería
            images = self.db.get_gallery_images(self.selected_property[0])
            
            all_paths = []
            if main_img and os.path.exists(main_img):
                all_paths.append(main_img)
            
            for img in images:
                path = img[1]
                if path and os.path.exists(path) and path not in all_paths:
                    all_paths.append(path)

            if not all_paths:
                if not messagebox.askyesno("Sin fotos", "Este inmueble no tiene fotos disponibles. ¿Enviar cotización sin fotos?", parent=self.window):
                    return
                self._proceed_send_quotation(nombre, email, tel, [], mode=mode)
            else:
                self._open_quote_image_selector(nombre, email, tel, all_paths, mode=mode)
        else:
            self._proceed_send_quotation(nombre, email, tel, [], mode=mode)

    def _open_quote_image_selector(self, nombre, email, tel, image_paths, mode="email"):
        """Abre un selector de imágenes robusto para la cotización."""
        selection_win = tk.Toplevel(self.window)
        selection_win.title("Seleccionar Fotos para Cotización")
        selection_win.geometry("650x750") 
        selection_win.configure(bg="#f8f9fa")
        selection_win.transient(self.window)
        selection_win.grab_set()

        # 1. Header
        header = tk.Frame(selection_win, bg="#2c3e50", pady=15)
        header.pack(side=tk.TOP, fill=tk.X)
        tk.Label(header, text="📸 SELECCIONAR FOTOS (MÁX. 10)", font=("Segoe UI", 12, "bold"), 
                 bg="#2c3e50", fg="white").pack()

        # 2. Footer (Botón de acción - Pack BOTTOM para asegurar visibilidad)
        footer = tk.Frame(selection_win, bg="#f8f9fa", pady=20, border=1, relief=tk.SUNKEN)
        footer.pack(side=tk.BOTTOM, fill=tk.X)

        def confirm():
            selected = [p for p, v in vars_map if v.get()]
            if not selected:
                messagebox.showwarning("Atención", "Debe seleccionar al menos una foto para enviar.")
                return
            if len(selected) > 10:
                messagebox.showwarning("Atención", f"Ha seleccionado {len(selected)} fotos. El límite es 10.")
                return
            
            selection_win.destroy()
            self._proceed_send_quotation(nombre, email, tel, selected, mode=mode)

        btn_confirm = tk.Button(footer, text="📧 CONFIRMAR Y ENVIAR COTIZACIÓN", command=confirm,
                               font=("Segoe UI", 11, "bold"), bg="#27ae60", fg="white", 
                               relief=tk.FLAT, pady=12, padx=40, cursor="hand2")
        btn_confirm.pack(pady=5)

        # 3. Contenedor Central con Scroll (Toma el resto del espacio)
        container = tk.Frame(selection_win, bg="#f8f9fa")
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(container, bg="#f8f9fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#f8f9fa")

        # Configurar el canvas para el scroll
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scroll_frame.bind("<Configure>", on_frame_configure)
        
        # Ajustar ancho del frame interno al canvas
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        vars_map = []
        self.quote_thumbnails = [] # Mantener referencias

        # Generar las filas de imágenes
        for i, path in enumerate(image_paths):
            item_f = tk.Frame(scroll_frame, bg="white", pady=8, padx=15, relief=tk.RIDGE, bd=1)
            item_f.pack(fill=tk.X, pady=4, padx=5)

            # Seleccionar por defecto solo las primeras 10
            is_selected = (i < 10)
            var = tk.BooleanVar(value=is_selected)
            chk = tk.Checkbutton(item_f, variable=var, bg="white", activebackground="white")
            chk.pack(side=tk.LEFT)

            try:
                img = Image.open(path)
                img.thumbnail((100, 75))
                tk_img = ImageTk.PhotoImage(img)
                self.quote_thumbnails.append(tk_img)
                tk.Label(item_f, image=tk_img, bg="white").pack(side=tk.LEFT, padx=15)
            except Exception as e:
                print(f"Error cargando miniatura: {e}")
                tk.Label(item_f, text="🖼️ (Error)", bg="white").pack(side=tk.LEFT, padx=15)

            name_label = tk.Label(item_f, text=os.path.basename(path), bg="white", font=("Segoe UI", 10))
            name_label.pack(side=tk.LEFT, fill=tk.X, expand=True, anchor="w")
            
            vars_map.append((path, var))

    def _proceed_send_quotation(self, nombre, email, tel, selected_images, mode="email"):
        """Proceso final de guardado y envío de cotización."""
        # Asegurar conexión
        if not self.db.connection or not self.db.connection.is_connected():
            self.db.connect()

        # 1. Verificar si el contacto ya existe (en clientes o prospectos) de forma robusta
        # Buscamos por Email O Teléfono
        existing, tipo = self.db.get_contact_by_any(email=email, phone=tel)

        client_id = None
        prospect_id = None

        if existing:
            if tipo == 'cliente':
                client_id = existing[0]
                print(f"Vinculando a cliente existente: {client_id}")
            else:
                prospect_id = existing[0]
                print(f"Vinculando a prospecto existente: {prospect_id}")
        else:
            # Es un nuevo contacto -> Guardar como prospecto
            parts = nombre.split(" ", 1)
            nom = parts[0]
            ape = parts[1] if len(parts) > 1 else "—"
            prospect_id = self.db.insert_prospect(("S/D", nom, ape, email if email else "no-email@wa.com", tel))
            if prospect_id:
                print(f"Nuevo prospecto creado: {prospect_id}")
                messagebox.showinfo("Éxito", f"Se ha registrado a '{nombre}' como un nuevo prospecto.", parent=self.window)
            else:
                messagebox.showerror("Error", "No se pudo registrar el nuevo prospecto.", parent=self.window)
                return

        if not client_id and not prospect_id:
            messagebox.showerror("Error", "No se pudo registrar ni encontrar el contacto.", parent=self.window)
            return
        # 1.5 Datos de cotización
        noches = (self.end_date - self.start_date).days
        valor_dia = float(self.selected_property[7])
        costo_total = noches * valor_dia

        discount_val_str = self.discount_var.get()
        descuento_monto = 0
        try:
            if self.discount_is_percentage.get():
                perc = float(discount_val_str) if discount_val_str else 0.0
                descuento_monto = costo_total * (perc / 100)
            else:
                descuento_monto = float(discount_val_str.replace("$", "").replace(".", "")) if discount_val_str else 0.0
        except: pass

        costo_con_desc = costo_total - descuento_monto

        quotation_data = {
            "id_cliente": client_id, 
            "id_prospecto": prospect_id,
            "id_inmueble": self.selected_property[0],
            "fecha_ingreso": self.start_date, "fecha_egreso": self.end_date,
            "noches": noches, "valor_dia": valor_dia, "costo_total": costo_total,
            "descuento": descuento_monto, "costo_con_descuento": costo_con_desc
        }

        quot_id = self.db.insert_quotation(quotation_data)
        if not quot_id:
            messagebox.showerror("Error", "No se pudo guardar la cotización en la base de datos.", parent=self.window)
            return
        # Obtener servicios y detalles para el envío
        servicios_raw = self.db.get_property_services(self.selected_property[0])
        servicios_str = ", ".join([f"{s[0]} {s[1]}" for s in servicios_raw]) if servicios_raw else "No especificados"
        
        p = self.selected_property
        dorms = p[9] if len(p) > 9 and p[9] is not None else 0
        camas = p[10] if len(p) > 10 and p[10] is not None else 0
        banos = p[11] if len(p) > 11 and p[11] is not None else 0

        data = {
            "id": quot_id, "inmueble": self.selected_property[1], "servicios": servicios_str,
            "fecha_ingreso": self.start_date.strftime("%d/%m/%Y"),
            "fecha_egreso": self.end_date.strftime("%d/%m/%Y"),
            "noches": noches, "ubicacion": f"{self.selected_property[4]}, {self.selected_property[5]}",
            "costo_total": self.lbl_costo_total.cget("text").replace("Costo Total: ", ""),
            "final_price": self.lbl_final_price.cget("text").replace("Precio Final: ", ""),
            "final_per_night": self.lbl_final_per_night.cget("text").replace("P/Noche Final: ", ""),
            "dormitorios": dorms, "camas": camas, "baños": banos
        }
        
        if mode == "email":
            self.window.config(cursor="watch")
            self.window.update()
            
            if send_quotation_email(email, nombre, data, image_paths=selected_images):
                messagebox.showinfo("Éxito", f"Cotización enviada correctamente a {email}.", parent=self.window)
                self._clear_lead_fields()
            else:
                messagebox.showerror("Error", "Fallo al enviar correo.", parent=self.window)
            self.window.config(cursor="")
        
        elif mode == "whatsapp":
            if send_whatsapp_quotation(tel, nombre, data):
                messagebox.showinfo("Éxito", "WhatsApp abierto con la cotización.", parent=self.window)
                self._clear_lead_fields()

    def _clear_lead_fields(self):
        """Limpia los campos del formulario de captación."""
        for var in self.lead_fields.values():
            if isinstance(var, tk.StringVar): var.set("")
            elif isinstance(var, tk.BooleanVar): var.set(False)

    def _on_name_key_release(self, event):
        """Busca contactos mientras se escribe el nombre."""
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return

        query = self.lead_fields["nombre"].get().strip()
        if len(query) < 3:
            self._hide_suggestions()
            return

        # Buscar en la base de datos (clientes y prospectos)
        results = self.db.search_contacts(query)
        
        if not results:
            self._hide_suggestions()
            return

        # Mostrar sugerencias
        self.suggestion_list.delete(0, tk.END)
        self.client_suggestions = results # Guardar referencia
        
        for res in results:
            # id, doc, nombre, apellido, email, tel, tipo
            display = f"{res[2]} {res[3]} ({res[4]}) - {'VIP' if res[6] == 'cliente' else 'PROSPECTO'}"
            self.suggestion_list.insert(tk.END, display)

        # Posicionar el listbox debajo del entry
        self.suggestion_list.pack(fill=tk.X, after=self.ent_nombre)
        self.suggestion_list.lift()

    def _select_client_suggestion(self, event):
        """Llena los campos con el cliente seleccionado de la lista."""
        selection = self.suggestion_list.curselection()
        if not selection:
            return

        idx = selection[0]
        client = self.client_suggestions[idx]
        
        # Llenar campos: id, doc, nombre, apellido, email, tel
        self.lead_fields["nombre"].set(f"{client[2]} {client[3]}")
        self.lead_fields["email"].set(client[4])
        self.lead_fields["telefono"].set(client[5])
        
        self._hide_suggestions()

    def _hide_suggestions(self):
        """Oculta la lista de sugerencias."""
        self.suggestion_list.pack_forget()

    def setup_ui(self):
        # --- ESTILOS ---
        style = ttk.Style(self.window)
        style.configure("Cons.TFrame", background="#f0f2f5")
        style.configure("ConsCard.TFrame", background="white", relief="flat")
        style.configure("ConsHeader.TLabel", font=("Segoe UI", 18, "bold"), foreground="white", background="#2c3e50")
        style.configure("Day.TButton", font=("Segoe UI", 10), width=4)
        style.configure("Selected.TButton", background="#3498db", foreground="white")
        style.configure("Reserved.TButton", background="#e74c3c", foreground="white")

        # --- ENCABEZADO ---
        header_frame = tk.Frame(self.window, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🔍 CONSULTA DE DISPONIBILIDAD", font=("Segoe UI", 16, "bold"), 
                 bg="#2c3e50", fg="#ecf0f1").pack(side=tk.LEFT, padx=30, pady=20)

        # --- CONTENIDO PRINCIPAL CON SCROLL ---
        outer_container = tk.Frame(self.window, bg="#f0f2f5")
        outer_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(outer_container, bg="#f0f2f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer_container, orient="vertical", command=canvas.yview)
        
        # main_frame ahora estará dentro del canvas - Usamos tk.Frame para mejor compatibilidad con canvas
        main_frame = tk.Frame(canvas, bg="#f0f2f5")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        canvas_window = canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        main_frame.bind("<Configure>", on_frame_configure)
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", on_canvas_configure)

        # Vincular la rueda del ratón al scroll
        def _on_mousewheel(event):
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Panel Izquierdo: Selección y Resumen
        left_panel = tk.Frame(main_frame, bg="#f0f2f5")
        left_panel.grid(row=0, column=0, sticky="nw", padx=(20, 10), pady=20)
        
        # Selección de Rango
        self.range_card = tk.LabelFrame(left_panel, text=" 📅 ESTADÍA SELECCIONADA ", font=("Segoe UI", 9, "bold"), 
                                      bg="white", padx=15, pady=15, relief=tk.FLAT, highlightbackground="#e0e0e0", highlightthickness=1,
                                      width=350) 
        self.range_card.pack(fill=tk.X, pady=(0, 20))
        self.range_card.pack_propagate(False) # Mantener el ancho del card
        
        self.lbl_desde = tk.Label(self.range_card, text="Desde: No seleccionada", bg="white", font=("Segoe UI", 9), anchor="w")
        self.lbl_desde.pack(fill=tk.X, pady=2)
        self.lbl_hasta = tk.Label(self.range_card, text="Hasta: No seleccionada", bg="white", font=("Segoe UI", 9), anchor="w")
        self.lbl_hasta.pack(fill=tk.X, pady=2)
        self.lbl_noches = tk.Label(self.range_card, text="Noches: 0", bg="white", font=("Segoe UI", 10, "bold"), fg="#2980b9", anchor="w")
        self.lbl_noches.pack(fill=tk.X, pady=2)
        
        self.lbl_costo_total = tk.Label(self.range_card, text="Costo Total: $0,00", bg="white", font=("Segoe UI", 12, "bold"), fg="#27ae60", anchor="w")
        self.lbl_costo_total.pack(fill=tk.X, pady=(5, 10))

        # ... (el resto de los widgets de left_panel se mantienen igual con .pack() dentro de left_panel) ...
        # --- SECCIÓN DE NEGOCIACIÓN PLEGABLE ---
        self.discount_header = tk.Frame(left_panel, bg="#2c3e50")
        self.discount_header.pack(fill=tk.X, pady=(0, 0))
        
        self.btn_toggle_discount = tk.Button(self.discount_header, text="💰 NEGOCIACIÓN ▲", font=("Segoe UI", 8, "bold"), 
                                           bg="#2c3e50", fg="white", bd=0, activebackground="#34495e", 
                                           activeforeground="white", anchor="w", padx=10, pady=5,
                                           command=self.toggle_discount_section)
        self.btn_toggle_discount.pack(fill=tk.X)

        self.discount_card = tk.Frame(left_panel, bg="white", padx=15, pady=15, highlightbackground="#e0e0e0", highlightthickness=1)
        self.discount_card.pack(fill=tk.X, pady=(0, 20))

        self.discount_is_percentage = tk.BooleanVar(value=True)
        disc_type_frame = tk.Frame(self.discount_card, bg="white")
        disc_type_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(disc_type_frame, text="Descuento:", font=("Segoe UI", 9, "bold"), bg="white", fg="#7f8c8d").pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(disc_type_frame, text="%", variable=self.discount_is_percentage, value=True, 
                       bg="white", command=self.update_selection_display).pack(side=tk.LEFT)
        tk.Radiobutton(disc_type_frame, text="$", variable=self.discount_is_percentage, value=False, 
                       bg="white", command=self.update_selection_display).pack(side=tk.LEFT, padx=10)

        self.discount_var = tk.StringVar(value="0")
        self.ent_discount = ttk.Entry(self.discount_card, textvariable=self.discount_var, font=("Segoe UI", 10))
        self.ent_discount.pack(fill=tk.X, pady=5)
        self.ent_discount.bind("<KeyRelease>", self.on_discount_change)

        # Resumen de estadía dentro de negociación para contexto
        self.lbl_disc_rango = tk.Label(self.discount_card, text="Estadía: -", bg="white", 
                                      font=("Segoe UI", 9, "bold"), fg="#34495e", anchor="w")
        self.lbl_disc_rango.pack(fill=tk.X, pady=(10, 0))
        
        self.lbl_disc_noches = tk.Label(self.discount_card, text="Noches: 0", bg="white", 
                                       font=("Segoe UI", 9), fg="#7f8c8d", anchor="w")
        self.lbl_disc_noches.pack(fill=tk.X, pady=(0, 5))

        self.lbl_final_price = tk.Label(self.discount_card, text="Precio Final: $0,00", bg="white", 
                                        font=("Segoe UI", 12, "bold"), fg="#e67e22", anchor="w")
        self.lbl_final_price.pack(fill=tk.X, pady=(5, 0))

        self.lbl_final_per_night = tk.Label(self.discount_card, text="P/Noche Final: $0,00", bg="white", 
                                            font=("Segoe UI", 9, "italic"), fg="#7f8c8d", anchor="w")
        self.lbl_final_per_night.pack(fill=tk.X, pady=2)

        # --- SECCIÓN DE CAPTACIÓN PLEGABLE ---
        self.lead_header = tk.Frame(left_panel, bg="#2c3e50")
        self.lead_header.pack(fill=tk.X)
        
        self.btn_toggle_lead = tk.Button(self.lead_header, text="📋 COTIZACIÓN ▼", font=("Segoe UI", 8, "bold"), 
                                        bg="#2c3e50", fg="white", bd=0, activebackground="#34495e", 
                                        activeforeground="white", anchor="w", padx=10, pady=5,
                                        command=self.toggle_lead_section)
        self.btn_toggle_lead.pack(fill=tk.X)

        self.lead_card = tk.Frame(left_panel, bg="white", padx=15, pady=15, highlightbackground="#e0e0e0", highlightthickness=1)
        # Inicia oculto por defecto

        tk.Label(self.lead_card, text="NOMBRE COMPLETO:", font=("Segoe UI", 8, "bold"), bg="white", fg="#7f8c8d").pack(anchor="w")
        self.ent_nombre = ttk.Entry(self.lead_card, textvariable=self.lead_fields["nombre"], font=("Segoe UI", 9))
        self.ent_nombre.pack(fill=tk.X, pady=(2, 8))
        self.ent_nombre.bind("<KeyRelease>", self._on_name_key_release)

        # Listbox para sugerencias (inicialmente oculto)
        self.suggestion_list = tk.Listbox(self.lead_card, height=4, font=("Segoe UI", 9), relief=tk.FLAT, bd=1, highlightthickness=1)
        self.suggestion_list.bind("<<ListboxSelect>>", self._select_client_suggestion)

        tk.Label(self.lead_card, text="TELÉFONO:", font=("Segoe UI", 8, "bold"), bg="white", fg="#7f8c8d").pack(anchor="w")
        ttk.Entry(self.lead_card, textvariable=self.lead_fields["telefono"], font=("Segoe UI", 9)).pack(fill=tk.X, pady=(2, 8))

        tk.Label(self.lead_card, text="EMAIL:", font=("Segoe UI", 8, "bold"), bg="white", fg="#7f8c8d").pack(anchor="w")
        ttk.Entry(self.lead_card, textvariable=self.lead_fields["email"], font=("Segoe UI", 9)).pack(fill=tk.X, pady=(2, 8))

        tk.Checkbutton(self.lead_card, text="📸 Incluir fotos (max 10)", variable=self.lead_fields["include_photos"], 
                       bg="white", font=("Segoe UI", 9)).pack(anchor="w", pady=5)

        # Contenedor de botones de envío
        send_btn_f = tk.Frame(self.lead_card, bg="white")
        send_btn_f.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(send_btn_f, text="📧 ENVIAR POR EMAIL", command=self.send_quotation).pack(fill=tk.X, pady=2)
        
        # Botón de WhatsApp con estilo personalizado
        self.btn_wa = tk.Button(send_btn_f, text="✅ ENVIAR POR WHATSAPP", command=self.send_quotation_whatsapp,
                               font=("Segoe UI", 9, "bold"), bg="#25D366", fg="white", 
                               relief=tk.FLAT, pady=8, cursor="hand2")
        self.btn_wa.pack(fill=tk.X, pady=2)

        self.btn_reservar = ttk.Button(left_panel, text="🚀 RESERVAR AHORA", state=tk.DISABLED, command=self.go_to_reservation)
        self.btn_reservar.pack(fill=tk.X, pady=10)
        
        ttk.Button(left_panel, text="LIMPIAR SELECCIÓN", command=self.reset_selection).pack(fill=tk.X)

        self.btn_ver_servicios = ttk.Button(left_panel, text="✨ VER SERVICIOS", command=self.show_services_popup)
        self.btn_ver_servicios.pack(fill=tk.X, pady=(10, 0))

        self.btn_ver_galeria = ttk.Button(left_panel, text="📸 VER GALERÍA", command=self.open_gallery)
        self.btn_ver_galeria.pack(fill=tk.X, pady=(10, 0))

        # Panel Derecho: Calendario
        right_panel = tk.Frame(main_frame, bg="#f0f2f5")
        right_panel.grid(row=0, column=1, sticky="nw", padx=(10, 20), pady=(20, 50))
        
        main_frame.columnconfigure(1, weight=1) # El calendario toma el espacio restante horizontalmente

        # --- SECCIÓN DE BÚSQUEDA Y FILTROS (Horizontal con Plegado) ---
        sel_card = tk.Frame(right_panel, bg="white", padx=20, pady=10, highlightbackground="#e0e0e0", highlightthickness=1)
        sel_card.pack(fill=tk.X)

        # Botón para mostrar/ocultar ubicación
        self.geo_visible = False
        self.btn_toggle_geo = ttk.Button(sel_card, text="📍 UBICACIÓN ▼", width=14, command=self.toggle_geo_filters)
        self.btn_toggle_geo.pack(side=tk.LEFT, padx=(0, 15))

        # Frame para filtros de ubicación (Prov/Loc) - Se packea dinámicamente
        self.geo_frame = tk.Frame(sel_card, bg="white")
        
        # Filtro: Provincia (dentro de geo_frame)
        tk.Label(self.geo_frame, text="Prov:", font=("Segoe UI", 8, "bold"), bg="white", fg="#7f8c8d").pack(side=tk.LEFT)
        self.prov_var = tk.StringVar(value="Todas")
        self.combo_prov = ttk.Combobox(self.geo_frame, textvariable=self.prov_var, state="readonly", font=("Segoe UI", 9), width=12)
        self.combo_prov.pack(side=tk.LEFT, padx=5)
        self.combo_prov.bind("<<ComboboxSelected>>", self.apply_filters)

        # Filtro: Localidad (dentro de geo_frame)
        tk.Label(self.geo_frame, text="Loc:", font=("Segoe UI", 8, "bold"), bg="white", fg="#7f8c8d").pack(side=tk.LEFT, padx=(5, 0))
        self.loc_var = tk.StringVar(value="Todas")
        self.combo_loc = ttk.Combobox(self.geo_frame, textvariable=self.loc_var, state="readonly", font=("Segoe UI", 9), width=15)
        self.combo_loc.pack(side=tk.LEFT, padx=5)
        self.combo_loc.bind("<<ComboboxSelected>>", self.apply_filters)

        # Separador visual sutil si está abierto
        self.geo_sep = tk.Label(self.geo_frame, text="|", fg="#e0e0e0", bg="white", padx=10)
        self.geo_sep.pack(side=tk.LEFT)

        # Filtros Fijos (Tipo y Selección)
        fixed_f = tk.Frame(sel_card, bg="white")
        fixed_f.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Filtro: Tipo
        tk.Label(fixed_f, text="Tipo:", font=("Segoe UI", 8, "bold"), bg="white", fg="#7f8c8d").pack(side=tk.LEFT)
        self.tipo_var = tk.StringVar(value="Todos")
        self.combo_tipo = ttk.Combobox(fixed_f, textvariable=self.tipo_var, state="readonly", font=("Segoe UI", 9), width=12)
        self.combo_tipo.pack(side=tk.LEFT, padx=5)
        self.combo_tipo.bind("<<ComboboxSelected>>", self.apply_filters)

        # Selector Final de Inmueble
        tk.Label(fixed_f, text="🏠 SELECCIONAR:", font=("Segoe UI", 8, "bold"), bg="white", fg="#2c3e50").pack(side=tk.LEFT, padx=(15, 5))
        self.prop_var = tk.StringVar()
        self.combo_prop = ttk.Combobox(fixed_f, textvariable=self.prop_var, state="readonly", font=("Segoe UI", 9, "bold"), width=25)
        self.combo_prop.pack(side=tk.LEFT, padx=5)
        self.combo_prop.bind("<<ComboboxSelected>>", self.on_property_selected)

        # Botón de Búsqueda Avanzada
        ttk.Button(fixed_f, text="🔍", width=3, command=self.open_advanced_search).pack(side=tk.LEFT, padx=15)

        # --- SECCIÓN DE DETALLES (Ahora arriba del calendario) ---
        self.info_card = tk.Frame(right_panel, bg="#f8f9fa", padx=20, pady=10, highlightbackground="#e0e0e0", highlightthickness=1)
        self.info_card.pack(fill=tk.X)

        tk.Label(self.info_card, text="🏠 DETALLES:", font=("Segoe UI", 9, "bold"), bg="#f8f9fa", fg="#2c3e50").pack(side=tk.LEFT, padx=(0, 10))
        
        self.lbl_capacidad = tk.Label(self.info_card, text="Capacidad: —", bg="#f8f9fa", font=("Segoe UI", 10))
        self.lbl_capacidad.pack(side=tk.LEFT, padx=15)

        self.lbl_precio = tk.Label(self.info_card, text="Precio/Noche: —", bg="#f8f9fa", font=("Segoe UI", 10, "bold"), fg="#27ae60")
        self.lbl_precio.pack(side=tk.LEFT, padx=15)

        # Contenedor para la marquesina de ubicación
        loc_container = tk.Frame(self.info_card, bg="#f8f9fa", width=300, height=25)
        loc_container.pack(side=tk.LEFT, padx=15, fill=tk.X, expand=True)
        loc_container.pack_propagate(False)

        self.lbl_ubicacion = tk.Label(loc_container, text="Ubicación: —", bg="#f8f9fa", font=("Segoe UI", 9), fg="#7f8c8d", anchor="w")
        self.lbl_ubicacion.pack(fill=tk.BOTH, expand=True)

        # Variables para la marquesina
        self.marquee_text = ""
        self.marquee_running = False

        cal_header = tk.Frame(right_panel, bg="#f8f9fa", pady=15)
        cal_header.pack(fill=tk.X)
        
        ttk.Button(cal_header, text="<<", width=5, command=self.prev_month).pack(side=tk.LEFT, padx=20)
        self.lbl_month = tk.Label(cal_header, text="MES AÑO", font=("Segoe UI", 14, "bold"), bg="#f8f9fa", fg="#2c3e50")
        self.lbl_month.pack(side=tk.LEFT, expand=True)
        ttk.Button(cal_header, text=">>", width=5, command=self.next_month).pack(side=tk.RIGHT, padx=20)
        
        days_header = tk.Frame(right_panel, bg="white")
        days_header.pack(fill=tk.X, padx=10)
        for d in ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]:
            tk.Label(days_header, text=d, width=10, font=("Segoe UI", 9, "bold"), bg="white", fg="#95a5a6").pack(side=tk.LEFT, expand=True)
            
        self.days_frame = tk.Frame(right_panel, bg="white", padx=10, pady=10)
        self.days_frame.pack(fill=tk.BOTH, expand=True)
        
        # Leyenda
        legend_frame = tk.Frame(right_panel, bg="#f8f9fa", pady=10)
        legend_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self._create_legend(legend_frame, "#27ae60", "Disponible")
        self._create_legend(legend_frame, "#3498db", "Ingreso")
        self._create_legend(legend_frame, "#e74c3c", "Ocupado")
        self._create_legend(legend_frame, "#9b59b6", "Egreso")
        self._create_legend(legend_frame, "#f1c40f", "Transición")
        self._create_legend(legend_frame, "#2980b9", "Tu Selección")
        
        tk.Label(right_panel, text="* Click en fecha ocupada para ver quién reservó", 
                 font=("Segoe UI", 8, "italic"), bg="white", fg="#7f8c8d").pack(side=tk.BOTTOM, pady=(0, 5))

    def _scroll_address(self):
        """Mueve el texto de la ubicación como una marquesina."""
        if not self.marquee_running:
            return
            
        # Tomar el texto actual, rotarlo y actualizar el label
        current = self.marquee_text
        self.marquee_text = current[1:] + current[0]
        self.lbl_ubicacion.config(text=self.marquee_text)
        
        # Programar la siguiente actualización (cada 150ms)
        self.window.after(150, self._scroll_address)

    def _create_legend(self, parent, color, text):
        f = tk.Frame(parent, bg="#f8f9fa")
        f.pack(side=tk.LEFT, padx=20, expand=True)
        tk.Frame(f, bg=color, width=15, height=15).pack(side=tk.LEFT, padx=5)
        tk.Label(f, text=text, font=("Segoe UI", 9), bg="#f8f9fa").pack(side=tk.LEFT)

    def load_properties(self):
        """Carga inicial de todos los inmuebles y sus filtros."""
        self.all_properties = self.db.get_all_properties()
        
        # Obtener valores únicos para los filtros iniciales
        provincias = sorted(list(set(p[5] for p in self.all_properties)))
        tipos = sorted(list(set(p[6] for p in self.all_properties)))
        
        self.combo_prov['values'] = ["Todas"] + provincias
        self.combo_tipo['values'] = ["Todos"] + tipos
        
        # Cargar todas inicialmente en el selector de inmuebles
        self.apply_filters()

    def apply_filters(self, event=None):
        """Filtra la lista de inmuebles según los criterios seleccionados."""
        prov = self.prov_var.get()
        loc = self.loc_var.get()
        tipo = self.tipo_var.get()
        
        filtered = []
        localidades = set()
        
        for p in self.all_properties:
            # p = (id, nombre, cap, dir, loc, prov, tipo, val, img)
            p_loc = p[4]
            p_prov = p[5]
            p_tipo = p[6]
            
            match_prov = (prov == "Todas" or p_prov == prov)
            match_tipo = (tipo == "Todos" or p_tipo == tipo)
            
            # Recolectar localidades posibles según provincia seleccionada
            if match_prov:
                localidades.add(p_loc)
            
            # Aplicar filtro de localidad si no es "Todas"
            match_loc = (loc == "Todas" or p_loc == loc)
            
            if match_prov and match_loc and match_tipo:
                filtered.append(p)

        # Actualizar opciones de localidad dinámicamente
        current_locs = sorted(list(localidades))
        self.combo_loc['values'] = ["Todas"] + current_locs
        if loc not in self.combo_loc['values']:
            self.loc_var.set("Todas")

        # Actualizar selector de inmuebles
        self.property_map = {p[1]: p for p in filtered}
        self.combo_prop['values'] = sorted(list(self.property_map.keys()))
        
        # Limpiar selección actual si ya no está en la lista filtrada
        if self.prop_var.get() not in self.property_map:
            self.prop_var.set("")
            self.selected_property = None
            self.draw_calendar()

    def toggle_geo_filters(self):
        """Muestra u oculta los filtros de Provincia y Localidad."""
        if self.geo_visible:
            self.geo_frame.pack_forget()
            self.btn_toggle_geo.config(text="📍 UBICACIÓN ▼")
            self.geo_visible = False
        else:
            # Insertar antes del frame de filtros fijos
            self.geo_frame.pack(side=tk.LEFT, after=self.btn_toggle_geo)
            self.btn_toggle_geo.config(text="📍 UBICACIÓN ▲")
            self.geo_visible = True

    def open_advanced_search(self):
        """Abre la ventana de búsqueda avanzada."""
        AdvancedSearchWindow(self.window, self.on_advanced_search_selected)

    def on_advanced_search_selected(self, prop_data, dates):
        """Callback cuando se selecciona un inmueble en la búsqueda avanzada."""
        # prop_data = (id, nombre, cap, dir, loc, prov, tipo, val, img)
        self.selected_property = prop_data
        self.prop_var.set(prop_data[1])
        
        # Sincronizar filtros por si acaso el inmueble no estaba visible
        self.prov_var.set("Todas")
        self.loc_var.set("Todas")
        self.tipo_var.set("Todos")
        self.apply_filters()
        
        # Forzar selección en el combo
        self.prop_var.set(prop_data[1])
        self.on_property_selected()
        
        # Cargar fechas seleccionadas
        self.start_date = dates["desde"]
        self.end_date = dates["hasta"]
        
        # Mover calendario al mes de inicio
        self.month = self.start_date.month
        self.year = self.start_date.year
        
        self.update_selection_display()
        self.draw_calendar()

    def show_services_popup(self):
        """Muestra los servicios del inmueble seleccionado en un popup con scroll."""
        if not self.selected_property:
            messagebox.showwarning("Atención", "Seleccione un inmueble para ver sus servicios.", parent=self.window)
            return
            
        servicios = self.db.get_property_services(self.selected_property[0])
        
        popup = tk.Toplevel(self.window)
        popup.title(f"Servicios - {self.selected_property[1]}")
        popup.geometry("380x550")
        popup.configure(bg="white")
        popup.transient(self.window)
        popup.grab_set()
        
        tk.Label(popup, text=f"✨ SERVICIOS DISPONIBLES", font=("Segoe UI", 12, "bold"), 
                 bg="#2c3e50", fg="white", pady=15).pack(fill=tk.X)
        
        # Contenedor para Scroll
        main_frame = tk.Frame(popup, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(main_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        # Primero pack el scrollbar a la derecha
        scrollbar.pack(side="right", fill="y")
        # Luego el canvas ocupando el resto
        canvas.pack(side="left", fill="both", expand=True)

        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Crear ventana dentro del canvas
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scrollable_frame.bind("<Configure>", on_frame_configure)
        
        def on_canvas_configure(event):
            # Ajustar el ancho del frame interno al ancho del canvas
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", on_canvas_configure)

        # Vincular rueda del ratón al scroll del popup
        def _on_mousewheel_popup(event):
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel_popup)
        
        # Asegurarse de desvincular al cerrar el popup
        def on_close_popup():
            canvas.unbind_all("<MouseWheel>")
            popup.destroy()
            
        popup.protocol("WM_DELETE_WINDOW", on_close_popup)

        # 1. Agregar Detalles del Inmueble (Dormitorios, Camas, Baños) al inicio
        # self.selected_property = (id, nombre, cap, dir, loc, prov, tipo, val, img, dorms, camas, banos)
        p = self.selected_property
        dorms = p[9] if len(p) > 9 and p[9] is not None else 0
        camas = p[10] if len(p) > 10 and p[10] is not None else 0
        banos = p[11] if len(p) > 11 and p[11] is not None else 0

        details = [
            ("🛏️", f"{dorms} Dormitorios"),
            ("🛌", f"{camas} Camas"),
            ("🚿", f"{banos} Baños")
        ]

        for icon, name in details:
            d_frame = tk.Frame(scrollable_frame, bg="#f8f9fa", padx=20, pady=5)
            d_frame.pack(fill=tk.X, pady=2)
            tk.Label(d_frame, text=icon, font=("Segoe UI", 12), bg="#f8f9fa").pack(side=tk.LEFT, padx=(0, 15))
            tk.Label(d_frame, text=name.upper(), font=("Segoe UI", 10, "bold"), bg="#f8f9fa", fg="#2c3e50").pack(side=tk.LEFT)

        tk.Frame(scrollable_frame, height=2, bg="#e0e0e0").pack(fill=tk.X, pady=10)

        # 2. Agregar Servicios de la DB
        if not servicios:
            tk.Label(scrollable_frame, text="No se especificaron otros servicios.",
                      font=("Segoe UI", 10, "italic"), bg="white", fg="#7f8c8d").pack(pady=20, fill=tk.X)
        else:
            for icon, name in servicios:
                s_frame = tk.Frame(scrollable_frame, bg="white", padx=20)
                s_frame.pack(fill=tk.X, pady=8)
                tk.Label(s_frame, text=icon, font=("Segoe UI", 13), bg="white").pack(side=tk.LEFT, padx=(0, 15))
                tk.Label(s_frame, text=name, font=("Segoe UI", 11), bg="white", fg="#2c3e50").pack(side=tk.LEFT)        
        ttk.Button(popup, text="CERRAR", command=on_close_popup).pack(pady=15)

    def open_gallery(self):
        """Abre el visor de galería para el inmueble seleccionado."""
        if not self.selected_property:
            messagebox.showwarning("Atención", "Seleccione un inmueble para ver su galería.", parent=self.window)
            return
            
        images = self.db.get_gallery_images(self.selected_property[0])
        if not images:
            messagebox.showinfo("Información", "Este inmueble no tiene fotos en su galería.", parent=self.window)
            return
            
        paths = [img[1] for img in images]
        client_email = self.lead_fields["email"].get() if "email" in self.lead_fields else None
        client_phone = self.lead_fields["telefono"].get() if "telefono" in self.lead_fields else None
        GalleryWindow(self.window, self.selected_property[1], paths, 
                      client_email=client_email, client_phone=client_phone)

    def on_property_selected(self, event=None):
        name = self.prop_var.get()
        if name in self.property_map:
            p = self.property_map[name]
            self.selected_property = p
            self.lbl_capacidad.config(text=f"Capacidad: {p[2]} personas")
            self.lbl_precio.config(text=f"Precio/Noche: {self._format_currency(p[7])}")
            
            # Configurar marquesina
            full_address = f"Ubicación: {p[3]}, {p[4]} ({p[5]})"
            self.marquee_text = full_address + "          " # Espacio de separación
            
            if not self.marquee_running:
                self.marquee_running = True
                self._scroll_address()
            
            # Cargar fechas reservadas
            self.reserved_ranges = self.db.get_reserved_ranges(id_inmueble=p[0])
            self.reset_selection()
            self.draw_calendar()

    def _format_currency(self, value):
        try:
            val = float(value)
            formatted = f"{val:,.2f}"
            m, d = formatted.split('.')
            return f"${m.replace(',', '.')},{d}"
        except: return str(value)

    def draw_calendar(self):
        for widget in self.days_frame.winfo_children():
            widget.destroy()
            
        meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        self.lbl_month.config(text=f"{meses[self.month].upper()} {self.year}")
        
        cal = calendar.monthcalendar(self.year, self.month)
        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                if day == 0:
                    continue
                
                d = date(self.year, self.month, day)
                day_info = self._get_day_info(d)
                is_selected = self._is_selected(d)
                is_past = d < self.now
                
                color = day_info["color"]
                fg = "white"
                
                if is_past:
                    fg = "#d1d8e0"
                    color = "white"
                elif is_selected:
                    color = "#3498db"
                    fg = "white"
                elif day_info["status"] == "disponible":
                    color = "#27ae60"
                    fg = "white"
                
                btn = tk.Button(self.days_frame, text=str(day), font=("Segoe UI", 14, "bold"),
                               bg=color, fg=fg, relief=tk.FLAT, bd=0, height=3, # Aumentar más la altura
                               command=lambda dd=d, info=day_info: self.on_day_click(dd, info))
                
                if is_past:
                     btn.config(state=tk.DISABLED)
                
                btn.grid(row=row_idx, column=col_idx, padx=3, pady=8, sticky="nsew") # Más padding vertical para estirar el calendario

        for i in range(7):
            self.days_frame.columnconfigure(i, weight=1)
        for i in range(len(cal)):
            self.days_frame.rowconfigure(i, weight=1)

    def _get_day_info(self, d):
        info = {
            "status": "disponible",
            "clients": [],
            "color": "#27ae60" # Verde por defecto
        }
        
        is_ingreso = False
        is_egreso = False
        is_occupied = False
        
        for ingreso, egreso, cliente in self.reserved_ranges:
            if isinstance(ingreso, str):
                ingreso = datetime.strptime(ingreso, "%Y-%m-%d").date()
            if isinstance(egreso, str):
                egreso = datetime.strptime(egreso, "%Y-%m-%d").date()
            
            if d == ingreso:
                is_ingreso = True
                info["clients"].append(f"➡️ INGRESO: {cliente}")
            elif d == egreso:
                is_egreso = True
                info["clients"].append(f"⬅️ EGRESO: {cliente}")
            elif ingreso < d < egreso:
                is_occupied = True
                info["clients"].append(f"🔴 OCUPADO: {cliente}")

        if is_occupied:
            info["status"] = "ocupado"
            info["color"] = "#e74c3c" # Rojo
        elif is_ingreso and is_egreso:
            info["status"] = "transicion"
            info["color"] = "#f1c40f" # Amarillo (Transición)
        elif is_ingreso:
            info["status"] = "ingreso"
            info["color"] = "#3498db" # Azul (Ingreso)
        elif is_egreso:
            info["status"] = "egreso"
            info["color"] = "#9b59b6" # Púrpura (Egreso)
            
        return info

    def _is_reserved(self, d):
        # Mantenemos este método por compatibilidad interna si se usa en validaciones de rango
        for ingreso, egreso, cliente in self.reserved_ranges:
            if isinstance(ingreso, str):
                ingreso = datetime.strptime(ingreso, "%Y-%m-%d").date()
            if isinstance(egreso, str):
                egreso = datetime.strptime(egreso, "%Y-%m-%d").date()
            if ingreso <= d < egreso:
                return cliente
        return None

    def _is_selected(self, d):
        if self.start_date and self.end_date:
            return self.start_date <= d < self.end_date
        if self.start_date:
            return d == self.start_date
        return False

    def on_day_click(self, d, day_info=None):
        if day_info and day_info["status"] != "disponible" and day_info["status"] != "egreso":
            # Si es egreso, permitimos click para que pueda ser el inicio de una nueva reserva
            # Pero si hay otros estados (ocupado, ingreso, transicion), mostramos info
            msg = "\n".join(day_info["clients"])
            messagebox.showinfo("Información de Reserva", msg, parent=self.window)
            if day_info["status"] != "egreso" and day_info["status"] != "transicion":
                return

        if not self.selected_property:
            messagebox.showwarning("Atención", "Primero seleccione un inmueble", parent=self.window)
            return

        if not self.start_date or (self.start_date and self.end_date):
            # Primera selección o reinicio
            self.start_date = d
            self.end_date = None
        else:
            # Segunda selección (fecha de egreso)
            if d <= self.start_date:
                self.start_date = d
                self.end_date = None
            else:
                # Verificar que no haya reservas en el medio
                temp_date = self.start_date
                has_conflict = False
                while temp_date < d:
                    if self._is_reserved(temp_date):
                        has_conflict = True
                        break
                    temp_date += timedelta(days=1)
                
                if has_conflict:
                    messagebox.showerror("Conflicto", "El rango seleccionado incluye días ya reservados.", parent=self.window)
                    self.start_date = d
                    self.end_date = None
                else:
                    self.end_date = d
        
        self.update_selection_display()
        self.draw_calendar()

    def on_discount_change(self, event=None):
        """Maneja el formateo visual del descuento mientras se escribe."""
        text = self.discount_var.get()
        if self.discount_is_percentage.get():
            # Solo permitir números y un punto
            cleaned = "".join(c for c in text if c.isdigit() or c == ".")
            if cleaned != text:
                self.discount_var.set(cleaned)
        else:
            # Formato moneda para monto fijo
            cleaned = "".join(c for c in text if c.isdigit())
            if cleaned:
                val = float(cleaned)
                formatted = f"{val:,.0f}".replace(",", ".")
                self.discount_var.set(f"${formatted}")
            else:
                self.discount_var.set("")
        
        self.update_selection_display()

    def update_selection_display(self):
        if self.start_date:
            self.lbl_desde.config(text=f"Desde: {self.start_date.strftime('%d/%m/%Y')}")
        else:
            self.lbl_desde.config(text="Desde: No seleccionada")

        if self.end_date:
            self.lbl_hasta.config(text=f"Hasta: {self.end_date.strftime('%d/%m/%Y')}")
            noches = (self.end_date - self.start_date).days
            self.lbl_noches.config(text=f"Noches: {noches}")

            # Actualizar labels en sección de negociación
            self.lbl_disc_rango.config(text=f"Estadía: {self.start_date.strftime('%d/%m')} al {self.end_date.strftime('%d/%m/%Y')}")
            self.lbl_disc_noches.config(text=f"Noches: {noches}")

            # Calcular costo total
            total_sin_desc = 0
            if self.selected_property:
                precio_noche = float(self.selected_property[7])
                total_sin_desc = noches * precio_noche
                self.lbl_costo_total.config(text=f"Costo Total: {self._format_currency(total_sin_desc)}")

            # Calcular Descuento
            final_price = total_sin_desc
            discount_val_str = self.discount_var.get()

            try:
                if self.discount_is_percentage.get():
                    # Porcentaje
                    perc = float(discount_val_str) if discount_val_str else 0.0
                    discount_amount = total_sin_desc * (perc / 100)
                    final_price = total_sin_desc - discount_amount
                else:
                    # Monto fijo
                    fixed = float(discount_val_str.replace("$", "").replace(".", "")) if discount_val_str else 0.0
                    final_price = total_sin_desc - fixed
            except:
                final_price = total_sin_desc

            self.lbl_final_price.config(text=f"Precio Final: {self._format_currency(max(0, final_price))}")

            # Calcular precio por noche final (guía para el dueño)
            if noches > 0:
                p_noche_final = max(0, final_price) / noches
                self.lbl_final_per_night.config(text=f"P/Noche Final: {self._format_currency(p_noche_final)}")
            else:
                self.lbl_final_per_night.config(text="P/Noche Final: $0,00")

            self.btn_reservar.config(state=tk.NORMAL)
        else:
            self.lbl_hasta.config(text="Hasta: No seleccionada")
            self.lbl_noches.config(text="Noches: 0")
            self.lbl_disc_rango.config(text="Estadía: -")
            self.lbl_disc_noches.config(text="Noches: 0")
            self.lbl_costo_total.config(text="Costo Total: $0,00")
            self.lbl_final_price.config(text="Precio Final: $0,00")
            self.lbl_final_per_night.config(text="P/Noche Final: $0,00")
            self.btn_reservar.config(state=tk.DISABLED)
    def reset_selection(self):
        self.start_date = None
        self.end_date = None
        self.discount_var.set("0")
        self.update_selection_display()
        self.draw_calendar()

    def prev_month(self):
        self.month -= 1
        if self.month == 0:
            self.month = 12
            self.year -= 1
        self.draw_calendar()

    def next_month(self):
        self.month += 1
        if self.month == 13:
            self.month = 1
            self.year += 1
        self.draw_calendar()

    def go_to_reservation(self):
        if not self.start_date or not self.end_date or not self.selected_property:
            return
            
        # Preparar datos de descuento para el formulario de reserva
        discount_val = self.discount_var.get()
        if not self.discount_is_percentage.get():
            discount_val = discount_val.replace("$", "").replace(".", "")

        initial_data = {
            "inmueble": self.selected_property[1],
            "fecha_ingreso": self.start_date.strftime("%d/%m/%Y"),
            "fecha_egreso": self.end_date.strftime("%d/%m/%Y"),
            "cantidad_personas": self.selected_property[2],
            "imagen": self.selected_property[8] if len(self.selected_property) > 8 else None,
            "descuento": discount_val,
            "discount_is_percentage": self.discount_is_percentage.get()
        }
        
        self.window.destroy()
        self.controller.create_reservation(initial_data=initial_data)
