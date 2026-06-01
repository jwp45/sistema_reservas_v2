import mysql.connector
from datetime import date, timedelta

class Database:
    def __init__(self):
        self.host = "localhost"
        self.user = "root"
        self.password = ""
        self.database = "clientes"
        self.connection = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                print("Conexión exitosa a la base de datos")
                self._init_db()
                return True
        except Exception as e:
            print(f"Error al conectar a la base de datos: {e}")
            return False

    def _init_db(self):
        """Inicializa las tablas necesarias si no existen y sincroniza datos."""
        # Eliminamos el check de _db_initialized para asegurar que la sincronización ocurra al menos una vez
        try:
            cursor = self.connection.cursor(buffered=True)
            
            # 1. Crear tabla de prospectos si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prospectos (
                    id_prospecto INT AUTO_INCREMENT PRIMARY KEY,
                    documento VARCHAR(20) DEFAULT 'S/D',
                    nombre VARCHAR(100) NOT NULL,
                    apellido VARCHAR(100) NOT NULL,
                    email VARCHAR(100),
                    telefono VARCHAR(50) NOT NULL,
                    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 2. Crear tabla de cotizaciones si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cotizaciones (
                    id_cotizacion INT AUTO_INCREMENT PRIMARY KEY,
                    id_cliente INT NULL,
                    id_prospecto INT NULL,
                    id_inmueble INT NOT NULL,
                    fecha_ingreso DATE NOT NULL,
                    fecha_egreso DATE NOT NULL,
                    noches INT NOT NULL,
                    valor_dia DECIMAL(10, 2) NOT NULL,
                    costo_total DECIMAL(10, 2) NOT NULL,
                    descuento DECIMAL(10, 2) DEFAULT 0,
                    costo_con_descuento DECIMAL(10, 2) NOT NULL,
                    fecha_cotizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    mkt_enviado TINYINT(1) DEFAULT 0,
                    FOREIGN KEY (id_cliente) REFERENCES clientes(id_clientes) ON DELETE CASCADE,
                    FOREIGN KEY (id_prospecto) REFERENCES prospectos(id_prospecto) ON DELETE CASCADE,
                    FOREIGN KEY (id_inmueble) REFERENCES inmuebles(id_inmueble) ON DELETE CASCADE
                )
            """)

            # 3. Crear tablas de limpieza si no existen
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS personal_limpieza (
                    id_personal INT PRIMARY KEY AUTO_INCREMENT,
                    nombre VARCHAR(100) NOT NULL,
                    telefono VARCHAR(20),
                    pin_acceso VARCHAR(10),
                    estado ENUM('activo', 'inactivo') DEFAULT 'activo',
                    sincronizado TINYINT(1) DEFAULT 0
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tareas_limpieza (
                    id_tarea INT PRIMARY KEY AUTO_INCREMENT,
                    id_inmueble INT,
                    id_reserva INT,
                    id_personal INT,
                    fecha_asignacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_inicio DATETIME NULL,
                    fecha_finalizacion DATETIME NULL,
                    pago_servicio DECIMAL(10,2),
                    estado ENUM('pendiente', 'en_proceso', 'completada', 'verificada') DEFAULT 'pendiente',
                    observaciones TEXT,
                    sincronizado TINYINT(1) DEFAULT 0,
                    FOREIGN KEY (id_inmueble) REFERENCES inmuebles(id_inmueble),
                    FOREIGN KEY (id_reserva) REFERENCES reservas(id_reserva),
                    FOREIGN KEY (id_personal) REFERENCES personal_limpieza(id_personal)
                )
            """)

            # 4. Crear tabla historial_pagos si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historial_pagos (
                    id_pago INT PRIMARY KEY AUTO_INCREMENT,
                    id_reserva INT,
                    monto DECIMAL(10,2),
                    fecha_pago DATETIME DEFAULT CURRENT_TIMESTAMP,
                    nota VARCHAR(255) DEFAULT NULL,
                    FOREIGN KEY (id_reserva) REFERENCES reservas(id_reserva) ON DELETE CASCADE
                )
            """)

            # Sincronización quirúrgica de historial_pagos
            cursor.execute("DESCRIBE historial_pagos")
            pay_cols = [c[0] for c in cursor.fetchall()]
            if 'nota' not in pay_cols:
                cursor.execute("ALTER TABLE historial_pagos ADD COLUMN nota VARCHAR(255) DEFAULT NULL")

            # Sincronización de columnas adicionales en Inmuebles
            cursor.execute("DESCRIBE inmuebles")
            prop_cols = [c[0] for c in cursor.fetchall()]
            if 'tarifa_limpieza' not in prop_cols:
                cursor.execute("ALTER TABLE inmuebles ADD COLUMN tarifa_limpieza DECIMAL(10,2) DEFAULT 0.00")

            # 4. Crear tabla de configuración (Aseguramos columnas de temporada y Resend)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuracion (
                    id INT PRIMARY KEY DEFAULT 1,
                    smtp_server VARCHAR(255),
                    smtp_port INT,
                    smtp_user VARCHAR(255),
                    smtp_password VARCHAR(255),
                    from_email VARCHAR(255),
                    business_name VARCHAR(255),
                    whatsapp_number VARCHAR(50),
                    logo_path VARCHAR(255),
                    season_start DATE DEFAULT NULL,
                    season_end DATE DEFAULT NULL,
                    resend_api_key VARCHAR(255),
                    email_service_type VARCHAR(20) DEFAULT 'SMTP',
                    channel_quotations VARCHAR(20) DEFAULT 'Both',
                    channel_reservations VARCHAR(20) DEFAULT 'Email'
                )
            """)

            # Sincronización quirúrgica de configuración
            cursor.execute("DESCRIBE configuracion")
            config_cols = [c[0] for c in cursor.fetchall()]
            if 'channel_cleaning' not in config_cols:
                cursor.execute("ALTER TABLE configuracion ADD COLUMN channel_cleaning VARCHAR(20) DEFAULT 'Both'")
            if 'firebase_api_key' not in config_cols:
                cursor.execute("ALTER TABLE configuracion ADD COLUMN firebase_api_key TEXT")
            if 'firebase_project_id' not in config_cols:
                cursor.execute("ALTER TABLE configuracion ADD COLUMN firebase_project_id VARCHAR(100)")

            # 5. Sincronización quirúrgica (SOLO si las columnas no están)
            cursor.execute("DESCRIBE cotizaciones")
            cols = {c[0]: c for c in cursor.fetchall()}

            if 'id_prospecto' not in cols:
                cursor.execute("SET FOREIGN_KEY_CHECKS=0")
                cursor.execute("ALTER TABLE cotizaciones ADD COLUMN id_prospecto INT NULL AFTER id_cliente")
                cursor.execute("ALTER TABLE cotizaciones ADD CONSTRAINT fk_cot_prospecto FOREIGN KEY (id_prospecto) REFERENCES prospectos(id_prospecto) ON DELETE CASCADE")
                cursor.execute("SET FOREIGN_KEY_CHECKS=1")
                
            if 'mkt_enviado' not in cols:
                cursor.execute("ALTER TABLE cotizaciones ADD COLUMN mkt_enviado TINYINT(1) DEFAULT 0")

            if cols.get('id_cliente') and cols['id_cliente'][2] == 'NO':
                cursor.execute("SET FOREIGN_KEY_CHECKS=0")
                cursor.execute("ALTER TABLE cotizaciones MODIFY COLUMN id_cliente INT NULL")
                cursor.execute("SET FOREIGN_KEY_CHECKS=1")

            # 3. Crear tabla de configuración (Aseguramos columnas de temporada y Resend)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuracion (
                    id INT PRIMARY KEY DEFAULT 1,
                    smtp_server VARCHAR(255),
                    smtp_port INT,
                    smtp_user VARCHAR(255),
                    smtp_password VARCHAR(255),
                    from_email VARCHAR(255),
                    business_name VARCHAR(255),
                    whatsapp_number VARCHAR(50),
                    logo_path VARCHAR(255),
                    season_start DATE DEFAULT NULL,
                    season_end DATE DEFAULT NULL,
                    show_wa_educational_msg TINYINT(1) DEFAULT 1,
                    email_service_type VARCHAR(20) DEFAULT 'SMTP',
                    resend_api_key VARCHAR(255),
                    resend_from_email VARCHAR(255),
                    reminder_days_before INT DEFAULT 5,
                    channel_quotations VARCHAR(20) DEFAULT 'Both',
                    channel_reservations VARCHAR(20) DEFAULT 'Email',
                    channel_reminders VARCHAR(20) DEFAULT 'Both',
                    CHECK (id = 1)
                )
            """)
            
            # Sincronizar columnas si ya existe la tabla
            cursor.execute("DESCRIBE configuracion")
            conf_cols = {c[0]: c for c in cursor.fetchall()}
            if 'season_start' not in conf_cols:
                cursor.execute("ALTER TABLE configuracion ADD COLUMN season_start DATE DEFAULT NULL")
            if 'season_end' not in conf_cols:
                cursor.execute("ALTER TABLE configuracion ADD COLUMN season_end DATE DEFAULT NULL")
            if 'logo_path' not in conf_cols:
                cursor.execute("ALTER TABLE configuracion ADD COLUMN logo_path VARCHAR(255)")
            if 'show_wa_educational_msg' not in conf_cols:
                cursor.execute("ALTER TABLE configuracion ADD COLUMN show_wa_educational_msg TINYINT(1) DEFAULT 1")
            if 'email_service_type' not in conf_cols:
                cursor.execute("ALTER TABLE configuracion ADD COLUMN email_service_type VARCHAR(20) DEFAULT 'SMTP'")
            if 'resend_api_key' not in conf_cols:
                cursor.execute("ALTER TABLE configuracion ADD COLUMN resend_api_key VARCHAR(255)")
            if 'resend_from_email' not in conf_cols:
                cursor.execute("ALTER TABLE configuracion ADD COLUMN resend_from_email VARCHAR(255)")
            if 'reminder_days_before' not in conf_cols:
                cursor.execute("ALTER TABLE configuracion ADD COLUMN reminder_days_before INT DEFAULT 5")
            if 'whatsapp_service_type' not in conf_cols:
                cursor.execute("ALTER TABLE configuracion ADD COLUMN whatsapp_service_type VARCHAR(20) DEFAULT 'Manual'")
            if 'whatsapp_api_key' not in conf_cols:
                cursor.execute("ALTER TABLE configuracion ADD COLUMN whatsapp_api_key VARCHAR(255) DEFAULT NULL")
            if 'whatsapp_api_url' not in conf_cols:
                cursor.execute("ALTER TABLE configuracion ADD COLUMN whatsapp_api_url VARCHAR(255) DEFAULT NULL")
            if 'whatsapp_acc_id' not in conf_cols:
                cursor.execute("ALTER TABLE configuracion ADD COLUMN whatsapp_acc_id VARCHAR(255) DEFAULT NULL")
            if 'channel_quotations' not in conf_cols:
                cursor.execute("ALTER TABLE configuracion ADD COLUMN channel_quotations VARCHAR(20) DEFAULT 'Both'")
            if 'channel_reservations' not in conf_cols:
                cursor.execute("ALTER TABLE configuracion ADD COLUMN channel_reservations VARCHAR(20) DEFAULT 'Email'")
            if 'channel_reminders' not in conf_cols:
                cursor.execute("ALTER TABLE configuracion ADD COLUMN channel_reminders VARCHAR(20) DEFAULT 'Both'")

            # Asegurar columna recordatorio_enviado y fecha_envio_recordatorio en reservas
            cursor.execute("DESCRIBE reservas")
            res_cols = {c[0]: c for c in cursor.fetchall()}
            if 'recordatorio_enviado' not in res_cols:
                cursor.execute("ALTER TABLE reservas ADD COLUMN recordatorio_enviado TINYINT(1) DEFAULT 0")
            if 'fecha_envio_recordatorio' not in res_cols:
                cursor.execute("ALTER TABLE reservas ADD COLUMN fecha_envio_recordatorio DATETIME DEFAULT NULL")
            if 'fecha_creacion' not in res_cols:
                cursor.execute("ALTER TABLE reservas ADD COLUMN fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP")
            if 'checkin_status' not in res_cols:
                cursor.execute("ALTER TABLE reservas ADD COLUMN checkin_status TINYINT(1) DEFAULT 0")
            if 'checkout_status' not in res_cols:
                cursor.execute("ALTER TABLE reservas ADD COLUMN checkout_status TINYINT(1) DEFAULT 0")

            # Asegurar columnas en inmuebles
            cursor.execute("DESCRIBE inmuebles")
            inm_cols = {c[0]: c for c in cursor.fetchall()}
            if 'dormitorios' not in inm_cols:
                cursor.execute("ALTER TABLE inmuebles ADD COLUMN dormitorios INT DEFAULT 0")
            if 'camas' not in inm_cols:
                cursor.execute("ALTER TABLE inmuebles ADD COLUMN camas INT DEFAULT 0")
            if 'baños' not in inm_cols:
                cursor.execute("ALTER TABLE inmuebles ADD COLUMN baños INT DEFAULT 0")
            if 'video_url' not in inm_cols:
                cursor.execute("ALTER TABLE inmuebles ADD COLUMN video_url VARCHAR(255) DEFAULT NULL")
            if 'checkin_time' not in inm_cols:
                cursor.execute("ALTER TABLE inmuebles ADD COLUMN checkin_time VARCHAR(20) DEFAULT '14:00'")
            if 'checkout_time' not in inm_cols:
                cursor.execute("ALTER TABLE inmuebles ADD COLUMN checkout_time VARCHAR(20) DEFAULT '10:00'")

            # ASEGURAR QUE EXISTE LA FILA ID=1
            cursor.execute("SELECT COUNT(*) FROM configuracion WHERE id = 1")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO configuracion (id, smtp_server, smtp_port, smtp_user, smtp_password, from_email, business_name, whatsapp_number, logo_path)
                    VALUES (1, 'smtp.gmail.com', 587, 'wolf10dra@gmail.com', 'xsyy xbcl rkoq esud', 'wolf10dra@gmail.com', 'Sistema de Reservas', '5492236689548', '')
                """)
                print("DEBUG: Fila de configuración ID=1 creada.")
            
            self.connection.commit()
            self._db_initialized = True
            cursor.close()
        except Exception as e:
            print(f"Error al inicializar la base de datos: {e}")
            import traceback
            traceback.print_exc()

    def get_config(self):
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True, buffered=True)
            query = "SELECT * FROM configuracion WHERE id = 1"
            cursor.execute(query)
            return cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener configuración: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def update_config(self, data):
        print(f"DEBUG DB update_config params: {data}")
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            # Asegurar que las fechas vacías sean None
            s_start = data.get('season_start')
            s_end = data.get('season_end')
            
            # Si son strings vacíos o None, forzar None para SQL
            if not s_start: s_start = None
            if not s_end: s_end = None
            
            data['season_start'] = s_start
            data['season_end'] = s_end

            # Usamos una consulta más agresiva para asegurar que el ID 1 se actualice o cree
            query = """INSERT INTO configuracion 
                       (id, smtp_server, smtp_port, smtp_user, smtp_password, from_email, business_name, whatsapp_number, logo_path, 
                        season_start, season_end, show_wa_educational_msg, email_service_type, resend_api_key, resend_from_email, 
                        reminder_days_before, whatsapp_service_type, whatsapp_api_key, whatsapp_api_url, whatsapp_acc_id)
                       VALUES (1, %(smtp_server)s, %(smtp_port)s, %(smtp_user)s, %(smtp_password)s, %(from_email)s, %(business_name)s, 
                               %(whatsapp_number)s, %(logo_path)s, %(season_start)s, %(season_end)s, %(show_wa_educational_msg)s, 
                               %(email_service_type)s, %(resend_api_key)s, %(resend_from_email)s, %(reminder_days_before)s,
                               %(whatsapp_service_type)s, %(whatsapp_api_key)s, %(whatsapp_api_url)s, %(whatsapp_acc_id)s)
                       ON DUPLICATE KEY UPDATE
                       smtp_server = VALUES(smtp_server),
                       smtp_port = VALUES(smtp_port),
                       smtp_user = VALUES(smtp_user),
                       smtp_password = VALUES(smtp_password),
                       from_email = VALUES(from_email),
                       business_name = VALUES(business_name),
                       whatsapp_number = VALUES(whatsapp_number),
                       logo_path = VALUES(logo_path),
                       season_start = VALUES(season_start),
                       season_end = VALUES(season_end),
                       show_wa_educational_msg = VALUES(show_wa_educational_msg),
                       email_service_type = VALUES(email_service_type),
                       resend_api_key = VALUES(resend_api_key),
                       resend_from_email = VALUES(resend_from_email),
                       reminder_days_before = VALUES(reminder_days_before),
                       whatsapp_service_type = VALUES(whatsapp_service_type),
                       whatsapp_api_key = VALUES(whatsapp_api_key),
                       whatsapp_api_url = VALUES(whatsapp_api_url),
                       whatsapp_acc_id = VALUES(whatsapp_acc_id)"""
            cursor.execute(query, data)
            affected = cursor.rowcount
            self.connection.commit()
            print(f"DEBUG DB update_config: COMMIT exitoso. Rowcount: {affected}")
            
            # Verificación final
            cursor.execute("SELECT id, season_start, season_end FROM configuracion WHERE id = 1")
            check = cursor.fetchone()
            print(f"DEBUG DB verificacion final: {check}")
            
            return True
        except Exception as e:
            print(f"Error al actualizar configuración: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def set_config_value(self, key, value):
        """Actualiza un valor específico en la tabla de configuración."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = f"UPDATE configuracion SET {key} = %s WHERE id = 1"
            cursor.execute(query, (value,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar config {key}: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def get_client_by_dni(self, dni):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "SELECT id_clientes, documento, nombre, apellido, email, telefono FROM clientes WHERE documento = %s"
            cursor.execute(query, (dni,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener cliente por DNI: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def get_prospect_by_dni(self, dni):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "SELECT id_prospecto, documento, nombre, apellido, email, telefono FROM prospectos WHERE documento = %s"
            cursor.execute(query, (dni,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener prospecto por DNI: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def get_client_by_phone(self, phone):
        """Retorna los datos del cliente si el teléfono ya existe."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "SELECT id_clientes, documento, nombre, apellido, email, telefono FROM clientes WHERE telefono = %s"
            cursor.execute(query, (phone,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener cliente por teléfono: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def get_prospect_by_phone(self, phone):
        """Retorna los datos del prospecto si el teléfono ya existe."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "SELECT id_prospecto, documento, nombre, apellido, email, telefono FROM prospectos WHERE telefono = %s"
            cursor.execute(query, (phone,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener prospecto por teléfono: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def get_contact_by_any(self, email=None, dni=None, phone=None):
        """Busca un contacto (cliente o prospecto) por email, DNI o teléfono de forma inteligente."""
        # Limpiar y validar
        email = email.strip().lower() if email else None
        dni = dni.strip().upper() if dni else None
        phone = phone.strip() if phone else None
        
        # Ignorar placeholders comunes
        placeholders = ["S/D", "SD", "0", "NONE", "—", "", "NO-EMAIL@WA.COM"]
        if email and email.upper() in placeholders: email = None
        if dni and dni.upper() in placeholders: dni = None
        if phone and phone.upper() in placeholders: phone = None

        if not email and not dni and not phone: return None, None
        
        # 1. Buscar en Clientes
        client = None
        if dni: client = self.get_client_by_dni(dni)
        if not client and email: client = self.get_client_by_email(email)
        if not client and phone: client = self.get_client_by_phone(phone)
        
        if client: return client, 'cliente'
        
        # 2. Buscar en Prospectos
        prospect = None
        if dni: prospect = self.get_prospect_by_dni(dni)
        if not prospect and email: prospect = self.get_prospect_by_email(email)
        if not prospect and phone: prospect = self.get_prospect_by_phone(phone)
        
        if prospect: return prospect, 'prospecto'
        
        return None, None

    def get_contact_by_email_or_dni(self, email=None, dni=None):
        """Compatibilidad con código anterior, redirige a get_contact_by_any."""
        return self.get_contact_by_any(email=email, dni=dni)

    def insert_client(self, client_data):
        """client_data = (id, doc, nom, ape, email, tel) o (doc, nom, ape, email, tel)"""
        cursor = None
        try:
            # Verificar duplicados por DNI o Email antes de insertar
            doc = client_data[1] if len(client_data) == 6 else client_data[0]
            email = client_data[4] if len(client_data) == 6 else client_data[3]
            
            existing, tipo = self.get_contact_by_email_or_dni(email, doc)
            if existing and tipo == 'cliente':
                print(f"Error: El cliente con DNI {doc} o Email {email} ya existe.")
                return False

            cursor = self.connection.cursor(buffered=True)
            if len(client_data) == 6:
                query = "INSERT INTO clientes (id_clientes, documento, nombre, apellido, email, telefono) VALUES (%s, %s, %s, %s, %s, %s)"
            else:
                query = "INSERT INTO clientes (documento, nombre, apellido, email, telefono) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, client_data)
            client_id = cursor.lastrowid if len(client_data) != 6 else client_data[0]
            self.connection.commit()
            print(f"Cliente guardado exitosamente con ID: {client_id}")
            return client_id
        except Exception as e:
            print(f"Error al guardar el cliente: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def get_next_available_client_id(self):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = """
                SELECT MIN(t1.id_clientes + 1) AS next_id
                FROM clientes t1
                LEFT JOIN clientes t2 ON t1.id_clientes + 1 = t2.id_clientes
                WHERE t2.id_clientes IS NULL
            """
            cursor.execute(query)
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]
            else:
                return 1
        except Exception as e:
            print(f"Error al obtener el próximo ID disponible: {e}")
            return 1
        finally:
            if cursor: cursor.close()

    def get_all_clients(self):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "SELECT id_clientes, documento, nombre, apellido, email, telefono FROM clientes"
            cursor.execute(query)
            result = cursor.fetchall()
            return result
        except Exception as e:
            print(f"Error al obtener los clientes: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def get_property_by_id(self, property_id):
        """Obtiene los datos de un inmueble por su ID."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "SELECT * FROM inmuebles WHERE id_inmueble = %s"
            cursor.execute(query, (property_id,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener inmueble por ID: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def get_all_properties(self):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = """SELECT id_inmueble, nombre, cantidad_personas, direccion, localidad, 
                              provincia, tipo, valor_dia, COALESCE(imagen, ''),
                              dormitorios, camas, baños, video_url, checkin_time, checkout_time
                       FROM inmuebles"""
            cursor.execute(query)
            result = cursor.fetchall()
            return result
        except Exception as e:
            print(f"Error al obtener los inmuebles: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def get_property_services(self, id_inmueble):
        """Retorna la lista de servicios de un inmueble (icono, nombre)."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "SELECT icono, nombre_servicio FROM servicios_inmuebles WHERE id_inmueble = %s"
            cursor.execute(query, (id_inmueble,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener servicios del inmueble: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def insert_property_services(self, id_inmueble, servicios_con_iconos):
        """Guarda una lista de servicios (icono, nombre) para un inmueble."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            # Primero eliminamos los existentes
            cursor.execute("DELETE FROM servicios_inmuebles WHERE id_inmueble = %s", (id_inmueble,))
            
            if servicios_con_iconos:
                query = "INSERT INTO servicios_inmuebles (id_inmueble, icono, nombre_servicio) VALUES (%s, %s, %s)"
                data = [(id_inmueble, s[0], s[1]) for s in servicios_con_iconos if s[1].strip()]
                cursor.executemany(query, data)
            
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error al guardar servicios del inmueble: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def delete_client(self, client_id):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "DELETE FROM clientes WHERE id_clientes = %s"
            cursor.execute(query, (client_id,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar el cliente: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def get_gallery_images(self, id_inmueble):
        """Retorna las rutas de las imágenes de la galería de un inmueble."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "SELECT id_imagen, ruta_imagen FROM galeria_inmuebles WHERE id_inmueble = %s"
            cursor.execute(query, (id_inmueble,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener galería del inmueble: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def insert_gallery_image(self, id_inmueble, ruta_imagen):
        """Guarda una imagen en la galería de un inmueble."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "INSERT INTO galeria_inmuebles (id_inmueble, ruta_imagen) VALUES (%s, %s)"
            cursor.execute(query, (id_inmueble, ruta_imagen))
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error al guardar imagen en galería: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def delete_gallery_image(self, id_imagen):
        """Elimina una imagen de la galería."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "DELETE FROM galeria_inmuebles WHERE id_imagen = %s"
            cursor.execute(query, (id_imagen,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar imagen de galería: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def update_client(self, client_id, client_data):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = """UPDATE clientes SET 
                       documento = %s, nombre = %s, apellido = %s, 
                       email = %s, telefono = %s 
                       WHERE id_clientes = %s"""
            cursor.execute(query, (*client_data, client_id))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar el cliente: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def delete_property(self, property_id):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "DELETE FROM inmuebles WHERE id_inmueble = %s"
            cursor.execute(query, (property_id,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar el inmueble: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def insert_reservation(self, data):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = """INSERT INTO reservas 
                (id_cliente, id_inmueble, fecha_ingreso, fecha_egreso, valor_dia, noches, costo_total, costo_con_descuento, adelanto, pago_pendiente, provincia)
                VALUES (%(id_cliente)s, %(id_inmueble)s, %(fecha_ingreso)s, %(fecha_egreso)s, %(valor_dia)s, %(noches)s, %(costo_total)s, %(costo_con_descuento)s, %(adelanto)s, %(pago_pendiente)s, %(provincia)s)"""
            cursor.execute(query, data)
            reservation_id = cursor.lastrowid

            adelanto = float(data.get("adelanto", 0))
            if adelanto > 0:
                cursor.execute("INSERT INTO historial_pagos (id_reserva, monto) VALUES (%s, %s)", (reservation_id, adelanto))

            self.connection.commit()
            return reservation_id

        except Exception as e:
            print(f"Error al guardar la reserva: {e}")
            raise
        finally:
            if cursor: cursor.close()

    def update_reservation_wa_status(self, reservation_id, sid, status):
        """Actualiza el SID y estado del último mensaje de WhatsApp enviado."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "UPDATE reservas SET wa_last_sid = %s, wa_last_status = %s WHERE id_reserva = %s"
            cursor.execute(query, (sid, status, reservation_id))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar estado WA: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def get_reservations_with_wa_tracking(self):
        """Obtiene reservas que tienen un SID de WhatsApp para seguimiento."""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True, buffered=True)
            # Buscamos las que tienen SID y que NO están en 'read' ni 'failed'
            query = """SELECT id_reserva, wa_last_sid, wa_last_status 
                       FROM reservas 
                       WHERE wa_last_sid IS NOT NULL 
                       AND (wa_last_status IS NULL OR wa_last_status NOT IN ('read', 'failed'))"""
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener reservas WA: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def get_reservation_client_id(self, reservation_id):
        """Obtiene el ID del cliente de una reserva específica."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            cursor.execute("SELECT id_cliente FROM reservas WHERE id_reserva = %s", (reservation_id,))
            res = cursor.fetchone()
            return res[0] if res else None
        except Exception as e:
            print(f"Error al obtener id_cliente de reserva: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def get_season_financial_summary(self, start_date, end_date):
        """Obtiene resumen de adelantos, ingresos totales y saldos de la temporada."""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True, buffered=True)
            query = """
                SELECT 
                    COALESCE(SUM(costo_con_descuento), 0) as total_esperado,
                    COALESCE(SUM(adelanto), 0) as total_adelantos,
                    COALESCE(SUM(pago_pendiente), 0) as total_pendientes,
                    COALESCE(SUM(CASE WHEN checkin_status = 1 THEN pago_pendiente ELSE 0 END), 0) as total_cobrado_checkin,
                    COALESCE(SUM(CASE WHEN checkin_status = 1 THEN costo_con_descuento ELSE adelanto END), 0) as total_real_recaudado
                FROM reservas 
                WHERE fecha_ingreso BETWEEN %s AND %s
            """
            cursor.execute(query, (start_date, end_date))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error en get_season_financial_summary: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def get_all_reservations(self):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = """SELECT r.id_reserva, CONCAT(c.nombre, ' ', c.apellido), c.telefono,
                              i.nombre, r.fecha_ingreso, r.fecha_egreso, r.noches,
                              r.valor_dia, r.costo_total, r.costo_con_descuento,
                              r.adelanto, r.pago_pendiente, r.provincia, r.id_inmueble,
                              r.fecha_creacion, r.wa_last_status, r.checkin_status
                       FROM reservas r
                       JOIN clientes c ON r.id_cliente = c.id_clientes
                       JOIN inmuebles i ON r.id_inmueble = i.id_inmueble
                       ORDER BY r.id_reserva DESC"""
            cursor.execute(query)
            return cursor.fetchall()

        except Exception as e:
            print(f"Error al obtener las reservas: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def get_client_reservations(self, client_id):
        """Obtiene el historial completo de reservas de un cliente."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = """SELECT r.id_reserva, i.nombre, r.fecha_ingreso, r.fecha_egreso,
                               r.noches, r.costo_con_descuento, r.pago_pendiente, r.fecha_creacion
                        FROM reservas r
                        JOIN inmuebles i ON r.id_inmueble = i.id_inmueble
                        WHERE r.id_cliente = %s
                        ORDER BY r.fecha_ingreso DESC"""
            cursor.execute(query, (client_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener historial de cliente: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def delete_reservation(self, reservation_id):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            cursor.execute("DELETE FROM reservas WHERE id_reserva = %s", (reservation_id,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar la reserva: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def get_reservation_by_id(self, reservation_id):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = """SELECT id_cliente, id_inmueble, fecha_ingreso, fecha_egreso,
                              valor_dia, noches, costo_total, costo_con_descuento,
                              adelanto, pago_pendiente, provincia, fecha_creacion
                       FROM reservas WHERE id_reserva = %s"""
            cursor.execute(query, (reservation_id,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener la reserva: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def update_reservation(self, reservation_id, data):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = """UPDATE reservas SET
                id_cliente = %(id_cliente)s, id_inmueble = %(id_inmueble)s,
                fecha_ingreso = %(fecha_ingreso)s, fecha_egreso = %(fecha_egreso)s,
                valor_dia = %(valor_dia)s, noches = %(noches)s,
                costo_total = %(costo_total)s, costo_con_descuento = %(costo_con_descuento)s,
                adelanto = %(adelanto)s, pago_pendiente = %(pago_pendiente)s,
                provincia = %(provincia)s
                WHERE id_reserva = %(id_reserva)s"""
            data["id_reserva"] = reservation_id
            cursor.execute(query, data)
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar la reserva: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def get_reserved_ranges(self, id_inmueble=None, exclude_id=None):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            conditions = []
            params = []
            if id_inmueble is not None:
                conditions.append("r.id_inmueble = %s")
                params.append(id_inmueble)
            if exclude_id is not None:
                conditions.append("r.id_reserva != %s")
                params.append(exclude_id)
            where = "WHERE " + " AND ".join(conditions) if conditions else ""
            query = f"""SELECT r.fecha_ingreso, r.fecha_egreso, CONCAT(c.nombre, ' ', c.apellido) as cliente 
                       FROM reservas r
                       JOIN clientes c ON r.id_cliente = c.id_clientes
                       {where}"""
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener rangos reservados: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def is_range_available(self, id_inmueble, start_date, end_date, exclude_res_id=None):
        """Verifica si un rango de fechas está libre para un inmueble."""
        ranges = self.get_reserved_ranges(id_inmueble=id_inmueble, exclude_id=exclude_res_id)
        from datetime import date
        # Convertir a objetos date si vienen como string ISO
        if isinstance(start_date, str):
            from datetime import datetime
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            from datetime import datetime
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            
        for r_start, r_end, _ in ranges:
            # r_start/r_end suelen venir como objetos date de MySQL
            if (start_date < r_end) and (end_date > r_start):
                return False
        return True

    def mark_checkin(self, reservation_id):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            # Al hacer checkin, el status cambia a 1. 
            query = "UPDATE reservas SET checkin_status = 1 WHERE id_reserva = %s"
            cursor.execute(query, (reservation_id,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error en mark_checkin: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def mark_checkout(self, reservation_id):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "UPDATE reservas SET checkout_status = 1 WHERE id_reserva = %s"
            cursor.execute(query, (reservation_id,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error en mark_checkout: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def get_upcoming_checkins(self):
        """Obtiene todas las reservas pendientes de Check-In."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = """SELECT r.id_reserva, CONCAT(c.nombre, ' ', c.apellido), c.telefono,
                               i.provincia, i.nombre, r.fecha_ingreso, r.fecha_egreso
                        FROM reservas r
                        JOIN clientes c ON r.id_cliente = c.id_clientes
                        JOIN inmuebles i ON r.id_inmueble = i.id_inmueble
                        WHERE r.checkin_status = 0
                        ORDER BY r.fecha_ingreso ASC"""
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener próximos ingresos: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def get_upcoming_checkouts(self):
        """Obtiene todas las estadías pendientes de Check-Out."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = """SELECT r.id_reserva, CONCAT(c.nombre, ' ', c.apellido), c.telefono,
                               i.provincia, i.nombre, r.fecha_ingreso, r.fecha_egreso,
                               r.checkin_status
                        FROM reservas r
                        JOIN clientes c ON r.id_cliente = c.id_clientes
                        JOIN inmuebles i ON r.id_inmueble = i.id_inmueble
                        WHERE r.checkout_status = 0
                        ORDER BY r.fecha_egreso ASC"""
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener próximos egresos: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def get_client_by_id(self, client_id):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "SELECT id_clientes, nombre, apellido, email, telefono, documento FROM clientes WHERE id_clientes = %s"
            cursor.execute(query, (client_id,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener el cliente: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def get_client_by_email(self, email):
        """Retorna los datos del cliente si el email ya existe."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "SELECT id_clientes, documento, nombre, apellido, email, telefono FROM clientes WHERE email = %s"
            cursor.execute(query, (email,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener cliente por email: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def get_financial_summary(self):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = """SELECT 
                        SUM(costo_con_descuento) as total_potencial, 
                        SUM(adelanto) as total_cobrado, 
                        SUM(pago_pendiente) as total_pendiente 
                       FROM reservas"""
            cursor.execute(query)
            result = cursor.fetchone()
            return [float(x) if x is not None else 0.0 for x in result]
        except Exception as e:
            print(f"Error en get_financial_summary: {e}")
            return [0.0, 0.0, 0.0]
        finally:
            if cursor: cursor.close()

    def search_contacts(self, query):
        """Busca en clientes y prospectos por nombre, apellido, DNI o email."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            # Buscar en Clientes
            sql_c = """SELECT id_clientes, documento, nombre, apellido, email, telefono, 'cliente' as tipo 
                     FROM clientes 
                     WHERE nombre LIKE %s OR apellido LIKE %s OR email LIKE %s OR documento LIKE %s
                     LIMIT 5"""
            # Buscar en Prospectos
            sql_p = """SELECT id_prospecto, documento, nombre, apellido, email, telefono, 'prospecto' as tipo 
                     FROM prospectos 
                     WHERE nombre LIKE %s OR apellido LIKE %s OR email LIKE %s OR documento LIKE %s
                     LIMIT 5"""
            q = f"%{query}%"
            cursor.execute(sql_c, (q, q, q, q))
            res_c = cursor.fetchall()
            cursor.execute(sql_p, (q, q, q, q))
            res_p = cursor.fetchall()
            return res_c + res_p
        except Exception as e:
            print(f"Error al buscar contactos: {e}")
            return []
        finally:
            if cursor: cursor.close()
    def reassign_client_data(self, old_client_id, new_client_id):
        """Transfiere todas las reservas y cotizaciones de un cliente a otro."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            
            # 1. Transferir Reservas
            cursor.execute("UPDATE reservas SET id_cliente = %s WHERE id_cliente = %s", (new_client_id, old_client_id))
            
            # 2. Transferir Cotizaciones
            cursor.execute("UPDATE cotizaciones SET id_cliente = %s WHERE id_cliente = %s", (new_client_id, old_client_id))
            
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error al reasignar datos del cliente: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def get_monthly_financial_breakdown(self, start_date=None, end_date=None):
        """Obtiene el desglose mensual de adelantos, cobros y pendientes en un rango de fechas."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            
            where_clause = ""
            params = []
            if start_date and end_date:
                where_clause = "WHERE fecha_ingreso BETWEEN %s AND %s"
                params = [start_date, end_date]
            
            query = f"""
                SELECT 
                    DATE_FORMAT(fecha_ingreso, '%Y-%m') as mes, 
                    SUM(adelanto) as adelantos,
                    SUM(CASE WHEN checkin_status = 1 THEN pago_pendiente ELSE 0 END) as cobrado_checkin,
                    SUM(CASE WHEN checkin_status = 0 THEN pago_pendiente ELSE 0 END) as pendiente
                FROM reservas 
                {where_clause}
                GROUP BY mes
                ORDER BY mes ASC
            """
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error en get_monthly_financial_breakdown: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def get_revenue_by_month(self):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = """SELECT 
                        DATE_FORMAT(fecha_ingreso, '%Y-%m') as mes,
                        SUM(costo_con_descuento) as total
                       FROM reservas
                       GROUP BY mes
                       ORDER BY mes DESC
                       LIMIT 12"""
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error en get_revenue_by_month: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def get_revenue_by_property(self):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = """SELECT 
                        i.nombre,
                        SUM(r.costo_con_descuento) as total
                       FROM reservas r
                       JOIN inmuebles i ON r.id_inmueble = i.id_inmueble
                       GROUP BY i.nombre
                       ORDER BY total DESC"""
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error en get_revenue_by_property: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def get_pending_payments_list(self):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = """SELECT 
                        r.id_reserva,
                        CONCAT(c.nombre, ' ', c.apellido) as cliente,
                        i.nombre as inmueble,
                        r.fecha_ingreso,
                        r.pago_pendiente
                       FROM reservas r
                       JOIN clientes c ON r.id_cliente = c.id_clientes
                       JOIN inmuebles i ON r.id_inmueble = i.id_inmueble
                       WHERE r.pago_pendiente > 0
                       ORDER BY r.fecha_ingreso ASC"""
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error en get_pending_payments_list: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def add_payment_to_reservation(self, reservation_id, amount):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query_get = "SELECT adelanto, pago_pendiente FROM reservas WHERE id_reserva = %s"
            cursor.execute(query_get, (reservation_id,))
            result = cursor.fetchone()
            
            if not result:
                return False, "No se encontró la reserva."
            
            actual_adelanto = float(result[0])
            actual_pendiente = float(result[1])
            
            if amount > actual_pendiente:
                return False, f"El monto (${amount:,.2f}) supera el saldo pendiente (${actual_pendiente:,.2f})."
            
            nuevo_adelanto = actual_adelanto + amount
            nuevo_pendiente = actual_pendiente - amount
            
            cursor.execute("INSERT INTO historial_pagos (id_reserva, monto) VALUES (%s, %s)", (reservation_id, amount))
            
            query_upd = "UPDATE reservas SET adelanto = %s, pago_pendiente = %s WHERE id_reserva = %s"
            cursor.execute(query_upd, (nuevo_adelanto, nuevo_pendiente, reservation_id))
            
            self.connection.commit()
            return True, "Pago registrado con éxito e ingresado al historial."
            
        except Exception as e:
            print(f"Error en add_payment_to_reservation: {e}")
            return False, f"Error en la base de datos: {str(e)}"
        finally:
            if cursor: cursor.close()

    def get_payment_history(self, reservation_id):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "SELECT fecha_pago, monto FROM historial_pagos WHERE id_reserva = %s ORDER BY fecha_pago DESC"
            cursor.execute(query, (reservation_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error en get_payment_history: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def insert_prospect(self, prospect_data):
        """prospect_data = (doc, nom, ape, email, tel)"""
        cursor = None
        try:
            # Verificar duplicados por DNI, Email o Teléfono antes de insertar
            doc, email, tel = prospect_data[0], prospect_data[3], prospect_data[4]
            existing, tipo = self.get_contact_by_any(email=email, dni=doc, phone=tel)
            
            if existing:
                print(f"Aviso: Ya existe un {tipo} vinculado a estos datos. No se duplicará.")
                return existing[0] # Retornamos el ID existente en lugar de fallar

            cursor = self.connection.cursor(buffered=True)
            query = "INSERT INTO prospectos (documento, nombre, apellido, email, telefono) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, prospect_data)
            prospect_id = cursor.lastrowid
            self.connection.commit()
            print(f"Prospecto guardado exitosamente con ID: {prospect_id}")
            return prospect_id
        except Exception as e:
            print(f"Error al guardar el prospecto: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def get_prospect_by_id(self, prospect_id):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "SELECT id_prospecto, nombre, apellido, email, telefono, documento FROM prospectos WHERE id_prospecto = %s"
            cursor.execute(query, (prospect_id,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener el prospecto: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def get_prospect_by_email(self, email):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "SELECT id_prospecto, documento, nombre, apellido, email, telefono FROM prospectos WHERE email = %s"
            cursor.execute(query, (email,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener prospecto por email: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def convert_prospect_to_client(self, prospect_id, updated_data=None):
        """Mueve un prospecto a la tabla clientes y actualiza sus cotizaciones."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)

            if updated_data:
                # Usar datos frescos del formulario (doc, nom, ape, email, tel)
                doc, nom, ape, email, tel = updated_data
            else:
                # 1. Obtener datos originales del prospecto si no se pasan nuevos
                cursor.execute("SELECT documento, nombre, apellido, email, telefono FROM prospectos WHERE id_prospecto = %s", (prospect_id,))
                prospect = cursor.fetchone()
                if not prospect:
                    return False, "Prospecto no encontrado"
                doc, nom, ape, email, tel = prospect

            # 2. Verificar si ya existe un cliente con ese DNI o Email (excluyendo este prospecto que aún no es cliente)
            existing_client, _ = self.get_contact_by_email_or_dni(email, doc)

            if existing_client and _ == 'cliente':
                # El cliente ya existe -> Solo actualizar las cotizaciones
                new_client_id = existing_client[0]
                print(f"El cliente ya existía (ID: {new_client_id}). Vinculando cotizaciones...")
            else:
                # El cliente no existe -> Insertar nuevo
                cursor.execute("INSERT INTO clientes (documento, nombre, apellido, email, telefono) VALUES (%s, %s, %s, %s, %s)", (doc, nom, ape, email, tel))
                new_client_id = cursor.lastrowid
                print(f"Nuevo cliente creado con ID: {new_client_id}")

            # 3. Actualizar cotizaciones (del prospecto al cliente encontrado o nuevo)
            cursor.execute("UPDATE cotizaciones SET id_cliente = %s, id_prospecto = NULL WHERE id_prospecto = %s", (new_client_id, prospect_id))

            # 4. Eliminar del prospectos
            cursor.execute("DELETE FROM prospectos WHERE id_prospecto = %s", (prospect_id,))

            self.connection.commit()
            return new_client_id, "Conversión exitosa"
        except Exception as e:
            print(f"Error al convertir prospecto a cliente: {e}")
            return False, str(e)
        finally:
            if cursor: cursor.close()
    def insert_quotation(self, data):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = """INSERT INTO cotizaciones 
                (id_cliente, id_prospecto, id_inmueble, fecha_ingreso, fecha_egreso, noches, valor_dia, costo_total, descuento, costo_con_descuento)
                VALUES (%(id_cliente)s, %(id_prospecto)s, %(id_inmueble)s, %(fecha_ingreso)s, %(fecha_egreso)s, %(noches)s, %(valor_dia)s, %(costo_total)s, %(descuento)s, %(costo_con_descuento)s)"""
            cursor.execute(query, data)
            quot_id = cursor.lastrowid
            self.connection.commit()
            return quot_id
        except Exception as e:
            print(f"Error al guardar la cotización: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def get_all_quotations(self):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = """SELECT q.id_cotizacion, 
                              COALESCE(CONCAT(c.nombre, ' ', c.apellido), CONCAT(p.nombre, ' ', p.apellido)) as cliente,
                              i.nombre as inmueble, q.fecha_ingreso, q.fecha_egreso, 
                              q.noches, q.costo_con_descuento, q.fecha_cotizacion,
                              COALESCE(q.id_cliente, q.id_prospecto) as id_contacto, 
                              q.id_inmueble, q.valor_dia, q.costo_total, q.descuento,
                              i.cantidad_personas, q.mkt_enviado,
                              CASE WHEN q.id_cliente IS NOT NULL THEN 'cliente' ELSE 'prospecto' END as tipo_contacto
                       FROM cotizaciones q
                       LEFT JOIN clientes c ON q.id_cliente = c.id_clientes
                       LEFT JOIN prospectos p ON q.id_prospecto = p.id_prospecto
                       JOIN inmuebles i ON q.id_inmueble = i.id_inmueble
                       ORDER BY q.fecha_cotizacion DESC"""
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener cotizaciones: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def get_all_prospects(self):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "SELECT id_prospecto, documento, nombre, apellido, email, telefono, fecha_registro FROM prospectos ORDER BY fecha_registro DESC"
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener prospectos: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def delete_prospect(self, prospect_id):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "DELETE FROM prospectos WHERE id_prospecto = %s"
            cursor.execute(query, (prospect_id,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar prospecto: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def mark_reminder_sent(self, id_reserva):
        """Marca una reserva indicando que ya se envió el recordatorio de check-in."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            cursor.execute("UPDATE reservas SET recordatorio_enviado = 1, fecha_envio_recordatorio = NOW() WHERE id_reserva = %s", (id_reserva,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error al marcar recordatorio_enviado: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def get_todays_notifications(self):
        """Obtiene las notificaciones enviadas el día de hoy."""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True, buffered=True)
            query = """SELECT r.id_reserva, CONCAT(c.nombre, ' ', c.apellido) as cliente,
                              i.nombre as inmueble, r.fecha_envio_recordatorio, r.recordatorio_enviado
                       FROM reservas r
                       JOIN clientes c ON r.id_cliente = c.id_clientes
                       JOIN inmuebles i ON r.id_inmueble = i.id_inmueble
                       WHERE DATE(r.fecha_envio_recordatorio) = CURDATE()
                       ORDER BY r.fecha_envio_recordatorio DESC"""
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener notificaciones de hoy: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def get_pending_reminders(self, days=5):
        """Obtiene reservas que inician en exactamente X días y no tienen recordatorio enviado."""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True, buffered=True)
            query = """SELECT r.*, c.nombre as cliente_nombre, c.apellido as cliente_apellido, c.email as cliente_email, c.telefono as cliente_telefono,
                               i.nombre as inmueble_nombre, i.direccion as inmueble_direccion, i.localidad as inmueble_localidad,
                               i.checkin_time, i.checkout_time, i.dormitorios, i.camas, i.baños
                        FROM reservas r
                       JOIN clientes c ON r.id_cliente = c.id_clientes
                       JOIN inmuebles i ON r.id_inmueble = i.id_inmueble
                       WHERE r.fecha_ingreso = DATE_ADD(CURDATE(), INTERVAL %s DAY)
                       AND r.recordatorio_enviado = 0"""
            cursor.execute(query, (days,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener recordatorios pendientes: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def delete_quotation(self, id_cotizacion):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            cursor.execute("DELETE FROM cotizaciones WHERE id_cotizacion = %s", (id_cotizacion,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar cotización: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def cleanup_old_quotations(self, hours=72):
        """Elimina cotizaciones que superen el tiempo de validez."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "DELETE FROM cotizaciones WHERE fecha_cotizacion < DATE_SUB(NOW(), INTERVAL %s HOUR)"
            cursor.execute(query, (hours,))
            count = cursor.rowcount
            self.connection.commit()
            if count > 0:
                print(f"Limpieza: Se eliminaron {count} cotizaciones vencidas (> {hours}hs).")
            return count
        except Exception as e:
            print(f"Error al limpiar cotizaciones: {e}")
            return 0
        finally:
            if cursor: cursor.close()

    def get_quotations_expiring_soon(self, hours=48):
        """Retorna el conteo de cotizaciones que vencen en las próximas X horas."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            # Validez de 15 días = 360 horas. 
            # Vence pronto si: (fecha_cotizacion + 360h) está entre NOW y (NOW + hours)
            query = """SELECT COUNT(*) FROM cotizaciones 
                       WHERE DATE_ADD(fecha_cotizacion, INTERVAL 360 HOUR) 
                       BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL %s HOUR)"""
            cursor.execute(query, (hours,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            print(f"Error en get_quotations_expiring_soon: {e}")
            return 0
        finally:
            if cursor: cursor.close()

    def get_today_occupancy_stats(self):
        """Retorna el total de inmuebles y cuántos están ocupados hoy."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            # Total inmuebles
            cursor.execute("SELECT COUNT(*) FROM inmuebles")
            total = cursor.fetchone()[0]

            # Ocupados hoy (fecha actual entre ingreso y egreso)
            cursor.execute("""SELECT COUNT(DISTINCT id_inmueble) FROM reservas 
                           WHERE CURDATE() >= fecha_ingreso AND CURDATE() < fecha_egreso""")
            occupied = cursor.fetchone()[0]

            return occupied, total
        except Exception as e:
            print(f"Error en get_today_occupancy_stats: {e}")
            return 0, 0
        finally:
            if cursor: cursor.close()

    def get_weekly_occupancy_forecast(self):
        """Retorna la ocupación prevista para los próximos 7 días."""
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            # Total inmuebles
            cursor.execute("SELECT COUNT(*) FROM inmuebles")
            total_properties = cursor.fetchone()[0]

            forecast = []
            for i in range(7):
                target_date = date.today() + timedelta(days=i)
                query = """SELECT COUNT(DISTINCT id_inmueble) FROM reservas 
                           WHERE %s >= fecha_ingreso AND %s < fecha_egreso"""
                cursor.execute(query, (target_date, target_date))
                count = cursor.fetchone()[0]
                forecast.append((target_date, count, total_properties))
            return forecast
        except Exception as e:
            print(f"Error en get_weekly_occupancy_forecast: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def get_season_stats(self):
        """Calcula estadísticas de ocupación para el rango de la temporada configurada."""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT id, season_start, season_end FROM configuracion WHERE id = 1")
            config = cursor.fetchone()
            
            if not config:
                return None

            if not config['season_start'] or not config['season_end']:
                return None

            start = config['season_start']
            end = config['season_end']
            
            # Conversión de seguridad si vienen como string
            if isinstance(start, str):
                from datetime import datetime
                start = datetime.strptime(start, "%Y-%m-%d").date()
            if isinstance(end, str):
                from datetime import datetime
                end = datetime.strptime(end, "%Y-%m-%d").date()
            
            # Total días-inmueble disponibles en la temporada
            cursor.execute("SELECT COUNT(*) FROM inmuebles")
            total_properties = cursor.fetchone()['COUNT(*)']
            
            total_days = max(1, (end - start).days + 1)
            capacity_days = max(0, total_properties * total_days)
            
            print(f"DEBUG Season: {start} a {end} ({total_days} días, Capacidad: {capacity_days})")

            if capacity_days == 0:
                return {
                    'total_capacity': 0, 'occupied': 0, 'free': 0, 'rented': 0,
                    'start': start, 'end': end
                }

            # Días ocupados por todas las reservas
            cursor.execute("""
                SELECT id_inmueble, fecha_ingreso, fecha_egreso, adelanto
                FROM reservas 
                WHERE (fecha_ingreso <= %s AND fecha_egreso >= %s)
            """, (end, start))
            reservations = cursor.fetchall()
            
            occupied_days = 0
            alquilados_days = 0
            
            for res in reservations:
                # Asegurar que las fechas de reserva también sean objetos date
                r_start = res['fecha_ingreso']
                r_end = res['fecha_egreso']
                if isinstance(r_start, str): r_start = datetime.strptime(r_start, "%Y-%m-%d").date()
                if isinstance(r_end, str): r_end = datetime.strptime(r_end, "%Y-%m-%d").date()

                # Intersección real
                inter_start = max(start, r_start)
                inter_end = min(end, r_end)
                
                if inter_start < inter_end:
                    days = (inter_end - inter_start).days
                    occupied_days += days
                    if float(res['adelanto']) > 0:
                        alquilados_days += days
                elif inter_start == inter_end:
                    # Si coincide exactamente un día (ej: entra y sale el mismo día, aunque raro en reservas)
                    # O si la reserva es de un solo día.
                    occupied_days += 1
                    if float(res['adelanto']) > 0:
                        alquilados_days += 1

            free_days = max(0, capacity_days - occupied_days)
            
            print(f"DEBUG Stats Final: Ocupados={occupied_days}, Alquilados={alquilados_days}, Libres={free_days}")

            return {
                'total_capacity': capacity_days,
                'occupied': occupied_days,
                'free': free_days,
                'rented': alquilados_days,
                'start': start,
                'end': end
            }
        except Exception as e:
            print(f"Error en get_season_stats: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            if cursor: cursor.close()


    # --- MÉTODOS DE LIMPIEZA ---
    def get_cleaning_staff(self, active_only=True):
        if not self.connect(): return []
        try:
            cursor = self.connection.cursor()
            query = "SELECT * FROM personal_limpieza"
            if active_only:
                query += " WHERE estado = 'activo'"
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error en get_cleaning_staff: {e}")
            return []

    def add_cleaning_staff(self, data):
        if not self.connect(): return False
        try:
            cursor = self.connection.cursor()
            query = "INSERT INTO personal_limpieza (nombre, telefono, pin_acceso) VALUES (%s, %s, %s)"
            cursor.execute(query, (data['nombre'], data['telefono'], data['pin']))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error en add_cleaning_staff: {e}")
            return False

    def get_pending_cleanings(self):
        """Busca inmuebles que necesitan limpieza (check-out hoy o sin tarea completada)"""
        if not self.connect(): return []
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT p.*, r.fecha_egreso, r.id_reserva
                FROM inmuebles p
                JOIN reservas r ON p.id_inmueble = r.id_inmueble
                LEFT JOIN tareas_limpieza t ON p.id_inmueble = t.id_inmueble AND r.id_reserva = t.id_reserva
                WHERE r.fecha_egreso <= CURDATE()
                AND (t.id_tarea IS NULL OR t.estado != 'completada')
                GROUP BY p.id_inmueble
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error en get_pending_cleanings: {e}")
            return []

    def assign_cleaning_task(self, data):
        if not self.connect(): return False
        try:
            cursor = self.connection.cursor()
            query = """INSERT INTO tareas_limpieza 
                       (id_inmueble, id_reserva, id_personal, pago_servicio, estado) 
                       VALUES (%s, %s, %s, %s, 'pendiente')"""
            cursor.execute(query, (data['id_inmueble'], data.get('id_reserva'), 
                                   data['id_personal'], data['pago']))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error en assign_cleaning_task: {e}")
            return False

    def update_property_cleaning_fee(self, prop_id, fee):
        if not self.connect(): return False
        try:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE inmuebles SET tarifa_limpieza = %s WHERE id_inmueble = %s", (fee, prop_id))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error en update_property_cleaning_fee: {e}")
            return False

    def update_reservation_checkin_status(self, reservation_id, status):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            cursor.execute("UPDATE reservas SET checkin_status = %s WHERE id_reserva = %s", (status, reservation_id))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar checkin_status: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def update_reservation_checkout_status(self, reservation_id, status):
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            cursor.execute("UPDATE reservas SET checkout_status = %s WHERE id_reserva = %s", (status, reservation_id))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar checkout_status: {e}")
            return False
        finally:
            if cursor: cursor.close()

    def get_reservation_status(self, reservation_id):
        """Obtiene los estados de checkin y checkout de una reserva."""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT checkin_status, checkout_status FROM reservas WHERE id_reserva = %s", (reservation_id,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener estados de reserva: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def get_reservation_details(self, reservation_id):
        """Obtiene detalles completos de una reserva y su cliente."""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True, buffered=True)
            query = """
                SELECT r.*, c.nombre, c.apellido, c.telefono, c.email, i.nombre as inmueble_nombre
                FROM reservas r
                JOIN clientes c ON r.id_cliente = c.id_clientes
                JOIN inmuebles i ON r.id_inmueble = i.id_inmueble
                WHERE r.id_reserva = %s
            """
            cursor.execute(query, (reservation_id,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener detalles de reserva: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def record_checkin_payment(self, reservation_id, amount):
        """Registra el pago final realizado durante el check-in."""
        if amount <= 0: return True
        cursor = None
        try:
            cursor = self.connection.cursor(buffered=True)
            # 1. Registrar en historial de pagos
            cursor.execute("INSERT INTO historial_pagos (id_reserva, monto, nota) VALUES (%s, %s, 'Pago en Check-In')", 
                         (reservation_id, amount))
            # 2. Actualizar adelanto y pendiente en la reserva
            cursor.execute("UPDATE reservas SET adelanto = adelanto + %s, pago_pendiente = pago_pendiente - %s WHERE id_reserva = %s",
                         (amount, amount, reservation_id))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error al registrar pago de check-in: {e}")
            return False
        finally:
            if cursor: cursor.close()
