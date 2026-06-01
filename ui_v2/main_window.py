import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame, 
                             QGridLayout, QScrollArea, QSpacerItem, QSizePolicy,
                             QStackedWidget, QMessageBox, QDialog, QLineEdit, QComboBox)
from PySide6.QtCore import Qt, QSize, QUrl, QByteArray
from PySide6.QtGui import QFont, QIcon, QColor, QPixmap, QDesktopServices
import os
from datetime import date, datetime

# Importar controladores existentes
from controllers.database import Database
from controllers.property_controller import PropertyController
from controllers.client_controller import ClientController
from controllers.reservation_controller import ReservationController
from controllers.automation_controller import AutomationController

# Importar nuevas páginas V2
from ui_v2.client_list_page import ClientListPage
from ui_v2.consultation_page import ConsultationPage
from ui_v2.reservation_list_page import ReservationListPage
from ui_v2.finance_page import FinancePage
from ui_v2.property_list_page import PropertyListPage
from ui_v2.config_page import ConfigPage
from ui_v2.prospect_list_page import ProspectListPage
from ui_v2.quotation_list_page import QuotationListPage
from ui_v2.cleaning_page import CleaningPage
from ui_v2.widgets import BarChartWidget, HorizontalBarChartWidget, SeasonStatCard, KPICard, SidebarButton
from utils.whatsapp_sender import open_whatsapp_chat, get_whatsapp_url

