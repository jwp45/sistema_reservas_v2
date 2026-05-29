import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta, date
from controllers.database import Database

class AdvancedSearchWindow:
    def __init__(self, master, on_property_selected_callback):
        self.master = master
        self.callback = on_property_selected_callback
        self.db = Database()
        self.db.connect()

        self.window = tk.Toplevel(master)
        self.window.title("Búsqueda Avanzada de Inmuebles")
        self.window.geometry("800x600")
        self.window.configure(bg="#f0f2f5")
        self.window.transient(master)
        self.window.grab_set()

        self.start_date = None
        self.end_date = None
        
        self.setup_ui()
        self.load_filters()

    def setup_ui(self):
        # Estilos
        style = ttk.Style(self.window)
        style.configure("Search.TFrame", background="#f0f2f5")
        style.configure("Card.TFrame", background="white", relief="flat")
        
        # Header
        header_frame = tk.Frame(self.window, bg="#2c3e50", height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text="🔍 BÚSQUEDA AVANZADA", font=("Segoe UI", 14, "bold"), 
                 bg="#2c3e50", fg="white").pack(pady=15)

        # Formulario de filtros
        filter_frame = ttk.Frame(self.window, padding=20, style="Search.TFrame")
        filter_frame.pack(fill=tk.X)

        # Fila 1: Fechas
        date_frame = tk.Frame(filter_frame, bg="#f0f2f5")
        date_frame.pack(fill=tk.X, pady=5)

        tk.Label(date_frame, text="Desde:", bg="#f0f2f5", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.ent_desde = ttk.Entry(date_frame, width=15)
        self.ent_desde.pack(side=tk.LEFT, padx=5)
        ttk.Button(date_frame, text="📅", width=3, command=lambda: self.select_date("desde")).pack(side=tk.LEFT)

        tk.Label(date_frame, text="Hasta:", bg="#f0f2f5", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(20, 5))
        self.ent_hasta = ttk.Entry(date_frame, width=15)
        self.ent_hasta.pack(side=tk.LEFT, padx=5)
        ttk.Button(date_frame, text="📅", width=3, command=lambda: self.select_date("hasta")).pack(side=tk.LEFT)

        # Fila 2: Capacidad y Ubicación
        loc_frame = tk.Frame(filter_frame, bg="#f0f2f5")
        loc_frame.pack(fill=tk.X, pady=15)

        tk.Label(loc_frame, text="Personas:", bg="#f0f2f5", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.var_personas = tk.StringVar(value="1")
        self.ent_personas = ttk.Entry(loc_frame, textvariable=self.var_personas, width=5)
        self.ent_personas.pack(side=tk.LEFT, padx=5)

        tk.Label(loc_frame, text="Provincia:", bg="#f0f2f5", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(20, 5))
        self.var_prov = tk.StringVar(value="Todas")
        self.combo_prov = ttk.Combobox(loc_frame, textvariable=self.var_prov, state="readonly", width=15)
        self.combo_prov.pack(side=tk.LEFT, padx=5)
        self.combo_prov.bind("<<ComboboxSelected>>", self.update_localidades)

        tk.Label(loc_frame, text="Localidad:", bg="#f0f2f5", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(20, 5))
        self.var_loc = tk.StringVar(value="Todas")
        self.combo_loc = ttk.Combobox(loc_frame, textvariable=self.var_loc, state="readonly", width=15)
        self.combo_loc.pack(side=tk.LEFT, padx=5)

        # Botón de Búsqueda
        ttk.Button(filter_frame, text="BUSCAR DISPONIBLES", command=self.perform_search).pack(pady=10)

        # Resultados
        results_frame = ttk.Frame(self.window, padding=20, style="Search.TFrame")
        results_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "nombre", "capacidad", "ubicacion", "tipo", "precio")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Inmueble")
        self.tree.heading("capacidad", text="Cap.")
        self.tree.heading("ubicacion", text="Ubicación")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("precio", text="Precio/Noche")

        self.tree.column("id", width=30, anchor="center")
        self.tree.column("nombre", width=200)
        self.tree.column("capacidad", width=50, anchor="center")
        self.tree.column("ubicacion", width=200)
        self.tree.column("tipo", width=100)
        self.tree.column("precio", width=100, anchor="e")

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.on_item_double_click)

        tk.Label(self.window, text="* Doble click para seleccionar el inmueble y volver al calendario", 
                 font=("Segoe UI", 8, "italic"), bg="#f0f2f5", fg="#7f8c8d").pack(pady=10)

    def load_filters(self):
        properties = self.db.get_all_properties()
        provincias = sorted(list(set(p[5] for p in properties)))
        self.combo_prov['values'] = ["Todas"] + provincias
        self.update_localidades()

    def update_localidades(self, event=None):
        prov = self.var_prov.get()
        properties = self.db.get_all_properties()
        if prov == "Todas":
            localidades = sorted(list(set(p[4] for p in properties)))
        else:
            localidades = sorted(list(set(p[4] for p in properties if p[5] == prov)))
        
        self.combo_loc['values'] = ["Todas"] + localidades
        self.var_loc.set("Todas")

    def select_date(self, field):
        from controllers.reservation_controller import CalendarDialog
        
        def callback(date_str):
            if field == "desde":
                self.ent_desde.delete(0, tk.END)
                self.ent_desde.insert(0, date_str)
                self.start_date = datetime.strptime(date_str, "%d/%m/%Y").date()
            else:
                self.ent_hasta.delete(0, tk.END)
                self.ent_hasta.insert(0, date_str)
                self.end_date = datetime.strptime(date_str, "%d/%m/%Y").date()

        # Si estamos seleccionando el "hasta", pasar el "desde" como fecha inicial si existe
        init_d = None
        if field == "hasta" and self.start_date:
            init_d = self.start_date
            
        CalendarDialog(self.window, callback, initial_date=init_d, highlight_date=init_d)

    def perform_search(self):
        # Validar fechas
        desde_str = self.ent_desde.get()
        hasta_str = self.ent_hasta.get()
        
        if not desde_str or not hasta_str:
            messagebox.showwarning("Atención", "Debe seleccionar un rango de fechas.")
            return

        try:
            d_desde = datetime.strptime(desde_str, "%d/%m/%Y").date()
            d_hasta = datetime.strptime(hasta_str, "%d/%m/%Y").date()
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha inválido (DD/MM/AAAA).")
            return

        if d_hasta <= d_desde:
            messagebox.showerror("Error", "La fecha de egreso debe ser posterior a la de ingreso.")
            return

        try:
            min_personas = int(self.var_personas.get())
        except ValueError:
            messagebox.showerror("Error", "La cantidad de personas debe ser un número.")
            return

        prov = self.var_prov.get()
        loc = self.var_loc.get()

        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Buscar inmuebles
        all_props = self.db.get_all_properties()
        results = []

        for p in all_props:
            # p = (id, nombre, cap, dir, loc, prov, tipo, val, img, dorms, camas, banos)
            p_id = p[0]
            p_nom = p[1]
            p_cap = p[2]
            p_loc = p[4]
            p_prov = p[5]
            p_tipo = p[6]
            p_val = p[7]

            # Filtro Capacidad
            if p_cap < min_personas:
                continue

            # Filtro Provincia
            if prov != "Todas" and p_prov != prov:
                continue

            # Filtro Localidad
            if loc != "Todas" and p_loc != loc:
                continue

            # Filtro Disponibilidad
            if self.db.is_range_available(p_id, d_desde, d_hasta):
                results.append(p)

        # Cargar en Treeview
        for p in results:
            self.tree.insert("", tk.END, values=(
                p[0], p[1], p[2], f"{p[4]}, {p[5]}", p[6], self._format_currency(p[7])
            ))

        if not results:
            messagebox.showinfo("Búsqueda", "No se encontraron inmuebles disponibles con esos criterios.")

    def _format_currency(self, value):
        try:
            val = float(value)
            formatted = f"{val:,.2f}"
            m, d = formatted.split('.')
            return f"${m.replace(',', '.')},{d}"
        except: return str(value)

    def on_item_double_click(self, event):
        item = self.tree.selection()
        if not item:
            return
        
        values = self.tree.item(item, "values")
        p_id = int(values[0])
        p_name = values[1]
        
        # Encontrar el objeto propiedad completo
        all_props = self.db.get_all_properties()
        selected_prop = next((p for p in all_props if p[0] == p_id), None)
        
        if selected_prop:
            # Pasar fechas seleccionadas también
            dates = {
                "desde": datetime.strptime(self.ent_desde.get(), "%d/%m/%Y").date(),
                "hasta": datetime.strptime(self.ent_hasta.get(), "%d/%m/%Y").date()
            }
            self.callback(selected_prop, dates)
            self.window.destroy()
