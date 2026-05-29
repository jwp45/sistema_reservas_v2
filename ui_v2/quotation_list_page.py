from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QScrollArea, QMessageBox,
                             QCheckBox, QGridLayout, QInputDialog, QApplication)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPixmap, QIcon
from controllers.database import Database
from datetime import datetime, timedelta
from ui_v2.reservation_form import ReservationFormDialog
import os

class QuotationCard(QFrame):
    clicked = Signal(object) # Emit the quotation data when clicked
    
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data # q = (0:id, 1:cliente, 2:inmueble, 3:f_ing, 4:f_eg, 5:noches, 6:final, 7:f_cot, 8:contact_id, 9:inm_id, 10:val_d, 11:total, 12:desc, 13:cap, 14:mkt_sent, 15:contact_type)
        self.setCursor(Qt.PointingHandCursor)
        self.init_ui()

    def init_ui(self):
        self.setFixedHeight(140)
        self.setStyleSheet("""
            #QuotationCard {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #eef0f2;
            }
            #QuotationCard:hover {
                border: 1px solid #3498db;
                background-color: #f7fbff;
            }
        """)
        self.setObjectName("QuotationCard")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(20)

        # 1. ID & Status Badge
        id_layout = QVBoxLayout()
        lbl_id = QLabel(f"Q-{str(self.data[0]).zfill(5)}")
        lbl_id.setStyleSheet("font-weight: 800; font-size: 14px; color: #34495e; border: none;")
        id_layout.addWidget(lbl_id)
        
        # Calculate validity status
        now = datetime.now()
        expiracion = self.data[7] + timedelta(days=15)
        restante = expiracion - now
        
        dias = restante.days
        horas = restante.seconds // 3600
        
        status_lbl = QLabel()
        if restante.total_seconds() <= 0:
            status_lbl.setText("EXPIRADO")
            status_lbl.setStyleSheet("background-color: #fceaea; color: #e74c3c; font-size: 10px; font-weight: bold; padding: 4px 8px; border-radius: 4px;")
        elif dias < 3:
            status_lbl.setText(f"EN RIESGO ({dias}d {horas}h)")
            status_lbl.setStyleSheet("background-color: #fff4e5; color: #f39c12; font-size: 10px; font-weight: bold; padding: 4px 8px; border-radius: 4px;")
        else:
            status_lbl.setText(f"ACTIVA ({dias}d {horas}h)")
            status_lbl.setStyleSheet("background-color: #eafaf1; color: #27ae60; font-size: 10px; font-weight: bold; padding: 4px 8px; border-radius: 4px;")
        
        id_layout.addWidget(status_lbl)
        id_layout.addStretch()
        main_layout.addLayout(id_layout)

        # 2. Main Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        lbl_client = QLabel(str(self.data[1]).upper())
        lbl_client.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; border: none;")
        
        lbl_prop = QLabel(f"🏠 {self.data[2]}")
        lbl_prop.setStyleSheet("font-size: 13px; color: #34495e; border: none;")
        
        lbl_period = QLabel(f"📅 {self.data[3].strftime('%d/%m')} al {self.data[4].strftime('%d/%m')} ({self.data[5]} noches)")
        lbl_period.setStyleSheet("font-size: 13px; color: #7f8c8d; border: none;")
        
        info_layout.addWidget(lbl_client)
        info_layout.addWidget(lbl_prop)
        info_layout.addWidget(lbl_period)
        main_layout.addLayout(info_layout, 1)

        # 3. Price Info
        price_layout = QVBoxLayout()
        price_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        lbl_total = QLabel(self.format_currency(self.data[6]))
        lbl_total.setStyleSheet("font-size: 20px; font-weight: 800; color: #27ae60; border: none;")
        
        lbl_sent = QLabel(f"Enviada: {self.data[7].strftime('%d/%m/%Y')}")
        lbl_sent.setStyleSheet("font-size: 11px; color: #95a5a6; border: none;")
        
        if self.data[14]: # mkt_sent
            lbl_mkt = QLabel("✨ Oferta Especial")
            lbl_mkt.setStyleSheet("font-size: 11px; color: #9b59b6; font-weight: bold; border: none;")
            price_layout.addWidget(lbl_mkt)

        price_layout.addWidget(lbl_total)
        price_layout.addWidget(lbl_sent)
        main_layout.addLayout(price_layout)

        # 4. Integrated Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_reserve = QPushButton("🚀 RESERVAR")
        self.btn_reserve.setFixedSize(110, 35)
        self.btn_reserve.setStyleSheet("""
            QPushButton { background-color: #3498db; color: white; font-weight: bold; border-radius: 6px; font-size: 11px; }
            QPushButton:hover { background-color: #2980b9; }
        """)
        
        self.btn_reoffer = QPushButton("🎁 RE-OFERTA")
        self.btn_reoffer.setFixedSize(110, 35)
        self.btn_reoffer.setStyleSheet("""
            QPushButton { background-color: #27ae60; color: white; font-weight: bold; border-radius: 6px; font-size: 11px; }
            QPushButton:hover { background-color: #219150; }
        """)
        
        self.btn_delete = QPushButton("🗑️")
        self.btn_delete.setFixedSize(35, 35)
        self.btn_delete.setStyleSheet("""
            QPushButton { background-color: #f8d7da; color: #e74c3c; border: none; border-radius: 6px; }
            QPushButton:hover { background-color: #f5c6cb; }
        """)
        
        btn_layout.addWidget(self.btn_reoffer)
        btn_layout.addWidget(self.btn_reserve)
        btn_layout.addWidget(self.btn_delete)
        main_layout.addLayout(btn_layout)

    def format_currency(self, val):
        return f"${float(val):,.0f}".replace(",", ".")

    def mousePressEvent(self, event):
        self.clicked.emit(self.data)
        super().mousePressEvent(event)

class QuotationListPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.all_quotations = []
        
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        
        title_container = QVBoxLayout()
        title = QLabel("Gestión de Cotizaciones")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #2c3e50;")
        self.lbl_stats = QLabel("Cargando historial...")
        self.lbl_stats.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        title_container.addWidget(title)
        title_container.addWidget(self.lbl_stats)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por cliente, inmueble o código (Q-XXXX)...")
        self.search_input.setFixedWidth(400) # Un poco más ancho para el texto extra
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

        self.chk_risk = QCheckBox("⚠️ En Riesgo de Cierre")
        self.chk_risk.setStyleSheet("font-weight: bold; color: #e67e22; font-size: 13px;")
        self.chk_risk.stateChanged.connect(self.filter_cards)

        self.btn_bulk_reoffer = QPushButton("🎁 ENVIAR RE-OFERTAS MASIVAS")
        self.btn_bulk_reoffer.setFixedSize(220, 45)
        self.btn_bulk_reoffer.setCursor(Qt.PointingHandCursor)
        self.btn_bulk_reoffer.setStyleSheet("""
            QPushButton { 
                background-color: #f1c40f; 
                color: #2c3e50; 
                font-weight: bold; 
                border-radius: 22px; 
                font-size: 11px;
            }
            QPushButton:hover { background-color: #f39c12; }
            QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }
        """)
        self.btn_bulk_reoffer.clicked.connect(self.send_bulk_reoffers)
        self.btn_bulk_reoffer.hide() # Solo mostrar cuando hay filtro de riesgo

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
        header_layout.addWidget(self.chk_risk)
        header_layout.addSpacing(10)
        header_layout.addWidget(self.btn_bulk_reoffer)
        header_layout.addSpacing(20)
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
        self.all_quotations = self.db.get_all_quotations()
        self.display_quotations(self.all_quotations)
        
        total = len(self.all_quotations)
        self.lbl_stats.setText(f"Mostrando {total} cotizaciones procesadas")

    def set_risk_filter_enabled(self, enabled):
        """Activa o desactiva el filtro de riesgo externamente."""
        self.chk_risk.setChecked(enabled)
        self.filter_cards()

    def display_quotations(self, data):
        # Clear existing cards
        while self.cards_layout.count() > 1: # Mantener el stretch
            item = self.cards_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        for q in data:
            card = QuotationCard(q)
            # Connect integrated buttons
            card.btn_reserve.clicked.connect(lambda chk=False, q_data=q: self.convert_to_reservation(q_data))
            card.btn_reoffer.clicked.connect(lambda chk=False, q_data=q: self.reoffer_quotation(q_data))
            card.btn_delete.clicked.connect(lambda chk=False, q_data=q: self.delete_quotation(q_data))
            
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def filter_cards(self):
        query = self.search_input.text().lower()
        only_risk = self.chk_risk.isChecked()
        now = datetime.now()
        
        filtered = []
        for q in self.all_quotations:
            # Generar código de búsqueda formateado (ej: q-00001)
            q_code = f"q-{str(q[0]).zfill(5)}"
            
            # Coincidencia por cliente, inmueble o código
            match_search = query in f"{q[1]} {q[2]} {q_code}".lower()
            
            expiracion = q[7] + timedelta(days=15)
            restante = expiracion - now
            is_risk = 0 < restante.days < 3
            match_risk = not only_risk or is_risk
            
            if match_search and match_risk:
                filtered.append(q)
        
        self.btn_bulk_reoffer.setVisible(only_risk and len(filtered) > 0)
        self.display_quotations(filtered)

    def send_bulk_reoffers(self):
        # 1. Obtener las cotizaciones filtradas (las que se están mostrando)
        query = self.search_input.text().lower()
        now = datetime.now()
        to_reoffer = []
        
        for q in self.all_quotations:
            q_code = f"q-{str(q[0]).zfill(5)}"
            match_search = query in f"{q[1]} {q[2]} {q_code}".lower()
            expiracion = q[7] + timedelta(days=15)
            restante = expiracion - now
            if match_search and (0 < restante.days < 3):
                to_reoffer.append(q)
        
        if not to_reoffer:
            return

        # 2. Preguntar descuento
        extra_pct, ok = QInputDialog.getDouble(self, "Re-Oferta Masiva", 
                                             f"Se enviará una oferta a {len(to_reoffer)} clientes.\nDescuento adicional (%):", 
                                             5, 0, 50, 1)
        if not ok: return

        # 3. Confirmación final
        confirm = QMessageBox.question(self, "Confirmar Envío", 
                                     f"¿Estás seguro de enviar {len(to_reoffer)} correos electrónicos ahora?",
                                     QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.No: return

        # 4. Proceso de envío
        from utils.email_sender import send_marketing_offer_email
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.btn_bulk_reoffer.setEnabled(False)
        self.btn_bulk_reoffer.setText("🚀 ENVIANDO...")
        
        success_count = 0
        try:
            for q in to_reoffer:
                qid = q[0]
                contact = self.db.get_client_by_id(q[8]) if q[15] == 'cliente' else self.db.get_prospect_by_id(q[8])
                if contact:
                    current_price = float(q[6])
                    new_price = current_price * (1 - (extra_pct / 100))
                    data = {
                        "id": qid, "inmueble": q[2],
                        "old_price": f"${current_price:,.0f}".replace(",", "."),
                        "new_price": f"${new_price:,.0f}".replace(",", "."),
                        "fecha_ingreso": q[3].strftime("%d/%m/%Y"),
                        "fecha_egreso": q[4].strftime("%d/%m/%Y")
                    }
                    if send_marketing_offer_email(contact[3], f"{contact[1]} {contact[2]}", data, contact_type=q[15]):
                        self.db.mark_quotation_mkt_sent(qid)
                        success_count += 1
                QApplication.processEvents() # Mantener UI viva
        finally:
            self.btn_bulk_reoffer.setEnabled(True)
            self.btn_bulk_reoffer.setText("🎁 ENVIAR RE-OFERTAS MASIVAS")
            QApplication.restoreOverrideCursor()
            
        QMessageBox.information(self, "Proceso Completado", f"Se enviaron con éxito {success_count} de {len(to_reoffer)} re-ofertas.")
        self.load_data()

    def delete_quotation(self, q):
        qid = q[0]
        if QMessageBox.question(self, "Eliminar", f"¿Desea eliminar la cotización Q-{str(qid).zfill(5)}?",
                               QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            if self.db.delete_quotation(qid):
                self.load_data()

    def reoffer_quotation(self, q):
        qid = q[0]
        extra_pct, ok = QInputDialog.getDouble(self, "Re-Ofertar", "Descuento adicional (%):", 5, 0, 50, 1)
        if ok:
            from utils.email_sender import send_marketing_offer_email
            
            # Obtener contacto
            contact = self.db.get_client_by_id(q[8]) if q[15] == 'cliente' else self.db.get_prospect_by_id(q[8])
            if contact:
                current_price = float(q[6])
                new_price = current_price * (1 - (extra_pct / 100))
                data = {
                    "id": qid, "inmueble": q[2],
                    "old_price": f"${current_price:,.0f}".replace(",", "."),
                    "new_price": f"${new_price:,.0f}".replace(",", "."),
                    "fecha_ingreso": q[3].strftime("%d/%m/%Y"),
                    "fecha_egreso": q[4].strftime("%d/%m/%Y")
                }
                QApplication.setOverrideCursor(Qt.WaitCursor)
                try:
                    if send_marketing_offer_email(contact[3], f"{contact[1]} {contact[2]}", data, contact_type=q[15]):
                        self.db.mark_quotation_mkt_sent(qid)
                        QMessageBox.information(self, "Éxito", "Oferta enviada correctamente.")
                        self.load_data()
                finally:
                    QApplication.restoreOverrideCursor()

    def convert_to_reservation(self, q):
        # q = (id, client, prop, f_in, f_out, nights, final, f_cot, contact_id, inm_id, val_d, total, desc, cap, mkt, type)
        initial_data = {
            "inmueble": q[2],
            "fecha_ingreso": q[3].strftime("%d/%m/%Y"),
            "fecha_egreso": q[4].strftime("%d/%m/%Y"),
            "cantidad_personas": q[13],
            "descuento": str(q[12]),
            "discount_is_percentage": False,
            "id_cliente": q[8] if q[15] == 'cliente' else None
        }
        if q[15] == 'prospecto':
            initial_data["id_cliente"] = q[8] 
        
        dialog = ReservationFormDialog(self, initial_data=initial_data)
        if dialog.exec():
            self.load_data()
