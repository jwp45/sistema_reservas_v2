from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QScrollArea,
                             QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QColor
from controllers.database import Database
from controllers.automation_controller import AutomationController
from ui_v2.payment_dialog import PaymentDialog
from ui_v2.reservation_form import ReservationFormDialog

class ReservationCard(QFrame):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        self.setFixedHeight(140)
        self.setStyleSheet("""
            #ReservationCard {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #eef0f2;
            }
            #ReservationCard:hover {
                border: 1px solid #3498db;
                background-color: #f7fbff;
            }
        """)
        self.setObjectName("ReservationCard")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(20)

        # 1. ID & Status Badge
        id_layout = QVBoxLayout()
        lbl_id = QLabel(f"R-{str(self.data[0]).zfill(5)}")
        lbl_id.setStyleSheet("font-weight: 800; font-size: 14px; color: #34495e; border: none;")
        id_layout.addWidget(lbl_id)
        
        # Payment Status Badge
        pendiente_raw = float(self.data[11]) if self.data[11] is not None else 0
        status_lbl = QLabel("SALDADO" if pendiente_raw <= 0 else "PENDIENTE")
        if pendiente_raw <= 0:
            status_lbl.setStyleSheet("background-color: #eafaf1; color: #27ae60; font-size: 10px; font-weight: bold; padding: 4px 8px; border-radius: 4px;")
        else:
            status_lbl.setStyleSheet("background-color: #fceaea; color: #e74c3c; font-size: 10px; font-weight: bold; padding: 4px 8px; border-radius: 4px;")
        id_layout.addWidget(status_lbl)
        
        # WhatsApp Status (Checks underneath status)
        wa_status = self.data[15] if len(self.data) > 15 else None
        if wa_status:
            wa_lbl = QLabel()
            wa_lbl.setFixedHeight(18)
            if wa_status == "read":
                wa_lbl.setText("✓✓ LEÍDO")
                wa_lbl.setStyleSheet("color: #34b7f1; font-weight: bold; font-size: 9px; border: none;")
            elif wa_status == "delivered":
                wa_lbl.setText("✓✓ ENTREGADO")
                wa_lbl.setStyleSheet("color: #95a5a6; font-weight: bold; font-size: 9px; border: none;")
            elif wa_status == "sent":
                wa_lbl.setText("✓ ENVIADO")
                wa_lbl.setStyleSheet("color: #95a5a6; font-weight: bold; font-size: 9px; border: none;")
            elif wa_status == "failed":
                wa_lbl.setText("✕ ERROR")
                wa_lbl.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 9px; border: none;")
            id_layout.addWidget(wa_lbl)
            
        id_layout.addStretch()
        main_layout.addLayout(id_layout)

        # 2. Main Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        lbl_client = QLabel(str(self.data[1]).upper())
        lbl_client.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; border: none;")
        
        lbl_prop = QLabel(f"🏠 {self.data[3]}")
        lbl_prop.setStyleSheet("font-size: 13px; color: #34495e; border: none;")
        
        lbl_period = QLabel(f"📅 {self.fmt_date(self.data[4])} al {self.fmt_date(self.data[5])} ({self.data[6]} noches)")
        lbl_period.setStyleSheet("font-size: 13px; color: #7f8c8d; border: none;")
        
        # Fecha de Registro (Creación)
        try:
            created_at = self.data[14]
            created_str = self.fmt_date(created_at)
            lbl_created = QLabel(f"📝 Registrada: {created_str}")
            lbl_created.setStyleSheet("font-size: 11px; color: #95a5a6; border: none; font-style: italic;")
            info_layout.addWidget(lbl_client)
            info_layout.addWidget(lbl_prop)
            info_layout.addWidget(lbl_period)
            info_layout.addWidget(lbl_created)
        except:
            info_layout.addWidget(lbl_client)
            info_layout.addWidget(lbl_prop)
            info_layout.addWidget(lbl_period)
        
        main_layout.addLayout(info_layout, 1)

        # 3. Price/Payment Info
        price_layout = QVBoxLayout()
        price_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Calculate real pending
        adelanto = float(self.data[10]) if self.data[10] else 0
        total_desc = float(self.data[9]) if self.data[9] else 0
        pendiente = total_desc - adelanto
        
        lbl_total = QLabel(f"Total: {self.format_currency(total_desc)}")
        lbl_total.setStyleSheet("font-size: 11px; color: #95a5a6; border: none;")
        
        lbl_pending = QLabel(self.format_currency(pendiente) if pendiente > 0 else "SALDADO")
        color_pend = "#e74c3c" if pendiente > 0 else "#27ae60"
        lbl_pending.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {color_pend}; border: none;")
        
        lbl_pend_text = QLabel("SALDO PENDIENTE" if pendiente > 0 else "PAGO TOTAL")
        lbl_pend_text.setStyleSheet(f"font-size: 9px; font-weight: bold; color: {color_pend}; border: none;")

        price_layout.addWidget(lbl_total)
        price_layout.addWidget(lbl_pending)
        price_layout.addWidget(lbl_pend_text)
        main_layout.addLayout(price_layout)

        # 4. Integrated Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        def create_action_btn(text, bg, hover, width=100):
            btn = QPushButton(text)
            btn.setFixedSize(width, 35)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{ background-color: {bg}; color: white; font-weight: bold; border-radius: 6px; font-size: 11px; }}
                QPushButton:hover {{ background-color: {hover}; }}
            """)
            return btn

        self.btn_pay = create_action_btn("💳 PAGOS", "#27ae60", "#219150")
        self.btn_edit = create_action_btn("✏️ EDITAR", "#3498db", "#2980b9")
        self.btn_delete = create_action_btn("🗑️", "#f8d7da", "#f5c6cb", 35)
        self.btn_delete.setStyleSheet(self.btn_delete.styleSheet().replace("white", "#e74c3c")) # Text color for delete
        
        btn_layout.addWidget(self.btn_pay)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        main_layout.addLayout(btn_layout)

    def format_currency(self, value):
        try:
            val = float(value)
            return f"${val:,.0f}".replace(",", ".")
        except: return "$0"

    def fmt_date(self, d):
        if not d: return ""
        try: return d.strftime("%d/%m/%Y")
        except: return str(d)

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

        # Header
        header = QHBoxLayout()
        title = QLabel("Gestión de Reservas")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #2c3e50;")
        header.addWidget(title)
        
        header.addStretch()
        
        # Stats label
        self.lbl_stats = QLabel("Total: 0 reservas | Deuda: $0")
        self.lbl_stats.setStyleSheet("background-color: #f8f9fa; padding: 10px 20px; border-radius: 20px; color: #34495e; font-weight: 600; font-size: 13px;")
        header.addWidget(self.lbl_stats)
        
        layout.addLayout(header)

        # Search & Actions
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por cliente, inmueble o ID...")
        self.search_input.setFixedHeight(45)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding-left: 15px;
                border: 1px solid #d1d8e0;
                border-radius: 10px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus { border: 2px solid #3498db; }
        """)
        self.search_input.textChanged.connect(self.filter_cards)
        search_layout.addWidget(self.search_input, 1)
        
        btn_new = QPushButton("＋ NUEVA RESERVA")
        btn_new.setFixedHeight(45)
        btn_new.setFixedWidth(180)
        btn_new.setCursor(Qt.PointingHandCursor)
        btn_new.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 10px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        btn_new.clicked.connect(lambda: self.open_reservation_form())
        search_layout.addWidget(btn_new)
        
        layout.addLayout(search_layout)

        # Scroll Area for Cards
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
        
        # Actualizar estados de WhatsApp inmediatamente al entrar (de forma silenciosa)
        try:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self._sync_wa_statuses)
        except: pass

        self.all_reservations = self.db.get_all_reservations()
        self.display_reservations(self.all_reservations)
        self.update_stats()

    def _sync_wa_statuses(self):
        """Tarea en segundo plano para sincronizar estados de WA sin bloquear la UI."""
        try:
            auto = AutomationController()
            if auto.update_whatsapp_statuses():
                # Si hubo cambios, forzar la recarga completa de la lista
                print("DEBUG: Cambios en WA detectados, refrescando lista...")
                self.load_data() 
        except Exception as e:
            print(f"Error sincronizando WA en vista: {e}")

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
        total_pending = sum(float(r[11]) for r in self.all_reservations if r[11] is not None)
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

    def open_reservation_form(self, initial_data=None):
        dialog = ReservationFormDialog(self, initial_data=initial_data)
        if dialog.exec():
            self.load_data()
