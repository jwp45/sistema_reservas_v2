from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QScrollArea, QMessageBox,
                             QGridLayout, QApplication)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPixmap
from controllers.database import Database
import webbrowser
import urllib.parse
import os

class ProspectCard(QFrame):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data # p = (id, doc, nombre, apellido, email, tel, fecha_reg)
        self.init_ui()

    def init_ui(self):
        self.setFixedHeight(120)
        self.setStyleSheet("""
            #ProspectCard {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #eef0f2;
            }
            #ProspectCard:hover {
                border: 1px solid #f39c12;
                background-color: #fffaf0;
            }
        """)
        self.setObjectName("ProspectCard")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(25, 15, 25, 15)
        main_layout.setSpacing(20)

        # 1. Avatar / Icon (Different color for Leads)
        avatar = QLabel("🎯")
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("""
            background-color: #fff4e5;
            border-radius: 25px;
            font-size: 24px;
            border: none;
        """)
        main_layout.addWidget(avatar)

        # 2. Main Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        lbl_name = QLabel(f"{self.data[2]} {self.data[3]}".upper())
        lbl_name.setStyleSheet("font-size: 17px; font-weight: 800; color: #2c3e50; border: none;")
        
        f_reg = self.data[6].strftime("%d/%m/%Y") if hasattr(self.data[6], 'strftime') else str(self.data[6])
        lbl_doc = QLabel(f"📄 DNI: {self.data[1]} | 📅 Captado: {f_reg}")
        lbl_doc.setStyleSheet("font-size: 12px; color: #7f8c8d; border: none;")
        
        info_layout.addWidget(lbl_name)
        info_layout.addWidget(lbl_doc)
        main_layout.addLayout(info_layout, 1)

        # 3. Contact Info
        contact_layout = QVBoxLayout()
        contact_layout.setSpacing(2)
        contact_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        lbl_email = QLabel(f"📧 {self.data[4]}")
        lbl_email.setStyleSheet("font-size: 13px; color: #34495e; border: none;")
        
        lbl_tel = QLabel(f"📞 {self.data[5]}")
        lbl_tel.setStyleSheet("font-size: 13px; color: #34495e; border: none;")
        
        contact_layout.addWidget(lbl_email)
        contact_layout.addWidget(lbl_tel)
        main_layout.addLayout(contact_layout, 1)

        # 4. Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_wa = QPushButton("✅ WHATSAPP")
        self.btn_wa.setFixedSize(110, 35)
        self.btn_wa.setCursor(Qt.PointingHandCursor)
        self.btn_wa.setStyleSheet("""
            QPushButton { background-color: #25D366; color: white; font-weight: bold; border-radius: 8px; font-size: 10px; }
            QPushButton:hover { background-color: #128C7E; }
        """)
        
        self.btn_convert = QPushButton("👤 CONVERTIR")
        self.btn_convert.setFixedSize(110, 35)
        self.btn_convert.setCursor(Qt.PointingHandCursor)
        self.btn_convert.setStyleSheet("""
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
        
        btn_layout.addWidget(self.btn_wa)
        btn_layout.addWidget(self.btn_convert)
        btn_layout.addWidget(self.btn_delete)
        main_layout.addLayout(btn_layout)

class ProspectListPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.all_prospects = []
        
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        
        title_container = QVBoxLayout()
        title = QLabel("Gestión de Leads (Prospectos)")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #2c3e50;")
        self.lbl_stats = QLabel("Cargando lista de leads...")
        self.lbl_stats.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        title_container.addWidget(title)
        title_container.addWidget(self.lbl_stats)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por nombre, DNI o teléfono...")
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
        self.all_prospects = self.db.get_all_prospects()
        self.display_prospects(self.all_prospects)
        self.lbl_stats.setText(f"Total: {len(self.all_prospects)} prospectos registrados")

    def display_prospects(self, data):
        # Clear existing cards
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        for p in data:
            card = ProspectCard(p)
            # Connect integrated buttons
            card.btn_wa.clicked.connect(lambda chk=False, prospect=p: self.send_wa(prospect))
            card.btn_convert.clicked.connect(lambda chk=False, prospect=p: self.convert_to_client(prospect))
            card.btn_delete.clicked.connect(lambda chk=False, prospect=p: self.delete_prospect(prospect))
            
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def filter_cards(self):
        query = self.search_input.text().lower()
        if not query:
            self.display_prospects(self.all_prospects)
            return
            
        filtered = [p for p in self.all_prospects if any(query in str(field).lower() for field in p)]
        self.display_prospects(filtered)

    def delete_prospect(self, p):
        pid = p[0]
        name = f"{p[2]} {p[3]}"
        reply = QMessageBox.question(self, "Confirmar Eliminación", 
                                   f"¿Está seguro de eliminar al prospecto {name}?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.db.delete_prospect(pid):
                self.load_data()
                QMessageBox.information(self, "Éxito", "Prospecto eliminado correctamente.")

    def convert_to_client(self, p):
        # p = (id, doc, nombre, apellido, email, tel, fecha_reg)
        pid = p[0]
        name = f"{p[2]} {p[3]}"
        reply = QMessageBox.question(self, "Convertir", 
                                   f"¿Desea convertir a {name} en un Cliente oficial?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if not self.db.connect(): return
            cursor = self.db.connection.cursor()
            try:
                # 1. Insertar en clientes
                query = "INSERT INTO clientes (documento, nombre, apellido, email, telefono) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(query, (p[1], p[2], p[3], p[4], p[5]))
                new_cid = cursor.lastrowid
                
                # 2. Eliminar de prospectos
                cursor.execute("DELETE FROM prospectos WHERE id_prospecto = %s", (pid,))
                
                self.db.connection.commit()
                self.load_data()
                QMessageBox.information(self, "Éxito", f"{name} ahora es un cliente (ID #{new_cid})")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Fallo al convertir: {e}")

    def send_wa(self, p):
        phone = "".join(filter(str.isdigit, str(p[5])))
        if len(phone) == 10: phone = "54" + phone
        msg = urllib.parse.quote(f"Hola {p[2]}!")
        webbrowser.open(f"https://api.whatsapp.com/send?phone={phone}&text={msg}")
