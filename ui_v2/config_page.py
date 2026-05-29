from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QMessageBox,
                             QFileDialog, QScrollArea, QGroupBox, QFormLayout,
                             QTabWidget)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QIcon, QColor, QFont
from controllers.database import Database
from ui_v2.calendar_dialog import ModernCalendarDialog

class ConfigPage(QWidget):
    config_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.entries = {}
        self.init_ui()
        self.load_config()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title = QLabel("Configuración del Sistema")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #2c3e50;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e0e0e0; background: white; border-radius: 10px; }
            QTabBar::tab { 
                background: #f8f9fa; 
                padding: 12px 25px; 
                margin-right: 5px; 
                border-top-left-radius: 10px; 
                border-top-right-radius: 10px; 
                color: #7f8c8d;
                font-weight: bold;
            }
            QTabBar::tab:selected { background: white; color: #3498db; border: 1px solid #e0e0e0; border-bottom: none; }
        """)
        
        # TAB 1: GENERAL
        tab_general = QWidget()
        gen_layout = QVBoxLayout(tab_general)
        gen_layout.setContentsMargins(25, 25, 25, 25)
        gen_layout.setSpacing(20)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 10, 0)
        scroll_layout.setSpacing(25)

        # SMTP
        group_email = QGroupBox("Configuración de Email (SMTP)")
        group_email.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; color: #3498db; }")
        form_email = QFormLayout(group_email)
        form_email.setSpacing(15)
        form_email.setContentsMargins(20, 30, 20, 20)
        self.entries['smtp_server'] = self.create_input("smtp.gmail.com")
        self.entries['smtp_port'] = self.create_input("587")
        self.entries['smtp_user'] = self.create_input("tu-usuario@gmail.com")
        self.entries['smtp_password'] = self.create_input("", is_password=True)
        self.entries['from_email'] = self.create_input("tu-email@gmail.com")
        form_email.addRow("Servidor SMTP:", self.entries['smtp_server'])
        form_email.addRow("Puerto:", self.entries['smtp_port'])
        form_email.addRow("Usuario SMTP:", self.entries['smtp_user'])
        form_email.addRow("Contraseña SMTP:", self.entries['smtp_password'])
        form_email.addRow("Email Remitente:", self.entries['from_email'])
        scroll_layout.addWidget(group_email)

        # BUSINESS
        group_business = QGroupBox("Datos del Negocio")
        group_business.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; color: #27ae60; }")
        form_business = QFormLayout(group_business)
        form_business.setSpacing(15)
        form_business.setContentsMargins(20, 30, 20, 20)
        self.entries['business_name'] = self.create_input("Mi Negocio")
        self.entries['whatsapp_number'] = self.create_input("549...")
        logo_input_layout = QHBoxLayout()
        self.entries['logo_path'] = self.create_input("")
        btn_logo = QPushButton("🔍")
        btn_logo.setFixedWidth(40)
        btn_logo.clicked.connect(self.select_logo)
        logo_input_layout.addWidget(self.entries['logo_path'])
        logo_input_layout.addWidget(btn_logo)
        self.lbl_logo_preview = QLabel("Sin logo")
        self.lbl_logo_preview.setFixedSize(120, 120)
        self.lbl_logo_preview.setAlignment(Qt.AlignCenter)
        self.lbl_logo_preview.setStyleSheet("border: 1px dashed #bdc3c7; background-color: #f8f9fa; color: #7f8c8d; border-radius: 5px;")
        form_business.addRow("Nombre Comercial:", self.entries['business_name'])
        form_business.addRow("WhatsApp:", self.entries['whatsapp_number'])
        form_business.addRow("Logo Path:", logo_input_layout)
        form_business.addRow("", self.lbl_logo_preview)
        scroll_layout.addWidget(group_business)
        
        scroll.setWidget(scroll_content)
        gen_layout.addWidget(scroll)
        self.tabs.addTab(tab_general, "General")

        # TAB 2: TEMPORADA
        tab_season = QWidget()
        season_layout = QVBoxLayout(tab_season)
        season_layout.setContentsMargins(40, 40, 40, 40)
        season_layout.setSpacing(20)
        
        lbl_s_info = QLabel("Configuración de Temporada")
        lbl_s_info.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        season_layout.addWidget(lbl_s_info)
        
        lbl_s_desc = QLabel("Seleccione el rango de fechas para el análisis de ocupación en el dashboard.")
        lbl_s_desc.setStyleSheet("color: #7f8c8d; font-size: 13px;")
        lbl_s_desc.setWordWrap(True)
        season_layout.addWidget(lbl_s_desc)
        
        season_frame = QFrame()
        season_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 15px; border: 1px solid #eef0f2;")
        sf_layout = QFormLayout(season_frame)
        sf_layout.setContentsMargins(30, 30, 30, 30)
        sf_layout.setSpacing(20)
        
        # Nuevos selectores de fecha modernos (Botones que abren el dialogo)
        self.btn_date_start = QPushButton(QDate.currentDate().toString("dd/MM/yyyy"))
        self.btn_date_start.setFixedHeight(45)
        self.btn_date_start.setCursor(Qt.PointingHandCursor)
        self.btn_date_start.setStyleSheet("""
            QPushButton { 
                background: white; border: 1px solid #d1d8e0; border-radius: 8px; 
                text-align: left; padding-left: 15px; font-size: 14px; color: #2c3e50;
            }
            QPushButton:hover { border: 1px solid #3498db; background-color: #fcfdfe; }
        """)
        self.btn_date_start.clicked.connect(lambda: self.open_calendar("start"))
        
        self.btn_date_end = QPushButton(QDate.currentDate().addMonths(3).toString("dd/MM/yyyy"))
        self.btn_date_end.setFixedHeight(45)
        self.btn_date_end.setCursor(Qt.PointingHandCursor)
        self.btn_date_end.setStyleSheet(self.btn_date_start.styleSheet())
        self.btn_date_end.clicked.connect(lambda: self.open_calendar("end"))
        
        # Variables internas para guardar las fechas (QDate)
        self.val_date_start = QDate.currentDate()
        self.val_date_end = QDate.currentDate().addMonths(3)
        
        sf_layout.addRow("📅 Inicio de Temporada:", self.btn_date_start)
        sf_layout.addRow("📅 Fin de Temporada:", self.btn_date_end)
        
        season_layout.addWidget(season_frame)
        season_layout.addStretch()
        self.tabs.addTab(tab_season, "Temporada")

        layout.addWidget(self.tabs)

        # Save Button
        self.btn_save = QPushButton("💾 GUARDAR CAMBIOS")
        self.btn_save.setFixedHeight(50)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 15px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #219150; }
        """)
        self.btn_save.clicked.connect(self.save_config)
        layout.addWidget(self.btn_save)

    def open_calendar(self, target):
        initial = self.val_date_start if target == "start" else self.val_date_end
        dlg = ModernCalendarDialog(initial, self)
        dlg.date_selected.connect(lambda d: self.on_date_selected(d, target))
        dlg.exec()

    def on_date_selected(self, date, target):
        if target == "start":
            self.val_date_start = date
            self.btn_date_start.setText(date.toString("dd/MM/yyyy"))
        else:
            self.val_date_end = date
            self.btn_date_end.setText(date.toString("dd/MM/yyyy"))

    def create_input(self, placeholder, is_password=False):
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setFixedHeight(35)
        if is_password:
            edit.setEchoMode(QLineEdit.Password)
        edit.setStyleSheet("""
            QLineEdit {
                padding-left: 10px;
                border: 1.5px solid #d1d8e0;
                border-radius: 5px;
                background-color: white;
            }
            QLineEdit:focus { border: 2px solid #3498db; }
        """)
        return edit

    def select_logo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Logo", "", "Imágenes (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self.entries['logo_path'].setText(path)
            self.update_logo_preview(path)

    def update_logo_preview(self, path):
        from PySide6.QtGui import QPixmap
        import os
        if path and os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.lbl_logo_preview.setPixmap(pixmap.scaled(
                    self.lbl_logo_preview.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                ))
                self.lbl_logo_preview.setText("")
            else:
                self.lbl_logo_preview.setPixmap(QPixmap())
                self.lbl_logo_preview.setText("Error al cargar")
        else:
            self.lbl_logo_preview.setPixmap(QPixmap())
            self.lbl_logo_preview.setText("Sin logo")

    def load_config(self):
        if self.db.connect():
            config = self.db.get_config()
            if config:
                for field, value in config.items():
                    if field in self.entries:
                        val_str = str(value) if value is not None else ""
                        self.entries[field].setText(val_str)
                        if field == 'logo_path' and val_str:
                            self.update_logo_preview(val_str)
                    
                    if field == 'season_start' and value:
                        d = QDate.fromString(str(value), "yyyy-MM-dd")
                        self.val_date_start = d
                        self.btn_date_start.setText(d.toString("dd/MM/yyyy"))
                    if field == 'season_end' and value:
                        d = QDate.fromString(str(value), "yyyy-MM-dd")
                        self.val_date_end = d
                        self.btn_date_end.setText(d.toString("dd/MM/yyyy"))

    def save_config(self):
        data = {field: entry.text() for field, entry in self.entries.items()}
        data['season_start'] = self.val_date_start.toString("yyyy-MM-dd")
        data['season_end'] = self.val_date_end.toString("yyyy-MM-dd")
        
        # Validation
        required = ["smtp_server", "smtp_port", "smtp_user", "smtp_password", "from_email", "business_name", "whatsapp_number"]
        if not all(data[f] for f in required):
            QMessageBox.warning(self, "Campos Incompletos", "Por favor, complete todos los campos obligatorios.")
            return

        try:
            data['smtp_port'] = int(data['smtp_port'])
        except:
            QMessageBox.warning(self, "Error de Formato", "El puerto SMTP debe ser un número.")
            return

        if self.db.connect():
            if self.db.update_config(data):
                QMessageBox.information(self, "Reinicio Necesario", "Configuración guardada correctamente. La aplicación se reiniciará para aplicar los cambios en el Dashboard.")
                
                # Reiniciar la aplicación
                import os
                import sys
                try:
                    # Guardamos la ruta del ejecutable y los argumentos
                    python = sys.executable
                    os.execl(python, python, *sys.argv)
                except Exception as e:
                    # Si falla el auto-reinicio, pedimos cierre manual
                    QMessageBox.warning(self, "Aviso", f"No se pudo reiniciar automáticamente. Por favor, cierre y abra la app manualmente.\nError: {e}")
            else:
                QMessageBox.critical(self, "Error", "No se pudo guardar la configuración.")
