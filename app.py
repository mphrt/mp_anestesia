import streamlit as st
from fpdf import FPDF
import datetime

st.title("Formulario de Mantenimiento - Máquina de Anestesia")

# Información general
st.header("Información General")
marca = st.text_input("Marca")
modelo = st.text_input("Modelo")
sn = st.text_input("S/N")
n_inventario = st.text_input("N° Inventario")
fecha = st.date_input("Fecha", value=datetime.date.today())
ubicacion = st.text_input("Ubicación")

# Sección: Chequeo Visual
st.header("1. Chequeo Visual")
chequeo_items = [
    "1.1. Carcasa Frontal y Trasera",
    "1.2. Estado de Software",
    "1.3. Panel frontal",
    "1.4. Batería de respaldo"
]
chequeo_resultados = [st.radio(item, ["OK", "NO", "N/A"], key=item) for item in chequeo_items]

# Observaciones
st.header("Observaciones")
observaciones = st.text_area("Observaciones")
observaciones_interno = st.text_area("Observaciones (uso interno)")

# Firma y responsables
st.header("Firma")
equipo_operativo = st.radio("¿Equipo Operativo?", ["SI", "NO"])
nombre_tecnico = st.text_input("Nombre Técnico/Ingeniero")
empresa_responsable = st.text_input("Empresa Responsable")

# Generar PDF
if st.button("Generar PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "PAUTA MANTENCIÓN MAQUINA DE ANESTESIA", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.ln(10)

    datos = [
        ("Marca", marca),
        ("Modelo", modelo),
        ("S/N", sn),
        ("N° Inventario", n_inventario),
        ("Fecha", fecha.strftime("%Y-%m-%d")),
        ("Ubicación", ubicacion)
    ]
    for label, value in datos:
        pdf.cell(0, 10, f"{label}: {value}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Chequeo Visual:", ln=True)
    pdf.set_font("Arial", "", 12)
    for item, estado in zip(chequeo_items, chequeo_resultados):
        pdf.cell(0, 10, f"{item}: {estado}", ln=True)

    pdf.ln(5)
    pdf.multi_cell(0, 10, f"Observaciones: {observaciones}")
    pdf.multi_cell(0, 10, f"Observaciones (Interno): {observaciones_interno}")
    pdf.ln(5)

    pdf.cell(0, 10, f"Equipo Operativo: {equipo_operativo}", ln=True)
    pdf.cell(0, 10, f"Nombre Técnico/Ingeniero: {nombre_tecnico}", ln=True)
    pdf.cell(0, 10, f"Empresa Responsable: {empresa_responsable}", ln=True)

    # Guardar en archivo
    pdf.output("formulario_mantenimiento.pdf")

    with open("formulario_mantenimiento.pdf", "rb") as f:
        st.download_button("Descargar PDF", f, file_name="formulario_mantenimiento.pdf")