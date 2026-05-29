from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QFrame, QMessageBox)
from PySide6.QtCore import Qt
from controllers.database import Database
from datetime import datetime

class PaymentDialog(QDialog):
    def __init__(self, parent=None, reservation_id=None, client_name="", pending_amount=0.0):
        super().__init__(parent)
        self.db = Database()
        self.reservation_id = reservation_id
        self.client_name = client_name
        self.pending_amount = pending_amount
        
        self.setWindowTitle("Gestionar Pagos")
        self.setFixedWidth(500)
        self.setFixedHeight(650)
        
        self.init_ui()
        self.load_history()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header Info
        header = QVBoxLayout()
        header.setSpacing(5)
        
        lbl_res = QLabel(f"RESERVA #{self.reservation_id}")
        lbl_res.setStyleSheet("color: #7f8c8d; font-size: 11px; font-weight: bold;")
        
        lbl_name = QLabel(self.client_name.upper())
        lbl_name.setStyleSheet("color: #2c3e50; font-size: 18px; font-weight: bold;")
        
        header.addWidget(lbl_res)
        header.addWidget(lbl_name)
        layout.addLayout(header)
        
        # Pending Card
        pending_card = QFrame()
        pending_card.setStyleSheet("background-color: #fdf2f2; border-radius: 10px; border: 1px solid #fadbd8;")
        pc_layout = QVBoxLayout(pending_card)
        pc_layout.setContentsMargins(20, 15, 20, 15)
        
        lbl_p_title = QLabel("SALDO PENDIENTE ACTUAL")
        lbl_p_title.setStyleSheet("color: #e74c3c; font-size: 10px; font-weight: bold; border: none;")
        
        self.lbl_pending = QLabel(self.format_currency(self.pending_amount))
        self.lbl_pending.setStyleSheet("color: #e74c3c; font-size: 24px; font-weight: bold; border: none;")
        
        pc_layout.addWidget(lbl_p_title)
        pc_layout.addWidget(self.lbl_pending)
        layout.addWidget(pending_card)
        
        # History Table
        lbl_hist = QLabel("HISTORIAL DE MOVIMIENTOS")
        lbl_hist.setStyleSheet("color: #34495e; font-size: 12px; font-weight: bold;")
        layout.addWidget(lbl_hist)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Fecha", "Monto"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setStyleSheet("""
            QTableWidget { 
                border: 1px solid #e0e0e0; 
                border-radius: 5px; 
                background-color: white;
                alternate-background-color: #f8f9fa;
                color: #2c3e50;
            }
            QTableWidget::item {
                background-color: white;
                color: #2c3e50;
                padding: 5px;
            }
            QTableWidget::item:alternate {
                background-color: #f8f9fa;
            }
            QTableWidget::item:selected {
                background-color: #ebf5fb;
                color: #2980b9;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 5px;
                border: none;
                border-bottom: 1px solid #e0e0e0;
                font-weight: bold;
                color: #7f8c8d;
            }
        """)
        layout.addWidget(self.table)
        
        # New Payment Entry
        pay_layout = QVBoxLayout()
        pay_layout.setSpacing(8)
        
        lbl_new = QLabel("REGISTRAR NUEVO ABONO")
        lbl_new.setStyleSheet("color: #2c3e50; font-size: 12px; font-weight: bold;")
        
        self.edit_amount = QLineEdit()
        self.edit_amount.setPlaceholderText("$0,00")
        self.edit_amount.setFixedHeight(45)
        self.edit_amount.setStyleSheet("""
            QLineEdit {
                font-size: 18px;
                font-weight: bold;
                padding-left: 15px;
                border: 2px solid #3498db;
                border-radius: 5px;
                color: #2c3e50;
            }
        """)
        
        pay_layout.addWidget(lbl_new)
        pay_layout.addWidget(self.edit_amount)
        layout.addLayout(pay_layout)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("CANCELAR")
        btn_cancel.setFixedHeight(40)
        btn_cancel.clicked.connect(self.reject)
        
        self.btn_pay = QPushButton("REGISTRAR ABONO")
        self.btn_pay.setFixedHeight(40)
        self.btn_pay.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        self.btn_pay.clicked.connect(self.submit_payment)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_pay)
        layout.addLayout(btn_layout)

    def load_history(self):
        if not self.db.connect(): return
        history = self.db.get_payment_history(self.reservation_id)
        self.table.setRowCount(0)
        for row in history:
            # row: (fecha, monto)
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(row[0].strftime("%d/%m/%Y %H:%M")))
            self.table.setItem(r, 1, QTableWidgetItem(self.format_currency(row[1])))
            self.table.item(r, 1).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def format_currency(self, val):
        return f"${val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def submit_payment(self):
        try:
            val_str = self.edit_amount.text().replace("$", "").replace(".", "").replace(",", ".")
            amount = float(val_str)
            if amount <= 0:
                QMessageBox.warning(self, "Error", "El monto debe ser mayor a cero.")
                return
                
            if not self.db.connect(): return
            success, message = self.db.add_payment_to_reservation(self.reservation_id, amount)
            
            if success:
                QMessageBox.information(self, "Éxito", message)
                self.accept()
            else:
                QMessageBox.critical(self, "Error", message)
        except ValueError:
            QMessageBox.warning(self, "Error", "Monto inválido.")
