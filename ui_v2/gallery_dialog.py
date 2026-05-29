from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QMessageBox, QScrollArea, QWidget,
                             QListWidget, QListWidgetItem, QCheckBox, QInputDialog)
from PySide6.QtCore import Qt, QSize, QEvent
from PySide6.QtGui import QPixmap, QColor, QFont, QKeyEvent, QAction, QShortcut, QKeySequence
import os
import webbrowser
import urllib.parse
from utils.email_sender import send_gallery_email

class GalleryDialog(QDialog):
    def __init__(self, parent=None, property_name="", image_paths=None, client_email=None, client_phone=None):
        super().__init__(parent)
        self.property_name = property_name
        self.image_paths = image_paths or []
        self.client_email = client_email
        self.client_phone = client_phone
        self.current_index = 0
        self.current_pixmap = None
        
        self.setWindowTitle(f"Galería: {property_name}")
        self.resize(1000, 800)
        self.setStyleSheet("background-color: #1a1a1a; color: white;")
        
        self.init_ui()
        self.setup_shortcuts()
        self.show_image()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #2c3e50; border: none;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(30, 0, 30, 0)
        
        title_v = QVBoxLayout()
        self.lbl_title = QLabel(self.property_name.upper())
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        self.lbl_count = QLabel("Imagen 0 de 0")
        self.lbl_count.setStyleSheet("font-size: 12px; color: #bdc3c7;")
        title_v.addWidget(self.lbl_title)
        title_v.addWidget(self.lbl_count)
        h_layout.addLayout(title_v)
        
        h_layout.addStretch()
        
        btn_close = QPushButton("X")
        btn_close.setFixedSize(40, 40)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("background-color: transparent; font-size: 18px; font-weight: bold; color: #bdc3c7;")
        btn_close.clicked.connect(self.close)
        h_layout.addWidget(btn_close)
        
        layout.addWidget(header)
        
        # Main Viewer Area
        self.viewer_container = QWidget()
        viewer_layout = QHBoxLayout(self.viewer_container)
        viewer_layout.setContentsMargins(10, 10, 10, 10)
        
        btn_prev = QPushButton("◀")
        btn_prev.setFixedSize(60, 150)
        btn_prev.setCursor(Qt.PointingHandCursor)
        btn_prev.setStyleSheet("background-color: rgba(255,255,255,0.05); font-size: 30px; border: none; border-radius: 5px;")
        btn_prev.clicked.connect(self.prev_image)
        viewer_layout.addWidget(btn_prev)
        
        self.lbl_image = QLabel("CARGANDO...")
        self.lbl_image.setAlignment(Qt.AlignCenter)
        self.lbl_image.setStyleSheet("border: none;")
        viewer_layout.addWidget(self.lbl_image, 1)
        
        btn_next = QPushButton("▶")
        btn_next.setFixedSize(60, 150)
        btn_next.setCursor(Qt.PointingHandCursor)
        btn_next.setStyleSheet("background-color: rgba(255,255,255,0.05); font-size: 30px; border: none; border-radius: 5px;")
        btn_next.clicked.connect(self.next_image)
        viewer_layout.addWidget(btn_next)
        
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
        c_layout.addWidget(btn_wa)
        
        btn_email = QPushButton("📧 COMPARTIR POR EMAIL")
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
        c_layout.addWidget(btn_email)
        
        layout.addWidget(controls)

    def setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_Left), self, self.prev_image)
        QShortcut(QKeySequence(Qt.Key_Right), self, self.next_image)
        QShortcut(QKeySequence(Qt.Key_Escape), self, self.close)

    def show_image(self):
        if not self.image_paths:
            self.lbl_image.setText("NO HAY IMÁGENES EN LA GALERÍA")
            self.lbl_count.setText("0 de 0")
            return
            
        path = self.image_paths[self.current_index]
        self.lbl_count.setText(f"Imagen {self.current_index + 1} de {len(self.image_paths)}")
        
        if os.path.exists(path):
            self.current_pixmap = QPixmap(path)
            if self.current_pixmap.isNull():
                self.lbl_image.setText(f"ERROR AL CARGAR:\n{os.path.basename(path)}")
            else:
                self.update_image_size()
        else:
            self.lbl_image.setText(f"ARCHIVO NO ENCONTRADO:\n{path}")

    def update_image_size(self):
        if self.current_pixmap and not self.current_pixmap.isNull():
            # Get available size in the label
            size = self.lbl_image.size()
            if size.width() < 100 or size.height() < 100:
                size = QSize(800, 600)
            
            scaled = self.current_pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_image.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-scale image when window is resized, with a small delay to avoid too many updates
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
        phone = self.client_phone
        if not phone:
            phone, ok = QInputDialog.getText(self, "WhatsApp", "Número del cliente (549...):")
            if not ok or not phone: return
            
        clean_phone = "".join(filter(str.isdigit, phone))
        if len(clean_phone) == 10: clean_phone = "549" + clean_phone
        
        msg = urllib.parse.quote(f"¡Hola! Te comparto las fotos de *{self.property_name}*. ¡Quedo atento!")
        webbrowser.open(f"https://wa.me/{clean_phone}?text={msg}")
        QMessageBox.information(self, "WhatsApp", "Se abrió el chat. Adjunte las fotos manualmente.")

    def share_email(self):
        if not self.image_paths: return
        
        email = self.client_email
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

