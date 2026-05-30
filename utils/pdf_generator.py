import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime

def generate_reservation_pdf(reservation_data, output_path):
    """
    Genera un comprobante de reserva profesional en PDF.
    reservation_data: dict con info de la reserva y negocio.
    """
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    style_title = ParagraphStyle('Title', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=20, spaceAfter=20, textColor=colors.HexColor("#2c3e50"))
    style_subtitle = ParagraphStyle('Subtitle', parent=styles['Heading2'], alignment=TA_LEFT, fontSize=14, spaceAfter=10, textColor=colors.HexColor("#3498db"), borderPadding=5)
    style_normal = styles['Normal']
    style_right = ParagraphStyle('Right', parent=styles['Normal'], alignment=TA_RIGHT)
    style_label = ParagraphStyle('Label', parent=styles['Normal'], fontName='Helvetica-Bold')

    # --- ENCABEZADO (Logo y Nombre del Negocio) ---
    business_name = reservation_data.get('business_name', 'SISTEMA DE RESERVAS')
    logo_path = reservation_data.get('logo_path')
    
    header_data = []
    if logo_path and os.path.exists(logo_path):
        try:
            img = Image(logo_path, width=3*cm, height=3*cm, kind='proportional')
            header_data = [[img, Paragraph(f"<br/><br/><font size=18><b>{business_name}</b></font>", style_right)]]
        except:
            header_data = [[Paragraph(f"<font size=18><b>{business_name}</b></font>", style_title)]]
    else:
        header_data = [[Paragraph(f"<font size=18><b>{business_name}</b></font>", style_title)]]

    header_table = Table(header_data, colWidths=[5*cm, 12*cm])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    elements.append(header_table)
    elements.append(Spacer(1, 1*cm))

    # --- TÍTULO DEL DOCUMENTO ---
    elements.append(Paragraph(f"COMPROBANTE DE RESERVA #{str(reservation_data.get('id_reserva')).zfill(5)}", style_title))
    elements.append(Paragraph(f"Fecha de emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}", style_right))
    elements.append(Spacer(1, 0.5*cm))

    # --- SECCIÓN: DATOS DEL HUÉSPED ---
    elements.append(Paragraph("DATOS DEL HUÉSPED", style_subtitle))
    client_info = [
        [Paragraph("Nombre y Apellido:", style_label), reservation_data.get('cliente_nombre', 'N/A')],
        [Paragraph("DNI / Documento:", style_label), reservation_data.get('cliente_doc', 'N/A')],
        [Paragraph("Teléfono:", style_label), reservation_data.get('cliente_tel', 'N/A')],
        [Paragraph("Email:", style_label), reservation_data.get('cliente_email', 'N/A')]
    ]
    t1 = Table(client_info, colWidths=[5*cm, 12*cm])
    t1.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
        ('PADDING', (0,0), (-1,-1), 6)
    ]))
    elements.append(t1)
    elements.append(Spacer(1, 0.8*cm))

    # --- SECCIÓN: DETALLES DE LA ESTADÍA ---
    elements.append(Paragraph("DETALLES DE LA ESTADÍA", style_subtitle))
    stay_info = [
        [Paragraph("Inmueble:", style_label), reservation_data.get('inmueble', 'N/A')],
        [Paragraph("Dirección:", style_label), reservation_data.get('direccion', 'N/A')],
        [Paragraph("Ingreso (Check-in):", style_label), f"{reservation_data.get('fecha_ingreso')} - {reservation_data.get('checkin_time', '14:00')} hs"],
        [Paragraph("Egreso (Check-out):", style_label), f"{reservation_data.get('fecha_egreso')} - {reservation_data.get('checkout_time', '10:00')} hs"],
        [Paragraph("Noches:", style_label), str(reservation_data.get('noches', 0))]
    ]
    t2 = Table(stay_info, colWidths=[5*cm, 12*cm])
    t2.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
        ('PADDING', (0,0), (-1,-1), 6)
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 0.8*cm))

    # --- SECCIÓN: RESUMEN FINANCIERO ---
    elements.append(Paragraph("RESUMEN FINANCIERO", style_subtitle))
    
    def fmt(val):
        try: return f"${float(val):,.0f}".replace(",", ".")
        except: return "$0"

    total = float(reservation_data.get('costo_total', 0))
    desc = float(reservation_data.get('descuento', 0))
    final = float(reservation_data.get('costo_con_descuento', total - desc))
    adelanto = float(reservation_data.get('adelanto', 0))
    pendiente = final - adelanto

    # Estilo especial para el saldo pendiente (Rojo y Grande)
    style_pending = ParagraphStyle('Pending', parent=styles['Normal'], alignment=TA_RIGHT, textColor=colors.red, fontSize=14, fontName='Helvetica-Bold')

    fin_info = [
        [Paragraph("Costo Total Estancia:", style_label), fmt(total)],
        [Paragraph("Descuentos Aplicados:", style_label), f"- {fmt(desc)}"],
        [Paragraph("PRECIO FINAL:", style_label), fmt(final)],
        [Paragraph("Adelanto / Pagos Recibidos:", style_label), fmt(adelanto)],
        [Paragraph("SALDO PENDIENTE A PAGAR:", style_label), Paragraph(fmt(pendiente), style_pending)]
    ]
    
    t3 = Table(fin_info, colWidths=[8*cm, 9*cm])
    t3.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.grey),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,4), (1,4), colors.HexColor("#fceaea"))
    ]))
    elements.append(t3)

    # --- PIE DE PÁGINA / NOTAS ---
    elements.append(Spacer(1, 2*cm))
    elements.append(Paragraph("──────────────────────────────────────────────────", style_title))
    elements.append(Paragraph("Este documento sirve como comprobante de reserva. Por favor, preséntelo al momento del ingreso.", style_normal))
    elements.append(Paragraph(f"Gracias por su confianza. <b>{business_name}</b>", ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER)))

    doc.build(elements)
    return True
