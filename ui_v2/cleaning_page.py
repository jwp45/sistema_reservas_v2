import os
from datetime import date, datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QGridLayout, 
                             QScrollArea, QComboBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QDialog, QFormLayout)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon
from controllers.database import Database

class AddStaffDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir Personal de Limpieza")
        self.setFixedWidth(350)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)
        self.edit_nombre = QLineEdit()
        self.edit_tel = QLineEdit()
        self.edit_pin = QLineEdit()
        self.edit_pin.setPlaceholderText("Ej: 1234")
        
        layout.addRow("Nombre Completo:", self.edit_nombre)
        layout.addRow("Teléfono (WhatsApp):", self.edit_tel)
        layout.addRow("PIN de Acceso App:", self.edit_pin)
        
        btns = QHBoxLayout()
        btn_save = QPushButton("Guardar")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addRow(btns)

    def get_data(self):
        return {
            "nombre": self.edit_nombre.text().strip(),
            "telefono": self.edit_tel.text().strip(),
            "pin": self.edit_pin.text().strip()
        }

class CleaningPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(30)

        # --- PANEL IZQUIERDO: PERSONAL Y ESTADÍSTICAS ---
        left_panel = QFrame()
        left_panel.setFixedWidth(350)
        left_panel.setStyleSheet("background-color: white; border-radius: 15px; border: 1px solid #e0e0e0;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_staff_title = QLabel("👥 Personal de Limpieza")
        lbl_staff_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; border: none;")
        left_layout.addWidget(lbl_staff_title)
        
        self.table_staff = QTableWidget(0, 2)
        self.table_staff.setHorizontalHeaderLabels(["Nombre", "Estado"])
        self.table_staff.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_staff.setStyleSheet("border: none; background-color: #f8f9fa;")
        left_layout.addWidget(self.table_staff)
        
        btn_add_staff = QPushButton("+ Añadir Personal")
        btn_add_staff.setStyleSheet("""
            QPushButton { background-color: #3498db; color: white; font-weight: bold; padding: 10px; border-radius: 8px; }
            QPushButton:hover { background-color: #2980b9; }
        """)
        btn_add_staff.clicked.connect(self.add_staff)
        left_layout.addWidget(btn_add_staff)
        
        left_layout.addSpacing(30)
        
        lbl_sync_title = QLabel("☁️ Estado Sincronización")
        lbl_sync_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #7f8c8d; border: none;")
        left_layout.addWidget(lbl_sync_title)
        
        self.lbl_sync_status = QLabel("Pendiente de configurar Firebase")
        self.lbl_sync_status.setStyleSheet("color: #e67e22; font-weight: bold; border: none;")
        left_layout.addWidget(self.lbl_sync_status)

        self.main_layout.addWidget(left_panel)

        # --- PANEL DERECHO: TAREAS PENDIENTES ---
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: white; border-radius: 15px; border: 1px solid #e0e0e0;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(25, 25, 25, 25)
        
        header = QHBoxLayout()
        lbl_tasks_title = QLabel("🧹 Inmuebles Pendientes de Limpieza")
        lbl_tasks_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50; border: none;")
        header.addWidget(lbl_tasks_title)
        
        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.clicked.connect(self.load_data)
        header.addWidget(btn_refresh)
        right_layout.addLayout(header)
        
        # Tabla de inmuebles "sucios"
        self.table_pending = QTableWidget(0, 5)
        self.table_pending.setHorizontalHeaderLabels(["Inmueble", "Check-out", "Tarifa", "Asignar A", "Acción"])
        self.table_pending.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_pending.setStyleSheet("""
            QTableWidget { border: none; gridline-color: #f1f3f5; }
            QHeaderView::section { background-color: #f8f9fa; padding: 10px; font-weight: bold; border: none; }
        """)
        right_layout.addWidget(self.table_pending)

        self.main_layout.addWidget(right_panel, 1)

    def load_data(self):
        if not self.db.connect(): return
        
        # 1. Cargar Personal
        staff = self.db.get_cleaning_staff()
        self.table_staff.setRowCount(0)
        for s in staff:
            row = self.table_staff.rowCount()
            self.table_staff.insertRow(row)
            self.table_staff.setItem(row, 0, QTableWidgetItem(s[1]))
            status_item = QTableWidgetItem(s[4].upper())
            status_item.setForeground(QColor("#27ae60") if s[4] == 'activo' else QColor("#e74c3c"))
            self.table_staff.setItem(row, 1, status_item)
            
        # 2. Cargar Inmuebles que necesitan limpieza
        pending = self.db.get_pending_cleanings()
        self.table_pending.setRowCount(0)
        
        staff_names = {s[0]: s[1] for s in staff}
        
        for p in pending:
            row = self.table_pending.rowCount()
            self.table_pending.insertRow(row)
            
            # Inmueble
            self.table_pending.setItem(row, 0, QTableWidgetItem(p['nombre']))
            
            # Fecha Checkout
            self.table_pending.setItem(row, 1, QTableWidgetItem(p['fecha_egreso'].strftime("%d/%m/%Y")))
            
            # Tarifa (Editable)
            fee_edit = QLineEdit(str(p.get('tarifa_limpieza', 0.00)))
            fee_edit.setFixedWidth(80)
            self.table_pending.setCellWidget(row, 2, fee_edit)
            
            # Combo Personal
            combo_staff = QComboBox()
            combo_staff.addItem("Seleccionar...", None)
            for sid, name in staff_names.items():
                combo_staff.addItem(name, sid)
            self.table_pending.setCellWidget(row, 3, combo_staff)
            
            # Botón Enviar
            btn_send = QPushButton("Enviar a App")
            btn_send.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px;")
            btn_send.clicked.connect(lambda checked=False, r=row, data=p: self.assign_task(r, data))
            self.table_pending.setCellWidget(row, 4, btn_send)

    def add_staff(self):
        dialog = AddStaffDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data['nombre'] and data['pin']:
                if self.db.add_cleaning_staff(data):
                    QMessageBox.information(self, "Éxito", "Personal añadido correctamente.")
                    self.load_data()
                else:
                    QMessageBox.critical(self, "Error", "No se pudo añadir al personal.")

    def assign_task(self, row_idx, prop_data):
        fee_widget = self.table_pending.cellWidget(row_idx, 2)
        staff_widget = self.table_pending.cellWidget(row_idx, 3)
        
        fee = float(fee_widget.text() or 0)
        staff_id = staff_widget.currentData()
        
        if not staff_id:
            QMessageBox.warning(self, "Atención", "Debe seleccionar un empleado.")
            return
            
        task_data = {
            "id_inmueble": prop_data['id_inmuebles'],
            "id_reserva": prop_data['id_reserva'],
            "id_personal": staff_id,
            "pago": fee
        }
        
        if self.db.assign_cleaning_task(task_data):
            QMessageBox.information(self, "Tarea Enviada", 
                                    f"Limpieza asignada a {staff_widget.currentText()}.\nPróximamente se sincronizará con la App.")
            self.load_data()
        else:
            QMessageBox.critical(self, "Error", "No se pudo asignar la tarea.")
