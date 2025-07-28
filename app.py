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

def add_signature_to_pdf(pdf_obj, canvas_result, x_start_of_box, y):
    if canvas_result.image_data is not None:
        img_array = canvas_result.image_data.astype(np.uint8)
        img = Image.fromarray(img_array)

        # Convert to grayscale for easier background detection
        gray_img = img.convert('L')
        
        # Determine the background color's grayscale value. Since background_color="#EEEEEE" (light gray)
        # We can assume anything close to this value is background.
        # A simple threshold can separate the signature (darker) from the background.
        # Let's say we consider anything darker than 230 (on a 0-255 scale) as part of the signature.
        threshold = 230 
        
        # Get coordinates of all pixels that are darker than the threshold
        coords = np.argwhere(np.array(gray_img) < threshold)
        
        if coords.size == 0:
            # No significant drawing detected, skip adding the image
            return
        
        # Find the bounding box of these pixels
        min_y, min_x = coords.min(axis=0)
        max_y, max_x = coords.max(axis=0)
        
        # Crop the image based on the detected bounding box
        cropped_img = img.crop((min_x, min_y, max_x + 1, max_y + 1))
        
        # Convert to RGB if it's still RGBA after cropping (it should be fine if original was RGB or if we convert later)
        if cropped_img.mode == 'RGBA':
            cropped_img = cropped_img.convert('RGB')
        
        img_byte_arr = io.BytesIO()
        cropped_img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            tmp_file.write(img_byte_arr.read())
            tmp_path = tmp_file.name
        
        # Define a desired width for the signature image in PDF
        desired_img_width_mm = 50 
        # Calculate height based on the cropped image's aspect ratio
        img_height_mm = (cropped_img.height / cropped_img.width) * desired_img_width_mm
        
        # Ensure signature doesn't exceed a max height
        max_height = 30
        if img_height_mm > max_height:
            img_height_mm = max_height
            # Adjust width to maintain aspect ratio with the new max height
            desired_img_width_mm = (cropped_img.width / cropped_img.height) * img_height_mm 

        # Calculate x to center the image within a 60mm wide "signature box" area
        center_of_area_x = x_start_of_box + (60 / 2) # 60mm is the conceptual width for each signature
        image_x = center_of_area_x - (desired_img_width_mm / 2)
        
        try:
            pdf_obj.image(tmp_path, x=image_x, y=y, w=desired_img_width_mm, h=img_height_mm)
        except Exception as e:
            st.error(f"Error al añadir imagen: {e}")

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
        # You'll need to make sure 'logo_hrt_final.jpg' is in the same directory as your script
        # or provide a full path to it.
        try:
            pdf.image("logo_hrt_final.jpg", x=10, y=6, w=45)
        except Exception as e:
            st.warning(f"No se pudo cargar el logo: {e}. Asegúrate de que 'logo_hrt_final.jpg' esté en la misma carpeta.")

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "HOSPITAL REGIONAL DE TALCA", ln=True, align="C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 8, "UNIDAD DE INGENIERÍA CLÍNICA", ln=True, align="C")
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 10, "PAUTA MANTENIMIENTO PREVENTIVO MAQUINA ANESTESIA", ln=True, align="C")
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
        
        # Define the x positions for the start of each signature area.
        # These are the left-most points of where each signature's conceptual 60mm box starts.
        x_positions_for_signature_area = [20, 80, 140] 
        y_firma_image = 60 # Y position for the top of the signature image
        
        # Add signatures
        add_signature_to_pdf(pdf, canvas_result_tecnico, x_positions_for_signature_area[0], y_firma_image)
        add_signature_to_pdf(pdf, canvas_result_ingenieria, x_positions_for_signature_area[1], y_firma_image)
        add_signature_to_pdf(pdf, canvas_result_clinico, x_positions_for_signature_area[2], y_firma_image)

        # Move down to place the lines and labels
        # Assuming signature image can be up to 30mm tall, we place the line below that.
        y_firma_text = y_firma_image + 20 
        
        # Add signature lines and labels, centered within a 60mm width for each
        for i, label in enumerate(["TÉCNICO ENCARGADO", "INGENIERÍA CLÍNICA", "PERSONAL CLÍNICO"]):
            # Set the Y position for the current line of text
            pdf.set_y(y_firma_text)
            # Set X position to the start of the current signature area
            pdf.set_x(x_positions_for_signature_area[i]) 
            pdf.cell(60, 6, "_________________________", 0, 2, 'C') # Centered line, move to next line (within the 60mm cell)
            pdf.set_x(x_positions_for_signature_area[i]) # Reset X for the label
            pdf.cell(60, 6, label, 0, 0, 'C') # Centered label, stay on same line

        output = io.BytesIO(pdf.output(dest="S").encode("latin1"))
        st.download_button("Descargar PDF", output.getvalue(), file_name=f"MP_Anestesia_{sn}.pdf", mime="application/pdf")

if __name__ == "__main__":
    main()
