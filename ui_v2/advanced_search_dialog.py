from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QFrame, QAbstractItemView, QMessageBox,
                             QComboBox, QSpinBox)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFont
from controllers.database import Database
from datetime import datetime, date

class AdvancedSearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.selected_property = None
        self.selected_dates = None
        
        self.setWindowTitle("Búsqueda Avanzada de Disponibilidad")
        self.resize(900, 700)
        
        self.init_ui()
        self.load_filters()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        title = QLabel("🔍 ENCONTRAR INMUEBLES DISPONIBLES")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        # Filter Panel
        filter_card = QFrame()
        filter_card.setStyleSheet("background-color: #f8f9fa; border-radius: 10px; border: 1px solid #e0e0e0;")
        f_layout = QVBoxLayout(filter_card)
        f_layout.setContentsMargins(20, 20, 20, 20)
        
        # Row 1: Dates
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Ingreso:"))
        self.edit_in = QLineEdit()
        self.edit_in.setPlaceholderText("DD/MM/YYYY")
        row1.addWidget(self.edit_in)
        
        row1.addWidget(QLabel("Egreso:"))
        self.edit_out = QLineEdit()
        self.edit_out.setPlaceholderText("DD/MM/YYYY")
        row1.addWidget(self.edit_out)
        
        row1.addWidget(QLabel("Personas:"))
        self.spin_people = QSpinBox()
        self.spin_people.setRange(1, 50)
        row1.addWidget(self.spin_people)
        f_layout.addLayout(row1)
        
        # Row 2: Location
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Provincia:"))
        self.combo_prov = QComboBox()
        self.combo_prov.currentTextChanged.connect(self.update_localidades)
        row2.addWidget(self.combo_prov)
        
        row2.addWidget(QLabel("Localidad:"))
        self.combo_loc = QComboBox()
        row2.addWidget(self.combo_loc)
        
        btn_search = QPushButton("BUSCAR DISPONIBLES")
        btn_search.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 10px;")
        btn_search.clicked.connect(self.perform_search)
        row2.addWidget(btn_search)
        f_layout.addLayout(row2)
        
        layout.addWidget(filter_card)

        # Results Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Inmueble", "Capacidad", "Ubicación", "Precio/Noche"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.itemDoubleClicked.connect(self.confirm_selection)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table)
        
        lbl_help = QLabel("* Doble click en un resultado para seleccionarlo y volver al calendario.")
        lbl_help.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic;")
        layout.addWidget(lbl_help)

    def load_filters(self):
        if not self.db.connect(): return
        props = self.db.get_all_properties()
        provincias = sorted(list(set(p[5] for p in props)))
        self.combo_prov.addItem("Todas")
        self.combo_prov.addItems(provincias)
        self.update_localidades()

    def update_localidades(self):
        prov = self.combo_prov.currentText()
        if not self.db.connect(): return
        props = self.db.get_all_properties()
        if prov == "Todas":
            locs = sorted(list(set(p[4] for p in props)))
        else:
            locs = sorted(list(set(p[4] for p in props if p[5] == prov)))
        
        self.combo_loc.clear()
        self.combo_loc.addItem("Todas")
        self.combo_loc.addItems(locs)

    def perform_search(self):
        try:
            d_in = datetime.strptime(self.edit_in.text(), "%d/%m/%Y").date()
            d_out = datetime.strptime(self.edit_out.text(), "%d/%m/%Y").date()
        except:
            QMessageBox.warning(self, "Error", "Formato de fecha inválido (DD/MM/YYYY)")
            return
            
        if d_out <= d_in:
            QMessageBox.warning(self, "Error", "La fecha de egreso debe ser posterior.")
            return

        if not self.db.connect(): return
        all_props = self.db.get_all_properties()
        results = []
        
        prov = self.combo_prov.currentText()
        loc = self.combo_loc.currentText()
        min_p = self.spin_people.value()
        
        for p in all_props:
            # p = (id, nombre, cap, dir, loc, prov, tipo, val, ...)
            if p[2] < min_p: continue
            if prov != "Todas" and p[5] != prov: continue
            if loc != "Todas" and p[4] != loc: continue
            
            if self.db.is_range_available(p[0], d_in, d_out):
                results.append(p)
                
        self.display_results(results)

    def display_results(self, data):
        self.table.setRowCount(0)
        for p in data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(p[0])))
            self.table.setItem(row, 1, QTableWidgetItem(str(p[1]).upper()))
            self.table.setItem(row, 2, QTableWidgetItem(f"{p[2]} pers."))
            self.table.setItem(row, 3, QTableWidgetItem(f"{p[4]}, {p[5]}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"${p[7]:,.2f}"))
            
            self.table.item(row, 0).setTextAlignment(Qt.AlignCenter)

    def confirm_selection(self, item):
        row = item.row()
        pid = int(self.table.item(row, 0).text())
        
        if not self.db.connect(): return
        props = self.db.get_all_properties()
        self.selected_property = next((p for p in props if p[0] == pid), None)
        
        self.selected_dates = {
            "desde": datetime.strptime(self.edit_in.text(), "%d/%m/%Y").date(),
            "hasta": datetime.strptime(self.edit_out.text(), "%d/%m/%Y").date()
        }
        self.accept()
