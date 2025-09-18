# app.py
# -----------------------------------------------------------------------------------
# MP Anestesia V2 — Salida PDF idéntica a la plantilla (A4 horizontal, 1:1)
# Requisitos: streamlit, pillow, numpy, streamlit-drawable-canvas, reportlab, pypdf
# -----------------------------------------------------------------------------------

import streamlit as st
import datetime, io, numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas

from pypdf import PdfReader, PdfWriter, PageObject
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader

# ============================== Base de posiciones (mm) ==============================
MM = 2.83465  # 1 mm = 2.83465 pt

# ¡Ajustado! Estas coordenadas caen mejor sobre la pauta que mostraste.
BASE = {
    # Cabecera (se escribe SOBRE las líneas punteadas de la izquierda y la caja FECHA)
    "cab": {
        "marca":  {"x": 62,  "y": 35},
        "modelo": {"x": 62,  "y": 42},
        "sn":     {"x": 62,  "y": 49},
        "ninv":   {"x": 62,  "y": 56},
        "ubic":   {"x": 62,  "y": 63},
        "fecha":  {"x": 232, "y": 35},
    },

    # Checks izquierda (bloques 1..4). Centros de casillas OK/NO/N/A — AJUSTADOS
    "checks_left": {
        "ok": 144, "no": 153, "na": 162,   # ← mueve toda la columna si hiciera falta
        "row_h": 6.0,
        "sec1_y":  72,  "sec1_n": 4,   # 1. Chequeo Visual
        "sec2_y": 104,  "sec2_n": 4,   # 2. Alta Presión
        "sec3_y": 141,  "sec3_n": 9,   # 3. Baja presión
        "sec4_y": 192,  "sec4_n": 7,   # 4. Absorbedor
    },

    # Checks derecha (bloques 5..6) — AJUSTADOS
    "checks_right": {
        "ok": 283, "no": 292, "na": 301,
        "row_h": 6.0,
        "sec5a_y":  47,  "sec5a_n": 6,  # 5.1..5.6
        "sec5b_y":  83,  "sec5b_n": 2,  # 5.7..5.8
        "sec6_y":  106, "sec6_n": 3,    # 6. Seguridad eléctrica
    },

    # 7. Instrumentos de análisis (dos bloques a la derecha) — AJUSTADOS
    "ia": {
        "eq1": {"x": 215, "y": 133},
        "ma1": {"x": 215, "y": 140},
        "mo1": {"x": 215, "y": 147},
        "se1": {"x": 215, "y": 154},

        "eq2": {"x": 273, "y": 133},
        "ma2": {"x": 273, "y": 140},
        "mo2": {"x": 273, "y": 147},
        "se2": {"x": 273, "y": 154},
    },

    # Observaciones (caja grande derecha)
    "obs": {"x": 198, "y": 163, "line_h": 5.8, "max_lines": 6},

    # Equipo operativo (línea)
    "operativo": {"x": 198, "y": 179},

    # Técnico + caja de firma (pequeña, a la derecha del nombre)
    "tecnico": {"x": 198, "y": 186},
    "firma_tec_box": {"x": 265, "y": 181, "w": 38, "h": 12},

    # Empresa responsable (línea)
    "empresa": {"x": 198, "y": 194},

    # Observaciones uso interno (caja ancha inferior)
    "obs_int": {"x": 28, "y": 206, "line_h": 5.8, "max_lines": 4},

    # Recepción conforme (dos firmas sobre las líneas)
    "rc_ing": {"x": 70,  "y": 226, "w": 62, "h": 15},
    "rc_cli": {"x": 210, "y": 226, "w": 62, "h": 15},
}

# Offset vertical fino para centrar la “X” en cada casilla (positivo = baja la X)
CHECK_Y_OFFSET = 0.8  # mm (fino)

