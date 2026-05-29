import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime

from controllers.database import Database
from controllers.reservation_controller import CalendarDialog
from ui.payment_window import PaymentWindow


class EditReservationWindow:
    def __init__(self, master, reservation_id, refresh_callback):
        self.master = master
        self.reservation_id = reservation_id
        self.refresh_callback = refresh_callback
        self.db = Database()
        self.db.connect()
        self.meses = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
                      "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

        self.window = tk.Toplevel(master)
        self.window.title("Modificar Reserva")
        self.window.geometry("600x650")
        self.window.configure(bg="#f8f9fa")
        self.window.transient(master)

        raw = self.db.get_reservation_by_id(reservation_id)
        if not raw:
            messagebox.showerror("Error", "No se encontró la reserva", parent=self.window)
            self.window.destroy()
            return

        # self.original mapping...
        self.original = {
            "id_cliente": raw[0],
            "id_inmueble": raw[1],
            "fecha_ingreso": raw[2],
            "fecha_egreso": raw[3],
            "valor_dia": float(raw[4]),
            "noches": int(raw[5]),
            "costo_total": float(raw[6]),
            "costo_con_descuento": float(raw[7]),
            "adelanto": float(raw[8]),
            "pago_pendiente": float(raw[9]),
            "provincia": raw[10],
        }
        self.descuento_amount = self.original["costo_total"] - self.original["costo_con_descuento"]

        # Cargar inmuebles
        properties = self.db.get_all_properties()
        self.property_map = {p[1]: p for p in properties}
        property_names = list(self.property_map.keys())
        current_property_name = None
        for name, p in self.property_map.items():
            if p[0] == self.original["id_inmueble"]:
                current_property_name = name
                break

        self.fields = {}
        
        # Estilos locales
        style = ttk.Style(self.window)
        style.configure("EditHeader.TLabel", font=("Segoe UI", 14, "bold"), foreground="#2c3e50")
        style.configure("EditSection.TLabelframe", font=("Segoe UI", 10, "bold"))
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=10)

        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text=f"Modificando Reserva #{reservation_id}", style="EditHeader.TLabel").pack(pady=(0, 20))

        # ─── SECCIÓN: DATOS GENERALES ────────────────────────────
        sec_gen = ttk.LabelFrame(main_frame, text=" Información General ", padding=15, style="EditSection.TLabelframe")
        sec_gen.pack(fill=tk.X, pady=10)
        sec_gen.columnconfigure(1, weight=1)

        ttk.Label(sec_gen, text="Cliente ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(sec_gen, text=str(self.original["id_cliente"]), font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky=tk.W, padx=10)

        ttk.Label(sec_gen, text="Inmueble:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.fields["inmueble"] = tk.StringVar(value=current_property_name or "")
        combo_inmueble = ttk.Combobox(sec_gen, textvariable=self.fields["inmueble"], values=property_names, state="readonly")
        combo_inmueble.grid(row=1, column=1, sticky=tk.EW, padx=10)
        combo_inmueble.bind("<<ComboboxSelected>>", self._on_inmueble_change)

        # Fila: Valor por Día (solo lectura)
        row = ttk.Frame(sec_gen)
        row.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        ttk.Label(row, text="Valor por Día:").pack(side=tk.LEFT)
        self.var_valor_dia = tk.StringVar(value=self._format_currency(self.original['valor_dia']))
        ttk.Label(row, textvariable=self.var_valor_dia, font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=10)

        # ─── SECCIÓN: FECHAS ────────────────────────────
        sec_date = ttk.LabelFrame(main_frame, text=" Estadía ", padding=15, style="EditSection.TLabelframe")
        sec_date.pack(fill=tk.X, pady=10)
        sec_date.columnconfigure(1, weight=1)

        ttk.Label(sec_date, text="Fecha Ingreso:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.fields["fecha_ingreso"] = tk.StringVar(value=self._fmt_date(self.original["fecha_ingreso"]))
        fi_f = ttk.Frame(sec_date)
        fi_f.grid(row=0, column=1, sticky=tk.EW, padx=10)
        ttk.Entry(fi_f, textvariable=self.fields["fecha_ingreso"]).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(fi_f, text="📅", width=3, command=lambda: self._pick_date("fecha_ingreso")).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Label(sec_date, text="Fecha Egreso:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.fields["fecha_egreso"] = tk.StringVar(value=self._fmt_date(self.original["fecha_egreso"]))
        fe_f = ttk.Frame(sec_date)
        fe_f.grid(row=1, column=1, sticky=tk.EW, padx=10)
        ttk.Entry(fe_f, textvariable=self.fields["fecha_egreso"]).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(fe_f, text="📅", width=3, command=lambda: self._pick_date("fecha_egreso")).pack(side=tk.RIGHT, padx=(5, 0))

        # ─── SECCIÓN: RESUMEN FINANCIERO ────────────────────────────
        sec_fin = ttk.LabelFrame(main_frame, text=" Resumen Financiero ", padding=15, style="EditSection.TLabelframe")
        sec_fin.pack(fill=tk.X, pady=10)
        sec_fin.columnconfigure(1, weight=1)
        sec_fin.columnconfigure(3, weight=1)

        ttk.Label(sec_fin, text="Noches:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.fields["noches"] = tk.StringVar()
        ttk.Label(sec_fin, textvariable=self.fields["noches"], font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky=tk.W, padx=10)

        ttk.Label(sec_fin, text="Costo Total:").grid(row=0, column=2, sticky=tk.W, pady=5)
        self.fields["costo_total"] = tk.StringVar()
        ttk.Label(sec_fin, textvariable=self.fields["costo_total"]).grid(row=0, column=3, sticky=tk.W, padx=10)

        ttk.Label(sec_fin, text="Con Descuento:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.fields["costo_con_descuento"] = tk.StringVar()
        ttk.Label(sec_fin, textvariable=self.fields["costo_con_descuento"], foreground="#27ae60", font=("Segoe UI", 10, "bold")).grid(row=1, column=1, sticky=tk.W, padx=10)

        ttk.Label(sec_fin, text="Pago Pendiente:").grid(row=1, column=2, sticky=tk.W, pady=5)
        self.fields["pago_pendiente"] = tk.StringVar()
        ttk.Label(sec_fin, textvariable=self.fields["pago_pendiente"], foreground="#e74c3c", font=("Segoe UI", 10, "bold")).grid(row=1, column=3, sticky=tk.W, padx=10)

        # Bindings
        self.fields["fecha_ingreso"].trace_add("write", lambda *_: self.recalculate())
        self.fields["fecha_egreso"].trace_add("write", lambda *_: self.recalculate())

        self.recalculate()

        # Botones
        btn_frame = ttk.Frame(main_frame, padding=(0, 20, 0, 0))
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Cancelar", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Guardar Cambios", style="Action.TButton", command=self.save).pack(side=tk.RIGHT, padx=5)

    def _fmt_date(self, d):
        if isinstance(d, str):
            d = datetime.strptime(d, "%Y-%m-%d").date()
        return f"{d.day} {self.meses[d.month]} {d.year}"

    def _parse_date(self, s):
        parts = s.strip().split()
        dia, mes_str, anio = int(parts[0]), parts[1].lower(), int(parts[2])
        meses_inv = {m: i for i, m in enumerate(self.meses)}
        return date(anio, meses_inv[mes_str], dia)

    def _pick_date(self, field_name):
        def callback(date_str):
            d = datetime.strptime(date_str, "%d/%m/%Y").date()
            self.fields[field_name].set(self._fmt_date(d))

        id_inmueble = self._get_id_inmueble()
        
        # Lógica de apertura inteligente
        init_d = None
        high_d = None
        if field_name == "fecha_fin":
            ingreso_str = self.fields["fecha_inicio"].get()
            if ingreso_str:
                try:
                    init_d = self._parse_date(ingreso_str)
                    high_d = init_d
                except: pass

        ranges = self.db.get_reserved_ranges(id_inmueble=id_inmueble, exclude_id=self.reservation_id)
        CalendarDialog(self.window, callback, reserved_ranges=ranges, initial_date=init_d, highlight_date=high_d)

    def _get_valor_dia(self):
        name = self.fields["inmueble"].get()
        if name in self.property_map:
            return float(self.property_map[name][7])
        return self.original["valor_dia"]

    def _get_id_inmueble(self):
        name = self.fields["inmueble"].get()
        if name in self.property_map:
            return self.property_map[name][0]
        return self.original["id_inmueble"]

    def _format_currency(self, value):
        """Formatea un valor numérico como moneda ($1.234,56)."""
        try:
            if isinstance(value, str):
                value = value.replace('$', '').replace('.', '').replace(',', '.')
                value = float(value)
            formatted = f"{value:,.2f}"
            main_part, decimal_part = formatted.split('.')
            main_part = main_part.replace(',', '.')
            return f"${main_part},{decimal_part}"
        except (ValueError, TypeError):
            return "$0,00"

    def _on_inmueble_change(self, event=None):
        valor = self._get_valor_dia()
        self.var_valor_dia.set(self._format_currency(valor))
        self.recalculate()

    def recalculate(self):
        try:
            ingreso = self._parse_date(self.fields["fecha_ingreso"].get())
            egreso = self._parse_date(self.fields["fecha_egreso"].get())
            noches = (egreso - ingreso).days
            if noches < 0:
                noches = 0
            valor_dia = self._get_valor_dia()
            costo_total = noches * valor_dia
            costo_con_desc = max(costo_total - self.descuento_amount, 0)
            pago_pendiente = costo_con_desc - self.original["adelanto"]

            self.fields["noches"].set(str(noches))
            self.fields["costo_total"].set(self._format_currency(costo_total))
            self.fields["costo_con_descuento"].set(self._format_currency(costo_con_desc))
            self.fields["pago_pendiente"].set(self._format_currency(pago_pendiente))
        except Exception:
            pass

    def save(self):
        try:
            ingreso = self._parse_date(self.fields["fecha_ingreso"].get())
            egreso = self._parse_date(self.fields["fecha_egreso"].get())
            noches = (egreso - ingreso).days
            if noches <= 0:
                messagebox.showerror("Error", "La fecha de egreso debe ser posterior a la de ingreso", parent=self.window)
                return
            valor_dia = self._get_valor_dia()
            costo_total = noches * valor_dia
            costo_con_desc = max(costo_total - self.descuento_amount, 0)
            pago_pendiente = costo_con_desc - self.original["adelanto"]

            data = {
                "id_cliente": self.original["id_cliente"],
                "id_inmueble": self._get_id_inmueble(),
                "fecha_ingreso": ingreso.isoformat(),
                "fecha_egreso": egreso.isoformat(),
                "valor_dia": valor_dia,
                "noches": noches,
                "costo_total": costo_total,
                "costo_con_descuento": costo_con_desc,
                "adelanto": self.original["adelanto"],
                "pago_pendiente": pago_pendiente,
                "provincia": self.original["provincia"],
            }
            if self.db.update_reservation(self.reservation_id, data):
                messagebox.showinfo("Éxito", "Reserva actualizada correctamente", parent=self.window)
                self.window.destroy()
                self.refresh_callback()
            else:
                messagebox.showerror("Error", "No se pudo actualizar la reserva", parent=self.window)
        except Exception as e:
            messagebox.showerror("Error", f"Datos inválidos: {e}", parent=self.window)


class ReservationListWindow:
    def __init__(self, master, reservation_controller):
        self.master = master
        self.controller = reservation_controller
        self.db = Database()
        self.db.connect()
        self.cards = []
        self.selected_id = None

        self.window = tk.Toplevel(master)
        self.window.title("Historial de Reservas")
        self.window.geometry("1150x850")
        self.window.configure(bg="#f0f2f5")

        # Estilos locales
        style = ttk.Style(self.window)
        style.configure("Res.TFrame", background="#f0f2f5")
        style.configure("ResAction.TButton", font=("Segoe UI", 10, "bold"), padding=12)

        # --- ENCABEZADO ---
        header_frame = tk.Frame(self.window, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="📅 GESTIÓN DE RESERVAS", font=("Segoe UI", 16, "bold"), 
                 bg="#2c3e50", fg="#ecf0f1").pack(side=tk.LEFT, padx=30, pady=20)
        
        self.lbl_stats = tk.Label(header_frame, text="Cargando...", font=("Segoe UI", 10), 
                                 bg="#2c3e50", fg="#95a5a6")
        self.lbl_stats.pack(side=tk.RIGHT, padx=30)

        main_container = ttk.Frame(self.window, padding=30, style="Res.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True)

        # --- BARRA DE BÚSQUEDA ---
        search_card = tk.Frame(main_container, bg="white", highlightbackground="#e0e0e0", highlightthickness=1, padx=20, pady=15)
        search_card.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(search_card, text="🔎 BUSCAR RESERVA:", font=("Segoe UI", 9, "bold"), bg="white", fg="#2c3e50").pack(side=tk.LEFT, padx=(0, 15))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_card, textvariable=self.search_var, font=("Segoe UI", 11))
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_entry.bind("<KeyRelease>", lambda e: self.filter_cards())

        ttk.Button(search_card, text="🔄 REFRESCAR", command=self.load_reservations).pack(side=tk.RIGHT, padx=(15, 0))

        # --- LISTADO (SCROLL) ---
        canvas_frame = ttk.Frame(main_container, style="Res.TFrame")
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="#f0f2f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable = tk.Frame(self.canvas, bg="#f0f2f5")

        self.scrollable.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable, anchor="nw", width=1070)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- ACCIONES ---
        btn_frame = ttk.Frame(main_container, style="Res.TFrame")
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(btn_frame, text="🗑️ ELIMINAR SELECCIONADA", command=self.delete_reservation).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="💳 VER PAGOS / ABONAR", command=self.open_payment_window).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="✏️ MODIFICAR DETALLES", style="ResAction.TButton", command=self.modify_reservation).pack(side=tk.RIGHT)

        self.load_reservations()

    def bind_select(self, widget, res_id):
        widget.bind("<Button-1>", lambda e, i=res_id: self.select_card(i))
        for child in widget.winfo_children():
            self.bind_select(child, res_id)

    def create_card(self, row):
        # row mapping from get_all_reservations:
        # 0:id, 1:cliente_nombre, 2:telefono, 3:inmueble_nombre, 4:f_ing, 5:f_eg, 
        # 6:noches, 7:val_d, 8:total, 9:final, 10:adelanto, 11:pendiente, 12:provincia
        res_id = row[0]
        res_code = f"R-{str(res_id).zfill(5)}"
        client_name = row[1]
        phone = row[2]
        property_name = row[3]
        
        meses = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
                 "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

        def fmt_d(d):
            try:
                dt = datetime.strptime(str(d), "%Y-%m-%d")
                return f"{dt.day} {meses[dt.month]} {dt.year}"
            except: return str(d)

        card = tk.Frame(self.scrollable, bg="white", bd=0, highlightbackground="#d1d8e0", highlightthickness=1)
        card.pack(fill=tk.X, padx=5, pady=8)
        self.bind_select(card, res_id)

        inner = tk.Frame(card, bg="white", padx=15, pady=15)
        inner.pack(fill=tk.X)
        self.bind_select(inner, res_id)

        # Izquierda: Código e Info Cliente
        info_f = tk.Frame(inner, bg="white")
        info_f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.bind_select(info_f, res_id)

        code_f = tk.Frame(info_f, bg="#e8f8f5", padx=8, pady=2)
        code_f.pack(anchor="w")
        tk.Label(code_f, text=res_code, font=("Segoe UI", 10, "bold"), bg="#e8f8f5", fg="#16a085").pack()
        
        tk.Label(info_f, text=client_name.upper(), font=("Segoe UI", 13, "bold"), bg="white", fg="#2c3e50").pack(anchor="w", pady=(5,0))
        tk.Label(info_f, text=f"📞 {phone} | 📍 {row[12]}", font=("Segoe UI", 9), bg="white", fg="#7f8c8d").pack(anchor="w")
        tk.Label(info_f, text=f"🏠 {property_name}", font=("Segoe UI", 11, "bold"), bg="white", fg="#34495e").pack(anchor="w", pady=(5,0))

        # Centro: Estadía
        stay_f = tk.Frame(inner, bg="white", padx=20)
        stay_f.pack(side=tk.LEFT, fill=tk.Y)
        self.bind_select(stay_f, res_id)

        tk.Label(stay_f, text="ESTADÍA", font=("Segoe UI", 8, "bold"), bg="white", fg="#bdc3c7").pack(anchor="w")
        tk.Label(stay_f, text=f"Desde: {fmt_d(row[4])}", font=("Segoe UI", 10), bg="white", fg="#2c3e50").pack(anchor="w")
        tk.Label(stay_f, text=f"Hasta: {fmt_d(row[5])}", font=("Segoe UI", 10), bg="white", fg="#2c3e50").pack(anchor="w")
        tk.Label(stay_f, text=f"({row[6]} noches)", font=("Segoe UI", 9, "italic"), bg="white", fg="#95a5a6").pack(anchor="w")

        # Derecha: Resumen Financiero
        fin_f = tk.Frame(inner, bg="white", padx=10)
        fin_f.pack(side=tk.RIGHT, fill=tk.Y)
        self.bind_select(fin_f, res_id)

        pending = float(row[11])
        status_color = "#e74c3c" if pending > 0 else "#27ae60"
        status_text = "SALDO PENDIENTE" if pending > 0 else "TOTALMENTE PAGO"

        tk.Label(fin_f, text=status_text, font=("Segoe UI", 8, "bold"), bg="white", fg=status_color).pack(anchor="e")
        tk.Label(fin_f, text=self._format_currency(pending), font=("Segoe UI", 16, "bold"), bg="white", fg=status_color).pack(anchor="e")
        
        tk.Label(fin_f, text=f"Total: {self._format_currency(row[9])}", font=("Segoe UI", 9), bg="white", fg="#7f8c8d").pack(anchor="e", pady=(5,0))
        tk.Label(fin_f, text=f"Adelanto: {self._format_currency(row[10])}", font=("Segoe UI", 9), bg="white", fg="#2980b9").pack(anchor="e")

        card.res_id = res_id
        card.search_data = f"{res_code} {client_name} {property_name} {phone}".lower()
        self.cards.append(card)

    def select_card(self, res_id):
        self.selected_id = res_id
        for c in self.cards:
            is_sel = c.res_id == res_id
            c.configure(highlightbackground="#3498db" if is_sel else "#d1d8e0", highlightthickness=2 if is_sel else 1)
            bg_color = "#f1f9ff" if is_sel else "white"
            self._update_bg_recursive(c, bg_color)

    def _update_bg_recursive(self, widget, color):
        try:
            current_bg = str(widget.cget("background"))
            if "e8f8f5" not in current_bg:
                widget.configure(bg=color)
        except: pass
        for child in widget.winfo_children():
            self._update_bg_recursive(child, color)

    def load_reservations(self):
        for w in self.scrollable.winfo_children(): w.destroy()
        self.cards = []
        self.selected_id = None
        self.search_var.set("")
        
        if self.db.connect():
            rows = self.db.get_all_reservations()
            total_pending = 0.0
            for row in rows:
                self.create_card(row)
                total_pending += float(row[11])
            
            self.lbl_stats.config(text=f"TOTAL: {len(rows)} RESERVAS | PENDIENTE: {self._format_currency(total_pending)}")
            self.filter_cards()

    def filter_cards(self):
        query = self.search_var.get().lower()
        visible_count = 0
        for card in self.cards:
            if query in card.search_data:
                card.pack(fill=tk.X, padx=5, pady=8)
                visible_count += 1
            else:
                card.pack_forget()
        self.lbl_stats.config(text=f"MOSTRANDO: {visible_count} RESULTADOS")

    def _format_currency(self, value):
        try:
            val = float(value)
            formatted = f"{val:,.2f}"
            m, d = formatted.split('.')
            return f"${m.replace(',', '.')},{d}"
        except: return str(value)

    def open_payment_window(self):
        if not self.selected_id:
            messagebox.showwarning("Advertencia", "Seleccione una reserva.")
            return
        
        row = next((r for r in self.db.get_all_reservations() if r[0] == self.selected_id), None)
        if row:
            PaymentWindow(self.window, self.selected_id, row[1], float(row[11]), self.load_reservations)

    def delete_reservation(self):
        if not self.selected_id:
            messagebox.showwarning("Advertencia", "Seleccione una reserva.")
            return
        
        res_code = f"R-{str(self.selected_id).zfill(5)}"
        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar la reserva {res_code}?", parent=self.window):
            if self.db.delete_reservation(self.selected_id):
                messagebox.showinfo("Éxito", "Reserva eliminada correctamente", parent=self.window)
                self.load_reservations()

    def modify_reservation(self):
        if not self.selected_id:
            messagebox.showwarning("Advertencia", "Seleccione una reserva.")
            return
        EditReservationWindow(self.master, self.selected_id, self.load_reservations)
