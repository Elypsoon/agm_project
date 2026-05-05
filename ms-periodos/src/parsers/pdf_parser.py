import pdfplumber
import re

class ScheduleParser:
    def __init__(self):
        # NRCs are 5-digit anchors in BUAP programming documents[cite: 1, 2]
        self.nrc_pattern = re.compile(r'^(\d{5})')

    def is_virtual_room(self, salon_code: str) -> bool:
        """Flags rooms like 1CCOV or keywords as virtual."""
        virtual_indicators = ["VIRTUAL", "LINEA", "REMOTO", "V"]
        clean_code = salon_code.upper().strip()
        
        # Check if the code ends in 'V' or matches specific virtual keywords
        if clean_code.endswith("V") or any(word in clean_code for word in virtual_indicators):
            return True
        return False

    def extract_from_pdf(self, pdf_path: str):
        catalog = []
        current_entry = None

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table:
                    continue

                for row in table:
                    # Clean cells and handle multi-line text
                    parts = [str(c).strip().replace('\n', ' ') if c else "" for c in row]
                    
                    # Skip headers and empty noise
                    if not parts or "NRC" in parts[0] or "FACULTAD" in parts[0]:
                        continue

                    # Case 1: Detect a new Subject
                    if self.nrc_pattern.match(parts[0]):
                        current_entry = {
                            "nrc": parts[0],
                            "clave": parts[1],
                            "materia": parts[2],
                            "seccion": parts[3],
                            "horarios": []
                        }
                        catalog.append(current_entry)

                    # Ensure we have an active subject and ignore summary footers
                    if current_entry:
                        dia = parts[4]
                        hora = parts[5]
                        profesor = parts[6]
                        salon = parts[7]

                        # Valid schedule rows must have a day AND a real time
                        # This ignores the 'Summary' row where dia is '-' or empty
                        if dia and hora and hora != "-":
                            current_entry["horarios"].append({
                                "dia": dia,
                                "hora": hora,
                                "profesor": profesor,
                                "salon": salon if salon else "POR ASIGNAR", # Handles empty cells
                                "es_virtual": self.is_virtual_room(salon)
                            })

        return catalog