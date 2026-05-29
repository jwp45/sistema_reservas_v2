from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QMessageBox, 
                             QFrame)
from PySide6.QtCore import Qt
from controllers.database import Database

class ClientFormDialog(QDialog):
    def __init__(self, parent=None, client_data=None):
        super().__init__(parent)
        self.db = Database()
        self.client_id = client_data[0] if client_data else None
        self.setWindowTitle("Nuevo Cliente" if not self.client_id else "Editar Cliente")
        self.setFixedWidth(450)
        
        self.init_ui()
        if client_data:
            self.load_data(client_data)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        title = QLabel(self.windowTitle())
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Form Container
        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 10px; padding: 10px;")
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignRight)
        
        self.edit_doc = QLineEdit()
        self.edit_doc.setPlaceholderText("Ej: 35123456")
        
        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("Nombre")
        
        self.edit_surname = QLineEdit()
        self.edit_surname.setPlaceholderText("Apellido")
        
        self.edit_email = QLineEdit()
        self.edit_email.setPlaceholderText("ejemplo@correo.com")
        
        self.edit_phone = QLineEdit()
        self.edit_phone.setPlaceholderText("Ej: +54 9 11 ...")
        
        # Styling inputs
        for edit in [self.edit_doc, self.edit_name, self.edit_surname, self.edit_email, self.edit_phone]:
            edit.setFixedHeight(35)
            edit.setStyleSheet("background-color: white; border: 1px solid #d1d8e0; border-radius: 5px; padding-left: 10px; color: #2c3e50;")

        form_layout.addRow("📄 DNI:", self.edit_doc)
        form_layout.addRow("👤 Nombre:", self.edit_name)
        form_layout.addRow("👤 Apellido:", self.edit_surname)
        form_layout.addRow("📧 Email:", self.edit_email)
        form_layout.addRow("📞 Teléfono:", self.edit_phone)
        
        layout.addWidget(form_frame)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setFixedHeight(40)
        self.btn_cancel.setStyleSheet("background-color: white; border: 1px solid #d1d8e0; border-radius: 5px; font-weight: bold;")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("Guardar")
        self.btn_save.setFixedHeight(40)
        self.btn_save.setStyleSheet("background-color: #3498db; color: white; border-radius: 5px; font-weight: bold;")
        self.btn_save.clicked.connect(self.save_data)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def load_data(self, c):
        # c = (id, doc, nom, ape, email, tel)
        self.edit_doc.setText(str(c[1]))
        self.edit_name.setText(str(c[2]))
        self.edit_surname.setText(str(c[3]))
        self.edit_email.setText(str(c[4]))
        self.edit_phone.setText(str(c[5]))

    def save_data(self):
        doc = self.edit_doc.text().strip()
        name = self.edit_name.text().strip()
        surname = self.edit_surname.text().strip()
        email = self.edit_email.text().strip()
        phone = self.edit_phone.text().strip()
        
        if not all([doc, name, surname, email, phone]):
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios.")
            return
            
        if not self.db.connect():
            QMessageBox.critical(self, "Error", "No se pudo conectar a la base de datos.")
            return
            
        cursor = self.db.connection.cursor()
        try:
            if self.client_id:
                query = "UPDATE clientes SET documento=%s, nombre=%s, apellido=%s, email=%s, telefono=%s WHERE id_clientes=%s"
                cursor.execute(query, (doc, name, surname, email, phone, self.client_id))
            else:
                query = "INSERT INTO clientes (documento, nombre, apellido, email, telefono) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(query, (doc, name, surname, email, phone))
            
            self.db.connection.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Fallo al guardar: {e}")
