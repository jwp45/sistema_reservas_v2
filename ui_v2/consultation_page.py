import os
import calendar
from datetime import date, datetime, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QGridLayout, 
                             QScrollArea, QComboBox, QRadioButton, QButtonGroup,
                             QCheckBox, QMessageBox, QListWidget, QListWidgetItem,
                             QDialog, QInputDialog, QApplication)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor, QFont, QPalette, QPixmap
from controllers.database import Database
from utils.email_sender import send_quotation_email
from utils.whatsapp_sender import send_whatsapp_quotation
from ui_v2.reservation_form import ReservationFormDialog
from ui_v2.advanced_search_dialog import AdvancedSearchDialog
from ui_v2.gallery_dialog import GalleryDialog
from ui_v2.property_services_dialog import PropertyServicesDialog
import webbrowser
import urllib.parse

class QuoteImageSelectorDialog(QDialog):
    def __init__(self, parent=None, image_paths=None):
        super().__init__(parent)
        self.image_paths = image_paths or []
        self.selected_paths = []
        self.setWindowTitle("Seleccionar Fotos para Cotización")
        self.resize(600, 700)
        self.setStyleSheet("background-color: #f8f9fa;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        header = QLabel("📸 SELECCIONAR HASTA 10 FOTOS")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; padding: 10px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: white;")
        
        container = QWidget()
        self.grid = QVBoxLayout(container)
        
        self.check_boxes = []
        for i, path in enumerate(self.image_paths):
            item = QFrame()
            item.setStyleSheet("background-color: white; border-bottom: 1px solid #eee;")
            item_layout = QHBoxLayout(item)
            
            cb = QCheckBox()
            if i < 10: cb.setChecked(True)
            item_layout.addWidget(cb)
            
            lbl_img = QLabel()
            lbl_img.setFixedSize(100, 70)
            pix = QPixmap(path)
            if not pix.isNull():
                lbl_img.setPixmap(pix.scaled(100, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            item_layout.addWidget(lbl_img)
            
            lbl_name = QLabel(os.path.basename(path))
            lbl_name.setStyleSheet("color: #2c3e50;")
            item_layout.addWidget(lbl_name, 1)
            
            self.grid.addWidget(item)
            self.check_boxes.append((path, cb))
            
        scroll.setWidget(container)
        layout.addWidget(scroll)

        btn_confirm = QPushButton("📧 CONFIRMAR Y ENVIAR COTIZACIÓN")
        btn_confirm.setFixedHeight(50)
        btn_confirm.setStyleSheet("""
            QPushButton { 
                background-color: #27ae60; color: white; font-weight: bold; 
                border-radius: 5px; font-size: 14px; 
            }
            QPushButton:hover { background-color: #219150; }
        """)
        btn_confirm.clicked.connect(self.accept_selection)
        layout.addWidget(btn_confirm)

    def accept_selection(self):
        self.selected_paths = [p for p, cb in self.check_boxes if cb.isChecked()]
        if not self.selected_paths:
            QMessageBox.warning(self, "Atención", "Debe seleccionar al menos una foto.")
            return
        if len(self.selected_paths) > 10:
            QMessageBox.warning(self, "Atención", f"Límite excedido: {len(self.selected_paths)}/10 fotos.")
            return
        self.accept()

class DayButton(QPushButton):
    def __init__(self, day, full_date, status="disponible", parent=None):
        super().__init__(str(day), parent)
        self.full_date = full_date
        self.status = status
        self.setFixedSize(65, 65) # Aumentado de 45x45 a 65x65
        self.setCursor(Qt.PointingHandCursor)
        self.update_style()

    def update_style(self, is_selected=False):
        colors = {
            "disponible": "#27ae60",
            "ingreso": "#3498db",
            "ocupado": "#e74c3c",
            "egreso": "#9b59b6",
            "transicion": "#f1c40f",
            "pasado": "#d1d8e0"
        }
        
        bg = colors.get(self.status, "#27ae60")
        fg = "white" if self.status != "pasado" else "#7f8c8d"
        
        if is_selected:
            bg = "#2980b9"
            fg = "white"
            
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border-radius: 8px;
                font-weight: bold;
                font-size: 18px; /* Aumentado de 14px a 18px */
                border: none;
            }}
            QPushButton:hover {{
                background-color: {QColor(bg).darker(110).name()};
            }}
        """)

class SearchInput(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(42)
        self.setStyleSheet("""
            QLineEdit {
                padding-left: 15px;
                padding-right: 15px;
                border-radius: 21px;
                border: 1px solid #d1d8e0;
                background-color: white;
                color: #2c3e50;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: #fdfeff;
            }
        """)

class ConsultationPage(QWidget):
    def __init__(self, reservation_controller=None, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.controller = reservation_controller
        
        # State
        self.selected_property = None
        self.reserved_ranges = []
        self.start_date = None
        self.end_date = None
        self.all_properties = []
        self.property_map = {}
        self.day_buttons = [] # Pool de botones para estabilidad
        
        self.now = date.today()
        self.view_year = self.now.year
        self.view_month = self.now.month
        
        self.init_ui()
        self.load_initial_data()

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(20)

        # --- LEFT PANEL (Controls & Selection) ---
        self.left_panel = QFrame()
        self.left_panel.setFixedWidth(380)
        self.left_panel.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #e0e0e0;")
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(20, 20, 20, 20)
        self.left_layout.setSpacing(15)

        # Title
        lbl_title = QLabel("Detalles de Selección")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; border: none; margin-bottom: 5px;")
        self.left_layout.addWidget(lbl_title)

        # Selection Summary Card
        self.summary_card = QFrame()
        self.summary_card.setStyleSheet("background-color: #f8f9fa; border-radius: 10px; border: 1px solid #eee;")
        summary_layout = QVBoxLayout(self.summary_card)
        summary_layout.setSpacing(8) # Más espacio entre líneas
        summary_layout.setContentsMargins(20, 20, 20, 20)
        
        self.lbl_prop_name = QLabel("Inmueble: No seleccionado")
        self.lbl_prop_name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_prop_name.setStyleSheet("font-size: 15px; font-weight: bold; color: #2c3e50; border: none;")
        
        self.lbl_dates = QLabel("Estadía: -")
        self.lbl_dates.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_dates.setStyleSheet("font-size: 14px; color: #34495e; border: none;")
        
        self.lbl_nights = QLabel("Noches: 0")
        self.lbl_nights.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_nights.setStyleSheet("font-size: 16px; color: #2980b9; font-weight: bold; border: none;")
        
        self.lbl_total = QLabel("Costo Total: $0,00")
        self.lbl_total.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_total.setStyleSheet("font-size: 22px; font-weight: bold; color: #27ae60; border: none;")

        self.lbl_discount_amount = QLabel("")
        self.lbl_discount_amount.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_discount_amount.setStyleSheet("font-size: 14px; color: #e74c3c; font-weight: bold; border: none;")
        self.lbl_discount_amount.hide()
        
        summary_layout.addWidget(self.lbl_prop_name, 0, Qt.AlignLeft)
        summary_layout.addWidget(self.lbl_dates, 0, Qt.AlignLeft)
        summary_layout.addWidget(self.lbl_nights, 0, Qt.AlignLeft)
        summary_layout.addSpacing(10) # Espacio antes del total
        summary_layout.addWidget(self.lbl_total, 0, Qt.AlignLeft)
        summary_layout.addWidget(self.lbl_discount_amount, 0, Qt.AlignLeft)
        self.left_layout.addWidget(self.summary_card)

        # Negotiation Section
        lbl_neg = QLabel("💰 NEGOCIACIÓN")
        lbl_neg.setStyleSheet("font-size: 12px; font-weight: bold; color: #7f8c8d; border: none; margin-top: 10px;")
        self.left_layout.addWidget(lbl_neg)
        
        neg_layout = QHBoxLayout()
        self.btn_group_disc = QButtonGroup(self)
        self.rad_perc = QRadioButton("%")
        self.rad_perc.setChecked(True)
        self.rad_abs = QRadioButton("$")
        self.btn_group_disc.addButton(self.rad_perc)
        self.btn_group_disc.addButton(self.rad_abs)
        neg_layout.addWidget(QLabel("Tipo:"))
        neg_layout.addWidget(self.rad_perc)
        neg_layout.addWidget(self.rad_abs)
        neg_layout.addStretch()
        self.left_layout.addLayout(neg_layout)
        
        self.edit_discount = QLineEdit("0")
        self.edit_discount.setFixedHeight(35)
        self.edit_discount.setStyleSheet("padding-left: 10px; border: 1px solid #d1d8e0; border-radius: 5px; color: #2c3e50; background-color: white;")
        self.edit_discount.textChanged.connect(self.update_pricing)
        self.left_layout.addWidget(self.edit_discount)

        # Lead Section
        lbl_quote = QLabel("📋 COTIZACIÓN")
        lbl_quote.setStyleSheet("font-size: 12px; font-weight: bold; color: #7f8c8d; border: none; margin-top: 10px;")
        self.left_layout.addWidget(lbl_quote)
        
        self.edit_lead_name = SearchInput("🔍 Nombre del cliente")
        self.edit_lead_name.textChanged.connect(self._on_name_text_changed)
        self.left_layout.addWidget(self.edit_lead_name)

        # Suggestion List (initially hidden)
        self.suggestion_list = QListWidget()
        self.suggestion_list.setFixedHeight(120)
        self.suggestion_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #d1d8e0;
                border-radius: 10px;
                background-color: white;
                color: #2c3e50;
            }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #f0f2f5; }
            QListWidget::item:selected { background-color: #3498db; color: white; border-radius: 5px; }
        """)
        self.suggestion_list.hide()
        self.suggestion_list.itemClicked.connect(self._on_suggestion_clicked)
        self.left_layout.addWidget(self.suggestion_list)
        
        self.edit_lead_phone = SearchInput("📞 Teléfono")
        self.left_layout.addWidget(self.edit_lead_phone)
        
        self.edit_lead_email = SearchInput("📧 Email")
        self.left_layout.addWidget(self.edit_lead_email)

        self.check_include_photos = QCheckBox("📸 Incluir fotos (max 10)")
        self.check_include_photos.setStyleSheet("color: #2c3e50; border: none; margin-top: 5px;")
        self.left_layout.addWidget(self.check_include_photos)

        # Action Buttons
        self.btn_send_email = QPushButton("📧 Enviar por Email")
        self.btn_send_email.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; height: 40px; border: none;")
        self.btn_send_email.clicked.connect(self.send_email)
        self.left_layout.addWidget(self.btn_send_email)

        self.btn_send_wa = QPushButton("✅ Enviar por WhatsApp")
        self.btn_send_wa.setStyleSheet("background-color: #25D366; color: white; font-weight: bold; height: 40px; border: none;")
        self.btn_send_wa.clicked.connect(self.send_wa)
        self.left_layout.addWidget(self.btn_send_wa)
        
        self.btn_reserve = QPushButton("🚀 RESERVAR AHORA")
        self.btn_reserve.setEnabled(False)
        self.btn_reserve.setStyleSheet("""
            QPushButton { background-color: #3498db; color: white; font-weight: bold; height: 45px; border-radius: 5px; border: none; }
            QPushButton:disabled { background-color: #bdc3c7; }
        """)
        self.btn_reserve.clicked.connect(self.go_to_reservation)
        self.left_layout.addWidget(self.btn_reserve)

        # More Info Buttons (Below Reservar Ahora)
        info_btns_layout = QHBoxLayout()
        
        self.btn_view_gallery = QPushButton("📸 Ver Fotos")
        self.btn_view_gallery.setEnabled(False)
        self.btn_view_gallery.setCursor(Qt.PointingHandCursor)
        self.btn_view_gallery.setStyleSheet("""
            QPushButton { background-color: #2c3e50; color: white; font-weight: bold; height: 35px; border-radius: 5px; border: none; }
            QPushButton:hover { background-color: #34495e; }
            QPushButton:disabled { background-color: #ecf0f1; color: #bdc3c7; }
        """)
        self.btn_view_gallery.clicked.connect(self.open_gallery)
        
        self.btn_view_services = QPushButton("✨ Servicios")
        self.btn_view_services.setEnabled(False)
        self.btn_view_services.setCursor(Qt.PointingHandCursor)
        self.btn_view_services.setStyleSheet("""
            QPushButton { background-color: #2c3e50; color: white; font-weight: bold; height: 35px; border-radius: 5px; border: none; }
            QPushButton:hover { background-color: #34495e; }
            QPushButton:disabled { background-color: #ecf0f1; color: #bdc3c7; }
        """)
        self.btn_view_services.clicked.connect(self.open_services)
        
        info_btns_layout.addWidget(self.btn_view_gallery)
        info_btns_layout.addWidget(self.btn_view_services)
        self.left_layout.addLayout(info_btns_layout)
        
        self.left_layout.addStretch()
        self.main_layout.addWidget(self.left_panel)

        # --- RIGHT PANEL (Filters & Calendar) ---
        self.right_content = QWidget()
        self.right_layout = QVBoxLayout(self.right_content)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(20)

        # Filters Row (Contenedor Principal)
        self.filter_card = QFrame()
        self.filter_card.setFixedWidth(800) # Ancho fijo para control total de la estética
        self.filter_card.setStyleSheet("""
            QFrame {
                background-color: white; 
                border-radius: 12px; 
                border: 1px solid #e0e0e0;
            }
        """)
        
        # Layout Vertical para el Card
        filter_v_layout = QVBoxLayout(self.filter_card)
        filter_v_layout.setContentsMargins(15, 10, 15, 10)
        filter_v_layout.setSpacing(5)

        # --- FILA 1: PRINCIPAL (Siempre visible) ---
        main_row = QHBoxLayout()
        main_row.setSpacing(15)

        combo_style = """
            QComboBox {
                border: 1px solid #d1d8e0;
                border-radius: 8px;
                padding: 5px 12px;
                background: white;
                color: #2c3e50;
                min-width: 120px;
                height: 30px;
                combobox-popup: 0;
            }
            QComboBox:hover { border: 1px solid #3498db; }
            QComboBox::drop-down { border: 0px; }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #7f8c8d;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView, QListView {
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
            }
        """

        lbl_tipo = QLabel("Tipo:")
        lbl_tipo.setStyleSheet("font-weight: bold; color: #7f8c8d; border: none;")
        main_row.addWidget(lbl_tipo)
        
        self.combo_tipo = QComboBox()
        self.combo_tipo.setStyleSheet(combo_style)
        self.combo_tipo.currentTextChanged.connect(self.apply_filters)
        main_row.addWidget(self.combo_tipo)

        lbl_sel = QLabel("🏠 Inmueble:")
        lbl_sel.setStyleSheet("font-weight: bold; color: #2c3e50; border: none;")
        main_row.addWidget(lbl_sel)
        
        self.combo_prop = QComboBox()
        self.combo_prop.setFixedWidth(250)
        self.combo_prop.setStyleSheet(combo_style.replace("min-width: 120px;", "min-width: 200px; font-weight: bold; border: 1px solid #3498db;"))
        self.combo_prop.currentIndexChanged.connect(self.on_property_selected)
        main_row.addWidget(self.combo_prop)

        # Botón Lupa
        btn_adv_search = QPushButton("🔍")
        btn_adv_search.setFixedSize(38, 38)
        btn_adv_search.setCursor(Qt.PointingHandCursor)
        btn_adv_search.setToolTip("Búsqueda Avanzada")
        btn_adv_search.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #d1d8e0;
                border-radius: 19px;
                font-size: 16px;
            }
            QPushButton:hover { background-color: #e9ecef; border: 1px solid #3498db; }
        """)
        btn_adv_search.clicked.connect(self.open_advanced_search)
        main_row.addWidget(btn_adv_search)
        
        main_row.addStretch()

        # Botón de Toggle Ubicación
        self.btn_toggle_location = QPushButton("📍 Ubicación")
        self.btn_toggle_location.setCheckable(True)
        self.btn_toggle_location.setFixedSize(110, 32)
        self.btn_toggle_location.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_location.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #d1d8e0;
                border-radius: 8px;
                color: #7f8c8d;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:checked {
                background-color: #e3f2fd;
                border: 1px solid #3498db;
                color: #3498db;
            }
        """)
        main_row.addWidget(self.btn_toggle_location)
        filter_v_layout.addLayout(main_row)

        # --- FILA 2: UBICACIÓN (Colapsable hacia abajo) ---
        self.location_widget = QWidget()
        self.location_widget.setStyleSheet("border: none; background: #fdfdfe; border-radius: 8px;")
        location_layout = QHBoxLayout(self.location_widget)
        location_layout.setContentsMargins(10, 10, 10, 10)
        location_layout.setSpacing(20)

        lbl_prov = QLabel("Provincia:")
        lbl_prov.setStyleSheet("font-weight: bold; color: #7f8c8d; border: none;")
        location_layout.addWidget(lbl_prov)
        
        self.combo_prov = QComboBox()
        self.combo_prov.setStyleSheet(combo_style)
        self.combo_prov.currentTextChanged.connect(self.apply_filters)
        location_layout.addWidget(self.combo_prov)

        lbl_loc = QLabel("Localidad:")
        lbl_loc.setStyleSheet("font-weight: bold; color: #7f8c8d; border: none;")
        location_layout.addWidget(lbl_loc)
        
        self.combo_loc = QComboBox()
        self.combo_loc.setStyleSheet(combo_style)
        self.combo_loc.currentTextChanged.connect(self.apply_filters)
        location_layout.addWidget(self.combo_loc)
        location_layout.addStretch()

        self.btn_toggle_location.toggled.connect(self._toggle_location_filters)
        self.location_widget.setVisible(False)
        filter_v_layout.addWidget(self.location_widget)
        
        # Añadir el card al layout de la derecha
        self.right_layout.addWidget(self.filter_card, 0, Qt.AlignLeft)

        # Property Details Quick Info (Above Calendar)
        self.info_card = QFrame()
        self.info_card.setStyleSheet("background-color: #f8f9fa; border-radius: 8px; border: 1px solid #e0e0e0;")
        info_layout = QHBoxLayout(self.info_card)
        info_layout.setContentsMargins(15, 8, 15, 8)
        
        self.lbl_capacidad = QLabel("👥 Capacidad: —")
        self.lbl_capacidad.setStyleSheet("font-weight: bold; color: #2c3e50; border: none;")
        
        self.lbl_precio_noche = QLabel("💰 Precio/Noche: —")
        self.lbl_precio_noche.setStyleSheet("font-weight: bold; color: #27ae60; border: none;")
        
        self.lbl_ubicacion = QLabel("📍 Ubicación: —")
        self.lbl_ubicacion.setStyleSheet("color: #7f8c8d; border: none;")
        
        info_layout.addWidget(self.lbl_capacidad)
        info_layout.addSpacing(20)
        info_layout.addWidget(self.lbl_precio_noche)
        info_layout.addSpacing(20)
        info_layout.addWidget(self.lbl_ubicacion)
        info_layout.addStretch()
        
        self.right_layout.addWidget(self.info_card)

        # Calendar Card
        self.cal_card = QFrame()
        self.cal_card.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #e0e0e0;")
        self.cal_layout = QVBoxLayout(self.cal_card)
        self.cal_layout.setContentsMargins(20, 20, 20, 20)
        
        # Calendar Header
        cal_header = QHBoxLayout()
        btn_prev = QPushButton("<<")
        btn_prev.setFixedSize(50, 40) # Aumentado de 40, 30
        btn_prev.clicked.connect(self.prev_month)
        
        self.lbl_month = QLabel("MES AÑO")
        self.lbl_month.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50; border: none;") # Aumentado de 18px
        self.lbl_month.setAlignment(Qt.AlignCenter)
        
        btn_next = QPushButton(">>")
        btn_next.setFixedSize(50, 40) # Aumentado de 40, 30
        btn_next.clicked.connect(self.next_month)
        
        cal_header.addWidget(btn_prev)
        cal_header.addWidget(self.lbl_month)
        cal_header.addWidget(btn_next)
        self.cal_layout.addLayout(cal_header)
        
        # Day Names Header
        self.days_grid = QGridLayout()
        self.days_grid.setSpacing(8) # Aumentado de 5
        day_names = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        for i, name in enumerate(day_names):
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #95a5a6; font-weight: bold; font-size: 14px; padding: 10px; border: none;")
            self.days_grid.addWidget(lbl, 0, i)

        # Crear POOL fijo de botones (6 semanas * 7 días) para estabilidad total
        for row in range(1, 7):
            for col in range(7):
                btn = DayButton(0, date.today(), "disponible")
                btn.hide() # Se mostrarán según el mes
                self.days_grid.addWidget(btn, row, col)
                self.day_buttons.append(btn)
            
        self.cal_layout.addLayout(self.days_grid)
        self.right_layout.addWidget(self.cal_card)
        
        # Legend
        legend_row = QHBoxLayout()
        self._add_legend_item(legend_row, "#27ae60", "Disponible")
        self._add_legend_item(legend_row, "#3498db", "Ingreso")
        self._add_legend_item(legend_row, "#e74c3c", "Ocupado")
        self._add_legend_item(legend_row, "#9b59b6", "Egreso")
        self._add_legend_item(legend_row, "#f1c40f", "Transición")
        self._add_legend_item(legend_row, "#2980b9", "Tu Selección")
        self.right_layout.addLayout(legend_row)
        
        self.right_layout.addStretch()
        self.main_layout.addWidget(self.right_content, 1)

    def _toggle_location_filters(self, visible):
        self.location_widget.setVisible(visible)
        # Forzar que el layout recalcule y el contenedor se ajuste de forma segura
        self.filter_card.adjustSize()
        self.filter_card.updateGeometry()

    def _add_legend_item(self, layout, color, text):
        dot = QFrame()
        dot.setFixedSize(12, 12)
        dot.setStyleSheet(f"background-color: {color}; border-radius: 6px; border: none;")
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #7f8c8d; font-size: 11px; border: none;")
        layout.addWidget(dot)
        layout.addWidget(lbl)
        layout.addSpacing(15)

    def load_initial_data(self):
        if not self.db.connect(): return
        self.all_properties = self.db.get_all_properties()
        
        provincias = sorted(list(set(p[5] for p in self.all_properties)))
        localidades = sorted(list(set(p[4] for p in self.all_properties)))
        tipos = sorted(list(set(p[6] for p in self.all_properties)))
        
        self.combo_prov.blockSignals(True)
        self.combo_prov.clear()
        self.combo_prov.addItem("Todas")
        self.combo_prov.addItems(provincias)
        self.combo_prov.blockSignals(False)

        self.combo_loc.blockSignals(True)
        self.combo_loc.clear()
        self.combo_loc.addItem("Todas")
        self.combo_loc.addItems(localidades)
        self.combo_loc.blockSignals(False)
        
        self.combo_tipo.blockSignals(True)
        self.combo_tipo.clear()
        self.combo_tipo.addItem("Todos")
        self.combo_tipo.addItems(tipos)
        self.combo_tipo.blockSignals(False)
        
        self.apply_filters()

    def apply_filters(self):
        prov = self.combo_prov.currentText()
        loc = self.combo_loc.currentText()
        tipo = self.combo_tipo.currentText()
        
        filtered = []
        for p in self.all_properties:
            match_prov = (prov == "Todas" or p[5] == prov)
            match_loc = (loc == "Todas" or p[4] == loc)
            match_tipo = (tipo == "Todos" or p[6] == tipo)
            if match_prov and match_loc and match_tipo:
                filtered.append(p)
        
        self.property_map = {p[1]: p for p in filtered}
        self.combo_prop.blockSignals(True)
        self.combo_prop.clear()
        self.combo_prop.addItems(sorted(list(self.property_map.keys())))
        self.combo_prop.blockSignals(False)
        
        if filtered:
            self.on_property_selected()

    def on_property_selected(self):
        name = self.combo_prop.currentText()
        if name in self.property_map:
            self.selected_property = self.property_map[name]
            p = self.selected_property
            self.lbl_prop_name.setText(f"Inmueble: {name}")
            
            # Update Quick Info
            self.lbl_capacidad.setText(f"👥 Capacidad: {p[2]} personas")
            self.lbl_precio_noche.setText(f"💰 Precio/Noche: ${float(p[7]):,.0f}".replace(",", "."))
            self.lbl_ubicacion.setText(f"📍 Ubicación: {p[3]}, {p[4]} ({p[5]})")
            
            self.btn_view_gallery.setEnabled(True)
            self.btn_view_services.setEnabled(True)
            self.reserved_ranges = self.db.get_reserved_ranges(id_inmueble=self.selected_property[0])
            self.reset_selection()
        else:
            self.selected_property = None
            self.lbl_prop_name.setText("Inmueble: No seleccionado")
            self.lbl_capacidad.setText("👥 Capacidad: —")
            self.lbl_precio_noche.setText("💰 Precio/Noche: —")
            self.lbl_ubicacion.setText("📍 Ubicación: —")
            self.btn_view_gallery.setEnabled(False)
            self.btn_view_services.setEnabled(False)
            self.draw_calendar()

    def open_services(self):
        if not self.selected_property: return
        if not self.db.connect(): return
        
        # p = (id, nombre, cap, dir, loc, prov, tipo, val, img, dorms, cams, banos)
        p = self.selected_property
        servs = self.db.get_property_services(p[0])
        
        dialog = PropertyServicesDialog(self, property_data=p, services=servs)
        dialog.exec()

    def open_gallery(self):
        if not self.selected_property: return
        
        if not self.db.connect(): return
        images = self.db.get_gallery_images(self.selected_property[0])
        image_paths = [img[1] for img in images]
        
        if not image_paths:
            QMessageBox.information(self, "Galería", "Este inmueble no tiene fotos en su galería.")
            return
            
        dialog = GalleryDialog(self, property_name=self.selected_property[1], 
                               image_paths=image_paths,
                               client_email=self.edit_lead_email.text(),
                               client_phone=self.edit_lead_phone.text())
        dialog.exec()

    def reset_selection(self):
        self.start_date = None
        self.end_date = None
        self.update_pricing()
        self.draw_calendar()

    def open_advanced_search(self):
        dialog = AdvancedSearchDialog(self)
        if dialog.exec():
            p = dialog.selected_property
            d = dialog.selected_dates
            self.combo_prop.setCurrentText(p[1])
            self.start_date = d["desde"]
            self.end_date = d["hasta"]
            self.update_pricing()
            self.draw_calendar()

    def draw_calendar(self):
        # En lugar de borrar, ocultamos todos los botones del pool
        for btn in self.day_buttons:
            btn.hide()
            try: btn.clicked.disconnect() 
            except: pass

        meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.lbl_month.setText(f"{meses[self.view_month].upper()} {self.view_year}")

        cal = calendar.monthcalendar(self.view_year, self.view_month)
        
        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                if day == 0: continue
                
                d = date(self.view_year, self.view_month, day)
                status = self._get_day_status(d)
                if d < self.now: status = "pasado"
                
                # Obtener el botón correcto según su posición física en el grid (42 botones total)
                idx = (row_idx * 7) + col_idx
                if idx < len(self.day_buttons):
                    btn = self.day_buttons[idx]
                    btn.setText(str(day))
                    btn.full_date = d
                    btn.status = status
                    btn.setEnabled(status != "pasado")
                    
                    is_selected = self._is_selected(d)
                    btn.update_style(is_selected=is_selected)
                    
                    # Reconectar señal de forma segura (usamos valor por defecto para fijar dd)
                    btn.clicked.connect(lambda checked=False, dd=d: self.on_day_click(dd))
                    btn.show()

    def _get_day_status(self, d):
        is_ingreso = False
        is_egreso = False
        is_occupied = False
        
        for ingreso, egreso, _ in self.reserved_ranges:
            if isinstance(ingreso, str): ingreso = datetime.strptime(ingreso, "%Y-%m-%d").date()
            if isinstance(egreso, str): egreso = datetime.strptime(egreso, "%Y-%m-%d").date()
            
            if d == ingreso: is_ingreso = True
            elif d == egreso: is_egreso = True
            elif ingreso < d < egreso: is_occupied = True

        if is_occupied: return "ocupado"
        if is_ingreso and is_egreso: return "transicion"
        if is_ingreso: return "ingreso"
        if is_egreso: return "egreso"
        return "disponible"

    def _is_selected(self, d):
        if self.start_date and self.end_date:
            return self.start_date <= d < self.end_date
        if self.start_date:
            return d == self.start_date
        return False

    def on_day_click(self, d):
        if not self.selected_property:
            QMessageBox.warning(self, "Atención", "Seleccione un inmueble primero.")
            return

        try:
            if not self.start_date or (self.start_date and self.end_date):
                self.start_date = d
                self.end_date = None
            else:
                if d <= self.start_date:
                    self.start_date = d
                    self.end_date = None
                else:
                    self.end_date = d
                    
            self.update_pricing()
            self.draw_calendar()
        except Exception as e:
            print(f"DEBUG: Error in on_day_click: {e}")
            self.reset_selection()

    def update_pricing(self):
        if self.start_date and self.end_date:
            noches = (self.end_date - self.start_date).days
            self.lbl_dates.setText(f"Estadía: {self.start_date.strftime('%d/%m')} al {self.end_date.strftime('%d/%m')}")
            self.lbl_nights.setText(f"Noches: {noches}")
            
            if self.selected_property:
                base_total = noches * float(self.selected_property[7])
                disc_amount = 0
                try:
                    # Limpiar el texto para que solo queden números
                    clean_text = "".join(filter(lambda x: x.isdigit() or x == ".", self.edit_discount.text()))
                    disc_val = float(clean_text) if clean_text else 0.0
                    
                    if self.rad_perc.isChecked():
                        disc_amount = base_total * (min(100, disc_val) / 100)
                    else:
                        disc_amount = min(base_total, disc_val)
                except: 
                    disc_amount = 0.0
                
                final_total = max(0, base_total - disc_amount)
                
                self.lbl_total.setText(f"Costo Total: ${final_total:,.0f}".replace(",", "."))
                
                if disc_amount > 0:
                    self.lbl_discount_amount.setText(f"- Descuento: ${disc_amount:,.0f}".replace(",", "."))
                    self.lbl_discount_amount.show()
                else:
                    self.lbl_discount_amount.hide()
                    
                self.btn_reserve.setEnabled(True)
        else:
            self.lbl_dates.setText("Estadía: -")
            self.lbl_nights.setText("Noches: 0")
            self.lbl_total.setText("Costo Total: $0,00")
            self.lbl_discount_amount.hide()
            self.btn_reserve.setEnabled(False)

    def prev_month(self):
        self.view_month -= 1
        if self.view_month == 0:
            self.view_month = 12
            self.view_year -= 1
        self.draw_calendar()

    def next_month(self):
        self.view_month += 1
        if self.view_month == 13:
            self.view_month = 1
            self.view_year += 1
        self.draw_calendar()

    def _on_name_text_changed(self, text):
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
            display = f"{res[2]} {res[3]} ({res[4]})"
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, res) # Store the full tuple
            
            # Change color if it's a regular client vs prospect
            if res[6] == 'cliente':
                item.setForeground(QColor("#27ae60")) # Green for existing clients
            
            self.suggestion_list.addItem(item)
        
        self.suggestion_list.show()

    def _on_suggestion_clicked(self, item):
        data = item.data(Qt.UserRole)
        # data = (id, doc, nombre, apellido, email, tel, tipo)
        self.edit_lead_name.blockSignals(True)
        self.edit_lead_name.setText(f"{data[2]} {data[3]}")
        self.edit_lead_name.blockSignals(False)
        
        self.edit_lead_email.setText(str(data[4]) if data[4] else "")
        self.edit_lead_phone.setText(str(data[5]) if data[5] else "")
        self.suggestion_list.hide()

    def send_wa(self):
        self._prepare_quotation(mode="whatsapp")

    def send_email(self):
        self._prepare_quotation(mode="email")

    def _prepare_quotation(self, mode="email"):
        nombre = self.edit_lead_name.text().strip()
        email = self.edit_lead_email.text().strip().lower()
        tel = self.edit_lead_phone.text().strip()
        
        if not (nombre and tel):
            QMessageBox.critical(self, "Error", "Por favor completa Nombre y Teléfono.")
            return
            
        if mode == "email" and not email:
            QMessageBox.critical(self, "Error", "Por favor completa el Email.")
            return

        if not self.start_date or not self.end_date or not self.selected_property:
            QMessageBox.warning(self, "Atención", "Selecciona fechas e inmueble antes de enviar.")
            return

        # Photo selection logic
        if self.check_include_photos.isChecked() and mode == "email":
            images = self.db.get_gallery_images(self.selected_property[0])
            all_paths = [img[1] for img in images if os.path.exists(img[1])]
            
            # Add main image if exists
            main_img = self.selected_property[8]
            if main_img and os.path.exists(main_img) and main_img not in all_paths:
                all_paths.insert(0, main_img)

            if not all_paths:
                res = QMessageBox.question(self, "Sin fotos", "No hay fotos disponibles. ¿Enviar sin fotos?",
                                           QMessageBox.Yes | QMessageBox.No)
                if res == QMessageBox.No: return
                self._proceed_send_quotation(nombre, email, tel, [], mode=mode)
            else:
                dialog = QuoteImageSelectorDialog(self, image_paths=all_paths)
                if dialog.exec():
                    self._proceed_send_quotation(nombre, email, tel, dialog.selected_paths, mode=mode)
        else:
            self._proceed_send_quotation(nombre, email, tel, [], mode=mode)

    def _proceed_send_quotation(self, nombre, email, tel, selected_images, mode="email"):
        if not self.db.connect(): return

        # 1. Register or find contact
        existing, tipo = self.db.get_contact_by_any(email=email, phone=tel)
        client_id = None
        prospect_id = None

        if existing:
            if tipo == 'cliente': client_id = existing[0]
            else: prospect_id = existing[0]
        else:
            parts = nombre.split(" ", 1)
            nom = parts[0]
            ape = parts[1] if len(parts) > 1 else "—"
            prospect_id = self.db.insert_prospect(("S/D", nom, ape, email if email else "no-email@wa.com", tel))

        # 2. Save quotation to DB
        noches = (self.end_date - self.start_date).days
        valor_dia = float(self.selected_property[7])
        costo_total = noches * valor_dia
        
        disc_val = 0
        try:
            val_text = self.edit_discount.text().replace("$", "").replace(".", "")
            disc_val = float(val_text) if val_text else 0
            if self.rad_perc.isChecked():
                disc_val = costo_total * (disc_val / 100)
        except: pass

        quot_id = self.db.insert_quotation({
            "id_cliente": client_id, "id_prospecto": prospect_id,
            "id_inmueble": self.selected_property[0],
            "fecha_ingreso": self.start_date, "fecha_egreso": self.end_date,
            "noches": noches, "valor_dia": valor_dia, "costo_total": costo_total,
            "descuento": disc_val, "costo_con_descuento": costo_total - disc_val
        })

        # 3. Prepare data for sending
        servs = self.db.get_property_services(self.selected_property[0])
        servs_str = ", ".join([f"{s[0]} {s[1]}" for s in servs]) if servs else "No especificados"
        
        data = {
            "id": quot_id, "inmueble": self.selected_property[1], "servicios": servs_str,
            "fecha_ingreso": self.start_date.strftime("%d/%m/%Y"),
            "fecha_egreso": self.end_date.strftime("%d/%m/%Y"),
            "noches": noches, "ubicacion": f"{self.selected_property[4]}, {self.selected_property[5]}",
            "costo_total": f"${costo_total:,.0f}".replace(",", "."),
            "final_price": self.lbl_total.text().replace("Costo Total: ", ""),
            "final_per_night": f"${((costo_total - disc_val)/noches):,.0f}".replace(",", ".") if noches > 0 else "$0",
            "dormitorios": self.selected_property[9], 
            "camas": self.selected_property[10], 
            "baños": self.selected_property[11]
        }

        if mode == "email":
            # Visual Feedback: Cursor, Button state and Text
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.btn_send_email.setEnabled(False)
            self.btn_send_wa.setEnabled(False)
            original_text = self.btn_send_email.text()
            self.btn_send_email.setText("📧 ENVIANDO...")
            QApplication.processEvents() # Force UI update
            
            try:
                success = send_quotation_email(email, nombre, data, image_paths=selected_images)
                if success:
                    QMessageBox.information(self, "Éxito", f"Cotización enviada a {email}")
                    self._clear_lead_fields()
                else:
                    QMessageBox.critical(self, "Error", "Fallo al enviar el email. Verifique configuración SMTP.")
            finally:
                # Restore UI state
                self.btn_send_email.setText(original_text)
                self.btn_send_email.setEnabled(True)
                self.btn_send_wa.setEnabled(True)
                QApplication.restoreOverrideCursor()
        else:
            if send_whatsapp_quotation(tel, nombre, data):
                QMessageBox.information(self, "Éxito", "WhatsApp abierto.")
                self._clear_lead_fields()

    def _clear_lead_fields(self):
        self.edit_lead_name.clear()
        self.edit_lead_phone.clear()
        self.edit_lead_email.clear()
        self.check_include_photos.setChecked(False)

    def go_to_reservation(self):
        if not self.start_date or not self.end_date or not self.selected_property:
            return
            
        initial_data = {
            "inmueble": self.selected_property[1],
            "fecha_ingreso": self.start_date.strftime("%d/%m/%Y"),
            "fecha_egreso": self.end_date.strftime("%d/%m/%Y"),
            "cantidad_personas": self.selected_property[2],
            "descuento": self.edit_discount.text(),
            "discount_is_percentage": self.rad_perc.isChecked(),
            "imagen": self.selected_property[8] if len(self.selected_property) > 8 else None
        }
        
        dialog = ReservationFormDialog(self, initial_data=initial_data)
        if dialog.exec():
            pass
