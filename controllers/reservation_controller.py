import os
from controllers.database import Database
from utils.email_sender import send_reservation_email
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from PIL import Image, ImageTk

import calendar

class CalendarDialog(tk.Toplevel):
    def __init__(self, parent, callback, reserved_ranges=None, initial_date=None, highlight_date=None):
        super().__init__(parent)
        self.title("Seleccionar Fecha")
        self.geometry("400x520") # Un poco más de altura
        self.callback = callback
        self.reserved_ranges = reserved_ranges or []
        self.now = date.today()
        
        # Determinar mes y año inicial
        if initial_date:
            if isinstance(initial_date, str):
                try:
                    initial_date = datetime.strptime(initial_date, "%d/%m/%Y").date()
                except:
                    initial_date = self.now
            self.year = initial_date.year
            self.month = initial_date.month
        else:
            self.year = self.now.year
            self.month = self.now.month

        # Fecha para resaltar (referencia visual)
        self.highlight_date = highlight_date
        if isinstance(self.highlight_date, str):
            try:
                self.highlight_date = datetime.strptime(self.highlight_date, "%d/%m/%Y").date()
            except:
                self.highlight_date = None

        self.setup_ui()
        self.draw_calendar()
        self.grab_set()

    def _get_day_info(self, d):
        info = {
            "status": "disponible",
            "clients": [],
            "color": "#27ae60" # Verde
        }
        is_ingreso = False
        is_egreso = False
        is_occupied = False

        for ingreso, egreso, cliente in self.reserved_ranges:
            if isinstance(ingreso, str):
                ingreso = datetime.strptime(str(ingreso), "%Y-%m-%d").date()
            if isinstance(egreso, str):
                egreso = datetime.strptime(str(egreso), "%Y-%m-%d").date()
            
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
            info["color"] = "#f1c40f" # Amarillo
        elif is_ingreso:
            info["status"] = "ingreso"
            info["color"] = "#3498db" # Azul
        elif is_egreso:
            info["status"] = "egreso"
            info["color"] = "#9b59b6" # Púrpura
            
        return info

    def _is_reserved(self, d):
        for ingreso, egreso, cliente in self.reserved_ranges:
            if isinstance(ingreso, str):
                ingreso = datetime.strptime(str(ingreso), "%Y-%m-%d").date()
            if isinstance(egreso, str):
                egreso = datetime.strptime(str(egreso), "%Y-%m-%d").date()
            if ingreso <= d < egreso:
                return cliente
        return None

    def setup_ui(self):
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(header, text="<<", width=5, command=self.prev_month).pack(side=tk.LEFT)
        self.month_label = ttk.Label(header, text="", font=('Arial', 12, 'bold'))
        self.month_label.pack(side=tk.LEFT, expand=True)
        ttk.Button(header, text=">>", width=5, command=self.next_month).pack(side=tk.RIGHT)
        
        days_header = tk.Frame(self, bg="white")
        days_header.pack(fill=tk.X, padx=10)
        # Nombres de días con un poco más de espacio
        for d in ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]:
            tk.Label(days_header, text=d, width=5, anchor="center", font=('Arial', 10, 'bold'), bg="white").pack(side=tk.LEFT, expand=True)
            
        self.days_frame = tk.Frame(self, bg="white")
        self.days_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Leyenda rápida
        legend = tk.Frame(self, bg="#f0f0f0")
        legend.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        items = [
            ("#27ae60", "Disp"), 
            ("#3498db", "Entra"), 
            ("#e74c3c", "Ocup"), 
            ("#9b59b6", "Sale"), 
            ("#f1c40f", "Trans"),
            ("#2c3e50", "INICIO")
        ]
        
        for c, t in items:
            f = tk.Frame(legend, bg="#f0f0f0")
            f.pack(side=tk.LEFT, expand=True)
            tk.Frame(f, bg=c, width=10, height=10).pack(side=tk.LEFT, padx=2)
            lbl_font = ("Arial", 7, "bold" if t == "INICIO" else "normal")
            tk.Label(f, text=t, font=lbl_font, bg="#f0f0f0").pack(side=tk.LEFT)

    def draw_calendar(self):
        for widget in self.days_frame.winfo_children():
            widget.destroy()
            
        # Nombres de meses en español (manual para evitar dependencia de locale)
        meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        self.month_label.config(text=f"{meses[self.month]} {self.year}")
        
        cal = calendar.monthcalendar(self.year, self.month)
        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                if day == 0:
                    tk.Label(self.days_frame, text="", bg="white").grid(row=row_idx, column=col_idx, sticky="nsew")
                else:
                    d = date(self.year, self.month, day)
                    day_info = self._get_day_info(d)
                    is_past = d < self.now
                    
                    color = day_info["color"]
                    fg = "white"
                    
                    # Prioridad: Si es la fecha resaltada (Inicio)
                    if self.highlight_date and d == self.highlight_date:
                        color = "#2c3e50" # Azul oscuro para resaltar inicio
                        fg = "#f1c40f"    # Dorado
                    elif is_past:
                        fg = "#d1d8e0"
                        color = "white"
                    elif day_info["status"] == "disponible":
                        color = "#27ae60"
                        fg = "white"
                    
                    btn = tk.Button(self.days_frame, text=str(day), font=("Arial", 14, "bold"),
                                   bg=color, fg=fg, relief=tk.FLAT, bd=0,
                                   command=lambda dd=day, info=day_info: self.on_day_click(dd, info))
                    
                    if is_past:
                        btn.config(state=tk.DISABLED)
                        
                    btn.grid(row=row_idx, column=col_idx, padx=2, pady=2, sticky="nsew")

        for i in range(7):
            self.days_frame.columnconfigure(i, weight=1)
        for i in range(len(cal)):
            self.days_frame.rowconfigure(i, weight=1)

    def on_day_click(self, day, day_info=None):
        if day_info and day_info["status"] != "disponible" and day_info["status"] != "egreso":
            msg = "\n".join(day_info["clients"])
            messagebox.showinfo("Información", msg, parent=self)
            if day_info["status"] != "egreso" and day_info["status"] != "transicion":
                return
        self.select_day(day)

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

    def select_day(self, day):
        try:
            selected_date_obj = date(self.year, self.month, day)
            
            # Validación: La fecha seleccionada no debe ser anterior a hoy
            if selected_date_obj < self.now:
                messagebox.showwarning("Fecha Inválida", "No es posible seleccionar una fecha pasada. Por favor, elija una fecha a partir de hoy.", parent=self)
                return
            
            selected_date_str = f"{day:02d}/{self.month:02d}/{self.year}"
            self.callback(selected_date_str)
            self.destroy()
        except Exception as e:
            # Manejo de cualquier error de fecha inesperado
            messagebox.showerror("Error", f"Error al seleccionar la fecha: {e}", parent=self)
            self.destroy()


