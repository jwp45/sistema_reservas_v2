import urllib.parse
import sys
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
    message += f"{moon} *Noches:* {data.get('noches', '')}\n"
    message += f"{pin} *Ubicación:* {data.get('ubicacion', '')}\n"
    message += f"{bed} *Distribución:* {data.get('dormitorios', 0)} Dorm. | {data.get('camas', 0)} Camas | {shower} {data.get('baños', 0)} Baños\n\n"
    
    if data.get('servicios') and data.get('servicios') != "No especificados":
        message += f"{sparkles} *Servicios:* {data.get('servicios')}\n\n"
    
    message += f"{money_bag} *Costo Total:* {data.get('costo_total', '')}\n"
    
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
