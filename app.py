import streamlit as st
from fpdf import FPDF
import datetime
import io
import tempfile
from streamlit_drawable_canvas import st_canvas
import numpy as np
from PIL import Image

def create_checkbox_table(pdf, section_title, items, x_pos):
    pdf.set_x(x_pos)
    pdf.set_font("Arial", "B", 7)
    pdf.cell(0, 4, section_title, ln=True, border=0)
    
    pdf.set_x(x_pos)
    pdf.set_font("Arial", "", 6)
    pdf.cell(85, 3.5, "", 0)
    pdf.cell(10, 3.5, "OK", 1, 0, "C")
    pdf.cell(10, 3.5, "NO", 1, 0, "C")
    pdf.cell(10, 3.5, "N/A", 1, 1, "C")
    
    pdf.set_font("Arial", "", 6)
    for item, value in items:
        pdf.set_x(x_pos)
        pdf.cell(85, 3.5, item, 1, 0)
        pdf.cell(10, 3.5, "X" if value == "OK" else "", 1, 0, "C")
        pdf.cell(10, 3.5, "X" if value == "NO" else "", 1, 0, "C")
        pdf.cell(10, 3.5, "X" if value == "N/A" else "", 1, 1, "C")
    
    pdf.ln(2)

def add_signature_to_pdf(pdf_obj, canvas_result, x_start_of_box, y):
    if canvas_result.image_data is not None:
        img_array = canvas_result.image_data.astype(np.uint8)
        img = Image.fromarray(img_array)

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
        
        img_byte_arr = io.BytesIO()
        cropped_img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            tmp_file.write(img_byte_arr.read())
            tmp_path = tmp_file.name
        
        desired_img_width_mm = 40
        img_height_mm = (cropped_img.height / cropped_img.width) * desired_img_width_mm
        
        max_height = 20
        if img_height_mm > max_height:
            img_height_mm = max_height
            desired_img_width_mm = (cropped_img.width / cropped_img.height) * img_height_mm

        center_of_area_x = x_start_of_box + (50 / 2)
        image_x = center_of_area_x - (desired_img_width_mm / 2)
        
        try:
            pdf_obj.image(tmp_path, x=image_x, y=y, w=desired_img_width_mm, h=img_height_mm)
        except Exception as e:
            st.error(f"Error al añadir imagen: {e}")

