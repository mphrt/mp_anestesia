
import streamlit as st
from fpdf import FPDF
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import io, datetime, tempfile, numpy as np

def create_checkbox_table(pdf, title, items):
    if pdf.get_y() > 260: pdf.add_page()
    pdf.set_font("Arial", "B", 10); pdf.cell(0, 7, title, ln=True)
    pdf.set_font("Arial", "", 10); pdf.cell(140, 7, "", 0)
    for h in ["OK", "NO", "N/A"]: pdf.cell(15, 7, h, 1, 0, "C")
    pdf.ln()
    for item, val in items:
        if pdf.get_y() > 270: pdf.add_page()
        pdf.cell(140, 7, item, 1)
        for opt in ["OK", "NO", "N/A"]:
            pdf.cell(15, 7, "X" if val == opt else "", 1, 0, "C")
        pdf.ln()
    pdf.ln(3)

def add_signature(pdf, canvas, x0, y0):
    if canvas.image_data is None: return
    img = Image.fromarray(canvas.image_data.astype(np.uint8)).convert("L")
    coords = np.argwhere(np.array(img) < 230)
    if coords.size == 0: return
    min_y, min_x = coords.min(0); max_y, max_x = coords.max(0)
    cropped = Image.fromarray(canvas.image_data.astype(np.uint8)).crop((min_x, min_y, max_x+1, max_y+1)).convert("RGB")
    buffer = io.BytesIO(); cropped.save(buffer, format='PNG'); buffer.seek(0)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f: f.write(buffer.read()); path = f.name
    w, h = 50, 50 * cropped.height / cropped.width
    if h > 30: h, w = 30, 30 * cropped.width / cropped.height
    pdf.image(path, x=x0 + 30 - w / 2, y=y0, w=w, h=h)

