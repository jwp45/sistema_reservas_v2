import smtplib
import os
import tempfile
import json
import urllib.request
import urllib.error
import re
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from controllers.database import Database
from PIL import Image

def validate_email_format(email):
    """
    Valida la estructura y existencia básica del dominio de un correo electrónico.
    Retorna (bool, mensaje_error)
    """
    if not email:
        return False, "El correo electrónico no puede estar vacío."

    # 1. Validación de Estructura (Regex)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "La estructura del correo electrónico es inválida."
    
    # 2. Validación de Dominio (Existencia DNS básica)
    domain = email.split('@')[1]
    try:
        # Intenta resolver el dominio para verificar su existencia
        socket.gethostbyname(domain)
    except socket.gaierror:
        return False, f"El dominio '@{domain}' no parece ser válido o no tiene registros DNS."
    except Exception:
        # Otros errores de red se ignoran para no bloquear si no hay internet momentáneamente
        pass

    return True, ""

def get_smtp_config():
    db = Database()
    config = None
    if db.connect():
        config = db.get_config()
        if db.connection:
            db.connection.close()
    
    if config:
        return config
    # Fallback a variables de entorno o valores por defecto
    return {
        "smtp_server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
        "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
        "smtp_user": os.environ.get("SMTP_USER", "wolf10dra@gmail.com"),
        "smtp_password": os.environ.get("SMTP_PASSWORD", "xsyy xbcl rkoq esud"),
        "from_email": os.environ.get("FROM_EMAIL", "wolf10dra@gmail.com"),
        "business_name": "Sistema de Reservas",
        "whatsapp_number": "5492236689548"
    }

def optimize_image_for_email(source_path, max_size=(1024, 1024), quality=70):
    """Redimensiona y comprime una imagen para que sea apta para envío por email."""
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        temp_path = temp_file.name
        temp_file.close()

        img = Image.open(source_path)
        # Convertir a RGB si es necesario
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        img.save(temp_path, "JPEG", quality=quality, optimize=True)
        return temp_path
    except Exception as e:
        print(f"Error optimizando imagen {source_path}: {e}")
        return None

