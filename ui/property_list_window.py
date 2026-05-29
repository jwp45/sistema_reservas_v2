import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import shutil
import os
from datetime import datetime

from controllers.database import Database
from controllers.property_controller import PropertyController
from PIL import Image, ImageTk
from ui.gallery_window import GalleryWindow

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "inmuebles")


class EditPropertyWindow:
    def __init__(self, master, property_id, property_list_window):
        self.master = master
        self.property_id = property_id
        self.property_list_window = property_list_window
        self.imagen_path = ""

        self.window = tk.Toplevel(master)
        self.window.title("Ficha Técnica - Panel de Gestión")
        self.window.geometry("650x800")
        self.window.configure(bg="#f0f2f5")
        self.window.transient(master)

        # --- ESTILOS LOCALES ---
        style = ttk.Style(self.window)
        style.configure("PHeader.TFrame", background="#2c3e50")
        style.configure("PContent.TFrame", background="#f0f2f5")
        style.configure("PSection.TLabelframe", font=("Segoe UI", 10, "bold"), background="white")
        style.configure("PAction.TButton", font=("Segoe UI", 10, "bold"), padding=12)

        # --- ENCABEZADO ---
        header_frame = tk.Frame(self.window, bg="#2c3e50", height=70)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=f"🏠 GESTIONAR INMUEBLE #{property_id}", font=("Segoe UI", 14, "bold"), 
                 bg="#2c3e50", fg="#ecf0f1").pack(side=tk.LEFT, padx=30, pady=18)

        # --- CONTENIDO DESPLAZABLE ---
        main_scroll_container = ttk.Frame(self.window, style="PContent.TFrame")
        main_scroll_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(main_scroll_container, bg="#f0f2f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_scroll_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f0f2f5")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=620)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        content_padding = tk.Frame(scrollable_frame, bg="#f0f2f5", padx=30, pady=20)
        content_padding.pack(fill=tk.BOTH, expand=True)

        # --- SECCIÓN 1: DATOS GENERALES ---
        sec_info = tk.LabelFrame(content_padding, text=" ESPECIFICACIONES TÉCNICAS ", font=("Segoe UI", 9, "bold"), 
                                bg="white", fg="#2c3e50", padx=25, pady=25, relief=tk.FLAT, highlightbackground="#e0e0e0", highlightthickness=1)
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

        fields_order = [
            ("NOMBRE DEL INMUEBLE:", "nombre"),
            ("TIPO DE PROPIEDAD:", "tipo"),
            ("CAPACIDAD MÁXIMA:", "cantidad_personas"),
            ("VALOR POR NOCHE:", "valor_dia")
        ]

        for i, (label_text, field_name) in enumerate(fields_order):
            tk.Label(sec_info, text=label_text, bg="white", font=("Segoe UI", 8, "bold")).grid(row=i, column=0, sticky=tk.W, pady=10, padx=(0, 15))
            ent = ttk.Entry(sec_info, textvariable=self.fields[field_name], font=("Segoe UI", 10))
            ent.grid(row=i, column=1, sticky=tk.EW, pady=10)
            if field_name == "valor_dia":
                ent.bind("<KeyRelease>", self._format_currency_input)

        # --- Campos Detalle (Dormitorios, Camas, Baños) ---
        details_f = tk.Frame(sec_info, bg="white")
        details_f.grid(row=len(fields_order), column=0, columnspan=2, sticky=tk.EW, pady=15)
        
        def create_counter(parent, label_text, var):
            container = tk.Frame(parent, bg="white")
            container.pack(side=tk.LEFT, expand=True)
            tk.Label(container, text=label_text, bg="white", font=("Segoe UI", 8, "bold")).pack()
            
            ctrl_f = tk.Frame(container, bg="white")
            ctrl_f.pack(pady=2)
            tk.Button(ctrl_f, text="-", width=2, command=lambda: var.set(max(0, var.get() - 1))).pack(side=tk.LEFT)
            tk.Label(ctrl_f, textvariable=var, width=3, bg="white", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=5)
            tk.Button(ctrl_f, text="+", width=2, command=lambda: var.set(var.get() + 1)).pack(side=tk.LEFT)

        create_counter(details_f, "DORMITORIOS", self.fields["dormitorios"])
        create_counter(details_f, "CAMAS", self.fields["camas"])
        create_counter(details_f, "BAÑOS", self.fields["baños"])

        # --- SECCIÓN 2: UBICACIÓN ---
        sec_loc = tk.LabelFrame(content_padding, text=" LOCALIZACIÓN ", font=("Segoe UI", 9, "bold"), 
                               bg="white", fg="#2c3e50", padx=25, pady=25, relief=tk.FLAT, highlightbackground="#e0e0e0", highlightthickness=1)
        sec_loc.pack(fill=tk.X, pady=10)
        sec_loc.columnconfigure(1, weight=1)

        loc_fields = [("DIRECCIÓN:", "direccion"), ("LOCALIDAD:", "localidad"), ("PROVINCIA:", "provincia")]
        for i, (label_text, field_name) in enumerate(loc_fields):
            tk.Label(sec_loc, text=label_text, bg="white", font=("Segoe UI", 8, "bold")).grid(row=i, column=0, sticky=tk.W, pady=10, padx=(0, 15))
            ttk.Entry(sec_loc, textvariable=self.fields[field_name], font=("Segoe UI", 10)).grid(row=i, column=1, sticky=tk.EW, pady=10)

        # --- SECCIÓN 3: SERVICIOS ---
        sec_services = tk.LabelFrame(content_padding, text=" SERVICIOS / AMENITIES ", font=("Segoe UI", 9, "bold"), 
                               bg="white", fg="#2c3e50", padx=25, pady=25, relief=tk.FLAT, highlightbackground="#e0e0e0", highlightthickness=1)
        sec_services.pack(fill=tk.X, pady=10)

        service_add_frame = tk.Frame(sec_services, bg="white")
        service_add_frame.pack(fill=tk.X, pady=5)

        # Selector de Icono
        self.icon_var = tk.StringVar(value="✨")
        self.combo_icon = ttk.Combobox(service_add_frame, textvariable=self.icon_var, width=3, state="readonly", font=("Segoe UI", 12))
        self.combo_icon['values'] = ["✨", "📶", "❄️", "🌡️", "🔥", "🌀", "🐾", "🍳", "☕", "🥐", "🥘", "🍝", "🍱", "🅿️", "🏊", "📺", "🚿", "🧺", "🧼", "🛏️", "🛌", "🚫", "🍖", "🧴", "🛡️", "🚲"]
        self.combo_icon.pack(side=tk.LEFT, padx=(0, 10))

        self.service_var = tk.StringVar()
        self.ent_service = ttk.Entry(service_add_frame, textvariable=self.service_var, font=("Segoe UI", 10))
        self.ent_service.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.ent_service.bind("<Return>", lambda e: self.add_service())

        ttk.Button(service_add_frame, text="AGREGAR", command=self.add_service).pack(side=tk.RIGHT)

        list_frame = tk.Frame(sec_services, bg="white")
        list_frame.pack(fill=tk.X, pady=10)

        self.services_listbox = tk.Listbox(list_frame, height=5, font=("Segoe UI", 10))
        self.services_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)

        list_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.services_listbox.yview)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.services_listbox.config(yscrollcommand=list_scroll.set)

        ttk.Button(sec_services, text="ELIMINAR SELECCIONADO", command=self.remove_service).pack(fill=tk.X)

        # --- SECCIÓN 4: GALERÍA ---
        sec_gal = tk.LabelFrame(content_padding, text=" GALERÍA DE FOTOS ", font=("Segoe UI", 9, "bold"), 
                               bg="white", fg="#2c3e50", padx=25, pady=25, relief=tk.FLAT, highlightbackground="#e0e0e0", highlightthickness=1)
        sec_gal.pack(fill=tk.X, pady=10)

        gal_btn_f = tk.Frame(sec_gal, bg="white")
        gal_btn_f.pack(fill=tk.X)

        ttk.Button(gal_btn_f, text="AÑADIR FOTOS", command=self.add_to_gallery).pack(side=tk.LEFT, padx=5)
        ttk.Button(gal_btn_f, text="VER GALERÍA", command=self.open_gallery_viewer).pack(side=tk.LEFT, padx=5)
        
        self.lbl_gal_info = tk.Label(gal_btn_f, text="0 fotos cargadas", bg="white", fg="#7f8c8d", font=("Segoe UI", 8))
        self.lbl_gal_info.pack(side=tk.LEFT, padx=15)

        # Lista de imágenes (solo nombres/rutas)
        self.gal_listbox = tk.Listbox(sec_gal, height=4, font=("Segoe UI", 9))
        self.gal_listbox.pack(fill=tk.X, pady=10)

        ttk.Button(sec_gal, text="ELIMINAR FOTO SELECCIONADA", command=self.delete_from_gallery).pack(fill=tk.X)

        # --- SECCIÓN 5: MULTIMEDIA ---
        sec_img = tk.LabelFrame(content_padding, text=" VISTA PREVIA Y MULTIMEDIA ", font=("Segoe UI", 9, "bold"), 
                               bg="white", fg="#2c3e50", padx=25, pady=25, relief=tk.FLAT, highlightbackground="#e0e0e0", highlightthickness=1)
        sec_img.pack(fill=tk.X, pady=10)

        ttk.Button(sec_img, text="CAMBIAR IMAGEN", command=self.select_image).pack(pady=5)
        self.lbl_img_name = tk.Label(sec_img, text="Sin cambios", bg="white", fg="#95a5a6", font=("Segoe UI", 8))
        self.lbl_img_name.pack()

        self.img_preview = tk.Label(sec_img, bg="#f1f2f6", relief=tk.RIDGE)
        self.img_preview.pack(pady=15)

        self.load_property_data()

        # Barra de Botones Inferior
        btn_container = tk.Frame(self.window, bg="#f0f2f5", pady=25, padx=30)
        btn_container.pack(fill=tk.X)
        
        ttk.Button(btn_container, text="CANCELAR", command=self.window.destroy).pack(side=tk.LEFT)
        ttk.Button(btn_container, text="GUARDAR CAMBIOS", style="PAction.TButton", 
                   command=self.save_changes).pack(side=tk.RIGHT)

    def _format_currency_input(self, event):
        text = self.fields["valor_dia"].get()
        cleaned = ''.join(filter(lambda char: char.isdigit(), text))
        if cleaned:
            val = float(cleaned)
            formatted = f"{val:,.0f}".replace(',', '.')
            self.fields["valor_dia"].set(f"${formatted}")
        else:
            self.fields["valor_dia"].set("")

    def _format_currency(self, value):
        try:
            val = float(value)
            formatted = f"{val:,.2f}"
            m, d = formatted.split('.')
            return f"${m.replace(',', '.')},{d}"
        except: return str(value)

    def add_service(self):
        service = self.service_var.get().strip()
        icon = self.icon_var.get()
        if service:
            display_text = f"{icon} {service}"
            current = self.services_listbox.get(0, tk.END)
            if display_text not in current:
                self.services_listbox.insert(tk.END, display_text)
                self.service_var.set("")
            else:
                messagebox.showwarning("Atención", "El servicio ya está en la lista.")
        self.ent_service.focus()

    def remove_service(self):
        selected = self.services_listbox.curselection()
        if selected:
            self.services_listbox.delete(selected)

    def delete_from_gallery(self):
        selected = self.gal_listbox.curselection()
        if not selected: return
        
        index = selected[0]
        img_id, path = self.gallery_data[index]
        
        if messagebox.askyesno("Confirmar", "¿Eliminar esta foto de la galería?", parent=self.window):
            db = Database()
            if db.connect():
                if db.delete_gallery_image(img_id):
                    # Opcional: borrar archivo físico
                    # if os.path.exists(path): os.remove(path)
                    self.load_gallery_data()
            else:
                messagebox.showerror("Error", "No se pudo conectar a la base de datos")

    def add_to_gallery(self):
        paths = filedialog.askopenfilenames(
            title="Seleccionar fotos",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if not paths: return
        
        db = Database()
        if db.connect():
            gallery_dir = os.path.join(ASSETS_DIR, "gallery", str(self.property_id))
            os.makedirs(gallery_dir, exist_ok=True)
            
            for path in paths:
                ext = os.path.splitext(path)[1]
                dest = os.path.join(gallery_dir, f"gal_{int(datetime.now().timestamp())}_{os.path.basename(path)}")
                try:
                    shutil.copy2(path, dest)
                    db.insert_gallery_image(self.property_id, dest)
                except Exception as e:
                    print(f"Error copiando: {e}")
            
            self.load_gallery_data()
        else:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos")

    def open_gallery_viewer(self):
        if not hasattr(self, "gallery_data") or not self.gallery_data:
            messagebox.showinfo("Información", "No hay fotos cargadas en la galería.")
            return
        
        paths = [g[1] for s, g in enumerate(self.gallery_data)]
        GalleryWindow(self.window, self.fields["nombre"].get(), paths)

    def load_gallery_data(self):
        self.gal_listbox.delete(0, tk.END)
        db = Database()
        if db.connect():
            self.gallery_data = db.get_gallery_images(self.property_id)
            for _, path in self.gallery_data:
                self.gal_listbox.insert(tk.END, os.path.basename(path))
            self.lbl_gal_info.config(text=f"{len(self.gallery_data)} fotos cargadas")

    def select_image(self):
        path = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if path:
            self.imagen_path = path
            self.lbl_img_name.config(text=os.path.basename(path))
            try:
                img = Image.open(path)
                img.thumbnail((250, 180))
                tk_img = ImageTk.PhotoImage(img)
                self.img_preview.config(image=tk_img)
                self.img_preview.image = tk_img
            except Exception as e:
                print(f"Error al cargar imagen: {e}")

    def load_property_data(self):
        db = Database()
        if db.connect():
            query = """SELECT nombre, cantidad_personas, direccion, localidad, provincia, 
                              tipo, valor_dia, COALESCE(imagen, ''), dormitorios, camas, baños 
                       FROM inmuebles WHERE id_inmueble = %s"""
            cursor = db.connection.cursor()
            cursor.execute(query, (self.property_id,))
            result = cursor.fetchone()
            if result:
                self.fields["nombre"].set(result[0])
                self.fields["cantidad_personas"].set(result[1])
                self.fields["direccion"].set(result[2])
                self.fields["localidad"].set(result[3])
                self.fields["provincia"].set(result[4])
                self.fields["tipo"].set(result[5])
                self.fields["valor_dia"].set(self._format_currency(result[6]))
                
                img_path = result[7]
                if img_path and os.path.exists(img_path):
                    self.imagen_path = img_path
                    try:
                        img = Image.open(img_path)
                        img.thumbnail((250, 180))
                        tk_img = ImageTk.PhotoImage(img)
                        self.img_preview.config(image=tk_img)
                        self.img_preview.image = tk_img
                    except: pass
                
                # Campos Detalle
                self.fields["dormitorios"].set(result[8] if result[8] is not None else 0)
                self.fields["camas"].set(result[9] if result[9] is not None else 0)
                self.fields["baños"].set(result[10] if result[10] is not None else 0)
            
            # Cargar servicios
            servicios = db.get_property_services(self.property_id)
            for icon, name in servicios:
                self.services_listbox.insert(tk.END, f"{icon} {name}")
                
            # Cargar galería
            self.load_gallery_data()
        else:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos", parent=self.window)

    def save_changes(self):
        if not all(v.get() for v in self.fields.values()):
            messagebox.showerror("Error", "Todos los campos son obligatorios", parent=self.window)
            return

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
            query = """UPDATE inmuebles SET 
                       nombre=%s, cantidad_personas=%s, direccion=%s, localidad=%s, 
                       provincia=%s, tipo=%s, valor_dia=%s, 
                       dormitorios=%s, camas=%s, baños=%s 
                       WHERE id_inmueble=%s"""
            cursor.execute(query, property_data + (self.property_id,))

            # Guardar servicios parseando icono y nombre
            raw_services = self.services_listbox.get(0, tk.END)
            parsed_services = []
            for rs in raw_services:
                parts = rs.split(" ", 1)
                if len(parts) == 2:
                    parsed_services.append((parts[0], parts[1]))
                else:
                    parsed_services.append(("✨", rs))
            
            db.insert_property_services(self.property_id, parsed_services)

            if self.imagen_path and not self.imagen_path.startswith(ASSETS_DIR):
                ext = os.path.splitext(self.imagen_path)[1]
                dest = os.path.join(ASSETS_DIR, f"{self.property_id}{ext}")
                try:
                    shutil.copy2(self.imagen_path, dest)
                    cursor.execute("UPDATE inmuebles SET imagen = %s WHERE id_inmueble = %s", (dest, self.property_id))
                except Exception as e:
                    print(f"Error al copiar imagen: {e}")

            db.connection.commit()
            cursor.close()
            messagebox.showinfo("Éxito", "Inmueble actualizado exitosamente", parent=self.window)
            self.window.destroy()
            self.property_list_window.refresh_properties()
        else:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos", parent=self.window)


class PropertyListWindow:
    def __init__(self, master):
        self.master = master
        self.cards = []
        self.images = []
        self.selected_id = None

        self.window = tk.Toplevel(master)
        self.window.title("Catálogo de Inmuebles - Gestión Hotelera")
        self.window.geometry("1150x800")
        self.window.configure(bg="#f0f2f5")

        # --- ESTILOS ---
        style = ttk.Style(self.window)
        style.configure("PdDashboard.TFrame", background="#f0f2f5")
        style.configure("PdCard.TFrame", background="white", relief="flat")
        style.configure("PdAction.TButton", font=("Segoe UI", 10, "bold"), padding=12)

        # --- ENCABEZADO ---
        header_frame = tk.Frame(self.window, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🏠 CATÁLOGO DE INMUEBLES", font=("Segoe UI", 16, "bold"), 
                 bg="#2c3e50", fg="#ecf0f1").pack(side=tk.LEFT, padx=30, pady=20)
        
        self.lbl_stats = tk.Label(header_frame, text="Cargando catálogo...", font=("Segoe UI", 10), 
                                 bg="#2c3e50", fg="#95a5a6")
        self.lbl_stats.pack(side=tk.RIGHT, padx=30)

        main_container = ttk.Frame(self.window, padding=30, style="PdDashboard.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True)

        # --- FILTROS (CARD) ---
        filter_card = tk.Frame(main_container, bg="white", highlightbackground="#e0e0e0", highlightthickness=1, padx=20, pady=20)
        filter_card.pack(fill=tk.X, pady=(0, 25))

        tk.Label(filter_card, text="🔎 BUSCAR:", font=("Segoe UI", 9, "bold"), bg="white", fg="#2c3e50").pack(side=tk.LEFT, padx=(0, 10))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_card, textvariable=self.search_var, font=("Segoe UI", 10), width=35)
        search_entry.pack(side=tk.LEFT, padx=(0, 20))
        search_entry.bind("<KeyRelease>", lambda e: self.filter_cards())

        tk.Label(filter_card, text="TIPO:", font=("Segoe UI", 9, "bold"), bg="white", fg="#2c3e50").pack(side=tk.LEFT, padx=(0, 10))
        self.type_filter = ttk.Combobox(filter_card, values=["Todos", "Casa", "Departamento", "Cabaña", "Habitación"], state="readonly", width=18)
        self.type_filter.set("Todos")
        self.type_filter.pack(side=tk.LEFT, padx=(0, 20))
        self.type_filter.bind("<<ComboboxSelected>>", lambda e: self.filter_cards())

        ttk.Button(filter_card, text="ACTUALIZAR", command=self.load_properties).pack(side=tk.RIGHT)

        # --- LISTADO (SCROLL) ---
        canvas_frame = ttk.Frame(main_container, style="PdDashboard.TFrame")
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="#f0f2f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable = tk.Frame(self.canvas, bg="#f0f2f5")

        self.scrollable.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable, anchor="nw", width=1060)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- ACCIONES ---
        btn_frame = ttk.Frame(main_container, style="PdDashboard.TFrame")
        btn_frame.pack(fill=tk.X, pady=(25, 0))
        ttk.Button(btn_frame, text="ELIMINAR SELECCIONADO", command=self.delete_property).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="GESTIONAR DETALLES", style="PdAction.TButton", command=self.edit_property).pack(side=tk.RIGHT)

        self.db = Database()
        self.load_properties()

    def bind_select(self, widget, id_inmueble):
        widget.bind("<Button-1>", lambda e, i=id_inmueble: self.select_card(i))
        for child in widget.winfo_children():
            self.bind_select(child, id_inmueble)

    def create_card(self, prop):
        id_inmueble, nombre, capacidad, direccion, localidad, provincia, tipo, valor_dia, img_path, dorms, camas, banos = prop

        card = tk.Frame(self.scrollable, bg="white", bd=0, highlightbackground="#d1d8e0", highlightthickness=1)
        card.pack(fill=tk.X, padx=5, pady=8)
        self.bind_select(card, id_inmueble)
        card.bind("<Double-Button-1>", lambda e, i=id_inmueble: self.edit_property_by_id(i))

        inner = tk.Frame(card, bg="white", padx=15, pady=15)
        inner.pack(fill=tk.X)
        self.bind_select(inner, id_inmueble)

        # Imagen
        img_container = tk.Frame(inner, width=180, height=120, bg="#f1f2f6")
        img_container.pack_propagate(False)
        img_container.pack(side=tk.LEFT)
        self.bind_select(img_container, id_inmueble)

        img_label = tk.Label(img_container, text="Sin imagen", bg="#f1f2f6", fg="#a4b0be", font=("Segoe UI", 9))
        img_label.pack(fill=tk.BOTH, expand=True)
        self.bind_select(img_label, id_inmueble)

        if img_path and os.path.exists(img_path):
            try:
                img = Image.open(img_path)
                img.thumbnail((180, 120))
                tk_img = ImageTk.PhotoImage(img)
                img_label.config(image=tk_img, text="")
                self.images.append(tk_img)
            except: pass

        # Info
        info_frame = tk.Frame(inner, bg="white", padx=25)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.bind_select(info_frame, id_inmueble)

        tk.Label(info_frame, text=nombre.upper(), font=("Segoe UI", 13, "bold"), bg="white", fg="#2c3e50").pack(anchor="w")
        
        tags_f = tk.Frame(info_frame, bg="white")
        tags_f.pack(anchor="w", pady=5)
        self.bind_select(tags_f, id_inmueble)
        
        type_tag = tk.Frame(tags_f, bg="#e8f4fd", padx=8, pady=2)
        type_tag.pack(side=tk.LEFT)
        tk.Label(type_tag, text=tipo, font=("Segoe UI", 9, "bold"), bg="#e8f4fd", fg="#3498db").pack()
        self.bind_select(type_tag, id_inmueble)
        
        # Nuevos iconos de detalle
        details_str = f"🛏️ {dorms} | 🛌 {camas} | 🚿 {banos}"
        details_tag = tk.Frame(tags_f, bg="#f5f6fa", padx=8, pady=2)
        details_tag.pack(side=tk.LEFT, padx=10)
        tk.Label(details_tag, text=details_str, font=("Segoe UI", 9, "bold"), bg="#f5f6fa", fg="#7f8c8d").pack()
        self.bind_select(details_tag, id_inmueble)
        
        tk.Label(info_frame, text=f"👥 Capacidad: {capacidad} personas", font=("Segoe UI", 10), bg="white", fg="#7f8c8d").pack(anchor="w")
        tk.Label(info_frame, text=f"📍 {direccion}, {localidad} ({provincia})", font=("Segoe UI", 9), bg="white", fg="#57606f").pack(anchor="w", pady=(5, 0))

        # Precio
        price_frame = tk.Frame(inner, bg="white", padx=10)
        price_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.bind_select(price_frame, id_inmueble)

        tk.Label(price_frame, text=f"ID #{id_inmueble}", font=("Segoe UI", 8, "bold"), bg="white", fg="#dfe4ea").pack(anchor="e")
        
        try:
            val = float(valor_dia)
            formatted = f"{val:,.2f}"
            m, d = formatted.split('.')
            valor_fmt = f"${m.replace(',', '.')},{d}"
        except: valor_fmt = str(valor_dia)

        tk.Label(price_frame, text=valor_fmt, font=("Segoe UI", 16, "bold"), bg="white", fg="#27ae60").pack(anchor="e", pady=(15, 0))
        tk.Label(price_frame, text="POR NOCHE", font=("Segoe UI", 8, "bold"), bg="white", fg="#a4b0be").pack(anchor="e")

        card.id_inmueble = id_inmueble
        card.search_data = f"{nombre} {tipo} {direccion} {localidad} {provincia}".lower()
        card.tipo = tipo.lower()
        self.cards.append(card)

    def filter_cards(self):
        query = self.search_var.get().lower()
        tipo_sel = self.type_filter.get().lower()
        visible_count = 0
        for card in self.cards:
            match_query = query in card.search_data or query in str(card.id_inmueble)
            match_type = tipo_sel == "todos" or tipo_sel in card.tipo
            if match_query and match_type:
                card.pack(fill=tk.X, padx=5, pady=8)
                visible_count += 1
            else:
                card.pack_forget()
        self.lbl_stats.config(text=f"MOSTRANDO: {visible_count} / TOTAL: {len(self.cards)} INMUEBLES")

    def select_card(self, id_inmueble):
        self.selected_id = id_inmueble
        for c in self.cards:
            is_sel = hasattr(c, 'id_inmueble') and c.id_inmueble == id_inmueble
            c.configure(highlightbackground="#3498db" if is_sel else "#d1d8e0", highlightthickness=2 if is_sel else 1)
            bg_color = "#f1f9ff" if is_sel else "white"
            for w in c.winfo_children(): # inner
                w.configure(bg=bg_color)
                for sub in w.winfo_children():
                    if isinstance(sub, tk.Frame):
                        if "e8f4fd" not in str(sub.cget("background")):
                            sub.configure(bg=bg_color)
                            for g in sub.winfo_children():
                                try: g.configure(bg=bg_color)
                                except: pass
                    else:
                        try: sub.configure(bg=bg_color)
                        except: pass

    def load_properties(self):
        for w in self.scrollable.winfo_children(): w.destroy()
        self.cards = []; self.images = []
        if not self.db.connect(): return
        props = self.db.get_all_properties()
        for prop in props: self.create_card(prop)
        self.lbl_stats.config(text=f"TOTAL: {len(props)} INMUEBLES")
        self.filter_cards()

    def edit_property_by_id(self, id_inmueble):
        EditPropertyWindow(self.master, id_inmueble, self)

    def delete_property(self):
        pid = self.get_selected_id()
        if pid is None: return
        if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar el inmueble #{pid}?", parent=self.window):
            pc = PropertyController()
            if pc.delete_property(pid):
                messagebox.showinfo("Éxito", "Inmueble eliminado correctamente", parent=self.window)
                self.load_properties()

    def edit_property(self):
        pid = self.get_selected_id()
        if pid: self.edit_property_by_id(pid)

    def refresh_properties(self):
        self.selected_id = None
        self.load_properties()

    def get_selected_id(self):
        if self.selected_id: return self.selected_id
        messagebox.showwarning("Advertencia", "Seleccione un inmueble", parent=self.window)
        return None

    def show(self): pass
