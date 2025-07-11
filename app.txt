import streamlit as st
from fpdf import FPDF
import datetime
import io

def create_checkbox_table(pdf, section_title, items):
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, section_title, ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(140, 8, "", 0, 0)
    pdf.cell(15, 8, "OK", 1, 0, "C")
    pdf.cell(15, 8, "NO", 1, 0, "C")
    pdf.cell(15, 8, "N/A", 1, 1, "C")
    for item, value in items:
        pdf.cell(140, 8, item, 1)
        pdf.cell(15, 8, "X" if value == "OK" else "", 1, 0, "C")
        pdf.cell(15, 8, "X" if value == "NO" else "", 1, 0, "C")
        pdf.cell(15, 8, "X" if value == "N/A" else "", 1, 1, "C")

def main():
    st.title("Formulario de Mantenimiento - HRT (sin logo)")

    marca = st.text_input("Marca")
    modelo = st.text_input("Modelo")
    sn = st.text_input("S/N")
    n_inventario = st.text_input("N° Inventario")
    fecha = st.date_input("Fecha", value=datetime.date.today())
    ubicacion = st.text_input("Ubicación")

    def seccion(nombre, claves):
        return [(clave, st.radio(clave, ["OK", "NO", "N/A"], horizontal=True, key=clave)) for clave in claves]

    chequeo_visual = seccion("1. Chequeo Visual", [
        "1.1. Carcasa Frontal y Trasera", "1.2. Estado de Software", "1.3. Panel frontal", "1.4. Batería de respaldo"
    ])

    sistema_alta = seccion("2. Sistema de Alta Presión", [
        "2.1. Chequeo de yugo de O2, N2O, Aire", "2.2. Revisión empaquetadura de yugo",
        "2.3. Entrada de presión", "2.4. Calibración válvulas flujómetro"
    ])

    sistema_baja = seccion("3. Sistema de Baja Presión", [
        "3.1. Válvula N2O", "3.2. Válvula O2", "3.3. Válvula Aire", "3.4. Fugas", "3.5. Flujos",
        "3.6. Regulador 2da etapa", "3.7. Corte N2O/Aire", "3.8. Proporción O2/N2O", "3.9. Manifold vaporizadores"
    ])

    sistema_absorbedor = seccion("4. Sistema Absorbedor", [
        "4.1. Empaquetadura canister", "4.2. Válvula APL", "4.3. Manómetro vía aérea",
        "4.4. Válvula inhalatoria", "4.5. Válvula exhalatoria", "4.6. Fugas", "4.7. Hermeticidad"
    ])

    ventilador = seccion("5. Ventilador Mecánico", [
        "5.1. % Oxígeno", "5.2. Volumen corriente/minuto", "5.3. Presión vía aérea",
        "5.4. Frecuencia respiratoria", "5.5. Modo ventilatorio", "5.6. Alarmas",
        "5.7. Calibración celda O2", "5.8. Calibración sensores"
    ])

    seguridad = seccion("6. Seguridad Eléctrica", [
        "6.1. Corriente de fuga", "6.2. Tierra de protección", "6.3. Aislación"
    ])

    equipo1 = st.text_input("Equipo 1")
    marca1 = st.text_input("Marca 1")
    modelo1 = st.text_input("Modelo 1")
    serie1 = st.text_input("N° Serie 1")
    equipo2 = st.text_input("Equipo 2")
    marca2 = st.text_input("Marca 2")
    modelo2 = st.text_input("Modelo 2")
    serie2 = st.text_input("N° Serie 2")

    observaciones = st.text_area("Observaciones")
    observaciones_interno = st.text_area("Observaciones (uso interno)")
    operativo = st.radio("¿Equipo Operativo?", ["SI", "NO"])
    tecnico = st.text_input("Nombre Técnico/Ingeniero")
    empresa = st.text_input("Empresa Responsable")

    if st.button("Generar PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "HOSPITAL REGIONAL DE TALCA", ln=True, align="C")
        pdf.cell(0, 10, "UNIDAD DE INGENIERÍA CLÍNICA", ln=True, align="C")
        pdf.cell(0, 10, "PAUTA MANTENCIÓN MAQUINA DE ANESTESIA", ln=True, align="C")
        pdf.ln(5)

        pdf.set_font("Arial", "", 10)
        for label, val in [
            ("MARCA", marca), ("MODELO", modelo), ("S/N", sn),
            ("N° INVENTARIO", n_inventario), ("UBICACIÓN", ubicacion), ("FECHA", fecha.strftime("%Y-%m-%d"))
        ]:
            pdf.cell(0, 8, f"{label}: {val}", ln=True)

        create_checkbox_table(pdf, "1. Chequeo Visual", chequeo_visual)
        create_checkbox_table(pdf, "2. Sistema de Alta Presión", sistema_alta)
        create_checkbox_table(pdf, "3. Sistema de Baja Presión", sistema_baja)
        create_checkbox_table(pdf, "4. Sistema Absorbedor", sistema_absorbedor)
        create_checkbox_table(pdf, "5. Ventilador Mecánico", ventilador)
        create_checkbox_table(pdf, "6. Seguridad Eléctrica", seguridad)

        pdf.ln(5)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, "7. Instrumentos de Análisis", ln=True)
        pdf.set_font("Arial", "", 10)
        for e, m, mo, s in [(equipo1, marca1, modelo1, serie1), (equipo2, marca2, modelo2, serie2)]:
            pdf.cell(0, 6, f"Equipo: {e} | Marca: {m} | Modelo: {mo} | N° Serie: {s}", ln=True)

        pdf.ln(4)
        pdf.multi_cell(0, 6, f"Observaciones: {observaciones}")
        pdf.multi_cell(0, 6, f"Observaciones Internas: {observaciones_interno}")
        pdf.ln(4)
        pdf.cell(0, 8, f"Equipo Operativo: {operativo}", ln=True)
        pdf.cell(0, 8, f"Nombre Técnico: {tecnico}", ln=True)
        pdf.cell(0, 8, f"Empresa Responsable: {empresa}", ln=True)

        pdf.ln(20)
        pdf.cell(60, 8, "_________________________", 0, 0, 'C')
        pdf.cell(60, 8, "_________________________", 0, 0, 'C')
        pdf.cell(60, 8, "_________________________", 0, 1, 'C')
        pdf.cell(60, 6, "TÉCNICO ENCARGADO", 0, 0, 'C')
        pdf.cell(60, 6, "INGENIERÍA CLÍNICA", 0, 0, 'C')
        pdf.cell(60, 6, "PERSONAL CLÍNICO", 0, 1, 'C')

        output = io.BytesIO(pdf.output(dest="S").encode("latin1"))
        st.download_button("Descargar PDF", output, file_name=f"MP_Anestesia_{sn}.pdf", mime="application/pdf")

if __name__ == "__main__":
    main()