def send_reservation_email(client_email, client_name, data):
    config = get_smtp_config()
    smtp_user = config.get("smtp_user")
    smtp_password = config.get("smtp_password")
    smtp_server = config.get("smtp_server")
    smtp_port = config.get("smtp_port")
    from_email = config.get("from_email")

    if not smtp_user or not smtp_password:
        return False

    res_id = data.get('id_reserva', '—')
    res_code = f"R-{str(res_id).zfill(5)}" if str(res_id).isdigit() else res_id

    subject = f"Confirmación de Reserva {res_code} - {data.get('inmueble', '')}"

    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #2e7d32;">¡Reserva Confirmada!</h2>
        <p style="color: #555;">Código de Reserva: <strong>{res_code}</strong></p>
        <p>Hola <strong>{client_name}</strong>,</p>
        <p>Te confirmamos los detalles de tu reserva en <strong>{config.get('business_name')}</strong>:</p>
        <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Fecha Ingreso:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{data.get('fecha_ingreso', '')} (Check-in: {data.get('checkin_time', '14:00')} hs)</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Fecha Egreso:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{data.get('fecha_egreso', '')} (Check-out: {data.get('checkout_time', '10:00')} hs)</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Noches:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{data.get('noches', '')}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Inmueble:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{data.get('inmueble', '')}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Ubicación:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{data.get('ubicacion', 'Consultar')}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Distribución:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{data.get('dormitorios', 0)} Dorm. / {data.get('camas', 0)} Camas / {data.get('baños', 0)} Baños</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Servicios:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{data.get('servicios', 'No especificados')}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Valor por Día:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">${data.get('valor_dia', 0):,.2f}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Costo Total:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">${data.get('costo_total', 0):,.2f}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Costo con Descuento:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">${data.get('costo_con_descuento', 0):,.2f}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Adelanto:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">${data.get('adelanto', 0):,.2f}</td></tr>
            <tr><td style="padding: 8px;"><strong>Pago Pendiente:</strong></td><td style="padding: 8px;">${data.get('pago_pendiente', 0):,.2f}</td></tr>
        </table>
        <br>
        <p style="color: #555;">Gracias por confiar en <strong>{config.get('business_name')}</strong>.</p>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = client_email
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(from_email, client_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False

def send_quotation_email(client_email, client_name, data, image_paths=None):
    """Envía un correo de cotización formal con opción de adjuntar fotos."""
    config = get_smtp_config()
    smtp_user = config.get("smtp_user")
    smtp_password = config.get("smtp_password")
    smtp_server = config.get("smtp_server")
    smtp_port = config.get("smtp_port")
    from_email = config.get("from_email")
    business_name = config.get("business_name")
    whatsapp = config.get("whatsapp_number")

    if not smtp_user or not smtp_password:
        return False

    quot_id = data.get('id', '—')
    quot_code = f"Q-{str(quot_id).zfill(5)}" if str(quot_id).isdigit() else quot_id
    
    subject = f"🏨 Presupuesto de Estadía {quot_code} - {data.get('inmueble', '')}"

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = client_email

    body = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; color: #333; line-height: 1.6;">
        <div style="max-width: 600px; margin: auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
            <div style="background-color: #2c3e50; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">{business_name}</h1>
                <p style="margin: 5px 0; font-size: 14px; opacity: 0.8;">Presupuesto de Estadía - Código: {quot_code}</p>
            </div>
            <div style="padding: 30px;">
                <p>Hola <strong>{client_name}</strong>,</p>
                <p>Es un gusto saludarte. Tal como lo conversamos, te adjunto el presupuesto detallado para tu estadía:</p>
                
                <div style="background-color: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 5px 0;">📅 <strong>Periodo:</strong> Del {data.get('fecha_ingreso', '')} al {data.get('fecha_egreso', '')}</p>
                    <p style="margin: 5px 0;">🕒 <strong>Horarios:</strong> Ingreso {data.get('checkin_time', '14:00')} hs | Egreso {data.get('checkout_time', '10:00')} hs</p>
                    <p style="margin: 5px 0;">🌙 <strong>Noches:</strong> {data.get('noches', '')}</p>
                    <p style="margin: 5px 0;">📍 <strong>Ubicación:</strong> {data.get('ubicacion', 'Consultar')}</p>
                    <p style="margin: 5px 0;">🛏️ <strong>Detalles:</strong> {data.get('dormitorios', 0)} Dorm. | {data.get('camas', 0)} Camas | {data.get('baños', 0)} Baños</p>
                    <h3 style="margin-top: 15px; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">🏠 {data.get('inmueble', '')}</h3>
                    <p style="margin: 5px 0;">✨ <strong>Servicios:</strong> {data.get('servicios', 'No especificados')}</p>
                    {f'<p style="margin: 10px 0; padding: 10px; background-color: #fff3e0; border-radius: 4px; border-left: 4px solid #ff9800;">🎥 <strong>¡Mira el video del inmueble!:</strong> <a href="{data["video_url"]}" style="color: #e67e22; font-weight: bold; text-decoration: none;">Ver en YouTube</a></p>' if data.get('video_url') else ''}
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <p style="font-size: 18px; margin-bottom: 5px; color: #7f8c8d; text-decoration: line-through;">Total: {data.get('costo_total', '$0,00')}</p>
                    <p style="font-size: 28px; font-weight: bold; margin-top: 0; color: #e67e22;">Precio Final: {data.get('final_price', '$0,00')}</p>
                    <p style="font-size: 14px; color: #95a5a6;">(Promedio por noche: {data.get('final_per_night', '$0,00')})</p>
                </div>

                <p style="text-align: center; margin-top: 40px;">
                    <a href="https://wa.me/{whatsapp}?text=Hola!%20Quiero%20confirmar%20la%20reserva%20{quot_code}%20de%20{data.get('inmueble', '').replace(' ', '%20')}%20para%20las%20fechas%20{data.get('fecha_ingreso', '')}%20al%20{data.get('fecha_egreso', '')}" 
                       style="background-color: #27ae60; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">RESERVAR AHORA</a>
                </p>
                
                <p style="font-size: 13px; color: #95a5a6; margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px;">
                    * Este presupuesto tiene validez por 15 días y está sujeto a disponibilidad al momento de confirmar. Por favor, mencione el código <strong>{quot_code}</strong> al contactarnos.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(body, "html"))

    # Adjuntar imágenes si existen
    temp_attachments = []
    if image_paths:
        for i, path in enumerate(image_paths[:10]): # Límite de 10 como pidió el usuario
            if os.path.exists(path):
                optimized_path = optimize_image_for_email(path)
                if optimized_path:
                    try:
                        with open(optimized_path, "rb") as attachment:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            filename = f"inmueble_{i+1}.jpg"
                            part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
                            msg.attach(part)
                            temp_attachments.append(optimized_path)
                    except Exception as e:
                        print(f"Error adjuntando en cotización: {e}")

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(from_email, client_email, msg.as_string())
        
        # Limpiar temporales
        for temp_p in temp_attachments:
            try: os.remove(temp_p)
            except: pass
        return True
    except Exception as e:
        print(f"Error al enviar cotización: {e}")
        for temp_p in temp_attachments:
            try: os.remove(temp_p)
            except: pass
        return False

