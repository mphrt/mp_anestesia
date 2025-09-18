import streamlit as st
import datetime, io, numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# --- PDF stamping ---
from pypdf import PdfReader, PdfWriter, PageObject
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader

# ===========================
# CONFIG: posiciones (mm)
# ===========================
MM = 2.83465  # 1 mm en puntos

CFG = {
    "cab": {"xL": 25, "xR": 200, "row": 7.5},
    "tbl_left": {"x_text": 20, "w_text": 120, "w_col": 10, "ok": 140, "no": 150, "na": 160, "row": 6},
    "tbl_right": {"x_text": 185, "w_text": 98, "w_col": 10, "ok": 283, "no": 293, "na": 303, "row": 6},
    "y": {
        "sec1": 70, "sec2": 102, "sec3": 139, "sec4": 190,
        "sec5a": 46, "sec5b": 83, "sec6": 106, "ia": 132,
        "obs": 160, "op": 178, "tec": 186,
        "firmaTecBox": (255, 181, 38, 12),
        "emp": 194, "obs_int": 206,
        "rc_left": (60, 226, 65, 15),
        "rc_right": (200, 226, 65, 15),
    }
}

def recortar_firma(canvas_result):
    if canvas_result.image_data is None: return None
    arr = canvas_result.image_data.astype(np.uint8)
    img = Image.fromarray(arr).convert("RGB")
    gray = img.convert("L")
    ys, xs = np.where(np.array(gray) < 230)
    if len(xs) == 0: return None
    x1, y1, x2, y2 = xs.min(), ys.min(), xs.max()+1, ys.max()+1
    crop = img.crop((x1, y1, x2, y2))
    bio = io.BytesIO()
    crop.save(bio, format="PNG")
    bio.seek(0)
    return bio

def draw_img_centered(c, png_bytes, x_mm, y_mm, w_mm, h_mm, page_h_pt):
    if not png_bytes: return
    img = Image.open(png_bytes)
    iw, ih = img.size
    scale = min((w_mm*MM)/iw, (h_mm*MM)/ih)
    dw, dh = iw*scale, ih*scale
    x_pt = x_mm*MM + (w_mm*MM - dw)/2
    y_pt = page_h_pt - (y_mm*MM) - h_mm*MM + (h_mm*MM - dh)/2
    c.drawImage(ImageReader(png_bytes), x_pt, y_pt, width=dw, height=dh, mask='auto')

def draw_text(c, s, x_mm, y_mm, page_h_pt, size=9, bold=False, centered=False):
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    x_pt = x_mm*MM
    y_pt = page_h_pt - y_mm*MM
    if centered: c.drawCentredString(x_pt, y_pt, s)
    else: c.drawString(x_pt, y_pt, s)

def draw_x_in_col(c, sel, ok_x, no_x, na_x, y_mm, page_h_pt):
    if sel == "OK":
        draw_text(c, "X", ok_x, y_mm-4, page_h_pt, size=9, centered=True)
    elif sel == "NO":
        draw_text(c, "X", no_x, y_mm-4, page_h_pt, size=9, centered=True)
    elif sel == "N/A":
        draw_text(c, "X", na_x, y_mm-4, page_h_pt, size=9, centered=True)

st.title("Pauta Mantención — salida PDF igual a la plantilla (Landscape)")

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
    st.subheader(title)
    outs = []
    for it in items:
        a,b = st.columns([5,3])
        with a: st.write(it)
        with b: outs.append(st.radio(" ", ["OK","NO","N/A"], horizontal=True, key=f"{title}-{it}"))
    return outs

