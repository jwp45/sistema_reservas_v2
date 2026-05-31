import urllib.parse
import sys
import json
import urllib.request
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

def get_whatsapp_url(phone_number, message=""):
    """
    Genera la URL de WhatsApp limpia y codificada.
    """
    phone = "".join(filter(str.isdigit, str(phone_number)))
    if len(phone) == 10:
        phone = "54" + phone
    
    encoded_message = urllib.parse.quote(message)
    return f"https://api.whatsapp.com/send?phone={phone}&text={encoded_message}"

def open_whatsapp_chat(phone_number, message=""):
    """
    Limpia el número y abre el chat de WhatsApp usando el método de QDesktopServices.
    Este método es el mismo que usa el Dashboard y es el más fiable para traer el foco.
    """
    whatsapp_url = get_whatsapp_url(phone_number, message)
    QDesktopServices.openUrl(QUrl(whatsapp_url))
    return True

def format_argentina_phone(phone_number):
    """
    Asegura que los números de Argentina tengan el formato +549...
    """
    clean = "".join(filter(str.isdigit, str(phone_number)))
    
    # Si tiene 10 dígitos (ej: 2236689548), es un número local sin país
    if len(clean) == 10:
        return "549" + clean
    # Si empieza con 54 y tiene 10 dígitos después (total 12), falta el 9
    if clean.startswith("54") and len(clean) == 12:
        return "549" + clean[2:]
    # Si ya tiene el 549 o es otro formato, devolverlo tal cual
    return clean

def send_whatsapp_confirmation(phone_number, client_name, data):
    """
    Envía una confirmación de reserva vía WhatsApp usando el servicio configurado.
    """
    from utils.email_sender import get_smtp_config
    config = get_smtp_config()
    
    service_type = config.get('whatsapp_service_type', 'Manual')
    api_key = config.get('whatsapp_api_key')
    acc_id = config.get('whatsapp_acc_id')
    business_name = config.get('business_name', 'Sistema de Reservas')

    # Emojis para el mensaje
    wave = "\U0001F44B"
    check = "\U00002705"
    calendar = "\U0001F4C5"
    pin = "\U0001F4CD"
    money = "\U0001F4B0"
    bed = "\U0001F6CF"
    shower = "\U0001F6BF"
    sparkles = "\U00002728"
    fire = "\U0001F525"
    dollar = "\U0001F4B5"
    smile = "\U0001F60A"

    message = f"Hola *{client_name}*! {wave}\n\n"
    message += f"{check} *CONFIRMACIÓN DE RESERVA*\n"
    message += f"_{business_name}_\n\n"
    
    message += f"*DATOS DE LA ESTADÍA*\n"
    message += f"🏠 *Inmueble:* {data.get('inmueble')}\n"
    message += f"📅 *Periodo:*\n"
    message += f"_{data.get('fecha_ingreso')} al {data.get('fecha_egreso')}_\n"
    message += f"🌙 *Noches:* {data.get('noches')}\n\n"
    
    message += f"📍 *Ubicación:*\n"
    message += f"{data.get('direccion', 'Consultar')}\n"
    message += f"{data.get('localidad', '')}, {data.get('provincia', '')}\n\n"

    message += f"🕒 *Check-in:* {data.get('checkin_time', '14:00')} hs\n"
    message += f"🕦 *Check-out:* {data.get('checkout_time', '10:00')} hs\n\n"

    message += f"*COMODIDADES Y SERVICIOS*\n"
    message += f"🛏️ {data.get('dormitorios', 0)} Dorm. | {data.get('camas', 0)} Camas | {shower} {data.get('baños', 0)} Baños\n"
    if data.get('servicios') and data.get('servicios') != "No especificados":
        message += f"{sparkles} {data.get('servicios')}\n"
    message += "\n"
    
    message += f"*RESUMEN FINANCIERO*\n"
    message += f"• Valor por día: ${int(float(data.get('valor_dia', 0))):,.0f}\n".replace(',', '.')
    message += f"• Costo Total: ${int(float(data.get('costo_total', 0))):,.0f}\n".replace(',', '.')

    if float(data.get('descuento_monto', 0)) > 0:
        message += f"• Descuento: -${int(float(data.get('descuento_monto', 0))):,.0f}\n".replace(',', '.')
        message += f"• *Precio Final:* ${int(float(data.get('costo_con_descuento', 0))):,.0f}\n".replace(',', '.')

    if float(data.get('adelanto', 0)) > 0:
        message += f"• Adelanto Recibido: ${int(float(data.get('adelanto', 0))):,.0f}\n".replace(',', '.')
    
    message += f"\n💰 *SALDO PENDIENTE: ${int(float(data.get('pago_pendiente', 0))):,.0f}*\n".replace(',', '.')
    message += f"───────────────────\n\n"
    
    message += f"¡Muchas gracias por elegirnos! {smile}"

    if service_type == "Manual":
        return open_whatsapp_chat(phone_number, message)

    def clean_cred(c):
        return str(c).strip() if c else ""

    api_url = clean_cred(config.get('whatsapp_api_url'))
    api_key = clean_cred(api_key)
    acc_id = clean_cred(acc_id)
    
    clean_phone = format_argentina_phone(phone_number)

    try:
        url = ""
        payload_data = {}
        headers = {}
        method = "POST"
        data_encoded = b""

        if service_type == "Twilio":
            # Twilio requiere prefijo '+' y 'whatsapp:'
            to_phone = f"+{clean_phone}"
            from_phone = str(config.get('whatsapp_number', '')).strip()
            from_phone = from_phone.replace('whatsapp:', '').replace('+', '')
            tw_from = f"whatsapp:+{from_phone}"
            tw_to = f"whatsapp:{to_phone}"

            import base64
            auth_str = f"{acc_id}:{api_key}"
            auth_b64 = base64.b64encode(auth_str.encode('ascii')).decode('ascii')
            
            url = f"https://api.twilio.com/2010-04-01/Accounts/{acc_id}/Messages.json"
            payload_data = {"To": tw_to, "From": tw_from, "Body": message}
            data_encoded = urllib.parse.urlencode(payload_data).encode('utf-8')
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
        elif service_type == "Meta Cloud API":
            url = f"https://graph.facebook.com/v18.0/{acc_id}/messages"
            payload = {
                "messaging_product": "whatsapp",
                "to": clean_phone,
                "type": "text",
                "text": {"body": message}
            }
            data_encoded = json.dumps(payload).encode()
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            
        elif service_type == "Wati":
            url = f"{api_url}/api/v1/sendSessionMessage/{clean_phone}?messageText={urllib.parse.quote(message)}"
            headers = {"Authorization": f"Bearer {api_key}"}
            data_encoded = b"" 
            
        elif service_type == "UltraMsg":
            url = f"{api_url}/messages/chat"
            payload = {"token": api_key, "to": clean_phone, "body": message}
            data_encoded = urllib.parse.urlencode(payload).encode()
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
        else:
            return open_whatsapp_chat(phone_number, message)

        # Ejecutar Petición
        req = urllib.request.Request(url, data=data_encoded, headers=headers, method=method)
        with urllib.request.urlopen(req) as response:
            res_raw = response.read().decode()
            res_json = json.loads(res_raw)
            print(f"DEBUG: WhatsApp API Success: {res_raw}")
            
            # Extraer SID según el proveedor
            sid = None
            if service_type == "Twilio":
                sid = res_json.get("sid")
            elif service_type == "Meta Cloud API":
                messages = res_json.get("messages", [])
                if messages: sid = messages[0].get("id")
            elif service_type == "UltraMsg":
                sid = res_json.get("id")
            
            return sid if sid else True

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"Error HTTP de WhatsApp ({service_type}) - Código {e.code}: {error_body}")
        return open_whatsapp_chat(phone_number, message)
    except Exception as e:
        print(f"Error inesperado en envío WhatsApp ({service_type}): {e}")
        return open_whatsapp_chat(phone_number, message)

