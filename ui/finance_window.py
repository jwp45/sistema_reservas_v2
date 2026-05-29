import tkinter as tk
from tkinter import ttk, messagebox
from controllers.database import Database
from datetime import datetime
from ui.payment_window import PaymentWindow

class FinanceWindow:
    def __init__(self, master):
        self.master = master
        self.db = Database()
        
        self.window = tk.Toplevel(master)
        self.window.title("Control Financiero - Panel de Gestión")
        self.window.geometry("1100x900")
        self.window.configure(bg="#f0f2f5")
        self.window.transient(master)

        # --- ESTILOS ---
        style = ttk.Style(self.window)
        style.configure("Fin.TFrame", background="#f0f2f5")
        style.configure("FinCard.TFrame", background="white", relief="flat")
        style.configure("FinHeader.TLabel", font=("Segoe UI", 18, "bold"), foreground="white", background="#2c3e50")

        # --- ENCABEZADO ---
        header_frame = tk.Frame(self.window, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="💰 BALANCE Y CONTROL FINANCIERO", font=("Segoe UI", 16, "bold"), 
                 bg="#2c3e50", fg="#ecf0f1").pack(side=tk.LEFT, padx=30, pady=20)
        
        tk.Label(header_frame, text=f"ACTUALIZADO: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                 font=("Segoe UI", 9), bg="#2c3e50", fg="#95a5a6").pack(side=tk.RIGHT, padx=30)

        # Contenedor Principal
        self.main_container = ttk.Frame(self.window, padding=30, style="Fin.TFrame")
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # --- KPIs (TARJETAS SUPERIORES) ---
        kpi_area = tk.Frame(self.main_container, bg="#f0f2f5")
        kpi_area.pack(fill=tk.X, pady=(0, 30))
        kpi_area.columnconfigure(0, weight=1)
        kpi_area.columnconfigure(1, weight=1)
        kpi_area.columnconfigure(2, weight=1)

        self.card_total = self._create_kpi_card(kpi_area, 0, "INGRESOS TOTALES", "#34495e")
        self.card_collected = self._create_kpi_card(kpi_area, 1, "TOTAL COBRADO", "#27ae60")
        self.card_pending = self._create_kpi_card(kpi_area, 2, "SALDO PENDIENTE", "#e74c3c")

        # --- ÁREA CENTRAL (GRÁFICOS/TABLAS) ---
        mid_area = tk.Frame(self.main_container, bg="#f0f2f5")
        mid_area.pack(fill=tk.BOTH, expand=True)
        mid_area.columnconfigure(0, weight=1)
        mid_area.columnconfigure(1, weight=1)

        # Tabla Mensual
        month_frame = self._create_section(mid_area, 0, "INGRESOS MENSUALES (ÚLTIMO AÑO)")
        self.tree_month = ttk.Treeview(month_frame, columns=("Mes", "Monto"), show="headings", height=8)
        self.tree_month.heading("Mes", text="MES / PERÍODO")
        self.tree_month.heading("Monto", text="FACTURACIÓN")
        self.tree_month.pack(fill=tk.BOTH, expand=True)

        # Tabla Inmuebles
        prop_frame = self._create_section(mid_area, 1, "RENDIMIENTO POR INMUEBLE")
        self.tree_prop = ttk.Treeview(prop_frame, columns=("Inmueble", "Total"), show="headings", height=8)
        self.tree_prop.heading("Inmueble", text="PROPIEDAD")
        self.tree_prop.heading("Total", text="RECAUDACIÓN TOTAL")
        self.tree_prop.pack(fill=tk.BOTH, expand=True)

        # --- LISTADO DE DEUDORES (INFERIOR) ---
        bottom_area = self._create_section(self.main_container, 0, "⚠️ SEGUIMIENTO DE CUENTAS POR COBRAR (Saldos Pendientes)", row=None)
        bottom_area.pack(fill=tk.BOTH, expand=True, pady=(30, 0))

        self.tree_debt = ttk.Treeview(bottom_area, columns=("ID", "Cliente", "Inmueble", "Fecha", "Deuda"), show="headings", height=6)
        self.tree_debt.heading("ID", text="RESERVA")
        self.tree_debt.heading("Cliente", text="HUÉSPED")
        self.tree_debt.heading("Inmueble", text="INMUEBLE")
        self.tree_debt.heading("Fecha", text="INGRESO")
        self.tree_debt.heading("Deuda", text="MONTO PENDIENTE")
        
        self.tree_debt.column("ID", width=80, anchor=tk.CENTER)
        self.tree_debt.column("Deuda", anchor=tk.E)
        self.tree_debt.pack(fill=tk.BOTH, expand=True)

        # Botón para cobrar desde aquí
        ttk.Button(bottom_area, text="VER PAGOS / REGISTRAR COBRO", command=self.open_debt_payment).pack(pady=(15, 0), anchor=tk.E)

        # Cargar Datos
        self.refresh_data()

    def _parse_currency_robust(self, value_str):
        """Convierte una cadena de moneda ($1.234,56) a float de forma robusta."""
        try:
            clean = str(value_str).replace('$', '').replace(' ', '').replace('.', '').replace(',', '.')
            return float(clean)
        except (ValueError, TypeError):
            return 0.0

    def open_debt_payment(self):
        """Abre la ventana de pago para el deudor seleccionado."""
        selected = self.tree_debt.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un deudor de la lista.", parent=self.window)
            return
        
        vals = self.tree_debt.item(selected[0])['values']
        # vals: 0:ID, 1:Cliente, 2:Inmueble, 3:Fecha, 4:Deuda
        try:
            rid = vals[0]
            client = vals[1]
            pending = self._parse_currency_robust(vals[4])
            
            PaymentWindow(self.window, rid, client, pending, self.refresh_data)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo procesar el saldo deudor: {str(e)}", parent=self.window)

    def _create_kpi_card(self, parent, col, title, color):
        card = tk.Frame(parent, bg="white", highlightbackground="#e0e0e0", highlightthickness=1)
        card.grid(row=0, column=col, padx=10, sticky="nsew")
        
        line = tk.Frame(card, bg=color, height=4)
        line.pack(fill=tk.X)
        
        content = tk.Frame(card, bg="white", padx=20, pady=20)
        content.pack(fill=tk.BOTH)
        
        tk.Label(content, text=title, font=("Segoe UI", 9, "bold"), bg="white", fg="#7f8c8d").pack(anchor="w")
        lbl_val = tk.Label(content, text="$0,00", font=("Segoe UI", 20, "bold"), bg="white", fg=color)
        lbl_val.pack(anchor="w", pady=(5, 0))
        return lbl_val

    def _create_section(self, parent, col, title, row=0):
        frame = tk.Frame(parent, bg="white", highlightbackground="#e0e0e0", highlightthickness=1, padx=20, pady=20)
        if row is not None:
            frame.grid(row=row, column=col, padx=10, sticky="nsew")
        
        tk.Label(frame, text=title, font=("Segoe UI", 10, "bold"), bg="white", fg="#2c3e50").pack(anchor="w", pady=(0, 15))
        return frame

    def _format_currency(self, value):
        try:
            val = float(value)
            formatted = f"{val:,.2f}"
            m, d = formatted.split('.')
            return f"${m.replace(',', '.')},{d}"
        except: return str(value)

    def refresh_data(self):
        if not self.db.connect():
            messagebox.showerror("Error", "No se pudo conectar a la base de datos", parent=self.window)
            return

        # 1. KPIs
        summary = self.db.get_financial_summary()
        self.card_total.config(text=self._format_currency(summary[0]))
        self.card_collected.config(text=self._format_currency(summary[1]))
        self.card_pending.config(text=self._format_currency(summary[2]))

        # 2. Mensual
        for i in self.tree_month.get_children(): self.tree_month.delete(i)
        for row in self.db.get_revenue_by_month():
            self.tree_month.insert("", "end", values=(row[0], self._format_currency(row[1])))

        # 3. Inmuebles
        for i in self.tree_prop.get_children(): self.tree_prop.delete(i)
        for row in self.db.get_revenue_by_property():
            self.tree_prop.insert("", "end", values=(row[0], self._format_currency(row[1])))

        # 4. Deudores
        for i in self.tree_debt.get_children(): self.tree_debt.delete(i)
        for row in self.db.get_pending_payments_list():
            # row: id, cliente, inmueble, fecha, deuda
            vals = list(row)
            vals[4] = self._format_currency(vals[4])
            self.tree_debt.insert("", "end", values=tuple(vals))