items1 = ["1.1. Carcasa Frontal y Trasera","1.2. Estado de Software","1.3. Panel frontal","1.4. Batería de respaldo"]
items2 = ["2.1. Chequeo de yugo de O2, N2O, Aire","2.2. Revisión o reemplazo de empaquetadura de yugo","2.3. Verificación de entrada de presión","2.4. Revisión y calibración de válvulas de flujometro de O2, N2O, Aire"]
items3 = ["3.1. Revisión y calibración de válvula de flujómetro de N2O","3.2. Revisión y calibración de válvula de flujometro de O2","3.3. Revisión y calibración de válvula de flujometro de Aire","3.4. Chequeo de fugas","3.5. Verificación de flujos","3.6. Verificación de regulador de 2da etapa","3.7. Revisión de sistema de corte N2O/Aire por falta de O2","3.8. Revisión de sistema proporción de O2/N2O","3.9. Revisión de manifold de vaporizadores"]
items4 = ["4.1. Revisión o reemplazo de empaquetadura de canister","4.2. Revisión de válvula APL","4.3. Verificación de manómetro de presión de vía aérea (ajuste a cero)","4.4. Revisión de válvula inhalatoria","4.5. Revisión de válvula exhalatoria","4.6. Chequeo de fugas","4.7. Hermeticidad"]
items5 = ["5.1. Porcentaje de oxigeno","5.2. Volumen corriente y volumen minuto","5.3. Presión de vía aérea","5.4. Frecuencia respiratoria","5.5. Modo ventilatorio","5.6. Alarmas","5.7. Calibración de celda de oxígeno a 21% y al 100%","5.8. Calibración de sensores de flujo"]
items6 = ["6.1. Corriente de fuga","6.2. Tierra de protección","6.3. Aislación"]

res1 = block("1. Chequeo Visual", items1)
res2 = block("2. Sistema de Alta Presión", items2)
res3 = block("3. Sistema de baja presión", items3)
res4 = block("4. Sistema absorbedor", items4)
res5 = block("5. Ventilador mecánico", items5)
res6 = block("6. Seguridad eléctrica", items6)

st.subheader("7. Instrumentos de análisis")
cA,cB = st.columns(2)
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
op = st.radio("¿Equipo operativo?", ["SI","NO"], horizontal=True)

cT1,cT2 = st.columns([2,1])
with cT1:
    tecnico = st.text_input("NOMBRE TÉCNICO/INGENIERO")
    empresa = st.text_input("EMPRESA RESPONSABLE")
with cT2:
    st.caption("FIRMA TÉCNICO/INGENIERO")
    firma_tec = st_canvas(fill_color="rgba(0,0,0,0)", stroke_width=2, stroke_color="#000", background_color="#fff", height=110, width=260, drawing_mode="freedraw", key="firma_tec")

obs_int = st.text_area("Observaciones (uso interno)", height=90)

st.subheader("Recepción conforme")
cR1,cR2 = st.columns(2)
with cR1:
    st.write("PERSONAL INGENIERÍA CLÍNICA")
    firma_ing = st_canvas(fill_color="rgba(0,0,0,0)", stroke_width=2, stroke_color="#000", background_color="#fff", height=95, width=240, drawing_mode="freedraw", key="firma_ing")
with cR2:
    st.write("PERSONAL CLÍNICO")
    firma_cli = st_canvas(fill_color="rgba(0,0,0,0)", stroke_width=2, stroke_color="#000", background_color="#fff", height=95, width=240, drawing_mode="freedraw", key="firma_cli")

