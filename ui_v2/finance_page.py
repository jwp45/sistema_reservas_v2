from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QFrame, QAbstractItemView, QScrollArea,
                             QGridLayout, QApplication)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QLinearGradient
from controllers.database import Database
from datetime import datetime
from ui_v2.payment_dialog import PaymentDialog

# Re-using logic from dashboard for consistency
class FinBarChart(QWidget):
    def __init__(self, title, color, parent=None):
        super().__init__(parent)
        self.title = title
        self.color = QColor(color)
        self.data = []
        self.setMinimumHeight(220) # Reducido de 300 a 220
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        padding = 50
        chart_w, chart_h = w - (padding * 2), h - (padding * 2) - 30
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("white")))
        painter.drawRoundedRect(0, 0, w, h, 15, 15)
        
        painter.setPen(QPen(QColor("#2c3e50")))
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.drawText(30, 35, self.title)
        
        if not self.data: return
        # Convert values to float (fixes decimal.Decimal issues)
        values = [float(v) for _, v in self.data]
        max_val = max(values) if values else 1
        if max_val == 0: max_val = 1
        bar_w = chart_w / len(self.data)
        
        painter.setPen(QPen(QColor("#f0f2f5"), 1))
        for j in range(5):
            gy = int(h - padding - (j * chart_h / 4))
            painter.drawLine(padding, gy, w - padding, gy)

        for i, (label, val) in enumerate(self.data):
            val_f = float(val)
            bar_h = (val_f / max_val) * chart_h
            x = padding + (i * bar_w) + (bar_w * 0.2)
            y = h - padding - bar_h
            bw = bar_w * 0.6
            
            grad = QLinearGradient(x, y, x, y + bar_h)
            grad.setColorAt(0, self.color)
            grad.setColorAt(1, self.color.darker(115))
            
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.NoPen)
            # EXPLICIT CAST TO INT for all coordinates (fixes overflow and type errors)
            painter.drawRoundedRect(int(x), int(y), int(bw), int(bar_h), 5, 5)
            
            painter.setPen(QPen(QColor("#7f8c8d")))
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.drawText(int(x), int(h - padding + 10), int(bw), 20, Qt.AlignCenter, label)

