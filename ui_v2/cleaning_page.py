import os
from datetime import date, datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QGridLayout, 
                             QScrollArea, QComboBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QDialog, QFormLayout)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QIcon
from controllers.database import Database
from controllers.sync_controller import SyncController

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

class StaffPaymentDialog(QDialog):
    def __init__(self, staff_id, staff_name, tasks, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Liquidar Pagos: {staff_name}")
        self.setFixedWidth(500)
        self.tasks = tasks
        self.total = sum(float(t['pago_servicio']) for t in tasks)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        lbl_info = QLabel(f"Resumen de tareas pendientes para {self.windowTitle().split(': ')[1]}:")
        lbl_info.setStyleSheet("font-weight: bold; color: #2c3e50;")
        layout.addWidget(lbl_info)
        
        self.table = QTableWidget(len(self.tasks), 3)
        self.table.setHorizontalHeaderLabels(["Inmueble", "Fecha", "Monto"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("background-color: white; border-radius: 5px;")
        
        for i, t in enumerate(self.tasks):
            self.table.setItem(i, 0, QTableWidgetItem(t['property_name']))
            fecha = t['fecha_finalizacion'].strftime("%d/%m/%Y") if t['fecha_finalizacion'] else "-"
            self.table.setItem(i, 1, QTableWidgetItem(fecha))
            monto_item = QTableWidgetItem(f"$ {float(t['pago_servicio']):,.2f}")
            monto_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 2, monto_item)
            
        layout.addWidget(self.table)
        
        total_frame = QFrame()
        total_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 10px; padding: 10px;")
        total_layout = QHBoxLayout(total_frame)
        total_layout.addWidget(QLabel("TOTAL A LIQUIDAR:"))
        lbl_total = QLabel(f"$ {self.total:,.2f}")
        lbl_total.setStyleSheet("font-size: 20px; font-weight: bold; color: #27ae60;")
        total_layout.addStretch()
        total_layout.addWidget(lbl_total)
        layout.addWidget(total_frame)
        
        btns = QHBoxLayout()
        btn_confirm = QPushButton("Confirmar Pago Total")
        btn_confirm.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        btn_confirm.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_confirm)
        layout.addLayout(btns)

class CleaningPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.sync = SyncController()
        self.init_ui()
        self.load_data()
        
        # Iniciar listener de Firebase
        if self.sync.initialized:
            self.sync.start_listener(self.on_cloud_task_updated)
            self.lbl_sync_status.setText("☁️ Conectado a Firestore (Real-time)")
            self.lbl_sync_status.setStyleSheet("color: #27ae60; font-weight: bold; border: none;")
            # Sincronizar personal al iniciar
            staff = self.db.get_cleaning_staff(active_only=False)
            self.sync.sync_staff(staff)
        else:
            self.lbl_sync_status.setText("⚠️ Firebase no configurado")
            self.lbl_sync_status.setStyleSheet("color: #e74c3c; font-weight: bold; border: none;")

    def on_cloud_task_updated(self, doc_id, data):
        """Callback cuando una tarea cambia en Firebase (App Android)"""
        status = data.get('status')
        print(f"DEBUG: Tarea {doc_id} actualizada a {status}")
        
        if status == 'finished':
            # Extraer IDs de doc_id (task_IDPROP_IDRES)
            parts = doc_id.split('_')
            if len(parts) >= 3:
                # prop_id = parts[1], res_id = parts[2]
                # Buscar id_tarea local
                if not self.db.connect(): return
                cursor = self.db.connection.cursor(dictionary=True)
                cursor.execute("SELECT id_tarea FROM tareas_limpieza WHERE id_inmueble=%s AND id_reserva=%s AND estado='pendiente'", 
                             (parts[1], parts[2]))
                task = cursor.fetchone()
                if task:
                    # Completar tarea local
                    self.db.complete_cleaning_task(
                        task['id_tarea'], 
                        data.get('hours', 0), 
                        data.get('observations', '')
                    )
                    # Actualizar UI desde el hilo principal
                    QTimer.singleShot(0, self.load_data)

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
        
        self.table_staff = QTableWidget(0, 3)
        self.table_staff.setHorizontalHeaderLabels(["Nombre", "Deuda", "Acción"])
        self.table_staff.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_staff.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_staff.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_staff.verticalHeader().setDefaultSectionSize(45)
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
        self.table_pending.setHorizontalHeaderLabels(["Inmueble", "Check-out", "Tarifa/H", "Asignar A", "Acción"])
        self.table_pending.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_pending.verticalHeader().setDefaultSectionSize(50)
        self.table_pending.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_pending.setSelectionMode(QTableWidget.NoSelection)
        self.table_pending.setFocusPolicy(Qt.NoFocus)
        self.table_pending.setStyleSheet("""
            QTableWidget { 
                border: none; 
                gridline-color: #f1f3f5; 
                background-color: white; 
                color: #2c3e50;
                selection-background-color: white;
                selection-color: #2c3e50;
            }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #f1f3f5; }
            QTableWidget::item:hover { background-color: white; }
            QHeaderView::section { 
                background-color: #f8f9fa; 
                padding: 10px; 
                font-weight: bold; 
                border: none; 
                color: #7f8c8d;
                border-bottom: 2px solid #3498db;
            }
            QLineEdit, QComboBox {
                border: 1px solid #d1d8e0;
                border-radius: 4px;
                padding: 5px;
                height: 30px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #2c3e50;
                selection-background-color: #3498db;
                selection-color: white;
                border: 1px solid #d1d8e0;
                outline: 0px;
            }
            QComboBox QAbstractItemView::item {
                min-height: 35px;
                padding-left: 10px;
                background-color: white;
                color: #2c3e50;
            }
            QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover {
                background-color: #3498db;
                color: white;
            }
        """)
        right_layout.addWidget(self.table_pending)

        # --- PANEL DERECHO: HISTORIAL ---
        lbl_history_title = QLabel("✅ Limpiezas Finalizadas")
        lbl_history_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; border: none; margin-top: 30px;")
        right_layout.addWidget(lbl_history_title)
        
        self.table_history = QTableWidget(0, 6)
        self.table_history.setHorizontalHeaderLabels(["Inmueble", "Personal", "Horas", "Total", "Fecha", "Pago"])
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_history.verticalHeader().setDefaultSectionSize(50)
        self.table_history.setSelectionMode(QTableWidget.NoSelection)
        self.table_history.setFocusPolicy(Qt.NoFocus)
        self.table_history.setStyleSheet("""
            QTableWidget { 
                border: none; 
                gridline-color: #f1f3f5; 
                background-color: white; 
                color: #2c3e50;
                selection-background-color: white;
                selection-color: #2c3e50;
            }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #f1f3f5; }
            QTableWidget::item:hover { background-color: white; }
            QHeaderView::section { 
                background-color: #f8f9fa; 
                padding: 10px; 
                font-weight: bold; 
                border: none; 
                color: #7f8c8d;
                border-bottom: 2px solid #27ae60;
            }
        """)
        right_layout.addWidget(self.table_history)

        self.main_layout.addWidget(right_panel, 1)

    def load_data(self):
        if not self.db.connect(): return
        
        # 1. Cargar Personal y Deudas
        staff = self.db.get_cleaning_staff()
        debts = {d['id_personal']: d for d in self.db.get_cleaning_debts()}
        
        self.table_staff.setRowCount(0)
        for s in staff:
            sid = s[0]
            name = s[1]
            row = self.table_staff.rowCount()
            self.table_staff.insertRow(row)
            
            # Nombre
            self.table_staff.setItem(row, 0, QTableWidgetItem(name))
            
            # Deuda
            debt_data = debts.get(sid, {'deuda_total': 0.00})
            amount = float(debt_data['deuda_total'] or 0)
            debt_item = QTableWidgetItem(f"$ {amount:,.0f}")
            debt_item.setForeground(QColor("#e74c3c") if amount > 0 else QColor("#27ae60"))
            debt_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.table_staff.setItem(row, 1, debt_item)
            
            # Botón Pagar
            btn_pay = QPushButton("PAGAR")
            btn_pay.setFixedWidth(60)
            btn_pay.setCursor(Qt.PointingHandCursor)
            if amount > 0:
                btn_pay.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; border-radius: 4px; font-size: 10px;")
                btn_pay.clicked.connect(lambda checked=False, s_id=sid, s_name=name, s_amount=amount: self.pay_staff(s_id, s_name, s_amount))
            else:
                btn_pay.setEnabled(False)
                btn_pay.setStyleSheet("background-color: #bdc3c7; color: white; font-weight: bold; border-radius: 4px; font-size: 10px;")
            self.table_staff.setCellWidget(row, 2, btn_pay)
            
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
            combo_staff.addItem("📢 TODOS", None)
            for sid, name in staff_names.items():
                combo_staff.addItem(name, sid)
            self.table_pending.setCellWidget(row, 3, combo_staff)
            
            # Botón Enviar / Estado / Re-asignar
            status = p.get('task_status')
            if status:
                label_text = status.upper()
                if not p.get('staff_name'):
                    label_text = "📢 BROADCAST"
                
                # Layout para acciones de tarea existente
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                btn_reassign = QPushButton("🔄 Re-asignar")
                btn_reassign.setToolTip("Actualizar asignación o tarifa")
                btn_reassign.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; border-radius: 4px; padding: 5px;")
                btn_reassign.clicked.connect(lambda checked=False, r=row, data=p: self.reassign_task(r, data))
                
                btn_cancel = QPushButton("❌ Anular")
                btn_cancel.setToolTip("Quitar de la App y borrar asignación")
                btn_cancel.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; border-radius: 4px; padding: 5px;")
                btn_cancel.clicked.connect(lambda checked=False, data=p: self.cancel_task(data))
                
                if status in ['en_proceso', 'completada']:
                    btn_reassign.setEnabled(False)
                    btn_cancel.setEnabled(False)
                    btn_reassign.setStyleSheet("background-color: #bdc3c7; color: white; border-radius: 4px;")
                    btn_cancel.setStyleSheet("background-color: #bdc3c7; color: white; border-radius: 4px;")
                    fee_edit.setReadOnly(True)
                    combo_staff.setEnabled(False)
                
                actions_layout.addWidget(btn_reassign)
                actions_layout.addWidget(btn_cancel)
                
                widget = QWidget()
                widget.setLayout(actions_layout)
                self.table_pending.setCellWidget(row, 4, widget)
                
                # Seleccionar el personal actual en el combo
                current_staff_id = p.get('assigned_staff_id')
                if current_staff_id:
                    index = combo_staff.findData(current_staff_id)
                    if index >= 0: combo_staff.setCurrentIndex(index)
                else:
                    combo_staff.setCurrentIndex(0) # TODOS
            else:
                btn_send = QPushButton("Enviar a App")
                btn_send.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px;")
                btn_send.clicked.connect(lambda checked=False, r=row, data=p: self.assign_task(r, data))
                self.table_pending.setCellWidget(row, 4, btn_send)

        # 3. Cargar Historial
        completed = self.db.get_completed_cleanings()
        self.table_history.setRowCount(0)
        for c in completed:
            row = self.table_history.rowCount()
            self.table_history.insertRow(row)
            self.table_history.setItem(row, 0, QTableWidgetItem(c['property_name']))
            self.table_history.setItem(row, 1, QTableWidgetItem(c['staff_name']))
            self.table_history.setItem(row, 2, QTableWidgetItem(f"{c['horas_trabajadas']} hs"))
            
            pago_item = QTableWidgetItem(f"$ {float(c['pago_servicio']):,.2f}")
            pago_item.setForeground(QColor("#27ae60"))
            pago_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.table_history.setItem(row, 3, pago_item)
            
            fecha = c['fecha_finalizacion'].strftime("%d/%m/%Y %H:%M") if c['fecha_finalizacion'] else "-"
            self.table_history.setItem(row, 4, QTableWidgetItem(fecha))
            
            # Estado Pago
            pagado = c.get('pagado', 0)
            pay_status = QTableWidgetItem("💰 PAGADO" if pagado else "⏳ PENDIENTE")
            pay_status.setForeground(QColor("#27ae60") if pagado else QColor("#e67e22"))
            pay_status.setFont(QFont("Arial", 9, QFont.Bold))
            self.table_history.setItem(row, 5, pay_status)

    def add_staff(self):
        dialog = AddStaffDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data['nombre'] and data['pin']:
                if self.db.add_cleaning_staff(data):
                    # Sincronizar con Firebase
                    if self.sync.initialized:
                        staff = self.db.get_cleaning_staff(active_only=False)
                        self.sync.sync_staff(staff)
                    
                    QMessageBox.information(self, "Éxito", "Personal añadido correctamente.")
                    self.load_data()
                else:
                    QMessageBox.critical(self, "Error", "No se pudo añadir al personal.")

    def pay_staff(self, staff_id, name, amount):
        # Obtener detalle de tareas para el diálogo
        tasks = self.db.get_staff_pending_tasks(staff_id)
        if not tasks:
            QMessageBox.information(self, "Sin Tareas", "No hay tareas pendientes de pago para este empleado.")
            return
            
        dialog = StaffPaymentDialog(staff_id, name, tasks, self)
        if dialog.exec():
            if self.db.mark_all_staff_tasks_as_paid(staff_id):
                QMessageBox.information(self, "Éxito", f"Pago registrado para {name}.")
                self.load_data()
            else:
                QMessageBox.critical(self, "Error", "No se pudo registrar el pago.")

    def assign_task(self, row_idx, prop_data):
        fee_widget = self.table_pending.cellWidget(row_idx, 2)
        staff_widget = self.table_pending.cellWidget(row_idx, 3)
        
        try:
            fee = float(fee_widget.text() or 0)
        except:
            QMessageBox.warning(self, "Error", "La tarifa debe ser un número válido.")
            return

        staff_id = staff_widget.currentData()
        staff_name = staff_widget.currentText()
            
        task_data = {
            "id_inmueble": prop_data['id_inmueble'],
            "id_reserva": prop_data['id_reserva'],
            "id_personal": staff_id,
            "pago": fee
        }
        
        if self.db.assign_cleaning_task(task_data):
            # Subir a Firebase
            if self.sync.initialized:
                self.sync.upload_task(task_data)
            
            msg = f"Limpieza enviada a TODOS." if not staff_id else f"Limpieza asignada a {staff_name}."
            QMessageBox.information(self, "Tarea Enviada", 
                                    f"{msg}\nSe sincronizará con la App en tiempo real.")
            self.load_data()
        else:
            QMessageBox.critical(self, "Error", "No se pudo asignar la tarea.")

    def reassign_task(self, row_idx, prop_data):
        fee_widget = self.table_pending.cellWidget(row_idx, 2)
        staff_widget = self.table_pending.cellWidget(row_idx, 3)
        
        try:
            fee = float(fee_widget.text() or 0)
        except:
            QMessageBox.warning(self, "Error", "La tarifa debe ser un número válido.")
            return

        staff_id = staff_widget.currentData()
        staff_name = staff_widget.currentText()
            
        task_data = {
            "id_inmueble": prop_data['id_inmueble'],
            "id_reserva": prop_data['id_reserva'],
            "id_personal": staff_id,
            "pago": fee
        }
        
        if self.db.update_cleaning_task(task_data):
            # Actualizar en Firebase
            if self.sync.initialized:
                self.sync.upload_task(task_data)
            
            QMessageBox.information(self, "Tarea Actualizada", 
                                    f"La tarea ha sido re-asignada correctamente.")
            self.load_data()
        else:
            QMessageBox.critical(self, "Error", "No se pudo actualizar la tarea.")

    def cancel_task(self, prop_data):
        reply = QMessageBox.question(self, "Anular Tarea", 
                                   "¿Desea quitar esta tarea de la App y borrar la asignación actual?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.db.delete_cleaning_task(prop_data['id_inmueble'], prop_data['id_reserva']):
                # Eliminar de Firebase
                if self.sync.initialized:
                    self.sync.delete_task(prop_data['id_inmueble'], prop_data['id_reserva'])
                
                QMessageBox.information(self, "Tarea Anulada", "La tarea ha sido retirada de la App.")
                self.load_data()
            else:
                QMessageBox.critical(self, "Error", "No se pudo anular la tarea.")
