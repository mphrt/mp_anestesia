import streamlit as st
import datetime
import io
import tempfile
import numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# --- NUEVO: libs para “estampar” sobre la plantilla PDF ---
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import A4  # (595.27, 841.89) puntos
from reportlab.lib.units import mm
from pypdf import PdfReader, PdfWriter, PageObject

# ===================== util: firmas =====================
def _recortar_firma(canvas_result):
    if canvas_result.image_data is None:
        return None
    img_array = canvas_result.image_data.astype(np.uint8)
    img = Image.fromarray(img_array)
    gray = img.convert("L")
    coords = np.argwhere(np.array(gray) < 230)
    if coords.size == 0:
        return None
    min_y, min_x = coords.min(axis=0)
    max_y, max_x = coords.max(axis=0)
    cropped = img.crop((min_x, min_y, max_x + 1, max_y + 1))
    if cropped.mode == "RGBA":
        cropped = cropped.convert("RGB")
    bio = io.BytesIO()
    cropped.save(bio, format="PNG")
    bio.seek(0)
    return bio

def _draw_image_centered(c, png_bytesio, cx, cy, box_w, box_h):
    # Dibuja una imagen centrada en la caja (cx, cy, box_w, box_h)
    if not png_bytesio:
        return
    from reportlab.lib.utils import ImageReader
    img = Image.open(png_bytesio)
    iw, ih = img.size
    # Escalar manteniendo proporción
    scale = min(box_w / iw, box_h / ih)
    dw, dh = iw * scale, ih * scale
    x = cx + (box_w - dw) / 2
    y = cy + (box_h - dh) / 2
    c.drawImage(ImageReader(png_bytesio), x, y, width=dw, height=dh, mask='auto')

# ===================== UI =====================
st.title("Pauta Mantención Máquina de Anestesia — Plantilla PDF V2")

# Cabecera
c1, c2 = st.columns(2)
with c1:
    marca = st.text_input("MARCA")
    modelo = st.text_input("MODELO")
    sn = st.text_input("S/N")
with c2:
    n_inv = st.text_input("N/INVENTARIO")
    ubic = st.text_input("UBICACIÓN")
    fecha = st.date_input("FECHA", value=datetime.date.today())

def block(title, items):
    st.markdown(f"### {title}")
    out = []
    for it in items:
        a, b = st.columns([5, 3])
        with a: st.write(it)
        with b:
            sel = st.radio(" ", ["OK", "NO", "N/A"], horizontal=True, key=f"{title}-{it}")
        out.append(sel)
    return out

items1 = [
 "1.1. Carcasa Frontal y Trasera", "1.2. Estado de Software",
 "1.3. Panel frontal", "1.4. Batería de respaldo"
]
res1 = block("1. Chequeo Visual", items1)

items2 = [
 "2.1. Chequeo de yugo de O2, N2O, Aire",
 "2.2. Revisión o reemplazo de empaquetadura de yugo",
 "2.3. Verificación de entrada de presión",
 "2.4. Revisión y calibración de válvulas de flujometro de O2, N2O, Aire",
]
res2 = block("2. Sistema de Alta Presión", items2)

items3 = [
 "3.1. Revisión y calibración de válvula de flujómetro de N2O",
 "3.2. Revisión y calibración de válvula de flujometro de O2",
 "3.3. Revisión y calibración de válvula de flujometro de Aire",
 "3.4. Chequeo de fugas", "3.5. Verificación de flujos",
 "3.6. Verificación de regulador de 2da (segunda) etapa",
 "3.7. Revisión de sistema de corte N2O/Aire por falta de O2",
 "3.8. Revisión de sistema proporción de O2/N2O",
 "3.9. Revisión de manifold de vaporizadores",
]
res3 = block("3. Sistema de baja presión", items3)

items4 = [
 "4.1. Revisión o reemplazo de empaquetadura de canister",
 "4.2. Revisión de válvula APL",
 "4.3. Verificación de manómetro de presión de vía aérea (ajuste a cero)",
 "4.4. Revisión de válvula inhalatoria",
 "4.5. Revisión de válvula exhalatoria",
 "4.6. Chequeo de fugas", "4.7. Hermeticidad",
]
res4 = block("4. Sistema absorbedor", items4)

items5 = [
 "5.1. Porcentaje de oxigeno", "5.2. Volumen corriente y volumen minuto",
 "5.3. Presión de vía aérea", "5.4. Frecuencia respiratoria",
 "5.5. Modo ventilatorio", "5.6. Alarmas",
 "5.7. Calibración de celda de oxígeno a 21% y al 100%",
 "5.8. Calibración de sensores de flujo",
]
res5 = block("5. Ventilador mecánico", items5)

