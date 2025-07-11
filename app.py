import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from fpdf import FPDF
import os

class MaintenanceApp:
    def __init__(self, master):
        self.master = master
        master.title("Aplicación de Mantenimiento")
        master.geometry("800x600")

        self.create_centered_mp_buttons()

    def create_centered_mp_buttons(self):
        button_frame = ttk.Frame(self.master)
        button_frame.pack(expand=True, anchor="center")

        btn_maq_anestesia = ttk.Button(button_frame, text="Mantenimiento Preventivo: Máquinas de Anestesia", command=self.open_maq_anestesia_window)
        btn_maq_anestesia.pack(pady=10)

        #btn_msv = ttk.Button(button_frame, text="Mantenimiento Preventivo: Monitor de Signos Vitales", command=self.open_msv_window)
        #btn_msv.pack(pady=10)

        #btn_incubadoras = ttk.Button(button_frame, text="Mantenimiento Preventivo: Incubadoras", command=self.open_incubadoras_window)
        #btn_incubadoras.pack(pady=10)

    def open_maq_anestesia_window(self):
        self.maq_anestesia_window = tk.Toplevel(self.master)
        self.maq_anestesia_window.title("Mantenimiento Preventivo: Máquinas de Anestesia")
        self.maq_anestesia_window.geometry("800x700")

        self.create_maq_anestesia_form(self.maq_anestesia_window)

    def create_maq_anestesia_form(self, parent_window):
        canvas = tk.Canvas(parent_window)
        scrollbar = ttk.Scrollbar(parent_window, orient="vertical", command=canvas.yview)
        
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        scrollable_frame.grid_columnconfigure(0, weight=2)
        for i in range(1, 4):  
            scrollable_frame.grid_columnconfigure(i, weight=1)

        ttk.Label(scrollable_frame, text="HOSPITAL REGIONAL DE TALCA", font=("Arial", 12)).grid(row=0, column=0, columnspan=4, pady=5, sticky="w")
        ttk.Label(scrollable_frame, text="PAUTA MANTENCIÓN MAQUINA DE ANESTESIA", font=("Arial", 14, "bold")).grid(row=1, column=0, columnspan=4, pady=10, sticky="w")
        
        row_counter = 2

        info_labels = [
            ("MARCA:", "marca_entry"),
            ("MODELO:", "modelo_entry"),
            ("S/N:", "sn_entry"),
            ("N/INVENTARIO:", "n_inventario_entry"),  
            ("FECHA:", "fecha_entry"),
            ("UBICACIÓN:", "ubicacion_entry")
        ]

        for label_text, entry_name in info_labels:
            ttk.Label(scrollable_frame, text=label_text).grid(row=row_counter, column=0, sticky="w", padx=5, pady=2)
            setattr(self, entry_name, ttk.Entry(scrollable_frame, width=40))
            getattr(self, entry_name).grid(row=row_counter, column=1, columnspan=3, sticky="ew", padx=5, pady=2)
            row_counter += 1

        def create_section_radio(frame, title, items_list, start_row, description_text=None):
            ttk.Label(frame, text=title, font=("Arial", 10, "bold")).grid(row=start_row, column=0, columnspan=4, pady=10, sticky="w")
            start_row += 1
            if description_text:
                ttk.Label(frame, text=description_text, wraplength=700).grid(row=start_row, column=0, columnspan=4, sticky="w", padx=5)
                start_row += 1

            ttk.Label(frame, text="OK").grid(row=start_row, column=1)
            ttk.Label(frame, text="NO").grid(row=start_row, column=2)
            ttk.Label(frame, text="N/A").grid(row=start_row, column=3)
            start_row += 1

            vars_list = []
            for i, (item_text, _) in enumerate(items_list):
                ttk.Label(frame, text=item_text).grid(row=start_row + i, column=0, sticky="w", padx=5, pady=2)
                
                choice_var = tk.StringVar(value="")
                
                def create_radio_command(v, value_to_set):
                    return lambda: v.set(value_to_set)

                ttk.Radiobutton(frame, variable=choice_var, value="OK", command=create_radio_command(choice_var, "OK")).grid(row=start_row + i, column=1)
                ttk.Radiobutton(frame, variable=choice_var, value="NO", command=create_radio_command(choice_var, "NO")).grid(row=start_row + i, column=2)
                ttk.Radiobutton(frame, variable=choice_var, value="N/A", command=create_radio_command(choice_var, "N/A")).grid(row=start_row + i, column=3)
                
                vars_list.append(choice_var)
            return start_row + len(items_list), vars_list

        chequeo_visual_items = [
            ("1.1. Carcasa Frontal y Trasera", "carcasa_frontal_trasera"),
            ("1.2. Estado de Software", "estado_software"),
            ("1.3. Panel frontal", "panel_frontal"),
            ("1.4. Batería de respaldo", "bateria_respaldo")
        ]
        row_counter, self.chequeo_visual_vars = create_section_radio(scrollable_frame, "1. Chequeo Visual", chequeo_visual_items, row_counter)

        sistema_alta_presion_items = [
            ("2.1. Chequeo de yugo de O2, N2O, Aire", "chequeo_yugo"),
            ("2.2. Revisión o reemplazo de empaquetadura de yugo", "empaquetadura_yugo"),
            ("2.3. Verificación de entrada de presión", "entrada_presion"),
            ("2.4. Revisión y calibración de válvulas de flujometro de O2, N2O, Aire", "calibracion_valvulas_flujometro")
        ]
        row_counter, self.sistema_alta_presion_vars = create_section_radio(scrollable_frame, "2. Sistema de Alta Presión", sistema_alta_presion_items, row_counter)

        sistema_baja_presion_items = [
            ("3.1. Revisión y calibración de válvula de flujómetro de N2O", "valvula_flujometro_n2o"),
            ("3.2. Revisión y calibración de válvula de flujometro de 02", "valvula_flujometro_o2"),
            ("3.3. Revisión y calibración de válvula de flujometro de Aire", "valvula_flujometro_aire"),
            ("3.4. Chequeo de fugas", "chequeo_fugas_baja"),
            ("3.5. Verificación de flujos", "verificacion_flujos"),
            ("3.6. Verificación de regulador de 2da (segunda) etapa", "regulador_2da_etapa"),
            ("3.7. Revisión de sistema de corte N20/Aire por falta de 02", "corte_n2o_aire_falta_o2"),
            ("3.8. Revisión de sistema proporción de 02/N20", "proporcion_o2_n2o"),
            ("3.9. Revisión de manifold de vaporizadores", "manifold_vaporizadores")
        ]
        row_counter, self.sistema_baja_presion_vars = create_section_radio(scrollable_frame, "3. Sistema de baja presión", sistema_baja_presion_items, row_counter)

        sistema_absorbedor_items = [
            ("4.1. Revisión o reemplazo de empaquetadura de canister", "empaquetadura_canister"),
            ("4.2. Revisión de válvula APL", "valvula_apl"),
            ("4.3. Verificación de manómetro de presión de vía aérea (ajuste a cero)", "manometro_presion_via_aerea"),
            ("4.4. Revisión de válvula inhalatoria", "valvula_inhalatoria"),
            ("4.5. Revisión de válvula exhalatoria", "valvula_exhalatoria"),
            ("4.6. Chequeo de fugas", "chequeo_fugas_absorbedor"),
            ("4.7. Hermeticidad", "")
        ]
        row_counter, self.sistema_absorbedor_vars = create_section_radio(scrollable_frame, "4. Sistema absorbedor", sistema_absorbedor_items, row_counter)

        ventilador_mecanico_items = [
            ("5.1. Porcentaje de oxigeno", "oxigeno_var"),
            ("5.2. Volumen corriente y volumen minuto", "volumen_var"),
            ("5.3. Presión de vía aérea", "presion_via_aerea_var"),
            ("5.4. Frecuencia respiratoria", "frecuencia_respiratoria_var"),
            ("5.5. Modo ventilatorio", "modo_ventilatorio_var"),
            ("5.6. Alarmas", "alarmas_var"),
            ("5.7. Calibración de celda de oxígeno a 21% y al 100%", "calibracion_oxigeno"),
            ("5.8. Calibración de sensores de flujo", "calibracion_sensores_flujo")
        ]
        row_counter, self.ventilador_mecanico_vars = create_section_radio(
            scrollable_frame,  
            "5. Ventilador mecánico",  
            ventilador_mecanico_items,  
            row_counter,
            description_text="Verifique que el equipo muestra en pantalla los siguientes parámetros y realiza las siguientes acciones:"
        )

        seguridad_electrica_items = [
            ("6.1. Corriente de fuga", "corriente_fuga"),
            ("6.2. Tierra de protección", "tierra_proteccion"),
            ("6.3. Aislación", "")
        ]
        row_counter, self.seguridad_electrica_vars = create_section_radio(scrollable_frame, "6. Seguridad eléctrica", seguridad_electrica_items, row_counter)

        ttk.Label(scrollable_frame, text="7. Instrumentos de análisis", font=("Arial", 10, "bold")).grid(row=row_counter, column=0, columnspan=4, pady=10, sticky="w")
        row_counter += 1

        ttk.Label(scrollable_frame, text="EQUIPO").grid(row=row_counter, column=0, padx=5, pady=2, sticky="ew")
        ttk.Label(scrollable_frame, text="MARCA").grid(row=row_counter, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(scrollable_frame, text="MODELO").grid(row=row_counter, column=2, padx=5, pady=2, sticky="ew")
        ttk.Label(scrollable_frame, text="NUMERO SERIE").grid(row=row_counter, column=3, padx=5, pady=2, sticky="ew")
        row_counter += 1

        self.instrumento_equipo_entry1 = ttk.Entry(scrollable_frame, width=30) 
        self.instrumento_equipo_entry1.grid(row=row_counter, column=0, padx=5, pady=2, sticky="ew")
        self.instrumento_marca_entry1 = ttk.Entry(scrollable_frame)
        self.instrumento_marca_entry1.grid(row=row_counter, column=1, padx=5, pady=2, sticky="ew")
        self.instrumento_modelo_entry1 = ttk.Entry(scrollable_frame)
        self.instrumento_modelo_entry1.grid(row=row_counter, column=2, padx=5, pady=2, sticky="ew")
        self.instrumento_serie_entry1 = ttk.Entry(scrollable_frame)
        self.instrumento_serie_entry1.grid(row=row_counter, column=3, padx=5, pady=2, sticky="ew")
        row_counter += 1

        self.instrumento_equipo_entry2 = ttk.Entry(scrollable_frame, width=30)
        self.instrumento_equipo_entry2.grid(row=row_counter, column=0, padx=5, pady=2, sticky="ew")
        self.instrumento_marca_entry2 = ttk.Entry(scrollable_frame)
        self.instrumento_marca_entry2.grid(row=row_counter, column=1, padx=5, pady=2, sticky="ew")
        self.instrumento_modelo_entry2 = ttk.Entry(scrollable_frame)
        self.instrumento_modelo_entry2.grid(row=row_counter, column=2, padx=5, pady=2, sticky="ew")
        self.instrumento_serie_entry2 = ttk.Entry(scrollable_frame)
        self.instrumento_serie_entry2.grid(row=row_counter, column=3, padx=5, pady=2, sticky="ew")
        row_counter += 1

        ttk.Label(scrollable_frame, text="Observaciones:").grid(row=row_counter, column=0, sticky="w", padx=5, pady=10)
        row_counter += 1
        self.observaciones_text = tk.Text(scrollable_frame, height=5, width=60)
        self.observaciones_text.grid(row=row_counter, column=0, columnspan=4, padx=5, pady=2, sticky="ew")
        row_counter += 1

        ttk.Label(scrollable_frame, text="Observaciones (uso interno):").grid(row=row_counter, column=0, sticky="w", padx=5, pady=10)
        row_counter += 1
        self.observaciones_interno_text = tk.Text(scrollable_frame, height=3, width=60)
        self.observaciones_interno_text.grid(row=row_counter, column=0, columnspan=4, padx=5, pady=2, sticky="ew")
        row_counter += 1

        ttk.Label(scrollable_frame, text="EQUIPO OPERATIVO").grid(row=row_counter, column=0, sticky="w", padx=5, pady=10)
        self.equipo_operativo_var = tk.StringVar(value="")
        ttk.Radiobutton(scrollable_frame, text="SI", variable=self.equipo_operativo_var, value="SI").grid(row=row_counter, column=1)
        ttk.Radiobutton(scrollable_frame, text="NO", variable=self.equipo_operativo_var, value="NO").grid(row=row_counter, column=2)
        row_counter += 1
        
        ttk.Label(scrollable_frame, text="").grid(row=row_counter, column=0, columnspan=4, pady=5)
        row_counter += 1

        ttk.Label(scrollable_frame, text="NOMBRE TÉCNICO/INGENIERO:").grid(row=row_counter, column=0, sticky="w", padx=5, pady=5)
        self.nombre_tecnico_entry = ttk.Entry(scrollable_frame, width=40)
        self.nombre_tecnico_entry.grid(row=row_counter, column=1, columnspan=3, sticky="ew", padx=5, pady=5)
        row_counter += 1
        
        ttk.Label(scrollable_frame, text="").grid(row=row_counter, column=0, columnspan=4, pady=5)
        row_counter += 1

        ttk.Label(scrollable_frame, text="EMPRESA RESPONSABLE:").grid(row=row_counter, column=0, sticky="w", padx=5, pady=5)
        self.empresa_responsable_entry = ttk.Entry(scrollable_frame, width=40)
        self.empresa_responsable_entry.grid(row=row_counter, column=1, columnspan=3, sticky="ew", padx=5, pady=5)
        row_counter += 1
        
        ttk.Label(scrollable_frame, text="").grid(row=row_counter, column=0, columnspan=4, pady=5)
        row_counter += 1

        button_frame_bottom = ttk.Frame(scrollable_frame)
        button_frame_bottom.grid(row=row_counter, column=0, columnspan=4, pady=20)  

        ttk.Button(button_frame_bottom, text="Descargar PDF", command=self.save_and_download_maq_anestesia_data).pack(side=tk.LEFT, padx=10)


    def _get_maq_anestesia_data(self):
        try:
            data = {
                "Marca": self.marca_entry.get(),
                "Modelo": self.modelo_entry.get(),
                "S/N": self.sn_entry.get(),
                "N_Inventario": self.n_inventario_entry.get(),  
                "Fecha": self.fecha_entry.get(),
                "Ubicacion": self.ubicacion_entry.get(),
                "Instrumento_Equipo1": self.instrumento_equipo_entry1.get(),
                "Instrumento_Marca1": self.instrumento_marca_entry1.get(),
                "Instrumento_Modelo1": self.instrumento_modelo_entry1.get(),
                "Instrumento_Serie1": self.instrumento_serie_entry1.get(),
                "Instrumento_Equipo2": self.instrumento_equipo_entry2.get(),
                "Instrumento_Marca2": self.instrumento_marca_entry2.get(),
                "Instrumento_Modelo2": self.instrumento_modelo_entry2.get(),
                "Instrumento_Serie2": self.instrumento_serie_entry2.get(),
                "Observaciones": self.observaciones_text.get("1.0", tk.END).strip(),
                "Observaciones_Interno": self.observaciones_interno_text.get("1.0", tk.END).strip(),
                "Equipo_Operativo": self.equipo_operativo_var.get(),
                "Nombre_Tecnico": self.nombre_tecnico_entry.get(),
                "Empresa_Responsable": self.empresa_responsable_entry.get(),
                "Chequeo_Visual": [var.get() for var in self.chequeo_visual_vars],
                "Sistema_Alta_Presion": [var.get() for var in self.sistema_alta_presion_vars],
                "Sistema_Baja_Presion": [var.get() for var in self.sistema_baja_presion_vars],
                "Sistema_Absorbedor": [var.get() for var in self.sistema_absorbedor_vars],
                "Ventilador_Mecanico": [var.get() for var in self.ventilador_mecanico_vars],
                "Seguridad_Electrica": [var.get() for var in self.seguridad_electrica_vars],
            }
            return data
        except AttributeError as e:
            messagebox.showerror("Error de datos", f"Faltan elementos del formulario. Asegúrese de que todas las variables estén inicializadas. Error: {e}")
            return {}
            
    def _validate_maq_anestesia_data(self, data):
        # Mandatory fields for "Información General"
        required_entries = {
            "Marca": "Marca",
            "Modelo": "Modelo",
            "S/N": "S/N",
            "N_Inventario": "N/Inventario",
            "Fecha": "Fecha",
            "Ubicacion": "Ubicación"
        }
        for field, display_name in required_entries.items():
            if not data.get(field):
                messagebox.showwarning("Campo Obligatorio", f"El campo '{display_name}' es obligatorio.")
                return False

        # Mandatory radio button sections (all must have 'OK', 'NO', or 'N/A' selected)
        radio_sections = {
            "Chequeo Visual": data["Chequeo_Visual"],
            "Sistema de Alta Presión": data["Sistema_Alta_Presion"],
            "Sistema de Baja Presión": data["Sistema_Baja_Presion"],
            "Sistema Absorbedor": data["Sistema_Absorbedor"],
            "Ventilador Mecánico": data["Ventilador_Mecanico"],
            "Seguridad Eléctrica": data["Seguridad_Electrica"]
        }

        for section_name, values in radio_sections.items():
            if not values or any(val == "" for val in values): # Check if any radio button is not selected
                messagebox.showwarning("Campo Obligatorio", f"Todos los ítems en '{section_name}' deben ser seleccionados (OK/NO/N/A).")
                return False

        # Mandatory "Equipo Operativo" radio button
        if not data.get("Equipo_Operativo"):
            messagebox.showwarning("Campo Obligatorio", "Debe seleccionar si el 'EQUIPO OPERATIVO' (SI/NO).")
            return False

        # Mandatory fields for signatures
        required_signature_fields = {
            "Nombre_Tecnico": "Nombre Técnico/Ingeniero",
            "Empresa_Responsable": "Empresa Responsable"
        }
        for field, display_name in required_signature_fields.items():
            if not data.get(field):
                messagebox.showwarning("Campo Obligatorio", f"El campo '{display_name}' es obligatorio.")
                return False

        return True


    def save_and_download_maq_anestesia_data(self):
        data = self._get_maq_anestesia_data()
        if not data:
            return # _get_maq_anestesia_data already showed error

        if not self._validate_maq_anestesia_data(data):
            return # Validation failed, message already shown

        print("Datos guardados (simulado):", data)
        self.download_maq_anestesia_pdf(data)


    def download_maq_anestesia_pdf(self, data):
        # Data validation already happened in save_and_download_maq_anestesia_data
        
        sn_value = data.get("S/N", "SIN_NUMERO_SERIE").replace("/", "_").replace("\\", "_")

        default_filename = f"MP_PREV_ANESTESIA_{sn_value}.pdf"

        save_directory = os.getcwd()
        
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        file_path = os.path.join(save_directory, default_filename)

        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_left_margin(15)
        pdf.set_right_margin(15)
        pdf.set_top_margin(15)
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font("Arial", "", 8)  
        pdf.cell(0, 5, "Chrt", 0, 0, 'R')  
        pdf.ln(5) 
        
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, "HOSPITAL REGIONAL DE TALCA", ln=True, align="C")
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 7, "PAUTA MANTENCIÓN MAQUINA DE ANESTESIA", ln=True, align="C")
        pdf.ln(5)

        pdf.set_font("Arial", "", 10)
        label_width = 40
        entry_width = 0 

        pdf.cell(label_width, 7, "MARCA:", 0, 0, 'L')
        pdf.cell(entry_width, 7, data.get("Marca", "N/A"), 0, 1, 'L')
        
        pdf.cell(label_width, 7, "MODELO:", 0, 0, 'L')
        pdf.cell(entry_width, 7, data.get("Modelo", "N/A"), 0, 1, 'L')
        
        pdf.cell(label_width, 7, "S/N:", 0, 0, 'L')
        pdf.cell(entry_width, 7, data.get("S/N", "N/A"), 0, 1, 'L')

        pdf.cell(label_width, 7, "N/INVENTARIO:", 0, 0, 'L')
        pdf.cell(entry_width, 7, data.get("N_Inventario", "N/A"), 0, 1, 'L')  

        pdf.cell(label_width, 7, "FECHA:", 0, 0, 'L')
        pdf.cell(entry_width, 7, data.get("Fecha", "N/A"), 0, 1, 'L')
        
        pdf.cell(label_width, 7, "UBICACIÓN:", 0, 0, 'L')
        pdf.cell(entry_width, 7, data.get("Ubicacion", "N/A"), 0, 1, 'L')  
        
        pdf.ln(5)

        def add_section_to_pdf(pdf_obj, title, items, vars_data, description_text=None):
            pdf_obj.set_font("Arial", "B", 10)
            pdf_obj.cell(0, 7, title, ln=True)
            
            if description_text:
                pdf_obj.set_font("Arial", "", 10)
                pdf_obj.multi_cell(0, 6, description_text) 
            
            page_width = pdf_obj.w - pdf_obj.l_margin - pdf_obj.r_margin 
            check_col_width = 15 
            total_check_cols_width = check_col_width * 3
            item_text_width = page_width - total_check_cols_width  

            pdf_obj.set_x(pdf_obj.l_margin + item_text_width)
            pdf_obj.set_font("Arial", "", 9)  
            pdf_obj.cell(check_col_width, 7, "OK", 0, 0, 'C')
            pdf_obj.cell(check_col_width, 7, "NO", 0, 0, 'C')
            pdf_obj.cell(check_col_width, 7, "N/A", 0, 1, 'C') 
            
            pdf_obj.set_font("Arial", "", 10)
            for i, (item_text, _) in enumerate(items):
                start_y = pdf_obj.get_y()
                
                if start_y + 6 > pdf_obj.page_break_trigger:
                    pdf_obj.add_page()
                    pdf_obj.set_font("Arial", "B", 10)
                    pdf_obj.cell(0, 7, title, ln=True)
                    if description_text:
                        pdf_obj.set_font("Arial", "", 10)
                        pdf_obj.multi_cell(0, 6, description_text)
                    
                    pdf_obj.set_x(pdf_obj.l_margin + item_text_width)
                    pdf_obj.set_font("Arial", "", 9)  
                    pdf_obj.cell(check_col_width, 7, "OK", 0, 0, 'C')
                    pdf_obj.cell(check_col_width, 7, "NO", 0, 0, 'C')
                    pdf_obj.cell(check_col_width, 7, "N/A", 0, 1, 'C')  
                    pdf_obj.set_font("Arial", "", 10)
                    start_y = pdf_obj.get_y() 

                pdf_obj.set_x(pdf_obj.l_margin) 
                pdf_obj.multi_cell(item_text_width, 6, item_text, 0, 'L') 
                
                end_y = pdf_obj.get_y()
                
                pdf_obj.set_xy(pdf_obj.l_margin + item_text_width, start_y)  
                
                status = vars_data[i] if i < len(vars_data) else ""
                
                pdf_obj.cell(check_col_width, 6, "X" if status == "OK" else "", 0, 0, 'C')
                pdf_obj.cell(check_col_width, 6, "X" if status == "NO" else "", 0, 0, 'C')
                pdf_obj.cell(check_col_width, 6, "X" if status == "N/A" else "", 0, 0, 'C')  
                
                pdf_obj.ln(end_y - start_y)  
            pdf_obj.ln(5)

        chequeo_visual_items = [
            ("1.1. Carcasa Frontal y Trasera", ""),
            ("1.2. Estado de Software", ""),
            ("1.3. Panel frontal", ""),
            ("1.4. Batería de respaldo", "")
        ]
        add_section_to_pdf(pdf, "1. Chequeo Visual", chequeo_visual_items, data["Chequeo_Visual"])

        sistema_alta_presion_items = [
            ("2.1. Chequeo de yugo de O2, N2O, Aire", ""),
            ("2.2. Revisión o reemplazo de empaquetadura de yugo", ""),
            ("2.3. Verificación de entrada de presión", ""),
            ("2.4. Revisión y calibración de válvulas de flujometro de O2, N2O, Aire", "")
        ]
        add_section_to_pdf(pdf, "2. Sistema de Alta Presión", sistema_alta_presion_items, data["Sistema_Alta_Presion"])

        sistema_baja_presion_items = [
            ("3.1. Revisión y calibración de válvula de flujómetro de N2O", ""),
            ("3.2. Revisión y calibración de válvula de flujometro de 02", ""),
            ("3.3. Revisión y calibración de válvula de flujometro de Aire", ""),
            ("3.4. Chequeo de fugas", ""),
            ("3.5. Verificación de flujos", ""),
            ("3.6. Verificación de regulador de 2da (segunda) etapa", ""),
            ("3.7. Revisión de sistema de corte N20/Aire por falta de 02", ""),
            ("3.8. Revisión de sistema proporción de 02/N20", ""),
            ("3.9. Revisión de manifold de vaporizadores", "")
        ]
        add_section_to_pdf(pdf, "3. Sistema de baja presión", sistema_baja_presion_items, data["Sistema_Baja_Presion"])

        sistema_absorbedor_items = [
            ("4.1. Revisión o reemplazo de empaquetadura de canister", ""),
            ("4.2. Revisión de válvula APL", ""),
            ("4.3. Verificación de manómetro de presión de vía aérea (ajuste a cero)", ""),
            ("4.4. Revisión de válvula inhalatoria", ""),
            ("4.5. Revisión de válvula exhalatoria", ""),
            ("4.6. Chequeo de fugas", ""),
            ("4.7. Hermeticidad", "")
        ]
        add_section_to_pdf(pdf, "4. Sistema absorbedor", sistema_absorbedor_items, data["Sistema_Absorbedor"])

        ventilador_mecanico_items = [
            ("5.1. Porcentaje de oxigeno", ""),
            ("5.2. Volumen corriente y volumen minuto", ""),
            ("5.3. Presión de vía aérea", ""),
            ("5.4. Frecuencia respiratoria", ""),
            ("5.5. Modo ventilatorio", ""),
            ("5.6. Alarmas", ""),
            ("5.7. Calibración de celda de oxígeno a 21% y al 100%", ""),
            ("5.8. Calibración de sensores de flujo", "")
        ]
        add_section_to_pdf(
            pdf,  
            "5. Ventilador mecánico",  
            ventilador_mecanico_items,  
            data["Ventilador_Mecanico"],
            description_text="Verifique que el equipo muestra en pantalla los siguientes parámetros y realiza las siguientes acciones:"
        )
        
        seguridad_electrica_items = [
            ("6.1. Corriente de fuga", ""),
            ("6.2. Tierra de protección", ""),
            ("6.3. Aislación", "")
        ]
        add_section_to_pdf(pdf, "6. Seguridad eléctrica", seguridad_electrica_items, data["Seguridad_Electrica"])

        # 7. Instrumentos de análisis - REVISED to ensure row height adjusts and fits page width
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 7, "7. Instrumentos de análisis", ln=True)
        pdf.set_font("Arial", "", 10)
        
        # Calculate available width for the table
        page_width = pdf.w - pdf.l_margin - pdf.r_margin 
        # Define column width ratios (Equipo:Marca:Modelo:Numero Serie)
        # Sum of ratios: 4 + 2 + 2 + 3 = 11
        # Example ratios, adjust as needed for optimal look
        ratio_equipo = 4.0/11.0 
        ratio_marca = 2.0/11.0
        ratio_modelo = 2.0/11.0
        ratio_serie = 3.0/11.0

        col_widths = [
            page_width * ratio_equipo,
            page_width * ratio_marca,
            page_width * ratio_modelo,
            page_width * ratio_serie
        ]
        
        header_cell_height = 7
        line_height = 6 # Standard line height for multi_cell content

        # Table headers
        # Ensure header cells are drawn with the calculated widths
        pdf.cell(col_widths[0], header_cell_height, "EQUIPO", 1, 0, 'C')
        pdf.cell(col_widths[1], header_cell_height, "MARCA", 1, 0, 'C')
        pdf.cell(col_widths[2], header_cell_height, "MODELO", 1, 0, 'C')
        pdf.cell(col_widths[3], header_cell_height, "NUMERO SERIE", 1, 1, 'C')

        def add_instrument_row_adaptive(pdf_obj, equipo, marca, modelo, serie, widths, line_height):
            # Store initial positions
            start_x = pdf_obj.get_x()
            start_y = pdf_obj.get_y()
            
            # 1. Calculate the height required by each cell's content if wrapped
            # Temporarily set a large page break trigger to allow multi_cell to calculate full height
            original_page_break_trigger = pdf_obj.page_break_trigger
            pdf_obj.page_break_trigger = float('inf') 
            
            # Use current_x and current_y to simulate multi_cell without altering actual cursor for measurement
            temp_x = pdf_obj.get_x()
            temp_y = pdf_obj.get_y()

            pdf_obj.set_xy(temp_x, temp_y) 
            pdf_obj.multi_cell(widths[0], line_height, equipo, 0, 'L') # Calculate height, no border, no line break
            h_equipo = pdf_obj.get_y() - temp_y

            pdf_obj.set_xy(temp_x + widths[0], temp_y) 
            pdf_obj.multi_cell(widths[1], line_height, marca, 0, 'L')
            h_marca = pdf_obj.get_y() - temp_y

            pdf_obj.set_xy(temp_x + widths[0] + widths[1], temp_y)
            pdf_obj.multi_cell(widths[2], line_height, modelo, 0, 'L')
            h_modelo = pdf_obj.get_y() - temp_y

            pdf_obj.set_xy(temp_x + widths[0] + widths[1] + widths[2], temp_y)
            pdf_obj.multi_cell(widths[3], line_height, serie, 0, 'L')
            h_serie = pdf_obj.get_y() - temp_y

            # Restore original page break trigger
            pdf_obj.page_break_trigger = original_page_break_trigger
            
            # Determine the maximum height needed for this row, ensuring a minimum height
            row_height = max(line_height, h_equipo, h_marca, h_modelo, h_serie)
            
            # Reset cursor to initial position after measuring
            pdf_obj.set_xy(start_x, start_y)
            
            # 2. Check for page break before drawing the actual row
            # Now use the real page break trigger
            if start_y + row_height > pdf_obj.page_break_trigger:
                pdf_obj.add_page()
                # Re-print headers on new page
                pdf_obj.set_font("Arial", "B", 10)
                pdf_obj.cell(widths[0], header_cell_height, "EQUIPO", 1, 0, 'C')
                pdf_obj.cell(widths[1], header_cell_height, "MARCA", 1, 0, 'C')
                pdf_obj.cell(widths[2], header_cell_height, "MODELO", 1, 0, 'C')
                pdf_obj.cell(widths[3], header_cell_height, "NUMERO SERIE", 1, 1, 'C')
                pdf_obj.set_font("Arial", "", 10)
                start_x = pdf_obj.get_x() # Reset start_x/y for new page
                start_y = pdf_obj.get_y()

            # 3. Draw the cells and their contents
            current_x = start_x
            
            # Draw Equipo cell and text
            pdf_obj.set_xy(current_x, start_y)
            # Use pdf_obj.rect to draw the border for the full row_height
            pdf_obj.rect(current_x, start_y, widths[0], row_height)
            pdf_obj.multi_cell(widths[0], line_height, equipo, 0, 'L', False) # No border with multi_cell here
            
            # Draw Marca cell and text
            current_x += widths[0]
            pdf_obj.set_xy(current_x, start_y)
            pdf_obj.rect(current_x, start_y, widths[1], row_height)
            pdf_obj.multi_cell(widths[1], line_height, marca, 0, 'L', False)

            # Draw Modelo cell and text
            current_x += widths[1]
            pdf_obj.set_xy(current_x, start_y)
            pdf_obj.rect(current_x, start_y, widths[2], row_height)
            pdf_obj.multi_cell(widths[2], line_height, modelo, 0, 'L', False)
            
            # Draw Numero Serie cell and text
            current_x += widths[2]
            pdf_obj.set_xy(current_x, start_y)
            pdf_obj.rect(current_x, start_y, widths[3], row_height)
            pdf_obj.multi_cell(widths[3], line_height, serie, 0, 'L', False)

            # After drawing all cells for the row, explicitly move the cursor down
            # to prepare for the next row.
            pdf_obj.set_y(start_y + row_height)
            pdf_obj.set_x(pdf_obj.l_margin) # Reset X to left margin for the next row

        add_instrument_row_adaptive(pdf, 
                           data.get("Instrumento_Equipo1", ""), 
                           data.get("Instrumento_Marca1", ""), 
                           data.get("Instrumento_Modelo1", ""), 
                           data.get("Instrumento_Serie1", ""),
                           col_widths, line_height)

        add_instrument_row_adaptive(pdf, 
                           data.get("Instrumento_Equipo2", ""), 
                           data.get("Instrumento_Marca2", ""), 
                           data.get("Instrumento_Modelo2", ""), 
                           data.get("Instrumento_Serie2", ""),
                           col_widths, line_height)
        pdf.ln(5)

        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 7, "Observaciones:", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 6, data.get("Observaciones", "N/A")) 
        pdf.ln(5)

        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 7, "Observaciones (uso interno):", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 6, data.get("Observaciones_Interno", "N/A")) 
        pdf.ln(5)

        pdf.set_font("Arial", "B", 10)
        pdf.cell(60, 7, "EQUIPO OPERATIVO", 0, 0, 'L')
        
        check_box_label_width = 15
        check_box_width = 7
        
        pdf.cell(check_box_label_width, 7, "SI", 0, 0, 'L')
        pdf.cell(check_box_width, 7, "X" if data.get("Equipo_Operativo") == "SI" else "", 1, 0, 'C')
        pdf.cell(check_box_label_width, 7, "NO", 0, 0, 'L') 
        pdf.cell(check_box_width, 7, "X" if data.get("Equipo_Operativo") == "NO" else "", 1, 1, 'C') 
        pdf.ln(5)

        pdf.set_font("Arial", "B", 10)
        pdf.cell(70, 7, "NOMBRE TÉCNICO/INGENIERO:", 0, 0, 'L')
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 7, data.get("Nombre_Tecnico", "N/A"), 0, 1, 'L')
        pdf.ln(5) 

        pdf.set_font("Arial", "B", 10)
        pdf.cell(70, 7, "EMPRESA RESPONSABLE:", 0, 0, 'L')
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 7, data.get("Empresa_Responsable", "N/A"), 0, 1, 'L')
        pdf.ln(30) 

        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 7, "FIRMA TÉCNICO ENCARGADO", 0, 2, 'C')
        pdf.ln(25) 

        pdf.cell(0, 7, "RECEPCIÓN CONFORME PERSONAL INGENIERÍA CLÍNICA", 0, 2, 'C')
        pdf.ln(25) 

        pdf.cell(0, 7, "RECEPCIÓN CONFORME PERSONAL CLÍNICO", 0, 2, 'C')
        pdf.ln(25) 

        try:
            pdf.output(file_path)
            messagebox.showinfo("Descarga Exitosa", f"El PDF ha sido guardado en: {file_path}")
            
            # Clear the "Instrumentos de análisis" entries after successful PDF generation
            self.instrumento_equipo_entry1.delete(0, tk.END)
            self.instrumento_marca_entry1.delete(0, tk.END)
            self.instrumento_modelo_entry1.delete(0, tk.END)
            self.instrumento_serie_entry1.delete(0, tk.END)
            self.instrumento_equipo_entry2.delete(0, tk.END)
            self.instrumento_marca_entry2.delete(0, tk.END)
            self.instrumento_modelo_entry2.delete(0, tk.END)
            self.instrumento_serie_entry2.delete(0, tk.END)
            
            # Clear other fields (optional, but good practice after generating document)
            self.marca_entry.delete(0, tk.END)
            self.modelo_entry.delete(0, tk.END)
            self.sn_entry.delete(0, tk.END)
            self.n_inventario_entry.delete(0, tk.END)
            self.fecha_entry.delete(0, tk.END)
            self.ubicacion_entry.delete(0, tk.END)
            self.observaciones_text.delete("1.0", tk.END)
            self.observaciones_interno_text.delete("1.0", tk.END)
            self.nombre_tecnico_entry.delete(0, tk.END)
            self.empresa_responsable_entry.delete(0, tk.END)

            # Reset radio buttons
            for var in self.chequeo_visual_vars:
                var.set("")
            for var in self.sistema_alta_presion_vars:
                var.set("")
            for var in self.sistema_baja_presion_vars:
                var.set("")
            for var in self.sistema_absorbedor_vars:
                var.set("")
            for var in self.ventilador_mecanico_vars:
                var.set("")
            for var in self.seguridad_electrica_vars:
                var.set("")
            self.equipo_operativo_var.set("")

            # Close the Toplevel window after successful PDF generation and message display
            if hasattr(self, 'maq_anestesia_window') and self.maq_anestesia_window.winfo_exists():
                self.maq_anestesia_window.destroy()

        except Exception as e:
            messagebox.showerror("Error de Descarga", f"Error al guardar el PDF: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MaintenanceApp(root)
    root.mainloop()