# ========================= Calibración (sliders opcionales) =========================
with st.sidebar:
    st.header("Calibración (mm)")
    glob_dx = st.number_input("ΔX global", -10.0, 10.0, 0.0, 0.5)
    glob_dy = st.number_input("ΔY global", -10.0, 10.0, 0.0, 0.5)
    cab_dx  = st.number_input("ΔX cabecera", -5.0, 5.0, 0.0, 0.5)
    cab_dy  = st.number_input("ΔY cabecera", -5.0, 5.0, 0.0, 0.5)
    l_dx    = st.number_input("ΔX checks izquierda", -5.0, 5.0, 0.0, 0.5)
    l_dy    = st.number_input("ΔY checks izquierda", -5.0, 5.0, 0.0, 0.5)
    r_dx    = st.number_input("ΔX checks derecha", -5.0, 5.0, 0.0, 0.5)
    r_dy    = st.number_input("ΔY checks derecha", -5.0, 5.0, 0.0, 0.5)
    ia_dx   = st.number_input("ΔX instrumentos", -5.0, 5.0, 0.0, 0.5)
    ia_dy   = st.number_input("ΔY instrumentos", -5.0, 5.0, 0.0, 0.5)
    obs_dx  = st.number_input("ΔX observaciones", -5.0, 5.0, 0.0, 0.5)
    obs_dy  = st.number_input("ΔY observaciones", -5.0, 5.0, 0.0, 0.5)
    tec_dx  = st.number_input("ΔX técnico/firma", -5.0, 5.0, 0.0, 0.5)
    tec_dy  = st.number_input("ΔY técnico/firma", -5.0, 5.0, 0.0, 0.5)
    emp_dx  = st.number_input("ΔX empresa", -5.0, 5.0, 0.0, 0.5)
    emp_dy  = st.number_input("ΔY empresa", -5.0, 5.0, 0.0, 0.5)
    oi_dx   = st.number_input("ΔX obs. internas", -5.0, 5.0, 0.0, 0.5)
    oi_dy   = st.number_input("ΔY obs. internas", -5.0, 5.0, 0.0, 0.5)
    rc_dx   = st.number_input("ΔX recepción conf.", -5.0, 5.0, 0.0, 0.5)
    rc_dy   = st.number_input("ΔY recepción conf.", -5.0, 5.0, 0.0, 0.5)

def P(x, y, block_dx=0.0, block_dy=0.0):
    """Aplica offsets globales + de bloque, devuelve (x,y) ajustados en mm."""
    return x + glob_dx + block_dx, y + glob_dy + block_dy

# ============================== Utilidades de firmas ==============================
def recortar_firma(canvas_result):
    if canvas_result.image_data is None:
        return None
    arr = canvas_result.image_data.astype(np.uint8)
    img = Image.fromarray(arr).convert("RGB")
    gray = img.convert("L")
    ys, xs = np.where(np.array(gray) < 230)
    if len(xs) == 0:
        return None
    x1, y1, x2, y2 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    bio = io.BytesIO()
    img.crop((x1, y1, x2, y2)).save(bio, format="PNG")
    bio.seek(0)
    return bio

# ================================== UI ==================================
st.title("Pauta Mantención — PDF idéntico a plantilla (A4 horizontal)")

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
        with a: st.write(it)
        with b: outs.append(st.radio(" ", ["OK", "NO", "N/A"], horizontal=True, key=f"{title}-{it}"))
    return outs

items1 = ["1.1. Carcasa Frontal y Trasera", "1.2. Estado de Software", "1.3. Panel frontal", "1.4. Batería de respaldo"]
items2 = ["2.1. Chequeo de yugo de O2, N2O, Aire", "2.2. Revisión o reemplazo de empaquetadura de yugo",
          "2.3. Verificación de entrada de presión", "2.4. Revisión y calibración de válvulas de flujometro de O2, N2O, Aire"]
items3 = ["3.1. Revisión y calibración de válvula de flujómetro de N2O", "3.2. Revisión y calibración de válvula de flujometro de O2",
          "3.3. Revisión y calibración de válvula de flujometro de Aire", "3.4. Chequeo de fugas", "3.5. Verificación de flujos",
          "3.6. Verificación de regulador de 2da (segunda) etapa", "3.7. Revisión de sistema de corte N2O/Aire por falta de O2",
          "3.8. Revisión de sistema proporción de O2/N2O", "3.9. Revisión de manifold de vaporizadores"]
