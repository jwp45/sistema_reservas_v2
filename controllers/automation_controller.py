from controllers.database import Database
from utils.email_sender import send_checkin_reminder, get_smtp_config
from datetime import date
import urllib.request
import urllib.parse
import json

class AutomationController:
    def __init__(self):
        self.db = Database()

    def process_reminders(self):
        """Procesa y envía recordatorios de check-in pendientes."""
        if not self.db.connect():
            return {"success": False, "message": "No se pudo conectar a la base de datos."}

        config = self.db.get_config()
        if not config:
            return {"success": False, "message": "No se encontró la configuración del sistema."}

        # Determinamos si el sistema tiene capacidad de envío (SMTP o Resend)
        service_type = config.get('email_service_type', 'SMTP')
        api_key = config.get('resend_api_key')
        smtp_user = config.get('smtp_user')

        can_send = (service_type == "Resend" and api_key) or (service_type == "SMTP" and smtp_user)
        
        if not can_send:
            return {"success": False, "message": f"Servicio {service_type} no configurado correctamente."}

        days = config.get('reminder_days_before', 5)
        print(f"DEBUG Automation: Buscando recordatorios para {days} días antes.")
        pending = self.db.get_pending_reminders(days=days)
        print(f"DEBUG Automation: Encontradas {len(pending)} reservas pendientes.")
        
        if not pending:
            return {"success": True, "sent": 0, "message": "No hay recordatorios para procesar hoy."}

        sent_count = 0
        error_count = 0

        for res in pending:
            client_email = res.get('cliente_email')
            client_name = f"{res.get('cliente_nombre')} {res.get('cliente_apellido')}"
            
            if not client_email or "@" not in client_email:
                print(f"DEBUG: Cliente {client_name} no tiene email válido.")
                error_count += 1
                continue

            # Enviar recordatorio usando la función híbrida
            success = send_checkin_reminder(client_email, client_name, res)
            
            if success:
                self.db.mark_reminder_sent(res.get('id_reserva'))
                sent_count += 1
            else:
                error_count += 1

        if self.db.connection:
            self.db.connection.close()

        return {
            "success": True, 
            "sent": sent_count, 
            "errors": error_count,
            "message": f"Se enviaron {sent_count} recordatorios. Errores: {error_count}"
        }

    def update_whatsapp_statuses(self):
        """Consulta Twilio para actualizar los estados de los mensajes (delivered, read)."""
        if not self.db.connect(): return
        
        config = get_smtp_config()
        if config.get('whatsapp_service_type') != "Twilio": return
        
        acc_id = config.get('whatsapp_acc_id')
        api_key = config.get('whatsapp_api_key')
        if not acc_id or not api_key: return

        pending = self.db.get_reservations_with_wa_tracking()
        if not pending: return

        import base64
        auth_str = f"{acc_id}:{api_key}"
        auth_b64 = base64.b64encode(auth_str.encode('ascii')).decode('ascii')
        
        updated = 0
        for res in pending:
            sid = res['wa_last_sid']
            rid = res['id_reserva']
            current_status = res['wa_last_status']
            
            try:
                url = f"https://api.twilio.com/2010-04-01/Accounts/{acc_id}/Messages/{sid}.json"
                req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth_b64}"})
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode())
                    new_status = data.get('status')
                    
                    print(f"DEBUG WA: Reserva {rid} | SID {sid[:8]}... | Estado Twilio: {new_status} (Local era: {current_status})")
                    
                    if new_status and new_status != current_status:
                        self.db.update_reservation_wa_status(rid, sid, new_status)
                        updated += 1
                        print(f"DEBUG WA: ¡Estado actualizado en DB para reserva {rid}!")
            except Exception as e:
                print(f"Error actualizando estado Twilio SID {sid}: {e}")

        return updated
