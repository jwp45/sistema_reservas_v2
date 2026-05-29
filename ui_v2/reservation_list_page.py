from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QScrollArea, QMessageBox,
                             QGridLayout, QApplication)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPixmap
from controllers.database import Database
from datetime import datetime
from ui_v2.payment_dialog import PaymentDialog
from ui_v2.reservation_form import ReservationFormDialog
from ui_v2.gallery_dialog import GalleryDialog
import os

class ReservationCard(QFrame):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data # r = (0:id, 1:cliente, 2:tel, 3:inmueble, 4:f_ing, 5:f_eg, 6:noches, 7:val_d, 8:total, 9:final, 10:adelanto, 11:pendiente, 12:prov, 13:id_inm)
        self.init_ui()

    def init_ui(self):
        self.setFixedHeight(160)
        self.setStyleSheet("""
            #ReservationCard {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #eef0f2;
            }
            #ReservationCard:hover {
                border: 1px solid #3498db;
                background-color: #f7fbff;
            }
        """)
        self.setObjectName("ReservationCard")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(25)

        # 1. ID & Payment Status
        status_layout = QVBoxLayout()
        lbl_id = QLabel(f"R-{str(self.data[0]).zfill(5)}")
        lbl_id.setStyleSheet("font-weight: 800; font-size: 15px; color: #34495e; border: none;")
        status_layout.addWidget(lbl_id)
        
        pendiente = float(self.data[11])
        status_lbl = QLabel()
        if pendiente <= 0:
            status_lbl.setText("SALDADO ✅")
            status_lbl.setStyleSheet("background-color: #eafaf1; color: #27ae60; font-size: 11px; font-weight: bold; padding: 6px 12px; border-radius: 6px;")
        else:
            status_lbl.setText("PENDIENTE ⌛")
            status_lbl.setStyleSheet("background-color: #fceaea; color: #e74c3c; font-size: 11px; font-weight: bold; padding: 6px 12px; border-radius: 6px;")
        
        status_layout.addWidget(status_lbl)
        status_layout.addStretch()
        main_layout.addLayout(status_layout)

        # 2. Guest & Property Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        lbl_client = QLabel(str(self.data[1]).upper())
        lbl_client.setStyleSheet("font-size: 18px; font-weight: 800; color: #2c3e50; border: none;")
        
        lbl_prop = QLabel(f"🏠 {self.data[3]}")
        lbl_prop.setStyleSheet("font-size: 14px; color: #34495e; font-weight: 600; border: none;")
        
        lbl_dates = QLabel(f"📅 {self.fmt_date(self.data[4])} al {self.fmt_date(self.data[5])}")
        lbl_dates.setStyleSheet("font-size: 13px; color: #7f8c8d; border: none;")
        
        info_layout.addWidget(lbl_client)
        info_layout.addWidget(lbl_prop)
        info_layout.addWidget(lbl_dates)
        main_layout.addLayout(info_layout, 1)

        # 3. Financial Summary
        fin_layout = QVBoxLayout()
        fin_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        lbl_final_total = QLabel(f"Total: {self.format_currency(self.data[9])}")
        lbl_final_total.setStyleSheet("font-size: 12px; color: #95a5a6; border: none;")
        
        lbl_pending_val = QLabel(self.format_currency(pendiente) if pendiente > 0 else "SIN DEUDA")
        color = "#e74c3c" if pendiente > 0 else "#27ae60"
        lbl_pending_val.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {color}; border: none;")
        
        lbl_pending_text = QLabel("SALDO PENDIENTE" if pendiente > 0 else "PAGO TOTAL")
        lbl_pending_text.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {color}; border: none;")

        fin_layout.addWidget(lbl_final_total)
        fin_layout.addWidget(lbl_pending_val)
        fin_layout.addWidget(lbl_pending_text)
        main_layout.addLayout(fin_layout)

        # 4. Action Buttons
        actions_container = QWidget()
        actions_container.setStyleSheet("background: transparent;")
        btn_layout = QHBoxLayout(actions_container)
        btn_layout.setSpacing(10)
        
        self.btn_pay = QPushButton("💳 PAGOS")
        self.btn_pay.setFixedSize(100, 40)
        self.btn_pay.setCursor(Qt.PointingHandCursor)
        self.btn_pay.setStyleSheet("""
            QPushButton { background-color: #27ae60; color: white; font-weight: bold; border-radius: 8px; font-size: 11px; }
            QPushButton:hover { background-color: #219150; }
        """)
        
        self.btn_edit = QPushButton("✏️ EDITAR")
        self.btn_edit.setFixedSize(100, 40)
        self.btn_edit.setCursor(Qt.PointingHandCursor)
        self.btn_edit.setStyleSheet("""
            QPushButton { background-color: #3498db; color: white; font-weight: bold; border-radius: 8px; font-size: 11px; }
            QPushButton:hover { background-color: #2980b9; }
        """)
        
        self.btn_delete = QPushButton("🗑️")
        self.btn_delete.setFixedSize(40, 40)
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setStyleSheet("""
            QPushButton { background-color: #fceaea; color: #e74c3c; border: none; border-radius: 8px; }
            QPushButton:hover { background-color: #f8d7da; }
        """)
        
        btn_layout.addWidget(self.btn_pay)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        main_layout.addWidget(actions_container)

    def fmt_date(self, d):
        if not d: return "-"
        try:
            dt = datetime.strptime(str(d), "%Y-%m-%d") if isinstance(d, str) else d
            return dt.strftime("%d/%m/%y")
        except: return str(d)

    def format_currency(self, val):
        return f"${float(val):,.0f}".replace(",", ".")

class ReservationListPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.all_reservations = []
        
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        
        title_container = QVBoxLayout()
        title = QLabel("Gestión de Reservas")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #2c3e50;")
        self.lbl_stats = QLabel("Cargando estadísticas...")
        self.lbl_stats.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        title_container.addWidget(title)
        title_container.addWidget(self.lbl_stats)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por cliente, inmueble o ID...")
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
        self.all_reservations = self.db.get_all_reservations()
        self.display_reservations(self.all_reservations)
        self.update_stats()

    def display_reservations(self, data):
        # Clear existing cards
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        for r in data:
            card = ReservationCard(r)
            # Connect integrated buttons
            card.btn_pay.clicked.connect(lambda chk=False, res=r: self.open_payments(res))
            card.btn_edit.clicked.connect(lambda chk=False, res=r: self.edit_reservation(res))
            card.btn_delete.clicked.connect(lambda chk=False, res=r: self.delete_reservation(res))
            
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def filter_cards(self):
        query = self.search_input.text().lower()
        if not query:
            self.display_reservations(self.all_reservations)
            return
            
        filtered = []
        for r in self.all_reservations:
            res_code = f"R-{str(r[0]).zfill(5)}"
            search_data = f"{res_code} {r[1]} {r[3]}".lower()
            if query in search_data:
                filtered.append(r)
        
        self.display_reservations(filtered)

    def update_stats(self):
        total_count = len(self.all_reservations)
        total_pending = sum(float(r[11]) for r in self.all_reservations)
        self.lbl_stats.setText(f"Total: {total_count} reservas activas | Deuda Pendiente: ${total_pending:,.0f}".replace(",", "."))

    def open_payments(self, r):
        dialog = PaymentDialog(self, reservation_id=r[0], client_name=r[1], pending_amount=float(r[11]))
        if dialog.exec():
            self.load_data()

    def edit_reservation(self, r):
        dialog = ReservationFormDialog(self, reservation_id=r[0])
        if dialog.exec():
            self.load_data()

    def delete_reservation(self, r):
        res_code = f"R-{str(r[0]).zfill(5)}"
        reply = QMessageBox.question(self, "Confirmar Eliminación", 
                                   f"¿Está seguro de eliminar la reserva {res_code} de {r[1]}?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.db.delete_reservation(r[0]):
                self.load_data()
                QMessageBox.information(self, "Éxito", "Reserva eliminada correctamente.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar la reserva.")
