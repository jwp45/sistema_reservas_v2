import tkinter as tk
from tkinter import ttk, messagebox
from controllers.database import Database
from datetime import datetime

class PaymentWindow:
    def __init__(self, master, reservation_id, client_name, pending_amount, callback):
        self.master = master
        self.reservation_id = reservation_id
        self.client_name = client_name
        self.pending_amount = float(pending_amount)
        self.callback = callback
        self.db = Database()

        self.window = tk.Toplevel(master)
        self.window.title("Registrar Pago Parcial")
        self.window.geometry("550x750")
        self.window.configure(bg="#f0f2f5")
        self.window.transient(master)
        self.window.grab_set()

        # --- ESTILOS ---
        style = ttk.Style(self.window)
        style.configure("PayHeader.TFrame", background="#2c3e50")
        style.configure("PayAction.TButton", font=("Segoe UI", 10, "bold"), padding=10)

        # --- ENCABEZADO ---
        header = tk.Frame(self.window, bg="#2c3e50", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="💳 REGISTRO DE ABONO Y AUDITORÍA", font=("Segoe UI", 12, "bold"), bg="#2c3e50", fg="white").pack(pady=15)

        # --- CONTENIDO ---
        main_frame = ttk.Frame(self.window, padding=25)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Resumen de Reserva (CARD)
        summary_card = tk.Frame(main_frame, bg="white", highlightbackground="#e0e0e0", highlightthickness=1, padx=20, pady=20)
        summary_card.pack(fill=tk.X, pady=(0, 20))

        tk.Label(summary_card, text=f"RESERVA #{reservation_id}", font=("Segoe UI", 8, "bold"), bg="white", fg="#95a5a6").pack(anchor="w")
        tk.Label(summary_card, text=client_name.upper(), font=("Segoe UI", 12, "bold"), bg="white", fg="#2c3e50").pack(anchor="w", pady=(5, 10))
        
        tk.Label(summary_card, text="SALDO PENDIENTE ACTUAL:", font=("Segoe UI", 9), bg="white", fg="#7f8c8d").pack(anchor="w")
        self.lbl_pending = tk.Label(summary_card, text=self._format_currency(self.pending_amount), font=("Segoe UI", 18, "bold"), bg="white", fg="#e74c3c")
        self.lbl_pending.pack(anchor="w")

        # Historial de Pagos (CARD)
        history_card = tk.Frame(main_frame, bg="white", highlightbackground="#e0e0e0", highlightthickness=1, padx=20, pady=20)
        history_card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        tk.Label(history_card, text="HISTORIAL DE MOVIMIENTOS:", font=("Segoe UI", 9, "bold"), bg="white", fg="#34495e").pack(anchor="w", pady=(0, 10))
        
        self.history_table = ttk.Treeview(history_card, columns=("Fecha", "Monto"), show="headings", height=8)
        self.history_table.heading("Fecha", text="FECHA DE PAGO")
        self.history_table.heading("Monto", text="MONTO ABONADO")
        self.history_table.column("Monto", anchor=tk.E)
        self.history_table.pack(fill=tk.BOTH, expand=True)

        # Entrada de Pago
        pay_frame = ttk.Frame(main_frame)
        pay_frame.pack(fill=tk.X)

        tk.Label(pay_frame, text="NUEVO MONTO A ABONAR:", font=("Segoe UI", 10, "bold"), fg="#2c3e50").pack(anchor="w", pady=(0, 5))
        self.pay_var = tk.StringVar()
        self.pay_entry = ttk.Entry(pay_frame, textvariable=self.pay_var, font=("Segoe UI", 14, "bold"))
        self.pay_entry.pack(fill=tk.X, pady=5)
        self.pay_entry.bind("<KeyRelease>", self._format_input)
        self.pay_entry.focus_set()

        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=20)

        ttk.Button(btn_frame, text="CANCELAR", command=self.window.destroy).pack(side=tk.LEFT)
        self.pay_btn = ttk.Button(btn_frame, text="REGISTRAR ABONO", style="PayAction.TButton", command=self.submit_payment)
        self.pay_btn.pack(side=tk.RIGHT)

        # Si ya está pagado, deshabilitar entrada
        if self.pending_amount <= 0:
            self.pay_entry.config(state="disabled")
            self.pay_btn.config(state="disabled")
            tk.Label(pay_frame, text="RESERVA TOTALMENTE PAGADA", font=("Segoe UI", 9, "bold"), fg="#27ae60", bg="#f0f2f5").pack(pady=5)

        # Cargar historial
        self.load_history()

    def load_history(self):
        """Carga el historial de pagos de la base de datos."""
        for i in self.history_table.get_children(): self.history_table.delete(i)
        
        if self.db.connect():
            history = self.db.get_payment_history(self.reservation_id)
            for row in history:
                # row: (fecha, monto)
                fecha_fmt = row[0].strftime("%d/%m/%Y %H:%M")
                monto_fmt = self._format_currency(row[1])
                self.history_table.insert("", "end", values=(fecha_fmt, monto_fmt))

    def _format_input(self, event):
        text = self.pay_var.get()
        cleaned = ''.join(filter(lambda char: char.isdigit(), text))
        if cleaned:
            val = float(cleaned)
            formatted = f"{val:,.0f}".replace(',', '.')
            self.pay_var.set(f"${formatted}")
        else:
            self.pay_var.set("")

    def _format_currency(self, value):
        formatted = f"{value:,.2f}"
        m, d = formatted.split('.')
        return f"${m.replace(',', '.')},{d}"

    def submit_payment(self):
        pay_str = self.pay_var.get().replace('$', '').replace('.', '').replace(',', '.')
        try:
            amount = float(pay_str)
            if amount <= 0:
                messagebox.showerror("Error", "El monto debe ser mayor a cero.", parent=self.window)
                return
            
            if not self.db.connect():
                messagebox.showerror("Error", "No se pudo conectar a la base de datos.", parent=self.window)
                return
            
            success, message = self.db.add_payment_to_reservation(self.reservation_id, amount)
            
            if success:
                messagebox.showinfo("Éxito", message, parent=self.window)
                self.window.destroy()
                if self.callback:
                    self.callback()
            else:
                messagebox.showerror("Error", message, parent=self.window)
                
        except ValueError:
            messagebox.showerror("Error", "Monto inválido.", parent=self.window)