def send_whatsapp_quotation(phone_number, client_name, data, auto_open=True):
    """
    Genera un enlace de WhatsApp con el mensaje de cotización.
    """
    # Limpiar el número de teléfono (solo números)
    phone = "".join(filter(str.isdigit, str(phone_number)))
    
    # Si no tiene código de país, asumir Argentina (54)
    if len(phone) == 10:
        phone = "54" + phone
    
    # Usar códigos Unicode para emojis para mayor compatibilidad
    wave = "\U0001F44B"
    calendar = "\U0001F4C5"
    moon = "\U0001F319"
    pin = "\U0001F4CD"
    bed = "\U0001F6CF"
    shower = "\U0001F6BF"
    sparkles = "\U00002728"
    money_bag = "\U0001F4B0"
    fire = "\U0001F525"
    dollar = "\U0001F4B5"
    smile = "\U0001F60A"

    message = f"Hola *{client_name}*! {wave}\n\n"
    message += f"Te envío el presupuesto solicitado para tu estadía en *{data.get('inmueble', '')}*:\n\n"
    message += f"{calendar} *Periodo:* Del {data.get('fecha_ingreso', '')} al {data.get('fecha_egreso', '')}\n"
    message += f"🕒 *Horarios:* In {data.get('checkin_time', '14:00')}hs | Out {data.get('checkout_time', '10:00')}hs\n"
    message += f"{moon} *Noches:* {data.get('noches', '')}\n"
    message += f"{pin} *Ubicación:* {data.get('ubicacion', '')}\n"
    message += f"{bed} *Distribución:* {data.get('dormitorios', 0)} Dorm. | {data.get('camas', 0)} Camas | {shower} {data.get('baños', 0)} Baños\n\n"
    
    if data.get('servicios') and data.get('servicios') != "No especificados":
        message += f"{sparkles} *Servicios:* {data.get('servicios')}\n"
    
    if data.get('video_url'):
        message += f"\U0001F3A5 *Video:* {data.get('video_url')}\n"
    
    message += f"\n{money_bag} *Costo Total:* {data.get('costo_total', '')}\n"
    
    if data.get('final_price') != data.get('costo_total'):
        message += f"{fire} *PRECIO FINAL CON DESCUENTO:* {data.get('final_price', '')}\n"
    
    message += f"{dollar} *Promedio por noche:* {data.get('final_per_night', '')}\n\n"
    message += f"Quedo a tu disposición por cualquier consulta. Saludos! {smile}"

    whatsapp_url = get_whatsapp_url(phone, message)
    
    if not auto_open:
        return whatsapp_url

    # Usar QDesktopServices (igual que el Dashboard)
    QDesktopServices.openUrl(QUrl(whatsapp_url))
    return True

