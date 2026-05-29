from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QMessageBox, 
                             QFrame, QComboBox, QCheckBox, QScrollArea, QWidget, QGridLayout,
                             QListWidget, QListWidgetItem, QInputDialog)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap, QColor
import os
from controllers.database import Database
from datetime import datetime, date, timedelta
from utils.email_sender import send_reservation_email

class ReservationFormDialog(QDialog):
    def __init__(self, parent=None, initial_data=None, reservation_id=None):
        super().__init__(parent)
        self.db = Database()
        self.reservation_id = reservation_id
        self.setWindowTitle("Nueva Reserva" if not self.reservation_id else f"Editar Reserva #{self.reservation_id}")
        self.resize(900, 720) # Reducido de 800 a 720 para pantallas más pequeñas
        
        self.property_map = {}
        self.initial_data = initial_data or {}
        
        self.init_ui()
        self.load_data()
        
        if self.reservation_id:
            self.load_reservation_to_edit()
        else:
            self.apply_initial_data()

    def init_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #f0f2f5; }
            QLineEdit, QComboBox {
                padding: 8px 12px;
                border: 1px solid #d1d8e0;
                border-radius: 6px;
                background-color: white;
                color: #2c3e50;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #3498db;
                background-color: #f7fbff;
            }
            QLabel { color: #2c3e50; font-size: 13px; }
            QPushButton#ActionBtn {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton#ActionBtn:hover { background-color: #2980b9; }
            QPushButton#CancelBtn {
                background-color: #ecf0f1;
                color: #7f8c8d;
                font-weight: bold;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton#CancelBtn:hover { background-color: #bdc3c7; color: #2c3e50; }
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #2c3e50; border: none;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(35, 0, 35, 0)
        
        title_icon = "📝" if not self.reservation_id else "✏️"
        title_text = " REGISTRO DE RESERVA" if not self.reservation_id else " EDITAR RESERVA"
        title = QLabel(f"{title_icon}{title_text}")
        title.setStyleSheet("color: white; font-size: 22px; font-weight: bold; border: none;")
        h_layout.addWidget(title)
        
        self.lbl_op_id = QLabel(f"Folio: OP-{datetime.now().strftime('%Y%m%d-%H%M')}")
        self.lbl_op_id.setStyleSheet("color: #3498db; font-size: 14px; font-weight: bold; border: none;")
        h_layout.addStretch()
        h_layout.addWidget(self.lbl_op_id)
        
        self.main_layout.addWidget(header)
        
        # Scroll Area for Content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")
        
        content = QWidget()
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(35, 30, 35, 30)
        self.layout.setSpacing(25)
        
        # --- SECTION 1: CLIENT DATA ---
        sec_client = self._create_section("👤 DATOS DEL HUÉSPED", "#3498db")
        client_grid = QGridLayout()
        client_grid.setSpacing(15)
        client_grid.setContentsMargins(0, 5, 0, 5)
        
        # Búsqueda (Fila 0, completa)
        lbl_search = QLabel("ID / Búsqueda:")
        self.edit_client_id = QLineEdit()
        self.edit_client_id.setPlaceholderText("DNI, Nombre o Apellido...")
        self.edit_client_id.setFixedHeight(40)
        self.edit_client_id.setToolTip("Escriba para ver sugerencias o presione ENTER")
        self.edit_client_id.textChanged.connect(self._on_search_text_changed)
        self.edit_client_id.returnPressed.connect(self.autofill_client)
        
        btn_search_client = QPushButton("🔍 BUSCAR")
        btn_search_client.setFixedWidth(100)
        btn_search_client.setFixedHeight(40)
        btn_search_client.setCursor(Qt.PointingHandCursor)
        btn_search_client.setStyleSheet("background-color: #34495e; color: white; font-weight: bold; border-radius: 6px;")
        btn_search_client.clicked.connect(self.autofill_client)
        
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.edit_client_id)
        search_layout.addWidget(btn_search_client)
        
        client_grid.addWidget(lbl_search, 0, 0)
        client_grid.addLayout(search_layout, 0, 1, 1, 3) 
        
        # Lista de sugerencias (oculta por defecto)
        self.suggestion_list = QListWidget()
        self.suggestion_list.setFixedHeight(100)
        self.suggestion_list.setStyleSheet("""
            QListWidget { border: 1px solid #3498db; border-radius: 5px; background: white; }
            QListWidget::item { padding: 5px; border-bottom: 1px solid #eee; }
            QListWidget::item:selected { background: #3498db; color: white; }
        """)
        self.suggestion_list.hide()
        self.suggestion_list.itemClicked.connect(self._on_suggestion_selected)
        client_grid.addWidget(self.suggestion_list, 1, 1, 1, 3)
        
        # Campos en dos columnas
        self.edit_doc = QLineEdit()
        self.edit_name = QLineEdit()
        self.edit_surname = QLineEdit()
        self.edit_email = QLineEdit()
        self.edit_phone = QLineEdit()
        
        # Columna 1
        client_grid.addWidget(QLabel("Documento (DNI/Cuit):"), 1, 0)
        client_grid.addWidget(self.edit_doc, 1, 1)
        client_grid.addWidget(QLabel("Nombre:"), 2, 0)
        client_grid.addWidget(self.edit_name, 2, 1)
        client_grid.addWidget(QLabel("Apellido:"), 3, 0)
        client_grid.addWidget(self.edit_surname, 3, 1)
        
        # Columna 2
        client_grid.addWidget(QLabel("Email:"), 1, 2)
        client_grid.addWidget(self.edit_email, 1, 3)
        client_grid.addWidget(QLabel("Teléfono:"), 2, 2)
        client_grid.addWidget(self.edit_phone, 2, 3)
        
        sec_client.layout().addLayout(client_grid)
        self.layout.addWidget(sec_client)
        
        # --- SECTION 2: STAY DETAILS ---
        sec_stay = self._create_section("🏠 DETALLES DE ESTADÍA", "#2ecc71")
        stay_layout = QHBoxLayout()
        stay_layout.setSpacing(30)
        
        stay_form = QFormLayout()
        stay_form.setSpacing(18)
        stay_form.setLabelAlignment(Qt.AlignRight)
        
        self.combo_prop = QComboBox()
        self.combo_prop.setFixedHeight(40)
        self.combo_prop.currentIndexChanged.connect(self.on_property_changed)
        
        self.edit_checkin = QLineEdit()
        self.edit_checkin.setPlaceholderText("DD/MM/YYYY")
        self.edit_checkin.setFixedHeight(40)
        self.edit_checkin.textChanged.connect(self.calculate_totals)
        
        self.edit_checkout = QLineEdit()
        self.edit_checkout.setPlaceholderText("DD/MM/YYYY")
        self.edit_checkout.setFixedHeight(40)
        self.edit_checkout.textChanged.connect(self.calculate_totals)
        
        self.edit_people = QLineEdit()
        self.edit_price_day = QLineEdit()
        self.edit_price_day.textChanged.connect(self.calculate_totals)
        
        stay_form.addRow("Inmueble:", self.combo_prop)
        stay_form.addRow("Fecha Ingreso:", self.edit_checkin)
        stay_form.addRow("Fecha Egreso:", self.edit_checkout)
        stay_form.addRow("Huéspedes:", self.edit_people)
        stay_form.addRow("Precio x Noche:", self.edit_price_day)
        
        stay_layout.addLayout(stay_form, 2)
        
        # Preview Card
        self.preview_card = QFrame()
        self.preview_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: none;
            }
        """)
        self.preview_card.setFixedWidth(280)
        prev_layout = QVBoxLayout(self.preview_card)
        prev_layout.setContentsMargins(15, 15, 15, 15)
        
        self.lbl_prev_image = QLabel()
        self.lbl_prev_image.setFixedSize(250, 160)
        self.lbl_prev_image.setAlignment(Qt.AlignCenter)
        self.lbl_prev_image.setStyleSheet("background-color: #f0f2f5; border-radius: 8px; color: #bdc3c7; border: none;")
        prev_layout.addWidget(self.lbl_prev_image, 0, Qt.AlignCenter)
        
        self.lbl_prev_name = QLabel("Seleccione un inmueble")
        self.lbl_prev_name.setWordWrap(True)
        self.lbl_prev_name.setAlignment(Qt.AlignCenter)
        self.lbl_prev_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; border: none; margin-top: 10px;")
        prev_layout.addWidget(self.lbl_prev_name)
        
        stay_layout.addWidget(self.preview_card, 1)
        
        sec_stay.layout().addLayout(stay_layout)
        self.layout.addWidget(sec_stay)
        
        # --- SECTION 3: FINANCIALS ---
        sec_fin = self._create_section("💰 RESUMEN FINANCIERO", "#f1c40f")
        fin_main_layout = QVBoxLayout()
        
        # Input row
        fin_inputs = QHBoxLayout()
        fin_inputs.setSpacing(25)
        
        # Discount Box
        disc_box = QFrame()
        disc_box.setStyleSheet("background-color: #f8f9fa; border-radius: 8px; border: 1px solid #eee; padding: 10px;")
        disc_layout = QVBoxLayout(disc_box)
        disc_layout.addWidget(QLabel("🎁 DESCUENTO"))
        disc_row = QHBoxLayout()
        self.edit_discount = QLineEdit("0")
        self.edit_discount.setFixedWidth(120)
        self.edit_discount.textChanged.connect(self.calculate_totals)
        self.chk_perc = QCheckBox("%")
        self.chk_perc.setChecked(True)
        self.chk_perc.toggled.connect(self.calculate_totals)
        disc_row.addWidget(self.edit_discount)
        disc_row.addWidget(self.chk_perc)
        disc_layout.addLayout(disc_row)
        fin_inputs.addWidget(disc_box)
        
        # Advance Box
        adv_box = QFrame()
        adv_box.setStyleSheet("background-color: #f8f9fa; border-radius: 8px; border: 1px solid #eee; padding: 10px;")
        adv_layout = QVBoxLayout(adv_box)
        adv_layout.addWidget(QLabel("💵 ADELANTO / SEÑA"))
        self.edit_advance = QLineEdit("0")
        self.edit_advance.textChanged.connect(self.calculate_totals)
        adv_layout.addWidget(self.edit_advance)
        fin_inputs.addWidget(adv_box)
        
        fin_main_layout.addLayout(fin_inputs)
        fin_main_layout.addSpacing(20)
        
        # Result grid (Modernized)
        res_frame = QFrame()
        res_frame.setStyleSheet("background-color: #2c3e50; border-radius: 8px; color: white;")
        res_layout = QGridLayout(res_frame)
        res_layout.setContentsMargins(25, 20, 25, 20)
        res_layout.setSpacing(15)
        
        def style_res_lbl(lbl, size=14, color="white", bold=False):
            weight = "bold" if bold else "normal"
            lbl.setStyleSheet(f"font-size: {size}px; color: {color}; font-weight: {weight}; border: none; background: transparent;")

        lbl1 = QLabel("Estadía:")
        self.lbl_nights = QLabel("0 noches")
        lbl2 = QLabel("Costo Base:")
        self.lbl_total = QLabel("$0,00")
        lbl3 = QLabel("TOTAL FINAL:")
        self.lbl_final = QLabel("$0,00")
        lbl4 = QLabel("SALDO PENDIENTE:")
        self.lbl_pending = QLabel("$0,00")
        
        for l in [lbl1, lbl2, lbl3, lbl4]: style_res_lbl(l, 13, "#bdc3c7")
        style_res_lbl(self.lbl_nights, 15, "white", True)
        style_res_lbl(self.lbl_total, 15, "white", True)
        style_res_lbl(self.lbl_final, 22, "#2ecc71", True)
        style_res_lbl(self.lbl_pending, 22, "#e74c3c", True)
        
        res_layout.addWidget(lbl1, 0, 0)
        res_layout.addWidget(self.lbl_nights, 0, 1)
        res_layout.addWidget(lbl2, 0, 2)
        res_layout.addWidget(self.lbl_total, 0, 3)
        res_layout.addWidget(lbl3, 1, 0)
        res_layout.addWidget(self.lbl_final, 1, 1)
        res_layout.addWidget(lbl4, 1, 2)
        res_layout.addWidget(self.lbl_pending, 1, 3)
        
        fin_main_layout.addWidget(res_frame)
        
        sec_fin.layout().addLayout(fin_main_layout)
        self.layout.addWidget(sec_fin)
        
        scroll.setWidget(content)
        self.main_layout.addWidget(scroll, 1) # Añadido factor de estiramiento 1
        
        # Action Buttons
        btns = QFrame()
        btns.setFixedHeight(90)
        btns.setStyleSheet("background-color: #f0f2f5; border: none;") # Cambiado a fondo de ventana
        btns_layout = QHBoxLayout(btns)
        btns_layout.setContentsMargins(40, 0, 40, 0)
        
        btn_cancel = QPushButton("❌ CANCELAR OPERACIÓN")
        btn_cancel.setFixedSize(220, 45)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("💾 GUARDAR CAMBIOS" if self.reservation_id else "✅ CONFIRMAR Y REGISTRAR RESERVA")
        self.btn_save.setFixedSize(350, 45)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #219150; }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.btn_save.clicked.connect(self.save_reservation)
        
        btns_layout.addWidget(btn_cancel)
        btns_layout.addStretch()
        btns_layout.addWidget(self.btn_save)
        
        self.main_layout.addWidget(btns)

    def _create_section(self, title, accent_color="#3498db"):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: white; 
                border-radius: 12px; 
                border: none;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(25, 25, 25, 25)
        
        header_layout = QHBoxLayout()
        line = QFrame()
        line.setFixedWidth(4)
        line.setFixedHeight(20)
        line.setStyleSheet(f"background-color: {accent_color}; border-radius: 2px; border: none;")
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-weight: bold; color: #2c3e50; font-size: 15px; border: none; margin-left: 5px;")
        
        header_layout.addWidget(line)
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        layout.addSpacing(15)
        return frame

    def load_data(self):
        if not self.db.connect(): return
        props = self.db.get_all_properties()
        self.property_map = {p[1]: p for p in props}
        self.combo_prop.addItems(sorted(list(self.property_map.keys())))

    def apply_initial_data(self):
        d = self.initial_data
        if "inmueble" in d: 
            self.combo_prop.setCurrentText(d["inmueble"])
            self.lbl_prev_name.setText(d["inmueble"])
        if "fecha_ingreso" in d: self.edit_checkin.setText(d["fecha_ingreso"])
        if "fecha_egreso" in d: self.edit_checkout.setText(d["fecha_egreso"])
        if "cantidad_personas" in d: self.edit_people.setText(str(d["cantidad_personas"]))
        if "descuento" in d: self.edit_discount.setText(str(d["descuento"]))
        if "discount_is_percentage" in d: self.chk_perc.setChecked(d["discount_is_percentage"])
        if "id_cliente" in d: 
            self.edit_client_id.setText(str(d["id_cliente"]))
            self.autofill_client()
        
        # Load initial image if provided
        if "imagen" in d:
            self.update_preview_image(d["imagen"])
        elif "inmueble" in d:
            self.on_property_changed()
        
        self.calculate_totals()

    def load_reservation_to_edit(self):
        if not self.db.connect(): return
        # r = (client_id, prop_id, f_in, f_out, val_d, noches, total, total_desc, adelanto, pendiente, prov)
        r = self.db.get_reservation_by_id(self.reservation_id)
        if r:
            self.edit_client_id.setText(str(r[0]))
            self.autofill_client()
            
            # Find property name from id
            prop_name = next((name for name, data in self.property_map.items() if data[0] == r[1]), "")
            self.combo_prop.setCurrentText(prop_name)
            self.lbl_prev_name.setText(prop_name)
            
            # Update image
            if prop_name in self.property_map:
                self.update_preview_image(self.property_map[prop_name][8])
            
            self.edit_checkin.setText(r[2].strftime("%d/%m/%Y") if isinstance(r[2], (date, datetime)) else str(r[2]))
            self.edit_checkout.setText(r[3].strftime("%d/%m/%Y") if isinstance(r[3], (date, datetime)) else str(r[3]))
            self.edit_price_day.setText(str(r[4]))
            self.edit_advance.setText(str(r[8]))
            # Calculate discount
            total = float(r[6])
            total_desc = float(r[7])
            discount = total - total_desc
            self.edit_discount.setText(str(discount))
            self.chk_perc.setChecked(False) 
            
            self.calculate_totals()

    def update_preview_image(self, path):
        if path and os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.lbl_prev_image.setPixmap(pixmap.scaled(
                    self.lbl_prev_image.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                ))
                self.lbl_prev_image.setText("")
                return
        self.lbl_prev_image.setPixmap(QPixmap())
        self.lbl_prev_image.setText("🖼️")

    def on_property_changed(self):
        name = self.combo_prop.currentText()
        if name in self.property_map:
            p = self.property_map[name]
            self.edit_price_day.setText(str(p[7]))
            self.edit_people.setText(str(p[2]))
            self.lbl_prev_name.setText(name)
            self.update_preview_image(p[8])
        self.calculate_totals()

    def _on_search_text_changed(self, text):
        query = text.strip()
        if len(query) < 3:
            self.suggestion_list.hide()
            return

        if not self.db.connect(): return
        results = self.db.search_contacts(query)
        
        if not results:
            self.suggestion_list.hide()
            return

        self.suggestion_list.clear()
        for res in results:
            # res = (id, doc, nombre, apellido, email, tel, tipo)
            display = f"{res[2]} {res[3]} (DNI: {res[1]})"
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, res)
            if res[6] == 'cliente':
                item.setForeground(QColor("#27ae60"))
            self.suggestion_list.addItem(item)
        
        self.suggestion_list.show()

    def _on_suggestion_selected(self, item):
        data = item.data(Qt.UserRole)
        self._fill_client_fields(data)
        self.suggestion_list.hide()

    def _fill_client_fields(self, data):
        # data = (id, doc, nombre, apellido, email, tel, tipo)
        self.edit_client_id.blockSignals(True)
        self.edit_client_id.setText(str(data[0]))
        self.edit_client_id.blockSignals(False)
        
        self.edit_doc.setText(str(data[1]) if data[1] else "")
        self.edit_name.setText(str(data[2]) if data[2] else "")
        self.edit_surname.setText(str(data[3]) if data[3] else "")
        self.edit_email.setText(str(data[4]) if data[4] else "")
        self.edit_phone.setText(str(data[5]) if data[5] else "")

    def autofill_client(self):
        query = self.edit_client_id.text().strip()
        if not query: return
        if not self.db.connect(): return
        
        # 1. Intentar búsqueda exacta por ID/DNI
        client = self.db.get_client_by_id(query)
        if not client:
            client = self.db.get_prospect_by_id(query)
            
        if client:
            # Adaptar formato de get_client_by_id a nuestro estándar (id, doc, nom, ape, email, tel)
            # get_client_by_id retorna (id, nom, ape, email, tel, doc)
            formatted = (client[0], client[5], client[1], client[2], client[3], client[4], 'cliente')
            self._fill_client_fields(formatted)
            self.suggestion_list.hide()
            return

        # 2. Si no es búsqueda exacta, usar búsqueda por nombre/apellido
        results = self.db.search_contacts(query)
        if not results:
            QMessageBox.warning(self, "No encontrado", "No se encontró ningún contacto con ese criterio.")
            return

        if len(results) == 1:
            self._fill_client_fields(results[0])
            self.suggestion_list.hide()
        else:
            # Mostrar diálogo de selección simple
            items = [f"{r[2]} {r[3]} (DNI: {r[1]}) - {r[6].upper()}" for r in results]
            item, ok = QInputDialog.getItem(self, "Seleccionar Contacto", 
                                          "Se encontraron múltiples coincidencias:", items, 0, False)
            if ok and item:
                index = items.index(item)
                self._fill_client_fields(results[index])
                self.suggestion_list.hide()

    def open_client_search(self):
        QMessageBox.information(self, "Búsqueda", "Use el campo ID/Buscar y presione Enter")

    def calculate_totals(self):
        try:
            val_dia = float(self.edit_price_day.text() or 0)
            f_in = datetime.strptime(self.edit_checkin.text(), "%d/%m/%Y")
            f_out = datetime.strptime(self.edit_checkout.text(), "%d/%m/%Y")
            noches = (f_out - f_in).days
            if noches <= 0: raise ValueError()
            
            total = noches * val_dia
            disc = float(self.edit_discount.text() or 0)
            if self.chk_perc.isChecked():
                total_desc = total - (total * (disc / 100))
            else:
                total_desc = total - disc
                
            adelanto = float(self.edit_advance.text() or 0)
            pendiente = total_desc - adelanto
            
            self.lbl_nights.setText(f"{noches} noches")
            self.lbl_total.setText(f"${total:,.2f}")
            self.lbl_final.setText(f"${total_desc:,.2f}")
            self.lbl_pending.setText(f"${pendiente:,.2f}")
            self.btn_save.setEnabled(True)
        except:
            self.lbl_nights.setText("0 noches")
            self.lbl_total.setText("$0,00")
            self.lbl_final.setText("$0,00")
            self.lbl_pending.setText("$0,00")
            self.btn_save.setEnabled(False)

    def save_reservation(self):
        if not all([self.edit_doc.text(), self.edit_name.text(), self.edit_checkin.text(), self.edit_checkout.text()]):
            QMessageBox.warning(self, "Faltan Datos", "Complete todos los campos obligatorios.")
            return

        cid = self.edit_client_id.text().strip()
        doc = self.edit_doc.text().strip()
        nom = self.edit_name.text().strip()
        ape = self.edit_surname.text().strip()
        email = self.edit_email.text().strip()
        tel = self.edit_phone.text().strip()
        
        if not self.db.connect(): return
        cursor = self.db.connection.cursor()
        
        existing_client = self.db.get_client_by_id(cid) if cid else None
        if not existing_client:
            query = "INSERT INTO clientes (documento, nombre, apellido, email, telefono) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (doc, nom, ape, email, tel))
            cid = cursor.lastrowid
        else:
            query = "UPDATE clientes SET documento=%s, nombre=%s, apellido=%s, email=%s, telefono=%s WHERE id_clientes=%s"
            cursor.execute(query, (doc, nom, ape, email, tel, cid))
        
        p_name = self.combo_prop.currentText()
        id_inm = self.property_map[p_name][0]
        
        try:
            f_in = datetime.strptime(self.edit_checkin.text(), "%d/%m/%Y").date()
            f_out = datetime.strptime(self.edit_checkout.text(), "%d/%m/%Y").date()
        except:
            QMessageBox.warning(self, "Error", "Formato de fecha inválido (DD/MM/YYYY)")
            return
        
        noches = (f_out - f_in).days
        val_dia = float(self.edit_price_day.text())
        total = noches * val_dia
        disc = float(self.edit_discount.text() or 0)
        if self.chk_perc.isChecked():
            costo_final = total - (total * (disc / 100))
        else:
            costo_final = total - disc
            
        adelanto = float(self.edit_advance.text() or 0)
        pendiente = costo_final - adelanto
        
        if self.reservation_id:
            query = """UPDATE reservas SET id_clientes=%s, id_inmuebles=%s, fecha_ingreso=%s, fecha_egreso=%s, 
                       valor_dia=%s, noches=%s, costo_total=%s, costo_con_descuento=%s, adelanto=%s, 
                       pago_pendiente=%s, provincia=%s WHERE id_reservas=%s"""
            params = (cid, id_inm, f_in, f_out, val_dia, noches, total, costo_final, adelanto, 
                      pendiente, self.property_map[p_name][5], self.reservation_id)
            cursor.execute(query, params)
            rid = self.reservation_id
        else:
            res_data = {
                "id_cliente": cid, "id_inmueble": id_inm, "fecha_ingreso": f_in, "fecha_egreso": f_out,
                "valor_dia": val_dia, "noches": noches, "costo_total": total, "costo_con_descuento": costo_final,
                "adelanto": adelanto, "pago_pendiente": pendiente, "provincia": self.property_map[p_name][5]
            }
            rid = self.db.insert_reservation(res_data)
        
        if rid:
            self.db.connection.commit()
            QMessageBox.information(self, "Éxito", "Reserva guardada correctamente.")
            if not self.reservation_id: # Solo enviar si es nueva
                try:
                    email_data = {"id_reserva": rid, "inmueble": p_name, "fecha_ingreso": f_in.strftime("%d/%m/%Y"),
                                  "fecha_egreso": f_out.strftime("%d/%m/%Y"), "noches": noches, 
                                  "costo_con_descuento": costo_final, "adelanto": adelanto, "pago_pendiente": pendiente}
                    send_reservation_email(email, f"{nom} {ape}", email_data)
                except: pass
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudo guardar la reserva.")
