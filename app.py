import streamlit as st
import datetime
import io
import tempfile
import numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from fpdf import FPDF

# =============== Utilidades para firmas ===============
def recortar_firma(canvas_result):
    if canvas_result.image_data is None:
        return None, None
    img_array = canvas_result.image_data.astype(np.uint8)
    img = Image.fromarray(img_array)
    gray = img.convert("L")
    coords = np.argwhere(np.array(gray) < 230)
    if coords.size == 0:
        return None, None
    min_y, min_x = coords.min(axis=0)
    max_y, max_x = coords.max(axis=0)
    cropped = img.crop((min_x, min_y, max_x + 1, max_y + 1))
    if cropped.mode == "RGBA":
        cropped = cropped.convert("RGB")
    bio = io.BytesIO()
    cropped.save(bio, format="PNG")
    bio.seek(0)
    # guardamos temporal porque FPDF.image() necesita path
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp.write(bio.read())
    tmp.flush()
    return tmp, cropped.size  # (file, (w,h))

def dibujar_firma_centrada(pdf, tmpfile, img_size, x, y, box_w, box_h):
    if not tmpfile:
        return
    iw, ih = img_size
    # FPDF trabaja en mm; asumimos densidad relativa
    scale = min(box_w / iw, box_h / ih)
    dw, dh = iw * scale, ih * scale
    cx = x + (box_w - dw) / 2
    cy = y + (box_h - dh) / 2
    pdf.image(tmpfile.name, x=cx, y=cy, w=dw, h=dh)

# =============== Componentes UI ===============
def block_streamlit(title, items):
    st.markdown(f"### {title}")
    outs = []
    for it in items:
        a, b = st.columns([5, 3])
        with a:
            st.write(it)
        with b:
            sel = st.radio(" ", ["OK", "NO", "N/A"], horizontal=True, key=f"{title}-{it}")
        outs.append((it, sel))
    return outs

# =============== Dibujo de tabla de checks en PDF ===============
def checks_pdf(pdf, title, items, x_text, y_start, w_text, w_col, row_h, font_size=7.5):
    pdf.set_xy(x_text, y_start - 5)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 4.5, title, ln=1)
    # Cabecera columnas OK/NO/N/A alineadas a la derecha del texto
    pdf.set_xy(x_text, pdf.get_y())
    pdf.set_font("Arial", "B", font_size)
    pdf.cell(w_text, 5, "", 0, 0)
    pdf.cell(w_col, 5, "OK", 1, 0, "C")
    pdf.cell(w_col, 5, "NO", 1, 0, "C")
    pdf.cell(w_col, 5, "N/A", 1, 1, "C")

    pdf.set_font("Arial", "", font_size)
    for item, val in items:
        pdf.set_x(x_text)
        pdf.cell(w_text, row_h, item, 1, 0)
        pdf.cell(w_col, row_h, "X" if val == "OK" else "", 1, 0, "C")
        pdf.cell(w_col, row_h, "X" if val == "NO" else "", 1, 0, "C")
        pdf.cell(w_col, row_h, "X" if val == "N/A" else "", 1, 1, "C")