def send_gallery_email(client_email, property_name, image_paths):
    """Envía imágenes de la galería, dividiendo en varios correos si son muchas."""
    config = get_smtp_config()
    smtp_user = config.get("smtp_user")
    smtp_password = config.get("smtp_password")
    smtp_server = config.get("smtp_server")
    smtp_port = config.get("smtp_port")
    from_email = config.get("from_email")
    business_name = config.get("business_name")

    if not smtp_user or not smtp_password:
        return False

    # Dividir imágenes en lotes de 10 para evitar límites de tamaño/adjuntos
    batch_size = 10
    batches = [image_paths[i:i + batch_size] for i in range(0, len(image_paths), batch_size)]
    total_parts = len(batches)
    
    overall_success = True

    for part_idx, current_batch in enumerate(batches):
        part_num = part_idx + 1
        suffix = f" (Parte {part_num} de {total_parts})" if total_parts > 1 else ""
        subject = f"📸 Galería de Fotos: {property_name}{suffix} - {business_name}"

        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = client_email

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #2c3e50;">{business_name}</h2>
            <p>Hola,</p>
            <p>A continuación te enviamos las fotos del inmueble: <strong>{property_name}</strong>.{suffix}</p>
            <p>Quedamos a tu disposición por cualquier consulta adicional.</p>
            <br>
            <p style="font-size: 12px; color: #7f8c8d;">Atentamente,<br>{business_name}</p>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, "html"))

        temp_attachments = []
        for i, path in enumerate(current_batch):
            if os.path.exists(path):
                optimized_path = optimize_image_for_email(path)
                if optimized_path:
                    try:
                        with open(optimized_path, "rb") as attachment:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            
                            filename = f"foto_{part_idx*batch_size + i + 1}.jpg"
                            part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
                            msg.attach(part)
                            temp_attachments.append(optimized_path)
                    except Exception as e:
                        print(f"Error adjuntando {path}: {e}")

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(from_email, client_email, msg.as_string())
            
            # Limpiar temporales del lote
            for temp_p in temp_attachments:
                try: os.remove(temp_p)
                except: pass
        except Exception as e:
            print(f"Error al enviar parte {part_num}: {e}")
            overall_success = False
            for temp_p in temp_attachments:
                try: os.remove(temp_p)
                except: pass

    return overall_success

