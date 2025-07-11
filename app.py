import streamlit as st
from fpdf import FPDF
import datetime
import io

# Definir función para tabla con bordes estilo mp.pdf
def draw_bordered_table(pdf, headers, rows, col_widths, line_height=7):
    pdf.set_font("Arial", "B", 10)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], line_height, header, border=1, align="C")
    pdf.ln(line_height)
    pdf.set_font("Arial", "", 10)
    for row in rows:
        for i, cell in enumerate(row):
            pdf.cell(col_widths[i], line_height, str(cell), border=1)
        pdf.ln(line_height)

def main():
    st.title("Pauta Mantenimiento Preventivo - Máquina de Anestesia")

    # Campos generales
    marca = st.text_input("Marca")
    modelo = st.text_input("Modelo")
    sn = st.text_input("S/N")
    inventario = st.text_input("N° Inventario")
    fecha = st.date_input("Fecha", value=datetime.date.today())
    ubicacion = st.text_input("Ubicación")

    # Tabla tipo checklist
    def checklist(seccion, items):
        st.subheader(seccion)
        respuestas = []
        for item in items:
            col1, col2 = st.columns([4, 3])
            with col1:
                st.markdown(item)
            with col2:
                resp = st.radio("", ["OK", "NO", "N/A"], key=item, horizontal=True)
                respuestas.append((item, resp))
        return respuestas

    chequeo_visual = checklist("1. Chequeo Visual", [
        "1.1 Carcasa Frontal y Trasera", "1.2 Estado de Software",
        "1.3 Panel frontal", "1.4 Batería de respaldo"
    ])

    alta_presion = checklist("2. Sistema de Alta Presión", [
        "2.1 Yugo O2, N2O, Aire", "2.2 Empaquetadura yugo",
        "2.3 Entrada de presión", "2.4 Válvulas flujómetro"
    ])

    baja_presion = checklist("3. Sistema de Baja Presión", [
        "3.1 Flujómetro N2O", "3.2 Flujómetro O2", "3.3 Flujómetro Aire",
        "3.4 Fugas", "3.5 Flujos", "3.6 Regulador 2da etapa",
        "3.7 Corte N2O/Aire sin O2", "3.8 Proporción O2/N2O", "3.9 Manifold vaporizadores"
    ])

    absorbedor = checklist("4. Sistema Absorbedor", [
        "4.1 Empaquetadura canister", "4.2 Válvula APL", "4.3 Manómetro vía aérea",
        "4.4 Válvula inhalatoria", "4.5 Válvula exhalatoria",
        "4.6 Fugas", "4.7 Hermeticidad"
    ])

    ventilador = checklist("5. Ventilador Mecánico", [
        "5.1 % Oxígeno", "5.2 Volumen corriente/minuto",
        "5.3 Presión vía aérea", "5.4 Frecuencia respiratoria",
        "5.5 Modo ventilatorio", "5.6 Alarmas", "5.7 Calibración O2",
        "5.8 Calibración sensores"
    ])

    electrica = checklist("6. Seguridad Eléctrica", [
        "6.1 Corriente de fuga", "6.2 Tierra de protección", "6.3 Aislación"
    ])

    # Instrumentos
    st.subheader("7. Instrumentos de Análisis")
    instrumento_1 = [st.text_input("Equipo 1"), st.text_input("Marca 1"),
                     st.text_input("Modelo 1"), st.text_input("N° Serie 1")]
    instrumento_2 = [st.text_input("Equipo 2"), st.text_input("Marca 2"),
                     st.text_input("Modelo 2"), st.text_input("N° Serie 2")]

    # Observaciones
    obs = st.text_area("Observaciones")
    obs_interno = st.text_area("Observaciones (uso interno)")
    operativo = st.radio("¿Equipo Operativo?", ["SI", "NO"])
    tecnico = st.text_input("Nombre Técnico/Ingeniero")
    empresa = st.text_input("Empresa Responsable")

    if st.button("Generar PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "HOSPITAL REGIONAL DE TALCA", ln=True, align="C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 8, "UNIDAD DE INGENIERÍA CLÍNICA", ln=True, align="C")
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 10, "PAUTA MANTENIMIENTO PREVENTIVO MAQUINA ANESTESIA (Ver 2)", ln=True, align="C")
        pdf.ln(5)

        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 7, f"MARCA: {marca}", ln=True)
        pdf.cell(0, 7, f"MODELO: {modelo}", ln=True)
        pdf.cell(0, 7, f"S/N: {sn}", ln=True)
        pdf.cell(0, 7, f"N° INVENTARIO: {inventario}", ln=True)
        pdf.cell(0, 7, f"FECHA: {fecha.strftime('%Y-%m-%d')}", ln=True)
        pdf.cell(0, 7, f"UBICACIÓN: {ubicacion}", ln=True)
        pdf.ln(5)

        def print_checklist(title, data):
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 7, title, ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.cell(130, 7, "", 0)
            pdf.cell(15, 7, "OK", 1, 0, "C")
            pdf.cell(15, 7, "NO", 1, 0, "C")
            pdf.cell(15, 7, "N/A", 1, 1, "C")
            for item, val in data:
                pdf.cell(130, 7, item, 1)
                pdf.cell(15, 7, "X" if val == "OK" else "", 1, 0, "C")
                pdf.cell(15, 7, "X" if val == "NO" else "", 1, 0, "C")
                pdf.cell(15, 7, "X" if val == "N/A" else "", 1, 1, "C")

        for title, data in [
            ("1. Chequeo Visual", chequeo_visual),
            ("2. Sistema de Alta Presión", alta_presion),
            ("3. Sistema de Baja Presión", baja_presion),
            ("4. Sistema Absorbedor", absorbedor),
            ("5. Ventilador Mecánico", ventilador),
            ("6. Seguridad Eléctrica", electrica)
        ]:
            print_checklist(title, data)
            pdf.ln(2)

        # Instrumentos tabla
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 7, "7. Instrumentos de Análisis", ln=True)
        headers = ["EQUIPO", "MARCA", "MODELO", "N° SERIE"]
        rows = [instrumento_1, instrumento_2]
        draw_bordered_table(pdf, headers, rows, [50, 40, 40, 50])
        pdf.ln(5)

        # Observaciones
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 6, f"OBSERVACIONES: {obs}")
        pdf.multi_cell(0, 6, f"OBSERVACIONES (uso interno): {obs_interno}")
        pdf.ln(2)
        pdf.cell(0, 6, f"EQUIPO OPERATIVO: {operativo}", ln=True)
        pdf.cell(0, 6, f"NOMBRE TÉCNICO/INGENIERO: {tecnico}", ln=True)
        pdf.cell(0, 6, f"EMPRESA RESPONSABLE: {empresa}", ln=True)
        pdf.ln(15)

        # Firmas al final
        pdf.cell(60, 8, "_________________________", 0, 0, 'C')
        pdf.cell(60, 8, "_________________________", 0, 0, 'C')
        pdf.cell(60, 8, "_________________________", 0, 1, 'C')
        pdf.cell(60, 6, "TÉCNICO ENCARGADO", 0, 0, 'C')
        pdf.cell(60, 6, "INGENIERÍA CLÍNICA", 0, 0, 'C')
        pdf.cell(60, 6, "PERSONAL CLÍNICO", 0, 1, 'C')

        buffer = io.BytesIO(pdf.output(dest='S').encode('latin-1'))
        st.download_button("Descargar PDF", buffer, file_name=f"MP_{sn or 'SIN_SERIE'}.pdf", mime="application/pdf")

if __name__ == "__main__":
    main()