import streamlit as st
from fpdf import FPDF
import datetime
import io
import tempfile
from streamlit_drawable_canvas import st_canvas
import numpy as np
from PIL import Image

# ========= Pie de página =========
FOOTER_LINES = [
    "PAUTA MANTENIMIENTO PREVENTIVO MAQUINA ANESTESIA (Ver 2)",
    "UNIDAD DE INGENIERÍA CLÍNICA",
    "HOSPITAL REGIONAL DE TALCA",
]

class PDF(FPDF):
    def __init__(self, *args, footer_lines=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._footer_lines = footer_lines or []

    def footer(self):
        if not self._footer_lines:
            return

        # Ubicar ~15 mm sobre el borde inferior
        self.set_y(-15)
        y = self.get_y()

        # Fuente igual a subtítulos
        subtitle_fs = 6.2
        line_h = 3.4

        # Línea superior EXACTA al largo del primer texto
        first_line = self._footer_lines[0]
        self.set_font("Arial", "B", subtitle_fs)
        text_w = self.get_string_width(first_line)
        x_left = self.l_margin
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.2)
        self.line(x_left, y, x_left + text_w, y)

        # Texto del pie: interlineado 3.4 mm
        self.ln(1.6)
        self.set_x(self.l_margin)
        self.cell(0, line_h, first_line, ln=1, align="L")

        self.set_font("Arial", "", subtitle_fs)
        for line in self._footer_lines[1:]:
            self.set_x(self.l_margin)
            self.cell(0, line_h, line, ln=1, align="L")

# ========= utilidades =========
def _crop_signature(canvas_result):
    if canvas_result.image_data is None:
        return None
    img_array = canvas_result.image_data.astype(np.uint8)
    img = Image.fromarray(img_array)
    gray_img = img.convert('L')
    threshold = 230
    coords = np.argwhere(np.array(gray_img) < threshold)
    if coords.size == 0:
        return None
    min_y, min_x = coords.min(axis=0)
    max_y, max_x = coords.max(axis=0)
    cropped_img = img.crop((min_x, min_y, max_x + 1, max_y + 1))
    if cropped_img.mode == 'RGBA':
        cropped_img = cropped_img.convert('RGB')
    img_byte_arr = io.BytesIO()
    cropped_img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def add_signature_inline(pdf_obj, canvas_result, x, y, w_mm=65, h_mm=20):
    """Dibuja la firma en (x, y). Ajusta w_mm/h_mm si necesitas otro tamaño."""
    img_byte_arr = _crop_signature(canvas_result)
    if not img_byte_arr:
        return
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
        tmp_file.write(img_byte_arr.read())
        tmp_path = tmp_file.name
    try:
        img = Image.open(tmp_path)
        img_w = w_mm
        img_h = (img.height / img.width) * img_w
        if img_h > h_mm:
            img_h = h_mm
            img_w = (img.width / img.height) * img_h
        pdf_obj.image(tmp_path, x=x, y=y, w=img_w, h=img_h)
    except Exception as e:
        st.error(f"Error al añadir imagen: {e}")

def draw_si_no_boxes(pdf, x, y, selected, size=4.5, gap=4, text_gap=1.5, label_w=36):
    pdf.set_font("Arial", "", 7.5)
    pdf.set_xy(x, y)
    pdf.cell(label_w, size, "Equipo Operativo:", 0, 0)
    x_box_si = x + label_w + 2
    pdf.rect(x_box_si, y, size, size)
    pdf.set_xy(x_box_si, y); pdf.cell(size, size, "X" if selected == "SI" else "", 0, 0, "C")
    pdf.set_xy(x_box_si + size + text_gap, y); pdf.cell(6, size, "SI", 0, 0)
    x_box_no = x_box_si + size + text_gap + 6 + gap
    pdf.rect(x_box_no, y, size, size)
    pdf.set_xy(x_box_no, y); pdf.cell(size, size, "X" if selected == "NO" else "", 0, 0, "C")
    pdf.set_xy(x_box_no + size + text_gap, y); pdf.cell(6, size, "NO", 0, 1)