class FinKPICard(QFrame):
    def __init__(self, title, color, value="$0", icon="💰", parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.setFixedHeight(120)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 15px;
                border: 1px solid #eef0f2;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(25, 0, 25, 0)
        layout.setSpacing(20)
        
        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setFixedSize(60, 60)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet(f"background-color: {self.color.lighter(175).name()}; border-radius: 30px; font-size: 28px; border: none;")
        layout.addWidget(self.icon_lbl)
        
        txt_container = QWidget()
        txt_container.setStyleSheet("background: transparent; border: none;")
        txt_layout = QVBoxLayout(txt_container)
        txt_layout.setContentsMargins(0, 0, 0, 0)
        txt_layout.setSpacing(2)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color: #7f8c8d; font-size: 11px; font-weight: bold; border: none; text-transform: uppercase;")
        self.lbl_val = QLabel(value)
        self.lbl_val.setStyleSheet("color: #2c3e50; font-size: 26px; font-weight: 800; border: none;")
        
        txt_layout.addWidget(self.lbl_title)
        txt_layout.addWidget(self.lbl_val)
        layout.addWidget(txt_container, 1)

    def set_value(self, val):
        self.lbl_val.setText(val)

class PropertyPerformanceCard(QFrame):
    def __init__(self, name, revenue, percentage=0, parent=None):
        super().__init__(parent)
        self.setFixedHeight(85)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #f0f2f5;
            }
            QFrame:hover {
                border: 1px solid #3498db;
                background-color: #fcfdfe;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 20, 0)
        
        # Icon/Thumbnail placeholder
        self.icon_lbl = QLabel("🏠")
        self.icon_lbl.setFixedSize(45, 45)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet("background-color: #f8f9fa; border-radius: 10px; font-size: 20px; border: none;")
        layout.addWidget(self.icon_lbl)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(10, 0, 0, 0)
        
        self.name_lbl = QLabel(name.upper())
        self.name_lbl.setStyleSheet("color: #2c3e50; font-size: 13px; font-weight: 700; border: none;")
        
        # Mini progress bar container
        progress_container = QWidget()
        progress_container.setFixedHeight(6)
        progress_container.setStyleSheet("background-color: #f1f2f6; border-radius: 3px; border: none;")
        self.bar = QFrame(progress_container)
        self.bar.setFixedHeight(6)
        self.bar.setStyleSheet(f"background-color: #3498db; border-radius: 3px; border: none;")
        self.bar.setFixedWidth(int(150 * (percentage/100.0)) if percentage > 0 else 0)
        
        info_layout.addWidget(self.name_lbl)
        info_layout.addWidget(progress_container)
        layout.addLayout(info_layout, 1)
        
        self.rev_lbl = QLabel(revenue)
        self.rev_lbl.setStyleSheet("color: #27ae60; font-size: 16px; font-weight: 800; border: none;")
        layout.addWidget(self.rev_lbl, 0, Qt.AlignRight | Qt.AlignVCenter)

class DebtCard(QFrame):
    pay_clicked = Signal(int, str, float)

    def __init__(self, res_id, guest, date, balance, parent=None):
        super().__init__(parent)
        self.res_id = res_id
        self.guest = guest
        self.balance = balance
        
        self.setFixedHeight(95)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #f0f2f5;
            }
            QFrame:hover {
                border: 1px solid #e74c3c;
                background-color: #fffafa;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        
        # Left Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        code_lbl = QLabel(f"RESERVA R-{str(res_id).zfill(5)}")
        code_lbl.setStyleSheet("color: #7f8c8d; font-size: 10px; font-weight: bold; border: none;")
        
        guest_lbl = QLabel(guest.upper())
        guest_lbl.setStyleSheet("color: #2c3e50; font-size: 14px; font-weight: 700; border: none;")
        
        date_lbl = QLabel(f"📅 Ingreso: {date}")
        date_lbl.setStyleSheet("color: #95a5a6; font-size: 11px; border: none;")
        
        info_layout.addWidget(code_lbl)
        info_layout.addWidget(guest_lbl)
        info_layout.addWidget(date_lbl)
        layout.addLayout(info_layout, 1)
        
        # Right Info (Balance + Button)
        right_layout = QVBoxLayout()
        right_layout.setSpacing(5)
        right_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        bal_lbl = QLabel(balance)
        bal_lbl.setStyleSheet("color: #e74c3c; font-size: 18px; font-weight: 800; border: none;")
        
        self.btn_pay = QPushButton("PAGAR")
        self.btn_pay.setFixedSize(80, 28)
        self.btn_pay.setCursor(Qt.PointingHandCursor)
        self.btn_pay.setStyleSheet("""
            QPushButton { 
                background-color: #e74c3c; 
                color: white; 
                border-radius: 14px; 
                font-weight: bold; 
                font-size: 10px; 
                border: none;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        self.btn_pay.clicked.connect(self.on_pay_clicked)
        
        right_layout.addWidget(bal_lbl)
        right_layout.addWidget(self.btn_pay)
        layout.addLayout(right_layout)

    def on_pay_clicked(self):
        # Clean currency string for float conversion
        clean_bal = float(self.balance.replace('$', '').replace('.', '').replace(',', '.'))
        self.pay_clicked.emit(self.res_id, self.guest, clean_bal)

class FinancePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)

        # Header
        header = QHBoxLayout()
        title_container = QVBoxLayout()
        title = QLabel("Dashboard Financiero")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #2c3e50;")
        self.lbl_update = QLabel("Actualizado: -")
        self.lbl_update.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        title_container.addWidget(title)
        title_container.addWidget(self.lbl_update)
        
        btn_refresh = QPushButton("🔄 ACTUALIZAR DATOS")
        btn_refresh.setFixedSize(200, 45)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet("""
            QPushButton { background-color: white; border: 1px solid #d1d8e0; border-radius: 22px; font-weight: bold; color: #34495e; }
            QPushButton:hover { background-color: #f8f9fa; border: 1px solid #3498db; }
        """)
        btn_refresh.clicked.connect(self.load_data)
        
        header.addLayout(title_container)
        header.addStretch()
        header.addWidget(btn_refresh)
        layout.addLayout(header)

        # KPIs row
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(20)
        self.kpi_total = FinKPICard("FACTURACIÓN TOTAL", "#34495e", icon="📊")
        self.kpi_collected = FinKPICard("TOTAL RECAUDADO", "#27ae60", icon="✅")
        self.kpi_pending = FinKPICard("SALDO PENDIENTE", "#e74c3c", icon="⏳")
        kpi_layout.addWidget(self.kpi_total)
        kpi_layout.addWidget(self.kpi_collected)
        kpi_layout.addWidget(self.kpi_pending)
        layout.addLayout(kpi_layout)

        # Charts Area
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(25)
        self.revenue_chart = FinBarChart("Evolución de Ingresos (Mensual)", "#3498db")
        charts_layout.addWidget(self.revenue_chart)
        layout.addLayout(charts_layout, 2)

        # Tables Grid (Now Cards Grid)
        tables_grid = QGridLayout()
        tables_grid.setSpacing(25)

        # Performance by Property
        prop_sec = self.create_section("🏆 RENDIMIENTO POR INMUEBLE")
        self.prop_scroll = QScrollArea()
        self.prop_scroll.setWidgetResizable(True)
        self.prop_scroll.setFrameShape(QFrame.NoFrame)
        self.prop_scroll.setStyleSheet("background: transparent;")
        
        self.prop_container = QWidget()
        self.prop_container.setStyleSheet("background: transparent;")
        self.prop_layout = QVBoxLayout(self.prop_container)
        self.prop_layout.setContentsMargins(0, 0, 0, 0)
        self.prop_layout.setSpacing(10)
        self.prop_layout.addStretch()
        
        self.prop_scroll.setWidget(self.prop_container)
        prop_sec.layout().addWidget(self.prop_scroll)
        tables_grid.addWidget(prop_sec, 0, 0)

        # Debtors
        debt_sec = self.create_section("⚠️ DEUDAS PENDIENTES")
        self.debt_scroll = QScrollArea()
        self.debt_scroll.setWidgetResizable(True)
        self.debt_scroll.setFrameShape(QFrame.NoFrame)
        self.debt_scroll.setStyleSheet("background: transparent;")
        
        self.debt_container = QWidget()
        self.debt_container.setStyleSheet("background: transparent;")
        self.debt_layout = QVBoxLayout(self.debt_container)
        self.debt_layout.setContentsMargins(0, 0, 0, 0)
        self.debt_layout.setSpacing(10)
        self.debt_layout.addStretch()
        
        self.debt_scroll.setWidget(self.debt_container)
        debt_sec.layout().addWidget(self.debt_scroll)
        tables_grid.addWidget(debt_sec, 0, 1)
        
        layout.addLayout(tables_grid, 3)

    def create_section(self, title):
        frame = QFrame()
        frame.setStyleSheet("background-color: white; border-radius: 15px; border: 1px solid #eef0f2;")
        l = QVBoxLayout(frame)
        l.setContentsMargins(25, 25, 25, 25)
        lbl = QLabel(title)
        lbl.setStyleSheet("font-weight: 800; color: #34495e; font-size: 13px; border: none; margin-bottom: 15px;")
        l.addWidget(lbl)
        return frame

    def load_data(self):
        if not self.db.connect(): return
        
        # 1. KPIs
        summary = self.db.get_financial_summary()
        self.kpi_total.set_value(self.format_currency(summary[0]))
        self.kpi_collected.set_value(self.format_currency(summary[1]))
        self.kpi_pending.set_value(self.format_currency(summary[2]))
        
        # 2. Chart
        month_data = self.db.get_revenue_by_month()
        self.revenue_chart.set_data(month_data)

        # 3. Property Performance (Cards)
        # Clear layout
        while self.prop_layout.count() > 1:
            item = self.prop_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        prop_data = self.db.get_revenue_by_property()
        max_rev = max([float(v) for _, v in prop_data]) if prop_data else 1
        
        for name, val in prop_data:
            perc = (float(val) / max_rev) * 100 if max_rev > 0 else 0
            card = PropertyPerformanceCard(name, self.format_currency(val), perc)
            self.prop_layout.insertWidget(self.prop_layout.count() - 1, card)

        # 4. Debtors (Cards)
        # Clear layout
        while self.debt_layout.count() > 1:
            item = self.debt_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        debt_data = self.db.get_pending_payments_list()
        for rid, client, prop, f_ing, debt in debt_data:
            card = DebtCard(rid, client, self.fmt_date(f_ing), self.format_currency(debt))
            card.pay_clicked.connect(self.open_payment_from_card)
            self.debt_layout.insertWidget(self.debt_layout.count() - 1, card)

        self.lbl_update.setText(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    def open_payment_from_card(self, res_id, guest, debt):
        dialog = PaymentDialog(self, reservation_id=res_id, client_name=guest, pending_amount=debt)
        if dialog.exec():
            self.load_data()

    def fmt_date(self, d):
        try:
            dt = datetime.strptime(str(d), "%Y-%m-%d") if isinstance(d, str) else d
            return dt.strftime("%d/%m/%y")
        except: return str(d)

    def format_currency(self, value):
        try:
            val = float(value)
            return f"${val:,.0f}".replace(",", ".")
        except: return str(value)

