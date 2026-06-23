import io
import numpy as np
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import pandas as pd

def numpy_to_image_buffer(image_data):
    """Convierte numpy array (RGBA) a BytesIO"""
    try:
        pil_img = PILImage.fromarray(image_data.astype(np.uint8), 'RGBA')
        pil_img = pil_img.convert('RGB')  # PDF no soporta RGBA
        buf = io.BytesIO()
        pil_img.save(buf, format='PNG')
        buf.seek(0)
        return buf
    except Exception as e:
        return None

def generar_pdf_partides(partidas):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm, 
                             leftMargin=1.5*cm, rightMargin=1.5*cm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=18, spaceAfter=16)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=11, spaceAfter=4)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=9, spaceAfter=3)
    small_style = ParagraphStyle('Small', parent=styles['Normal'], fontSize=7, spaceAfter=2)

    elements = []
    elements.append(Paragraph("Historial de Partides", title_style))
    elements.append(Spacer(1, 0.2*cm))

    finished = [p for p in partidas if p.phase == "Finished"]

    for i, partida in enumerate(finished):
        ending = partida.ending
        player1, player2 = partida.player1, partida.player2
        t = "(i ho va aconseguir)" if ending == "won" else "(però no ho va aconseguir)"

        elements.append(Paragraph(f"Partida {i+1} — {player1} i {player2} {t}", subtitle_style))
        elements.append(Paragraph(f"<b>Text:</b> {partida.quote}", normal_style))
        elements.append(Spacer(1, 0.15*cm))

        # Imagen
        buf = numpy_to_image_buffer(partida.drawing.image_data)
        if buf:
            img = Image(buf, width=8*cm, height=5*cm, kind='proportional')
            elements.append(img)
        else:
            elements.append(Paragraph("[Error carregant imatge]", normal_style))

        elements.append(Spacer(1, 0.2*cm))

        # Tabla compacta de intentos
        if partida.guessed_quotes is not None and len(partida.guessed_quotes) > 0:
            df = partida.guessed_quotes if isinstance(partida.guessed_quotes, pd.DataFrame) else pd.DataFrame(partida.guessed_quotes)
            elements.append(Paragraph("<b>Intents:</b>", small_style))

            def format_val(v, col_idx):
                if isinstance(v, float):
                    return f"{v:.4f}"
                return str(v)[:80] if col_idx == 0 else str(v)[:20]  # Primera columna más larga

            table_data = [list(df.columns)] + [
                [format_val(v, j) for j, v in enumerate(row)]
                for row in df.values.tolist()
            ]

            # Primera columna más ancha, resto pequeñas
            n_cols = len(df.columns)
            other_col_width = 1.2*cm
            first_col_width = 16*cm - (other_col_width * (n_cols - 1))
            col_widths = [first_col_width] + [other_col_width] * (n_cols - 1)

            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND',      (0, 0), (-1, 0),  colors.HexColor('#4A90D9')),
                ('TEXTCOLOR',       (0, 0), (-1, 0),  colors.white),
                ('FONTNAME',        (0, 0), (-1, 0),  'Helvetica-Bold'),
                ('FONTSIZE',        (0, 0), (-1, -1), 6),
                ('ROWBACKGROUNDS',  (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F4FA')]),
                ('GRID',            (0, 0), (-1, -1), 0.3, colors.grey),
                ('TOPPADDING',      (0, 0), (-1, -1), 1),
                ('BOTTOMPADDING',   (0, 0), (-1, -1), 1),
                ('LEFTPADDING',     (0, 0), (-1, -1), 2),
                ('RIGHTPADDING',    (0, 0), (-1, -1), 2),
            ]))
            elements.append(table)

        elements.append(Spacer(1, 0.4*cm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        elements.append(Spacer(1, 0.4*cm))

    doc.build(elements)
    buffer.seek(0)
    return buffer