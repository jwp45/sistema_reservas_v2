import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import webbrowser
import urllib.parse
from utils.email_sender import send_gallery_email

class GalleryWindow:
    def __init__(self, master, property_name, image_paths, client_email=None, client_phone=None):
        self.master = master
        self.property_name = property_name
        self.image_paths = image_paths # Lista de rutas de archivos
        self.client_email = client_email
        self.client_phone = client_phone
        self.current_index = 0
        
        self.window = tk.Toplevel(master)
        self.window.title(f"Galería de Fotos - {property_name}")
        self.window.geometry("900x700")
        self.window.configure(bg="#1a1a1a")
        self.window.transient(master)
        self.window.grab_set()

        self.setup_ui()
        self.show_image()

    def setup_ui(self):
        # Header con info
        self.header = tk.Frame(self.window, bg="#1a1a1a", pady=10)
        self.header.pack(fill=tk.X)
        
        self.lbl_title = tk.Label(self.header, text=self.property_name.upper(), 
                                 font=("Segoe UI", 14, "bold"), bg="#1a1a1a", fg="white")
        self.lbl_title.pack()
        
        self.lbl_count = tk.Label(self.header, text="", font=("Segoe UI", 10), bg="#1a1a1a", fg="#95a5a6")
        self.lbl_count.pack()

        # Área de imagen central
        self.img_container = tk.Frame(self.window, bg="#1a1a1a")
        self.img_container.pack(fill=tk.BOTH, expand=True)
        
        self.lbl_image = tk.Label(self.img_container, bg="#1a1a1a")
        self.lbl_image.pack(fill=tk.BOTH, expand=True)

        # Controles
        controls = tk.Frame(self.window, bg="#1a1a1a", pady=20)
        controls.pack(fill=tk.X)
        
        btn_style = {"font": ("Segoe UI", 12, "bold"), "bg": "#333", "fg": "white", 
                     "relief": tk.FLAT, "padx": 20, "pady": 10, "cursor": "hand2"}
        
        self.btn_prev = tk.Button(controls, text="◀ ANTERIOR", command=self.prev_image, **btn_style)
        self.btn_prev.pack(side=tk.LEFT, padx=50)
        
        self.btn_next = tk.Button(controls, text="SIGUIENTE ▶", command=self.next_image, **btn_style)
        self.btn_next.pack(side=tk.RIGHT, padx=50)

        # Frame para botones de compartir
        share_frame = tk.Frame(controls, bg="#1a1a1a")
        share_frame.pack(pady=5)

        self.btn_share_email = tk.Button(share_frame, text="📧 COMPARTIR EMAIL", command=self.share_by_email,
                                  font=("Segoe UI", 10, "bold"), bg="#2c3e50", fg="white", 
                                  relief=tk.FLAT, padx=15, pady=8, cursor="hand2")
        self.btn_share_email.pack(side=tk.LEFT, padx=10)

        self.btn_share_ws = tk.Button(share_frame, text="💬 WHATSAPP", command=self.share_by_whatsapp,
                                  font=("Segoe UI", 10, "bold"), bg="#25D366", fg="white", 
                                  relief=tk.FLAT, padx=15, pady=8, cursor="hand2")
        self.btn_share_ws.pack(side=tk.LEFT, padx=10)
        
        # Atajos de teclado
        self.window.bind("<Left>", lambda e: self.prev_image())
        self.window.bind("<Right>", lambda e: self.next_image())
        self.window.bind("<Escape>", lambda e: self.window.destroy())

    def show_image(self):
        if not self.image_paths:
            self.lbl_image.config(text="No hay imágenes en la galería", fg="white", font=("Segoe UI", 14))
            self.lbl_count.config(text="0 / 0")
            self.btn_prev.config(state=tk.DISABLED)
            self.btn_next.config(state=tk.DISABLED)
            return

        path = self.image_paths[self.current_index]
        self.lbl_count.config(text=f"Imagen {self.current_index + 1} de {len(self.image_paths)}")
        
        try:
            if os.path.exists(path):
                img = Image.open(path)
                
                # Redimensionar dinámicamente al tamaño de la ventana
                win_w = self.window.winfo_width() if self.window.winfo_width() > 1 else 900
                win_h = self.window.winfo_height() - 150 # Descontar header y controles
                if win_h < 1: win_h = 550
                
                img.thumbnail((win_w - 40, win_h))
                tk_img = ImageTk.PhotoImage(img)
                
                self.lbl_image.config(image=tk_img, text="")
                self.lbl_image.image = tk_img
            else:
                self.lbl_image.config(image="", text="Archivo no encontrado", fg="red")
        except Exception as e:
            self.lbl_image.config(image="", text=f"Error: {str(e)}", fg="red")

    def prev_image(self):
        if self.image_paths:
            self.current_index = (self.current_index - 1) % len(self.image_paths)
            self.show_image()

    def next_image(self):
        if self.image_paths:
            self.current_index = (self.current_index + 1) % len(self.image_paths)
            self.show_image()

    def share_by_whatsapp(self):
        """Abre WhatsApp con un mensaje pre-cargado para el cliente."""
        phone = self.client_phone
        if not phone:
            phone = simpledialog.askstring("WhatsApp del Cliente", 
                                          "Ingrese el número (con código de país, ej: 549...):",
                                          parent=self.window)
        
        if not phone: return

        # Limpiar número: dejar solo dígitos
        clean_phone = "".join(filter(str.isdigit, phone))
        
        # Asegurar prefijo (asumiendo Argentina si no tiene, puedes ajustar esto)
        if len(clean_phone) == 10: # Nro local sin prefijo
            clean_phone = "549" + clean_phone
        
        message = f"¡Hola! Te comparto las fotos de {self.property_name} que solicitaste. ¡Quedo atento a tus dudas!"
        encoded_msg = urllib.parse.quote(message)
        
        url = f"https://wa.me/{clean_phone}?text={encoded_msg}"
        
        try:
            webbrowser.open(url)
            messagebox.showinfo("WhatsApp", "Se ha abierto WhatsApp. Ahora puedes adjuntar las fotos manualmente en el chat.", parent=self.window)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el navegador: {e}")

    def share_by_email(self):
        """Abre un diálogo visual para elegir qué imágenes enviar por email."""
        if not self.image_paths:
            messagebox.showwarning("Atención", "No hay imágenes para compartir.")
            return

        # Ventana de selección
        selection_win = tk.Toplevel(self.window)
        selection_win.title("Seleccionar Fotos para Enviar")
        selection_win.geometry("500x600")
        selection_win.configure(bg="#f8f9fa")
        selection_win.transient(self.window)
        selection_win.grab_set()

        tk.Label(selection_win, text="✉️ SELECCIONAR FOTOS", font=("Segoe UI", 12, "bold"), 
                 bg="#2c3e50", fg="white", pady=10).pack(fill=tk.X)

        # Contenedor con Scroll
        container = tk.Frame(selection_win, bg="#f8f9fa")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(container, bg="#f8f9fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#f8f9fa")

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=460)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Lista de variables para los checkboxes
        vars_map = [] # List of (path, BooleanVar)

        # Generar miniaturas para la selección
        self.selection_thumbnails = [] # Mantener referencia para evitar GC

        for path in self.image_paths:
            item_f = tk.Frame(scroll_frame, bg="white", pady=5, padx=10, relief=tk.RIDGE, bd=1)
            item_f.pack(fill=tk.X, pady=2)

            var = tk.BooleanVar(value=True)
            chk = tk.Checkbutton(item_f, variable=var, bg="white", activebackground="white")
            chk.pack(side=tk.LEFT)

            try:
                img = Image.open(path)
                img.thumbnail((80, 60))
                tk_img = ImageTk.PhotoImage(img)
                self.selection_thumbnails.append(tk_img)
                
                lbl_thumb = tk.Label(item_f, image=tk_img, bg="white")
                lbl_thumb.pack(side=tk.LEFT, padx=10)
            except:
                tk.Label(item_f, text="🖼️", bg="white").pack(side=tk.LEFT, padx=10)

            tk.Label(item_f, text=os.path.basename(path), bg="white", font=("Segoe UI", 9)).pack(side=tk.LEFT)
            vars_map.append((path, var))

        def proceed():
            selected_paths = [path for path, var in vars_map if var.get()]
            if not selected_paths:
                messagebox.showwarning("Atención", "Seleccione al menos una imagen.")
                return

            email = self.client_email
            if not email:
                email = simpledialog.askstring("Email del Cliente", 
                                              "Ingrese el email del destinatario:",
                                              parent=selection_win)
            if not email: return

            selection_win.config(cursor="watch")
            selection_win.update()
            
            success = send_gallery_email(email, self.property_name, selected_paths)
            
            selection_win.config(cursor="")
            if success:
                messagebox.showinfo("Éxito", f"¡Se han enviado {len(selected_paths)} fotos a {email}!", parent=selection_win)
                selection_win.destroy()
            else:
                messagebox.showerror("Error", "No se pudo enviar el correo. Verifique la configuración SMTP.", parent=selection_win)

        # Footer
        footer = tk.Frame(selection_win, bg="#f8f9fa", pady=15)
        footer.pack(fill=tk.X)
        
        btn_send = tk.Button(footer, text="ENVIAR SELECCIONADAS", command=proceed,
                            font=("Segoe UI", 11, "bold"), bg="#27ae60", fg="white", 
                            relief=tk.FLAT, pady=10, padx=30, cursor="hand2")
        btn_send.pack()
