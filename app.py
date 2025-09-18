# app.py
# -----------------------------------------------------------
# Pauta Mantención Máquina de Anestesia (V2) - PDF idéntico a la plantilla
# Genera un PDF 1:1 usando MAQ ANESTESIA_V2.pdf como fondo (A4 landscape)
# Requisitos: streamlit, pillow, numpy, streamlit-drawable-canvas, reportlab, pypdf
# -----------------------------------------------------------

import streamlit as st
import datetime, io, numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# PDF: fondo + superposición
from pypdf import PdfReader, PdfWriter, PageObject
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader

# ============= Config posiciones (en mm) calibradas para MAQ ANESTESIA_V2.pdf =============
MM = 2.83465  # 1 mm en puntos

CFG_POS = {
    # --- Cabecera izquierda/derecha (se escribe sobre líneas punteadas) ---
    "cab": {
        "marca":  {"x": 42,  "y": 35, "w": 60},   # MARCA (izq)
        "modelo": {"x": 42,  "y": 42, "w": 60},   # MODELO (izq)
        "sn":     {"x": 42,  "y": 49, "w": 60},   # S/N (izq)
        "ninv":   {"x": 42,  "y": 56, "w": 60},   # N/INVENTARIO (izq)
        "ubic":   {"x": 42,  "y": 63, "w": 60},   # UBICACIÓN (izq)
        "fecha":  {"x": 215, "y": 35, "w": 32},   # FECHA (caja derecha)
    },

    # --- Columnas de checks (X) ---
    # Bloques 1..4 (lado izquierdo)
    "checks_left": {
        "ok":  140, "no": 150, "na": 160,  # centros columnas OK/NO/N/A (mm)
        "row_h": 6.0,
        "sec1_y":  72,  "sec1_n": 4,   # 1. Chequeo Visual
        "sec2_y": 104,  "sec2_n": 4,   # 2. Alta Presión
        "sec3_y": 141,  "sec3_n": 9,   # 3. Baja presión
        "sec4_y": 192,  "sec4_n": 7,   # 4. Absorbedor
    },
    # Bloques 5..6 (lado derecho)
    "checks_right": {
        "ok":  282, "no": 292, "na": 302,
        "row_h": 6.0,
        "sec5a_y":  47,  "sec5a_n": 6,  # 5.1..5.6
        "sec5b_y":  83,  "sec5b_n": 2,  # 5.7..5.8
        "sec6_y":  106, "sec6_n": 3,    # 6. Seguridad eléctrica
    },

    # --- 7. Instrumentos de análisis (dos bloques, lado derecho) ---
    "ia": {
        "eq1": {"x": 206, "y": 133, "w": 40},
        "ma1": {"x": 206, "y": 140, "w": 40},
        "mo1": {"x": 206, "y": 147, "w": 40},
        "se1": {"x": 206, "y": 154, "w": 40},

        "eq2": {"x": 264, "y": 133, "w": 40},
        "ma2": {"x": 264, "y": 140, "w": 40},
        "mo2": {"x": 264, "y": 147, "w": 40},
        "se2": {"x": 264, "y": 154, "w": 40},
    },

    # --- Observaciones (caja grande derecha) ---
    "obs": {"x": 190, "y": 163, "w": 112, "line_h": 5.8, "max_lines": 6},

    # --- Equipo operativo (SI/NO) en línea ---
    "operativo": {"x": 190, "y": 179, "w": 70},

    # --- Técnico + firma (caja) ---
    "tecnico": {"x": 190, "y": 186, "w": 85},
    "firma_tec_box": {"x": 257, "y": 181, "w": 38, "h": 12},  # caja firma técnico (mm)

    # --- Empresa responsable ---
    "empresa": {"x": 190, "y": 194, "w": 90},

    # --- Observaciones (uso interno) ---
    "obs_int": {"x": 20, "y": 206, "w": 265, "line_h": 5.8, "max_lines": 4},

    # --- Recepción conforme (firmas) ---
    "rc_ing": {"x": 62,  "y": 226, "w": 62, "h": 15},
    "rc_cli": {"x": 202, "y": 226, "w": 62, "h": 15},
}

