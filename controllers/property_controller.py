from controllers.database import Database

class PropertyController:
    def __init__(self):
        self.db = Database()

    def create_property(self):
        # Lógica para crear una nueva propiedad
        print("Crear Propiedad")
        # Aquí se llamará a la función que abre la ventana de creación de propiedades

    def delete_property(self, property_id):
        """Eliminar un inmueble"""
        if self.db.connect():
            return self.db.delete_property(property_id)
        return False