def build_overlay(template_path="MAQ ANESTESIA_V2.pdf"):
    reader = PdfReader(template_path)
    page = reader.pages[0]
    W = float(page.mediabox.width)
    H = float(page.mediabox.height)

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(W, H))

    xL, xR, row = CFG["cab"]["xL"], CFG["cab"]["xR"], CFG["cab"]["row"]
    y0 = 30
    draw_text(c, f"MARCA  : {marca}", xL, y0, H, size=9)
    draw_text(c, f"FECHA : {fecha.strftime('%d/%m/%Y')}", xR, y0, H, size=9)
    draw_text(c, f"MODELO : {modelo}", xL, y0+row, H, size=9)
    draw_text(c, f"S/N : {sn}", xR, y0+row, H, size=9)
    draw_text(c, f"N/INVENTARIO : {n_inv}", xL, y0+2*row, H, size=9)
    draw_text(c, f"UBICACIÓN : {ubic}", xR, y0+2*row, H, size=9)

    def paint_section(items_sel, side, y_from_top):
        col = CFG["tbl_left"] if side=="L" else CFG["tbl_right"]
        y = y_from_top
        for sel in items_sel:
            s = sel[1] if isinstance(sel, tuple) else sel
            draw_x_in_col(c, s, col["ok"], col["no"], col["na"], y, H)
            y += col["row"]

    paint_section(res1, "L", CFG["y"]["sec1"])
    paint_section(res2, "L", CFG["y"]["sec2"])
    paint_section(res3, "L", CFG["y"]["sec3"])
    paint_section(res4, "L", CFG["y"]["sec4"])
    paint_section([s for s in res5[:6]], "R", CFG["y"]["sec5a"])
    paint_section([s for s in res5[6:]], "R", CFG["y"]["sec5b"])
    paint_section(res6, "R", CFG["y"]["sec6"])

    ia_y = CFG["y"]["ia"]
    draw_text(c, f"EQUIPO  : {eq1}", 190, ia_y, H, size=9)
    draw_text(c, f"MARCA   : {ma1}", 190, ia_y+7, H, size=9)
    draw_text(c, f"MODELO  : {mo1}", 190, ia_y+14, H, size=9)
    draw_text(c, f"NUMERO SERIE : {se1}", 190, ia_y+21, H, size=9)

    draw_text(c, f"EQUIPO  : {eq2}", 255, ia_y, H, size=9)
    draw_text(c, f"MARCA   : {ma2}", 255, ia_y+7, H, size=9)
    draw_text(c, f"MODELO  : {mo2}", 255, ia_y+14, H, size=9)
    draw_text(c, f"NUMERO SERIE : {se2}", 255, ia_y+21, H, size=9)

    for i, line in enumerate((obs or "").splitlines()[:6]):
        draw_text(c, line, 190, CFG["y"]["obs"] + i*6, H, size=9)

    si = "X" if op=="SI" else " "
    no = "X" if op=="NO" else " "
    draw_text(c, f"EQUIPO OPERATIVO   SI [ {si} ]    NO [ {no} ]", 190, CFG["y"]["op"], H, size=9)

    draw_text(c, f"NOMBRE TÉCNICO/INGENIERO  : {tecnico}", 190, CFG["y"]["tec"], H, size=9)
    xF, yF, wF, hF = CFG["y"]["firmaTecBox"]
    draw_img_centered(c, recortar_firma(firma_tec), xF, yF, wF, hF, H)

    draw_text(c, f"EMPRESA RESPONSABLE : {empresa}", 190, CFG["y"]["emp"], H, size=9)

    for i, line in enumerate((obs_int or "").splitlines()[:4]):
        draw_text(c, line, 20, CFG["y"]["obs_int"] + i*6, H, size=9)

    x1,y1,w1,h1 = CFG["y"]["rc_left"]
    x2,y2,w2,h2 = CFG["y"]["rc_right"]
    draw_img_centered(c, recortar_firma(firma_ing), x1, y1, w1, h1, H)
    draw_img_centered(c, recortar_firma(firma_cli), x2, y2, w2, h2, H)

    c.showPage(); c.save(); buf.seek(0)
    return buf

def merge_with_template(overlay_bytes, template_path="MAQ ANESTESIA_V2.pdf"):
    base_reader = PdfReader(template_path)
    base_page = base_reader.pages[0]
    ov_reader = PdfReader(overlay_bytes)
    ov_page = ov_reader.pages[0]
    merged = PageObject.create_blank_page(width=base_page.mediabox.width, height=base_page.mediabox.height)
    merged.merge_page(base_page); merged.merge_page(ov_page)
    writer = PdfWriter(); writer.add_page(merged)
    out = io.BytesIO(); writer.write(out); out.seek(0)
    return out

if st.button("Generar PDF (idéntico a plantilla, Horizontal)"):
    overlay = build_overlay("MAQ ANESTESIA_V2.pdf")
    final_pdf = merge_with_template(overlay, "MAQ ANESTESIA_V2.pdf")
    st.download_button(
        "Descargar PDF (V2 — igual a plantilla)",
        data=final_pdf.getvalue(),
        file_name=f"MP_Anestesia_V2_{(st.session_state.get('sn') or 'sin_serie')}.pdf",
        mime="application/pdf"
    )
