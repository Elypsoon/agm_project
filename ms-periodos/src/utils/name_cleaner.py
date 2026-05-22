def clean_professor_name(raw_name):
    if not raw_name or raw_name == "POR ASIGNAR":
        return "POR ASIGNAR"
        
    cleaned = raw_name.replace(" - ", " ")
    
    cleaned = cleaned.replace("-", " ")
    
    cleaned = " ".join(cleaned.split())
    
    return cleaned.upper()