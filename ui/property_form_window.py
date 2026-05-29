import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import shutil
import os
from datetime import datetime

from controllers.database import Database
from PIL import Image, ImageTk

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "inmuebles")


class PropertyFormWindow:
    def __init__(self, master):
        self.master = master
        self.imagen_path = ""
        self.gallery_paths = []

        self.window = tk.Toplevel(master)
        self.window.title("Registrar Nuevo Inmueble")
        self.window.geometry("600x800")
        self.window.configure(bg="#f8f9fa")
        self.window.transient(master)

        # Estilos locales
        style = ttk.Style(self.window)
        style.configure("FormHeader.TLabel", font=("Segoe UI", 16, "bold"), foreground="#2c3e50", background="#f8f9fa")
        style.configure("FormSection.TLabelframe", font=("Segoe UI", 10, "bold"))
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=10)

        main_scroll_container = ttk.Frame(self.window)
        main_scroll_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(main_scroll_container, bg="#f8f9fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_scroll_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding=20)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=560)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Label(scrollable_frame, text="Registro de Inmueble", style="FormHeader.TLabel").pack(pady=(0, 20))

        # --- SECCIÓN 1: DETALLES GENERALES ---
        sec_info = ttk.LabelFrame(scrollable_frame, text=" Información General ", padding=15, style="FormSection.TLabelframe")
        sec_info.pack(fill=tk.X, pady=10)
        sec_info.columnconfigure(1, weight=1)

        self.fields = {
            "nombre": tk.StringVar(),
            "cantidad_personas": tk.StringVar(),
            "direccion": tk.StringVar(),
            "localidad": tk.StringVar(),
            "provincia": tk.StringVar(),
            "tipo": tk.StringVar(),
            "valor_dia": tk.StringVar(),
            "dormitorios": tk.IntVar(value=0),
            "camas": tk.IntVar(value=0),
            "baños": tk.IntVar(value=0)
        }
        
        self.fields["provincia"].set("Buenos Aires")

        ttk.Label(sec_info, text="Nombre:").grid(row=0, column=0, sticky=tk.W, pady=8)
        ttk.Entry(sec_info, textvariable=self.fields["nombre"]).grid(row=0, column=1, sticky=tk.EW, pady=8, padx=(10, 0))

        ttk.Label(sec_info, text="Tipo:").grid(row=1, column=0, sticky=tk.W, pady=8)
        self.combo_tipo = ttk.Combobox(sec_info, textvariable=self.fields["tipo"], 
                                      values=["Casa", "Departamento", "Cabaña", "Habitación", "Quinta"], state="readonly")
        self.combo_tipo.grid(row=1, column=1, sticky=tk.EW, pady=8, padx=(10, 0))
        self.combo_tipo.set("Departamento")

        ttk.Label(sec_info, text="Capacidad:").grid(row=2, column=0, sticky=tk.W, pady=8)
        ttk.Entry(sec_info, textvariable=self.fields["cantidad_personas"]).grid(row=2, column=1, sticky=tk.EW, pady=8, padx=(10, 0))

        # --- Campos Detalle (Dormitorios, Camas, Baños) ---
        details_f = tk.Frame(sec_info, bg="white")
        details_f.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        def create_counter(parent, label_text, var):
            container = tk.Frame(parent, bg="white")
            container.pack(side=tk.LEFT, expand=True)
            tk.Label(container, text=label_text, bg="white", font=("Segoe UI", 9)).pack()
            
            ctrl_f = tk.Frame(container, bg="white")
            ctrl_f.pack(pady=2)
            tk.Button(ctrl_f, text="-", width=2, command=lambda: var.set(max(0, var.get() - 1))).pack(side=tk.LEFT)
            tk.Label(ctrl_f, textvariable=var, width=3, bg="white", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=5)
            tk.Button(ctrl_f, text="+", width=2, command=lambda: var.set(var.get() + 1)).pack(side=tk.LEFT)

        create_counter(details_f, "Dormitorios", self.fields["dormitorios"])
        create_counter(details_f, "Camas", self.fields["camas"])
        create_counter(details_f, "Baños", self.fields["baños"])

        ttk.Label(sec_info, text="Valor por Día:").grid(row=4, column=0, sticky=tk.W, pady=8)
        ent_val = ttk.Entry(sec_info, textvariable=self.fields["valor_dia"])
        ent_val.grid(row=4, column=1, sticky=tk.EW, pady=8, padx=(10, 0))
        ent_val.bind("<KeyRelease>", self._format_currency_input)

        # --- SECCIÓN 2: UBICACIÓN ---
        sec_loc = ttk.LabelFrame(scrollable_frame, text=" Ubicación ", padding=15, style="FormSection.TLabelframe")
        sec_loc.pack(fill=tk.X, pady=10)
        sec_loc.columnconfigure(1, weight=1)

        ttk.Label(sec_loc, text="Dirección:").grid(row=0, column=0, sticky=tk.W, pady=8)
        ttk.Entry(sec_loc, textvariable=self.fields["direccion"]).grid(row=0, column=1, sticky=tk.EW, pady=8, padx=(10, 0))

        ttk.Label(sec_loc, text="Localidad:").grid(row=1, column=0, sticky=tk.W, pady=8)
        ttk.Entry(sec_loc, textvariable=self.fields["localidad"]).grid(row=1, column=1, sticky=tk.EW, pady=8, padx=(10, 0))

        ttk.Label(sec_loc, text="Provincia:").grid(row=2, column=0, sticky=tk.W, pady=8)
        ttk.Entry(sec_loc, textvariable=self.fields["provincia"]).grid(row=2, column=1, sticky=tk.EW, pady=8, padx=(10, 0))

        # --- SECCIÓN 3: SERVICIOS ---
        sec_services = ttk.LabelFrame(scrollable_frame, text=" Servicios / Amenities ", padding=15, style="FormSection.TLabelframe")
        sec_services.pack(fill=tk.X, pady=10)

        service_add_frame = tk.Frame(sec_services, bg="white")
        service_add_frame.pack(fill=tk.X, pady=5)

        # Selector de Icono
        self.icon_var = tk.StringVar(value="✨")
        self.combo_icon = ttk.Combobox(service_add_frame, textvariable=self.icon_var, width=3, state="readonly", font=("Segoe UI", 12))
        self.combo_icon['values'] = ["✨", "📶", "❄️", "🌡️", "🔥", "🌀", "🐾", "🍳", "☕", "🥐", "🥘", "🍝", "🍱", "🅿️", "🏊", "📺", "🚿", "🧺", "🧼", "🛏️", "🛌", "🚫", "🍖", "🧴", "🛡️", "🚲"]
        self.combo_icon.pack(side=tk.LEFT, padx=(0, 10))

        self.service_var = tk.StringVar()
        self.ent_service = ttk.Entry(service_add_frame, textvariable=self.service_var)
        self.ent_service.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.ent_service.bind("<Return>", lambda e: self.add_service())

        ttk.Button(service_add_frame, text="AGREGAR", command=self.add_service).pack(side=tk.RIGHT)

        # Lista de servicios con scroll
        list_frame = tk.Frame(sec_services, bg="white")
        list_frame.pack(fill=tk.X, pady=10)

        self.services_listbox = tk.Listbox(list_frame, height=5, font=("Segoe UI", 10))
        self.services_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)

        list_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.services_listbox.yview)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.services_listbox.config(yscrollcommand=list_scroll.set)

        ttk.Button(sec_services, text="ELIMINAR SELECCIONADO", command=self.remove_service).pack(fill=tk.X)

        # --- SECCIÓN 4: IMAGEN ---
        sec_img = ttk.LabelFrame(scrollable_frame, text=" Multimedia ", padding=15, style="FormSection.TLabelframe")
        sec_img.pack(fill=tk.X, pady=10)

        btn_row = ttk.Frame(sec_img)
        btn_row.pack(fill=tk.X)
        ttk.Button(btn_row, text="Seleccionar Imagen", command=self.select_image).pack(side=tk.LEFT, padx=5)
        self.lbl_img_name = ttk.Label(btn_row, text="Ninguna seleccionada", foreground="gray", font=("Segoe UI", 9))
        self.lbl_img_name.pack(side=tk.LEFT, padx=5)

        self.img_preview = ttk.Label(sec_img, background="#ecf0f1", relief=tk.RIDGE)
        self.img_preview.pack(pady=15)

        # --- SECCIÓN 5: GALERÍA ---
        sec_gal = ttk.LabelFrame(scrollable_frame, text=" Galería de Fotos ", padding=15, style="FormSection.TLabelframe")
        sec_gal.pack(fill=tk.X, pady=10)

        gal_row = ttk.Frame(sec_gal)
        gal_row.pack(fill=tk.X)
        ttk.Button(gal_row, text="Añadir Fotos a Galería", command=self.select_gallery).pack(side=tk.LEFT, padx=5)
        self.lbl_gal_count = ttk.Label(gal_row, text="0 fotos seleccionadas", foreground="gray", font=("Segoe UI", 9))
        self.lbl_gal_count.pack(side=tk.LEFT, padx=5)

        ttk.Button(sec_gal, text="Limpiar Galería", command=self.clear_gallery).pack(side=tk.RIGHT, padx=5)

        # Botones de Acción
        btn_frame = ttk.Frame(scrollable_frame, padding=(0, 20, 0, 0))
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="CANCELAR", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="GUARDAR INMUEBLE", style="Action.TButton", command=self.save_property).pack(side=tk.RIGHT, padx=5)

    def _format_currency_input(self, event):
        text = self.fields["valor_dia"].get()
        cleaned = ''.join(filter(lambda char: char.isdigit(), text))
        if cleaned:
            val = float(cleaned)
            formatted = f"{val:,.0f}".replace(',', '.')
            self.fields["valor_dia"].set(f"${formatted}")
        else:
            self.fields["valor_dia"].set("")

    def select_image(self):
        path = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if path:
            self.imagen_path = path
            self.lbl_img_name.config(text=os.path.basename(path), foreground="black")
            try:
                img = Image.open(path)
                img.thumbnail((300, 200))
                tk_img = ImageTk.PhotoImage(img)
                self.img_preview.config(image=tk_img)
                self.img_preview.image = tk_img
            except Exception as e:
                print(f"Error al cargar imagen: {e}")

    def add_service(self):
        service = self.service_var.get().strip()
        icon = self.icon_var.get()
        if service:
            display_text = f"{icon} {service}"
            current_services = self.services_listbox.get(0, tk.END)
            if display_text not in current_services:
                self.services_listbox.insert(tk.END, display_text)
                self.service_var.set("")
            else:
                messagebox.showwarning("Atención", "El servicio ya está en la lista.")
        self.ent_service.focus()

    def remove_service(self):
        selected = self.services_listbox.curselection()
        if selected:
            self.services_listbox.delete(selected)

    def select_gallery(self):
        paths = filedialog.askopenfilenames(
            title="Seleccionar fotos para la galería",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if paths:
            self.gallery_paths.extend(list(paths))
            self.lbl_gal_count.config(text=f"{len(self.gallery_paths)} fotos seleccionadas", foreground="black")

    def clear_gallery(self):
        self.gallery_paths = []
        self.lbl_gal_count.config(text="0 fotos seleccionadas", foreground="gray")

    def save_property(self):
        if not all(v.get() for v in self.fields.values()):
            messagebox.showerror("Error", "Todos los campos son obligatorios", parent=self.window)
            return

        # Limpiar formato de moneda
        valor_raw = self.fields["valor_dia"].get().replace('$', '').replace('.', '').replace(',', '.')
        try:
            valor_dia = float(valor_raw)
        except:
            messagebox.showerror("Error", "Valor por día inválido", parent=self.window)
            return

        property_data = (
            self.fields["nombre"].get(),
            self.fields["cantidad_personas"].get(),
            self.fields["direccion"].get(),
            self.fields["localidad"].get(),
            self.fields["provincia"].get(),
            self.fields["tipo"].get(),
            valor_dia,
            self.fields["dormitorios"].get(),
            self.fields["camas"].get(),
            self.fields["baños"].get()
        )

        db = Database()
        if db.connect():
            cursor = db.connection.cursor()
            query = """INSERT INTO inmuebles 
                       (nombre, cantidad_personas, direccion, localidad, provincia, tipo, valor_dia, dormitorios, camas, baños) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(query, property_data)
            db.connection.commit()
            id_inmueble = cursor.lastrowid

            # Guardar servicios parseando icono y nombre
            raw_services = self.services_listbox.get(0, tk.END)
            parsed_services = []
            for rs in raw_services:
                # El formato es "ICONO NOMBRE"
                parts = rs.split(" ", 1)
                if len(parts) == 2:
                    parsed_services.append((parts[0], parts[1]))
                else:
                    parsed_services.append(("✨", rs))
                    
            db.insert_property_services(id_inmueble, parsed_services)

            # Guardar galería
            if self.gallery_paths:
                gallery_dir = os.path.join(ASSETS_DIR, "gallery", str(id_inmueble))
                os.makedirs(gallery_dir, exist_ok=True)
                for i, path in enumerate(self.gallery_paths):
                    ext = os.path.splitext(path)[1]
                    dest = os.path.join(gallery_dir, f"gal_{i}_{int(datetime.now().timestamp())}{ext}")
                    try:
                        shutil.copy2(path, dest)
                        db.insert_gallery_image(id_inmueble, dest)
                    except Exception as e:
                        print(f"Error al copiar imagen de galería: {e}")

            if self.imagen_path:
                ext = os.path.splitext(self.imagen_path)[1]
                dest = os.path.join(ASSETS_DIR, f"{id_inmueble}{ext}")
                try:
                    shutil.copy2(self.imagen_path, dest)
                    cursor.execute("UPDATE inmuebles SET imagen = %s WHERE id_inmueble = %s", (dest, id_inmueble))
                    db.connection.commit()
                except Exception as e:
                    print(f"Error al copiar imagen: {e}")

            cursor.close()
            messagebox.showinfo("Éxito", "Inmueble guardado exitosamente", parent=self.window)
            self.window.destroy()
        else:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos", parent=self.window)

    def show(self):
        self.window.mainloop()
