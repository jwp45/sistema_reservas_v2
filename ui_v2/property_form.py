from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QMessageBox, 
                             QFrame, QComboBox, QSpinBox, QScrollArea, QWidget,
                             QListWidget, QFileDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from controllers.database import Database
import os
import shutil
from datetime import datetime

class PropertyFormDialog(QDialog):
    def __init__(self, parent=None, property_id=None):
        super().__init__(parent)
        self.db = Database()
        self.property_id = property_id
        self.imagen_path = ""
        self.gallery_paths = []
        
        self.setWindowTitle("Nuevo Inmueble" if not self.property_id else f"Editar Inmueble #{self.property_id}")
        self.resize(800, 850) # Aumentado de 650x800 a 800x850
        
        self.init_ui()
        if self.property_id:
            self.load_property_data()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Estilos generales para inputs
        self.setStyleSheet("""
            QLineEdit, QSpinBox, QComboBox {
                border: 1px solid #d1d8e0;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
                color: #2c3e50;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 2px solid #3498db;
            }
            QLabel { color: #34495e; font-weight: 500; }
        """)

        # Header
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #2c3e50; border: none;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(30, 0, 30, 0)
        
        title_icon = "🏠" if not self.property_id else "✏️"
        title = QLabel(f"{title_icon} {self.windowTitle().upper()}")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: 800; border: none;")
        h_layout.addWidget(title)
        self.main_layout.addWidget(header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: #f0f2f5;")
        
        content = QWidget()
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(40, 30, 40, 30)
        self.layout.setSpacing(25)
        
        # --- INFO SECTION ---
        sec_info = self._create_section("🏨 INFORMACIÓN GENERAL")
        info_layout = QVBoxLayout(sec_info)
        info_layout.setContentsMargins(25, 45, 25, 25) # Margen extra arriba para el título de sección
        info_layout.setSpacing(15)

        row1 = QHBoxLayout()
        vbox_name = QVBoxLayout()
        vbox_name.addWidget(QLabel("Nombre del Inmueble:"))
        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("Ej: Cabaña Los Pinos")
        vbox_name.addWidget(self.edit_name)
        row1.addLayout(vbox_name, 2)

        vbox_tipo = QVBoxLayout()
        vbox_tipo.addWidget(QLabel("Tipo:"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Casa", "Departamento", "Cabaña", "Habitación", "Quinta"])
        vbox_tipo.addWidget(self.combo_tipo)
        row1.addLayout(vbox_tipo, 1)
        info_layout.addLayout(row1)

        row2 = QHBoxLayout()
        vbox_cap = QVBoxLayout()
        vbox_cap.addWidget(QLabel("Capacidad:"))
        self.spin_people = QSpinBox()
        self.spin_people.setRange(1, 50)
        vbox_cap.addWidget(self.spin_people)
        row2.addLayout(vbox_cap)

        vbox_price = QVBoxLayout()
        vbox_price.addWidget(QLabel("Precio por Noche:"))
        self.edit_price = QLineEdit()
        self.edit_price.setPlaceholderText("0.00")
        vbox_price.addWidget(self.edit_price)
        row2.addLayout(vbox_price)
        info_layout.addLayout(row2)
        
        # Distribution
        dist_lbl = QLabel("Distribución de Camas y Baños:")
        dist_lbl.setStyleSheet("font-weight: bold; color: #7f8c8d; font-size: 12px; margin-top: 5px;")
        info_layout.addWidget(dist_lbl)
        
        dist_layout = QHBoxLayout()
        self.spin_dorms = QSpinBox()
        self.spin_beds = QSpinBox()
        self.spin_baths = QSpinBox()
        for s, label in [(self.spin_dorms, "Dorms"), (self.spin_beds, "Camas"), (self.spin_baths, "Baños")]:
            s.setRange(0, 20)
            vbox = QVBoxLayout()
            vbox.addWidget(QLabel(label))
            vbox.addWidget(s)
            dist_layout.addLayout(vbox)
        
        info_layout.addLayout(dist_layout)
        self.layout.addWidget(sec_info)
        
        # --- LOCATION SECTION ---
        sec_loc = self._create_section("📍 UBICACIÓN")
        loc_layout = QVBoxLayout(sec_loc)
        loc_layout.setContentsMargins(25, 45, 25, 25)
        loc_layout.setSpacing(15)

        self.edit_address = QLineEdit()
        self.edit_address.setPlaceholderText("Calle y número...")
        loc_layout.addWidget(QLabel("Dirección:"))
        loc_layout.addWidget(self.edit_address)

        row_loc = QHBoxLayout()
        vbox_city = QVBoxLayout()
        vbox_city.addWidget(QLabel("Localidad:"))
        self.edit_city = QLineEdit()
        vbox_city.addWidget(self.edit_city)
        row_loc.addLayout(vbox_city)

        vbox_prov = QVBoxLayout()
        vbox_prov.addWidget(QLabel("Provincia:"))
        self.edit_prov = QLineEdit("Buenos Aires")
        vbox_prov.addWidget(self.edit_prov)
        row_loc.addLayout(vbox_prov)
        loc_layout.addLayout(row_loc)
        
        self.layout.addWidget(sec_loc)
        
        # --- SERVICES SECTION ---
        sec_serv = self._create_section("✨ SERVICIOS Y AMENITIES")
        serv_layout = QVBoxLayout(sec_serv)
        serv_layout.setContentsMargins(25, 45, 25, 25)
        serv_layout.setSpacing(15)

        serv_add_layout = QHBoxLayout()
        serv_add_layout.setSpacing(10)
        
        # Selector de Icono más ancho para que se vean bien
        vbox_icon = QVBoxLayout()
        vbox_icon.addWidget(QLabel("Icono:"))
        self.combo_icon = QComboBox()
        self.combo_icon.setFixedWidth(80) # Un poco más ancho y estilizado
        self.combo_icon.addItems(["✨", "📶", "❄️", "🌡️", "🔥", "🌀", "🐾", "🍳", "☕", "🥐", "🥘", "🍝", "🍱", "🅿️", "🏊", "📺", "🚿", "🧺", "🧼", "🛏️", "🛌", "🚫", "🍖", "🧴", "🛡️", "🚲"])
        self.combo_icon.setStyleSheet("font-size: 16px;") # Iconos más grandes
        vbox_icon.addWidget(self.combo_icon)
        serv_add_layout.addLayout(vbox_icon)

        vbox_serv_name = QVBoxLayout()
        vbox_serv_name.addWidget(QLabel("Nuevo Servicio:"))
        self.edit_serv_name = QLineEdit()
        self.edit_serv_name.setPlaceholderText("Nombre del servicio (ej: WiFi 5G)...")
        vbox_serv_name.addWidget(self.edit_serv_name)
        serv_add_layout.addLayout(vbox_serv_name)
        
        btn_add_serv = QPushButton("Añadir")
        btn_add_serv.setFixedSize(90, 38)
        btn_add_serv.setCursor(Qt.PointingHandCursor)
        btn_add_serv.setStyleSheet("background-color: #34495e; color: white; font-weight: bold; margin-top: 20px;")
        btn_add_serv.clicked.connect(self.add_service)
        serv_add_layout.addWidget(btn_add_serv)
        
        serv_layout.addLayout(serv_add_layout)
        
        self.list_services = QListWidget()
        self.list_services.setFixedHeight(150) # Más alto para visibilidad
        self.list_services.setStyleSheet("""
            QListWidget { border-radius: 8px; padding: 5px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #f0f2f5; }
        """)
        serv_layout.addWidget(self.list_services)
        
        btn_rem_serv = QPushButton("🗑️ ELIMINAR SERVICIO SELECCIONADO")
        btn_rem_serv.setCursor(Qt.PointingHandCursor)
        btn_rem_serv.setStyleSheet("color: #e74c3c; font-weight: bold; border: 1px solid #f8d7da; height: 35px;")
        btn_rem_serv.clicked.connect(lambda: self.list_services.takeItem(self.list_services.currentRow()))
        serv_layout.addWidget(btn_rem_serv)
        
        self.layout.addWidget(sec_serv)
        
        # --- MULTIMEDIA SECTION ---
        sec_multi = self._create_section("🖼️ MULTIMEDIA Y GALERÍA")
        multi_layout = QVBoxLayout(sec_multi)
        multi_layout.setContentsMargins(25, 45, 25, 25)
        multi_layout.setSpacing(20)

        img_btns = QHBoxLayout()
        btn_img = QPushButton("📸 Imagen Principal")
        btn_img.setCursor(Qt.PointingHandCursor)
        btn_img.setFixedHeight(40)
        btn_img.clicked.connect(self.select_image)
        
        btn_gal = QPushButton("📂 Añadir a Galería")
        btn_gal.setCursor(Qt.PointingHandCursor)
        btn_gal.setFixedHeight(40)
        btn_gal.clicked.connect(self.select_gallery)
        
        img_btns.addWidget(btn_img)
        img_btns.addWidget(btn_gal)
        multi_layout.addLayout(img_btns)
        
        self.img_preview = QLabel("SIN IMAGEN PRINCIPAL")
        self.img_preview.setFixedSize(300, 180)
        self.img_preview.setAlignment(Qt.AlignCenter)
        self.img_preview.setStyleSheet("""
            background-color: white; 
            border: 2px dashed #d1d8e0; 
            border-radius: 10px;
            color: #7f8c8d;
            font-weight: bold;
        """)
        self.img_preview.setScaledContents(True)
        multi_layout.addWidget(self.img_preview, 0, Qt.AlignCenter)
        
        self.lbl_gal = QLabel("0 fotos en galería")
        self.lbl_gal.setAlignment(Qt.AlignCenter)
        self.lbl_gal.setStyleSheet("color: #3498db; font-weight: bold;")
        multi_layout.addWidget(self.lbl_gal)
        
        self.layout.addWidget(sec_multi)
        
        scroll.setWidget(content)
        self.main_layout.addWidget(scroll)
        
        # Actions
        btns = QFrame()
        btns.setFixedHeight(90)
        btns.setStyleSheet("background-color: white; border-top: 1px solid #e0e0e0;")
        btns_layout = QHBoxLayout(btns)
        btns_layout.setContentsMargins(30, 0, 30, 0)

        btn_cancel = QPushButton("CANCELAR")
        btn_cancel.setFixedSize(120, 45)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("background-color: #f8f9fa; border: 1px solid #d1d8e0; border-radius: 8px; color: #7f8c8d; font-weight: bold;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("💾 GUARDAR INMUEBLE")
        btn_save.setFixedSize(220, 45)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton { 
                background-color: #27ae60; 
                color: white; 
                font-weight: bold; 
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #219150; }
        """)
        btn_save.clicked.connect(self.save_property)
        
        btns_layout.addWidget(btn_cancel)
        btns_layout.addStretch()
        btns_layout.addWidget(btn_save)
        self.main_layout.addWidget(btns)

    def _create_section(self, title):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white; 
                border-radius: 15px; 
                border: 1px solid #eef0f2;
            }
        """)
        
        # Titulillo flotante para la sección
        lbl = QLabel(title, frame)
        lbl.setStyleSheet("""
            background-color: #f8f9fa; 
            color: #34495e; 
            font-weight: 800; 
            font-size: 11px; 
            border: 1px solid #eef0f2;
            border-radius: 10px;
            padding: 5px 15px;
        """)
        lbl.move(20, -12) # Posicionar sobre el borde superior
        
        return frame

    def add_service(self):
        name = self.edit_serv_name.text().strip()
        if name:
            self.list_services.addItem(f"{self.combo_icon.currentText()} {name}")
            self.edit_serv_name.clear()
            self.edit_serv_name.setFocus()

    def select_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Imagen Principal", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.imagen_path = path
            self.img_preview.setPixmap(QPixmap(path))

    def select_gallery(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Galería", "", "Images (*.png *.jpg *.jpeg)")
        if paths:
            self.gallery_paths.extend(paths)
            self.lbl_gal.setText(f"{len(self.gallery_paths)} fotos en galería")

    def load_property_data(self):
        if not self.db.connect(): return
        # p = (id, nombre, cap, dir, loc, prov, tipo, val, img, dorms, cams, banos)
        p = next((x for x in self.db.get_all_properties() if x[0] == self.property_id), None)
        if p:
            self.edit_name.setText(p[1])
            self.spin_people.setValue(p[2])
            self.edit_address.setText(p[3])
            self.edit_city.setText(p[4])
            self.edit_prov.setText(p[5])
            self.combo_tipo.setCurrentText(p[6])
            self.edit_price.setText(str(p[7]))
            if p[8] and os.path.exists(p[8]): self.img_preview.setPixmap(QPixmap(p[8]))
            self.spin_dorms.setValue(p[9])
            self.spin_beds.setValue(p[10])
            self.spin_baths.setValue(p[11])
            
            # Cargar servicios
            servs = self.db.get_property_services(self.property_id)
            for s in servs: self.list_services.addItem(f"{s[0]} {s[1]}")

    def save_property(self):
        if not self.edit_name.text(): return
        
        data = (
            self.edit_name.text(), self.spin_people.value(), self.edit_address.text(),
            self.edit_city.text(), self.edit_prov.text(), self.combo_tipo.currentText(),
            float(self.edit_price.text() or 0), self.spin_dorms.value(),
            self.spin_beds.value(), self.spin_baths.value()
        )
        
        if not self.db.connect(): return
        cursor = self.db.connection.cursor()
        
        if self.property_id:
            query = """UPDATE inmuebles SET nombre=%s, cantidad_personas=%s, direccion=%s, 
                       localidad=%s, provincia=%s, tipo=%s, valor_dia=%s, dormitorios=%s, 
                       camas=%s, baños=%s WHERE id_inmueble=%s"""
            cursor.execute(query, data + (self.property_id,))
            pid = self.property_id
        else:
            query = """INSERT INTO inmuebles (nombre, cantidad_personas, direccion, localidad, 
                       provincia, tipo, valor_dia, dormitorios, camas, baños) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(query, data)
            pid = cursor.lastrowid
            
        # Actualizar Servicios (Borrar y re-insertar para simplicidad)
        cursor.execute("DELETE FROM servicios_inmuebles WHERE id_inmueble=%s", (pid,))
        for i in range(self.list_services.count()):
            text = self.list_services.item(i).text()
            parts = text.split(" ", 1)
            icon = parts[0] if len(parts) > 1 else "✨"
            name = parts[1] if len(parts) > 1 else text
            cursor.execute("INSERT INTO servicios_inmuebles (id_inmueble, icono, nombre_servicio) VALUES (%s, %s, %s)", (pid, icon, name))
            
        # Manejo de imagen principal
        if self.imagen_path:
            assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "inmuebles")
            os.makedirs(assets_dir, exist_ok=True)
            ext = os.path.splitext(self.imagen_path)[1]
            dest = os.path.join(assets_dir, f"{pid}{ext}")
            shutil.copy2(self.imagen_path, dest)
            cursor.execute("UPDATE inmuebles SET imagen=%s WHERE id_inmueble=%s", (dest, pid))

        # Manejo de galería
        if self.gallery_paths:
            gallery_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "inmuebles", "gallery", str(pid))
            os.makedirs(gallery_dir, exist_ok=True)
            for path in self.gallery_paths:
                dest = os.path.join(gallery_dir, f"gal_{int(datetime.now().timestamp())}_{os.path.basename(path)}")
                try:
                    shutil.copy2(path, dest)
                    self.db.insert_gallery_image(pid, dest)
                except Exception as e:
                    print(f"Error al copiar imagen de galería: {e}")
            
        self.db.connection.commit()

        QMessageBox.information(self, "Éxito", "Inmueble guardado correctamente.")
        self.accept()
