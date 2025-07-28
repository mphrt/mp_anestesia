
import streamlit as st
from fpdf import FPDF
import datetime
import io
import tempfile
from streamlit_drawable_canvas import st_canvas
import numpy as np
from PIL import Image

def create_checkbox_table(pdf, section_title, items):
    if pdf.get_y() > 260:
        pdf.add_page()
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, section_title, ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(140, 7, "", 0)
    pdf.cell(15, 7, "OK", 1, 0, "C")
    pdf.cell(15, 7, "NO", 1, 0, "C")
    pdf.cell(15, 7, "N/A", 1, 1, "C")
    for item, value in items:
        if pdf.get_y() > 270:
            pdf.add_page()
        pdf.cell(140, 7, item, 1)
        pdf.cell(15, 7, "X" if value == "OK" else "", 1, 0, "C")
        pdf.cell(15, 7, "X" if value == "NO" else "", 1, 0, "C")
        pdf.cell(15, 7, "X" if value == "N/A" else "", 1, 1, "C")
    pdf.ln(3)

def add_signature_to_pdf(pdf_obj, canvas_result, x, y):
    if canvas_result.image_data is not None:
        img = Image.fromarray(canvas_result.image_data.astype(np.uint8))
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            tmp_file.write(img_byte_arr.read())
            tmp_path = tmp_file.name
        img_width_mm = 50
        img_height_mm = (img.height / img.width) * img_width_mm
        max_height = 30
        if img_height_mm > max_height:
            img_height_mm = max_height
            img_width_mm = (img.width / img.height) * img_height_mm
        try:
            pdf_obj.image(tmp_path, x=x, y=y, w=img_width_mm, h=img_height_mm)
        except:
            pass