items4 = ["4.1. Revisión o reemplazo de empaquetadura de canister", "4.2. Revisión de válvula APL",
          "4.3. Verificación de manómetro de presión de vía aérea (ajuste a cero)", "4.4. Revisión de válvula inhalatoria",
          "4.5. Revisión de válvula exhalatoria", "4.6. Chequeo de fugas", "4.7. Hermeticidad"]
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

obs = st.text_area("Observaciones", height=90)
op  = st.radio("¿Equipo operativo?", ["SI", "NO"], horizontal=True)

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

# ======================= Construcción del overlay sobre la plantilla =======================
def build_overlay(template_path="MAQ ANESTESIA_V2.pdf"):
    reader = PdfReader(template_path)
    page = reader.pages[0]
    W, H = float(page.mediabox.width), float(page.mediabox.height)

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(W, H))

    # Helpers
    def text_at(txt, x_mm, y_mm, size=9):
        c.setFont("Helvetica", size)
        c.drawString(x_mm * MM, H - y_mm * MM, txt or "")

    def lines_block(text, x_mm, y_mm, line_h, max_lines):
        c.setFont("Helvetica", 9)
        for i, ln in enumerate((text or "").splitlines()[:max_lines]):
            c.drawString(x_mm * MM, H - (y_mm + i * line_h) * MM, ln)

    def x_mark(cx_mm, y_mm):
        c.setFont("Helvetica-Bold", 10)
        # +CHECK_Y_OFFSET corrige el centrado vertical de la X en la casilla
        c.drawCentredString(cx_mm * MM, H - (y_mm + CHECK_Y_OFFSET) * MM, "X")

    # CABECERA
    for k, val in [
        ("marca", marca), ("modelo", modelo), ("sn", sn),
        ("ninv", n_inv), ("ubic", ubic)
    ]:
        x, y = BASE["cab"][k]["x"], BASE["cab"][k]["y"]
        x, y = P(x, y, cab_dx, cab_dy)
        text_at(val, x, y)
    x, y = P(BASE["cab"]["fecha"]["x"], BASE["cab"]["fecha"]["y"], cab_dx, cab_dy)
    text_at(fecha.strftime("%d/%m/%Y"), x, y)

    # CHECKS IZQUIERDA
    L = BASE["checks_left"]
    for sec_y, items in [(L["sec1_y"], res1), (L["sec2_y"], res2), (L["sec3_y"], res3), (L["sec4_y"], res4)]:
        y = sec_y + l_dy + glob_dy
        for sel in items:
            cx = {"OK": L["ok"] + l_dx + glob_dx, "NO": L["no"] + l_dx + glob_dx, "N/A": L["na"] + l_dx + glob_dx}[sel]
            x_mark(cx, y)
            y += L["row_h"]

    # CHECKS DERECHA
    R = BASE["checks_right"]
    for sec_y, items in [(R["sec5a_y"], res5[:6]), (R["sec5b_y"], res5[6:]), (R["sec6_y"], res6)]:
        y = sec_y + r_dy + glob_dy
        for sel in items:
            cx = {"OK": R["ok"] + r_dx + glob_dx, "NO": R["no"] + r_dx + glob_dx, "N/A": R["na"] + r_dx + glob_dx}[sel]
            x_mark(cx, y)
            y += R["row_h"]

    # 7. INSTRUMENTOS
    for key, val in [("eq1", eq1), ("ma1", ma1), ("mo1", mo1), ("se1", se1),
                     ("eq2", eq2), ("ma2", ma2), ("mo2", mo2), ("se2", se2)]:
        x0, y0 = BASE["ia"][key]["x"], BASE["ia"][key]["y"]
        x0, y0 = P(x0, y0, ia_dx, ia_dy)
        text_at(val, x0, y0)

    # OBSERVACIONES
    x0, y0 = P(BASE["obs"]["x"], BASE["obs"]["y"], obs_dx, obs_dy)
    lines_block(obs, x0, y0, BASE["obs"]["line_h"], BASE["obs"]["max_lines"])

    # EQUIPO OPERATIVO
    x0, y0 = P(BASE["operativo"]["x"], BASE["operativo"]["y"], obs_dx, obs_dy)
    text_at(f"SI [ {'X' if op=='SI' else ' '} ]    NO [ {'X' if op=='NO' else ' '} ]", x0, y0)

    # TÉCNICO + FIRMA
    x0, y0 = P(BASE["tecnico"]["x"], BASE["tecnico"]["y"], tec_dx, tec_dy)
    text_at(tecnico, x0, y0)
    ftec = recortar_firma(firma_tec)
    if ftec:
        bx, by = P(BASE["firma_tec_box"]["x"], BASE["firma_tec_box"]["y"], tec_dx, tec_dy)
        bw, bh = BASE["firma_tec_box"]["w"], BASE["firma_tec_box"]["h"]
        img = Image.open(ftec); iw, ih = img.size
        s = min((bw*MM)/iw, (bh*MM)/ih)
        dw, dh = iw*s, ih*s
        x_pt = bx*MM + (bw*MM - dw)/2
        y_pt = H - by*MM - bh*MM + (bh*MM - dh)/2
        c.drawImage(ImageReader(ftec), x_pt, y_pt, width=dw, height=dh, mask='auto')

    # EMPRESA
    x0, y0 = P(BASE["empresa"]["x"], BASE["empresa"]["y"], emp_dx, emp_dy)
    text_at(empresa, x0, y0)

    # OBS. USO INTERNO
    x0, y0 = P(BASE["obs_int"]["x"], BASE["obs_int"]["y"], oi_dx, oi_dy)
    lines_block(obs_int, x0, y0, BASE["obs_int"]["line_h"], BASE["obs_int"]["max_lines"])

    # RECEPCIÓN CONFORME (FIRMAS)
    for key, firma, dx, dy in [("rc_ing", firma_ing, rc_dx, rc_dy), ("rc_cli", firma_cli, rc_dx, rc_dy)]:
        fpng = recortar_firma(firma)
        if not fpng: continue
        bx, by = P(BASE[key]["x"], BASE[key]["y"], dx, dy)
        bw, bh = BASE[key]["w"], BASE[key]["h"]
        img = Image.open(fpng); iw, ih = img.size
        s = min((bw*MM)/iw, (bh*MM)/ih)
        dw, dh = iw*s, ih*s
        x_pt = bx*MM + (bw*MM - dw)/2
        y_pt = H - by*MM - bh*MM + (bh*MM - dh)/2
        c.drawImage(ImageReader(fpng), x_pt, y_pt, width=dw, height=dh, mask='auto')

    c.showPage(); c.save(); buf.seek(0)
    return buf

# ====================== Fusión overlay + plantilla y descarga ======================
def merge_with_template(overlay_bytes, template_path="MAQ ANESTESIA_V2.pdf"):
    base_reader = PdfReader(template_path)
    base_page = base_reader.pages[0]
    ov_reader = PdfReader(overlay_bytes)
    ov_page = ov_reader.pages[0]
    merged = PageObject.create_blank_page(width=base_page.mediabox.width, height=base_page.mediabox.height)
    merged.merge_page(base_page)
    merged.merge_page(ov_page)
    writer = PdfWriter(); writer.add_page(merged)
    out = io.BytesIO(); writer.write(out); out.seek(0)
    return out

if st.button("Generar PDF (igual a plantilla, Horizontal)"):
    overlay = build_overlay("MAQ ANESTESIA_V2.pdf")
    final_pdf = merge_with_template(overlay, "MAQ ANESTESIA_V2.pdf")
    st.download_button(
        "Descargar PDF (V2 — 1:1)",
        data=final_pdf.getvalue(),
        file_name=f"MP_Anestesia_V2_{(sn or 'sin_serie')}.pdf",
        mime="application/pdf"
    )