# ============= Helpers de firmas y texto =============
def recortar_firma(canvas_result):
    """Recorta la firma dibujada (elimina fondo en blanco) y devuelve PNG en memoria."""
    if canvas_result.image_data is None:
        return None
    arr = canvas_result.image_data.astype(np.uint8)
    img = Image.fromarray(arr).convert("RGB")
    gray = img.convert("L")
    ys, xs = np.where(np.array(gray) < 230)
    if len(xs) == 0:
        return None
    x1, y1, x2, y2 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    crop = img.crop((x1, y1, x2, y2))
    bio = io.BytesIO()
    crop.save(bio, format="PNG")
    bio.seek(0)
    return bio

# ============= UI =============
st.title("Pauta Mantención — PDF idéntico a la plantilla (A4 Horizontal)")

c1, c2 = st.columns(2)
with c1:
    marca  = st.text_input("MARCA")
    modelo = st.text_input("MODELO")
    sn     = st.text_input("S/N")
with c2:
    n_inv  = st.text_input("N/INVENTARIO")
    ubic   = st.text_input("UBICACIÓN")
    fecha  = st.date_input("FECHA", value=datetime.date.today())

def block(title, items):
    st.subheader(title)
    outs = []
    for it in items:
        a, b = st.columns([5, 3])
        with a:
            st.write(it)
        with b:
            outs.append(st.radio(" ", ["OK", "NO", "N/A"], horizontal=True, key=f"{title}-{it}"))
    return outs

# Ítems por bloque
items1 = ["1.1. Carcasa Frontal y Trasera", "1.2. Estado de Software", "1.3. Panel frontal", "1.4. Batería de respaldo"]
items2 = ["2.1. Chequeo de yugo de O2, N2O, Aire", "2.2. Revisión o reemplazo de empaquetadura de yugo", "2.3. Verificación de entrada de presión", "2.4. Revisión y calibración de válvulas de flujometro de O2, N2O, Aire"]
items3 = [
    "3.1. Revisión y calibración de válvula de flujómetro de N2O", "3.2. Revisión y calibración de válvula de flujometro de O2",
    "3.3. Revisión y calibración de válvula de flujometro de Aire", "3.4. Chequeo de fugas", "3.5. Verificación de flujos",
    "3.6. Verificación de regulador de 2da etapa", "3.7. Revisión de sistema de corte N2O/Aire por falta de O2",
    "3.8. Revisión de sistema proporción de O2/N2O", "3.9. Revisión de manifold de vaporizadores"
]
items4 = ["4.1. Revisión o reemplazo de empaquetadura de canister", "4.2. Revisión de válvula APL", "4.3. Verificación de manómetro de presión de vía aérea (ajuste a cero)",
          "4.4. Revisión de válvula inhalatoria", "4.5. Revisión de válvula exhalatoria", "4.6. Chequeo de fugas", "4.7. Hermeticidad"]
items5 = ["5.1. Porcentaje de oxigeno", "5.2. Volumen corriente y volumen minuto", "5.3. Presión de vía aérea",
          "5.4. Frecuencia respiratoria", "5.5. Modo ventilatorio", "5.6. Alarmas",
          "5.7. Calibración de celda de oxígeno a 21% y al 100%", "5.8. Calibración de sensores de flujo"]
items6 = ["6.1. Corriente de fuga", "6.2. Tierra de protección", "6.3. Aislación"]

res1 = block("1. Chequeo Visual", items1)
res2 = block("2. Sistema de Alta Presión", items2)
res3 = block("3. Sistema de baja presión", items3)
res4 = block("4. Sistema absorbedor", items4)
res5 = block("5. Ventilador mecánico", items5)
res6 = block("6. Seguridad eléctrica", items6)

st.subheader("7. Instrumentos de análisis")
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

obs    = st.text_area("Observaciones", height=90)
op     = st.radio("¿Equipo operativo?", ["SI", "NO"], horizontal=True)

cT1, cT2 = st.columns([2, 1])
with cT1:
    tecnico = st.text_input("NOMBRE TÉCNICO/INGENIERO")
    empresa = st.text_input("EMPRESA RESPONSABLE")
with cT2:
    st.caption("FIRMA TÉCNICO/INGENIERO")
    firma_tec = st_canvas(fill_color="rgba(0,0,0,0)", stroke_width=2, stroke_color="#000",
                          background_color="#fff", height=110, width=260, drawing_mode="freedraw", key="firma_tec")

obs_int = st.text_area("Observaciones (uso interno)", height=90)

st.subheader("Recepción conforme")
cR1, cR2 = st.columns(2)
with cR1:
    st.write("PERSONAL INGENIERÍA CLÍNICA")
    firma_ing = st_canvas(fill_color="rgba(0,0,0,0)", stroke_width=2, stroke_color="#000",
                          background_color="#fff", height=95, width=240, drawing_mode="freedraw", key="firma_ing")
