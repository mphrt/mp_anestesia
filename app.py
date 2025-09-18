import streamlit as st
from fpdf import FPDF
import datetime
import io
import tempfile
from streamlit_drawable_canvas import st_canvas
import numpy as np
from PIL import Image

# ---------- Utilidades ----------
def add_signature_to_pdf(pdf_obj, canvas_result, x, y, box_w=48, max_h=18):
    """Recorta la firma dibujada y la inserta centrada en (x..x+box_w, y..y+max_h)"""
    if canvas_result.image_data is None:
        return
    img_array = canvas_result.image_data.astype(np.uint8)
    img = Image.fromarray(img_array)

    # Binarizado para recorte
    gray_img = img.convert('L')
    threshold = 230
    coords = np.argwhere(np.array(gray_img) < threshold)
    if coords.size == 0:
        return
    min_y, min_x = coords.min(axis=0)
    max_y, max_x = coords.max(axis=0)
    cropped_img = img.crop((min_x, min_y, max_x + 1, max_y + 1))
    if cropped_img.mode == 'RGBA':
        cropped_img = cropped_img.convert('RGB')

    # Guardar temporal
    img_byte_arr = io.BytesIO()
    cropped_img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
        tmp_file.write(img_byte_arr.read())
        tmp_path = tmp_file.name

    # Calcular tamaño para encajar en la caja
    w_mm = box_w
    h_mm = (cropped_img.height / cropped_img.width) * w_mm
    if h_mm > max_h:
        h_mm = max_h
        w_mm = (cropped_img.width / cropped_img.height) * h_mm

    # Centrar en la caja
    cx = x + (box_w - w_mm) / 2
    try:
        pdf_obj.image(tmp_path, x=cx, y=y, w=w_mm, h=h_mm)
    except Exception as e:
        st.error(f"Error al añadir firma: {e}")

def checkbox_block_streamlit(title, items):
    st.markdown(f"### {title}")
    respuestas = []
    for item in items:
        c1, c2 = st.columns([5, 3])
        with c1:
            st.markdown(item)
        with c2:
            sel = st.radio(" ",
                           ["OK", "NO", "N/A"],
                           horizontal=True,
                           key=f"{title}-{item}")
        respuestas.append((item, sel))
    return respuestas

def checkbox_block_pdf(pdf, section_title, items):
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 6, section_title, ln=1)

    # Cabecera tabla
    pdf.set_font("Arial", "B", 8)
    pdf.cell(120, 6, "", border=0)  # col de texto
    pdf.cell(18, 6, "OK", 1, 0, "C")
    pdf.cell(18, 6, "NO", 1, 0, "C")
    pdf.cell(18, 6, "N/A", 1, 1, "C")

    pdf.set_font("Arial", "", 8)
    for item, value in items:
        pdf.cell(120, 6, item, 1, 0)
        pdf.cell(18, 6, "X" if value == "OK" else "", 1, 0, "C")
        pdf.cell(18, 6, "X" if value == "NO" else "", 1, 0, "C")
        pdf.cell(18, 6, "X" if value == "N/A" else "", 1, 1, "C")
    pdf.ln(2)

