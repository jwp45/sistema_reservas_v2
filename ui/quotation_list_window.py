import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from controllers.database import Database

class QuotationListWindow:
    def __init__(self, master, reservation_controller, show_at_risk=False):
        self.master = master
        self.controller = reservation_controller
        self.db = Database()
        if not self.db.connect():
            messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
            return

        self.cards = []
        self.selected_id = None

        self.window = tk.Toplevel(master)
        self.window.title("Historial de Cotizaciones Enviadas")
        self.window.geometry("1100x800")
        self.window.configure(bg="#f0f2f5")
        self.window.transient(master)
        
        # Esperar a que la ventana sea visible antes de hacer el grab_set
        self.window.wait_visibility()
        self.window.grab_set()

        # --- ESTILOS LOCALES ---
        style = ttk.Style(self.window)
        style.configure("Quot.TFrame", background="#f0f2f5")
        style.configure("QuotAction.TButton", font=("Segoe UI", 10, "bold"), padding=12)
        style.configure("Risk.TCheckbutton", font=("Segoe UI", 10, "bold"), background="white")

        # --- ENCABEZADO ---
        header_frame = tk.Frame(self.window, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="📑 HISTORIAL DE COTIZACIONES", font=("Segoe UI", 16, "bold"), 
                 bg="#2c3e50", fg="#ecf0f1").pack(side=tk.LEFT, padx=30, pady=20)

        self.lbl_stats = tk.Label(header_frame, text="Cargando...", font=("Segoe UI", 10), 
                                 bg="#2c3e50", fg="#95a5a6")
        self.lbl_stats.pack(side=tk.RIGHT, padx=30)

        main_container = ttk.Frame(self.window, padding=30, style="Quot.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True)

        # --- BARRA DE BÚSQUEDA Y FILTROS ---
        search_card = tk.Frame(main_container, bg="white", highlightbackground="#e0e0e0", highlightthickness=1, padx=20, pady=15)
        search_card.pack(fill=tk.X, pady=(0, 20))
        
        # Búsqueda Texto
        search_sub = tk.Frame(search_card, bg="white")
        search_sub.pack(fill=tk.X)
        
        tk.Label(search_sub, text="🔎 BUSCAR:", font=("Segoe UI", 9, "bold"), bg="white", fg="#2c3e50").pack(side=tk.LEFT, padx=(0, 10))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_sub, textvariable=self.search_var, font=("Segoe UI", 11))
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_entry.bind("<KeyRelease>", lambda e: self.filter_cards())

        # Filtro At Risk (Inicializar con show_at_risk)
        self.risk_var = tk.BooleanVar(value=show_at_risk)
        tk.Checkbutton(search_sub, text="⚠️ SOLO EN RIESGO (< 3 DÍAS)", variable=self.risk_var, 
                       command=self.filter_cards, bg="white", activebackground="white", 
                       font=("Segoe UI", 9, "bold"), fg="#e67e22").pack(side=tk.LEFT, padx=15)

        ttk.Button(search_sub, text="🔄 REFRESCAR", command=self.load_quotations).pack(side=tk.RIGHT)

        # --- LISTADO (SCROLL) ---
        canvas_frame = ttk.Frame(main_container, style="Quot.TFrame")
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="#f0f2f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable = tk.Frame(self.canvas, bg="#f0f2f5")

        self.scrollable.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable, anchor="nw", width=1020)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- BARRA DE ACCIONES ---
        btn_frame = ttk.Frame(main_container, style="Quot.TFrame")
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(btn_frame, text="🗑️ ELIMINAR SELECCIONADA", command=self.delete_quotation).pack(side=tk.LEFT)
        
        self.btn_batch = tk.Button(btn_frame, text="🎁 RE-OFERTAR TODOS EN RIESGO (5%)", font=("Segoe UI", 10, "bold"), 
                                   bg="#27ae60", fg="white", relief=tk.FLAT, padx=20, pady=8, cursor="hand2",
                                   command=self.reoffer_all_at_risk)
        # Se packea inicialmente si el filtro está activo, si no, filter_cards lo manejará
        self.btn_batch.pack(side=tk.LEFT, padx=20)

        ttk.Button(btn_frame, text="🚀 CONVERTIR EN RESERVA", style="QuotAction.TButton", 
                   command=self.convert_to_reservation).pack(side=tk.RIGHT)

        # Cargar datos al final
        self.window.after(100, self.load_quotations)

    def bind_select(self, widget, quot_id):
        widget.bind("<Button-1>", lambda e, i=quot_id: self.select_card(i))
        for child in widget.winfo_children():
            self.bind_select(child, quot_id)

    def create_card(self, q):
        # q = (0:id, 1:cliente, 2:inmueble, 3:f_ing, 4:f_eg, 5:noches, 6:final, 7:f_cot, 
        #      8:id_contacto, 9:id_inmueble, 10:val_d, 11:total, 12:desc, 13:capacidad, 14:mkt_enviado, 15:tipo_contacto)
        quot_id = q[0]
        quot_code = f"Q-{str(quot_id).zfill(5)}"
        client_name = q[1]
        property_name = q[2]
        tipo_contacto = q[15]
        now = datetime.now()

        # Calcular Vigencia
        f_cot_raw = q[7]
        vigencia_text = "Expirado"
        vigencia_color = "#e74c3c"
        if isinstance(f_cot_raw, datetime):
            expiracion = f_cot_raw + timedelta(days=15)
            restante = expiracion - now
            if restante.total_seconds() > 0:
                dias = restante.days
                horas = restante.seconds // 3600
                vigencia_text = f"Quedan: {dias}d {horas}h" if dias > 0 else f"Quedan: {horas}h"
                vigencia_color = "#f39c12" if dias < 3 else "#27ae60"

        card = tk.Frame(self.scrollable, bg="white", bd=0, highlightbackground="#d1d8e0", highlightthickness=1)
        card.pack(fill=tk.X, padx=5, pady=8)
        self.bind_select(card, quot_id)
        
        inner = tk.Frame(card, bg="white", padx=15, pady=15)
        inner.pack(fill=tk.X)
        self.bind_select(inner, quot_id)

        # Izquierda: Código e Info Principal
        info_f = tk.Frame(inner, bg="white")
        info_f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.bind_select(info_f, quot_id)

        # Header con código y tipo de cliente
        header_f = tk.Frame(info_f, bg="white")
        header_f.pack(anchor="w")
        
        code_f = tk.Frame(header_f, bg="#ebf5fb", padx=8, pady=2)
        code_f.pack(side=tk.LEFT)
        tk.Label(code_f, text=quot_code, font=("Segoe UI", 10, "bold"), bg="#ebf5fb", fg="#2980b9").pack()
        
        # Badge de tipo
        tipo_bg = "#fef9e7" if tipo_contacto == "prospecto" else "#e8f8f5"
        tipo_fg = "#f39c12" if tipo_contacto == "prospecto" else "#16a085"
        tipo_text = "PROSPECTO" if tipo_contacto == "prospecto" else "CLIENTE VIP"
        
        badge_f = tk.Frame(header_f, bg=tipo_bg, padx=6, pady=2)
        badge_f.pack(side=tk.LEFT, padx=10)
        tk.Label(badge_f, text=tipo_text, font=("Segoe UI", 8, "bold"), bg=tipo_bg, fg=tipo_fg).pack()
        
        tk.Label(info_f, text=client_name.upper(), font=("Segoe UI", 13, "bold"), bg="white", fg="#2c3e50").pack(anchor="w", pady=(5,0))
        tk.Label(info_f, text=f"🏠 {property_name}", font=("Segoe UI", 11), bg="white", fg="#34495e").pack(anchor="w")
        
        f_ing_str = q[3].strftime('%d/%m/%Y') if hasattr(q[3], 'strftime') else str(q[3])
        f_eg_str = q[4].strftime('%d/%m/%Y') if hasattr(q[4], 'strftime') else str(q[4])
        details_text = f"📅 {f_ing_str} al {f_eg_str} ({q[5]} noches)"
        tk.Label(info_f, text=details_text, font=("Segoe UI", 9), bg="white", fg="#7f8c8d").pack(anchor="w", pady=5)

        # Centro: Vigencia y Fecha Cotización
        time_f = tk.Frame(inner, bg="white", padx=20)
        time_f.pack(side=tk.LEFT, fill=tk.Y)
        self.bind_select(time_f, quot_id)

        tk.Label(time_f, text="VIGENCIA", font=("Segoe UI", 8, "bold"), bg="white", fg="#bdc3c7").pack(anchor="w")
        tk.Label(time_f, text=vigencia_text, font=("Segoe UI", 10, "bold"), bg="white", fg=vigencia_color).pack(anchor="w")
        
        f_cot_str = q[7].strftime("%d/%m/%Y %H:%M") if hasattr(q[7], 'strftime') else str(q[7])
        tk.Label(time_f, text=f"Enviada: {f_cot_str}", font=("Segoe UI", 8), bg="white", fg="#95a5a6").pack(anchor="w", pady=(5,0))

        # Derecha: Precios y Marketing
        price_f = tk.Frame(inner, bg="white", padx=10)
        price_f.pack(side=tk.RIGHT, fill=tk.Y)
        self.bind_select(price_f, quot_id)

        # Verificar disponibilidad y si ya fue enviada
        is_free = self.db.is_range_available(q[9], q[3], q[4])
        mkt_enviado = q[14]
        
        is_at_risk = False
        if isinstance(f_cot_raw, datetime):
            expiracion = f_cot_raw + timedelta(days=15)
            restante = expiracion - now
            is_at_risk = restante.total_seconds() > 0 and restante.days < 3

        try:
            precio_orig = float(q[11])
            monto_desc = float(q[12])
            precio_final = float(q[6])
            pct = int((monto_desc/precio_orig)*100) if precio_orig > 0 else 0
            
            if monto_desc > 0:
                tk.Label(price_f, text=self._format_currency(precio_orig), font=("Segoe UI", 9, "overstrike"), bg="white", fg="#bdc3c7").pack(anchor="e")
                tk.Label(price_f, text=f"DESC. {pct}%: -{self._format_currency(monto_desc)}", font=("Segoe UI", 8, "bold"), bg="white", fg="#e74c3c").pack(anchor="e")
            
            tk.Label(price_f, text=self._format_currency(precio_final), font=("Segoe UI", 16, "bold"), bg="white", fg="#27ae60").pack(anchor="e", pady=(5, 0))
            
            # Botón de Marketing o Estado
            if mkt_enviado:
                tk.Label(price_f, text="✨ OFERTA ENVIADA", font=("Segoe UI", 8, "bold"), bg="#e8f8f5", fg="#16a085").pack(anchor="e", pady=(10, 0))
            elif is_free:
                btn_mkt = tk.Button(price_f, text="🎁 RE-OFERTAR", font=("Segoe UI", 8, "bold"), 
                                    bg="#27ae60", fg="white", bd=0, padx=10, pady=5, cursor="hand2",
                                    command=lambda i=quot_id: self.open_reoffer_dialog(i))
                btn_mkt.pack(anchor="e", pady=(10, 0))
            else:
                tk.Label(price_f, text="⚠️ OCUPADO", font=("Segoe UI", 8, "bold"), bg="white", fg="#95a5a6").pack(anchor="e", pady=(10, 0))

        except: pass

        card.quot_id = quot_id
        card.search_data = f"{quot_code} {client_name} {property_name}".lower()
        card.is_at_risk = is_at_risk
        card.is_free = is_free
        card.mkt_enviado = mkt_enviado
        card.raw_data = q
        self.cards.append(card)

    def reoffer_all_at_risk(self):
        """Envía una oferta especial masiva a todas las cotizaciones en riesgo filtradas."""
        targets = [c for c in self.cards if c.winfo_viewable() and c.is_at_risk and c.is_free and not c.mkt_enviado]
        
        if not targets:
            messagebox.showinfo("Información", "No hay cotizaciones en riesgo (y con disponibilidad) para re-ofertar en la vista actual.")
            return

        if not messagebox.askyesno("Confirmar Envío Masivo", 
                                  f"Se enviará una oferta especial con 5% de descuento extra a {len(targets)} contactos.\n\n¿Desea continuar?"):
            return

        from utils.email_sender import send_marketing_offer_email
        success_count = 0
        self.window.config(cursor="watch")
        self.window.update()

        for c in targets:
            q = c.raw_data
            current_price = float(q[6])
            new_price = current_price * 0.95 # 5% extra
            
            contact_id = q[8]
            tipo_contacto = q[15]
            
            contact = self.db.get_client_by_id(contact_id) if tipo_contacto == 'cliente' else self.db.get_prospect_by_id(contact_id)
            if not contact: continue

            data = {
                "id": q[0],
                "inmueble": q[2],
                "old_price": self._format_currency(current_price, show_decimals=False),
                "new_price": self._format_currency(new_price, show_decimals=False),
                "fecha_ingreso": q[3].strftime("%d/%m/%Y"),
                "fecha_egreso": q[4].strftime("%d/%m/%Y")
            }

            if send_marketing_offer_email(contact[3], f"{contact[1]} {contact[2]}", data, contact_type=tipo_contacto):
                self.db.mark_quotation_mkt_sent(q[0])
                success_count += 1

        self.window.config(cursor="")
        messagebox.showinfo("Proceso Completado", f"Se enviaron {success_count} ofertas de marketing exitosamente.")
        self.load_quotations()

    def open_reoffer_dialog(self, quot_id):
        """Abre un diálogo para proponer un nuevo descuento."""
        # Obtener datos de la cotización
        all_q = self.db.get_all_quotations()
        q = next((x for x in all_q if x[0] == quot_id), None)
        if not q: return

        # Ventana emergente
        dialog = tk.Toplevel(self.window)
        dialog.title("Mejorar Oferta de Marketing")
        dialog.geometry("400x350")
        dialog.configure(bg="#f8f9fa")
        dialog.transient(self.window)
        dialog.grab_set()

        main_d = ttk.Frame(dialog, padding=25)
        main_d.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_d, text="🎁 NUEVA OFERTA ESPECIAL", font=("Segoe UI", 12, "bold"), fg="#27ae60").pack(pady=(0, 20))
        
        current_price = float(q[6])
        tk.Label(main_d, text=f"Precio actual: {self._format_currency(current_price)}", font=("Segoe UI", 10)).pack(anchor="w")
        
        tk.Label(main_d, text="Nuevo Descuento Adicional (%):", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(15, 5))
        discount_var = tk.StringVar(value="5")
        ent = ttk.Entry(main_d, textvariable=discount_var, font=("Segoe UI", 12))
        ent.pack(fill=tk.X)
        ent.focus_set()

        def confirm():
            try:
                extra_pct = float(discount_var.get())
                new_price = current_price * (1 - (extra_pct / 100))
                
                # Obtener datos del contacto (cliente o prospecto)
                contact_id = q[8]
                tipo_contacto = q[15]
                
                contact = None
                if tipo_contacto == 'cliente':
                    contact = self.db.get_client_by_id(contact_id)
                else:
                    contact = self.db.get_prospect_by_id(contact_id)
                
                if not contact: 
                    messagebox.showerror("Error", "No se encontró el contacto asociado.")
                    return

                # contact = (id, nombre, apellido, email, tel, doc)
                data = {
                    "id": quot_id,
                    "inmueble": q[2],
                    "old_price": self._format_currency(current_price, show_decimals=False),
                    "new_price": self._format_currency(new_price, show_decimals=False),
                    "fecha_ingreso": q[3].strftime("%d/%m/%Y"),
                    "fecha_egreso": q[4].strftime("%d/%m/%Y")
                }

                from utils.email_sender import send_marketing_offer_email
                if send_marketing_offer_email(contact[3], f"{contact[1]} {contact[2]}", data, contact_type=tipo_contacto):
                    self.db.mark_quotation_mkt_sent(quot_id)
                    messagebox.showinfo("Éxito", f"¡Oferta especial enviada a {contact[3]}!", parent=dialog)
                    dialog.destroy()
                    self.load_quotations()
                else:
                    messagebox.showerror("Error", "No se pudo enviar el correo de marketing.", parent=dialog)
            except ValueError:
                messagebox.showerror("Error", "Ingrese un porcentaje válido.", parent=dialog)

        ttk.Button(main_d, text="ENVIAR REGALO POR EMAIL", style="QuotAction.TButton", command=confirm).pack(fill=tk.X, pady=25)

    def select_card(self, quot_id):
        self.selected_id = quot_id
        for c in self.cards:
            is_sel = c.quot_id == quot_id
            c.configure(highlightbackground="#3498db" if is_sel else "#d1d8e0", highlightthickness=2 if is_sel else 1)
            bg_color = "#f1f9ff" if is_sel else "white"
            self._update_bg_recursive(c, bg_color)

    def _update_bg_recursive(self, widget, color):
        try:
            current_bg = str(widget.cget("background"))
            if "ebf5fb" not in current_bg and "e8f4fd" not in current_bg:
                widget.configure(bg=color)
        except: pass
        for child in widget.winfo_children():
            self._update_bg_recursive(child, color)

    def load_quotations(self):
        """Carga las cotizaciones desde la DB."""
        for w in self.scrollable.winfo_children(): w.destroy()
        self.cards = []
        self.selected_id = None
        self.search_var.set("")
        
        quotations = self.db.get_all_quotations()
        for q in quotations:
            self.create_card(q)
            
        self.lbl_stats.config(text=f"TOTAL: {len(quotations)} COTIZACIONES")
        self.filter_cards()

    def filter_cards(self):
        query = self.search_var.get().lower()
        only_risk = self.risk_var.get()
        
        visible_count = 0
        for card in self.cards:
            match_search = query in card.search_data
            match_risk = not only_risk or (only_risk and card.is_at_risk)
            
            if match_search and match_risk:
                card.pack(fill=tk.X, padx=5, pady=8)
                visible_count += 1
            else:
                card.pack_forget()
        
        self.lbl_stats.config(text=f"MOSTRANDO: {visible_count} / TOTAL: {len(self.cards)}")
        
        # Ocultar o mostrar el botón masivo según si hay filtro de riesgo
        if only_risk and visible_count > 0:
            self.btn_batch.pack(side=tk.LEFT, padx=20, after=self.btn_batch.master.winfo_children()[0])
        else:
            # Si no hay nada o no está el filtro, dejarlo pero quizás deshabilitado o simplemente visible
            pass

    def _format_currency(self, value, show_decimals=True):
        try:
            val = float(value)
            if show_decimals:
                formatted = f"{val:,.2f}"
                m, d = formatted.split('.')
                return f"${m.replace(',', '.')},{d}"
            else:
                formatted = f"{val:,.0f}"
                return f"${formatted.replace(',', '.')}"
        except: return str(value)

    def delete_quotation(self):
        if not self.selected_id:
            messagebox.showwarning("Atención", "Seleccione una cotización para eliminar.")
            return
            
        quot_code = f"Q-{str(self.selected_id).zfill(5)}"
        if messagebox.askyesno("Confirmar", f"¿Desea eliminar la cotización {quot_code}?", parent=self.window):
            if self.db.delete_quotation(self.selected_id):
                self.load_quotations()

    def convert_to_reservation(self):
        """Toma los datos de la cotización y abre el formulario de reserva."""
        if not self.selected_id:
            messagebox.showwarning("Atención", "Seleccione una cotización para convertir.")
            return
            
        try:
            # Obtener datos completos de la DB
            all_q = self.db.get_all_quotations()
            q_data = next((x for x in all_q if x[0] == self.selected_id), None)
            
            if not q_data: 
                messagebox.showerror("Error", "No se encontraron los datos de la cotización.")
                return

            # Preparar datos iniciales de forma segura
            try:
                monto_desc = q_data[12] if q_data[12] is not None else 0
                descuento_str = str(int(float(monto_desc)))
            except:
                descuento_str = "0"

            initial_data = {
                "quotation_id": self.selected_id,
                "id_cliente": q_data[8],
                "is_prospect": q_data[15] == "prospecto",
                "inmueble": q_data[2],
                "fecha_ingreso": q_data[3].strftime("%d/%m/%Y") if hasattr(q_data[3], 'strftime') else q_data[3],
                "fecha_egreso": q_data[4].strftime("%d/%m/%Y") if hasattr(q_data[4], 'strftime') else q_data[4],
                "descuento": descuento_str,
                "discount_is_percentage": False, 
                "cantidad_personas": q_data[13]
            }
            
            quot_code = f"Q-{str(self.selected_id).zfill(5)}"
            if messagebox.askyesno("Convertir", f"¿Desea crear la reserva para {q_data[1]} basada en la cotización {quot_code}?", parent=self.window):
                # Guardamos la referencia antes de destruir
                ctrl = self.controller
                data = initial_data
                
                # Cerramos la ventana de cotizaciones PRIMERO para liberar el grab_set si lo hubiera
                self.window.destroy()
                
                # Iniciamos la reserva
                ctrl.create_reservation(initial_data=data)
                
        except Exception as e:
            messagebox.showerror("Error Crítico", f"No se pudo iniciar la conversión: {str(e)}")
            print(f"Error en convert_to_reservation: {e}")
