import streamlit as st
from fpdf import FPDF
import datetime
import io
import tempfile
from streamlit_drawable_canvas import st_canvas
import numpy as np
from PIL import Image

def get_table_height(section_title, items):
    # Calcula la altura que ocupará una tabla.
    # Título (1 línea) + encabezado (1 línea) + filas (1 línea por ítem)
    # Se añade un pequeño margen
    return 5 + 5 + (5 * len(items)) + 2

def create_checkbox_table(pdf, section_title, items, x_pos, y_pos):
    item_width = 100
    ok_width = 15
    no_width = 15
    na_width = 15
    
    # Título de la sección
    pdf.set_xy(x_pos, y_pos)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(item_width + ok_width + no_width + na_width, 5, section_title, ln=1, align='L')
    y_pos += 5

    # Encabezado de la tabla
    pdf.set_xy(x_pos, y_pos)
    pdf.set_font("Arial", "", 10)
    pdf.cell(item_width, 5, "", 1, 0)
    pdf.cell(ok_width, 5, "OK", 1, 0, "C")
    pdf.cell(no_width, 5, "NO", 1, 0, "C")
    pdf.cell(na_width, 5, "N/A", 1, 1, "C")
    y_pos += 5
    
    # Filas de la tabla
    for item, value in items:
        pdf.set_xy(x_pos, y_pos)
        pdf.cell(item_width, 5, item, 1)
        pdf.cell(ok_width, 5, "X" if value == "OK" else "", 1, 0, "C")
        pdf.cell(no_width, 5, "X" if value == "NO" else "", 1, 0, "C")
        pdf.cell(na_width, 5, "X" if value == "N/A" else "", 1, 1, "C")
        y_pos += 5
    
    return y_pos + 2 # Retornar la posición y para la siguiente tabla

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
        
        desired_img_width_mm = 50
        img_height_mm = (cropped_img.height / cropped_img.width) * desired_img_width_mm
        
        max_height = 30
        if img_height_mm > max_height:
            img_height_mm = max_height
            desired_img_width_mm = (cropped_img.width / cropped_img.height) * img_height_mm

        center_of_area_x = x_start_of_box + (60 / 2)
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
        canvas_result_tecnico = st_canvas(fill_color="rgba(255, 165, 0, 0.3)", stroke_width=2, stroke_color="#000000", background_color="#EEEEEE", height=150, width=200, drawing_mode="freedraw", key="canvas_tecnico")

    with col_ingenieria:
        st.write("Ingeniería Clínica:")
        canvas_result_ingenieria = st_canvas(fill_color="rgba(255, 165, 0, 0.3)", stroke_width=2, stroke_color="#000000", background_color="#EEEEEE", height=150, width=200, drawing_mode="freedraw", key="canvas_ingenieria")

    with col_clinico:
        st.write("Personal Clínico:")
        canvas_result_clinico = st_canvas(fill_color="rgba(255, 165, 0, 0.3)", stroke_width=2, stroke_color="#000000", background_color="#EEEEEE", height=150, width=200, drawing_mode="freedraw", key="canvas_clinico")


    if st.button("Generar PDF"):
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        
        try:
            pdf.image("logo_hrt_final.jpg", x=10, y=6, w=45)
        except Exception as e:
            st.warning(f"No se pudo cargar el logo: {e}. Asegúrate de que 'logo_hrt_final.jpg' esté en la misma carpeta.")

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "HOSPITAL REGIONAL DE TALCA", ln=1, align="C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 6, "UNIDAD DE INGENIERÍA CLÍNICA", ln=1, align="C")
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, "PAUTA MANTENIMIENTO PREVENTIVO MAQUINA ANESTESIA", ln=1, align="C")
        pdf.ln(3)
        
        pdf.set_font("Arial", "", 10)
        info_block = [
            f"Marca: {marca}",
            f"Modelo: {modelo}",
            f"Número de Serie: {sn}",
            f"Número de Inventario: {inventario}",
            f"Ubicación: {ubicacion}",
            f"Fecha: {fecha.strftime('%d/%m/%Y')}"
        ]
        
        for line in info_block:
            pdf.cell(0, 5, line, ln=1)
        pdf.ln(3)

        # ----------------------------------------------------
        # NUEVO ENFOQUE: Distribuir las tablas en dos columnas
        # ----------------------------------------------------
        x_pos_col1 = 10
        x_pos_col2 = 145
        y_pos_start = pdf.get_y()

        # 1. Crear una lista de todas las tablas con su altura
        all_tables = [
            {"title": "1. Chequeo Visual", "items": chequeo_visual, "height": get_table_height("1. Chequeo Visual", chequeo_visual)},
            {"title": "2. Sistema de Alta Presión", "items": sistema_alta, "height": get_table_height("2. Sistema de Alta Presión", sistema_alta)},
            {"title": "3. Sistema de Baja Presión", "items": sistema_baja, "height": get_table_height("3. Sistema de Baja Presión", sistema_baja)},
            {"title": "4. Sistema absorbedor", "items": sistema_absorbedor, "height": get_table_height("4. Sistema absorbedor", sistema_absorbedor)},
            {"title": "5. Ventilador mecánico", "items": ventilador_mecanico, "height": get_table_height("5. Ventilador mecánico", ventilador_mecanico)},
            {"title": "6. Seguridad eléctrica", "items": seguridad_electrica, "height": get_table_height("6. Seguridad eléctrica", seguridad_electrica)},
        ]
        
        # 2. Distribuir las tablas en dos columnas de forma equilibrada
        col1_tables = []
        col2_tables = []
        col1_height = 0
        col2_height = 0
        
        for table in all_tables:
            if col1_height <= col2_height:
                col1_tables.append(table)
                col1_height += table["height"]
            else:
                col2_tables.append(table)
                col2_height += table["height"]

        # 3. Dibujar las tablas en la primera columna
        y_pos_col1 = y_pos_start
        for table in col1_tables:
            y_pos_col1 = create_checkbox_table(pdf, table["title"], table["items"], x_pos_col1, y_pos_col1)
            
        # 4. Dibujar las tablas en la segunda columna
        y_pos_col2 = y_pos_start
        for table in col2_tables:
            y_pos_col2 = create_checkbox_table(pdf, table["title"], table["items"], x_pos_col2, y_pos_col2)
            
        # ----------------------------------------------------
        # Continuar con el resto del contenido
        # ----------------------------------------------------
        max_y = max(y_pos_col1, y_pos_col2)
        pdf.set_y(max_y)
        
        pdf.set_x(x_pos_col1)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, "7. Instrumentos de análisis", ln=1)
        pdf.set_x(x_pos_col1)
        pdf.set_font("Arial", "", 10)

        if st.session_state.analisis_equipos and any(equipo.get('equipo') or equipo.get('marca') or equipo.get('modelo') or equipo.get('serie') for equipo in st.session_state.analisis_equipos):
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Arial", "B", 9)
            pdf.cell(50, 6, "Equipo", 1, 0, "C", 1)
            pdf.cell(50, 6, "Marca", 1, 0, "C", 1)
            pdf.cell(50, 6, "Modelo", 1, 0, "C", 1)
            pdf.cell(40, 6, "N° Serie", 1, 1, "C", 1)
            
            pdf.set_font("Arial", "", 9)
            for equipo_data in st.session_state.analisis_equipos:
                equipo = equipo_data.get('equipo', '')
                marca_equipo = equipo_data.get('marca', '')
                modelo_equipo = equipo_data.get('modelo', '')
                serie_equipo = equipo_data.get('serie', '')
                
                if equipo or marca_equipo or modelo_equipo or serie_equipo:
                    pdf.cell(50, 6, equipo, 1, 0, "L")
                    pdf.cell(50, 6, marca_equipo, 1, 0, "L")
                    pdf.cell(50, 6, modelo_equipo, 1, 0, "L")
                    pdf.cell(40, 6, serie_equipo, 1, 1, "L")

        pdf.ln(3)
        pdf.set_x(x_pos_col1)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 4, f"Observaciones: {observaciones}")
        pdf.set_x(x_pos_col1)
        pdf.multi_cell(0, 4, f"Observaciones (uso interno): {observaciones_interno}")
        
        pdf.set_x(x_pos_col1)
        pdf.cell(0, 4, f"Equipo Operativo: {operativo}", ln=1)
        pdf.set_x(x_pos_col1)
        pdf.cell(0, 4, f"Nombre Técnico: {tecnico}", ln=1)
        pdf.set_x(x_pos_col1)
        pdf.cell(0, 4, f"Empresa Responsable: {empresa}", ln=1)
        
        pdf.ln(10)
        
        x_positions_for_signature_area = [20, 120, 220]
        y_firma_start = pdf.get_y()
        y_firma_image = y_firma_start + 5
        
        add_signature_to_pdf(pdf, canvas_result_tecnico, x_positions_for_signature_area[0], y_firma_image)
        add_signature_to_pdf(pdf, canvas_result_ingenieria, x_positions_for_signature_area[1], y_firma_image)
        add_signature_to_pdf(pdf, canvas_result_clinico, x_positions_for_signature_area[2], y_firma_image)

        y_firma_text = y_firma_image + 30
        
        pdf.set_y(y_firma_text)
        pdf.set_x(x_positions_for_signature_area[0])
        pdf.cell(60, 5, "_________________________", 0, 0, 'C')
        pdf.set_x(x_positions_for_signature_area[1])
        pdf.cell(60, 5, "_________________________", 0, 0, 'C')
        pdf.set_x(x_positions_for_signature_area[2])
        pdf.cell(60, 5, "_________________________", 0, 1, 'C')
        
        pdf.set_y(pdf.get_y() - 1)
        pdf.set_x(x_positions_for_signature_area[0])
        pdf.cell(60, 5, "TÉCNICO ENCARGADO", 0, 0, 'C')
        pdf.set_x(x_positions_for_signature_area[1])
        pdf.cell(60, 5, "INGENIERÍA CLÍNICA", 0, 0, 'C')
        pdf.set_x(x_positions_for_signature_area[2])
        pdf.cell(60, 5, "PERSONAL CLÍNICO", 0, 1, 'C')

        output = io.BytesIO(pdf.output(dest="S").encode("latin-1"))
        st.download_button("Descargar PDF", output.getvalue(), file_name=f"MP_Anestesia_{sn}.pdf", mime="application/pdf")

if __name__ == "__main__":
    main()