def create_checkbox_table(pdf, section_title, items, x_pos, item_w, col_w,
                          row_h=3.4, head_fs=7.2, cell_fs=6.2,
                          indent_w=5.0, title_tab_spaces=2):
    title_prefix = " " * (title_tab_spaces * 2)
    pdf.set_x(x_pos)
    pdf.set_fill_color(230, 230, 230); pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", head_fs)
    pdf.cell(item_w, row_h, f"{title_prefix}{section_title}", border=1, ln=0, align="L", fill=True)
    pdf.set_font("Arial", "B", cell_fs)
    pdf.cell(col_w, row_h, "OK",  border=1, ln=0, align="C", fill=True)
    pdf.cell(col_w, row_h, "NO",  border=1, ln=0, align="C", fill=True)
    pdf.cell(col_w, row_h, "N/A", border=1, ln=1, align="C", fill=True)

    pdf.set_font("Arial", "", cell_fs)
    for item, value in items:
        pdf.set_x(x_pos)
        pdf.cell(indent_w, row_h, "", border=0, ln=0)
        pdf.cell(max(1, item_w - indent_w), row_h, item, border=0, ln=0, align="L")
        pdf.cell(col_w, row_h, "X" if value == "OK" else "", border=1, ln=0, align="C")
        pdf.cell(col_w, row_h, "X" if value == "NO" else "", border=1, ln=0, align="C")
        pdf.cell(col_w, row_h, "X" if value == "N/A" else "", border=1, ln=1, align="C")
    pdf.ln(1.6)

def create_rows_only(pdf, items, x_pos, item_w, col_w, row_h=3.4, cell_fs=6.2, indent_w=5.0):
    pdf.set_font("Arial", "", cell_fs)
    for item, value in items:
        pdf.set_x(x_pos)
        pdf.cell(indent_w, row_h, "", border=0, ln=0)
        pdf.cell(max(1, item_w - indent_w), row_h, item, border=0, ln=0, align="L")
        pdf.cell(col_w, row_h, "X" if value == "OK" else "", border=1, ln=0, align="C")
        pdf.cell(col_w, row_h, "X" if value == "NO" else "", border=1, ln=0, align="C")
        pdf.cell(col_w, row_h, "X" if value == "N/A" else "", border=1, ln=1, align="C")
    pdf.ln(1.4)

def draw_boxed_text_auto(pdf, x, y, w, min_h, title, text,
                          head_h=4.6, fs_head=7.2, fs_body=7.0,
                          body_line_h=3.2, padding=1.2):
    pdf.set_xy(x, y)
    pdf.set_fill_color(230, 230, 230); pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", fs_head)
    pdf.cell(w, head_h, title, border=1, ln=1, align="L", fill=True)

    y_body = y + head_h
    x_text = x + padding
    w_text = max(1, w - 2*padding)
    pdf.set_xy(x_text, y_body + padding)
    pdf.set_font("Arial", "", fs_body)
    if text:
        pdf.multi_cell(w_text, body_line_h, text, border=0, align="L")

    end_y = pdf.get_y()
    content_h = max(min_h, (end_y - (y_body + padding)) + padding)
    pdf.rect(x, y_body, w, content_h)
    pdf.set_y(y_body + content_h)
    
def draw_analisis_columns(pdf, x_start, y_start, col_w, data_list):
    """
    Dibuja los instrumentos de análisis en 1 o 2 columnas (2 instrumentos por columna).
    """
    row_h_field = 3.4
    label_w = 28.0
    text_w = col_w - label_w - 3.0
    TAB = "  " * 2
    
    def draw_column_no_lines(x, y, data):
        yy = y
        def field(lbl, val=""):
            nonlocal yy
            pdf.set_xy(x, yy); pdf.cell(label_w, row_h_field, f"{TAB}{lbl}:", border=0, ln=0)
            pdf.set_xy(x + label_w + 2, yy); pdf.cell(text_w, row_h_field, (val or ""), border=0, ln=1)
            yy += row_h_field
        field("EQUIPO",  data.get('equipo', ''))
        field("MARCA",   data.get('marca', ''))
        field("MODELO",  data.get('modelo', ''))
        field("NÚMERO DE SERIE", data.get('serie', ''))
        return yy
    
    num_equipos = len(data_list)
    y_current = y_start
    
    # Maneja de 1 a 2 equipos
    if num_equipos == 1:
        # Dibuja la única columna en la posición inicial (x_start)
        draw_column_no_lines(x_start, y_current, data_list[0])
        y_current = pdf.get_y() + 2 # Actualizar y_current después de la primera columna
    elif num_equipos >= 2:
        gap_cols = 6
        col_w2 = (col_w - gap_cols) / 2.0
        left_x = x_start
        right_x = x_start + col_w2 + gap_cols
        
        end_left = draw_column_no_lines(left_x, y_current, data_list[0])
        end_right = draw_column_no_lines(right_x, y_current, data_list[1])
        y_current = max(end_left, end_right) + 2

    # Maneja 3 o 4 equipos, dibujando una segunda fila de columnas
    if num_equipos >= 3:
        gap_cols = 6 # Definir de nuevo para este bloque, aunque ya existía
        col_w2 = (col_w - gap_cols) / 2.0
        left_x = x_start
        right_x = x_start + col_w2 + gap_cols
        
        end_left_row2 = draw_column_no_lines(left_x, y_current, data_list[2])
        end_right_row2 = 0
        if num_equipos >= 4:
            end_right_row2 = draw_column_no_lines(right_x, y_current, data_list[3])
        y_current = max(end_left_row2, end_right_row2) + 2
    
    return y_current

