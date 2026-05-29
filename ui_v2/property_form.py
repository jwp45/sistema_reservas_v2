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
        self.resize(650, 800)
        
        self.init_ui()
        if self.property_id:
            self.load_property_data()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("background-color: #2c3e50;")
        h_layout = QHBoxLayout(header)
        title = QLabel(self.windowTitle().upper())
        title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        h_layout.addWidget(title)
        self.main_layout.addWidget(header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)
        
        # --- INFO SECTION ---
        sec_info = self._create_section("🏨 INFORMACIÓN GENERAL")
        info_form = QFormLayout()
        
        self.edit_name = QLineEdit()
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Casa", "Departamento", "Cabaña", "Habitación", "Quinta"])
        
        self.spin_people = QSpinBox()
        self.spin_people.setRange(1, 50)
        
        self.edit_price = QLineEdit()
        self.edit_price.setPlaceholderText("0.00")
        
        info_form.addRow("Nombre:", self.edit_name)
        info_form.addRow("Tipo:", self.combo_tipo)
        info_form.addRow("Capacidad:", self.spin_people)
        info_form.addRow("Precio/Noche:", self.edit_price)
        
        sec_info.layout().addLayout(info_form)
        
        # Distribution
        dist_layout = QHBoxLayout()
        self.spin_dorms = QSpinBox()
        self.spin_beds = QSpinBox()
        self.spin_baths = QSpinBox()
        for s in [self.spin_dorms, self.spin_beds, self.spin_baths]: s.setRange(0, 20)
        
        dist_layout.addWidget(QLabel("Dorms:"))
        dist_layout.addWidget(self.spin_dorms)
        dist_layout.addWidget(QLabel("Camas:"))
        dist_layout.addWidget(self.spin_beds)
        dist_layout.addWidget(QLabel("Baños:"))
        dist_layout.addWidget(self.spin_baths)
        sec_info.layout().addLayout(dist_layout)
        
        self.layout.addWidget(sec_info)
        
        # --- LOCATION SECTION ---
        sec_loc = self._create_section("📍 UBICACIÓN")
        loc_form = QFormLayout()
        self.edit_address = QLineEdit()
        self.edit_city = QLineEdit()
        self.edit_prov = QLineEdit("Buenos Aires")
        
        loc_form.addRow("Dirección:", self.edit_address)
        loc_form.addRow("Localidad:", self.edit_city)
        loc_form.addRow("Provincia:", self.edit_prov)
        sec_loc.layout().addLayout(loc_form)
        self.layout.addWidget(sec_loc)
        
        # --- SERVICES SECTION ---
        sec_serv = self._create_section("✨ SERVICIOS")
        serv_add_layout = QHBoxLayout()
        self.combo_icon = QComboBox()
        self.combo_icon.addItems(["✨", "📶", "❄️", "🌡️", "🔥", "🌀", "🐾", "🍳", "☕", "🥐", "🥘", "🍝", "🍱", "🅿️", "🏊", "📺", "🚿", "🧺", "🧼", "🛏️", "🛌", "🚫", "🍖", "🧴", "🛡️", "🚲"])
        self.edit_serv_name = QLineEdit()
        self.edit_serv_name.setPlaceholderText("Nombre del servicio...")
        btn_add_serv = QPushButton("Añadir")
        btn_add_serv.clicked.connect(self.add_service)
        
        serv_add_layout.addWidget(self.combo_icon)
        serv_add_layout.addWidget(self.edit_serv_name)
        serv_add_layout.addWidget(btn_add_serv)
        sec_serv.layout().addLayout(serv_add_layout)
        
        self.list_services = QListWidget()
        self.list_services.setFixedHeight(100)
        sec_serv.layout().addWidget(self.list_services)
        
        btn_rem_serv = QPushButton("Eliminar Seleccionado")
        btn_rem_serv.clicked.connect(lambda: self.list_services.takeItem(self.list_services.currentRow()))
        sec_serv.layout().addWidget(btn_rem_serv)
        
        self.layout.addWidget(sec_serv)
        
        # --- MULTIMEDIA SECTION ---
        sec_multi = self._create_section("🖼️ MULTIMEDIA")
        btn_img = QPushButton("Seleccionar Imagen Principal")
        btn_img.clicked.connect(self.select_image)
        sec_multi.layout().addWidget(btn_img)
        
        self.img_preview = QLabel("Sin Imagen")
        self.img_preview.setFixedSize(200, 120)
        self.img_preview.setStyleSheet("background-color: #f0f2f5; border: 1px solid #ddd;")
        self.img_preview.setScaledContents(True)
        sec_multi.layout().addWidget(self.img_preview, 0, Qt.AlignCenter)
        
        btn_gal = QPushButton("Añadir a Galería")
        btn_gal.clicked.connect(self.select_gallery)
        sec_multi.layout().addWidget(btn_gal)
        self.lbl_gal = QLabel("0 fotos en galería")
        sec_multi.layout().addWidget(self.lbl_gal)
        
        self.layout.addWidget(sec_multi)
        
        scroll.setWidget(content)
        self.main_layout.addWidget(scroll)
        
        # Actions
        btns = QFrame()
        btns.setFixedHeight(80)
        btns.setStyleSheet("background-color: #f8f9fa; border-top: 1px solid #ddd;")
        btns_layout = QHBoxLayout(btns)
        btn_cancel = QPushButton("CANCELAR")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("GUARDAR INMUEBLE")
        btn_save.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_save.setFixedHeight(40)
        btn_save.clicked.connect(self.save_property)
        
        btns_layout.addWidget(btn_cancel)
        btns_layout.addStretch()
        btns_layout.addWidget(btn_save)
        self.main_layout.addWidget(btns)

    def _create_section(self, title):
        frame = QFrame()
        frame.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #e0e0e0;")
        layout = QVBoxLayout(frame)
        lbl = QLabel(title)
        lbl.setStyleSheet("font-weight: bold; color: #7f8c8d; font-size: 11px; border: none;")
        layout.addWidget(lbl)
        return frame

    def add_service(self):
        name = self.edit_serv_name.text().strip()
        if name:
            self.list_services.addItem(f"{self.combo_icon.currentText()} {name}")
            self.edit_serv_name.clear()

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