with cR2:
    st.write("PERSONAL CLÍNICO")
    firma_cli = st_canvas(fill_color="rgba(0,0,0,0)", stroke_width=2, stroke_color="#000",
                          background_color="#fff", height=95, width=240, drawing_mode="freedraw", key="firma_cli")

# ============= Construir overlay (texto/X/firmas) en la misma página que la plantilla =============
def build_overlay(template_path="MAQ ANESTESIA_V2.pdf"):
    reader = PdfReader(template_path)
    page = reader.pages[0]
    W, H = float(page.mediabox.width), float(page.mediabox.height)

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(W, H))

    # Helpers
    def draw_text_mm(txt, x, y, size=9):
        c.setFont("Helvetica", size)
        c.drawString(x * MM, H - y * MM, txt or "")

    def draw_lines_block(text, x, y, line_h, max_lines):
        c.setFont("Helvetica", 9)
        for i, ln in enumerate((text or "").splitlines()[:max_lines]):
            c.drawString(x * MM, H - (y + i * line_h) * MM, ln)

    def put_x(center_x_mm, y_mm):
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(center_x_mm * MM, H - (y_mm - 3) * MM, "X")

    # CABECERA
    draw_text_mm(marca,  CFG_POS["cab"]["marca"]["x"],  CFG_POS["cab"]["marca"]["y"])
    draw_text_mm(modelo, CFG_POS["cab"]["modelo"]["x"], CFG_POS["cab"]["modelo"]["y"])
    draw_text_mm(sn,     CFG_POS["cab"]["sn"]["x"],     CFG_POS["cab"]["sn"]["y"])
    draw_text_mm(n_inv,  CFG_POS["cab"]["ninv"]["x"],   CFG_POS["cab"]["ninv"]["y"])
    draw_text_mm(ubic,   CFG_POS["cab"]["ubic"]["x"],   CFG_POS["cab"]["ubic"]["y"])
    draw_text_mm(fecha.strftime("%d/%m/%Y"), CFG_POS["cab"]["fecha"]["x"], CFG_POS["cab"]["fecha"]["y"])

    # CHECKS IZQUIERDA (1..4)
    cl = CFG_POS["checks_left"]
    y = cl["sec1_y"]
    for sel in res1:
        put_x({"OK": cl["ok"], "NO": cl["no"], "N/A": cl["na"]}[sel], y)
        y += cl["row_h"]

    y = cl["sec2_y"]
    for sel in res2:
        put_x({"OK": cl["ok"], "NO": cl["no"], "N/A": cl["na"]}[sel], y)
        y += cl["row_h"]

    y = cl["sec3_y"]
    for sel in res3:
        put_x({"OK": cl["ok"], "NO": cl["no"], "N/A": cl["na"]}[sel], y)
        y += cl["row_h"]

    y = cl["sec4_y"]
    for sel in res4:
        put_x({"OK": cl["ok"], "NO": cl["no"], "N/A": cl["na"]}[sel], y)
        y += cl["row_h"]

    # CHECKS DERECHA (5..6)
    cr = CFG_POS["checks_right"]
    y = cr["sec5a_y"]
    for sel in res5[:6]:
        put_x({"OK": cr["ok"], "NO": cr["no"], "N/A": cr["na"]}[sel], y)
        y += cr["row_h"]

    y = cr["sec5b_y"]
    for sel in res5[6:]:
        put_x({"OK": cr["ok"], "NO": cr["no"], "N/A": cr["na"]}[sel], y)
        y += cr["row_h"]

    y = cr["sec6_y"]
    for sel in res6:
        put_x({"OK": cr["ok"], "NO": cr["no"], "N/A": cr["na"]}[sel], y)
        y += cr["row_h"]

    # 7. INSTRUMENTOS DE ANÁLISIS
    ia = CFG_POS["ia"]
    draw_text_mm(eq1, ia["eq1"]["x"], ia["eq1"]["y"])
    draw_text_mm(ma1, ia["ma1"]["x"], ia["ma1"]["y"])
    draw_text_mm(mo1, ia["mo1"]["x"], ia["mo1"]["y"])
    draw_text_mm(se1, ia["se1"]["x"], ia["se1"]["y"])

    draw_text_mm(eq2, ia["eq2"]["x"], ia["eq2"]["y"])
    draw_text_mm(ma2, ia["ma2"]["x"], ia["ma2"]["y"])
    draw_text_mm(mo2, ia["mo2"]["x"], ia["mo2"]["y"])
    draw_text_mm(se2, ia["se2"]["x"], ia["se2"]["y"])

    # OBSERVACIONES
    draw_lines_block(obs, CFG_POS["obs"]["x"], CFG_POS["obs"]["y"],
                     CFG_POS["obs"]["line_h"], CFG_POS["obs"]["max_lines"])

    # EQUIPO OPERATIVO
    si = "X" if op == "SI" else ""
    no = "X" if op == "NO" else ""
    draw_text_mm(f"SI [ {si} ]    NO [ {no} ]", CFG_POS["operativo"]["x"], CFG_POS["operativo"]["y"])

    # TÉCNICO + FIRMA
    draw_text_mm(tecnico, CFG_POS["tecnico"]["x"], CFG_POS["tecnico"]["y"])
    ftec = recortar_firma(firma_tec)
    if ftec:
        x, yb, w, h = (CFG_POS["firma_tec_box"][k] for k in ("x", "y", "w", "h"))
        img = Image.open(ftec); iw, ih = img.size
        scale = min((w*MM)/iw, (h*MM)/ih); dw, dh = iw*scale, ih*scale
        x_pt = x*MM + (w*MM - dw)/2
        y_pt = H - yb*MM - h*MM + (h*MM - dh)/2
        c.drawImage(ImageReader(ftec), x_pt, y_pt, width=dw, height=dh, mask='auto')

    # EMPRESA
    draw_text_mm(empresa, CFG_POS["empresa"]["x"], CFG_POS["empresa"]["y"])

    # OBS. (USO INTERNO)
    draw_lines_block(obs_int, CFG_POS["obs_int"]["x"], CFG_POS["obs_int"]["y"],
                     CFG_POS["obs_int"]["line_h"], CFG_POS["obs_int"]["max_lines"])

    # RECEPCIÓN CONFORME (FIRMAS)
    fing = recortar_firma(firma_ing)
    fcli = recortar_firma(firma_cli)
    if fing:
        x, yb, w, h = (CFG_POS["rc_ing"][k] for k in ("x", "y", "w", "h"))
        img = Image.open(fing); iw, ih = img.size
        scale = min((w*MM)/iw, (h*MM)/ih); dw, dh = iw*scale, ih*scale
        x_pt = x*MM + (w*MM - dw)/2
        y_pt = H - yb*MM - h*MM + (h*MM - dh)/2
        c.drawImage(ImageReader(fing), x_pt, y_pt, width=dw, height=dh, mask='auto')
    if fcli:
        x, yb, w, h = (CFG_POS["rc_cli"][k] for k in ("x", "y", "w", "h"))
        img = Image.open(fcli); iw, ih = img.size
        scale = min((w*MM)/iw, (h*MM)/ih); dw, dh = iw*scale, ih*scale
        x_pt = x*MM + (w*MM - dw)/2
        y_pt = H - yb*MM - h*MM + (h*MM - dh)/2
        c.drawImage(ImageReader(fcli), x_pt, y_pt, width=dw, height=dh, mask='auto')

    c.showPage(); c.save(); buf.seek(0)
    return buf

# Fusiona overlay con plantilla
def merge_with_template(overlay_bytes, template_path="MAQ ANESTESIA_V2.pdf"):
    base_reader = PdfReader(template_path)
    base_page = base_reader.pages[0]
    ov_reader = PdfReader(overlay_bytes)
    ov_page = ov_reader.pages[0]

    merged = PageObject.create_blank_page(width=base_page.mediabox.width,
                                          height=base_page.mediabox.height)
    merged.merge_page(base_page)
    merged.merge_page(ov_page)

    writer = PdfWriter()
    writer.add_page(merged)
    out = io.BytesIO()
    writer.write(out); out.seek(0)
    return out

# ============= Botón: generar y descargar =============
if st.button("Generar PDF (idéntico a plantilla, Horizontal)"):
    overlay = build_overlay("MAQ ANESTESIA_V2.pdf")
    final_pdf = merge_with_template(overlay, "MAQ ANESTESIA_V2.pdf")
    st.download_button(
        "Descargar PDF (V2 — igual a plantilla)",
        data=final_pdf.getvalue(),
        file_name=f"MP_Anestesia_V2_{(sn or 'sin_serie')}.pdf",
        mime="application/pdf"
    )
