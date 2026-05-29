import tkinter as tk
from tkinter import ttk, messagebox, StringVar, BooleanVar, Frame
from datetime import date
from controllers.client_controller import ClientController
from controllers.property_controller import PropertyController
from controllers.reservation_controller import ReservationController
from controllers.database import Database
from ui.client_list_window import ClientListWindow
from ui.property_form_window import PropertyFormWindow
from ui.property_list_window import PropertyListWindow
from ui.reservation_list_window import ReservationListWindow
from ui.finance_window import FinanceWindow
from ui.consultation_window import ConsultationWindow
from ui.config_window import ConfigWindow
from PIL import Image, ImageTk
import os

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sistema de Reservas Profesional")

        # Crear instancias de los controladores (mantenemos la estructura existente)
        self.property_controller = PropertyController()
        self.client_controller = ClientController()
        self.reservation_controller = ReservationController(self.root)

        # Variables para el formulario de clientes
        self.client_fields = {
            "id_clientes": StringVar(),
            "documento": StringVar(),
            "nombre": StringVar(),
            "apellido": StringVar(),
            "email": StringVar(),
            "telefono": StringVar(),
            "provincia": StringVar(),
            "fecha_registro": StringVar(),
            "cantidad_personas": StringVar(),
            "adelanto": StringVar(),
            "discount_is_percentage": BooleanVar(),
            "descuento": StringVar(),
            "inmueble": StringVar(),
            "fecha_ingreso": StringVar(),
            "fecha_egreso": StringVar()
        }

    def setup_ui(self):
        """Configurar la interfaz gráfica principal con un diseño de Dashboard Profesional"""
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f2f5")

        # --- ESTILOS ---
        style = ttk.Style()
        style.configure("Sidebar.TFrame", background="#2c3e50")
        style.configure("Content.TFrame", background="#f0f2f5")
        style.configure("Nav.TButton", font=("Segoe UI", 10, "bold"), padding=12, width=22)
        style.configure("SubNav.TButton", font=("Segoe UI", 9), padding=8, width=25)
        style.configure("Group.TButton", font=("Segoe UI", 10, "bold"), padding=12, width=22, foreground="#3498db")
        style.configure("DashboardHeader.TLabel", font=("Segoe UI", 22, "bold"), background="#f0f2f5", foreground="#2c3e50")
        style.configure("Card.TFrame", background="white", relief="flat", borderwidth=0)
        style.configure("CardHeader.TLabel", font=("Segoe UI", 14, "bold"), background="white", foreground="#34495e")

        # --- ESTRUCTURA PRINCIPAL ---
        # Sidebar (Izquierda)
        self.sidebar = ttk.Frame(self.root, style="Sidebar.TFrame")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # Contenedor para el Logo/Header (asegura que esté arriba de los botones)
        self.sidebar_header = tk.Frame(self.sidebar, bg="#2c3e50")
        self.sidebar_header.pack(side=tk.TOP, fill=tk.X)

        # Contenedor Principal (Derecha)
        self.main_container = ttk.Frame(self.root, style="Content.TFrame")
        self.main_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- CONTENIDO SIDEBAR ---
        self.db = Database()
        self.logo_image = None
        self._display_sidebar_header()
        
        # Grupo: INICIO
        btn_refresh = ttk.Button(self.sidebar, text="🏠 INICIO / REFRESCAR", 
                                 command=self.refresh_dashboard, style="Nav.TButton")
        btn_refresh.pack(fill=tk.X, padx=20, pady=(10, 5))

        # Grupo: RESERVAS
        self._create_nav_group("📅 RESERVAS", [
            ("Consultar Disponibilidad", self.show_consultation_tool),
            ("Nueva Reserva", self.handle_new_reservation),
            ("Ver Reservas", self.handle_my_reservations),
            ("Ver Cotizaciones", self.show_quotation_list),
        ])

        # Grupo: GESTIÓN
        self._create_nav_group("🏨 GESTIÓN", [
            ("Ver Clientes", self.show_client_list),
            ("Ver Prospectos (Leads)", self.show_prospect_list),
            ("Ver Inmuebles", self.show_property_list),
            ("Registrar Cliente", self.handle_clients),
            ("Registrar Inmueble", self.handle_properties),
            ("Control Financiero", self.show_finance_dashboard),
        ])

        # Grupo: ADMINISTRACIÓN
        self._create_nav_group("⚙️ SISTEMA", [
            ("Configuración", self.show_config),
        ])

        # ACCIONES RÁPIDAS (Botones directos)
        tk.Label(self.sidebar, text="⚡ ACCIONES RÁPIDAS", font=("Segoe UI", 9, "bold"), 
                 background="#2c3e50", foreground="#3498db").pack(fill=tk.X, padx=25, pady=(20, 5), anchor="w")
        
        btn_quick_quote = ttk.Button(self.sidebar, text="➕ Nueva Cotización", 
                                   command=self.show_consultation_tool, style="Nav.TButton")
        btn_quick_quote.pack(fill=tk.X, padx=20, pady=2)
        
        btn_quick_pay = ttk.Button(self.sidebar, text="💰 Cargar Pago", 
                                 command=self.handle_my_reservations, style="Nav.TButton")
        btn_quick_pay.pack(fill=tk.X, padx=20, pady=2)

        ttk.Label(self.sidebar, text="Admin Panel v2.5", font=("Segoe UI", 8), background="#2c3e50", foreground="#95a5a6").pack(side=tk.BOTTOM, pady=30)

        # --- CONTENIDO PRINCIPAL ---
        header_area = ttk.Frame(self.main_container, style="Content.TFrame", padding=(40, 30, 40, 10))
        header_area.pack(fill=tk.X)
        
        ttk.Label(header_area, text="Panel de Control General", style="DashboardHeader.TLabel").pack(side=tk.LEFT)
        self.lbl_today = ttk.Label(header_area, text=date.today().strftime("%d de %B, %Y"), font=("Segoe UI", 12), background="#f0f2f5", foreground="#7f8c8d")
        self.lbl_today.pack(side=tk.RIGHT, pady=15)

        # Área de Widgets/Cards
        widgets_area = ttk.Frame(self.main_container, style="Content.TFrame", padding=40)
        widgets_area.pack(fill=tk.BOTH, expand=True)
        widgets_area.columnconfigure(0, weight=1)
        widgets_area.columnconfigure(1, weight=1)
        widgets_area.columnconfigure(2, weight=1)
        widgets_area.columnconfigure(3, weight=1)

        # --- FILA 1: KPIs ---
        self.kpi_pending = self._create_kpi_card(widgets_area, 0, 0, "COBROS PENDIENTES", "#e74c3c", command=self.show_finance_dashboard)
        self.kpi_expiring = self._create_kpi_card(widgets_area, 0, 1, "VENTAS EN RIESGO", "#f39c12", command=lambda: self.show_quotation_list(show_at_risk=True))
        self.kpi_occupancy = self._create_kpi_card(widgets_area, 0, 2, "OCUPACIÓN HOY", "#3498db", command=self.handle_my_reservations)
        self.kpi_revenue = self._create_kpi_card(widgets_area, 0, 3, "INGRESOS MES", "#27ae60", command=self.show_finance_dashboard)

        # --- FILA 2: PRÓXIMOS MOVIMIENTOS ---
        # Card: Próximos Ingresos
        self.card_in = tk.Frame(widgets_area, bg="white", highlightbackground="#e0e0e0", highlightthickness=1)
        self.card_in.grid(row=1, column=0, columnspan=2, padx=(0, 10), pady=(30, 0), sticky="nsew")
        
        in_header = tk.Frame(self.card_in, bg="#27ae60", height=5)
        in_header.pack(fill=tk.X)
        in_content = tk.Frame(self.card_in, bg="white", padx=30, pady=25)
        in_content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(in_content, text="📥 PRÓXIMO CHECK-IN", font=("Segoe UI", 10, "bold"), bg="white", fg="#27ae60").pack(anchor="w")
        self.lbl_checkin = tk.Label(in_content, text="—", font=("Segoe UI", 24, "bold"), bg="white", fg="#2c3e50")
        self.lbl_checkin.pack(anchor="w", pady=10)
        self.lbl_checkin_name = tk.Label(in_content, text="", font=("Segoe UI", 13, "bold"), bg="white", fg="#34495e")
        self.lbl_checkin_name.pack(anchor="w")
        self.lbl_checkin_inmueble = tk.Label(in_content, text="", font=("Segoe UI", 11), bg="white", fg="#7f8c8d")
        self.lbl_checkin_inmueble.pack(anchor="w", pady=(5, 10))
        
        info_in = tk.Frame(in_content, bg="white")
        info_in.pack(fill=tk.X)
        self.lbl_checkin_phone = tk.Label(info_in, text="", font=("Segoe UI", 11), bg="white", fg="#2c3e50")
        self.lbl_checkin_phone.pack(side=tk.LEFT)
        self.lbl_checkin_prov = tk.Label(info_in, text="", font=("Segoe UI", 11, "italic"), bg="white", fg="#95a5a6")
        self.lbl_checkin_prov.pack(side=tk.RIGHT)

        # Card: Próximos Egresos
        self.card_out = tk.Frame(widgets_area, bg="white", highlightbackground="#e0e0e0", highlightthickness=1)
        self.card_out.grid(row=1, column=2, columnspan=2, padx=(10, 0), pady=(30, 0), sticky="nsew")
        
        out_header = tk.Frame(self.card_out, bg="#2980b9", height=5)
        out_header.pack(fill=tk.X)
        out_content = tk.Frame(self.card_out, bg="white", padx=30, pady=25)
        out_content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(out_content, text="📤 PRÓXIMO CHECK-OUT", font=("Segoe UI", 10, "bold"), bg="white", fg="#2980b9").pack(anchor="w")
        self.lbl_checkout = tk.Label(out_content, text="—", font=("Segoe UI", 24, "bold"), bg="white", fg="#2c3e50")
        self.lbl_checkout.pack(anchor="w", pady=10)
        self.lbl_checkout_name = tk.Label(out_content, text="", font=("Segoe UI", 13, "bold"), bg="white", fg="#34495e")
        self.lbl_checkout_name.pack(anchor="w")
        self.lbl_checkout_inmueble = tk.Label(out_content, text="", font=("Segoe UI", 11), bg="white", fg="#7f8c8d")
        self.lbl_checkout_inmueble.pack(anchor="w", pady=(5, 10))
        
        info_out = tk.Frame(out_content, bg="white")
        info_out.pack(fill=tk.X)
        self.lbl_checkout_phone = tk.Label(info_out, text="", font=("Segoe UI", 11), bg="white", fg="#2c3e50")
        self.lbl_checkout_phone.pack(side=tk.LEFT)
        self.lbl_checkout_prov = tk.Label(info_out, text="", font=("Segoe UI", 11, "italic"), bg="white", fg="#95a5a6")
        self.lbl_checkout_prov.pack(side=tk.RIGHT)

        # --- FILA 3: GRÁFICOS ---
        self.card_chart_occ = tk.Frame(widgets_area, bg="white", highlightbackground="#e0e0e0", highlightthickness=1)
        self.card_chart_occ.grid(row=2, column=0, columnspan=2, padx=(0, 10), pady=(30, 0), sticky="nsew")
        
        self.card_chart_rev = tk.Frame(widgets_area, bg="white", highlightbackground="#e0e0e0", highlightthickness=1)
        self.card_chart_rev.grid(row=2, column=2, columnspan=2, padx=(10, 0), pady=(30, 0), sticky="nsew")
        
        # Títulos de gráficos
        tk.Label(self.card_chart_occ, text="📊 OCUPACIÓN PRÓXIMOS 7 DÍAS", font=("Segoe UI", 9, "bold"), bg="white", fg="#34495e").pack(anchor="w", padx=20, pady=(15, 0))
        tk.Label(self.card_chart_rev, text="💰 INGRESOS MENSUALES (ÚLT. 6 MESES)", font=("Segoe UI", 9, "bold"), bg="white", fg="#34495e").pack(anchor="w", padx=20, pady=(15, 0))

        self.canvas_occ = tk.Canvas(self.card_chart_occ, bg="white", height=180, highlightthickness=0)
        self.canvas_occ.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 15))
        
        self.canvas_rev = tk.Canvas(self.card_chart_rev, bg="white", height=180, highlightthickness=0)
        self.canvas_rev.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 15))

        self.refresh_dashboard()

    def _create_quick_action(self, parent, text, color, command):
        """Crea un botón de acción rápida estilizado."""
        btn = tk.Button(parent, text=text, font=("Segoe UI", 9, "bold"), 
                        bg="white", fg=color, activebackground=color, activeforeground="white",
                        relief=tk.FLAT, highlightbackground="#e0e0e0", highlightthickness=1,
                        padx=20, pady=12, cursor="hand2", command=command)
        btn.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)
        
        # Efecto hover simple
        btn.bind("<Enter>", lambda e: btn.config(bg="#f8f9fa"))
        btn.bind("<Leave>", lambda e: btn.config(bg="white"))

    def _create_kpi_card(self, parent, row, col, title, color, command=None):
        card = tk.Frame(parent, bg="white", highlightbackground="#e0e0e0", highlightthickness=1, cursor="hand2")
        card.grid(row=row, column=col, padx=10, sticky="nsew")
        
        line = tk.Frame(card, bg=color, height=4)
        line.pack(fill=tk.X)
        
        content = tk.Frame(card, bg="white", padx=20, pady=20)
        content.pack(fill=tk.BOTH)
        
        tk.Label(content, text=title, font=("Segoe UI", 8, "bold"), bg="white", fg="#7f8c8d", cursor="hand2").pack(anchor="w")
        lbl_val = tk.Label(content, text="—", font=("Segoe UI", 16, "bold"), bg="white", fg=color, cursor="hand2")
        lbl_val.pack(anchor="w", pady=(5, 0))

        # Hacer que toda la tarjeta sea clickable
        if command:
            for widget in [card, content, lbl_val]:
                widget.bind("<Button-1>", lambda e: command())
            
            # Efecto hover
            def on_enter(e):
                card.config(highlightbackground=color, highlightthickness=2)
            def on_leave(e):
                card.config(highlightbackground="#e0e0e0", highlightthickness=1)
            
            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)

        return lbl_val

    def _format_currency(self, value, decimals=True):
        try:
            val = float(value)
            if decimals:
                formatted = f"{val:,.2f}"
                m, d = formatted.split('.')
                return f"${m.replace(',', '.')},{d}"
            else:
                return f"${f'{val:,.0f}'.replace(',', '.')}"
        except: return str(value)

        self.refresh_dashboard()

    def handle_new_reservation(self):
        """Manejar la lógica para iniciar una nueva reserva"""
        self.reservation_controller.create_reservation()

    def show_consultation_tool(self):
        """Muestra la herramienta de consulta de disponibilidad"""
        ConsultationWindow(self.root, self.reservation_controller)

    def handle_my_reservations(self):
        ReservationListWindow(self.root, self.reservation_controller)

    def show_quotation_list(self, show_at_risk=False):
        """Mostrar la ventana de lista de cotizaciones"""
        from ui.quotation_list_window import QuotationListWindow
        QuotationListWindow(self.root, self.reservation_controller, show_at_risk=show_at_risk)

    def handle_contact(self):
        """Manejar la sección de contacto y soporte"""
        pass

    def handle_clients(self):
        """Manejar la lógica para el registro de nuevos clientes"""
        client_window = tk.Toplevel(self.root)
        client_window.title("Registrar Nuevo Cliente")
        client_window.geometry("550x500")
        client_window.configure(bg="#f8f9fa")
        client_window.transient(self.root)

        # Estilos locales
        style = ttk.Style(client_window)
        style.configure("ClientFormHeader.TLabel", font=("Segoe UI", 16, "bold"), foreground="#2c3e50", background="#f8f9fa")
        style.configure("ClientFormSection.TLabelframe", font=("Segoe UI", 10, "bold"))
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=10)

        main_frame = ttk.Frame(client_window, padding=30)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Registro de Huésped", style="ClientFormHeader.TLabel").pack(pady=(0, 25))

        # Sección de Datos
        sec_form = ttk.LabelFrame(main_frame, text=" Información Personal ", padding=20, style="ClientFormSection.TLabelframe")
        sec_form.pack(fill=tk.X, pady=10)
        sec_form.columnconfigure(1, weight=1)

        # Obtener el próximo ID disponible
        db = Database()
        db.connect()
        next_id = db.get_next_available_client_id()
        self.client_fields["id_clientes"].set(str(next_id))

        # Campos del formulario (limpiar primero)
        for key in ["nombre", "apellido", "email", "telefono", "documento"]:
            self.client_fields[key].set("")

        fields_order = [
            ("ID Cliente:", "id_clientes", True),
            ("Documento:", "documento", False),
            ("Nombre:", "nombre", False),
            ("Apellido:", "apellido", False),
            ("Email:", "email", False),
            ("Teléfono:", "telefono", False)
        ]

        for i, (label_text, field_name, is_readonly) in enumerate(fields_order):
            ttk.Label(sec_form, text=label_text).grid(row=i, column=0, sticky=tk.W, pady=10, padx=(0, 15))
            state = "readonly" if is_readonly else "normal"
            ttk.Entry(sec_form, textvariable=self.client_fields[field_name], state=state).grid(row=i, column=1, sticky=tk.EW, pady=10)

        # Barra de Botones
        btn_frame = ttk.Frame(main_frame, padding=(0, 20, 0, 0))
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="CANCELAR", command=client_window.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="GUARDAR CLIENTE", style="Action.TButton", 
                   command=lambda: self.save_client(client_window)).pack(side=tk.RIGHT, padx=5)

    def save_client(self, client_window):
        """Guardar los datos del cliente en la base de datos"""
        nombre = self.client_fields["nombre"].get()
        apellido = self.client_fields["apellido"].get()
        email = self.client_fields["email"].get()
        telefono = self.client_fields["telefono"].get()
        documento = self.client_fields["documento"].get()
        id_cliente = self.client_fields["id_clientes"].get()

        if not (nombre and apellido and email and telefono and documento):
            messagebox.showerror("Error", "Todos los campos son obligatorios", parent=client_window)
            return

        client_data = (
            int(id_cliente),
            documento,
            nombre,
            apellido,
            email,
            telefono
        )

        db = Database()
        if db.connect():
            # Verificar duplicados manualmente para dar un mensaje específico
            existing, tipo = db.get_contact_by_email_or_dni(email, documento)
            if existing:
                messagebox.showerror("Error de Duplicado", f"Ya existe un {tipo} registrado con ese DNI o Email.\n\nNombre: {existing[2]} {existing[3]}\nTipo: {tipo.upper()}", parent=client_window)
                return

            if db.insert_client(client_data):
                messagebox.showinfo("Éxito", f"Cliente {nombre} {apellido} registrado exitosamente con ID #{id_cliente}", parent=client_window)
                client_window.destroy()
            else:
                messagebox.showerror("Error", "No se pudo guardar el cliente en la base de datos.", parent=client_window)
        else:
            messagebox.showerror("Error", "Error de conexión a la base de datos", parent=client_window)

    def save_reservation(self, reservation_window):
        """Guardar los datos de la reserva en la base de datos"""
        pass

    def handle_properties(self):
        """Manejar la lógica para inmuebles"""
        property_form = PropertyFormWindow(self.root)
        property_form.show()

    def show_client_list(self):
        """Mostrar la ventana de lista de clientes"""
        client_list_window = ClientListWindow(self.root)
        client_list_window.show()

    def show_prospect_list(self):
        """Mostrar la ventana de lista de prospectos"""
        from ui.prospect_list_window import ProspectListWindow
        ProspectListWindow(self.root)

    def show_property_list(self):
        """Mostrar la ventana de lista de inmuebles"""
        property_list_window = PropertyListWindow(self.root)
        property_list_window.show()

    def show_finance_dashboard(self):
        """Mostrar la ventana de control financiero"""
        FinanceWindow(self.root)

    def show_config(self):
        """Mostrar la ventana de configuración"""
        ConfigWindow(self.root)

    def _display_sidebar_header(self):
        """Muestra el logo o el nombre del hotel en el sidebar"""
        config = None
        if self.db.connect():
            config = self.db.get_config()
        
        # Limpiar header anterior
        for widget in self.sidebar_header.winfo_children():
            widget.destroy()

        if config and config.get('logo_path') and os.path.exists(config.get('logo_path')):
            try:
                img = Image.open(config.get('logo_path'))
                # Redimensionar manteniendo proporción (máx 180x120)
                img.thumbnail((180, 120))
                self.logo_image = ImageTk.PhotoImage(img)
                lbl_logo = tk.Label(self.sidebar_header, image=self.logo_image, background="#2c3e50")
                lbl_logo.pack(pady=(30, 10), padx=20)
                
                # También mostrar el nombre si existe
                if config.get('business_name'):
                    lbl_name = ttk.Label(self.sidebar_header, text=config.get('business_name'), 
                                         font=("Segoe UI", 12, "bold"), background="#2c3e50", foreground="#ecf0f1")
                    lbl_name.pack(pady=(0, 20))
                return
            except Exception as e:
                print(f"Error cargando logo: {e}")

        # Default fallback
        header_text = config.get('business_name') if config and config.get('business_name') else "SISTEMA HOTEL"
        lbl_default = ttk.Label(self.sidebar_header, text=header_text, font=("Segoe UI", 16, "bold"), 
                                background="#2c3e50", foreground="#ecf0f1")
        lbl_default.pack(pady=40)

    def _create_nav_group(self, title, items):
        """Crea un grupo de navegación desplegable en el sidebar"""
        group_frame = tk.Frame(self.sidebar, bg="#2c3e50")
        group_frame.pack(fill=tk.X, padx=20, pady=2)

        sub_frame = tk.Frame(group_frame, bg="#34495e")
        sub_frame.is_collapsed = True

        def toggle():
            if sub_frame.is_collapsed:
                sub_frame.pack(fill=tk.X, after=btn_group)
                btn_group.config(text=f"▼ {title}")
                sub_frame.is_collapsed = False
            else:
                sub_frame.pack_forget()
                btn_group.config(text=f"▶ {title}")
                sub_frame.is_collapsed = True

        btn_group = ttk.Button(group_frame, text=f"▶ {title}", command=toggle, style="Nav.TButton")
        btn_group.pack(fill=tk.X)

        for text, cmd in items:
            btn = ttk.Button(sub_frame, text=text, command=cmd, style="SubNav.TButton")
            btn.pack(fill=tk.X, padx=(20, 0), pady=2)

    def _draw_occupancy_chart(self, data):
        """Dibuja un gráfico de barras de ocupación en el canvas."""
        self.canvas_occ.delete("all")
        if not data: return
        
        self.root.update_idletasks() # Asegurar que los tamaños estén actualizados
        w = self.canvas_occ.winfo_width()
        h = self.canvas_occ.winfo_height()
        if w < 100: w = 450 # Fallbacks razonables
        if h < 50: h = 180
        
        padding_x = 40
        padding_y = 30
        chart_w = w - (padding_x * 2)
        chart_h = h - (padding_y * 2)
        
        # Valor máximo para escala (total de inmuebles)
        max_val = data[0][2] if data[0][2] > 0 else 1
        
        bar_w = chart_w / len(data)
        for i, (dt, count, total) in enumerate(data):
            x0 = padding_x + (i * bar_w) + 10
            x1 = padding_x + ((i + 1) * bar_w) - 10
            
            # Altura proporcional
            val_h = (count / max_val) * chart_h
            y0 = h - padding_y - val_h
            y1 = h - padding_y
            
            # Color según ocupación
            color = "#3498db" if count > 0 else "#f0f2f5"
            self.canvas_occ.create_rectangle(x0, y0, x1, y1, fill=color, outline="", tags="bar")
            
            # Etiquetas
            day_str = dt.strftime("%d/%m")
            self.canvas_occ.create_text((x0+x1)/2, h - padding_y + 15, text=day_str, font=("Segoe UI", 8), fill="#7f8c8d")
            if count > 0:
                self.canvas_occ.create_text((x0+x1)/2, y0 - 10, text=str(count), font=("Segoe UI", 8, "bold"), fill="#2c3e50")

    def _draw_revenue_chart(self, data):
        """Dibuja un gráfico de barras de ingresos mensuales en el canvas."""
        self.canvas_rev.delete("all")
        if not data: return
        
        # Revertir para mostrar cronológicamente (venía DESC) y tomar últimos 6
        data = data[:6][::-1]
        
        self.root.update_idletasks()
        w = self.canvas_rev.winfo_width()
        h = self.canvas_rev.winfo_height()
        if w < 100: w = 450
        if h < 50: h = 180
        
        padding_x = 50
        padding_y = 30
        chart_w = w - (padding_x * 2)
        chart_h = h - (padding_y * 2)
        
        max_rev = max([float(row[1]) for row in data]) if data else 1
        if max_rev == 0: max_rev = 1
        
        bar_w = chart_w / len(data)
        for i, (mes, total) in enumerate(data):
            x0 = padding_x + (i * bar_w) + 15
            x1 = padding_x + ((i + 1) * bar_w) - 15
            
            val_h = (float(total) / max_rev) * chart_h
            y0 = h - padding_y - val_h
            y1 = h - padding_y
            
            self.canvas_rev.create_rectangle(x0, y0, x1, y1, fill="#27ae60", outline="", tags="bar")
            
            # Formatear mes (YYYY-MM -> MM/YY)
            try:
                y, m = mes.split('-')
                label_mes = f"{m}/{y[2:]}"
            except: label_mes = mes
                
            self.canvas_rev.create_text((x0+x1)/2, h - padding_y + 15, text=label_mes, font=("Segoe UI", 8), fill="#7f8c8d")
            
            # Valor abreviado (K)
            val_k = float(total) / 1000
            label_val = f"{val_k:.1f}k" if val_k >= 1 else str(int(total))
            self.canvas_rev.create_text((x0+x1)/2, y0 - 10, text=label_val, font=("Segoe UI", 7, "bold"), fill="#27ae60")

    def refresh_dashboard(self):
        self._display_sidebar_header()
        from datetime import datetime
        now = datetime.now()
        meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

        def fmt_date(d):
            try:
                dt = datetime.strptime(str(d), "%Y-%m-%d")
                return f"{dt.day} {meses[dt.month]} {dt.year}"
            except: return str(d)

        db = Database()
        if db.connect():
            # 1. ACTUALIZAR KPIs
            # Cobros Pendientes
            summary = db.get_financial_summary()
            self.kpi_pending.config(text=self._format_currency(summary[2], decimals=False))
            
            # Ventas en Riesgo (cotizaciones que vencen en < 48hs)
            expiring_count = db.get_quotations_expiring_soon(hours=48)
            self.kpi_expiring.config(text=str(expiring_count))
            
            # Ocupación Hoy
            occ, total = db.get_today_occupancy_stats()
            pct = int((occ/total)*100) if total > 0 else 0
            self.kpi_occupancy.config(text=f"{occ}/{total} ({pct}%)")
            
            # Ingresos Mes (basado en lo cobrado/adelanto este mes)
            rev_month = db.get_revenue_by_month()
            current_month_str = now.strftime("%Y-%m")
            current_rev = 0.0
            for row in rev_month:
                if row[0] == current_month_str:
                    current_rev = float(row[1])
                    break
            self.kpi_revenue.config(text=self._format_currency(current_rev, decimals=False))

            # 2. ACTUALIZAR MOVIMIENTOS (INGRESOS/EGRESOS)
            # Actualizar Ingreso
            checkins = db.get_upcoming_checkins()
            if checkins:
                r = checkins[0]
                self.lbl_checkin.config(text=fmt_date(r[5]))
                self.lbl_checkin_name.config(text=str(r[1]).upper())
                self.lbl_checkin_phone.config(text=f"📞 {r[2]}")
                self.lbl_checkin_prov.config(text=f"📍 {r[3]}")
                self.lbl_checkin_inmueble.config(text=f"🏠 {r[4]}")
            else:
                self.lbl_checkin.config(text="Sin ingresos")
                self.lbl_checkin_name.config(text="")
                self.lbl_checkin_inmueble.config(text="Agenda libre")

            # Actualizar Egreso
            checkouts = db.get_upcoming_checkouts()
            if checkouts:
                r = checkouts[0]
                self.lbl_checkout.config(text=fmt_date(r[6]))
                self.lbl_checkout_name.config(text=str(r[1]).upper())
                self.lbl_checkout_phone.config(text=f"📞 {r[2]}")
                self.lbl_checkout_prov.config(text=f"📍 {r[3]}")
                self.lbl_checkout_inmueble.config(text=f"🏠 {r[4]}")
            else:
                self.lbl_checkout.config(text="Sin egresos")
                self.lbl_checkout_name.config(text="")
                self.lbl_checkout_inmueble.config(text="Todo al día")

            # 3. ACTUALIZAR GRÁFICOS
            occ_forecast = db.get_weekly_occupancy_forecast()
            self._draw_occupancy_chart(occ_forecast)
            self._draw_revenue_chart(rev_month)

    def run(self):
        self.setup_ui()
        self.root.mainloop()
