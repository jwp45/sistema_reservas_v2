from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QGridLayout, QWidget, QFrame)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QColor, QFont

class ModernCalendarDialog(QDialog):
    date_selected = Signal(QDate)

    def __init__(self, initial_date=None, parent=None, reserved_ranges=None, target="in"):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Fecha")
        self.setFixedWidth(350)
        self.setFixedHeight(420)
        self.current_date = initial_date or QDate.currentDate()
        self.view_date = QDate(self.current_date.year(), self.current_date.month(), 1)
        self.reserved_ranges = reserved_ranges or []
        self.target = target # "in" o "out"
        
        self.init_ui()
        self.render_calendar()

    def init_ui(self):
        self.setStyleSheet("background-color: white; border-radius: 10px;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header Navigation
        nav_layout = QHBoxLayout()
        
        self.btn_prev = QPushButton("<")
        self.btn_prev.setFixedSize(35, 35)
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.setStyleSheet("""
            QPushButton { background-color: #f0f2f5; color: #2c3e50; border: none; border-radius: 17px; font-weight: bold; }
            QPushButton:hover { background-color: #3498db; color: white; }
        """)
        self.btn_prev.clicked.connect(self.prev_month)

        self.lbl_month = QLabel("")
        self.lbl_month.setAlignment(Qt.AlignCenter)
        self.lbl_month.setStyleSheet("font-size: 16px; font-weight: 800; color: #2c3e50; border: none;")

        self.btn_next = QPushButton(">")
        self.btn_next.setFixedSize(35, 35)
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.setStyleSheet(self.btn_prev.styleSheet())
        self.btn_next.clicked.connect(self.next_month)

        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.lbl_month, 1)
        nav_layout.addWidget(self.btn_next)
        layout.addLayout(nav_layout)

        # Days Header
        days_header = QGridLayout()
        days_header.setSpacing(0)
        days = ["L", "M", "X", "J", "V", "S", "D"]
        for i, d in enumerate(days):
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #95a5a6; font-size: 11px; font-weight: bold; border: none; padding-bottom: 10px;")
            days_header.addWidget(lbl, 0, i)
        layout.addLayout(days_header)

        # Days Grid
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent; border: none;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(5)
        layout.addWidget(self.grid_container)

    def render_calendar(self):
        # Clear grid
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        month_names = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                       "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.lbl_month.setText(f"{month_names[self.view_date.month()]} {self.view_date.year()}")

        # Fill grid
        first_day = self.view_date.dayOfWeek() # 1=Mon, 7=Sun
        days_in_month = self.view_date.daysInMonth()
        
        # Adjust for grid (0-indexed, Mon=0)
        start_col = first_day - 1
        
        now = QDate.currentDate()
        
        row = 0
        for day in range(1, days_in_month + 1):
            col = (start_col + day - 1) % 7
            if col == 0 and day > 1: row += 1
            
            d_obj = QDate(self.view_date.year(), self.view_date.month(), day)
            status = self._get_day_status(d_obj)
            
            btn = QPushButton(str(day))
            btn.setFixedSize(40, 40)
            btn.setCursor(Qt.PointingHandCursor)
            
            is_selected = (self.current_date.day() == day and 
                           self.current_date.month() == self.view_date.month() and 
                           self.current_date.year() == self.view_date.year())
            
            # --- STYLING LOGIC ---
            style = "background-color: transparent; color: #2c3e50; border-radius: 20px; border: none;"
            enabled = True
            
            if d_obj < now:
                style = "background-color: transparent; color: #d1d8e0; border: none;"
                enabled = False
            elif status == "ocupado":
                style = "background-color: #fceaea; color: #e74c3c; border: none; text-decoration: line-through;"
                enabled = False
            elif status == "transicion":
                # Alguien sale y otro entra. Totalmente bloqueado.
                style = "background-color: #f1f8e9; color: #f1c40f; border: 2px solid #f1c40f;"
                enabled = False
            elif status == "ingreso":
                # Alguien entra. Solo se puede elegir si es para SALIR (target="out")
                style = "background-color: #ebf5fb; color: #3498db; font-weight: bold;"
                if self.target == "in": enabled = False
            elif status == "egreso":
                # Alguien sale. Solo se puede elegir si es para ENTRAR (target="in")
                style = "background-color: #f5eef8; color: #9b59b6; font-weight: bold;"
                if self.target == "out": enabled = False
            
            if is_selected:
                style = "background-color: #3498db; color: white; border-radius: 20px; font-weight: bold; border: none;"
            elif col >= 5 and enabled: # Weekend
                style += " color: #e74c3c;"
            
            btn.setEnabled(enabled)
            btn.setStyleSheet(f"QPushButton {{ {style} }} QPushButton:hover {{ background-color: #f0f2f5; color: #3498db; }}")
            
            # Use a closure to capture the day
            btn.clicked.connect(lambda checked=False, d=day: self.select_day(d))
            self.grid_layout.addWidget(btn, row, col)

    def _get_day_status(self, q_date):
        from datetime import date, datetime
        d = date(q_date.year(), q_date.month(), q_date.day())
        
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

    def select_day(self, day):
        self.current_date = QDate(self.view_date.year(), self.view_date.month(), day)
        self.date_selected.emit(self.current_date)
        self.accept()

    def prev_month(self):
        self.view_date = self.view_date.addMonths(-1)
        self.render_calendar()

    def next_month(self):
        self.view_date = self.view_date.addMonths(1)
        self.render_calendar()

        self.current_date = QDate(self.view_date.year(), self.view_date.month(), day)
        self.date_selected.emit(self.current_date)
        self.accept()

    def prev_month(self):
        self.view_date = self.view_date.addMonths(-1)
        self.render_calendar()

    def next_month(self):
        self.view_date = self.view_date.addMonths(1)
        self.render_calendar()
