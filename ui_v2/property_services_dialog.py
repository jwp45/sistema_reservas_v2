from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QScrollArea, QWidget, QGridLayout)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor

class PropertyServicesDialog(QDialog):
    def __init__(self, parent=None, property_data=None, services=None):
        super().__init__(parent)
        self.p = property_data # (id, nombre, cap, dir, loc, prov, tipo, val, img, dorms, cams, banos)
        self.services = services or []
        
        self.setWindowTitle(f"Ficha Técnica: {self.p[1]}")
        self.resize(700, 600)
        self.setStyleSheet("background-color: #f8f9fa;")
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(90)
        header.setStyleSheet("background-color: #2c3e50; border: none;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(30, 0, 30, 0)
        h_layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel(self.p[1].upper())
        title.setStyleSheet("color: white; font-size: 22px; font-weight: 800;")
        h_layout.addWidget(title)
        
        subtitle = QLabel(f"📍 {self.p[4]}, {self.p[5]} | {self.p[6]}")
        subtitle.setStyleSheet("color: #bdc3c7; font-size: 13px; font-weight: bold;")
        h_layout.addWidget(subtitle)
        layout.addWidget(header)

        # Scroll Area for Content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(40, 30, 40, 30)
        c_layout.setSpacing(30)

        # --- SECCIÓN 1: ESPECIFICACIONES ---
        spec_frame = QFrame()
        spec_frame.setStyleSheet("background-color: white; border-radius: 15px; border: 1px solid #eef0f2;")
        spec_layout = QHBoxLayout(spec_frame)
        spec_layout.setContentsMargins(20, 20, 20, 20)
        spec_layout.setSpacing(15)

        specs = [
            ("🛏️", f"{self.p[9]} Dormitorios"),
            ("🛌", f"{self.p[10]} Camas"),
            ("🚿", f"{self.p[11]} Baños"),
            ("👥", f"Cap. {self.p[2]} pers.")
        ]

        for icon, text in specs:
            vbox = QVBoxLayout()
            vbox.setAlignment(Qt.AlignCenter)
            lbl_icon = QLabel(icon)
            lbl_icon.setStyleSheet("font-size: 28px; border: none;")
            lbl_text = QLabel(text)
            lbl_text.setStyleSheet("font-size: 13px; font-weight: bold; color: #34495e; border: none;")
            vbox.addWidget(lbl_icon)
            vbox.addWidget(lbl_text)
            spec_layout.addLayout(vbox)
            if icon != specs[-1][0]: # Separador
                line = QFrame()
                line.setFixedWidth(1)
                line.setStyleSheet("background-color: #eee; border: none;")
                spec_layout.addWidget(line)

        c_layout.addWidget(spec_frame)

        # --- SECCIÓN 2: SERVICIOS ADICIONALES ---
        serv_title = QLabel("✨ AMENITIES E INSTALACIONES")
        serv_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #7f8c8d; margin-top: 10px;")
        c_layout.addWidget(serv_title)

        if not self.services:
            no_serv = QLabel("No hay servicios adicionales especificados.")
            no_serv.setStyleSheet("color: #95a5a6; font-style: italic;")
            c_layout.addWidget(no_serv)
        else:
            serv_grid = QGridLayout()
            serv_grid.setSpacing(15)
            
            for i, (icon, name) in enumerate(self.services):
                row, col = divmod(i, 2) # 2 columnas para que sea grande y legible
                
                s_item = QFrame()
                s_item.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #f0f2f5;")
                s_layout = QHBoxLayout(s_item)
                s_layout.setContentsMargins(15, 12, 15, 12)
                
                s_icon = QLabel(icon)
                s_icon.setStyleSheet("font-size: 20px; border: none;")
                s_name = QLabel(name)
                s_name.setStyleSheet("font-size: 14px; font-weight: 500; color: #2c3e50; border: none;")
                
                s_layout.addWidget(s_icon)
                s_layout.addWidget(s_name)
                s_layout.addStretch()
                
                serv_grid.addWidget(s_item, row, col)
            
            c_layout.addLayout(serv_grid)

        c_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Footer Button
        footer = QFrame()
        footer.setFixedHeight(80)
        footer.setStyleSheet("background-color: white; border-top: 1px solid #eee;")
        f_layout = QHBoxLayout(footer)
        f_layout.setAlignment(Qt.AlignCenter)
        
        btn_close = QPushButton("ENTENDIDO / CERRAR")
        btn_close.setFixedSize(250, 45)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #34495e; }
        """)
        btn_close.clicked.connect(self.accept)
        f_layout.addWidget(btn_close)
        layout.addWidget(footer)