def send_whatsapp_reminder(phone_number, client_name, reservation_data, auto_open=True):
    """
    Envía un recordatorio de check-in vía WhatsApp.
    """
    from utils.email_sender import get_smtp_config
    config = get_smtp_config()
    business_name = config.get('business_name', 'Sistema de Reservas')
    
    # Emojis
    wave = "\U0001F44B"
    smile = "\U0001F60A"
    pin = "\U0001F4CD"
    calendar = "\U0001F4C5"
    money = "\U0001F4B0"
    
    message = f"¡Hola *{client_name}*! {wave}\n\n"
    message += f"¡Estamos muy emocionados por recibirte! Queremos recordarte que todo está listo para tu llegada el próximo *{reservation_data.get('fecha_ingreso')}*.\n\n"
    
    message += f"*DETALLES DE TU LLEGADA:*\n"
    message += f"📍 *Inmueble:* {reservation_data.get('inmueble_nombre')}\n"
    message += f"{calendar} *Fecha Ingreso:* {reservation_data.get('fecha_ingreso')} (a las {reservation_data.get('checkin_time', '14:00')} hs)\n"
    message += f"🕒 *Fecha Egreso:* {reservation_data.get('fecha_egreso')} (a las {reservation_data.get('checkout_time', '10:00')} hs)\n\n"
    
    message += f"🏠 *Dirección:* {reservation_data.get('inmueble_direccion')}, {reservation_data.get('inmueble_localidad')}\n"
    message += f"📍 *Ver en Google Maps:* https://www.google.com/maps/search/?api=1&query={reservation_data.get('inmueble_direccion').replace(' ', '+')}+{reservation_data.get('inmueble_localidad').replace(' ', '+')}\n\n"
    
    if float(reservation_data.get('pago_pendiente', 0)) > 0:
        message += f"{money} *Saldo Pendiente:* ${float(reservation_data.get('pago_pendiente', 0)):,.2f}\n\n"
    
    message += f"¡Nos vemos pronto! {smile}\n"
    message += f"_{business_name}_"

    service_type = config.get('whatsapp_service_type', 'Manual')
    if service_type == "Manual":
        if not auto_open: return False # En automatización no podemos enviar manual
        return open_whatsapp_chat(phone_number, message)
    
    # Si es API, usamos la misma lógica que confirmation (podríamos refactorizar pero por ahora es más seguro así)
    api_key = config.get('whatsapp_api_key')
    acc_id = config.get('whatsapp_acc_id')
    api_url = config.get('whatsapp_api_url')
    clean_phone = format_argentina_phone(phone_number)
    
    try:
        url = ""
        payload = {}
        headers = {}
        data_encoded = b""

        if service_type == "Twilio":
            tw_from = f"whatsapp:+{str(config.get('whatsapp_number', '')).strip().replace('+', '')}"
            tw_to = f"whatsapp:+{clean_phone}"
            import base64
            auth_b64 = base64.b64encode(f"{acc_id}:{api_key}".encode()).decode()
            url = f"https://api.twilio.com/2010-04-01/Accounts/{acc_id}/Messages.json"
            payload = {"To": tw_to, "From": tw_from, "Body": message}
            data_encoded = urllib.parse.urlencode(payload).encode('utf-8')
            headers = {"Authorization": f"Basic {auth_b64}", "Content-Type": "application/x-www-form-urlencoded"}
        elif service_type == "Meta Cloud API":
            url = f"https://graph.facebook.com/v18.0/{acc_id}/messages"
            payload = {"messaging_product": "whatsapp", "to": clean_phone, "type": "text", "text": {"body": message}}
            data_encoded = json.dumps(payload).encode()
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        # ... otros servicios ...
        else:
            if not auto_open: return False
            return open_whatsapp_chat(phone_number, message)

        req = urllib.request.Request(url, data=data_encoded, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            res_raw = response.read().decode()
            res_json = json.loads(res_raw)
            
            # Extraer SID según el proveedor
            sid = None
            if service_type == "Twilio":
                sid = res_json.get("sid")
            elif service_type == "Meta Cloud API":
                messages = res_json.get("messages", [])
                if messages: sid = messages[0].get("id")
            
            return sid if sid else True
    except Exception as e:
        print(f"Error en envío recordatorio WhatsApp ({service_type}): {e}")
        if not auto_open: return False
        return open_whatsapp_chat(phone_number, message)