def main():
    st.title("Pauta de Mantenimiento Preventivo - Máquina de Anestesia")
    marca, modelo, sn = st.text_input("Marca"), st.text_input("Modelo"), st.text_input("S/N")
    inventario, fecha, ubicacion = st.text_input("N° Inventario"), st.date_input("Fecha", value=datetime.date.today()), st.text_input("Ubicación")

    def checklist(t, items):
        st.subheader(t); return [(i, st.columns([5, 3])[1].radio("", ["OK", "NO", "N/A"], horizontal=True, key=i)) for i in items]

    secciones = [
        ("1. Chequeo Visual", [
            "1.1. Carcasa Frontal y Trasera", "1.2. Estado de Software", "1.3. Panel frontal", "1.4. Batería de respaldo"
        ]),
        ("2. Sistema de Alta Presión", [
            "2.1. Chequeo de yugo de O2, N2O, Aire", "2.2. Revisión o reemplazo de empaquetadura de yugo",
            "2.3. Verificación de entrada de presión", "2.4. Revisión y calibración de válvulas de flujometro de O2, N2O, Aire"
        ]),
        ("3. Sistema de baja presión", [
            "3.1. Revisión y calibración de válvula de flujómetro de N2O", "3.2. Revisión y calibración de válvula de flujometro de O2",
            "3.3. Revisión y calibración de válvula de flujometro de Aire", "3.4. Chequeo de fugas", "3.5. Verificación de flujos",
            "3.6. Verificación de regulador de 2da etapa", "3.7. Revisión de sistema de corte N2O/Aire por falta de O2",
            "3.8. Revisión de sistema proporción de O2/N2O", "3.9. Revisión de manifold de vaporizadores"
        ]),
        ("4. Sistema absorbedor", [
            "4.1. Revisión o reemplazo de empaquetadura de canister", "4.2. Revisión de válvula APL",
            "4.3. Verificación de manómetro de presión de vía aérea", "4.4. Revisión de válvula inhalatoria",
            "4.5. Revisión de válvula exhalatoria", "4.6. Chequeo de fugas", "4.7. Hermeticidad"
        ]),
        ("5. Ventilador mecánico", [
            "5.1. Porcentaje de oxígeno", "5.2. Volumen corriente y volumen minuto", "5.3. Presión de vía aérea",
            "5.4. Frecuencia respiratoria", "5.5. Modo ventilatorio", "5.6. Alarmas",
            "5.7. Calibración de celda de oxígeno a 21% y al 100%", "5.8. Calibración de sensores de flujo"
        ]),
        ("6. Seguridad eléctrica", [
            "6.1. Corriente de fuga", "6.2. Tierra de protección", "6.3. Aislación"
        ])
    ]
    respuestas = [checklist(t, i) for t, i in secciones]

    eq1, marca1, modelo1, serie1 = st.text_input("Equipo 1"), st.text_input("Marca 1"), st.text_input("Modelo 1"), st.text_input("N° Serie 1")
    eq2, marca2, modelo2, serie2 = st.text_input("Equipo 2"), st.text_input("Marca 2"), st.text_input("Modelo 2"), st.text_input("N° Serie 2")
    observaciones, obs_int = st.text_area("Observaciones"), st.text_area("Observaciones (uso interno)")
    operativo, tecnico, empresa = st.radio("¿Equipo operativo?", ["SI", "NO"]), st.text_input("Nombre Técnico/Ingeniero"), st.text_input("Empresa Responsable")

    st.subheader("Firmas")
    canvas_tecnico = st_canvas(height=150, width=300, stroke_width=2, background_color="#EEEEEE", key="tecnico")
    canvas_ingenieria = st_canvas(height=150, width=300, stroke_width=2, background_color="#EEEEEE", key="ingenieria")
    canvas_clinico = st_canvas(height=150, width=300, stroke_width=2, background_color="#EEEEEE", key="clinico")

    if st.button("Generar PDF"):
        pdf = FPDF(); pdf.add_page()
        try: pdf.image("logo_hrt_final.jpg", x=10, y=6, w=45)
        except: pass
        pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, "HOSPITAL REGIONAL DE TALCA", ln=True, align="C")
        pdf.set_font("Arial", "", 10); pdf.cell(0, 8, "UNIDAD DE INGENIERÍA CLÍNICA", ln=True, align="C")
        pdf.set_font("Arial", "B", 11); pdf.cell(0, 10, "PAUTA MANTENIMIENTO PREVENTIVO MAQUINA ANESTESIA (Ver 2)", ln=True, align="C")
        pdf.ln(5)

        for k, v in [("MARCA", marca), ("MODELO", modelo), ("S/N", sn), ("N° INVENTARIO", inventario), ("UBICACIÓN", ubicacion), ("FECHA", fecha.strftime("%d/%m/%Y"))]:
            pdf.cell(0, 7, f"{k}: {v}", ln=True)
        pdf.ln(5)

        for (titulo, _), data in zip(secciones, respuestas):
            create_checkbox_table(pdf, titulo, data)

        pdf.set_font("Arial", "B", 10); pdf.cell(0, 7, "7. Instrumentos de análisis", ln=True)
        pdf.set_font("Arial", "", 10)
        for eq, mk, mo, se in [(eq1, marca1, modelo1, serie1), (eq2, marca2, modelo2, serie2)]:
            pdf.cell(0, 7, f"Equipo: {eq} | Marca: {mk} | Modelo: {mo} | N° Serie: {se}", ln=True)
        for t, txt in [("Observaciones", observaciones), ("Observaciones (uso interno)", obs_int)]:
            pdf.multi_cell(0, 6, f"{t}: {txt}")
        for l, val in [("Equipo Operativo", operativo), ("Nombre Técnico", tecnico), ("Empresa Responsable", empresa)]:
            pdf.cell(0, 7, f"{l}: {val}", ln=True)

        pdf.add_page()
        x_pos = [20, 90, 150]; y = 60
        for x, c in zip(x_pos, [canvas_tecnico, canvas_ingenieria, canvas_clinico]):
            add_signature(pdf, c, x, y)
        pdf.set_y(y + 30)
        for x, label in zip(x_pos, ["TÉCNICO ENCARGADO", "INGENIERÍA CLÍNICA", "PERSONAL CLÍNICO"]):
            pdf.set_x(x); pdf.cell(60, 6, "_________________________", 0, 2, 'C')
            pdf.set_x(x); pdf.cell(60, 6, label, 0, 0, 'C')

        st.download_button("Descargar PDF", io.BytesIO(pdf.output(dest="S").encode("latin1")).getvalue(), file_name=f"MP_Anestesia_{sn}.pdf", mime="application/pdf")

if __name__ == "__main__": main()
