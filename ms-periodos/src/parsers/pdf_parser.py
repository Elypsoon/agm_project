import pdfplumber
import re

class ScheduleParser:
    def __init__(self):
        self.nrc_pattern = re.compile(r'^(\d{5})')

    def is_virtual_room(self, salon_code: str) -> bool:
        """Flags rooms like 1CCOV or keywords as virtual."""
        virtual_indicators = ["VIRTUAL", "LINEA", "REMOTO", "V"]
        clean_code = salon_code.upper().strip() if salon_code else ""
        if clean_code.endswith("V") or any(word in clean_code for word in virtual_indicators):
            return True
        return False

    def clean_professor_name(self, raw_name: str) -> str:
        """Cleans formatting artifacts."""
        if not raw_name or raw_name.strip() in ["POR ASIGNAR", ""]:
            return "POR ASIGNAR"
        
        cleaned = raw_name.replace(" - ", " ").replace("-", " ")
        return " ".join(cleaned.split()).upper()

    def extract_metadata_from_text(self, page_text: str):
        """Scans the banner text to extract Campus and Plan de Estudios."""
        # 1. Determine Campus
        campus = "SAN_MANUEL"
        if "CU2" in page_text:
            campus = "CU2"
        elif "SAN MANUEL" in page_text:
            campus = "SAN_MANUEL"

        # 2. Determine Plan de Estudios
        plan_estudios = "ITI"
        if "CIENCIAS DE LA COMPUTACIÓN" in page_text:
            plan_estudios = "LCC"
        elif "INGENIERÍA EN TECNOLOGÍAS" in page_text:
            plan_estudios = "ITI"
        elif "INGENIERÍA EN CIENCIAS" in page_text:
            plan_estudios = "ICC"
        elif "INGENIERÍA EN CIENCIA DE DATOS" in page_text:
            plan_estudios = "ICD"
        elif "INGENIERÍA EN CIBERSEGURIDAD" in page_text:
            plan_estudios = "ISC"

        return campus, plan_estudios

    def extract_from_pdf(self, pdf_path: str):
        catalog = []
        current_entry = None

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                campus, plan_estudios = self.extract_metadata_from_text(page_text)

                table = page.extract_table()
                if not table:
                    continue

                for row in table:
                    parts = [str(c).strip().replace('\n', ' ') if c else "" for c in row]
                    
                    if not parts or "NRC" in parts[0] or "FACULTAD" in parts[0]:
                        continue

                    # Case 1: Detect a new Subject
                    if self.nrc_pattern.match(parts[0]):
                        current_entry = {
                            "nrc": parts[0],
                            "clave": parts[1],
                            "materia": parts[2],
                            "seccion": parts[3],
                            "campus": campus,
                            "plan_estudios": plan_estudios,
                            "horarios": []
                        }
                        catalog.append(current_entry)

                    # Ensure we have an active subject
                    if current_entry:
                        dia = parts[4]
                        hora = parts[5]
                        profesor = parts[6]
                        salon = parts[7]

                        if dia and hora and hora != "-":
                            profesor_limpio = self.clean_professor_name(profesor)
                            
                            current_entry["horarios"].append({
                                "dia": dia,
                                "hora": hora,
                                "profesor": profesor_limpio,
                                "salon": salon if salon else "POR ASIGNAR",
                                "es_virtual": self.is_virtual_room(salon)
                            })

        return catalog