items6 = ["6.1. Corriente de fuga", "6.2. Tierra de protección", "6.3. Aislación"]
res6 = block("6. Seguridad eléctrica", items6)

st.markdown("### 7. Instrumentos de análisis")
cA, cB = st.columns(2)
with cA:
    eq1, ma1, mo1, se1 = (
        st.text_input("EQUIPO (1)"), st.text_input("MARCA (1)"),
        st.text_input("MODELO (1)"), st.text_input("NÚMERO SERIE (1)")
    )
with cB:
    eq2, ma2, mo2, se2 = (
        st.text_input("EQUIPO (2)"), st.text_input("MARCA (2)"),
        st.text_input("MODELO (2)"), st.text_input("NÚMERO SERIE (2)")
    )

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
obs_int = st.text_area("Observaciones (uso interno)", height=120)

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

# ===================== COLOCACIÓN EN LA PLANTILLA =====================
# Coordenadas en puntos (PDF A4). Origen (0,0) esquina inferior izquierda.
# Estas posiciones fueron tomadas para calzar con la pauta V2. Ajusta milimétricamente si lo necesitas.
# Tip: 1 mm = 2.83465 pt

PT = 1.0  # factor base
# Cabecera (dos columnas)
Y_TOP = 770*PT
X_L = 40*PT
X_R = 320*PT
ROW = 16*PT

# Tabla de checkboxes: definimos anchos fijos y columnas OK/NO/NA
X_TEXT = 40*PT
W_TEXT = 360*PT
W_COL = 40*PT
X_OK = X_TEXT + W_TEXT
X_NO = X_OK + W_COL
X_NA = X_NO + W_COL

# Líneas base por bloque
Y1 = 690*PT  # inicio sec1
Y2 = 615*PT  # sec2
Y3 = 530*PT  # sec3
Y4 = 420*PT  # sec4
Y5a = 340*PT # sec5 (parte parámetros)
Y5b = 290*PT # sec5 (parte acciones)
Y6 = 245*PT  # sec6

ROW_CHECK = 16*PT

# Instrumentos análisis
Y7 = 200*PT
X_IA_L = 60*PT
X_IA_R = 330*PT
ROW_IA = 18*PT

# Observaciones generales
Y_OBS = 150*PT
X_OBS = 40*PT
W_OBS = 515*PT
LINE_OBS = 12*PT

# Operativo + Técnico + Firma
Y_OP = 112*PT
X_OP = 40*PT
X_TEC = 40*PT
Y_TEC = 95*PT
X_FT = 420*PT
Y_FT = 90*PT
W_FT = 120*PT
H_FT = 28*PT

# Empresa responsable
Y_EMP = 75*PT
X_EMP = 40*PT

# Observaciones internas
Y_OBS_INT = 48*PT
X_OBS_INT = 40*PT
W_OBS_INT = 515*PT
LINE_OBS_INT = 12*PT

# Recepción conforme (dos líneas/firma)
Y_RC = 18*PT
X_RC_L = 80*PT
X_RC_R = 350*PT
W_RC = 140*PT
H_RC = 24*PT

def _draw_checks_row(c, y, sel):
    c.setFont("Helvetica", 9)
    # pinta una "X" en la columna elegida
    if sel == "OK":
        c.drawCentredString(X_OK + W_COL/2, y, "X")
    elif sel == "NO":
        c.drawCentredString(X_NO + W_COL/2, y, "X")
    elif sel == "N/A":
        c.drawCentredString(X_NA + W_COL/2, y, "X")

def _multi_text(c, text, x, y, max_width, line_h):
    c.setFont("Helvetica", 9)
    from textwrap import wrap
    lines = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append("")
            continue
        # aproximación: 1 char ≈ 4.7 pt de ancho (Helvetica 9)
        max_chars = int(max_width / 4.7)
        lines += wrap(para, width=max_chars)
    y0 = y
    for ln in lines:
        c.drawString(x, y0, ln)
        y0 -= line_h

