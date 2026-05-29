import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from controllers.database import Database

class ConfigWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Configuración del Sistema")
        self.window.geometry("600x900")
        self.window.configure(bg="#f8f9fa")
        self.window.transient(parent)
        self.window.grab_set()

        self.db = Database()
        self.config_data = {}
        
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        style = ttk.Style(self.window)
        style.configure("ConfigHeader.TLabel", font=("Segoe UI", 18, "bold"), foreground="#2c3e50", background="#f8f9fa")
        style.configure("ConfigSection.TLabelframe", font=("Segoe UI", 10, "bold"))
        style.configure("Save.TButton", font=("Segoe UI", 10, "bold"), padding=10, background="#27ae60")

        main_frame = ttk.Frame(self.window, padding=30)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Configuración General", style="ConfigHeader.TLabel").pack(pady=(0, 20))

        # --- SECCIÓN TUTORIAL / AYUDA ---
        help_frame = ttk.LabelFrame(main_frame, text=" 💡 Guía Rápida de Configuración ", padding=15)
        help_frame.pack(fill=tk.X, pady=(0, 20))
        
        help_text = (
            "Para enviar cotizaciones por correos automáticamente (Gmail), siga estos pasos:\n\n"
            "1. Active la 'Verificación en 2 pasos' en su cuenta de Google.\n"
            "2. Busque 'Contraseñas de aplicaciones' en la configuración de seguridad.\n"
            "3. Genere una nueva contraseña para 'Otra (Nombre personalizado)' como 'Sistema Reservas'.\n"
            "4. Use el código de 16 dígitos generado como su 'Contraseña SMTP'.\n\n"
            "Valores comunes (Gmail): Servidor: smtp.gmail.com | Puerto: 587"
        )
        
        lbl_help = tk.Label(help_frame, text=help_text, font=("Segoe UI", 9), justify=tk.LEFT, 
                            anchor="w", bg="#e8f4f8", fg="#2c3e50", padx=10, pady=10, 
                            wraplength=500)
        lbl_help.pack(fill=tk.X)

        # --- SECCIÓN EMAIL (SMTP) ---
        email_frame = ttk.LabelFrame(main_frame, text=" Configuración de Email (SMTP) ", padding=20)
        email_frame.pack(fill=tk.X, pady=10)

        fields = [
            ("Servidor SMTP:", "smtp_server"),
            ("Puerto:", "smtp_port"),
            ("Usuario SMTP:", "smtp_user"),
            ("Contraseña SMTP:", "smtp_password"),
            ("Email Remitente:", "from_email")
        ]

        self.entries = {}
        for i, (label_text, field_name) in enumerate(fields):
            ttk.Label(email_frame, text=label_text).grid(row=i, column=0, sticky=tk.W, pady=8, padx=(0, 15))
            
            show = "*" if "password" in field_name else ""
            entry = ttk.Entry(email_frame, show=show)
            entry.grid(row=i, column=1, sticky=tk.EW, pady=8)
            email_frame.columnconfigure(1, weight=1)
            self.entries[field_name] = entry

        # --- SECCIÓN NEGOCIO ---
        business_frame = ttk.LabelFrame(main_frame, text=" Datos del Negocio ", padding=20)
        business_frame.pack(fill=tk.X, pady=10)

        business_fields = [
            ("Nombre del Negocio:", "business_name"),
            ("WhatsApp (con prefijo):", "whatsapp_number"),
            ("Logo Personalizado:", "logo_path")
        ]

        for i, (label_text, field_name) in enumerate(business_fields):
            ttk.Label(business_frame, text=label_text).grid(row=i, column=0, sticky=tk.W, pady=8, padx=(0, 15))
            entry = ttk.Entry(business_frame)
            entry.grid(row=i, column=1, sticky=tk.EW, pady=8)
            business_frame.columnconfigure(1, weight=1)
            self.entries[field_name] = entry
            
            if field_name == "logo_path":
                btn_logo = ttk.Button(business_frame, text="🔍", width=3, 
                                      command=lambda e=entry: self.select_logo(e))
                btn_logo.grid(row=i, column=2, padx=5)

        # Ayuda para WhatsApp
        ttk.Label(business_frame, text="Ej: 5492236689548", font=("Segoe UI", 8, "italic"), foreground="#7f8c8d").grid(row=1, column=1, sticky=tk.W)

        # --- BOTONES ---
        btn_frame = ttk.Frame(main_frame, padding=(0, 20, 0, 0))
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="CANCELAR", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="GUARDAR CAMBIOS", command=self.save_config, style="Save.TButton").pack(side=tk.RIGHT, padx=5)

    def load_config(self):
        if self.db.connect():
            config = self.db.get_config()
            if config:
                for field, value in config.items():
                    if field in self.entries:
                        self.entries[field].delete(0, tk.END)
                        self.entries[field].insert(0, str(value) if value is not None else "")
            else:
                messagebox.showerror("Error", "No se pudo cargar la configuración.")

    def select_logo(self, entry):
        file_path = filedialog.askopenfilename(
            title="Seleccionar Logo",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if file_path:
            entry.delete(0, tk.END)
            entry.insert(0, file_path)

    def save_config(self):
        data = {field: entry.get() for field, entry in self.entries.items()}
        
        # Validaciones básicas (excepto logo que puede ser opcional)
        required_fields = ["smtp_server", "smtp_port", "smtp_user", "smtp_password", "from_email", "business_name", "whatsapp_number"]
        if not all(data[f] for f in required_fields):
            messagebox.showwarning("Advertencia", "Los campos de SMTP y Negocio son obligatorios.")
            return

        try:
            data['smtp_port'] = int(data['smtp_port'])
        except ValueError:
            messagebox.showerror("Error", "El puerto SMTP debe ser un número.")
            return

        if self.db.connect():
            if self.db.update_config(data):
                messagebox.showinfo("Éxito", "Configuración actualizada correctamente.")
                self.window.destroy()
            else:
                messagebox.showerror("Error", "No se pudo actualizar la configuración en la base de datos.")