class ReservationController:
    def __init__(self, master):
        self.master = master
        self.db = Database()
        # Configurar nombres de meses en español
        self.months = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
    
    def _format_currency(self, value):
        """Formatea un valor numérico como moneda ($1.234,56)."""
        try:
            if isinstance(value, str):
                # Limpiar la cadena antes de convertir
                value = value.replace('$', '').replace('.', '').replace(',', '.')
                value = float(value)
            
            # Formatear con estándar US primero para obtener comas y puntos
            formatted = f"{value:,.2f}"
            # Intercambiar comas y puntos para formato ES/AR
            # 1,234.56 -> 1.234,56
            # Primero cambiamos el punto decimal por un marcador temporal
            main_part, decimal_part = formatted.split('.')
            main_part = main_part.replace(',', '.')
            return f"${main_part},{decimal_part}"
        except (ValueError, TypeError):
            return "$0,00"

    def _parse_currency(self, value_str):
        """Convierte una cadena de moneda ($1.234,56) a float."""
        if not value_str:
            return 0.0
        try:
            # Eliminar $, luego eliminar puntos de miles, luego cambiar coma decimal por punto
            clean = value_str.replace('$', '').replace('.', '').replace(',', '.')
            return float(clean)
        except ValueError:
            return 0.0

    def format_discount_input(self, event, client_fields):
        text = client_fields["descuento"].get()
        if client_fields["discount_is_percentage"].get():
            cleaned_text = ''.join(filter(lambda char: char.isdigit() or char == '.', text))
            client_fields["descuento"].set(cleaned_text)
        else:
            cleaned_text = ''.join(filter(lambda char: char.isdigit(), text))
            if cleaned_text:
                val = float(cleaned_text)
                formatted = f"{val:,.0f}".replace(',', '.')
                client_fields["descuento"].set(f"${formatted}")
            else:
                client_fields["descuento"].set("")

        self.update_cost_total(client_fields)

    def format_down_payment_input(self, event, client_fields):
        """Formatea el campo de adelanto con símbolo $ y puntos de miles."""
        text = client_fields["adelanto"].get()
        cleaned_text = ''.join(filter(lambda char: char.isdigit(), text))
        
        if cleaned_text:
            val = float(cleaned_text)
            formatted = f"{val:,.0f}".replace(',', '.')
            client_fields["adelanto"].set(f"${formatted}")
        else:
            client_fields["adelanto"].set("")
        
        self.update_cost_total(client_fields)


    def open_client_search(self, client_fields, reservation_window):
        """Abre la búsqueda visual de clientes."""
        from ui.client_list_window import ClientListWindow
        
        def on_client_selected(client_data):
            # client_data = (id, documento, nombre, apellido, email, telefono)
            if client_data:
                client_fields["id_clientes"].set(str(client_data[0]))
                client_fields["documento"].set(str(client_data[1]))
                client_fields["nombre"].set(str(client_data[2]))
                client_fields["apellido"].set(str(client_data[3]))
                client_fields["email"].set(str(client_data[4]))
                client_fields["telefono"].set(str(client_data[5]))
                self.update_cost_total(client_fields)
            
        ClientListWindow(reservation_window, select_callback=on_client_selected)

    def create_reservation(self, initial_data=None):
        try:
            reservation_window = tk.Toplevel(self.master)
            reservation_window.title("Nueva Reserva - Panel de Gestión")
            reservation_window.geometry("950x850")
            reservation_window.configure(bg="#f0f2f5")
            
            # --- ESTILOS LOCALES ---
            style = ttk.Style(reservation_window)
            style.configure("ResHeader.TFrame", background="#2c3e50")
            style.configure("ResContent.TFrame", background="#f0f2f5")
            style.configure("ResCard.TLabelframe", font=("Segoe UI", 10, "bold"), background="white")
            style.configure("ResHeader.TLabel", font=("Segoe UI", 18, "bold"), foreground="white", background="#2c3e50")
            style.configure("ResAction.TButton", font=("Segoe UI", 10, "bold"), padding=12)

            # --- ENCABEZADO TIPO DASHBOARD ---
            header_frame = tk.Frame(reservation_window, bg="#2c3e50", height=80)
            header_frame.pack(fill=tk.X)
            header_frame.pack_propagate(False)
            
            tk.Label(header_frame, text="📋 REGISTRO DE NUEVA RESERVA", font=("Segoe UI", 16, "bold"), 
                     bg="#2c3e50", fg="#ecf0f1").pack(side=tk.LEFT, padx=30, pady=20)
            
            tk.Label(header_frame, text=f"ID OPERACIÓN: {datetime.now().strftime('%H%M%S')}", 
                     font=("Segoe UI", 9), bg="#2c3e50", fg="#95a5a6").pack(side=tk.RIGHT, padx=30)

            # --- CONTENEDOR DESPLAZABLE ---
            main_container = ttk.Frame(reservation_window, style="ResContent.TFrame")
            main_container.pack(fill=tk.BOTH, expand=True)

            canvas = tk.Canvas(main_container, bg="#f0f2f5", highlightthickness=0)
            scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="#f0f2f5")

            scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=920)
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            content_padding = tk.Frame(scrollable_frame, bg="#f0f2f5", padx=30, pady=20)
            content_padding.pack(fill=tk.BOTH, expand=True)

            client_fields = {
                "id_clientes": tk.StringVar(),
                "documento": tk.StringVar(),
                "nombre": tk.StringVar(),
                "apellido": tk.StringVar(),
                "email": tk.StringVar(),
                "telefono": tk.StringVar(),
                "provincia": tk.StringVar(),
                "fecha_registro": tk.StringVar(),
                "cantidad_personas": tk.StringVar(),
                "adelanto": tk.StringVar(),
                "descuento": tk.StringVar(),
                "inmueble": tk.StringVar(),
                "valor_dia": tk.StringVar(),
                "fecha_ingreso": tk.StringVar(),
                "fecha_egreso": tk.StringVar(),
                "noches": tk.StringVar(),
                "costo_total": tk.StringVar(),
                "costo_con_descuento": tk.StringVar(),
                "pago_pendiente": tk.StringVar(),
                "discount_is_percentage": tk.BooleanVar(),
                "display_adelanto": tk.StringVar(),
                "display_descuento": tk.StringVar(),
                "quotation_id": tk.StringVar(),
                "is_prospect": tk.BooleanVar(value=False)
            }

            client_fields["fecha_registro"].set(date.today().strftime("%d/%m/%Y"))
            client_fields["provincia"].set("Buenos Aires")

            # Aplicar datos iniciales si existen
            if initial_data:
                if "quotation_id" in initial_data:
                    client_fields["quotation_id"].set(str(initial_data["quotation_id"]))
                if "inmueble" in initial_data:
                    client_fields["inmueble"].set(initial_data["inmueble"])
                if "fecha_ingreso" in initial_data:
                    client_fields["fecha_ingreso"].set(initial_data["fecha_ingreso"])
                if "fecha_egreso" in initial_data:
                    client_fields["fecha_egreso"].set(initial_data["fecha_egreso"])
                if "cantidad_personas" in initial_data:
                    client_fields["cantidad_personas"].set(str(initial_data["cantidad_personas"]))
                if "descuento" in initial_data:
                    client_fields["descuento"].set(initial_data["descuento"])
                if "discount_is_percentage" in initial_data:
                    client_fields["discount_is_percentage"].set(initial_data["discount_is_percentage"])
                if "is_prospect" in initial_data:
                    client_fields["is_prospect"].set(initial_data["is_prospect"])
                if "id_cliente" in initial_data:
                    client_fields["id_clientes"].set(str(initial_data["id_cliente"]))
                    self.autofill_client_data(client_fields, parent=reservation_window)

            if not self.db.connection or not self.db.connection.is_connected():
                self.db.connect()
                
            # Solo buscar el próximo ID si no se cargó uno de la cotización
            if not client_fields["id_clientes"].get():
                next_id = self.db.get_next_available_client_id()
                client_fields["id_clientes"].set(str(next_id))

            provincias = ["Buenos Aires", "Catamarca", "Chaco", "Chubut", "CABA", "Córdoba", "Corrientes", "Entre Ríos", "Formosa", "Jujuy", "La Pampa", "La Rioja", "Mendoza", "Misiones", "Neuquén", "Río Negro", "Salta", "San Juan", "San Luis", "Santa Cruz", "Santa Fe", "Santiago del Estero", "Tierra del Fuego", "Tucumán"]
            properties = self.db.get_all_properties()
            self.property_map = {p[1]: p for p in properties}
            property_names = list(self.property_map.keys())

            # Si tenemos datos iniciales, actualizar el valor por día y recalcular
            if initial_data and "inmueble" in initial_data:
                name = initial_data["inmueble"]
                if name in self.property_map:
                    valor = self.property_map[name][7]
                    client_fields["valor_dia"].set(self._format_currency(valor))

            # --- SECCIÓN 3: FINANZAS (RESUMEN) ---
            sec1 = tk.LabelFrame(content_padding, text=" 👤 DATOS DEL HUÉSPED ", font=("Segoe UI", 10, "bold"), 
                                bg="white", fg="#2c3e50", padx=20, pady=20, relief=tk.FLAT, highlightbackground="#e0e0e0", highlightthickness=1)
            sec1.pack(fill=tk.X, pady=10)
            sec1.columnconfigure(1, weight=1)
            sec1.columnconfigure(3, weight=1)

            # Fila 0: ID y Búsqueda
            tk.Label(sec1, text="ID CLIENTE:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=8)
            id_f = tk.Frame(sec1, bg="white")
            id_f.grid(row=0, column=1, sticky=tk.EW, padx=10)
            ent_id = ttk.Entry(id_f, textvariable=client_fields["id_clientes"])
            ent_id.pack(side=tk.LEFT, fill=tk.X, expand=True)
            ent_id.bind("<Return>", lambda e: self.autofill_client_data(client_fields, parent=reservation_window))
            ttk.Button(id_f, text="🔍", width=3, command=lambda: self.open_client_search(client_fields, reservation_window)).pack(side=tk.RIGHT, padx=(5,0))

            tk.Label(sec1, text="DOCUMENTO (Obligatorio):", bg="white", font=("Segoe UI", 8, "bold"), fg="#e74c3c").grid(row=0, column=2, sticky=tk.W, padx=10)
            # Campo resaltado en ROJO (Obligatorio)
            ent_doc = tk.Entry(sec1, textvariable=client_fields["documento"], bg="#ffe6e6", fg="#c0392b", 
                              font=("Segoe UI", 9, "bold"), relief=tk.FLAT, highlightbackground="#f5b7b1", highlightthickness=1)

            ent_doc.grid(row=0, column=3, sticky=tk.EW)

            # Fila 1: Nombre y Apellido

            tk.Label(sec1, text="NOMBRE:", bg="white", font=("Segoe UI", 9)).grid(row=1, column=0, sticky=tk.W, pady=8)
            ttk.Entry(sec1, textvariable=client_fields["nombre"]).grid(row=1, column=1, sticky=tk.EW, padx=10)
            tk.Label(sec1, text="APELLIDO:", bg="white", font=("Segoe UI", 9)).grid(row=1, column=2, sticky=tk.W, padx=10)
            ttk.Entry(sec1, textvariable=client_fields["apellido"]).grid(row=1, column=3, sticky=tk.EW)

            # Fila 2: Email y Teléfono
            tk.Label(sec1, text="EMAIL:", bg="white", font=("Segoe UI", 9)).grid(row=2, column=0, sticky=tk.W, pady=8)
            ttk.Entry(sec1, textvariable=client_fields["email"]).grid(row=2, column=1, sticky=tk.EW, padx=10)
            tk.Label(sec1, text="TELÉFONO:", bg="white", font=("Segoe UI", 9)).grid(row=2, column=2, sticky=tk.W, padx=10)
            ttk.Entry(sec1, textvariable=client_fields["telefono"]).grid(row=2, column=3, sticky=tk.EW)

            # --- SECCIÓN 2: RESERVA Y VISTA PREVIA ---
            sec2 = tk.LabelFrame(content_padding, text=" 🏠 DETALLES DE ESTADÍA ", font=("Segoe UI", 10, "bold"), 
                                bg="white", fg="#2c3e50", padx=20, pady=20, relief=tk.FLAT, highlightbackground="#e0e0e0", highlightthickness=1)
            sec2.pack(fill=tk.X, pady=10)

            # Grid Principal de la sección (Izquierda: Form, Derecha: Card Inmueble)
            sec2.columnconfigure(0, weight=2)
            sec2.columnconfigure(1, weight=1)

            left_form = tk.Frame(sec2, bg="white")
            left_form.grid(row=0, column=0, sticky=tk.NSEW)
            left_form.columnconfigure(1, weight=1)

            # Inmueble
            tk.Label(left_form, text="INMUEBLE:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=10)
            cb_inm = ttk.Combobox(left_form, textvariable=client_fields["inmueble"], values=property_names, state="readonly")
            cb_inm.grid(row=0, column=1, sticky=tk.EW, padx=15)

            # Capacidad y Valor
            tk.Label(left_form, text="CAPACIDAD:", bg="white", font=("Segoe UI", 9)).grid(row=1, column=0, sticky=tk.W, pady=8)
            ttk.Entry(left_form, textvariable=client_fields["cantidad_personas"], width=10).grid(row=1, column=1, sticky=tk.W, padx=15)

            tk.Label(left_form, text="VALOR/DÍA:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky=tk.W, pady=8)
            val_e = ttk.Entry(left_form, textvariable=client_fields["valor_dia"], font=("Segoe UI", 10, "bold"))
            val_e.grid(row=2, column=1, sticky=tk.EW, padx=15)
            val_e.bind("<KeyRelease>", lambda e: self.format_discount_input(e, client_fields))

            # Fechas
            tk.Label(left_form, text="INGRESO:", bg="white", font=("Segoe UI", 9)).grid(row=3, column=0, sticky=tk.W, pady=8)
            f_in_f = tk.Frame(left_form, bg="white")
            f_in_f.grid(row=3, column=1, sticky=tk.EW, padx=15)
            ttk.Entry(f_in_f, textvariable=client_fields["fecha_ingreso"]).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Button(f_in_f, text="📅", width=3, command=lambda: self.select_date("fecha_ingreso", client_fields, reservation_window)).pack(side=tk.RIGHT, padx=(5,0))

            tk.Label(left_form, text="EGRESO:", bg="white", font=("Segoe UI", 9)).grid(row=4, column=0, sticky=tk.W, pady=8)
            f_out_f = tk.Frame(left_form, bg="white")
            f_out_f.grid(row=4, column=1, sticky=tk.EW, padx=15)
            ttk.Entry(f_out_f, textvariable=client_fields["fecha_egreso"]).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Button(f_out_f, text="📅", width=3, command=lambda: self.select_date("fecha_egreso", client_fields, reservation_window)).pack(side=tk.RIGHT, padx=(5,0))

            # Vista Previa Estilo Dashboard
            right_preview = tk.Frame(sec2, bg="#f8f9fa", bd=0, highlightbackground="#d1d8e0", highlightthickness=1)
            right_preview.grid(row=0, column=1, sticky=tk.NSEW, padx=(20, 0))

            prev_top = tk.Frame(right_preview, bg="#3498db", height=4)
            prev_top.pack(fill=tk.X)

            self.img_container = tk.Frame(right_preview, width=220, height=140, bg="#ecf0f1")
            self.img_container.pack_propagate(False)
            self.img_container.pack(pady=10, padx=10)

            self.inmueble_preview = tk.Label(self.img_container, text="SÍMBOLO INMUEBLE", fg="#bdc3c7", bg="#ecf0f1", font=("Segoe UI", 8, "italic"))
            self.inmueble_preview.pack(fill=tk.BOTH, expand=True)

            self.lbl_prev_info = tk.Label(right_preview, text="Seleccione un inmueble", font=("Segoe UI", 9), bg="#f8f9fa", fg="#7f8c8d")
            self.lbl_prev_info.pack(pady=5)

            def on_inmueble_select(event):
                selected = client_fields["inmueble"].get()
                if selected in self.property_map:
                    pd = self.property_map[selected]
                    client_fields["valor_dia"].set(self._format_currency(pd[7]))
                    client_fields["cantidad_personas"].set(str(pd[2]))
                    self.lbl_prev_info.config(text=f"{selected.upper()}\nCapacidad: {pd[2]} pers.", fg="#2c3e50", font=("Segoe UI", 9, "bold"))
                    self.update_cost_total(client_fields)
                    img_path = pd[8]
                    if img_path and os.path.exists(img_path):
                        try:
                            img = Image.open(img_path)
                            img.thumbnail((220, 140))
                            tk_img = ImageTk.PhotoImage(img)
                            self.inmueble_preview.config(image=tk_img, text="")
                            self.inmueble_preview.image = tk_img
                        except: self.inmueble_preview.config(image="", text="Error carga")
                    else: self.inmueble_preview.config(image="", text="Sin imagen")
            cb_inm.bind("<<ComboboxSelected>>", on_inmueble_select)

            # Si tenemos datos iniciales, actualizar el valor por día, imagen y recalcular
            if initial_data and "inmueble" in initial_data:
                name = initial_data["inmueble"]
                if name in self.property_map:
                    valor = self.property_map[name][7]
                    client_fields["valor_dia"].set(self._format_currency(valor))

                    # Cargar imagen y actualizar info de vista previa
                    img_path = initial_data.get("imagen")
                    if img_path and os.path.exists(img_path):
                        try:
                            img = Image.open(img_path)
                            img.thumbnail((220, 140))
                            tk_img = ImageTk.PhotoImage(img)
                            self.inmueble_preview.config(image=tk_img, text="")
                            self.inmueble_preview.image = tk_img
                            self.lbl_prev_info.config(text=f"{name.upper()}\nCapacidad: {initial_data.get('cantidad_personas')} pers.", fg="#2c3e50", font=("Segoe UI", 9, "bold"))
                        except: pass

                    self.update_cost_total(client_fields)

            # --- SECCIÓN 3: FINANZAS (RESUMEN) ---
            sec3 = tk.LabelFrame(content_padding, text=" 💰 RESUMEN FINANCIERO ", font=("Segoe UI", 10, "bold"), 
                                bg="white", fg="#2c3e50", padx=20, pady=20, relief=tk.FLAT, highlightbackground="#e0e0e0", highlightthickness=1)
            sec3.pack(fill=tk.X, pady=10)
            sec3.columnconfigure(1, weight=1)
            sec3.columnconfigure(3, weight=1)

            # Adelanto y Descuento
            tk.Label(sec3, text="ADELANTO (Opcional):", bg="white", font=("Segoe UI", 8, "bold"), fg="#27ae60").grid(row=0, column=0, sticky=tk.W, pady=8)
            # Campo resaltado en VERDE (Opcional)
            ent_ade = tk.Entry(sec3, textvariable=client_fields["adelanto"], bg="#e8f8f5", fg="#16a085",
                              font=("Segoe UI", 10, "bold"), relief=tk.FLAT, highlightbackground="#a3e4d7", highlightthickness=1)
            ent_ade.grid(row=0, column=1, sticky=tk.EW, padx=10)
            ent_ade.bind("<KeyRelease>", lambda e: self.format_down_payment_input(e, client_fields))

            tk.Label(sec3, text="DESCUENTO:", bg="white", font=("Segoe UI", 9)).grid(row=0, column=2, sticky=tk.W, padx=10)
            des_f = tk.Frame(sec3, bg="white")
            des_f.grid(row=0, column=3, sticky=tk.EW)
            ent_des = ttk.Entry(des_f, textvariable=client_fields["descuento"])
            ent_des.pack(side=tk.LEFT, fill=tk.X, expand=True)
            ent_des.bind("<KeyRelease>", lambda e: self.format_discount_input(e, client_fields))

            sym_l = tk.Label(des_f, text="$", bg="white", font=("Segoe UI", 10, "bold"), width=2)
            sym_l.pack(side=tk.RIGHT)
            ttk.Checkbutton(sec3, text="%", variable=client_fields["discount_is_percentage"], 
                            command=lambda: self._toggle_discount_symbol(sym_l, client_fields)).grid(row=0, column=4, padx=5)

            # Totales
            tk.Label(sec3, text="NOCHES:", bg="white", font=("Segoe UI", 9)).grid(row=1, column=0, sticky=tk.W, pady=15)
            tk.Label(sec3, textvariable=client_fields["noches"], bg="white", font=("Segoe UI", 11, "bold"), fg="#2980b9").grid(row=1, column=1, sticky=tk.W, padx=10)

            tk.Label(sec3, text="COSTO TOTAL:", bg="white", font=("Segoe UI", 9)).grid(row=1, column=2, sticky=tk.W, padx=10)
            tk.Label(sec3, textvariable=client_fields["costo_total"], bg="white", font=("Segoe UI", 11, "bold")).grid(row=1, column=3, sticky=tk.W)

            # Destacados
            tk.Label(sec3, text="A PAGAR FINAL:", bg="white", font=("Segoe UI", 10, "bold"), fg="#27ae60").grid(row=2, column=0, sticky=tk.W, pady=10)
            tk.Label(sec3, textvariable=client_fields["costo_con_descuento"], bg="white", font=("Segoe UI", 14, "bold"), fg="#27ae60").grid(row=2, column=1, sticky=tk.W, padx=10)

            tk.Label(sec3, text="SALDO PENDIENTE:", bg="white", font=("Segoe UI", 10, "bold"), fg="#e74c3c").grid(row=2, column=2, sticky=tk.W, padx=10)
            tk.Label(sec3, textvariable=client_fields["pago_pendiente"], bg="white", font=("Segoe UI", 16, "bold"), fg="#e74c3c").grid(row=2, column=3, sticky=tk.W)

            # --- BOTONES DE ACCIÓN (INFERIOR) ---
            btn_container = tk.Frame(reservation_window, bg="#f0f2f5", pady=20, padx=30)
            btn_container.pack(fill=tk.X)

            ttk.Button(btn_container, text="CANCELAR", command=reservation_window.destroy).pack(side=tk.LEFT)
            ttk.Button(btn_container, text="CONFIRMAR Y REGISTRAR RESERVA", style="ResAction.TButton", 
                    command=lambda: self.save_reservation(reservation_window, client_fields)).pack(side=tk.RIGHT)

        except Exception as e:
            messagebox.showerror("Error Crítico", f"Error al construir la ventana de reserva: {str(e)}")
            print(f"Error detallado en create_reservation: {e}")
            if 'reservation_window' in locals():
                reservation_window.destroy()

    def _toggle_discount_symbol(self, label, fields):
        if fields["discount_is_percentage"].get():
            label.config(text="%")
        else:
            label.config(text="$")
        fields["descuento"].set("")
        self.update_cost_total(fields)

    def select_date(self, field_name, client_fields, parent):
        def update_date_field(selected_date):
            client_fields[field_name].set(selected_date)
            self.update_cost_total(client_fields)

        id_inmueble = None
        nombre = client_fields["inmueble"].get()
        if nombre and hasattr(self, "property_map") and nombre in self.property_map:
            id_inmueble = self.property_map[nombre][0]

        # Lógica de apertura inteligente para "EGRESO"
        init_d = None
        high_d = None
        if field_name == "fecha_egreso":
            ingreso_str = client_fields["fecha_ingreso"].get()
            if ingreso_str:
                try:
                    init_d = datetime.strptime(ingreso_str, "%d/%m/%Y").date()
                    high_d = init_d
                except: pass

        ranges = self.db.get_reserved_ranges(id_inmueble=id_inmueble)
        CalendarDialog(parent, update_date_field, reserved_ranges=ranges, initial_date=init_d, highlight_date=high_d)

    def autofill_client_data(self, client_fields, parent=None):
        # Usar self.master si no se proporciona parent
        parent = parent or self.master

        # Obtener el ID del cliente ingresado
        client_id = client_fields["id_clientes"].get()
        
        if not client_id:
            return

        # Asegurar que la base de datos esté conectada
        if not self.db.connection or not self.db.connection.is_connected():
            if not self.db.connect():
                messagebox.showerror("Error", "No se pudo conectar a la base de datos", parent=parent)
                return

        # Buscar el cliente en la base de datos (primero clientes, luego prospectos)
        client_data = self.db.get_client_by_id(client_id)
        is_prospect = False
        
        if not client_data:
            client_data = self.db.get_prospect_by_id(client_id)
            if client_data:
                is_prospect = True

        if client_data:
            # Ambos tienen misma estructura básica: id, nombre, ape, email, tel, doc
            client_fields["nombre"].set(client_data[1])
            client_fields["apellido"].set(client_data[2])
            client_fields["email"].set(client_data[3])
            client_fields["telefono"].set(client_data[4])
            if len(client_data) > 5:
                client_fields["documento"].set(client_data[5] if client_data[5] else "")
            
            # Guardar si es prospecto para el momento del guardado
            client_fields["is_prospect"].set(is_prospect)
        else:
            messagebox.showerror("Error", "Contacto no encontrado en Clientes ni en Prospectos", parent=parent)

        # Recalcular costos después de autocompletar
        self.update_cost_total(client_fields)

    def update_cost_total(self, client_fields):
        # Obtener valores del formulario
        fecha_ingreso_str = client_fields["fecha_ingreso"].get()
        fecha_egreso_str = client_fields["fecha_egreso"].get()
        valor_dia_str = client_fields["valor_dia"].get()
        descuento_str = client_fields["descuento"].get()
        adelanto_str = client_fields["adelanto"].get()
        
        if not (fecha_ingreso_str and fecha_egreso_str and valor_dia_str):
            # Limpiar campos de costo si faltan datos básicos
            client_fields["noches"].set("")
            client_fields["costo_total"].set("$0,00")
            client_fields["costo_con_descuento"].set("$0,00")
            client_fields["pago_pendiente"].set("$0,00")
            # Actualizar resúmenes visuales
            client_fields["display_adelanto"].set("$0,00")
            client_fields["display_descuento"].set("$0,00")
            return

        try:
            # Convertir fechas a objetos date
            fecha_ingreso = datetime.strptime(fecha_ingreso_str, "%d/%m/%Y").date()
            fecha_egreso = datetime.strptime(fecha_egreso_str, "%d/%m/%Y").date()
            
            # Calcular número de noches
            delta = fecha_egreso - fecha_ingreso
            noches = delta.days
            
            # Convertir valor por día a número usando el nuevo parser
            valor_dia = self._parse_currency(valor_dia_str)
            
            # Calcular costo total
            costo_total = noches * valor_dia
            
            # Calcular costo con descuento si el campo no está vacío
            if descuento_str:
                if client_fields["discount_is_percentage"].get():
                    # Para el porcentaje, seguimos permitiendo el punto decimal
                    descuento_val = float(descuento_str.replace('%', '').strip())
                    descuento = costo_total * (descuento_val / 100.0)
                else:
                    descuento = self._parse_currency(descuento_str)
                costo_con_descuento = costo_total - descuento
            else:
                descuento = 0
                costo_con_descuento = costo_total
            
            # Calcular pago pendiente
            adelanto = self._parse_currency(adelanto_str)
            pago_pendiente = costo_con_descuento - adelanto
            
            # Actualizar campos con el nuevo formato
            client_fields["noches"].set(str(noches))
            client_fields["costo_total"].set(self._format_currency(costo_total))
            client_fields["costo_con_descuento"].set(self._format_currency(costo_con_descuento))
            client_fields["pago_pendiente"].set(self._format_currency(pago_pendiente))
            
            # *** ACTUALIZACIÓN DE RESUMEN VISUAL ***
            client_fields["display_adelanto"].set(self._format_currency(adelanto))
            client_fields["display_descuento"].set(self._format_currency(descuento))
            
        except Exception as e:
            # En caso de error, no mostrar mensaje molesto mientras se escribe, solo log
            print(f"Error en update_cost_total: {e}")
            client_fields["costo_total"].set("$0,00")
            client_fields["noches"].set("")
            client_fields["costo_con_descuento"].set("$0,00")
            client_fields["pago_pendiente"].set("$0,00")


    def save_reservation(self, reservation_window, client_fields):
        # Obtener valores del formulario
        fecha_ingreso_str = client_fields["fecha_ingreso"].get()
        fecha_egreso_str = client_fields["fecha_egreso"].get()
        valor_dia_str = client_fields["valor_dia"].get()
        descuento_str = client_fields["descuento"].get()
        adelanto_str = client_fields["adelanto"].get()
        noches_str = client_fields["noches"].get()
        
        # Validar campos obligatorios
        if not (fecha_ingreso_str and fecha_egreso_str and valor_dia_str and noches_str):
            messagebox.showerror("Error", "Por favor complete todos los campos obligatorios (Fechas, Valor por Día)", parent=reservation_window)
            return

        try:
            # Convertir fechas a objetos date
            fecha_ingreso = datetime.strptime(fecha_ingreso_str, "%d/%m/%Y").date()
            fecha_egreso = datetime.strptime(fecha_egreso_str, "%d/%m/%Y").date()
            
            # Calcular número de noches
            delta = fecha_egreso - fecha_ingreso
            noches = delta.days
            
            # Usar los parsers para obtener los valores reales
            valor_dia = self._parse_currency(valor_dia_str)
            costo_total = noches * valor_dia
            
            if descuento_str:
                if client_fields["discount_is_percentage"].get():
                    descuento_val = float(descuento_str.replace('%', '').strip())
                    descuento = costo_total * (descuento_val / 100.0)
                else:
                    descuento = self._parse_currency(descuento_str)
                costo_con_descuento = costo_total - descuento
            else:
                descuento = 0
                costo_con_descuento = costo_total
            
            adelanto = self._parse_currency(adelanto_str)
            pago_pendiente = costo_con_descuento - adelanto
            
            # Verificar si el cliente existe, si no, crearlo o convertirlo
            id_cliente = client_fields["id_clientes"].get()
            if not id_cliente:
                messagebox.showerror("Error", "Debe ingresar un ID de cliente", parent=reservation_window)
                return
            
            # Verificar si es un prospecto que debe ser convertido
            is_prospect = client_fields.get("is_prospect", tk.BooleanVar(value=False)).get()
            
            if is_prospect:
                # EXIGIR DNI PARA CREAR CLIENTE REAL
                documento = client_fields["documento"].get().strip()
                if not documento or documento == "S/D":
                    messagebox.showerror("DNI Requerido", "Para promover un prospecto a CLIENTE REAL debe ingresar un número de documento válido.", parent=reservation_window)
                    return

                # Preparar datos frescos del formulario para la conversión
                updated_prospect_data = (
                    documento,
                    client_fields["nombre"].get(),
                    client_fields["apellido"].get(),
                    client_fields["email"].get(),
                    client_fields["telefono"].get()
                )

                # Convertir prospecto a cliente real (usando datos actualizados del form)
                new_id, msg = self.db.convert_prospect_to_client(id_cliente, updated_data=updated_prospect_data)
                if new_id:
                    print(f"Prospecto {id_cliente} convertido a cliente {new_id}")
                    id_cliente = new_id
                    messagebox.showinfo("Lead Convertido", "El prospecto ha sido promovido a Cliente Real exitosamente.", parent=reservation_window)
                else:
                    messagebox.showerror("Error", f"No se pudo convertir el prospecto: {msg}", parent=reservation_window)
                    return
            else:
                existing_client = self.db.get_client_by_id(id_cliente)
                if not existing_client:
                    # Antes de crear uno nuevo, verificar si los datos (DNI/Email) ya existen en otro ID
                    nombre = client_fields["nombre"].get()
                    apellido = client_fields["apellido"].get()
                    documento = client_fields["documento"].get()
                    email = client_fields["email"].get()
                    
                    if not (nombre and apellido and documento):
                        messagebox.showerror("Error", "Para crear un nuevo cliente debe ingresar al menos Nombre, Apellido y Documento", parent=reservation_window)
                        return
                    
                    # Verificar si ya existe ese DNI o Email en otro cliente
                    existing, tipo = self.db.get_contact_by_email_or_dni(email, documento)
                    if existing and tipo == 'cliente':
                        msg = f"No se puede crear el cliente. El DNI o Email ya pertenecen al Cliente ID #{existing[0]} ({existing[2]} {existing[3]}).\n\nPor favor, use el buscador (🔍) para seleccionar al cliente correcto."
                        messagebox.showwarning("Cliente Duplicado", msg, parent=reservation_window)
                        return

                    new_client_data = (
                        int(id_cliente),
                        documento,
                        nombre,
                        apellido,
                        email,
                        client_fields["telefono"].get()
                    )
                    if self.db.insert_client(new_client_data):
                        messagebox.showinfo("Nuevo Cliente", f"Se ha creado automáticamente el nuevo cliente: {nombre} {apellido} (ID: {id_cliente})", parent=reservation_window)
                    else:
                        messagebox.showerror("Error", "No se pudo crear el nuevo cliente. Verifique que los datos no estén duplicados.", parent=reservation_window)
                        return

            inmueble_nombre = client_fields["inmueble"].get()
            prop_data = self.property_map.get(inmueble_nombre)
            id_inmueble = prop_data[0] if prop_data else None

            if not id_cliente or not id_inmueble:
                messagebox.showerror("Error", "Debe seleccionar un cliente y un inmueble", parent=reservation_window)
                return

            reservation_data = {
                "id_cliente": int(id_cliente),
                "id_inmueble": id_inmueble,
                "fecha_ingreso": fecha_ingreso,
                "fecha_egreso": fecha_egreso,
                "valor_dia": valor_dia,
                "noches": noches,
                "costo_total": costo_total,
                "costo_con_descuento": costo_con_descuento,
                "adelanto": adelanto,
                "pago_pendiente": pago_pendiente,
                "provincia": client_fields["provincia"].get()
            }
            
            reservation_id = self.db.insert_reservation(reservation_data)

            # Si la reserva proviene de una cotización, eliminar la cotización
            q_id = client_fields.get("quotation_id", tk.StringVar()).get()
            if q_id:
                self.db.delete_quotation(q_id)

            # Obtener servicios para el email
            servicios_raw = self.db.get_property_services(id_inmueble)
            servicios_str = ", ".join([f"{s[0]} {s[1]}" for s in servicios_raw]) if servicios_raw else "No especificados"
            
            client_email = client_fields["email"].get()
            client_name = f"{client_fields['nombre'].get()} {client_fields['apellido'].get()}"
            email_data = {
                "id_reserva": reservation_id,
                "inmueble": inmueble_nombre,
                "ubicacion": prop_data[4] if prop_data else "Consultar",
                "servicios": servicios_str,
                "fecha_ingreso": fecha_ingreso.strftime("%d/%m/%Y"),
                "fecha_egreso": fecha_egreso.strftime("%d/%m/%Y"),
                "noches": noches,
                "valor_dia": valor_dia,
                "costo_total": costo_total,
                "costo_con_descuento": costo_con_descuento,
                "adelanto": adelanto,
                "pago_pendiente": pago_pendiente,
                "dormitorios": prop_data[9] if prop_data and len(prop_data) > 9 else 0,
                "camas": prop_data[10] if prop_data and len(prop_data) > 10 else 0,
                "baños": prop_data[11] if prop_data and len(prop_data) > 11 else 0,
            }
            send_reservation_email(client_email, client_name, email_data)
            
            # Mostrar mensaje de éxito
            messagebox.showinfo("Éxito", "Reserva guardada correctamente", parent=reservation_window)
            reservation_window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar reserva: {str(e)}", parent=reservation_window)