class MainWindow(QMainWindow):

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
        
        # Automatización de recordatorios en segundo plano
        from PySide6.QtCore import QTimer
        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self.run_automations)
        self.auto_timer.start(1800000) # Ejecutar cada 30 minutos
        
        QTimer.singleShot(5000, self.run_automations) # Primera ejecución a los 5 seg

    def run_automations(self):
        """Ejecuta las tareas automáticas del sistema."""
        print("DEBUG: Iniciando tareas automáticas (Recordatorios y WhatsApp Status)...")
        self.automation = AutomationController()
        
        # 1. Procesar recordatorios de email
        result = self.automation.process_reminders()
        if result.get('sent', 0) > 0:
            print(f"AUTOMATION: {result.get('message')}")
        
        # 2. Actualizar estados de WhatsApp (Twilio)
        updated_wa = self.automation.update_whatsapp_statuses()
        if updated_wa:
            print(f"AUTOMATION: Se actualizaron {updated_wa} estados de WhatsApp.")
            
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

        self.btn_consultas = SidebarButton("🔍 Consultas")
        self.btn_consultas.clicked.connect(lambda: self.switch_page(1))
        self.sidebar_layout.addWidget(self.btn_consultas)
        
        self.btn_reservas = SidebarButton("📅 Reservas")
        self.btn_reservas.clicked.connect(lambda: self.switch_page(2))
        self.sidebar_layout.addWidget(self.btn_reservas)
        
        self.btn_cotizaciones = SidebarButton("📑 Cotizaciones")
        self.btn_cotizaciones.clicked.connect(lambda: self.switch_page(3))
        self.sidebar_layout.addWidget(self.btn_cotizaciones)

        self.btn_prospectos = SidebarButton("🎯 Leads (Prospectos)")
        self.btn_prospectos.clicked.connect(lambda: self.switch_page(4))
        self.sidebar_layout.addWidget(self.btn_prospectos)

        self.btn_clientes = SidebarButton("👥 Clientes")
        self.btn_clientes.clicked.connect(lambda: self.switch_page(5))
        self.sidebar_layout.addWidget(self.btn_clientes)
        
        self.btn_inmuebles = SidebarButton("🏠 Inmuebles")
        self.btn_inmuebles.clicked.connect(lambda: self.switch_page(6))
        self.sidebar_layout.addWidget(self.btn_inmuebles)

        self.btn_limpieza = SidebarButton("🧹 Limpieza")
        self.btn_limpieza.clicked.connect(lambda: self.switch_page(7))
        self.sidebar_layout.addWidget(self.btn_limpieza)

        self.btn_finanzas = SidebarButton("💰 Finanzas")
        self.btn_finanzas.clicked.connect(lambda: self.switch_page(8))
        self.sidebar_layout.addWidget(self.btn_finanzas)

        self.btn_config = SidebarButton("⚙️ Configuración")
        self.btn_config.clicked.connect(lambda: self.switch_page(9))
        self.sidebar_layout.addWidget(self.btn_config)
        
        # Agrupar botones para exclusividad
        self.nav_buttons = [self.btn_dashboard, self.btn_consultas, self.btn_reservas, 
                            self.btn_cotizaciones, self.btn_prospectos, self.btn_clientes, 
                            self.btn_inmuebles, self.btn_limpieza, self.btn_finanzas, self.btn_config]
        
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
        
        # PAGINA 1: CONSULTAS
        self.page_consultation = ConsultationPage(self.reservation_controller)
        self.page_consultation.data_updated.connect(self.refresh_dashboard)
        self.pages.addWidget(self.page_consultation)

        # PAGINA 2: RESERVAS
        self.page_reservas = ReservationListPage()
        self.page_reservas.data_updated.connect(self.refresh_dashboard)
        self.pages.addWidget(self.page_reservas)

        # PAGINA 3: COTIZACIONES
        self.page_cotizaciones = QuotationListPage()
        self.pages.addWidget(self.page_cotizaciones)
        
        # PAGINA 4: PROSPECTOS
        self.page_prospectos = ProspectListPage()
        self.pages.addWidget(self.page_prospectos)

        # PAGINA 5: CLIENTES
        self.page_clientes = ClientListPage()
        self.pages.addWidget(self.page_clientes)
        
        # PAGINA 6: INMUEBLES
        self.page_inmuebles = PropertyListPage()
        self.pages.addWidget(self.page_inmuebles)

        # PAGINA 7: LIMPIEZA
        self.page_limpieza = CleaningPage()
        self.pages.addWidget(self.page_limpieza)

        # PAGINA 8: FINANZAS
        self.page_finanzas = FinancePage()
        self.pages.addWidget(self.page_finanzas)

        # PAGINA 9: CONFIGURACIÓN
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
        
        header_right = QHBoxLayout()
        header_right.setSpacing(15)
        
        # Campana de Notificaciones
        self.btn_notifications = QPushButton("🔔")
        self.btn_notifications.setFixedSize(45, 45)
        self.btn_notifications.setCursor(Qt.PointingHandCursor)
        self.btn_notifications.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #eef0f2;
                border-radius: 22px;
                font-size: 20px;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border: 1px solid #9b59b6;
            }
        """)
        self.btn_notifications.clicked.connect(self.show_notifications_popup)
        
        # Badge de notificaciones (Número)
        self.notif_badge = QLabel("0", self.btn_notifications)
        self.notif_badge.setFixedSize(18, 18)
        self.notif_badge.setAlignment(Qt.AlignCenter)
        self.notif_badge.setStyleSheet("""
            background-color: #e74c3c;
            color: white;
            border-radius: 9px;
            font-size: 10px;
            font-weight: bold;
            border: 2px solid white;
        """)
        self.notif_badge.move(25, 5)
        self.notif_badge.hide()

        self.lbl_date = QLabel(date.today().strftime("%A, %d de %B %Y"))
        self.lbl_date.setStyleSheet("font-size: 14px; color: #7f8c8d; margin-left: 10px;")
        
        header_right.addWidget(self.btn_notifications)
        header_right.addWidget(self.lbl_date)
        
        header_layout.addWidget(self.lbl_welcome)
        header_layout.addStretch()
        header_layout.addLayout(header_right)
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
        
        # Middle Section: Two Columns (Movements and Chart)
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(30)
        
        # Column 1: Upcoming Movements
        movements_col = QVBoxLayout()
        movements_col.setSpacing(20)
        self.card_checkin = self._create_movement_card("📥 PRÓXIMOS CHECK-IN", "#27ae60")
        self.card_checkout = self._create_movement_card("📤 PRÓXIMOS CHECK-OUT", "#2980b9")
        movements_col.addWidget(self.card_checkin)
        movements_col.addWidget(self.card_checkout)
        middle_layout.addLayout(movements_col, 1)
        
        # Column 2: Financial Chart (now vertical)
        chart_col = QVBoxLayout()
        self.chart_finance = BarChartWidget("RENDIMIENTO ECONÓMICO TEMPORADA", "#3498db")
        self.chart_finance.setMinimumHeight(350) # Matching the height of the two movement cards
        chart_col.addWidget(self.chart_finance)
        middle_layout.addLayout(chart_col, 1)
        
        self.content_layout.addLayout(middle_layout)

        # Seasonal Stats Section (Bottom full-width row)
        self.season_section = QFrame()
        self.season_section.setObjectName("SeasonSection")
        self.season_section.setStyleSheet("#SeasonSection { background: transparent; border: none; }")
        self.season_vbox = QVBoxLayout(self.season_section)
        self.season_vbox.setContentsMargins(0, 0, 0, 0)
        self.season_vbox.setSpacing(15)
        
        self.lbl_season = QLabel("📊 RENDIMIENTO DE TEMPORADA")
        self.lbl_season.setStyleSheet("font-size: 13px; font-weight: 800; color: #34495e; margin-bottom: 5px; border: none;")
        self.season_vbox.addWidget(self.lbl_season)
        
        season_stats_container = QFrame()
        season_stats_container.setStyleSheet("background-color: white; border-radius: 15px; border: 1px solid #eef0f2;")
        season_stats_layout = QVBoxLayout(season_stats_container)
        season_stats_layout.setContentsMargins(20, 20, 20, 20)
        season_stats_layout.setSpacing(20)

        self.season_cards_layout = QHBoxLayout()
        self.season_cards_layout.setSpacing(20)
        self.donut_occupied = SeasonStatCard("Ocupación", "#3498db")
        self.donut_free = SeasonStatCard("Días Libres", "#95a5a6")
        self.donut_rented = SeasonStatCard("Días Alquilados", "#27ae60")
        
        self.season_cards_layout.addWidget(self.donut_occupied)
        self.season_cards_layout.addWidget(self.donut_free)
        self.season_cards_layout.addWidget(self.donut_rented)
        season_stats_layout.addLayout(self.season_cards_layout)
        
        self.season_vbox.addWidget(season_stats_container)
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

        if index == 0: 
            self.refresh_dashboard() # Esto ya refresca KPIs y Notificaciones
        elif index == 1: self.page_consultation.load_initial_data()
        elif index == 2: self.page_reservas.load_data()
        elif index == 3: self.page_cotizaciones.load_data()
        elif index == 4: self.page_prospectos.load_data()
        elif index == 5: self.page_clientes.load_data()
        elif index == 6: self.page_inmuebles.load_data()
        elif index == 7: self.page_limpieza.load_data()
        elif index == 8: self.page_finanzas.load_data()
        elif index == 9: self.page_config.load_config()
        
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
        
        # Update Notifications Badge
        notifs = self.db.get_todays_notifications()
        count = len(notifs)
        if count > 0:
            self.notif_badge.setText(str(count))
            self.notif_badge.show()
        else:
            self.notif_badge.hide()

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

                # Cargar datos para el gráfico financiero vertical (Apilado por Mes)
                try:
                    start_db = season['start'].strftime('%Y-%m-%d')
                    end_db = season['end'].strftime('%Y-%m-%d')
                    monthly_breakdown = self.db.get_monthly_financial_breakdown(start_db, end_db)
                    if monthly_breakdown:
                        fin_data = []
                        meses_es = {
                            "01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril",
                            "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto",
                            "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"
                        }
                        for row in monthly_breakdown:
                            mes_raw = row[0] # Formato YYYY-MM
                            try:
                                anio, mes_num = mes_raw.split("-")
                                mes_nombre = meses_es.get(mes_num, mes_num)
                                mes_label = f"{mes_nombre} {anio}"
                            except:
                                mes_label = mes_raw
                                
                            adelantos = float(row[1])
                            cobrado_ci = float(row[2])
                            pendientes = float(row[3])
                            
                            fin_data.append((
                                mes_label, 
                                [adelantos, cobrado_ci, pendientes], 
                                ["#27ae60", "#3498db", "#f1c40f"]
                            ))
                        self.chart_finance.set_data(fin_data)
                        self.chart_finance.title = "RENDIMIENTO DE TEMPORADA"
                except Exception as e_fin:
                    print(f"Error cargando finanzas mensual: {e_fin}")
            else:
                self.season_section.setVisible(False)
        except Exception as e:
            self.season_section.setVisible(False)

    def show_notifications_popup(self):
        from PySide6.QtWidgets import QMenu, QWidgetAction
        
        notifs = self.db.get_todays_notifications()
        if not notifs:
            return
            
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #eef0f2;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        for n in notifs:
            item_widget = QFrame()
            item_widget.setFixedWidth(350)
            item_widget.setStyleSheet("background-color: #f8f9fa; border-radius: 8px; border: 1px solid #eef0f2; margin-bottom: 5px;")
            i_layout = QVBoxLayout(item_widget)
            i_layout.setContentsMargins(15, 10, 15, 10)
            i_layout.setSpacing(5)
            
            h_layout = QHBoxLayout()
            hora_str = n['fecha_envio_recordatorio'].strftime("%H:%M") if n['fecha_envio_recordatorio'] else "--:--"
            lbl_hora = QLabel(f"🕒 {hora_str}")
            lbl_hora.setStyleSheet("font-weight: bold; color: #7f8c8d; border: none; font-size: 11px;")
            
            lbl_status = QLabel("✓ ENVIADO")
            lbl_status.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 10px; border: none;")
            
            h_layout.addWidget(lbl_hora)
            h_layout.addStretch()
            h_layout.addWidget(lbl_status)
            i_layout.addLayout(h_layout)
            
            lbl_info = QLabel(f"Aviso enviado a <b>{n['cliente']}</b><br>Propiedad: <b>{n['inmueble']}</b>")
            lbl_info.setStyleSheet("color: #2c3e50; border: none; font-size: 12px;")
            lbl_info.setWordWrap(True)
            i_layout.addWidget(lbl_info)
            
            action = QWidgetAction(menu)
            action.setDefaultWidget(item_widget)
            menu.addAction(action)
            
        menu.exec(self.btn_notifications.mapToGlobal(self.btn_notifications.rect().bottomLeft()))

    def _update_movements(self):
        self._fill_movement_card(self.card_checkin, self.db.get_upcoming_checkins(), "No hay ingresos")
        self._fill_movement_card(self.card_checkout, self.db.get_upcoming_checkouts(), "No hay egresos")

    def _create_movement_card(self, title, color):
        card = QFrame()
        card.setProperty("card_type", "CHECK-IN" if "CHECK-IN" in title else "CHECK-OUT")
        card.setStyleSheet("background-color: white; border-radius: 15px; border: 1px solid #eef0f2;")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 20)
        layout.setSpacing(0)
        
        # Top color strip
        top_line = QFrame()
        top_line.setFixedHeight(4)
        top_line.setStyleSheet(f"background-color: {color}; border-radius: 2px; border: none;")
        layout.addWidget(top_line)
        
        # Header with Title and Navigation
        header = QHBoxLayout()
        header.setContentsMargins(0, 10, 0, 10)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {color}; font-weight: 800; font-size: 11px; border: none; text-transform: uppercase;")
        header.addWidget(lbl_title)
        header.addStretch()
        
        # Nav controls
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(5)
        
        btn_prev = QPushButton("◀")
        btn_next = QPushButton("▶")
        style_nav = """
            QPushButton { 
                background: #f8f9fa; border: 1px solid #eef0f2; border-radius: 4px; 
                font-size: 10px; color: #7f8c8d; width: 22px; height: 22px; 
            }
            QPushButton:hover { background: #eef0f2; color: #2c3e50; }
        """
        btn_prev.setStyleSheet(style_nav)
        btn_next.setStyleSheet(style_nav)
        btn_prev.setCursor(Qt.PointingHandCursor)
        btn_next.setCursor(Qt.PointingHandCursor)
        
        lbl_count = QLabel("0/0")
        lbl_count.setStyleSheet("color: #95a5a6; font-size: 10px; font-weight: bold; border: none; margin-right: 5px;")
        
        nav_layout.addWidget(lbl_count)
        nav_layout.addWidget(btn_prev)
        nav_layout.addWidget(btn_next)
        header.addLayout(nav_layout)
        layout.addLayout(header)
        
        # Stacked widget for multiple entries
        stack = QStackedWidget()
        stack.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(stack)
        
        # Store refs in the card object for easy access in _fill
        card.nav_prev = btn_prev
        card.nav_next = btn_next
        card.nav_count = lbl_count
        card.stack = stack
        
        # Connect arrows using the specific stack and label of this card
        btn_prev.clicked.connect(lambda: self._navigate_stack(stack, lbl_count, -1))
        btn_next.clicked.connect(lambda: self._navigate_stack(stack, lbl_count, 1))
        
        return card

    def _navigate_stack(self, stack, lbl, delta):
        idx = stack.currentIndex()
        count = stack.count()
        if count <= 1: return
        
        new_idx = (idx + delta) % count
        stack.setCurrentIndex(new_idx)
        lbl.setText(f"{new_idx + 1}/{count}")

    def _fill_movement_card(self, card, data, empty_msg):
        stack = card.stack
        lbl_count = card.nav_count
        card_type = card.property("card_type")
        
        # Clear previous items
        while stack.count() > 0:
            w = stack.widget(0)
            stack.removeWidget(w)
            w.deleteLater()
            
        if not data:
            lbl_count.setText("0/0")
            card.nav_prev.hide()
            card.nav_next.hide()
            
            empty_widget = QWidget()
            l = QVBoxLayout(empty_widget)
            lbl = QLabel(empty_msg)
            lbl.setStyleSheet("color: #95a5a6; font-size: 13px; border: none;")
            lbl.setAlignment(Qt.AlignCenter)
            l.addWidget(lbl)
            stack.addWidget(empty_widget)
            return

        card.nav_prev.setVisible(len(data) > 1)
        card.nav_next.setVisible(len(data) > 1)
        lbl_count.setText(f"1/{len(data)}")

        for i, r in enumerate(data):
            item_widget = QWidget()
            item_widget.setStyleSheet("background: transparent; border: none;")
            c_layout = QVBoxLayout(item_widget)
            c_layout.setContentsMargins(0, 0, 0, 0)
            c_layout.setSpacing(8)
            
            date_str = r[5] if card_type == "CHECK-IN" else r[6]
            try:
                dt = datetime.strptime(str(date_str), "%Y-%m-%d")
                meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                display_date = f"{dt.day} {meses[dt.month]} {dt.year}"
            except: display_date = str(date_str)

            date_lbl = QLabel(display_date)
            date_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #2c3e50; border: none;")
            
            name = QLabel(str(r[1]).upper())
            name.setStyleSheet("font-size: 15px; font-weight: bold; color: #34495e; border: none;")
            
            # --- Badge de Check-In ---
            header_name = QHBoxLayout()
            header_name.addWidget(name)
            
            # Si ya hizo check-in (índice 7 en egresos, para ingresos siempre es 0)
            has_checked_in = False
            if card_type == "CHECK-OUT" and len(r) > 7:
                has_checked_in = bool(r[7])
            
            if has_checked_in:
                badge = QLabel(" ✓ CHECK-IN ")
                badge.setStyleSheet("""
                    background-color: #e8f5e9; color: #27ae60; 
                    font-size: 9px; font-weight: 800; border-radius: 4px;
                    border: 1px solid #c8e6c9; padding: 2px 5px;
                """)
                header_name.addWidget(badge)
            header_name.addStretch()
            
            prop = QLabel(f"  🏠 {r[4]}  ")
            prop.setStyleSheet("font-size: 13px; font-weight: bold; color: #2c3e50; background-color: #f1f3f5; border-radius: 6px; border: 1px solid #e9ecef; padding: 4px;")
            
            actions_layout = QHBoxLayout()
            actions_layout.setSpacing(10)
            
            phone_val = str(r[2])
            client_name = str(r[1])
            res_id = r[0]
            
            btn_wa = QPushButton("💬 WhatsApp")
            btn_wa.setFixedSize(100, 30)
            btn_wa.setStyleSheet("QPushButton { background-color: #25D366; color: white; border-radius: 6px; font-weight: bold; font-size: 10px; }")
            btn_wa.clicked.connect(lambda checked=False, p=phone_val, n=client_name: 
                                   QDesktopServices.openUrl(QUrl(get_whatsapp_url(p, f"Hola {n}!"))))
            
            if card_type == "CHECK-IN":
                btn_action = QPushButton("📥 Procesar Ingreso")
                btn_action.setStyleSheet("QPushButton { background-color: #3498db; color: white; border-radius: 6px; font-weight: bold; font-size: 10px; }")
                btn_action.clicked.connect(lambda checked=False, rid=res_id: self._handle_checkin(rid))
            else:
                btn_action = QPushButton("📤 Procesar Salida")
                btn_action.setStyleSheet("QPushButton { background-color: #e67e22; color: white; border-radius: 6px; font-weight: bold; font-size: 10px; }")
                btn_action.clicked.connect(lambda checked=False, rid=res_id: self._handle_checkout(rid))
                
            btn_action.setFixedSize(110, 30)
            btn_action.setCursor(Qt.PointingHandCursor)
            
            actions_layout.addWidget(btn_wa)
            actions_layout.addWidget(btn_action)
            actions_layout.addStretch()
            
            c_layout.addWidget(date_lbl)
            c_layout.addLayout(header_name)
            c_layout.addWidget(prop, 0, Qt.AlignLeft)
            c_layout.addLayout(actions_layout)
            
            stack.addWidget(item_widget)
        
        stack.setCurrentIndex(0)

        return card

    def _handle_checkin(self, reservation_id):
        # 1. Obtener detalles completos
        data = self.db.get_reservation_details(reservation_id)
        if not data:
            QMessageBox.critical(self, "Error", "No se pudieron obtener los detalles de la reserva.")
            return

        # Validación: Solo se puede hacer check-in en la fecha de ingreso programada
        today = date.today()
        # Asegurar que comparamos fechas (si data['fecha_ingreso'] es datetime)
        checkin_date = data['fecha_ingreso'].date() if isinstance(data['fecha_ingreso'], datetime) else data['fecha_ingreso']
        
        if today != checkin_date:
            QMessageBox.warning(self, "Fecha no válida", 
                                f"No se puede realizar el Check-In hoy.\n\n"
                                f"La fecha de ingreso programada es el {checkin_date.strftime('%d/%m/%Y')}.\n"
                                f"Hoy es {today.strftime('%d/%m/%Y')}.")
            return

        # 2. Abrir el nuevo diálogo
        dialog = CheckInDialog(self, data)
        if dialog.exec():
            res = dialog.get_result()
            
            # 3. Si eligió pago completo, registrar el dinero
            if res['pago_completo']:
                if not self.db.record_checkin_payment(reservation_id, res['monto_a_cobrar']):
                    QMessageBox.warning(self, "Error de Pago", "No se pudo registrar el pago, pero el ingreso continuará.")

            # 4. Marcar como ingresado en la DB
            if self.db.update_reservation_checkin_status(reservation_id, 1):
                QMessageBox.information(self, "Éxito", f"Huésped ingresado correctamente el {res['fecha_real']}.")
                self.refresh_dashboard()
            else:
                QMessageBox.critical(self, "Error", "No se pudo actualizar el estado de check-in.")

    def _handle_checkout(self, reservation_id):
        # 1. Obtener detalles completos para validaciones
        data = self.db.get_reservation_details(reservation_id)
        if not data:
            QMessageBox.critical(self, "Error", "No se pudieron obtener los detalles de la reserva.")
            return

        # Validación 1: No se puede hacer check-out sin check-in previo
        if not data.get('checkin_status'):
            QMessageBox.warning(self, "Acción no permitida", 
                                "No se puede realizar el Check-Out porque aún no se ha registrado el Check-In para esta reserva.")
            return

        # Validación 2: Alerta de Deuda
        pending = float(data.get('pago_pendiente', 0))
        if pending > 0:
            msg = f"⚠️ ATENCIÓN: El cliente {data['nombre']} {data['apellido']} todavía ADEUDA ${pending:,.2f}.\n\n"
            msg += "¿Desea continuar con el Check-Out de todas formas?"
            res = QMessageBox.warning(self, "Cliente con Deuda", msg, 
                                     QMessageBox.Yes | QMessageBox.No)
            if res == QMessageBox.No:
                return

        res = QMessageBox.question(self, "Confirmar Check-Out", 
                                 f"¿Desea marcar la reserva #{reservation_id} como FINALIZADA?",
                                 QMessageBox.Yes | QMessageBox.No)
        if res == QMessageBox.Yes:
            if self.db.update_reservation_checkout_status(reservation_id, 1):
                QMessageBox.information(self, "Éxito", "Check-Out registrado correctamente.")
                
                # Preguntar si desea crear orden de limpieza
                clean = QMessageBox.question(self, "Limpieza", 
                                          "¿Desea generar una orden de limpieza para este inmueble?",
                                          QMessageBox.Yes | QMessageBox.No)
                if clean == QMessageBox.Yes:
                    self.switch_page(7) # Ir a la página de limpieza
                else:
                    self.refresh_dashboard()
            else:
                QMessageBox.critical(self, "Error", "No se pudo actualizar el estado de check-out.")

class CheckInDialog(QDialog):
    def __init__(self, parent=None, reservation_data=None):
        super().__init__(parent)
        self.data = reservation_data
        self.setWindowTitle(f"Procesar Check-In - Reserva #{self.data['id_reserva']}")
        self.setFixedWidth(500)
        self.init_ui()

    def init_ui(self):
        from PySide6.QtWidgets import QFormLayout
        self.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(self)
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        title = QLabel(f"Check-In Reserva #{self.data['id_reserva']}")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; border: none;")
        layout.addWidget(title)
        
        # --- INFO CLIENTE ---
        sec_client = QFrame()
        sec_client.setStyleSheet("background-color: #f8f9fa; border-radius: 10px; padding: 10px; border: 1px solid #eef0f2;")
        client_layout = QFormLayout(sec_client)
        client_layout.setSpacing(10)
        
        lbl_name = QLabel(f"{self.data['nombre']} {self.data['apellido']}")
        lbl_name.setStyleSheet("font-weight: bold; font-size: 15px; color: #3498db; border: none;")
        
        client_layout.addRow("👤 Huésped:", lbl_name)
        client_layout.addRow("🆔 ID Cliente:", QLabel(str(self.data['id_cliente'])))
        client_layout.addRow("📞 Teléfono:", QLabel(str(self.data['telefono'])))
        client_layout.addRow("📧 Email:", QLabel(str(self.data['email'])))
        layout.addWidget(sec_client)
        
        # --- INFO ESTADIA ---
        sec_stay = QFrame()
        sec_stay.setStyleSheet("background-color: #ffffff; border-radius: 10px; border: 1px solid #d1d8e0; padding: 10px;")
        stay_layout = QFormLayout(sec_stay)
        stay_layout.setSpacing(12)
        
        self.edit_date = QLineEdit(date.today().strftime("%d/%m/%Y"))
        self.edit_date.setFixedHeight(35)
        self.edit_date.setStyleSheet("background-color: #f8f9fa; border: 1px solid #d1d8e0; border-radius: 5px; padding-left: 10px;")
        stay_layout.addRow("📅 Fecha Real Ingreso:", self.edit_date)
        
        lbl_inm = QLabel(self.data['inmueble_nombre'])
        lbl_inm.setStyleSheet("font-weight: bold; color: #2c3e50;")
        stay_layout.addRow("🏠 Inmueble:", lbl_inm)
        layout.addWidget(sec_stay)
        
        # --- FINANZAS ---
        sec_fin = QFrame()
        sec_fin.setStyleSheet("background-color: #ebf5fb; border-radius: 10px; border: 1px solid #3498db; padding: 15px;")
        fin_layout = QFormLayout(sec_fin)
        fin_layout.setSpacing(10)
        
        fin_layout.addRow("Costo Total:", QLabel(f"${float(self.data['costo_con_descuento']):,.2f}"))
        fin_layout.addRow("Adelanto Recibido:", QLabel(f"${float(self.data['adelanto']):,.2f}"))
        
        self.lbl_pending = QLabel(f"${float(self.data['pago_pendiente']):,.2f}")
        self.lbl_pending.setStyleSheet("font-weight: 800; font-size: 22px; color: #e74c3c; border: none;")
        fin_layout.addRow("💰 SALDO PENDIENTE:", self.lbl_pending)
        
        self.combo_payment = QComboBox()
        self.combo_payment.addItems(["Pago Completo", "Adeuda Pago"])
        self.combo_payment.setFixedHeight(40)
        self.combo_payment.setStyleSheet("""
            QComboBox { 
                background-color: white; border: 1px solid #3498db; border-radius: 5px; 
                padding-left: 10px; padding-top: 2px; padding-bottom: 2px;
                font-weight: bold; color: #2c3e50;
            }
            QComboBox::drop-down { border: 0px; }
            QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 5px solid #3498db; margin-right: 10px; }
            QComboBox QAbstractItemView {
                background-color: white;
                selection-background-color: #3498db;
                selection-color: white;
                outline: 0px;
                border: 1px solid #3498db;
            }
            QComboBox QAbstractItemView::item {
                min-height: 40px;
                padding-left: 10px;
                color: #2c3e50;
            }
        """)
        fin_layout.addRow("📝 Estado de Pago:", self.combo_payment)
        layout.addWidget(sec_fin)
        
        # --- BOTONES ---
        btns = QHBoxLayout()
        btns.setSpacing(15)
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setFixedHeight(45)
        btn_cancel.setStyleSheet("background-color: white; border: 1px solid #d1d8e0; border-radius: 8px; font-weight: bold; color: #7f8c8d;")
        btn_cancel.clicked.connect(self.reject)
        
        self.btn_confirm = QPushButton("✓ CONFIRMAR INGRESO")
        self.btn_confirm.setFixedHeight(45)
        self.btn_confirm.setStyleSheet("""
            QPushButton { background-color: #3498db; color: white; font-weight: bold; border-radius: 8px; border: none; font-size: 13px; }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.btn_confirm.clicked.connect(self.accept)
        
        btns.addWidget(btn_cancel)
        btns.addWidget(self.btn_confirm, 1)
        layout.addLayout(btns)

    def get_result(self):
        return {
            "fecha_real": self.edit_date.text(),
            "pago_completo": self.combo_payment.currentText() == "Pago Completo",
            "monto_a_cobrar": float(self.data['pago_pendiente'])
        }