def main():
    st.title("Pauta de Mantenimiento Preventivo - Máquina de Anestesia")
    marca = st.text_input("Marca")
    modelo = st.text_input("Modelo")
    sn = st.text_input("S/N")
    inventario = st.text_input("N° Inventario")
    fecha = st.date_input("Fecha", value=datetime.date.today())
    ubicacion = st.text_input("Ubicación")

    def checklist(title, items):
        st.subheader(title)
        respuestas = []
        for item in items:
            col1, col2 = st.columns([5, 3])
            with col1:
                st.markdown(item)
            with col2:
                seleccion = st.radio("", ["OK", "NO", "N/A"], horizontal=True, key=item)
            respuestas.append((item, seleccion))
        return respuestas

    chequeo_visual = checklist("1. Chequeo Visual", [
        "1.1. Carcasa Frontal y Trasera",
        "1.2. Estado de Software",
        "1.3. Panel frontal",
        "1.4. Batería de respaldo"
    ])

    sistema_alta = checklist("2. Sistema de Alta Presión", [
        "2.1. Chequeo de yugo de O2, N2O, Aire",
        "2.2. Revisión o reemplazo de empaquetadura de yugo",
        "2.3. Verificación de entrada de presión",
        "2.4. Revisión y calibración de válvulas de flujometro de O2, N2O, Aire"
    ])

    sistema_baja = checklist("3. Sistema de baja presión", [
        "3.1. Revisión y calibración de válvula de flujómetro de N2O",
        "3.2. Revisión y calibración de válvula de flujometro de O2",
        "3.3. Revisión y calibración de válvula de flujometro de Aire",
        "3.4. Chequeo de fugas",
        "3.5. Verificación de flujos",
        "3.6. Verificación de regulador de 2da etapa",
        "3.7. Revisión de sistema de corte N2O/Aire por falta de O2",
        "3.8. Revisión de sistema proporción de O2/N2O",
        "3.9. Revisión de manifold de vaporizadores"
    ])

    sistema_absorbedor = checklist("4. Sistema absorbedor", [
        "4.1. Revisión o reemplazo de empaquetadura de canister",
        "4.2. Revisión de válvula APL",
        "4.3. Verificación de manómetro de presión de vía aérea",
        "4.4. Revisión de válvula inhalatoria",
        "4.5. Revisión de válvula exhalatoria",
        "4.6. Chequeo de fugas",
        "4.7. Hermeticidad"
    ])

    ventilador_mecanico = checklist("5. Ventilador mecánico", [
        "5.1. Porcentaje de oxígeno",
        "5.2. Volumen corriente y volumen minuto",
        "5.3. Presión de vía aérea",
        "5.4. Frecuencia respiratoria",
        "5.5. Modo ventilatorio",
        "5.6. Alarmas",
        "5.7. Calibración de celda de oxígeno a 21% y al 100%",
        "5.8. Calibración de sensores de flujo"
    ])

    seguridad_electrica = checklist("6. Seguridad eléctrica", [
        "6.1. Corriente de fuga",
        "6.2. Tierra de protección",
        "6.3. Aislación"
    ])

    st.subheader("7. Instrumentos de análisis")
    eq1 = st.text_input("Equipo 1")
    marca1 = st.text_input("Marca 1")
    modelo1 = st.text_input("Modelo 1")
    serie1 = st.text_input("N° Serie 1")
    eq2 = st.text_input("Equipo 2")
    marca2 = st.text_input("Marca 2")
    modelo2 = st.text_input("Modelo 2")
    serie2 = st.text_input("N° Serie 2")
    observaciones = st.text_area("Observaciones")
    observaciones_interno = st.text_area("Observaciones (uso interno)")
    operativo = st.radio("¿Equipo operativo?", ["SI", "NO"])
    tecnico = st.text_input("Nombre Técnico/Ingeniero")
    empresa = st.text_input("Empresa Responsable")

    st.subheader("Firmas")
    st.write("Firma de Técnico Encargado:")
    canvas_result_tecnico = st_canvas(fill_color="rgba(255, 165, 0, 0.3)", stroke_width=2, stroke_color="#000000", background_color="#EEEEEE", height=150, width=300, drawing_mode="freedraw", key="canvas_tecnico")
    st.write("Firma de Ingeniería Clínica:")
    canvas_result_ingenieria = st_canvas(fill_color="rgba(255, 165, 0, 0.3)", stroke_width=2, stroke_color="#000000", background_color="#EEEEEE", height=150, width=300, drawing_mode="freedraw", key="canvas_ingenieria")
    st.write("Firma de Personal Clínico:")
    canvas_result_clinico = st_canvas(fill_color="rgba(255, 165, 0, 0.3)", stroke_width=2, stroke_color="#000000", background_color="#EEEEEE", height=150, width=300, drawing_mode="freedraw", key="canvas_clinico")

    if st.button("Generar PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.image("logo_hrt_final.jpg", x=10, y=6, w=45)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "HOSPITAL REGIONAL DE TALCA", ln=True, align="C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 8, "UNIDAD DE INGENIERÍA CLÍNICA", ln=True, align="C")
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 10, "PAUTA MANTENIMIENTO PREVENTIVO MAQUINA ANESTESIA (Ver 2)", ln=True, align="C")
        pdf.ln(5)

        for label, val in [("MARCA", marca), ("MODELO", modelo), ("S/N", sn), ("N° INVENTARIO", inventario), ("UBICACIÓN", ubicacion), ("FECHA", fecha.strftime("%d/%m/%Y"))]:
            pdf.cell(0, 7, f"{label}: {val}", ln=True)
        pdf.ln(5)

        for title, data in [
            ("1. Chequeo Visual", chequeo_visual),
            ("2. Sistema de Alta Presión", sistema_alta),
            ("3. Sistema de Baja Presión", sistema_baja),
            ("4. Sistema absorbedor", sistema_absorbedor),
            ("5. Ventilador mecánico", ventilador_mecanico),
            ("6. Seguridad eléctrica", seguridad_electrica)
        ]:
            create_checkbox_table(pdf, title, data)

        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 7, "7. Instrumentos de análisis", ln=True)
        pdf.set_font("Arial", "", 10)
        for equipo, marca, modelo, serie in [(eq1, marca1, modelo1, serie1), (eq2, marca2, modelo2, serie2)]:
            pdf.cell(0, 7, f"Equipo: {equipo} | Marca: {marca} | Modelo: {modelo} | N° Serie: {serie}", ln=True)

        pdf.ln(5)
        pdf.multi_cell(0, 6, f"Observaciones: {observaciones}")
        pdf.multi_cell(0, 6, f"Observaciones (uso interno): {observaciones_interno}")
        pdf.cell(0, 7, f"Equipo Operativo: {operativo}", ln=True)
        pdf.cell(0, 7, f"Nombre Técnico: {tecnico}", ln=True)
        pdf.cell(0, 7, f"Empresa Responsable: {empresa}", ln=True)

        pdf.add_page()

        x_positions = [20, 85, 150]
        y_firma = 50
        add_signature_to_pdf(pdf, canvas_result_tecnico, x_positions[0], y_firma)
        add_signature_to_pdf(pdf, canvas_result_ingenieria, x_positions[1], y_firma)
        add_signature_to_pdf(pdf, canvas_result_clinico, x_positions[2], y_firma)

        pdf.set_y(y_firma + 30)
        for i, label in enumerate(["TÉCNICO ENCARGADO", "INGENIERÍA CLÍNICA", "PERSONAL CLÍNICO"]):
            pdf.set_xy(x_positions[i], pdf.get_y())
            pdf.cell(60, 6, "_________________________", 0, 2, 'C')
            pdf.cell(60, 6, label, 0, 0, 'C')

        output = io.BytesIO(pdf.output(dest="S").encode("latin1"))
        st.download_button("Descargar PDF", output.getvalue(), file_name=f"MP_Anestesia_{sn}.pdf", mime="application/pdf")

if __name__ == "__main__":
    main()
