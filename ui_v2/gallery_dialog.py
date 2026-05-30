from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QMessageBox, QScrollArea, QWidget,
                             QListWidget, QListWidgetItem, QCheckBox, QInputDialog, QApplication)
from PySide6.QtCore import Qt, QSize, QEvent, QUrl
from PySide6.QtGui import QPixmap, QColor, QFont, QKeyEvent, QAction, QShortcut, QKeySequence, QDesktopServices
import os
import webbrowser
import urllib.parse
from utils.email_sender import send_gallery_email
from utils.whatsapp_sender import get_whatsapp_url

class GalleryDialog(QDialog):
    def __init__(self, parent=None, property_name="", image_paths=None, client_email=None, client_phone=None):
        super().__init__(parent)
        self.property_name = property_name
        self.image_paths = image_paths or []
        self.client_email = client_email
        self.client_phone = client_phone
        self.current_index = 0
        self.current_pixmap = None
        
        self.setWindowTitle(f"Galería - {property_name}")
        self.resize(1000, 800)
        self.setStyleSheet("background-color: #1a1a1a; color: white;")
        
        self.init_ui()
        if self.image_paths:
            self.show_image()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Viewer Area
        self.viewer_container = QWidget()
        self.viewer_layout = QVBoxLayout(self.viewer_container)
        self.viewer_layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_image = QLabel()
        self.lbl_image.setAlignment(Qt.AlignCenter)
        self.lbl_image.setStyleSheet("background-color: black; border: none;")
        self.viewer_layout.addWidget(self.lbl_image)
        
        layout.addWidget(self.viewer_container, 1)

        # Controls Bar
        controls = QFrame()
        controls.setFixedHeight(100)
        controls.setStyleSheet("background-color: #2c3e50; border: none;")
        c_layout = QHBoxLayout(controls)
        c_layout.setContentsMargins(30, 0, 30, 0)
        c_layout.setSpacing(20)

        btn_wa = QPushButton("💬 ENVIAR POR WHATSAPP")
        btn_wa.setFixedHeight(45)
        btn_wa.setCursor(Qt.PointingHandCursor)
        btn_wa.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 0 20px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #128C7E; }
        """)
        btn_wa.clicked.connect(self.share_wa)

        btn_email = QPushButton("📧 ENVIAR POR EMAIL")
        btn_email.setFixedHeight(45)
        btn_email.setCursor(Qt.PointingHandCursor)
        btn_email.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 0 20px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        btn_email.clicked.connect(self.share_email)

        nav_layout = QHBoxLayout()
        btn_prev = QPushButton("<")
        btn_prev.setFixedSize(50, 50)
        btn_prev.setCursor(Qt.PointingHandCursor)
        btn_prev.setStyleSheet("background-color: #34495e; color: white; border-radius: 25px; font-size: 20px; font-weight: bold;")
        btn_prev.clicked.connect(self.prev_image)

        self.lbl_counter = QLabel("0 / 0")
        self.lbl_counter.setStyleSheet("font-size: 16px; font-weight: bold; margin: 0 20px;")

        btn_next = QPushButton(">")
        btn_next.setFixedSize(50, 50)
        btn_next.setCursor(Qt.PointingHandCursor)
        btn_next.setStyleSheet(btn_prev.styleSheet())
        btn_next.clicked.connect(self.next_image)

        nav_layout.addWidget(btn_prev)
        nav_layout.addWidget(self.lbl_counter)
        nav_layout.addWidget(btn_next)

        c_layout.addWidget(btn_wa)
        c_layout.addWidget(btn_email)
        c_layout.addStretch()
        c_layout.addLayout(nav_layout)
        c_layout.addStretch()
        
        btn_close = QPushButton("CERRAR")
        btn_close.setFixedHeight(40)
        btn_close.setStyleSheet("background-color: #e74c3c; color: white; padding: 0 20px; border-radius: 5px;")
        btn_close.clicked.connect(self.close)
        c_layout.addWidget(btn_close)

        layout.addWidget(controls)

    def show_image(self):
        if not self.image_paths: return
        
        path = self.image_paths[self.current_index]
        if os.path.exists(path):
            self.current_pixmap = QPixmap(path)
            self.update_image_size()
            self.lbl_counter.setText(f"{self.current_index + 1} / {len(self.image_paths)}")

    def update_image_size(self):
        if self.current_pixmap:
            scaled = self.current_pixmap.scaled(self.lbl_image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_image.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_image_size()

    def prev_image(self):
        if self.image_paths:
            self.current_index = (self.current_index - 1) % len(self.image_paths)
            self.show_image()

    def next_image(self):
        if self.image_paths:
            self.current_index = (self.current_index + 1) % len(self.image_paths)
            self.show_image()

    def share_wa(self):
        if not self.image_paths: return
        
        # Intentar obtener teléfono de la instancia o del padre (ConsultationPage)
        phone = self.client_phone
        if not phone and hasattr(self.parent(), 'edit_lead_phone'):
            phone = self.parent().edit_lead_phone.text().strip()
            
        if not phone:
            phone, ok = QInputDialog.getText(self, "WhatsApp", "Número del cliente (549...):")
            if not ok or not phone: return
            
        # Copiar imagen actual al portapapeles
        current_path = self.image_paths[self.current_index]
        if os.path.exists(current_path):
            pixmap = QPixmap(current_path)
            if not pixmap.isNull():
                QApplication.clipboard().setPixmap(pixmap)
        
        wa_url = get_whatsapp_url(phone, f"¡Hola! Te comparto esta foto de *{self.property_name}*.")
        QDesktopServices.openUrl(QUrl(wa_url))

    def share_email(self):
        if not self.image_paths: return
        
        # Intentar obtener email de la instancia o del padre
        email = self.client_email
        if not email and hasattr(self.parent(), 'edit_lead_email'):
            email = self.parent().edit_lead_email.text().strip()

        if not email:
            email, ok = QInputDialog.getText(self, "Email", "Email del destinatario:")
            if not ok or not email: return
            
        QApplication.setOverrideCursor(Qt.WaitCursor)
        success = send_gallery_email(email, self.property_name, self.image_paths)
        QApplication.restoreOverrideCursor()

        if success:
            QMessageBox.information(self, "Éxito", f"¡Email enviado a {email}!")
        else:
            QMessageBox.critical(self, "Error", "Fallo al enviar email. Verifique configuración SMTP.")
