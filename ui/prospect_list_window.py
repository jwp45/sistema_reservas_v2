import tkinter as tk
from tkinter import ttk, messagebox
from controllers.database import Database
from datetime import datetime

class ProspectListWindow:
    def __init__(self, master):
        self.master = master
        self.db = Database()
        self.cards = []
        self.selected_id = None
        self.prospect_data_map = {}

        self.window = tk.Toplevel(master)
        self.window.title("Gestión de Prospectos (Leads) - Panel de Marketing")
        self.window.geometry("1000x800")
        self.window.configure(bg="#f0f2f5")

        # --- ESTILOS LOCALES ---
        style = ttk.Style(self.window)
        style.configure("PrDashboard.TFrame", background="#f0f2f5")
        style.configure("PrAction.TButton", font=("Segoe UI", 10, "bold"), padding=12)

        # --- ENCABEZADO ---
        header_frame = tk.Frame(self.window, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🎯 DIRECTORIO DE PROSPECTOS", font=("Segoe UI", 16, "bold"), 
                 bg="#2c3e50", fg="#ecf0f1").pack(side=tk.LEFT, padx=30, pady=20)
        
        self.lbl_total = tk.Label(header_frame, text="Cargando...", font=("Segoe UI", 10), 
                                bg="#2c3e50", fg="#95a5a6")
        self.lbl_total.pack(side=tk.RIGHT, padx=30)

        main_container = ttk.Frame(self.window, padding=30, style="PrDashboard.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True)

        # --- ÁREA DE BÚSQUEDA ---
        search_card = tk.Frame(main_container, bg="white", highlightbackground="#e0e0e0", highlightthickness=1, padx=20, pady=20)
        search_card.pack(fill=tk.X, pady=(0, 25))
        
        tk.Label(search_card, text="🔎 FILTRAR LEADS:", font=("Segoe UI", 9, "bold"), bg="white", fg="#2c3e50").pack(side=tk.LEFT, padx=(0, 15))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_card, textvariable=self.search_var, font=("Segoe UI", 11))
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_entry.bind("<KeyRelease>", lambda e: self.filter_cards())

        ttk.Button(search_card, text="ACTUALIZAR", command=self.load_prospects).pack(side=tk.RIGHT, padx=(15, 0))

        # --- LISTADO (SCROLL) ---
        canvas_frame = ttk.Frame(main_container, style="PrDashboard.TFrame")
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
        actions_frame = ttk.Frame(main_container, style="PrDashboard.TFrame")
        actions_frame.pack(fill=tk.X, pady=(25, 0))

        ttk.Button(actions_frame, text="🗑️ ELIMINAR PROSPECTO", command=self.delete_prospect).pack(side=tk.LEFT)
        
        btn_mkt = ttk.Button(actions_frame, text="✉️ ENVIAR PROMOCIÓN (PRÓXIMAMENTE)", style="PrAction.TButton", state="disabled")
        btn_mkt.pack(side=tk.RIGHT)

        # Cargar datos
        self.load_prospects()

    def bind_select(self, widget, prospect_id):
        widget.bind("<Button-1>", lambda e, i=prospect_id: self.select_card(i))
        for child in widget.winfo_children():
            self.bind_select(child, prospect_id)

    def create_card(self, p):
        # p = (id, doc, nombre, apellido, email, tel, fecha_reg)
        prospect_id = p[0]
        full_name = f"{p[2]} {p[3]}".upper()
        doc = p[1]
        email = p[4]
        phone = p[5]
        
        try:
            f_reg = p[6].strftime("%d/%m/%Y") if hasattr(p[6], 'strftime') else str(p[6])
        except: f_reg = "S/D"

        card = tk.Frame(self.scrollable, bg="white", bd=0, highlightbackground="#d1d8e0", highlightthickness=1)
        card.pack(fill=tk.X, padx=5, pady=8)
        self.bind_select(card, prospect_id)

        inner = tk.Frame(card, bg="white", padx=15, pady=15)
        inner.pack(fill=tk.X)
        self.bind_select(inner, prospect_id)

        # Info Principal
        info_f = tk.Frame(inner, bg="white")
        info_f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.bind_select(info_f, prospect_id)

        tk.Label(info_f, text=full_name, font=("Segoe UI", 12, "bold"), bg="white", fg="#2c3e50").pack(anchor="w")
        tk.Label(info_f, text=f"DNI: {doc} | Registrado: {f_reg}", font=("Segoe UI", 9), bg="white", fg="#7f8c8d").pack(anchor="w")

        # Contacto
        contact_f = tk.Frame(inner, bg="white")
        contact_f.pack(side=tk.RIGHT, fill=tk.Y)
        self.bind_select(contact_f, prospect_id)

        tk.Label(contact_f, text=f"✉️ {email}", font=("Segoe UI", 10), bg="white", fg="#34495e").pack(anchor="e")
        tk.Label(contact_f, text=f"📞 {phone}", font=("Segoe UI", 10, "bold"), bg="white", fg="#e67e22").pack(anchor="e")

        card.prospect_id = prospect_id
        card.search_data = f"{full_name} {doc} {email} {phone}".lower()
        self.cards.append(card)
        self.prospect_data_map[prospect_id] = p

    def select_card(self, prospect_id):
        self.selected_id = prospect_id
        for c in self.cards:
            is_sel = c.prospect_id == prospect_id
            c.configure(highlightbackground="#e67e22" if is_sel else "#d1d8e0", highlightthickness=2 if is_sel else 1)
            bg_color = "#fffbf2" if is_sel else "white"
            self._update_bg_recursive(c, bg_color)

    def _update_bg_recursive(self, widget, color):
        try:
            widget.configure(bg=color)
        except: pass
        for child in widget.winfo_children():
            self._update_bg_recursive(child, color)

    def load_prospects(self):
        for w in self.scrollable.winfo_children(): w.destroy()
        self.cards = []
        self.prospect_data_map = {}
        self.selected_id = None
        self.search_var.set("")

        if self.db.connect():
            prospects = self.db.get_all_prospects()
            self.lbl_total.config(text=f"TOTAL: {len(prospects)} PROSPECTOS")
            for p in prospects:
                self.create_card(p)
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
        self.lbl_total.config(text=f"MOSTRANDO: {visible_count} / TOTAL: {len(self.cards)}")

    def delete_prospect(self):
        if not self.selected_id:
            messagebox.showwarning("Atención", "Seleccione un prospecto para eliminar.")
            return

        p = self.prospect_data_map[self.selected_id]
        if messagebox.askyesno("Confirmar", f"¿Eliminar a {p[2]} {p[3]} de la lista de leads?"):
            if self.db.delete_prospect(self.selected_id):
                messagebox.showinfo("Éxito", "Prospecto eliminado.")
                self.load_prospects()