def send_marketing_offer_email(client_email, client_name, data, contact_type='prospecto'):
    """Envía un correo de marketing mejorando la oferta original, diferenciando por tipo de cliente."""
    config = get_smtp_config()
    smtp_user = config.get("smtp_user")
    smtp_password = config.get("smtp_password")
    smtp_server = config.get("smtp_server")
    smtp_port = config.get("smtp_port")
    from_email = config.get("from_email")
    business_name = config.get("business_name")
    whatsapp = config.get("whatsapp_number")

    if not smtp_user or not smtp_password:
        return False

    quot_id = data.get('id', '—')
    quot_code = f"Q-{str(quot_id).zfill(5)}" if str(quot_id).isdigit() else quot_id
    
    # Personalización según tipo de contacto
    if contact_type == 'cliente':
        title_text = f"🎁 ¡Qué bueno verte de nuevo, {client_name.split()[0]}! Tenemos un beneficio para ti"
        header_sub = "Valoramos que vuelvas a elegirnos"
        intro_text = f"Es un placer saludarte nuevamente. Como ya eres parte de nuestra comunidad en <strong>{business_name}</strong>, queremos facilitarte el cierre de tu próxima estadía con una atención especial."
    else:
        title_text = f"🎁 ¡Bienvenido! Tenemos un regalo especial para ti"
        header_sub = "Queremos que vivas tu primera experiencia con nosotros"
        intro_text = f"Es un gusto saludarte. Notamos que consultaste por <strong>{data.get('inmueble', '')}</strong> y queremos que te sientas como en casa desde el primer momento."

    subject = f"🎁 {title_text}"

    body = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; color: #333; line-height: 1.6;">
        <div style="max-width: 600px; margin: auto; border: 2px solid #27ae60; border-radius: 8px; overflow: hidden;">
            <div style="background-color: #27ae60; color: white; padding: 25px; text-align: center;">
                <h1 style="margin: 0;">{title_text}</h1>
                <p style="margin: 5px 0; font-size: 16px;">{header_sub}</p>
            </div>
            <div style="padding: 30px;">
                <p>Hola <strong>{client_name}</strong>,</p>
                <p>{intro_text}</p>
                
                <p>Tu presupuesto <strong>{quot_code}</strong> sigue activo, pero para asegurarnos de que no pierdas estas fechas, hemos aplicado un <strong>descuento adicional inmediato</strong>:</p>

                <div style="background-color: #f9f9f9; padding: 20px; border-radius: 5px; margin: 25px 0; text-align: center; border: 1px dashed #27ae60;">
                    <p style="font-size: 16px; margin-bottom: 5px; color: #7f8c8d; text-decoration: line-through;">Precio Cotizado: {data.get('old_price', '$0,00')}</p>
                    <p style="font-size: 30px; font-weight: bold; margin-top: 0; color: #27ae60;">NUEVO PRECIO ESPECIAL: {data.get('new_price', '$0,00')}</p>
                    <p style="font-size: 13px; color: #34495e;">(Válido para el periodo: {data.get('fecha_ingreso', '')} al {data.get('fecha_egreso', '')})</p>
                </div>

                <p style="text-align: center; margin-top: 30px;">
                    <a href="https://wa.me/{whatsapp}?text=Hola!%20Recibí%20la%20oferta%20especial%20{quot_code}%20y%20quiero%20confirmar%20mi%20reserva%20de%20{data.get('inmueble', '').replace(' ', '%20')}" 
                       style="background-color: #2c3e50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">¡ACEPTAR OFERTA Y RESERVAR!</a>
                </p>
                
                <p style="font-size: 13px; color: #95a5a6; margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px; text-align: center;">
                    * Esta oferta es un beneficio único y caducará automáticamente si el inmueble es reservado por otro usuario.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = client_email
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(from_email, client_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False

def send_checkin_reminder_smtp(client_email, client_name, reservation_data):
    """Envía un recordatorio de check-in utilizando SMTP tradicional."""
    config = get_smtp_config()
    smtp_user = config.get("smtp_user")
    smtp_password = config.get("smtp_password")
    smtp_server = config.get("smtp_server")
    smtp_port = config.get("smtp_port")
    from_email = config.get("from_email")
    business_name = config.get("business_name")

    if not smtp_user or not smtp_password:
        return False

    res_id = reservation_data.get('id_reserva', '—')
    res_code = f"R-{str(res_id).zfill(5)}" if str(res_id).isdigit() else res_id

    subject = f"⏳ ¡Faltan pocos días para tu estadía en {reservation_data.get('inmueble_nombre')}!"
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6;">
        <h2 style="color: #2c3e50;">{business_name}</h2>
        <p>Hola <strong>{client_name}</strong>,</p>
        <p>¡Estamos muy emocionados por recibirte! Queremos que todo esté listo para tu llegada el próximo <strong>{reservation_data.get('fecha_ingreso')}</strong>.</p>
        
        <div style="background-color: #f4f7f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p style="margin: 5px 0;"><strong>📍 Inmueble:</strong> {reservation_data.get('inmueble_nombre')}</p>
            <p style="margin: 5px 0;"><strong>📅 Fecha Ingreso:</strong> {reservation_data.get('fecha_ingreso')} (a las {reservation_data.get('checkin_time', '14:00')} hs)</p>
            <p style="margin: 5px 0;"><strong>🕒 Fecha Egreso:</strong> {reservation_data.get('fecha_egreso')} (a las {reservation_data.get('checkout_time', '10:00')} hs)</p>
            <p style="margin: 5px 0;"><strong>Dirección:</strong> {reservation_data.get('inmueble_direccion')}, {reservation_data.get('inmueble_localidad')}</p>
            <p style="margin: 5px 0;"><strong>Saldo Pendiente:</strong> ${float(reservation_data.get('pago_pendiente', 0)):,.2f}</p>
        </div>

        <p>Puedes ver la ubicación exacta en Google Maps aquí:<br>
        <a href="https://www.google.com/maps/search/?api=1&query={reservation_data.get('inmueble_direccion').replace(' ', '+')}+{reservation_data.get('inmueble_localidad').replace(' ', '+')}">Ver Mapa</a></p>

        <p>Cualquier duda, contáctanos por WhatsApp al {config.get('whatsapp_number')}.</p>
        <br>
        <p style="font-size: 12px; color: #7f8c8d;">Atentamente,<br>{business_name}</p>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{business_name} <{from_email}>"
    msg["To"] = client_email
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(from_email, client_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Error al enviar recordatorio SMTP: {e}")
        return False

def send_checkin_reminder(client_email, client_name, reservation_data):
    """Función híbrida que decide si enviar por Resend o SMTP según configuración."""
    config = get_smtp_config()
    service_type = config.get("email_service_type", "SMTP")
    
    if service_type == "Resend" and config.get("resend_api_key"):
        print(f"DEBUG: Enviando recordatorio vía RESEND a {client_email}")
        return send_checkin_reminder_resend(client_email, client_name, reservation_data)
    else:
        print(f"DEBUG: Enviando recordatorio vía SMTP a {client_email}")
        return send_checkin_reminder_smtp(client_email, client_name, reservation_data)

def send_checkin_reminder_resend(client_email, client_name, reservation_data):
    """Envía un recordatorio de check-in utilizando la API de Resend."""
    config = get_smtp_config()
    api_key = config.get("resend_api_key")
    from_email = config.get("resend_from_email") or config.get("from_email")
    business_name = config.get("business_name")

    if not api_key:
        print("Error: No hay API Key de Resend configurada.")
        return False

    res_id = reservation_data.get('id_reserva', '—')
    res_code = f"R-{str(res_id).zfill(5)}" if str(res_id).isdigit() else res_id

    subject = f"⏳ ¡Faltan pocos días para tu estadía en {reservation_data.get('inmueble_nombre')}!"
    
    body = f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: auto; border: 1px solid #eee; border-radius: 10px; padding: 20px;">
        <div style="text-align: center; border-bottom: 2px solid #3498db; padding-bottom: 15px;">
            <h1 style="color: #2c3e50; margin: 0;">{business_name}</h1>
            <p style="color: #3498db; font-weight: bold; margin: 5px 0;">Recordatorio de Próximo Check-in ({res_code})</p>
        </div>
        
        <div style="padding: 20px 0;">
            <p>Hola <strong>{client_name}</strong>,</p>
            <p>¡Estamos muy emocionados por recibirte! Queremos que todo esté listo para tu llegada el próximo <strong>{reservation_data.get('fecha_ingreso')}</strong>.</p>
            
            <div style="background-color: #f9f9f9; border-left: 4px solid #3498db; padding: 15px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #2c3e50;">📍 Detalles de Ubicación</h3>
                <p style="margin: 5px 0;"><strong>Inmueble:</strong> {reservation_data.get('inmueble_nombre')}</p>
                <p style="margin: 5px 0;"><strong>Dirección:</strong> {reservation_data.get('inmueble_direccion')}, {reservation_data.get('inmueble_localidad')}</p>
                <p style="margin: 15px 0 0 0; text-align: center;">
                    <a href="https://www.google.com/maps/search/?api=1&query={reservation_data.get('inmueble_direccion').replace(' ', '+')}+{reservation_data.get('inmueble_localidad').replace(' ', '+')}" 
                       style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">VER EN GOOGLE MAPS</a>
                </p>
            </div>

            <h3 style="color: #2c3e50;">ℹ️ Información Importante</h3>
            <ul style="padding-left: 20px;">
                <li><strong>Check-in:</strong> A partir de las {reservation_data.get('checkin_time', '14:00')} hs.</li>
                <li><strong>Check-out:</strong> Hasta las {reservation_data.get('checkout_time', '10:00')} hs.</li>
                <li><strong>Saldo Pendiente:</strong> ${float(reservation_data.get('pago_pendiente', 0)):,.2f}</li>
            </ul>

            <p>Si tienes alguna duda o necesitas coordinar tu horario de llegada, puedes escribirnos directamente por WhatsApp al <strong>{config.get('whatsapp_number')}</strong>.</p>
        </div>

        <div style="text-align: center; border-top: 1px solid #eee; padding-top: 20px; font-size: 12px; color: #7f8c8d;">
            <p>Este es un mensaje automático enviado por {business_name}.<br>Por favor, no respondas a este correo.</p>
        </div>
    </body>
    </html>
    """

    payload = {
        "from": f"{business_name} <{from_email}>",
        "to": [client_email],
        "subject": subject,
        "html": body
    }

    try:
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            },
            method="POST"
        )
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            print(f"Resend Success Response: {res_body}")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"Error HTTP de Resend ({e.code}): {error_body}")
        return False
    except Exception as e:
        print(f"Error inesperado al enviar por Resend: {e}")
        return False
