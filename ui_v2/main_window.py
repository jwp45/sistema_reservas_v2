import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame, 
                             QGridLayout, QScrollArea, QSpacerItem, QSizePolicy,
                             QStackedWidget)
from PySide6.QtCore import Qt, QSize, QUrl, QByteArray
from PySide6.QtGui import QFont, QIcon, QColor, QPainter, QBrush, QPen, QLinearGradient, QPixmap, QDesktopServices
import os
from datetime import date, datetime

# Importar controladores existentes
from controllers.database import Database
from controllers.property_controller import PropertyController
from controllers.client_controller import ClientController
from controllers.reservation_controller import ReservationController

# Importar nuevas páginas V2
from ui_v2.client_list_page import ClientListPage
from ui_v2.consultation_page import ConsultationPage
from ui_v2.reservation_list_page import ReservationListPage
from ui_v2.finance_page import FinancePage
from ui_v2.property_list_page import PropertyListPage
from ui_v2.config_page import ConfigPage
from ui_v2.prospect_list_page import ProspectListPage
from ui_v2.quotation_list_page import QuotationListPage
from utils.whatsapp_sender import open_whatsapp_chat, get_whatsapp_url

class BarChartWidget(QWidget):
    def __init__(self, title, color, parent=None):
        super().__init__(parent)
        self.title = title
        self.color = QColor(color)
        self.data = [] # List of (label, value)
        self.setMinimumHeight(250)
        # Asegurar que el widget sea transparente para que se vean bien los bordes redondeados
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        padding = 45
        chart_w = w - (padding * 2)
        chart_h = h - (padding * 2) - 30
        
        # Background
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("white")))
        painter.drawRoundedRect(0, 0, w, h, 15, 15)
        
        # Title
        painter.setPen(QPen(QColor("#2c3e50")))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(25, 30, self.title)
        
        if not self.data:
            painter.setPen(QPen(QColor("#95a5a6")))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(self.rect(), Qt.AlignCenter, "Cargando datos...")
            return

        max_val = max([val for _, val in self.data]) if self.data else 1
        if max_val == 0: max_val = 1
        
        bar_w = chart_w / len(self.data)
        
        # Draw horizontal grid lines
        painter.setPen(QPen(QColor("#f0f2f5"), 1, Qt.SolidLine))
        for j in range(5):
            gy = h - padding - (j * chart_h / 4)
            painter.drawLine(padding, gy, w - padding, gy)

        for i, (label, val) in enumerate(self.data):
            bar_height = (val / max_val) * chart_h
            x = padding + (i * bar_w) + (bar_w * 0.15)
            y = h - padding - bar_height
            bw = bar_w * 0.7
            
            # Draw Bar with Gradient and Border
            grad = QLinearGradient(x, y, x, y + bar_height)
            grad.setColorAt(0, self.color)
            grad.setColorAt(1, self.color.darker(120))
            
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x, y, bw, bar_height, 6, 6)
            
            # Label
            painter.setPen(QPen(QColor("#7f8c8d")))
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.drawText(x, h - padding + 10, bw, 20, Qt.AlignCenter, label)
            
            # Value
            if val > 0:
                painter.setPen(QPen(QColor("#2c3e50")))
                painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
                val_text = f"{int(val/1000)}k" if val >= 1000 and "INGRESOS" in self.title else str(int(val))
                painter.drawText(x, y - 18, bw, 15, Qt.AlignCenter, val_text)