# ========= app =========
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

    st.subheader("    7. Instrumentos de análisis")
    if 'analisis_equipos' not in st.session_state:
        st.session_state.analisis_equipos = [{}]

    def add_equipo():
        st.session_state.analisis_equipos.append({})

    for i, _ in enumerate(st.session_state.analisis_equipos):
        st.markdown(f"**Equipo {i+1}**")
        col_eq, col_btn = st.columns([0.9, 0.1])
        with col_eq:
            st.session_state.analisis_equipos[i]['equipo'] = st.text_input("Equipo", key=f"equipo_{i}")
            st.session_state.analisis_equipos[i]['marca']  = st.text_input("Marca",  key=f"marca_{i}")
            st.session_state.analisis_equipos[i]['modelo'] = st.text_input("Modelo", key=f"modelo_{i}")
            st.session_state.analisis_equipos[i]['serie']  = st.text_input("Número de Serie", key=f"serie_{i}")
        if i > 0:
            with col_btn:
                st.write("")
                if st.button("−", key=f"remove_btn_{i}"):
                    st.session_state.analisis_equipos.pop(i)
                    st.experimental_rerun()
    st.button("Agregar Equipo +", on_click=add_equipo)

    observaciones = st.text_area("    Observaciones")
    observaciones_interno = st.text_area("    Observaciones (uso interno)")
    operativo = st.radio("¿Equipo operativo?", ["SI", "NO"])
    tecnico = st.text_input("Nombre Técnico/Ingeniero")
    empresa = st.text_input("Empresa Responsable")

    st.subheader("Firmas")
    col_tecnico, col_ingenieria, col_clinico = st.columns(3)
    with col_tecnico:
        st.write("Técnico Encargado:")
        canvas_result_tecnico = st_canvas(
            fill_color="rgba(255,165,0,0.3)", stroke_width=3,
            stroke_color="#000000", background_color="#EEEEEE",
            height=190, width=360, drawing_mode="freedraw",
            key="canvas_tecnico"
        )
    with col_ingenieria:
        st.write("Ingeniería Clínica:")
        canvas_result_ingenieria = st_canvas(
            fill_color="rgba(255,165,0,0.3)", stroke_width=3,
            stroke_color="#000000", background_color="#EEEEEE",
            height=190, width=360, drawing_mode="freedraw",
            key="canvas_ingenieria"
        )
    with col_clinico:
        st.write("Personal Clínico:")
        canvas_result_clinico = st_canvas(
            fill_color="rgba(255,165,0,0.3)", stroke_width=3,
            stroke_color="#000000", background_color="#EEEEEE",
            height=190, width=360, drawing_mode="freedraw",
            key="canvas_clinico"
        )

    if st.button("Generar PDF"):
        SIDE_MARGIN = 9
        TOP_MARGIN  = 4

        pdf = PDF('L', 'mm', 'A4', footer_lines=FOOTER_LINES)
        pdf.set_margins(SIDE_MARGIN, TOP_MARGIN, SIDE_MARGIN)
        pdf.set_auto_page_break(True, margin=TOP_MARGIN + 8)
        pdf.add_page()

        page_w = pdf.w
        COL_GAP = 6
        FIRST_COL_LEFT = SIDE_MARGIN
        usable_w = page_w - 2*SIDE_MARGIN
        col_total_w = (usable_w - COL_GAP) / 2.0
        COL_W = 12.0
        ITEM_W = max(62.0, col_total_w - 3 * COL_W)
        FIRST_TAB_RIGHT = FIRST_COL_LEFT + col_total_w
        SECOND_COL_LEFT = FIRST_TAB_RIGHT + COL_GAP

        # ======= ENCABEZADO =======
        logo_x, logo_y = 2, 2
        LOGO_W_MM = 60
        sep = 4
        title_text = "PAUTA DE MANTENCION DE MAQUINAS DE ANESTESIA"

        try:
            with Image.open("logo_hrt_final.jpg") as im:
                ratio = im.height / im.width if im.width else 1.0
            logo_h = LOGO_W_MM * ratio
        except Exception:
            logo_h = LOGO_W_MM * 0.8

        try:
            pdf.image("logo_hrt_final.jpg", x=logo_x, y=logo_y, w=LOGO_W_MM)
        except Exception:
            st.warning("No se pudo cargar el logo. Deja 'logo_hrt_final.jpg' junto al script.")

        pdf.set_font("Arial", "B", 7)
        title_h = 5.0
        title_x = logo_x + LOGO_W_MM + sep
        title_y = (logo_y + logo_h) - title_h
        cell_w  = max(10, FIRST_TAB_RIGHT - title_x)
        pdf.set_fill_color(230, 230, 230); pdf.set_text_color(0, 0, 0)
        pdf.set_xy(title_x, title_y); pdf.cell(cell_w, title_h, title_text, border=1, ln=1, align="C", fill=True)

        header_bottom = max(logo_y + logo_h, title_y + title_h)
        content_y_base = header_bottom + 2
        pdf.set_y(content_y_base)

        # ======= COLUMNA IZQUIERDA =======
        pdf.set_font("Arial", "", 7.5)
        line_h = 3.4

        y_marca = pdf.get_y()
        date_col_w   = 11.0
        date_table_w = date_col_w * 3
        x_date_right = FIRST_TAB_RIGHT
        x_date       = x_date_right - date_table_w
        fecha_label_w = 13.0
        gap_lab_box  = 1.8
        x_label_fecha = x_date - fecha_label_w - gap_lab_box
        
        label_w_common = 28.0
        gap_after_label = 1.0

        pdf.set_xy(FIRST_COL_LEFT, y_marca)
        pdf.cell(label_w_common, line_h, "Marca:", 0, 0, "L")
        value_w_line1 = x_label_fecha - (FIRST_COL_LEFT + label_w_common + gap_after_label)
        value_w_line1 = max(10, value_w_line1)
        pdf.cell(value_w_line1, line_h, f"{marca}", 0, 0, "L")

        pdf.set_xy(x_label_fecha, y_marca); pdf.set_font("Arial", "B", 7.5)
        pdf.cell(fecha_label_w, line_h, "FECHA:", 0, 0, "R")
        pdf.set_font("Arial", "", 7.5)
        dd = f"{fecha.day:02d}"; mm = f"{fecha.month:02d}"; yyyy = f"{fecha.year:04d}"
        pdf.set_xy(x_date, y_marca)
        pdf.cell(date_col_w, line_h, dd,   1, 0, "C")
        pdf.cell(date_col_w, line_h, mm,   1, 0, "C")
        pdf.cell(date_col_w, line_h, yyyy, 1, 0, "C")
        pdf.ln(line_h)

        def left_field(lbl, val):
            pdf.set_x(FIRST_COL_LEFT)
            pdf.cell(label_w_common, line_h, f"{lbl}:", 0, 0, "L")
            value_w = FIRST_TAB_RIGHT - (FIRST_COL_LEFT + label_w_common + gap_after_label)
            pdf.cell(value_w, line_h, f"{val}", 0, 1, "L")

        left_field("Modelo", modelo)
        left_field("Número de Serie", sn)
        left_field("Número de Inventario", inventario)
        left_field("Ubicación", ubicacion)

        pdf.ln(2.6)

        LEFT_ROW_H = 3.4
        create_checkbox_table(pdf, "1. Chequeo Visual", chequeo_visual, x_pos=FIRST_COL_LEFT,
                              item_w=ITEM_W, col_w=COL_W, row_h=LEFT_ROW_H,
                              head_fs=7.2, cell_fs=6.2, indent_w=5.0, title_tab_spaces=2)
        create_checkbox_table(pdf, "2. Sistema de Alta Presión", sistema_alta, x_pos=FIRST_COL_LEFT,
                              item_w=ITEM_W, col_w=COL_W, row_h=LEFT_ROW_H,
                              head_fs=7.2, cell_fs=6.2, indent_w=5.0, title_tab_spaces=2)
        create_checkbox_table(pdf, "3. Sistema de Baja Presión", sistema_baja, x_pos=FIRST_COL_LEFT,
                              item_w=ITEM_W, col_w=COL_W, row_h=LEFT_ROW_H,
                              head_fs=7.2, cell_fs=6.2, indent_w=5.0, title_tab_spaces=2)
        create_checkbox_table(pdf, "4. Sistema absorbedor", sistema_absorbedor, x_pos=FIRST_COL_LEFT,
                              item_w=ITEM_W, col_w=COL_W, row_h=LEFT_ROW_H,
                              head_fs=7.2, cell_fs=6.2, indent_w=5.0, title_tab_spaces=2)

        vm_izq = [(it, val) for it, val in ventilador_mecanico
                  if it.startswith("5.1.") or it.startswith("5.2.") or it.startswith("5.3.")
                  or it.startswith("5.4.") or it.startswith("5.5.") or it.startswith("5.6.")]
        pdf.set_x(FIRST_COL_LEFT)
        pdf.set_fill_color(230, 230, 230); pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "B", 7.2)
        title_prefix = " " * (2 * 2)
        pdf.cell(ITEM_W, LEFT_ROW_H, f"{title_prefix}5. Ventilador mecánico", border=1, ln=0, align="L", fill=True)
        pdf.set_font("Arial", "B", 6.2)
        pdf.cell(COL_W, LEFT_ROW_H, "OK",  border=1, ln=0, align="C", fill=True)
        pdf.cell(COL_W, LEFT_ROW_H, "NO",  border=1, ln=0, align="C", fill=True)
        pdf.cell(COL_W, LEFT_ROW_H, "N/A", border=1, ln=1, align="C", fill=True)
        pdf.set_font("Arial", "", 6.2)
        pdf.set_x(FIRST_COL_LEFT)
        pdf.cell(5.0, LEFT_ROW_H, "", border=0, ln=0)
        pdf.cell(max(1, ITEM_W - 5.0), LEFT_ROW_H,
                 "Verifique que el equipo muestra en pantalla los siguientes parámetros:",
                 border=0, ln=1, align="L")
        create_rows_only(pdf, vm_izq, x_pos=FIRST_COL_LEFT,
                         item_w=ITEM_W, col_w=COL_W, row_h=LEFT_ROW_H, cell_fs=6.2, indent_w=5.0)
        pdf.ln(1.6)

        # ======= COLUMNA DERECHA =======
        pdf.set_y(content_y_base)
        pdf.set_x(SECOND_COL_LEFT)
        pdf.set_font("Arial", "", 6.2)
        pdf.multi_cell(col_total_w, 3.4, "Verifique que el equipo realiza las siguientes acciones:", border=0)
        pdf.ln(0.2)

        vm_der = [(it, val) for it, val in ventilador_mecanico if it.startswith("5.7.") or it.startswith("5.8.")]
        if vm_der:
            create_rows_only(pdf, vm_der, x_pos=SECOND_COL_LEFT,
                             item_w=ITEM_W, col_w=COL_W, row_h=3.4, cell_fs=6.2, indent_w=5.0)

        create_checkbox_table(pdf, "6. Seguridad eléctrica", seguridad_electrica, x_pos=SECOND_COL_LEFT,
                              item_w=ITEM_W, col_w=COL_W, row_h=3.4,
                              head_fs=7.2, cell_fs=6.2, indent_w=5.0, title_tab_spaces=2)

        # ======= 7. Instrumentos de análisis =======
        TAB = "  " * 2
        pdf.set_x(SECOND_COL_LEFT)
        pdf.set_fill_color(230, 230, 230); pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "B", 7.5)
        pdf.cell(col_total_w, 4.0, f"{TAB}7. Instrumentos de análisis", border=1, ln=1, align="L", fill=True)
        pdf.ln(1.0)
        
        y_bottom_analisis = draw_analisis_columns(pdf, SECOND_COL_LEFT, pdf.get_y(), col_total_w, st.session_state.analisis_equipos)
        
        pdf.set_y(y_bottom_analisis)

        # ---------- Observaciones ----------
        draw_boxed_text_auto(pdf, x=SECOND_COL_LEFT, y=pdf.get_y(),
                             w=col_total_w, min_h=10,
                             title=f"{TAB}Observaciones", text=observaciones,
                             head_h=4.6, fs_head=7.2, fs_body=7.0, body_line_h=3.2, padding=1.2)
        pdf.ln(2)

        # ---------- Equipo Operativo + Nombre/Firma + Empresa ----------
        y_equipo_op = pdf.get_y()
        draw_si_no_boxes(pdf, x=SECOND_COL_LEFT, y=y_equipo_op, selected=operativo, size=4.5, label_w=40)
        pdf.ln(1.6)

        pdf.set_x(SECOND_COL_LEFT); pdf.set_font("Arial", "", 7.5)
        y_nombre = pdf.get_y()
        name_text = f"Nombre Técnico/Ingeniero: {tecnico}"
        name_box_w = min(100, col_total_w * 0.58)
        pdf.cell(name_box_w, 4.6, name_text, 0, 0, "L")
        pdf.cell(14, 4.6, "Firma:", 0, 0, "L")
        x_sig_tecnico = pdf.get_x()
        add_signature_inline(pdf, canvas_result_tecnico, x=x_sig_tecnico, y=y_nombre, w_mm=65, h_mm=20)
        pdf.set_y(y_nombre + 20 + 2)

        pdf.set_x(SECOND_COL_LEFT)
        pdf.cell(0, 4.0, f"Empresa Responsable: {empresa}", 0, 1)
        pdf.ln(2.0)

        # ---------- Observaciones (uso interno) ----------
        draw_boxed_text_auto(pdf, x=SECOND_COL_LEFT, y=pdf.get_y(),
                             w=col_total_w, min_h=10,
                             title=f"{TAB}Observaciones (uso interno)", text=observaciones_interno,
                             head_h=4.6, fs_head=7.2, fs_body=7.0, body_line_h=3.2, padding=1.2)
        pdf.ln(2)

        # ---------- Firmas de recepción (líneas fijas; imágenes ajustables por offset) ----------
        ancho_area = col_total_w
        center_left  = SECOND_COL_LEFT + (ancho_area * 0.25)
        center_right = SECOND_COL_LEFT + (ancho_area * 0.75)

        pdf.set_font("Arial", "B", 7.5)
        w_rc = pdf.get_string_width("RECEPCIÓN CONFORME")
        w_pi = pdf.get_string_width("PERSONAL INGENIERÍA CLÍNICA")
        w_pc = pdf.get_string_width("PERSONAL CLÍNICO")
        text_block_w = max(w_rc, w_pi, w_pc) + 12
        half_w = ancho_area / 2.0
        max_line_len = half_w - 8
        line_len = min(max(text_block_w, 65), max_line_len)

        sig_w = min(65, line_len - 6)
        sig_h = 20

        SIG_OFF_X_LEFT  = 15
        SIG_OFF_Y_LEFT  = 0
        SIG_OFF_X_RIGHT = 15
        SIG_OFF_Y_RIGHT = 0

        y_top = pdf.get_y()
        y_sig = y_top + 2.0

        x_line_left  = center_left  - line_len / 2.0
        x_line_right = center_right - line_len / 2.0

        add_signature_inline(pdf, canvas_result_ingenieria,
                             x=center_left - sig_w/2.0 + SIG_OFF_X_LEFT,
                             y=y_sig + SIG_OFF_Y_LEFT,
                             w_mm=sig_w, h_mm=sig_h)
        add_signature_inline(pdf, canvas_result_clinico,
                             x=center_right - sig_w/2.0 + SIG_OFF_X_RIGHT,
                             y=y_sig + SIG_OFF_Y_RIGHT,
                             w_mm=sig_w, h_mm=sig_h)

        y_line = y_sig + sig_h + 3.0
        pdf.set_draw_color(0, 0, 0)
        pdf.line(x_line_left,  y_line, x_line_left  + line_len, y_line)
        pdf.line(x_line_right, y_line, x_line_right + line_len, y_line)

        pdf.set_xy(x_line_left,  y_line + 0.8)
        pdf.cell(line_len, 3.6, "RECEPCIÓN CONFORME", 0, 2, 'C')
        pdf.set_xy(x_line_left,  pdf.get_y())
        pdf.cell(line_len, 3.6, "PERSONAL INGENIERÍA CLÍNICA", 0, 0, 'C')

        pdf.set_xy(x_line_right, y_line + 0.8)
        pdf.cell(line_len, 3.6, "RECEPCIÓN CONFORME", 0, 2, 'C')
        pdf.set_xy(x_line_right, pdf.get_y())
        pdf.cell(line_len, 3.6, "PERSONAL CLÍNICO", 0, 0, 'C')

        pdf.set_y(max(y_line + 7, pdf.get_y()))

        out = pdf.output(dest="S")
        if isinstance(out, str):
            out = out.encode("latin1")
        else:
            out = bytes(out)

        st.download_button(
            "Descargar PDF",
            out,
            file_name=f"MP_Anestesia_{sn}.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main()
