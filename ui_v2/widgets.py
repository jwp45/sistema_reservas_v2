from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QBrush, QPen, QColor, QLinearGradient, QFont

class BarChartWidget(QWidget):
    def __init__(self, title, color, parent=None):
        super().__init__(parent)
        self.title = title
        self.color = QColor(color)
        self.data = [] # List of (label, value, color) OR (label, [stacked_values], [stacked_colors])
        self.setMinimumHeight(250)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")

    def set_data(self, data):
        self.data = data
        self.update()

    def format_currency(self, val):
        return f"${int(val):,}".replace(",", ".")

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
        
        # Legend (Top Right)
        if self.data and isinstance(self.data[0][1], list):
            legend_x = w - 25
            legend_labels = ["PENDIENTE", "INGRESOS", "ADELANTOS"]
            legend_colors = ["#f1c40f", "#3498db", "#27ae60"] # Matches reverse stack order for clarity
            
            painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
            for label, color_hex in zip(legend_labels, legend_colors):
                # Measure text width
                tw = painter.fontMetrics().horizontalAdvance(label)
                legend_x -= (tw + 20)
                
                # Draw color circle
                painter.setBrush(QBrush(QColor(color_hex)))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(legend_x, 22, 8, 8)
                
                # Draw label
                painter.setPen(QPen(QColor("#7f8c8d")))
                painter.drawText(legend_x + 12, 30, label)
                legend_x -= 10 # Spacing between items
        
        if not self.data:
            painter.setPen(QPen(QColor("#95a5a6")))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(self.rect(), Qt.AlignCenter, "Cargando datos...")
            return

        # Calculate max_val supporting stacked bars
        max_val = 0
        for item in self.data:
            if isinstance(item[1], list):
                max_val = max(max_val, sum(item[1]))
            else:
                max_val = max(max_val, float(item[1]))
        
        if max_val == 0: max_val = 1
        
        bar_w = chart_w / len(self.data)
        
        # Draw horizontal grid lines
        painter.setPen(QPen(QColor("#f0f2f5"), 1, Qt.SolidLine))
        for j in range(5):
            gy = h - padding - (j * chart_h / 4)
            painter.drawLine(padding, gy, w - padding, gy)

        for i, item in enumerate(self.data):
            label = item[0]
            val_data = item[1]
            colors_data = item[2] if len(item) > 2 else self.color
            
            x = padding + (i * bar_w) + (bar_w * 0.15)
            bw = bar_w * 0.7
            
            if isinstance(val_data, list):
                # Stacked Bar
                current_y = h - padding
                total_val = sum(val_data)
                for val, color_hex in zip(val_data, colors_data):
                    if val <= 0: continue
                    bar_height = (val / max_val) * chart_h
                    y = current_y - bar_height
                    
                    color = QColor(color_hex)
                    painter.setBrush(QBrush(color))
                    painter.setPen(Qt.NoPen)
                    painter.drawRect(int(x), int(y), int(bw), int(bar_height))
                    
                    # --- NUEVO: Dibujar valor dentro del segmento si hay espacio ---
                    if bar_height > 15:
                        painter.setPen(QPen(Qt.white if color.lightness() < 180 else QColor("#2c3e50")))
                        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
                        val_text = self.format_currency(val)
                        painter.drawText(int(x), int(y), int(bw), int(bar_height), Qt.AlignCenter, val_text)
                    
                    current_y = y
                
                # Draw total value on top
                if total_val > 0:
                    painter.setPen(QPen(QColor("#2c3e50")))
                    painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    val_text = self.format_currency(total_val)
                    painter.drawText(int(x), int(current_y - 18), int(bw), 15, Qt.AlignCenter, val_text)
            else:
                # Normal Bar
                val = float(val_data)
                color = QColor(colors_data) if isinstance(colors_data, str) else self.color
                bar_height = (val / max_val) * chart_h
                y = h - padding - bar_height
                
                grad = QLinearGradient(x, y, x, y + bar_height)
                grad.setColorAt(0, color)
                grad.setColorAt(1, color.darker(120))
                
                painter.setBrush(QBrush(grad))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(int(x), int(y), int(bw), int(bar_height), 6, 6)
                
                if val > 0:
                    painter.setPen(QPen(QColor("#2c3e50")))
                    painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    val_text = self.format_currency(val)
                    painter.drawText(int(x), int(y - 18), int(bw), 15, Qt.AlignCenter, val_text)
            
            # Label
            painter.setPen(QPen(QColor("#7f8c8d")))
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.drawText(int(x), int(h - padding + 10), int(bw), 20, Qt.AlignCenter, label)

class HorizontalBarChartWidget(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.data = [] # List of (label, value, color)
        self.setMinimumHeight(200)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")

    def set_data(self, data):
        self.data = data
        self.update()

    def format_currency(self, val):
        return f"${val:,.0f}".replace(",", ".")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        padding_left = 130
        padding_right = 90
        padding_top = 60
        padding_bottom = 30

        # Background
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("white")))
        painter.drawRoundedRect(0, 0, w, h, 15, 15)

        # Title
        painter.setPen(QPen(QColor("#2c3e50")))
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.drawText(25, 35, self.title)

        if not self.data:
            painter.setPen(QPen(QColor("#95a5a6")))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(self.rect(), Qt.AlignCenter, "Sin datos...")
            return

        max_val = max([d[1] for d in self.data]) if self.data else 1
        if max_val == 0: max_val = 1

        chart_w = w - padding_left - padding_right
        bar_h = 25
        spacing = (h - padding_top - padding_bottom) / len(self.data)

        for i, (label, val, color_hex) in enumerate(self.data):
            y = padding_top + (i * spacing)
            bar_width = (val / max_val) * chart_w if val > 0 else 5

            # Label (Left)
            painter.setPen(QPen(QColor("#34495e")))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(25, y + (bar_h/2) + 5, padding_left - 35, bar_h, Qt.AlignLeft, label)

            # Bar
            color = QColor(color_hex)
            grad = QLinearGradient(padding_left, y, padding_left + bar_width, y)
            grad.setColorAt(0, color)
            grad.setColorAt(1, color.lighter(110))

            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(padding_left, y, bar_width, bar_h, 4, 4)

            # Value (Right)
            painter.setPen(QPen(QColor("#7f8c8d")))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(padding_left + bar_width + 10, y + (bar_h/2) + 5, padding_right, bar_h, Qt.AlignLeft, self.format_currency(val))

class SeasonStatCard(QFrame):
    def __init__(self, title, color, parent=None):
        super().__init__(parent)
        self.title = title
        self.color = QColor(color)
        self.percentage = 0
        self.center_text = "0"
        self.show_pct = False
        
        self.setFixedHeight(140)
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
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(15)
        
        # Icon Frame
        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setFixedSize(50, 50)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet(f"""
            background-color: {self.color.lighter(170).name()};
            border-radius: 25px;
            font-size: 24px;
            border: none;
        """)
        self.layout.addWidget(self.icon_lbl)
        
        # Text Container
        self.text_container = QWidget()
        self.text_container.setStyleSheet("background: transparent; border: none;")
        self.text_layout = QVBoxLayout(self.text_container)
        self.text_layout.setContentsMargins(0, 0, 0, 0)
        self.text_layout.setSpacing(1)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(f"color: #7f8c8d; font-size: 10px; font-weight: bold; border: none; text-transform: uppercase;")
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(f"color: #2c3e50; font-size: 20px; font-weight: 800; border: none;")
        
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
