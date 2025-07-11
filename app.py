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
    st.title("Formulario de Mantenimiento - HRT")

    marca = st.text_input("Marca")
    modelo = st.text_input("Modelo")
    sn = st.text_input("S/N")
    n_inventario = st.text_input("N° Inventario")
    fecha = st.date_input("Fecha", value=datetime.date.today())
    ubicacion = st.text_input("Ubicación")

    def seccion(numero, nombre, claves):
        st.markdown(f"### {numero}. {nombre}")
        return [(f"{numero}.{i+1}. {clave}", st.radio("", ["OK", "NO", "N/A"], horizontal=True, key=f"{numero}-{i}")) for i, clave in enumerate(claves)]

    chequeo_visual = seccion("1", "Chequeo Visual", [
        "Carcasa Frontal y Trasera", "Estado de Software", "Panel frontal", "Batería de respaldo"
    ])

    sistema_alta = seccion("2", "Sistema de Alta Presión", [
        "Chequeo de yugo de O2, N2O, Aire",
        "Revisión o reemplazo de empaquetadura de yugo",
        "Verificación de entrada de presión",
        "Revisión y calibración de válvulas de flujometro de O2, N2O, Aire"
    ])

    sistema_baja = seccion("3", "Sistema de baja presión", [
        "Revisión y calibración de válvula de flujómetro de N2O",
        "Revisión y calibración de válvula de flujómetro de 02",
        "Revisión y calibración de válvula de flujómetro de Aire",
        "Chequeo de fugas",
        "Verificación de flujos",
        "Verificación de regulador de 2da (segunda) etapa",
        "Revisión de sistema de corte N2O/Aire por falta de 02",
        "Revisión de sistema proporción de 02/N2O",
        "Revisión de manifold de vaporizadores"
    ])

    sistema_absorbedor = seccion("4", "Sistema Absorbedor", [
        "Revisión o reemplazo de empaquetadura de canister",
        "Revisión de válvula APL",
        "Verificación de manómetro de presión de vía aérea (ajuste a cero)",
        "Revisión de válvula inhalatoria",
        "Revisión de válvula exhalatoria",
        "Chequeo de fugas",
        "Hermeticidad"
    ])

    ventilador = seccion("5", "Ventilador Mecánico", [
        "Porcentaje de oxígeno",
        "Volumen corriente y volumen minuto",
        "Presión de vía aérea",
        "Frecuencia respiratoria",
        "Modo ventilatorio",
        "Alarmas",
        "Calibración de celda de oxígeno a 21% y al 100%",
        "Calibración de sensores de flujo"
    ])

    seguridad = seccion("6", "Seguridad Eléctrica", [
        "Corriente de fuga",
        "Tierra de protección",
        "Aislación"
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
