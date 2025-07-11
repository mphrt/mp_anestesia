import streamlit as st
from fpdf import FPDF
import datetime
import io

def show_radio_section(title, items, description=None):
    st.markdown(f"### {title}")
    if description:
        st.info(description)
    responses = []
    for item in items:
        choice = st.radio(item, ["OK", "NO", "N/A"], key=item)
        responses.append((item, choice))
    return responses

def main():
    st.title("Formulario de Mantenimiento - Máquina de Anestesia")

    st.subheader("Información General")
    marca = st.text_input("Marca")
    modelo = st.text_input("Modelo")
    sn = st.text_input("S/N")
    n_inventario = st.text_input("N° Inventario")
    fecha = st.date_input("Fecha", value=datetime.date.today())
    ubicacion = st.text_input("Ubicación")

    chequeo_visual = show_radio_section("1. Chequeo Visual", [
        "1.1. Carcasa Frontal y Trasera",
        "1.2. Estado de Software",
        "1.3. Panel frontal",
        "1.4. Batería de respaldo"
    ])

    sistema_alta = show_radio_section("2. Sistema de Alta Presión", [
        "2.1. Chequeo de yugo de O2, N2O, Aire",
        "2.2. Revisión o reemplazo de empaquetadura de yugo",
        "2.3. Verificación de entrada de presión",
        "2.4. Revisión y calibración de válvulas de flujometro de O2, N2O, Aire"
    ])

    sistema_baja = show_radio_section("3. Sistema de Baja Presión", [
        "3.1. Revisión válvula flujómetro N2O",
        "3.2. Revisión válvula flujómetro O2",
        "3.3. Revisión válvula flujómetro Aire",
        "3.4. Chequeo de fugas",
        "3.5. Verificación de flujos",
        "3.6. Verificación regulador 2da etapa",
        "3.7. Revisión corte N2O/Aire por falta O2",
        "3.8. Revisión sistema proporción O2/N2O",
        "3.9. Revisión de manifold de vaporizadores"
    ])

    sistema_absorbedor = show_radio_section("4. Sistema Absorbedor", [
        "4.1. Revisión empaquetadura canister",
        "4.2. Revisión válvula APL",
        "4.3. Verificación manómetro vía aérea",
        "4.4. Revisión válvula inhalatoria",
        "4.5. Revisión válvula exhalatoria",
        "4.6. Chequeo de fugas",
        "4.7. Hermeticidad"
    ])

    ventilador = show_radio_section("5. Ventilador Mecánico", [
        "5.1. Porcentaje de oxígeno",
        "5.2. Volumen corriente y volumen minuto",
        "5.3. Presión de vía aérea",
        "5.4. Frecuencia respiratoria",
        "5.5. Modo ventilatorio",
        "5.6. Alarmas",
        "5.7. Calibración celda de oxígeno",
        "5.8. Calibración sensores de flujo"
    ], description="Verifique que el equipo muestra los parámetros y realiza las siguientes acciones:")

    seguridad = show_radio_section("6. Seguridad Eléctrica", [
        "6.1. Corriente de fuga",
        "6.2. Tierra de protección",
        "6.3. Aislación"
    ])

    st.subheader("7. Instrumentos de Análisis")
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

    equipo_operativo = st.radio("¿Equipo Operativo?", ["SI", "NO"])
    tecnico = st.text_input("Nombre Técnico/Ingeniero")
    empresa = st.text_input("Empresa Responsable")

    if st.button("Generar PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "PAUTA MANTENCIÓN MAQUINA DE ANESTESIA", ln=True, align="C")
        pdf.set_font("Arial", "", 10)
        pdf.ln(5)

        for label, val in [
            ("Marca", marca), ("Modelo", modelo), ("S/N", sn),
            ("N° Inventario", n_inventario), ("Fecha", fecha.strftime("%Y-%m-%d")), ("Ubicación", ubicacion)
        ]:
            pdf.cell(0, 8, f"{label}: {val}", ln=True)

        def add_section(title, data):
            pdf.ln(5)
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 8, title, ln=True)
            pdf.set_font("Arial", "", 10)
            for item, val in data:
                pdf.cell(0, 6, f"{item}: {val}", ln=True)

        add_section("1. Chequeo Visual", chequeo_visual)
        add_section("2. Sistema de Alta Presión", sistema_alta)
        add_section("3. Sistema de Baja Presión", sistema_baja)
        add_section("4. Sistema Absorbedor", sistema_absorbedor)
        add_section("5. Ventilador Mecánico", ventilador)
        add_section("6. Seguridad Eléctrica", seguridad)

        pdf.ln(5)
        pdf.cell(0, 8, "Instrumentos de Análisis:", ln=True)
        for e, m, mo, s in [(equipo1, marca1, modelo1, serie1), (equipo2, marca2, modelo2, serie2)]:
            pdf.cell(0, 6, f"Equipo: {e} | Marca: {m} | Modelo: {mo} | N° Serie: {s}", ln=True)

        pdf.ln(5)
        pdf.multi_cell(0, 6, f"Observaciones: {observaciones}")
        pdf.multi_cell(0, 6, f"Observaciones Internas: {observaciones_interno}")
        pdf.ln(5)

        pdf.cell(0, 8, f"Equipo Operativo: {equipo_operativo}", ln=True)
        pdf.cell(0, 8, f"Nombre Técnico: {tecnico}", ln=True)
        pdf.cell(0, 8, f"Empresa Responsable: {empresa}", ln=True)

        # Guardar en memoria
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        pdf_buffer = io.BytesIO(pdf_bytes)

        st.success("PDF generado con éxito.")
        st.download_button("Descargar PDF", pdf_buffer, file_name=f"MP_Anestesia_{sn}.pdf", mime="application/pdf")

if __name__ == "__main__":
    main()
