import sys
from PySide6.QtWidgets import QApplication
from ui_v2.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Estilo Global para corregir problemas de visibilidad (Texto en blanco sobre blanco)
    app.setStyleSheet("""
        QWidget {
            color: #2c3e50;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QLabel {
            color: #2c3e50;
        }
        QLineEdit {
            color: #2c3e50;
            background-color: white;
            border: 1px solid #d1d8e0;
            padding: 5px;
        }
        QComboBox {
            color: #2c3e50;
            background-color: white;
            border: 1px solid #d1d8e0;
            padding: 5px;
            combobox-popup: 0;
        }
        QComboBox QAbstractItemView, QListView {
            color: #2c3e50;
            background-color: white;
            selection-background-color: #3498db;
            selection-color: white;
            border: 1px solid #d1d8e0;
            outline: 0px;
        }
        QComboBox QAbstractItemView::item {
            min-height: 35px;
            padding-left: 10px;
            background-color: white;
        }
        QMessageBox {
            background-color: white;
        }
        QMessageBox QLabel {
            color: #2c3e50;
            font-size: 13px;
        }
        QMessageBox QPushButton {
            background-color: #f8f9fa;
            border: 1px solid #d1d8e0;
            border-radius: 4px;
            padding: 5px 15px;
            min-width: 80px;
            font-weight: bold;
        }
        QMessageBox QPushButton:hover {
            background-color: #3498db;
            color: white;
            border: 1px solid #3498db;
        }
        QTableWidget {
            color: #2c3e50;
            gridline-color: #f0f2f5;
        }
        QHeaderView::section {
            color: #7f8c8d;
            background-color: #f8f9fa;
        }
        QCalendarWidget QHeaderView {
            background-color: white;
            color: #2c3e50;
        }
        QCalendarWidget QHeaderView::section {
            background-color: white;
            color: #2c3e50;
            border: none;
            height: 25px;
        }
    """)
    
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
