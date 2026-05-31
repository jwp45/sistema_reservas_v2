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

        channel = config.get('channel_reminders', 'Both')
        days = config.get('reminder_days_before', 5)
        
        pending = self.db.get_pending_reminders(days=days)
        if not pending:
            return {"success": True, "sent": 0, "message": "No hay recordatorios para procesar hoy."}

        from utils.whatsapp_sender import send_whatsapp_reminder

        sent_count = 0
        error_count = 0

        for res in pending:
            # Enriquecer datos con servicios
            servs = self.db.get_property_services(res.get('id_inmueble'))
            res['servicios'] = ", ".join([f"{s[0]} {s[1]}" for s in servs]) if servs else "No especificados"

            # El sender espera 'inmueble_nombre', 'inmueble_direccion' y 'inmueble_localidad'
            # pero Database.get_pending_reminders ya los trae así. 
            # Sin embargo, nos aseguramos de que no falten por si acaso
            if 'inmueble' in res and 'inmueble_nombre' not in res:
                res['inmueble_nombre'] = res['inmueble']
            if 'direccion' in res and 'inmueble_direccion' not in res:
                res['inmueble_direccion'] = res['direccion']
            if 'localidad' in res and 'inmueble_localidad' not in res:
                res['inmueble_localidad'] = res['localidad']

            client_email = res.get('cliente_email')
            client_phone = res.get('cliente_telefono')
            client_name = f"{res.get('cliente_nombre')} {res.get('cliente_apellido')}"
            
            success_email = False
            success_wa = False

            # 1. Enviar Email
            if channel in ["Email", "Both"]:
                if client_email and "@" in client_email:
                    success_email = send_checkin_reminder(client_email, client_name, res)
                else:
                    print(f"DEBUG: Cliente {client_name} no tiene email válido para recordatorio.")

            # 2. Enviar WhatsApp
            if channel in ["WhatsApp", "Both"]:
                if client_phone:
                    # En automatización usamos auto_open=False para que no intente abrir navegador si es API
                    # Si es 'Manual', devolverá la URL pero no hará nada en segundo plano (esperado)
                    success_wa = send_whatsapp_reminder(client_phone, client_name, res, auto_open=False)
                    
                    # Si success_wa es un SID (string), lo guardamos para seguimiento
                    if isinstance(success_wa, str) and not success_wa.startswith("http"):
                        self.db.update_reservation_wa_status(res.get('id_reserva'), success_wa, 'sent')
                else:
                    print(f"DEBUG: Cliente {client_name} no tiene teléfono para recordatorio.")

            # Marcamos como enviado si el canal preferido (o al menos uno si es Both) tuvo éxito
            if channel == "Email" and success_email:
                sent_count += 1
                self.db.mark_reminder_sent(res.get('id_reserva'))
            elif channel == "WhatsApp" and success_wa:
                sent_count += 1
                self.db.mark_reminder_sent(res.get('id_reserva'))
            elif channel == "Both" and (success_email or success_wa):
                sent_count += 1
                self.db.mark_reminder_sent(res.get('id_reserva'))
            else:
                error_count += 1

        if self.db.connection:
            self.db.connection.close()

        return {
            "success": True, 
            "sent": sent_count, 
            "errors": error_count,
            "message": f"Se procesaron {sent_count} recordatorios via {channel}."
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