def main():
    st.title("Pauta de Mantenimiento Preventivo - Máquina de Anestesia")
    marca = st.text_input("Marca")
    modelo = st.text_input("Modelo")
    sn = st.text_input("Número de Serie")
    inventario = st.text_input("Número de Inventario")
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

    if 'analisis_equipos' not in st.session_state:
        st.session_state.analisis_equipos = [{}]

    def add_equipo():
        st.session_state.analisis_equipos.append({})

    for i, equipo_data in enumerate(st.session_state.analisis_equipos):
        st.markdown(f"**Equipo {i+1}**")
        col_eq, col_btn = st.columns([0.9, 0.1])
        with col_eq:
            st.session_state.analisis_equipos[i]['equipo'] = st.text_input("Equipo", key=f"equipo_{i}")
            st.session_state.analisis_equipos[i]['marca'] = st.text_input("Marca", key=f"marca_{i}")
            st.session_state.analisis_equipos[i]['modelo'] = st.text_input("Modelo", key=f"modelo_{i}")
            st.session_state.analisis_equipos[i]['serie'] = st.text_input("Número de Serie", key=f"serie_{i}")
        
        if i > 0:
            with col_btn:
                st.write("")
                if st.button("−", key=f"remove_btn_{i}"):
                    st.session_state.analisis_equipos.pop(i)
                    st.experimental_rerun()
    
    st.button("Agregar Equipo +", on_click=add_equipo)

    observaciones = st.text_area("Observaciones")
    observaciones_interno = st.text_area("Observaciones (uso interno)")
    operativo = st.radio("¿Equipo operativo?", ["SI", "NO"])
    tecnico = st.text_input("Nombre Técnico/Ingeniero")
    empresa = st.text_input("Empresa Responsable")

    st.subheader("Firmas")
    col_tecnico, col_ingenieria, col_clinico = st.columns(3)

    with col_tecnico:
        st.write("Técnico Encargado:")
        canvas_result_tecnico = st_canvas(fill_color="rgba(255, 165, 0, 0.3)", stroke_width=2, stroke_color="#000000", background_color="#EEEEEE", height=150, width=300, drawing_mode="freedraw", key="canvas_tecnico")

    with col_ingenieria:
        st.write("Ingeniería Clínica:")
        canvas_result_ingenieria = st_canvas(fill_color="rgba(255, 165, 0, 0.3)", stroke_width=2, stroke_color="#000000", background_color="#EEEEEE", height=150, width=300, drawing_mode="freedraw", key="canvas_ingenieria")

    with col_clinico:
        st.write("Personal Clínico:")
        canvas_result_clinico = st_canvas(fill_color="rgba(255, 165, 0, 0.3)", stroke_width=2, stroke_color="#000000", background_color="#EEEEEE", height=150, width=300, drawing_mode="freedraw", key="canvas_clinico")

    if st.button("Generar PDF"):
        pdf = FPDF('L', 'mm', 'A4')
        pdf.add_page()
        
        # --- ENCABEZADO Y TÍTULOS CENTRADOS ---
        try:
            pdf.image("logo_hrt_final.jpg", x=22, y=6, w=40)
        except Exception as e:
            st.warning(f"No se pudo cargar el logo: {e}. Asegúrate de que 'logo_hrt_final.jpg' esté en la misma carpeta.")
        
        y_title_start = 6
        pdf.set_y(y_title_start)
        
        pdf.set_font("Arial", "B", 9)
        pdf.cell(0, 4, "HOSPITAL REGIONAL DE TALCA", 0, 1, "C")
        
        pdf.set_font("Arial", "", 7)
        pdf.cell(0, 3, "UNIDAD DE INGENIERÍA CLÍNICA", 0, 1, "C")
        
        pdf.set_font("Arial", "B", 8)
        pdf.cell(0, 4, "PAUTA MANTENIMIENTO PREVENTIVO MAQUINA ANESTESIA", 0, 1, "C")
        
        y_column_start_left = pdf.get_y() + 15
        y_column_start_right = pdf.get_y() + 5
        
        # --- COLUMNA IZQUIERDA ---
        pdf.set_y(y_column_start_left)
        pdf.set_x(22)
        pdf.set_font("Arial", "", 7)
        pdf.cell(0, 3.5, f"Marca: {marca}", 0, 1)
        pdf.set_x(22)
        pdf.cell(0, 3.5, f"Modelo: {modelo}", 0, 1)
        pdf.set_x(22)
        pdf.cell(0, 3.5, f"Número de Serie: {sn}", 0, 1)
        pdf.set_x(22)
        pdf.cell(0, 3.5, f"Número de Inventario: {inventario}", 0, 1)
        pdf.set_x(22)
        pdf.cell(0, 3.5, f"Ubicación: {ubicacion}", 0, 1)
        pdf.set_x(22)
        pdf.cell(0, 3.5, f"Fecha: {fecha.strftime('%d/%m/%Y')}", 0, 1)
        pdf.ln(2)

        create_checkbox_table(pdf, "1. Chequeo Visual", chequeo_visual, x_pos=22)
        create_checkbox_table(pdf, "2. Sistema de Alta Presión", sistema_alta, x_pos=22)
        create_checkbox_table(pdf, "3. Sistema de Baja Presión", sistema_baja, x_pos=22)
        create_checkbox_table(pdf, "4. Sistema absorbedor", sistema_absorbedor, x_pos=22)
        
        # --- COLUMNA DERECHA ---
        pdf.set_y(y_column_start_right) 
        
        create_checkbox_table(pdf, "5. Ventilador mecánico", ventilador_mecanico, x_pos=160)
        create_checkbox_table(pdf, "6. Seguridad eléctrica", seguridad_electrica, x_pos=160)
        
        # Sección de Instrumentos de análisis (Columna Derecha)
        pdf.set_x(160)
        pdf.set_font("Arial", "B", 7)
        pdf.cell(0, 4, "7. Instrumentos de análisis", ln=True)
        
        if st.session_state.analisis_equipos and any(equipo.get('equipo') or equipo.get('marca') or equipo.get('modelo') or equipo.get('serie') for equipo in st.session_state.analisis_equipos):
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Arial", "B", 6)
            pdf.set_x(160)
            pdf.cell(34, 3.5, "Equipo", 1, 0, "C", 1)
            pdf.cell(27, 3.5, "Marca", 1, 0, "C", 1)
            pdf.cell(27, 3.5, "Modelo", 1, 0, "C", 1)
            pdf.cell(27, 3.5, "N° Serie", 1, 1, "C", 1)
            
            pdf.set_font("Arial", "", 6)
            for equipo_data in st.session_state.analisis_equipos:
                equipo = equipo_data.get('equipo', '')
                marca_equipo = equipo_data.get('marca', '')
                modelo_equipo = equipo_data.get('modelo', '')
                serie_equipo = equipo_data.get('serie', '')
                
                if equipo or marca_equipo or modelo_equipo or serie_equipo:
                    pdf.set_x(160)
                    pdf.cell(34, 3.5, equipo, 1, 0, "L")
                    pdf.cell(27, 3.5, marca_equipo, 1, 0, "L")
                    pdf.cell(27, 3.5, modelo_equipo, 1, 0, "L")
                    pdf.cell(27, 3.5, serie_equipo, 1, 1, "L")
        
        pdf.ln(2)

        # Observaciones y datos del técnico
        pdf.set_x(160)
        pdf.set_font("Arial", "B", 7)
        pdf.cell(0, 3.5, "Observaciones:", ln=True)
        pdf.set_font("Arial", "", 7)
        pdf.set_x(160)
        # Se define un ancho de 115mm para que el texto se alinee con las tablas
        pdf.multi_cell(115, 3.5, f"{observaciones}")
        pdf.ln(1)
        
        pdf.set_x(160)
        pdf.set_font("Arial", "B", 7)
        pdf.cell(0, 3.5, "Observaciones (uso interno):", ln=True)
        pdf.set_font("Arial", "", 7)
        pdf.set_x(160)
        # Se define un ancho de 115mm para que el texto se alinee con las tablas
        pdf.multi_cell(115, 3.5, f"{observaciones_interno}")
        pdf.ln(1)
        
        pdf.set_x(160)
        pdf.cell(0, 3.5, f"Equipo Operativo: {operativo}", ln=True)
        
        pdf.set_x(160)
        pdf.cell(0, 3.5, f"Nombre Técnico/Ingeniero: {tecnico}", 0, 1)
        pdf.set_x(160)
        pdf.cell(0, 3.5, f"Empresa Responsable: {empresa}", 0, 1)
        
        # --- SECCIÓN DE FIRMAS ---
        pdf.ln(5) 
        
        x_tecnico = 160 + (117 / 3 / 2) - (50 / 2)
        x_ingenieria = 160 + (117 / 3) + (117 / 3 / 2) - (50 / 2)
        x_clinico = 160 + (117 / 3 * 2) + (117 / 3 / 2) - (50 / 2)

        y_firma_start = pdf.get_y()
        y_firma_image = y_firma_start + 5
        
        add_signature_to_pdf(pdf, canvas_result_tecnico, x_tecnico, y_firma_image)
        add_signature_to_pdf(pdf, canvas_result_ingenieria, x_ingenieria, y_firma_image)
        add_signature_to_pdf(pdf, canvas_result_clinico, x_clinico, y_firma_image)

        y_firma_text = y_firma_start + 25
        pdf.set_y(y_firma_text)
        
        pdf.set_x(x_tecnico)
        pdf.cell(50, 4, "_________________________", 0, 0, 'C')
        pdf.set_x(x_ingenieria)
        pdf.cell(50, 4, "_________________________", 0, 0, 'C')
        pdf.set_x(x_clinico)
        pdf.cell(50, 4, "_________________________", 0, 1, 'C')
        
        pdf.set_y(pdf.get_y() - 1)
        pdf.set_font("Arial", "", 7)
        pdf.set_x(x_tecnico)
        pdf.cell(50, 4, "TÉCNICO ENCARGADO", 0, 0, 'C')
        pdf.set_x(x_ingenieria)
        pdf.cell(50, 4, "INGENIERÍA CLÍNICA", 0, 0, 'C')
        pdf.set_x(x_clinico)
        pdf.cell(50, 4, "PERSONAL CLÍNICO", 0, 1, 'C')

        output = io.BytesIO(pdf.output(dest="S").encode("latin1"))
        st.download_button("Descargar PDF", output.getvalue(), file_name=f"MP_Anestesia_{sn}.pdf", mime="application/pdf")

if __name__ == "__main__":
    main()
