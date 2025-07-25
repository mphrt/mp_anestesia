import streamlit as st
from fpdf import FPDF
import datetime
import io

def create_checkbox_table(pdf, section_title, items):
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, section_title, ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(140, 7, "", 0)
    pdf.cell(15, 7, "OK", 1, 0, "C")
    pdf.cell(15, 7, "NO", 1, 0, "C")
    pdf.cell(15, 7, "N/A", 1, 1, "C")
    for item, value in items:
        pdf.cell(140, 7, item, 1)
        pdf.cell(15, 7, "X" if value == "OK" else "", 1, 0, "C")
        pdf.cell(15, 7, "X" if value == "NO" else "", 1, 0, "C")
        pdf.cell(15, 7, "X" if value == "N/A" else "", 1, 1, "C")
    pdf.ln(3)

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
        "3.6. Verificación de regulador de 2da (segunda) etapa",
        "3.7. Revisión de sistema de corte N2O/Aire por falta de O2",
        "3.8. Revisión de sistema proporción de O2/N2O",
        "3.9. Revisión de manifold de vaporizadores"
    ])

    sistema_absorbedor = checklist("4. Sistema absorbedor", [
        "4.1. Revisión o reemplazo de empaquetadura de canister",
        "4.2. Revisión de válvula APL",
        "4.3. Verificación de manómetro de presión de vía aérea (ajuste a cero)",
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

    # New input for digital signature
    firma_digital = st.text_input("Firma Digital (Escriba su nombre completo para firmar)")


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
        for label, val in [
            ("MARCA", marca), ("MODELO", modelo), ("S/N", sn),
            ("N° INVENTARIO", inventario), ("UBICACIÓN", ubicacion), ("FECHA", fecha.strftime("%Y-%m-%d"))
        ]:
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

        # Add signature box
        pdf.ln(10) # Add some space
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, "FIRMA:", ln=True) # Label for signature
        
        # Draw a rectangle for the signature
        # x, y, width, height
        # Get current x and y position
        x = pdf.get_x()
        y = pdf.get_y()
        pdf.rect(x, y, 80, 25) # Draw a rectangle 80mm wide and 25mm high for the signature

        # If a digital signature was provided, add it inside the box (or just below)
        if firma_digital:
            pdf.ln(2) # Little space after the box if desired
            pdf.set_font("Arial", "I", 10) # Italic for signature text
            pdf.cell(0, 7, f"Firma Digital: {firma_digital}", ln=True)
        
        pdf.ln(15)
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