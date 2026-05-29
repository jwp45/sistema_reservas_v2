from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QScrollArea, QMessageBox,
                             QGridLayout, QApplication)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPixmap
from controllers.database import Database
import os
from ui_v2.property_form import PropertyFormDialog
from ui_v2.gallery_dialog import GalleryDialog

class PropertyCard(QFrame):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data # p = (id, nombre, capacidad, direccion, localidad, provincia, tipo, valor_dia, img_path, dorms, camas, banos)
        self.init_ui()

    def init_ui(self):
        self.setFixedHeight(180)
        self.setStyleSheet("""
            #PropertyCard {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #eef0f2;
            }
            #PropertyCard:hover {
                border: 1px solid #27ae60;
                background-color: #f7fff9;
            }
        """)
        self.setObjectName("PropertyCard")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)

        # 1. Image Thumbnail
        self.img_label = QLabel()
        self.img_label.setFixedSize(220, 150)
        self.img_label.setStyleSheet("background-color: #f0f2f5; border-radius: 10px; border: none;")
        self.img_label.setAlignment(Qt.AlignCenter)
        
        img_path = self.data[8]
        if img_path and os.path.exists(img_path):
            pix = QPixmap(img_path)
            self.img_label.setPixmap(pix.scaled(220, 150, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            self.img_label.setText("🏠\nSIN IMAGEN")
            self.img_label.setStyleSheet("background-color: #f0f2f5; border-radius: 10px; color: #bdc3c7; font-weight: bold; border: none;")
        
        main_layout.addWidget(self.img_label)

        # 2. Property Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        lbl_name = QLabel(str(self.data[1]).upper())
        lbl_name.setStyleSheet("font-size: 18px; font-weight: 800; color: #2c3e50; border: none;")
        
        lbl_loc = QLabel(f"📍 {self.data[4]}, {self.data[5]}")
        lbl_loc.setStyleSheet("font-size: 13px; color: #34495e; border: none;")
        
        lbl_type = QLabel(f"🏷️ {self.data[6]}")
        lbl_type.setStyleSheet("font-size: 12px; color: #7f8c8d; font-weight: bold; border: none;")
        
        lbl_capacity = QLabel(f"👥 {self.data[2]} pers. | 🛏️ {self.data[9]} Dorms | 😴 {self.data[10]} Camas | 🚿 {self.data[11]} Baños")
        lbl_capacity.setStyleSheet("font-size: 12px; color: #7f8c8d; border: none;")
        
        info_layout.addWidget(lbl_name)
        info_layout.addWidget(lbl_loc)
        info_layout.addWidget(lbl_type)
        info_layout.addWidget(lbl_capacity)
        info_layout.addStretch()
        main_layout.addLayout(info_layout, 1)

        # 3. Price & Actions
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignRight)
        
        lbl_price_title = QLabel("VALOR / NOCHE")
        lbl_price_title.setStyleSheet("font-size: 10px; font-weight: bold; color: #95a5a6; border: none;")
        
        lbl_price = QLabel(self.format_currency(self.data[7]))
        lbl_price.setStyleSheet("font-size: 24px; font-weight: 800; color: #27ae60; border: none;")
        
        right_layout.addWidget(lbl_price_title, 0, Qt.AlignRight)
        right_layout.addWidget(lbl_price, 0, Qt.AlignRight)
        right_layout.addStretch()

        # Action Buttons Row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        self.btn_gallery = QPushButton("🖼️ FOTOS")
        self.btn_gallery.setFixedSize(85, 35)
        self.btn_gallery.setCursor(Qt.PointingHandCursor)
        self.btn_gallery.setStyleSheet("""
            QPushButton { background-color: #34495e; color: white; font-weight: bold; border-radius: 8px; font-size: 10px; }
            QPushButton:hover { background-color: #2c3e50; }
        """)
        
        self.btn_edit = QPushButton("✏️ EDITAR")
        self.btn_edit.setFixedSize(85, 35)
        self.btn_edit.setCursor(Qt.PointingHandCursor)
        self.btn_edit.setStyleSheet("""
            QPushButton { background-color: #3498db; color: white; font-weight: bold; border-radius: 8px; font-size: 10px; }
            QPushButton:hover { background-color: #2980b9; }
        """)
        
        self.btn_delete = QPushButton("🗑️")
        self.btn_delete.setFixedSize(35, 35)
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setStyleSheet("""
            QPushButton { background-color: #fceaea; color: #e74c3c; border: none; border-radius: 8px; }
            QPushButton:hover { background-color: #f8d7da; }
        """)
        
        btn_layout.addWidget(self.btn_gallery)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        
        right_layout.addLayout(btn_layout)
        main_layout.addLayout(right_layout)

    def format_currency(self, val):
        return f"${float(val):,.0f}".replace(",", ".")

class PropertyListPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.all_properties = []
        
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        
        title_container = QVBoxLayout()
        title = QLabel("Catálogo de Inmuebles")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #2c3e50;")
        self.lbl_stats = QLabel("Cargando inventario...")
        self.lbl_stats.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        title_container.addWidget(title)
        title_container.addWidget(self.lbl_stats)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por nombre, dirección o tipo...")
        self.search_input.setFixedWidth(400)
        self.search_input.setFixedHeight(45)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding-left: 20px;
                border-radius: 22px;
                border: 1px solid #d1d8e0;
                background-color: white;
                color: #2c3e50;
                font-size: 14px;
            }
            QLineEdit:focus { border: 2px solid #3498db; }
        """)
        self.search_input.textChanged.connect(self.filter_cards)

        btn_add = QPushButton("➕ NUEVO INMUEBLE")
        btn_add.setFixedSize(190, 45)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton { background-color: #27ae60; color: white; border-radius: 22px; font-weight: bold; }
            QPushButton:hover { background-color: #219150; }
        """)
        btn_add.clicked.connect(self.add_property)

        btn_refresh = QPushButton("🔄 REFRESCAR")
        btn_refresh.setFixedSize(140, 45)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet("""
            QPushButton { background-color: white; border: 1px solid #d1d8e0; border-radius: 22px; font-weight: bold; color: #34495e; }
            QPushButton:hover { background-color: #f8f9fa; border: 1px solid #3498db; }
        """)
        btn_refresh.clicked.connect(self.load_data)

        header_layout.addLayout(title_container)
        header_layout.addStretch()
        header_layout.addWidget(self.search_input)
        header_layout.addWidget(btn_add)
        header_layout.addWidget(btn_refresh)
        layout.addLayout(header_layout)

        # --- SCROLL AREA FOR CARDS ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("background-color: transparent;")
        
        self.container = QWidget()
        self.container.setStyleSheet("background-color: transparent;")
        self.cards_layout = QVBoxLayout(self.container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(15)
        self.cards_layout.addStretch() # Inicialmente vacío
        
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

    def load_data(self):
        if not self.db.connect(): return
        self.all_properties = self.db.get_all_properties()
        self.display_properties(self.all_properties)
        self.lbl_stats.setText(f"Total: {len(self.all_properties)} inmuebles en catálogo")

    def display_properties(self, data):
        # Clear existing cards
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        for p in data:
            card = PropertyCard(p)
            # Connect integrated buttons
            card.btn_gallery.clicked.connect(lambda chk=False, prop=p: self.open_gallery(prop))
            card.btn_edit.clicked.connect(lambda chk=False, prop=p: self.edit_property(prop))
            card.btn_delete.clicked.connect(lambda chk=False, prop=p: self.delete_property(prop))
            
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def filter_cards(self):
        query = self.search_input.text().lower()
        if not query:
            self.display_properties(self.all_properties)
            return
            
        filtered = [p for p in self.all_properties if any(query in str(field).lower() for field in p)]
        self.display_properties(filtered)

    def add_property(self):
        dialog = PropertyFormDialog(self)
        if dialog.exec():
            self.load_data()

    def edit_property(self, p):
        dialog = PropertyFormDialog(self, property_id=p[0])
        if dialog.exec():
            self.load_data()

    def delete_property(self, p):
        prop_id = p[0]
        prop_name = p[1]
        reply = QMessageBox.question(self, "Confirmar Eliminación", 
                                   f"¿Está seguro de eliminar el inmueble #{prop_id} ({prop_name})?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.db.delete_property(prop_id):
                self.load_data()
                QMessageBox.information(self, "Éxito", "Inmueble eliminado correctamente.")

    def open_gallery(self, p):
        if not self.db.connect(): return
        images = self.db.get_gallery_images(p[0])
        image_paths = [img[1] for img in images]
        
        dialog = GalleryDialog(self, property_name=p[1], image_paths=image_paths)
        dialog.exec()
