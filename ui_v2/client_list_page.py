from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QScrollArea, QMessageBox,
                             QGridLayout, QApplication, QDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPixmap
from controllers.database import Database
from ui_v2.client_form import ClientFormDialog
import webbrowser
import urllib.parse
from datetime import date, datetime
from utils.whatsapp_sender import open_whatsapp_chat

class ReservationHistoryDialog(QDialog):
    def __init__(self, client_data, parent=None):
        super().__init__(parent)
        self.client_data = client_data # (id, doc, nom, ape, email, tel)
        self.db = Database()
        self.setWindowTitle(f"Historial: {client_data[2]} {client_data[3]}")
        self.resize(700, 500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel(f"Historial de Reservas para {self.client_data[2]} {self.client_data[3]}")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        self.list_layout = QVBoxLayout(container)
        self.list_layout.setSpacing(10)
        self.list_layout.addStretch()
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        self.load_history()

    def load_history(self):
        if not self.db.connect(): return
        reservations = self.db.get_client_reservations(self.client_data[0])
        
        if not reservations:
            lbl_empty = QLabel("Este cliente no tiene reservas registradas.")
            lbl_empty.setAlignment(Qt.AlignCenter)
            lbl_empty.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 40px;")
            self.list_layout.insertWidget(0, lbl_empty)
            return
            
        for r in reservations:
            # r = (id, nombre_inm, f_in, f_out, noches, total, pendiente, creacion)
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame { background-color: #f8f9fa; border-radius: 10px; border: 1px solid #eef0f2; }
                QFrame:hover { background-color: #f1f3f5; border: 1px solid #3498db; }
            """)
            f_layout = QHBoxLayout(frame)
            
            info = QVBoxLayout()
            lbl_id = QLabel(f"Reserva R-{str(r[0]).zfill(5)}")
            lbl_id.setStyleSheet("font-weight: bold; color: #34495e;")
            
            periodo = f"📅 {self.fmt_date(r[2])} al {self.fmt_date(r[3])} ({r[4]} noches)"
            lbl_periodo = QLabel(periodo)
            lbl_periodo.setStyleSheet("font-size: 13px; color: #2c3e50;")
            
            lbl_inm = QLabel(f"🏠 {r[1]}")
            lbl_inm.setStyleSheet("font-size: 12px; color: #7f8c8d;")
            
            info.addWidget(lbl_id)
            info.addWidget(lbl_periodo)
            info.addWidget(lbl_inm)
            f_layout.addLayout(info, 1)
            
            # Status and Price
            status_layout = QVBoxLayout()
            status_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            pago = float(r[6]) if r[6] else 0
            status_txt = "SALDADO" if pago <= 0 else "PENDIENTE"
            status_color = "#27ae60" if pago <= 0 else "#e74c3c"
            
            lbl_status = QLabel(status_txt)
            lbl_status.setStyleSheet(f"font-weight: bold; color: {status_color}; font-size: 11px;")
            
            lbl_price = QLabel(f"${float(r[5]):,.0f}".replace(",", "."))
            lbl_price.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
            
            status_layout.addWidget(lbl_status)
            status_layout.addWidget(lbl_price)
            f_layout.addLayout(status_layout)
            
            self.list_layout.insertWidget(self.list_layout.count() - 1, frame)

    def fmt_date(self, d):
        if not d: return ""
        try: return d.strftime("%d/%m/%Y")
        except: return str(d)

class ClientCard(QFrame):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data # c = (id, doc, nom, ape, email, tel)
        self.init_ui()

    def init_ui(self):
        self.setFixedHeight(120)
        self.setStyleSheet("""
            #ClientCard {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #eef0f2;
            }
            #ClientCard:hover {
                border: 1px solid #3498db;
                background-color: #f7fbff;
            }
        """)
        self.setObjectName("ClientCard")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(25, 15, 25, 15)
        main_layout.setSpacing(20)

        # 1. Avatar / Icon
        avatar = QLabel("👤")
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("""
            background-color: #f0f2f5;
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
        
        lbl_doc = QLabel(f"📄 DNI: {self.data[1]} | 🆔 ID: #{self.data[0]}")
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
        
        self.btn_history = QPushButton("📜 HISTORIAL")
        self.btn_history.setFixedSize(110, 35)
        self.btn_history.setCursor(Qt.PointingHandCursor)
        self.btn_history.setStyleSheet("""
            QPushButton { background-color: #9b59b6; color: white; font-weight: bold; border-radius: 8px; font-size: 10px; }
            QPushButton:hover { background-color: #8e44ad; }
        """)

        self.btn_edit = QPushButton("✏️ EDITAR")
        self.btn_edit.setFixedSize(90, 35)
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
        
        btn_layout.addWidget(self.btn_wa)
        btn_layout.addWidget(self.btn_history)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        main_layout.addLayout(btn_layout)

class ClientListPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.all_clients = []
        
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        
        title_container = QVBoxLayout()
        title = QLabel("Directorio de Clientes")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #2c3e50;")
        self.lbl_stats = QLabel("Cargando lista de clientes...")
        self.lbl_stats.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        title_container.addWidget(title)
        title_container.addWidget(self.lbl_stats)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por nombre, DNI o email...")
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

        btn_add = QPushButton("➕ NUEVO CLIENTE")
        btn_add.setFixedSize(180, 45)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton { background-color: #2ecc71; color: white; border-radius: 22px; font-weight: bold; }
            QPushButton:hover { background-color: #27ae60; }
        """)
        btn_add.clicked.connect(self.add_client)

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
        self.all_clients = self.db.get_all_clients()
        self.display_clients(self.all_clients)
        self.lbl_stats.setText(f"Total: {len(self.all_clients)} clientes registrados")

    def display_clients(self, data):
        # Clear existing cards
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        for c in data:
            card = ClientCard(c)
            # Connect integrated buttons
            card.btn_wa.clicked.connect(lambda chk=False, client=c: self.send_wa(client))
            card.btn_history.clicked.connect(lambda chk=False, client=c: self.show_history(client))
            card.btn_edit.clicked.connect(lambda chk=False, client=c: self.edit_client(client))
            card.btn_delete.clicked.connect(lambda chk=False, client=c: self.delete_client(client))
            
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def show_history(self, c):
        dialog = ReservationHistoryDialog(c, self)
        dialog.exec()

    def filter_cards(self):
        query = self.search_input.text().lower()
        if not query:
            self.display_clients(self.all_clients)
            return
            
        filtered = [c for c in self.all_clients if any(query in str(field).lower() for field in c)]
        self.display_clients(filtered)

    def add_client(self):
        dialog = ClientFormDialog(self)
        if dialog.exec():
            self.load_data()

    def edit_client(self, c):
        dialog = ClientFormDialog(self, client_data=c)
        if dialog.exec():
            self.load_data()

    def delete_client(self, c):
        reply = QMessageBox.question(self, "Confirmar Eliminación", 
                                   f"¿Está seguro de eliminar al cliente {c[2]} {c[3]}?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if not self.db.connect(): return
            cursor = self.db.connection.cursor()
            try:
                cursor.execute("DELETE FROM clientes WHERE id_clientes = %s", (c[0],))
                self.db.connection.commit()
                self.load_data()
                QMessageBox.information(self, "Éxito", "Cliente eliminado correctamente.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo eliminar: {e}")

    def send_wa(self, c):
        # c = (id, doc, nom, ape, email, tel)
        phone = str(c[5])
        name = f"{c[2]} {c[3]}"
        open_whatsapp_chat(phone, f"Hola {name}!")