# =============== APP ===============
def main():
    st.title("Pauta Mantención Máquina de Anestesia — Formato V2 (Horizontal)")

    # Cabecera (mismo orden que la plantilla)
    c1, c2 = st.columns(2)
    with c1:
        marca = st.text_input("MARCA")
        modelo = st.text_input("MODELO")
        sn = st.text_input("S/N")
    with c2:
        n_inv = st.text_input("N/INVENTARIO")
        ubic = st.text_input("UBICACIÓN")
        fecha = st.date_input("FECHA", value=datetime.date.today())

    # Secciones
    sec1 = block_streamlit("1. Chequeo Visual", [
        "1.1. Carcasa Frontal y Trasera",
        "1.2. Estado de Software",
        "1.3. Panel frontal",
        "1.4. Batería de respaldo",
    ])
    sec2 = block_streamlit("2. Sistema de Alta Presión", [
        "2.1. Chequeo de yugo de O2, N2O, Aire",
        "2.2. Revisión o reemplazo de empaquetadura de yugo",
        "2.3. Verificación de entrada de presión",
        "2.4. Revisión y calibración de válvulas de flujometro de O2, N2O, Aire",
    ])
    sec3 = block_streamlit("3. Sistema de baja presión", [
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
    sec4 = block_streamlit("4. Sistema absorbedor", [
        "4.1. Revisión o reemplazo de empaquetadura de canister",
        "4.2. Revisión de válvula APL",
        "4.3. Verificación de manómetro de presión de vía aérea (ajuste a cero)",
        "4.4. Revisión de válvula inhalatoria",
        "4.5. Revisión de válvula exhalatoria",
        "4.6. Chequeo de fugas",
        "4.7. Hermeticidad",
    ])
    sec5 = block_streamlit("5. Ventilador mecánico", [
        "5.1. Porcentaje de oxigeno",
        "5.2. Volumen corriente y volumen minuto",
        "5.3. Presión de vía aérea",
        "5.4. Frecuencia respiratoria",
        "5.5. Modo ventilatorio",
        "5.6. Alarmas",
        "5.7. Calibración de celda de oxígeno a 21% y al 100%",
        "5.8. Calibración de sensores de flujo",
    ])
    sec6 = block_streamlit("6. Seguridad eléctrica", [
        "6.1. Corriente de fuga",
        "6.2. Tierra de protección",
        "6.3. Aislación",
    ])

    # 7. Instrumentos de análisis (dos bloques)
    st.markdown("### 7. Instrumentos de análisis")
    cA, cB = st.columns(2)
    with cA:
        eq1 = st.text_input("EQUIPO (1)")
        ma1 = st.text_input("MARCA (1)")
        mo1 = st.text_input("MODELO (1)")
        se1 = st.text_input("NÚMERO SERIE (1)")
    with cB:
        eq2 = st.text_input("EQUIPO (2)")
        ma2 = st.text_input("MARCA (2)")
        mo2 = st.text_input("MODELO (2)")
        se2 = st.text_input("NÚMERO SERIE (2)")

    st.markdown("### Observaciones")
    obs = st.text_area("Observaciones", height=120)

    op = st.radio("¿Equipo operativo?", ["SI", "NO"], horizontal=True)

    cT1, cT2 = st.columns([2, 1])
    with cT1:
        tecnico = st.text_input("NOMBRE TÉCNICO/INGENIERO")
        empresa = st.text_input("EMPRESA RESPONSABLE")
    with cT2:
        st.markdown("**FIRMA TÉCNICO/INGENIERO**")
        firma_tec = st_canvas(
            fill_color="rgba(255,255,255,0)", stroke_width=2, stroke_color="#000000",
            background_color="#FFFFFF", height=120, width=300, drawing_mode="freedraw",
            key="firma_tec"
        )

    st.markdown("### Observaciones (uso interno)")
    obs_int = st.text_area("Observaciones (uso interno)", height=110)

    st.markdown("### Recepción conforme")
    cR1, cR2 = st.columns(2)
    with cR1:
        st.write("**PERSONAL INGENIERÍA CLÍNICA**")
        firma_ing = st_canvas(
            fill_color="rgba(255,255,255,0)", stroke_width=2, stroke_color="#000000",
            background_color="#FFFFFF", height=110, width=280, drawing_mode="freedraw",
            key="firma_ing"
        )
    with cR2:
        st.write("**PERSONAL CLÍNICO**")
        firma_cli = st_canvas(
            fill_color="rgba(255,255,255,0)", stroke_width=2, stroke_color="#000000",
            background_color="#FFFFFF", height=110, width=280, drawing_mode="freedraw",
            key="firma_cli"
        )

    if st.button("Generar PDF (Horizontal)"):
        # --------- PDF A4 Landscape ----------
        pdf = FPDF('L', 'mm', 'A4')  # Horizontal
        pdf.set_auto_page_break(auto=True, margin=10)
        pdf.add_page()
        pdf.set_margins(10, 8, 10)

        # Encabezado (imitando la pauta)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 6, "PAUTA MANTENIMIENTO PREVENTIVO MAQUINA ANESTESIA (Ver 2)", ln=1, align="C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, "UNIDAD DE INGENIERÍA CLÍNICA", ln=1, align="C")
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, "HOSPITAL REGIONAL DE TALCA", ln=1, align="C")
        pdf.ln(2)

        # Bloque de cabecera en dos columnas (coordenadas pensadas para landscape)
        pdf.set_font("Arial", "", 9)
        col_w = 140
        row_h = 6.5
        pdf.cell(col_w, row_h, f"MARCA  : {marca}", 0, 0)
        pdf.cell(col_w, row_h, f"FECHA : {fecha.strftime('%d/%m/%Y')}", 0, 1)
        pdf.cell(col_w, row_h, f"MODELO : {modelo}", 0, 0)
        pdf.cell(col_w, row_h, f"S/N : {sn}", 0, 1)
        pdf.cell(col_w, row_h, f"N/INVENTARIO : {n_inv}", 0, 0)
        pdf.cell(col_w, row_h, f"UBICACIÓN : {ubic}", 0, 1)
        pdf.ln(2)

        # Coordenadas base para tablas (landscape)
        x_left = 12
        x_right = 165
        w_text = 118
        w_col = 16
        row_h_chk = 6

        # Secciones izquierda
        pdf.set_xy(x_left, pdf.get_y())
        checks_pdf(pdf, "1. Chequeo Visual", sec1, x_left, pdf.get_y(), w_text, w_col, row_h_chk)
        checks_pdf(pdf, "2. Sistema de Alta Presión", sec2, x_left, pdf.get_y(), w_text, w_col, row_h_chk)
        checks_pdf(pdf, "3. Sistema de baja presión", sec3, x_left, pdf.get_y(), w_text, w_col, row_h_chk)
        checks_pdf(pdf, "4. Sistema absorbedor", sec4, x_left, pdf.get_y(), w_text, w_col, row_h_chk)

        # Secciones derecha
        start_y_right = 60  # altura aproximada para que calce visualmente
        pdf.set_xy(x_right, start_y_right)
        checks_pdf(pdf, "5. Ventilador mecánico", sec5, x_right, start_y_right, w_text, w_col, row_h_chk)
        checks_pdf(pdf, "6. Seguridad eléctrica", sec6, x_right, pdf.get_y(), w_text, w_col, row_h_chk)

        # 7. Instrumentos de análisis (dos bloques lado derecho)
        pdf.set_x(x_right)
        pdf.set_font("Arial", "B", 9)
        pdf.cell(0, 5, "7. Instrumentos de análisis", ln=1)
        pdf.set_font("Arial", "", 9)
        pdf.set_x(x_right)
        pdf.cell(0, 5, f"EQUIPO  : {eq1}", ln=1)
        pdf.set_x(x_right)
        pdf.cell(0, 5, f"MARCA   : {ma1}", ln=1)
        pdf.set_x(x_right)
        pdf.cell(0, 5, f"MODELO  : {mo1}", ln=1)
        pdf.set_x(x_right)
        pdf.cell(0, 5, f"NUMERO SERIE : {se1}", ln=1)
        pdf.ln(1)
        pdf.set_x(x_right)
        pdf.cell(0, 5, f"EQUIPO  : {eq2}", ln=1)
        pdf.set_x(x_right)
        pdf.cell(0, 5, f"MARCA   : {ma2}", ln=1)
        pdf.set_x(x_right)
        pdf.cell(0, 5, f"MODELO  : {mo2}", ln=1)
        pdf.set_x(x_right)
        pdf.cell(0, 5, f"NUMERO SERIE : {se2}", ln=1)
        pdf.ln(2)

        # Observaciones (columna derecha inferior)
        pdf.set_x(x_right)
        pdf.set_font("Arial", "B", 9)
        pdf.cell(0, 5, "Observaciones", ln=1)
        pdf.set_font("Arial", "", 9)
        pdf.set_x(x_right)
        pdf.multi_cell(120, 5, obs or "")
        pdf.ln(1)

        # Operativo SI/NO
        pdf.set_x(x_right)
        si = "X" if op == "SI" else ""
        no = "X" if op == "NO" else ""
        pdf.cell(0, 5, f"EQUIPO OPERATIVO   SI [ {si} ]    NO [ {no} ]", ln=1)

        # Técnico + Firma (firma a la derecha dentro de cajita)
        pdf.set_x(x_right)
        pdf.cell(0, 5, f"NOMBRE TÉCNICO/INGENIERO  : {tecnico}", ln=1)
        y_fbox = pdf.get_y()
        pdf.set_x(x_right + 70)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 5, "FIRMA:", ln=1)
        # caja de firma
        box_x = x_right + 70
        box_y = y_fbox + 4
        box_w = 45
        box_h = 18
        pdf.rect(box_x, box_y, box_w, box_h)

        # Empresa responsable
        pdf.set_x(x_right)
        pdf.set_y(box_y + box_h + 4)
        pdf.set_font("Arial", "", 9)
        pdf.cell(0, 5, f"EMPRESA RESPONSABLE : {empresa}", ln=1)

        # Observaciones (uso interno) — a todo el ancho final
        pdf.ln(2)
        pdf.set_x(12)
        pdf.set_font("Arial", "B", 9)
        pdf.cell(0, 5, "Observaciones (uso interno)", ln=1)
        pdf.set_font("Arial", "", 9)
        pdf.multi_cell(270, 5, obs_int or "")

        # Recepción conforme — dos líneas, espacio de firma centrado
        pdf.ln(3)
        y_rc = pdf.get_y()
        pdf.set_x(30)
        pdf.cell(100, 5, "____________________________________", 0, 0, "C")
        pdf.set_x(170)
        pdf.cell(100, 5, "____________________________________", 0, 1, "C")

        pdf.set_x(30)
        pdf.cell(100, 5, "RECEPCIÓN CONFORME", 0, 0, "C")
        pdf.set_x(170)
        pdf.cell(100, 5, "RECEPCIÓN CONFORME", 0, 1, "C")
        pdf.set_x(30)
        pdf.cell(100, 5, "PERSONAL INGENIERÍA CLÍNICA", 0, 0, "C")
        pdf.set_x(170)
        pdf.cell(100, 5, "PERSONAL CLÍNICO", 0, 1, "C")

        # Insertar firmas (centradas sobre las líneas)
        # Firma técnico (en la cajita)
        tmp_tec, size_tec = recortar_firma(firma_tec)
        dibujar_firma_centrada(pdf, tmp_tec, size_tec, box_x, box_y, box_w, box_h)

        # Firmas de recepción
        tmp_ing, size_ing = recortar_firma(firma_ing)
        tmp_cli, size_cli = recortar_firma(firma_cli)
        # cajas virtuales para centrar sobre las líneas
        dibujar_firma_centrada(pdf, tmp_ing, size_ing, 30, y_rc - 6, 100, 20)
        dibujar_firma_centrada(pdf, tmp_cli, size_cli, 170, y_rc - 6, 100, 20)

        # Descargar
        out = io.BytesIO(pdf.output(dest="S").encode("latin1"))
        st.download_button(
            "Descargar PDF (V2 Horizontal)",
            out.getvalue(),
            file_name=f"MP_Anestesia_V2_{sn or 'sin_serie'}.pdf",
            mime="application/pdf",
        )

if __name__ == "__main__":
    main()