def _build_overlay_pdf_bytes():
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)

    # Cabecera
    c.setFont("Helvetica", 10)
    c.drawString(X_L, Y_TOP, f"MARCA  : {marca}")
    c.drawString(X_R, Y_TOP, f"FECHA : {fecha.strftime('%d/%m/%Y')}")
    c.drawString(X_L, Y_TOP-ROW, f"MODELO : {modelo}")
    c.drawString(X_R, Y_TOP-ROW, f"S/N : {sn}")
    c.drawString(X_L, Y_TOP-2*ROW, f"N/INVENTARIO : {n_inv}")
    c.drawString(X_R, Y_TOP-2*ROW, f"UBICACIÓN : {ubic}")

    # Sec1
    y = Y1
    for sel in res1:
        _draw_checks_row(c, y, sel); y -= ROW_CHECK

    # Sec2
    y = Y2
    for sel in res2:
        _draw_checks_row(c, y, sel); y -= ROW_CHECK

    # Sec3 (9 ítems)
    y = Y3
    for sel in res3:
        _draw_checks_row(c, y, sel); y -= ROW_CHECK

    # Sec4 (7 ítems)
    y = Y4
    for sel in res4:
        _draw_checks_row(c, y, sel); y -= ROW_CHECK

    # Sec5 parte1 (6 ítems: 5.1..5.6)
    y = Y5a
    for sel in res5[:6]:
        _draw_checks_row(c, y, sel); y -= ROW_CHECK

    # Sec5 parte2 (5.7..5.8)
    y = Y5b
    for sel in res5[6:]:
        _draw_checks_row(c, y, sel); y -= ROW_CHECK

    # Sec6 (3 ítems)
    y = Y6
    for sel in res6:
        _draw_checks_row(c, y, sel); y -= ROW_CHECK

    # 7. Instrumentos de análisis (2 bloques)
    c.setFont("Helvetica", 10)
    c.drawString(X_IA_L, Y7, f"EQUIPO  : {eq1}")
    c.drawString(X_IA_L, Y7-ROW_IA, f"MARCA   : {ma1}")
    c.drawString(X_IA_L, Y7-2*ROW_IA, f"MODELO  : {mo1}")
    c.drawString(X_IA_L, Y7-3*ROW_IA, f"NUMERO SERIE : {se1}")

    c.drawString(X_IA_R, Y7, f"EQUIPO  : {eq2}")
    c.drawString(X_IA_R, Y7-ROW_IA, f"MARCA   : {ma2}")
    c.drawString(X_IA_R, Y7-2*ROW_IA, f"MODELO  : {mo2}")
    c.drawString(X_IA_R, Y7-3*ROW_IA, f"NUMERO SERIE : {se2}")

    # Observaciones
    _multi_text(c, obs or "", X_OBS, Y_OBS, W_OBS, LINE_OBS)

    # Operativo
    c.setFont("Helvetica", 10)
    si = "X" if op == "SI" else ""
    no = "X" if op == "NO" else ""
    c.drawString(X_OP, Y_OP, f"EQUIPO OPERATIVO   SI [ {si} ]    NO [ {no} ]")

    # Técnico + Firma (firma centrada dentro de caja a la derecha)
    c.drawString(X_TEC, Y_TEC, f"NOMBRE TÉCNICO/INGENIERO  : {tecnico}")
    firma_tec_png = _recortar_firma(firma_tec)
    _draw_image_centered(c, firma_tec_png, X_FT, Y_FT, W_FT, H_FT)

    # Empresa
    c.drawString(X_EMP, Y_EMP, f"EMPRESA RESPONSABLE : {empresa}")

    # Observaciones (uso interno)
    _multi_text(c, obs_int or "", X_OBS_INT, Y_OBS_INT, W_OBS_INT, LINE_OBS_INT)

    # Recepción conforme (firmas)
    f_ing_png = _recortar_firma(firma_ing)
    f_cli_png = _recortar_firma(firma_cli)
    _draw_image_centered(c, f_ing_png, X_RC_L, Y_RC, W_RC, H_RC)
    _draw_image_centered(c, f_cli_png, X_RC_R, Y_RC, W_RC, H_RC)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf

def _merge_with_template(overlay_bytes, template_path="MAQ ANESTESIA_V2.pdf"):
    # Lee plantilla y fusiona con la “capa” dibujada
    base_reader = PdfReader(template_path)
    base_page = base_reader.pages[0]

    ov_reader = PdfReader(overlay_bytes)
    ov_page = ov_reader.pages[0]

    # Combinar (stamp)
    merged = PageObject.create_blank_page(
        width=base_page.mediabox.width, height=base_page.mediabox.height
    )
    merged.merge_page(base_page)
    merged.merge_page(ov_page)

    writer = PdfWriter()
    writer.add_page(merged)

    out_buf = io.BytesIO()
    writer.write(out_buf)
    out_buf.seek(0)
    return out_buf

if st.button("Generar PDF (plantilla V2 1:1)"):
    overlay = _build_overlay_pdf_bytes()
    final_pdf = _merge_with_template(overlay, template_path="MAQ ANESTESIA_V2.pdf")
    st.download_button(
        "Descargar PDF (V2 idéntico a plantilla)",
        data=final_pdf.getvalue(),
        file_name=f"MP_Anestesia_V2_{sn or 'sin_serie'}.pdf",
        mime="application/pdf"
    )