# ---------- App ----------
def main():
    st.title("Pauta Mantención Máquina de Anestesia — Formato V2 (HRT)")

    # Datos principales (en el orden del PDF)
    c1, c2 = st.columns(2)
    with c1:
        marca = st.text_input("MARCA")
        modelo = st.text_input("MODELO")
        sn = st.text_input("S/N")
    with c2:
        n_inventario = st.text_input("N/INVENTARIO")
        ubicacion = st.text_input("UBICACIÓN")
        fecha = st.date_input("FECHA", value=datetime.date.today())

    # 1..6 bloques
    sec1 = checkbox_block_streamlit("1. Chequeo Visual", [
        "1.1. Carcasa Frontal y Trasera",
        "1.2. Estado de Software",
        "1.3. Panel frontal",
        "1.4. Batería de respaldo",
    ])
    sec2 = checkbox_block_streamlit("2. Sistema de Alta Presión", [
        "2.1. Chequeo de yugo de O2, N2O, Aire",
        "2.2. Revisión o reemplazo de empaquetadura de yugo",
        "2.3. Verificación de entrada de presión",
        "2.4. Revisión y calibración de válvulas de flujometro de O2, N2O, Aire",
    ])
    sec3 = checkbox_block_streamlit("3. Sistema de baja presión", [
        "3.1. Revisión y calibración de válvula de flujómetro de N2O",
        "3.2. Revisión y calibración de válvula de flujometro de O2",
        "3.3. Revisión y calibración de válvula de flujometro de Aire",
        "3.4. Chequeo de fugas",
        "3.5. Verificación de flujos",
        "3.6. Verificación de regulador de 2da (segunda) etapa",
        "3.7. Revisión de sistema de corte N2O/Aire por falta de O2",
        "3.8. Revisión de sistema proporción de O2/N2O",
        "3.9. Revisión de manifold de vaporizadores",
    ])
    sec4 = checkbox_block_streamlit("4. Sistema absorbedor", [
        "4.1. Revisión o reemplazo de empaquetadura de canister",
        "4.2. Revisión de válvula APL",
        "4.3. Verificación de manómetro de presión de vía aérea (ajuste a cero)",
        "4.4. Revisión de válvula inhalatoria",
        "4.5. Revisión de válvula exhalatoria",
        "4.6. Chequeo de fugas",
        "4.7. Hermeticidad",
    ])
    sec5 = checkbox_block_streamlit("5. Ventilador mecánico", [
        "5.1. Porcentaje de oxigeno",
        "5.2. Volumen corriente y volumen minuto",
        "5.3. Presión de vía aérea",
        "5.4. Frecuencia respiratoria",
        "5.5. Modo ventilatorio",
        "5.6. Alarmas",
        "5.7. Calibración de celda de oxígeno a 21% y al 100%",
        "5.8. Calibración de sensores de flujo",
    ])
    sec6 = checkbox_block_streamlit("6. Seguridad eléctrica", [
        "6.1. Corriente de fuga",
        "6.2. Tierra de protección",
        "6.3. Aislación",
    ])

    # 7. Instrumentos de análisis (exactamente 2 bloques como en el PDF)
    st.markdown("### 7. Instrumentos de análisis")
    st.caption("Complete hasta dos equipos tal como en el formato.")
    cA1, cA2 = st.columns(2)
    with cA1:
        eq1_equipo = st.text_input("EQUIPO (1):")
        eq1_marca = st.text_input("MARCA (1):")
        eq1_modelo = st.text_input("MODELO (1):")
        eq1_serie = st.text_input("NÚMERO SERIE (1):")
    with cA2:
        eq2_equipo = st.text_input("EQUIPO (2):")
        eq2_marca = st.text_input("MARCA (2):")
        eq2_modelo = st.text_input("MODELO (2):")
        eq2_serie = st.text_input("NÚMERO SERIE (2):")

    st.markdown("### Observaciones")
    observaciones = st.text_area("Observaciones", height=120)

    st.markdown("### Equipo operativo")
    operativo = st.radio("¿Equipo operativo?", ["SI", "NO"], horizontal=True)

    cT1, cT2 = st.columns([2, 1])
    with cT1:
        tecnico = st.text_input("NOMBRE TÉCNICO/INGENIERO")
        empresa = st.text_input("EMPRESA RESPONSABLE")
    with cT2:
        st.markdown("**FIRMA TÉCNICO/INGENIERO**")
        firma_tecnico = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",
            stroke_width=2,
            stroke_color="#000000",
            background_color="#FFFFFF",
            height=140,
            width=300,
            drawing_mode="freedraw",
            key="firma_tecnico",
        )

    st.markdown("### Observaciones (uso interno)")
    observaciones_interno = st.text_area("Observaciones (uso interno)", height=120)

    # Firmas de recepción conforme (dos líneas separadas)
    st.markdown("### Recepción conforme")
    cR1, cR2 = st.columns(2)
    with cR1:
        st.write("**PERSONAL INGENIERÍA CLÍNICA**")
        firma_ing = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",
            stroke_width=2,
            stroke_color="#000000",
            background_color="#FFFFFF",
            height=120,
            width=300,
            drawing_mode="freedraw",
            key="firma_ing",
        )
    with cR2:
        st.write("**PERSONAL CLÍNICO**")
        firma_clin = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",
            stroke_width=2,
            stroke_color="#000000",
            background_color="#FFFFFF",
            height=120,
            width=300,
            drawing_mode="freedraw",
            key="firma_clin",
        )

    if st.button("Generar PDF (Formato V2)"):
        # PDF en orientación retrato, márgenes similares a pauta adjunta
        pdf = FPDF('P', 'mm', 'A4')
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        pdf.set_margins(15, 12, 15)

        # Encabezado
        try:
            # opcional: coloca tu logo si lo tienes
            pdf.image("logo_hrt_final.jpg", x=15, y=10, w=28)
        except:
            pass

        pdf.set_xy(15, 12)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 6, "PAUTA MANTENIMIENTO PREVENTIVO MAQUINA ANESTESIA (Ver 2)", ln=1, align="C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, "UNIDAD DE INGENIERÍA CLÍNICA", ln=1, align="C")
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, "HOSPITAL REGIONAL DE TALCA", ln=1, align="C")
        pdf.ln(2)

        # Bloque de cabecera (campos en dos columnas)
        pdf.set_font("Arial", "", 9)
        col_w = 95
        row_h = 7

        # Fila 1
        pdf.cell(col_w, row_h, f"MARCA  : {marca}", 0, 0)
        pdf.cell(col_w, row_h, f"FECHA : {fecha.strftime('%d/%m/%Y')}", 0, 1)
        # Fila 2
        pdf.cell(col_w, row_h, f"MODELO : {modelo}", 0, 0)
        pdf.cell(col_w, row_h, f"S/N : {sn}", 0, 1)
        # Fila 3
        pdf.cell(col_w, row_h, f"N/INVENTARIO : {n_inventario}", 0, 0)
        pdf.cell(col_w, row_h, f"UBICACIÓN : {ubicacion}", 0, 1)
        pdf.ln(2)

        # Secciones 1..6
        checkbox_block_pdf(pdf, "1. Chequeo Visual", sec1)
        checkbox_block_pdf(pdf, "2. Sistema de Alta Presión", sec2)
        checkbox_block_pdf(pdf, "3. Sistema de baja presión", sec3)
        checkbox_block_pdf(pdf, "4. Sistema absorbedor", sec4)
        checkbox_block_pdf(pdf, "5. Ventilador mecánico", sec5)
        checkbox_block_pdf(pdf, "6. Seguridad eléctrica", sec6)

        # 7. Instrumentos de análisis (dos bloques)
        pdf.set_font("Arial", "B", 9)
        pdf.cell(0, 6, "7. Instrumentos de análisis", ln=1)
        pdf.set_font("Arial", "", 9)

        # Bloque 1
        pdf.cell(0, 6, f"EQUIPO  : {eq1_equipo}", ln=1)
        pdf.cell(0, 6, f"MARCA   : {eq1_marca}", ln=1)
        pdf.cell(0, 6, f"MODELO  : {eq1_modelo}", ln=1)
        pdf.cell(0, 6, f"NUMERO SERIE : {eq1_serie}", ln=1)
        pdf.ln(1)

        # Bloque 2
        pdf.cell(0, 6, f"EQUIPO  : {eq2_equipo}", ln=1)
        pdf.cell(0, 6, f"MARCA   : {eq2_marca}", ln=1)
        pdf.cell(0, 6, f"MODELO  : {eq2_modelo}", ln=1)
        pdf.cell(0, 6, f"NUMERO SERIE : {eq2_serie}", ln=1)
        pdf.ln(2)

        # Observaciones
        pdf.set_font("Arial", "B", 9)
        pdf.cell(0, 6, "Observaciones", ln=1)
        pdf.set_font("Arial", "", 9)
        pdf.multi_cell(0, 6, observaciones)
        pdf.ln(1)

        # Equipo Operativo (SI/NO)
        pdf.set_font("Arial", "", 9)
        marca_si = "X" if operativo == "SI" else ""
        marca_no = "X" if operativo == "NO" else ""
        pdf.cell(55, 6, "EQUIPO OPERATIVO   SI [ {} ]    NO [ {} ]".format(marca_si, marca_no), ln=1)

        # Técnico + Firma
        pdf.ln(1)
        pdf.set_font("Arial", "", 9)
        pdf.cell(120, 6, f"NOMBRE TÉCNICO/INGENIERO  : {tecnico}", ln=0)
        # Caja de firma técnico a la derecha
        x_sig = pdf.get_x() + 5
        y_sig = pdf.get_y() - 6
        pdf.set_xy(150, y_sig)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(50, 5, "FIRMA:", ln=1)
        # Caja visual para ubicar firma
        pdf.rect(150, y_sig + 5, 48, 18)  # caja
        add_signature_to_pdf(pdf, firma_tecnico, x=150, y=y_sig + 5, box_w=48, max_h=18)

        # Empresa responsable
        pdf.ln(2)
        pdf.set_x(15)
        pdf.set_font("Arial", "", 9)
        pdf.cell(0, 6, f"EMPRESA RESPONSABLE : {empresa}", ln=1)

        # Observaciones uso interno
        pdf.ln(2)
        pdf.set_font("Arial", "B", 9)
        pdf.cell(0, 6, "Observaciones (uso interno)", ln=1)
        pdf.set_font("Arial", "", 9)
        pdf.multi_cell(0, 6, observaciones_interno)
        pdf.ln(2)

        # Recepción conforme — dos líneas con espacio para firma
        pdf.set_font("Arial", "", 9)
        # Ingeniería Clínica
        pdf.ln(2)
        pdf.set_x(15)
        pdf.cell(90, 6, "____________________________________", ln=0, align="C")
        pdf.cell(10, 6, "", ln=0)
        pdf.cell(90, 6, "____________________________________", ln=1, align="C")
        pdf.set_x(15)
        pdf.cell(90, 6, "RECEPCIÓN CONFORME", ln=0, align="C")
        pdf.cell(10, 6, "", ln=0)
        pdf.cell(90, 6, "RECEPCIÓN CONFORME", ln=1, align="C")
        pdf.set_x(15)
        pdf.cell(90, 6, "PERSONAL INGENIERÍA CLÍNICA", ln=0, align="C")
        pdf.cell(10, 6, "", ln=0)
        pdf.cell(90, 6, "PERSONAL CLÍNICO", ln=1, align="C")

        # Insertar firmas dibujadas dentro (encima) de las líneas
        # Coordenadas aproximadas sobre las líneas (ajustadas a A4)
        y_line_top = pdf.get_y() - 18  # un poco encima de la línea
        add_signature_to_pdf(pdf, firma_ing, x=15 + 21, y=y_line_top, box_w=48, max_h=16)
        add_signature_to_pdf(pdf, firma_clin, x=15 + 21 + 100, y=y_line_top, box_w=48, max_h=16)

        # Salida
        out = io.BytesIO(pdf.output(dest="S").encode("latin1"))
        st.download_button(
            "Descargar PDF (V2)",
            out.getvalue(),
            file_name=f"MP_Anestesia_V2_{sn or 'sin_serie'}.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main()
