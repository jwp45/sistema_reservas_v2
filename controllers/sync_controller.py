import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os
import threading

class SyncController:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SyncController, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.db_firestore = None
        self.cred_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "firebase_key.json")
        self.initialized = self._initialize_firebase()
        self._initialized = True
        self.on_task_updated = None # Callback para la UI

    def _initialize_firebase(self):
        try:
            if not os.path.exists(self.cred_path):
                print("SyncController: firebase_key.json no encontrado.")
                return False
            
            if not firebase_admin._apps:
                cred = credentials.Certificate(self.cred_path)
                firebase_admin.initialize_app(cred)
            
            self.db_firestore = firestore.client()
            print("SyncController: Conectado a Firebase Firestore.")
            return True
        except Exception as e:
            print(f"SyncController: Error al inicializar Firebase: {e}")
            return False

    def sync_staff(self, staff_list):
        """Sincroniza la lista de personal con Firestore"""
        if not self.initialized: return False
        
        try:
            batch = self.db_firestore.batch()
            for s in staff_list:
                # s = (id, nombre, telefono, pin, estado, ...)
                staff_ref = self.db_firestore.collection('staff').document(str(s[0]))
                batch.set(staff_ref, {
                    'name': s[1],
                    'phone': s[2],
                    'pin': s[3],
                    'status': s[4]
                })
            batch.commit()
            return True
        except Exception as e:
            print(f"SyncController: Error al sincronizar personal: {e}")
            return False

    def upload_task(self, task_data):
        """Sube una nueva tarea a Firestore"""
        if not self.initialized: return False
        
        try:
            # task_data de CleaningPage: id_inmueble, id_reserva, id_personal, pago
            # Necesitamos más info para la App (dirección, nombre inmueble)
            from controllers.database import Database
            db = Database()
            prop = db.get_property_details(task_data['id_inmueble'])
            
            task_id = f"task_{task_data['id_inmueble']}_{task_data['id_reserva']}"
            task_ref = self.db_firestore.collection('tasks').document(task_id)
            
            doc_data = {
                'id_property': task_data['id_inmueble'],
                'id_reservation': task_data['id_reserva'],
                'property_name': prop['nombre'],
                'address': prop['direccion'],
                'fee_per_hour': task_data['pago'],
                'status': 'pending',
                'staff_id': str(task_data['id_personal']) if task_data['id_personal'] else None,
                'staff_name': None, # Se llenará cuando alguien acepte si es "TODOS"
                'created_at': firestore.SERVER_TIMESTAMP,
                'started_at': None,
                'finished_at': None,
                'hours': 0,
                'observations': ""
            }
            
            task_ref.set(doc_data)
            return True
        except Exception as e:
            print(f"SyncController: Error al subir tarea: {e}")
            return False

    def delete_task(self, id_inmueble, id_reserva):
        """Elimina una tarea de Firestore"""
        if not self.initialized: return False
        try:
            task_id = f"task_{id_inmueble}_{id_reserva}"
            self.db_firestore.collection('tasks').document(task_id).delete()
            print(f"SyncController: Tarea {task_id} eliminada de Firestore.")
            return True
        except Exception as e:
            print(f"SyncController: Error al eliminar tarea: {e}")
            return False

    def start_listener(self, callback):
        """Inicia un listener para cambios en las tareas"""
        if not self.initialized: return
        
        self.on_task_updated = callback
        self.tasks_ref = self.db_firestore.collection('tasks').where('status', 'in', ['accepted', 'finished'])
        self.query_watch = self.tasks_ref.on_snapshot(self._on_snapshot)

    def _on_snapshot(self, col_snapshot, changes, read_time):
        for change in changes:
            if change.type.name in ['ADDED', 'MODIFIED']:
                doc = change.document.to_dict()
                doc_id = change.document.id
                print(f"SyncController: Tarea actualizada en la nube: {doc_id}")
                if self.on_task_updated:
                    self.on_task_updated(doc_id, doc)

    def stop_listener(self):
        if hasattr(self, 'query_watch'):
            self.query_watch.unsubscribe()