class SeasonStatCard(QFrame):
    def __init__(self, title, color, parent=None):
        super().__init__(parent)
        self.title = title
        self.color = QColor(color)
        self.percentage = 0
        self.center_text = "0"
        self.show_pct = False
        
        self.setFixedHeight(160)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 15px;
                border: 1px solid #eef0f2;
            }}
            QFrame:hover {{
                border: 1px solid {self.color.name()};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        self.lbl_title = QLabel(title.upper())
        self.lbl_title.setStyleSheet("color: #7f8c8d; font-size: 11px; font-weight: bold; border: none;")
        layout.addWidget(self.lbl_title)
        
        val_layout = QHBoxLayout()
        self.lbl_val = QLabel("0")
        self.lbl_val.setStyleSheet("color: #2c3e50; font-size: 32px; font-weight: 800; border: none;")
        self.lbl_unit = QLabel("DÍAS")
        self.lbl_unit.setStyleSheet("color: #95a5a6; font-size: 12px; font-weight: bold; border: none; margin-top: 10px;")
        val_layout.addWidget(self.lbl_val)
        val_layout.addWidget(self.lbl_unit)
        val_layout.addStretch()
        layout.addLayout(val_layout)
        
        # Progress Bar
        self.bar_bg = QFrame()
        self.bar_bg.setFixedHeight(12)
        self.bar_bg.setStyleSheet("background-color: #f0f2f5; border-radius: 6px; border: none;")
        
        self.bar_fill = QFrame(self.bar_bg)
        self.bar_fill.setFixedHeight(12)
        self.bar_fill.setStyleSheet(f"background-color: {self.color.name()}; border-radius: 6px; border: none;")
        self.bar_fill.setFixedWidth(0)
        
        layout.addWidget(self.bar_bg)

    def set_data(self, value, total, show_percentage=False):
        try:
            val_f = float(value) if value is not None else 0.0
            tot_f = float(total) if total is not None else 0.0
            
            if tot_f > 0:
                self.percentage = (val_f / tot_f) * 100
            else:
                self.percentage = 0
            
            self.show_pct = show_percentage
            if show_percentage:
                self.lbl_val.setText(f"{int(self.percentage)}%")
                self.lbl_unit.setText("")
            else:
                self.lbl_val.setText(str(int(val_f)))
                self.lbl_unit.setText("DÍAS")
                
            # Forzar actualizacion de geometria para obtener el ancho real
            self.bar_bg.update()
            
            self._update_bar_width()
        except Exception as e:
            print(f"DEBUG ERROR in SeasonStatCard.set_data: {e}")

    def _update_bar_width(self):
        max_w = self.bar_bg.width()
        if max_w > 5: # Un minimo razonable
            target_w = int(max_w * (min(100, self.percentage) / 100.0))
            self.bar_fill.setFixedWidth(max(0, target_w))
        else:
            # Si todavia no tiene ancho (ej: oculto al inicio), lo intentara en el resize
            self.bar_fill.setFixedWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_bar_width()

class KPICard(QFrame):
    def __init__(self, title, color, value="—", icon="📈", parent=None):
        super().__init__(parent)
        self.setObjectName("KPICard")
        self.setCursor(Qt.PointingHandCursor)
        self.color = QColor(color)
        
        self.layout = QHBoxLayout(self) # Horizontal to put icon and text side by side
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)
        
        # Icon Frame
        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setFixedSize(60, 60)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet(f"""
            background-color: {self.color.lighter(170).name()};
            border-radius: 30px;
            font-size: 28px;
            border: none;
        """)
        self.layout.addWidget(self.icon_lbl)
        
        # Text Container
        self.text_container = QWidget()
        self.text_container.setStyleSheet("background: transparent; border: none;")
        self.text_layout = QVBoxLayout(self.text_container)
        self.text_layout.setContentsMargins(0, 0, 0, 0)
        self.text_layout.setSpacing(2)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(f"color: #7f8c8d; font-size: 11px; font-weight: bold; border: none; text-transform: uppercase;")
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(f"color: #2c3e50; font-size: 24px; font-weight: 800; border: none;")
        
        self.text_layout.addWidget(self.lbl_title)
        self.text_layout.addWidget(self.lbl_value)
        self.layout.addWidget(self.text_container)
        
        self.setStyleSheet(f"""
            #KPICard {{
                background-color: white;
                border-radius: 15px;
                border: 1px solid #eef0f2;
            }}
            #KPICard:hover {{
                border: 1px solid {self.color.name()};
                background-color: {self.color.lighter(195).name()};
            }}
        """)

    def set_value(self, value):
        self.lbl_value.setText(str(value))

class SidebarButton(QPushButton):
    def __init__(self, text, icon_path=None, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setFixedHeight(45)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 20px;
                background-color: transparent;
                border: none;
                color: #ecf0f1;
                font-size: 14px;
                font-weight: 500;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:checked {
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
        """)

class MainWindowV2(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Reservas - NextGen")
        self.resize(1280, 850)
        
        # Inicializar base de datos y controladores
        self.db = Database()
        self.db.connect()
        
        self.property_controller = PropertyController()
        self.client_controller = ClientController()
        self.reservation_controller = ReservationController(None)
        
        self.init_ui()
        self.refresh_dashboard()
        
    def init_ui(self):
        # Widget Central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout Principal (Horizontal: Sidebar + Contenido)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # --- SIDEBAR ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setStyleSheet("""
            #Sidebar {
                background-color: #2c3e50;
                border: none;
            }
        """)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(15, 15, 15, 30)
        self.sidebar_layout.setSpacing(5)
        
        # Logo / Título
        self.lbl_logo = QLabel()
        self.lbl_logo.setAlignment(Qt.AlignCenter)
        self.lbl_logo.setStyleSheet("margin-bottom: 10px; border: none;")
        self.sidebar_layout.addWidget(self.lbl_logo, 0, Qt.AlignCenter)
        
        self.load_sidebar_logo()
        
        # Botones de Navegación
        self.btn_dashboard = SidebarButton("🏠 Dashboard")
        self.btn_dashboard.setChecked(True)
        self.btn_dashboard.clicked.connect(lambda: self.switch_page(0))
        self.sidebar_layout.addWidget(self.btn_dashboard)
        
        self.btn_reservas = SidebarButton("📅 Reservas")
        self.btn_reservas.clicked.connect(lambda: self.switch_page(1))
        self.sidebar_layout.addWidget(self.btn_reservas)

        self.btn_consultas = SidebarButton("🔍 Consultas")
        self.btn_consultas.clicked.connect(lambda: self.switch_page(2))
        self.sidebar_layout.addWidget(self.btn_consultas)
        
        self.btn_cotizaciones = SidebarButton("📑 Cotizaciones")
        self.btn_cotizaciones.clicked.connect(lambda: self.switch_page(3))
        self.sidebar_layout.addWidget(self.btn_cotizaciones)

        self.btn_clientes = SidebarButton("👥 Clientes")
        self.btn_clientes.clicked.connect(lambda: self.switch_page(4))
        self.sidebar_layout.addWidget(self.btn_clientes)
        
        self.btn_prospectos = SidebarButton("🎯 Leads (Prospectos)")
        self.btn_prospectos.clicked.connect(lambda: self.switch_page(5))
        self.sidebar_layout.addWidget(self.btn_prospectos)

        self.btn_finanzas = SidebarButton("💰 Finanzas")
        self.btn_finanzas.clicked.connect(lambda: self.switch_page(6))
        self.sidebar_layout.addWidget(self.btn_finanzas)

        self.btn_inmuebles = SidebarButton("🏠 Inmuebles")
        self.btn_inmuebles.clicked.connect(lambda: self.switch_page(7))
        self.sidebar_layout.addWidget(self.btn_inmuebles)

        self.btn_config = SidebarButton("⚙️ Configuración")
        self.btn_config.clicked.connect(lambda: self.switch_page(8))
        self.sidebar_layout.addWidget(self.btn_config)
        
        # Agrupar botones para exclusividad
        self.nav_buttons = [self.btn_dashboard, self.btn_reservas, self.btn_consultas, 
                            self.btn_cotizaciones, self.btn_clientes, self.btn_prospectos, 
                            self.btn_finanzas, self.btn_inmuebles, self.btn_config]
        
        self.sidebar_layout.addStretch()
        
        self.lbl_version = QLabel("v3.0.0 Enterprise")
        self.lbl_version.setStyleSheet("color: #95a5a6; font-size: 11px;")
        self.lbl_version.setAlignment(Qt.AlignCenter)
        self.sidebar_layout.addWidget(self.lbl_version)
        
        self.main_layout.addWidget(self.sidebar)
        
        # --- STACKED WIDGET ---
        self.pages = QStackedWidget()
        self.pages.setStyleSheet("background-color: #f0f2f5;")
        
        # PAGINA 0: DASHBOARD
        self.setup_dashboard_page()
        
        # PAGINA 1: RESERVAS
        self.page_reservas = ReservationListPage()
        self.pages.addWidget(self.page_reservas)

        # PAGINA 2: CONSULTAS
        self.page_consultation = ConsultationPage(self.reservation_controller)
        self.pages.addWidget(self.page_consultation)

        # PAGINA 3: COTIZACIONES
        self.page_cotizaciones = QuotationListPage()
        self.pages.addWidget(self.page_cotizaciones)
        
        # PAGINA 4: CLIENTES
        self.page_clientes = ClientListPage()
        self.pages.addWidget(self.page_clientes)
        
        # PAGINA 5: PROSPECTOS
        self.page_prospectos = ProspectListPage()
        self.pages.addWidget(self.page_prospectos)
        
        # PAGINA 6: FINANZAS
        self.page_finanzas = FinancePage()
        self.pages.addWidget(self.page_finanzas)

        # PAGINA 7: INMUEBLES
        self.page_inmuebles = PropertyListPage()
        self.pages.addWidget(self.page_inmuebles)

        # PAGINA 8: CONFIGURACIÓN
        self.page_config = ConfigPage()
        self.page_config.config_updated.connect(self.refresh_dashboard)
        self.pages.addWidget(self.page_config)
        
        self.main_layout.addWidget(self.pages)

    def setup_dashboard_page(self):
        self.content_area = QScrollArea()
        self.content_area.setWidgetResizable(True)
        self.content_area.setFrameShape(QFrame.NoFrame)
        self.content_area.setStyleSheet("background-color: #f0f2f5;")
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(40, 40, 40, 40)
        self.content_layout.setSpacing(30)
        
        header_layout = QHBoxLayout()
        self.lbl_welcome = QLabel("Resumen General")
        self.lbl_welcome.setStyleSheet("font-size: 26px; font-weight: bold; color: #2c3e50;")
        self.lbl_date = QLabel(date.today().strftime("%A, %d de %B %Y"))
        self.lbl_date.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        header_layout.addWidget(self.lbl_welcome)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_date)
        self.content_layout.addLayout(header_layout)
        
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(20)
        self.kpi_pending = KPICard("COBROS PENDIENTES", "#e74c3c", icon="💸")
        self.kpi_expiring = KPICard("VENTAS EN RIESGO", "#f39c12", icon="⚠️")
        self.kpi_expiring.mousePressEvent = lambda e: self._on_kpi_expiring_clicked()
        
        self.kpi_occupancy = KPICard("OCUPACIÓN HOY", "#3498db", icon="🏠")
        self.kpi_revenue = KPICard("INGRESOS MES", "#27ae60", icon="💰")
        self.kpi_layout.addWidget(self.kpi_pending)
        self.kpi_layout.addWidget(self.kpi_expiring)
        self.kpi_layout.addWidget(self.kpi_occupancy)
        self.kpi_layout.addWidget(self.kpi_revenue)
        self.content_layout.addLayout(self.kpi_layout)
        
        self.movements_layout = QHBoxLayout()
        self.movements_layout.setSpacing(30)
        self.card_checkin = self._create_movement_card("📥 PRÓXIMOS CHECK-IN", "#27ae60")
        self.movements_layout.addWidget(self.card_checkin)
        self.card_checkout = self._create_movement_card("📤 PRÓXIMOS CHECK-OUT", "#2980b9")
        self.movements_layout.addWidget(self.card_checkout)
        self.content_layout.addLayout(self.movements_layout)
        
        # Seasonal Stats Section (ahora debajo de los movimientos)
        self.season_section = QFrame()
        self.season_section.setObjectName("SeasonSection")
        self.season_section.setMinimumHeight(200)
        self.season_section.setStyleSheet("#SeasonSection { background: transparent; border: none; }")
        self.season_vbox = QVBoxLayout(self.season_section)
        self.season_vbox.setContentsMargins(0, 0, 0, 0)
        self.season_vbox.setSpacing(15)
        
        self.lbl_season = QLabel("📊 RENDIMIENTO DE TEMPORADA")
        self.lbl_season.setStyleSheet("font-size: 13px; font-weight: 800; color: #34495e; margin-bottom: 5px; border: none;")
        self.season_vbox.addWidget(self.lbl_season)
        
        self.season_cards_layout = QHBoxLayout()
        self.season_cards_layout.setSpacing(20)
        self.donut_occupied = SeasonStatCard("Ocupación", "#3498db")
        self.donut_free = SeasonStatCard("Días Libres", "#95a5a6")
        self.donut_rented = SeasonStatCard("Días Alquilados", "#27ae60")
        
        self.season_cards_layout.addWidget(self.donut_occupied)
        self.season_cards_layout.addWidget(self.donut_free)
        self.season_cards_layout.addWidget(self.donut_rented)
        self.season_vbox.addLayout(self.season_cards_layout)
        
        self.content_layout.addWidget(self.season_section)

        self.content_layout.addStretch()
        self.content_area.setWidget(self.content_widget)
        self.pages.addWidget(self.content_area)

    def _on_kpi_expiring_clicked(self):
        # 1. Cambiar a la página de cotizaciones (Índice 3 según init_ui)
        self.switch_page(3)
        # 2. Activar el filtro de riesgo
        self.page_cotizaciones.set_risk_filter_enabled(True)

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        
        if index == 0: self.refresh_dashboard()
        elif index == 1: self.page_reservas.load_data()
        elif index == 2: self.page_consultation.load_initial_data()
        elif index == 3: self.page_cotizaciones.load_data()
        elif index == 4: self.page_clientes.load_data()
        elif index == 5: self.page_prospectos.load_data()
        elif index == 6: self.page_finanzas.load_data()
        elif index == 7: self.page_inmuebles.load_data()
        elif index == 8: self.page_config.load_config()
        
        # Siempre refrescar el logo por si cambió en config
        self.load_sidebar_logo()

    def load_sidebar_logo(self):
        # Limpiar logo anterior y estilos de fallback
        self.lbl_logo.setPixmap(QPixmap())
        self.lbl_logo.setFixedSize(230, 140) # Altura reducida para compactar
        self.lbl_logo.setStyleSheet("border: none; margin-bottom: 5px;")
        
        config = self.db.get_config()
        if config and config.get('logo_path'):
            path = config['logo_path']
            if os.path.exists(path):
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    # Escalar manteniendo proporción, aprovechando mejor el nuevo espacio
                    scaled = pixmap.scaled(220, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.lbl_logo.setPixmap(scaled)
                    self.lbl_logo.setText("")
                    return
        
        # Fallback si no hay logo
        business_name = config.get('business_name', 'PRO-RESERVAS') if config else "PRO-RESERVAS"
        self.lbl_logo.setText(business_name)
        self.lbl_logo.setStyleSheet("""
            color: white; 
            font-size: 18px; 
            font-weight: bold; 
            margin-bottom: 20px; 
            border: none;
        """)

    def refresh_dashboard(self):
        if not self.db.connection or not self.db.connection.is_connected():
            self.db.connect()

        summary = self.db.get_financial_summary()
        self.kpi_pending.set_value(f"${int(summary[2]):,}".replace(",", "."))
        self.kpi_expiring.set_value(str(self.db.get_quotations_expiring_soon(hours=48)))
        
        occ, total = self.db.get_today_occupancy_stats()
        pct = int((occ/total)*100) if total > 0 else 0
        self.kpi_occupancy.set_value(f"{occ}/{total} ({pct}%)")
        
        rev_data = self.db.get_revenue_by_month()
        current_month = datetime.now().strftime("%Y-%m")
        this_month_rev = next((val for mes, val in rev_data if mes == current_month), 0)
        self.kpi_revenue.set_value(f"${int(this_month_rev):,}".replace(",", "."))

        self._update_movements()

        # Season Stats
        try:
            season = self.db.get_season_stats()
            
            if season and isinstance(season, dict):
                self.season_section.setVisible(True)
                
                start_str = season['start'].strftime('%d/%m') if hasattr(season['start'], 'strftime') else str(season['start'])
                end_str = season['end'].strftime('%d/%m') if hasattr(season['end'], 'strftime') else str(season['end'])
                self.lbl_season.setText(f"📊 RENDIMIENTO TEMPORADA ({start_str} - {end_str})")
                
                cap = season['total_capacity']
                
                self.donut_occupied.set_data(season['occupied'], cap, show_percentage=True)
                self.donut_free.set_data(season['free'], cap, show_percentage=False)
                self.donut_rented.set_data(season['rented'], cap, show_percentage=False)
            else:
                self.season_section.setVisible(False)
        except Exception as e:
            self.season_section.setVisible(False)

    def _update_movements(self):
        self._fill_movement_card(self.card_checkin, self.db.get_upcoming_checkins(), "No hay ingresos")
        self._fill_movement_card(self.card_checkout, self.db.get_upcoming_checkouts(), "No hay egresos")

    def _fill_movement_card(self, card, data, empty_msg):
        layout = card.layout()
        if not layout: return
        for i in reversed(range(2, layout.count())): # Skip top_line and title
            item = layout.itemAt(i)
            if item.widget(): item.widget().setParent(None)
            
        if not data:
            lbl = QLabel(empty_msg)
            lbl.setStyleSheet("color: #95a5a6; font-size: 14px; margin-top: 20px; border: none;")
            lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl)
            return

        r = data[0]
        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(0, 15, 0, 0)
        c_layout.setSpacing(8)
        
        # Fecha destacada - Usamos la propiedad dinámica 'card_type'
        card_type = card.property("card_type")
        date_str = r[5] if card_type == "CHECK-IN" else r[6]
        try:
            dt = datetime.strptime(str(date_str), "%Y-%m-%d")
            meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            display_date = f"{dt.day} {meses[dt.month]} {dt.year}"
        except: display_date = str(date_str)

        date_lbl = QLabel(display_date)
        date_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #2c3e50; border: none;")
        
        name = QLabel(str(r[1]).upper())
        name.setStyleSheet("font-size: 16px; font-weight: bold; color: #34495e; border: none;")
        
        details_layout = QHBoxLayout()
        details_layout.setSpacing(10)
        
        # Estilo profesional para el inmueble (tipo Badge/Tag)
        prop = QLabel(f"  🏠 {r[4]}  ")
        prop.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #2c3e50; 
            background-color: #f1f3f5; 
            border-radius: 6px; 
            border: 1px solid #e9ecef;
            padding: 4px;
        """)
        
        # Contenedor para el botón WhatsApp
        phone_container = QWidget()
        phone_container.setStyleSheet("background: transparent; border: none;")
        phone_layout = QHBoxLayout(phone_container)
        phone_layout.setContentsMargins(0, 0, 0, 0)
        phone_layout.setSpacing(0)

        client_name = str(r[1])
        phone_val = str(r[2])
        
        btn_wa = QPushButton("💬 WhatsApp")
        btn_wa.setToolTip(f"Enviar mensaje a {phone_val}")
        btn_wa.setFixedSize(110, 32)
        btn_wa.setCursor(Qt.PointingHandCursor)
        btn_wa.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                border-radius: 6px;
                border: none;
                font-weight: bold;
                font-size: 11px;
                padding: 0 5px;
            }
            QPushButton:hover {
                background-color: #128C7E;
            }
        """)
        # Usar valores por defecto en el lambda para capturar el estado actual del bucle/función
        btn_wa.clicked.connect(lambda checked=False, p=phone_val, n=client_name: 
                               QDesktopServices.openUrl(QUrl(get_whatsapp_url(p, f"Hola {n}!"))))
        
        phone_layout.addWidget(btn_wa)
        
        details_layout.addWidget(prop)
        details_layout.addStretch()
        details_layout.addWidget(phone_container)
        
        c_layout.addWidget(date_lbl)
        c_layout.addWidget(name)
        c_layout.addLayout(details_layout)
        layout.addWidget(container)

    def _create_movement_card(self, title, color):
        card = QFrame()
        # Guardamos el tipo de tarjeta como propiedad para evitar errores de búsqueda
        card.setProperty("card_type", "CHECK-IN" if "CHECK-IN" in title else "CHECK-OUT")
        
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white; 
                border-radius: 15px; 
                border: 1px solid #eef0f2;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header strip
        top_line = QFrame()
        top_line.setFixedHeight(5)
        top_line.setStyleSheet(f"background-color: {color}; border-radius: 2px; border: none;")
        layout.addWidget(top_line)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {color}; font-weight: 800; font-size: 12px; border: none; text-transform: uppercase; margin-top: 10px;")
        layout.addWidget(lbl_title)
        return card

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindowV2()
    window.show()
    sys.exit(app.exec())
