import httpx
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

ALUMNOS_SERVICE_URL = "http://127.0.0.1:8000/docentes/"

async def fetch_docente_id_by_name(clean_name: str) -> str | None:
    """
    Queries the Docentes microservice using the clean professor name.
    """
    if not clean_name or clean_name == "POR ASIGNAR":
        return None

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(ALUMNOS_SERVICE_URL, params={"search": clean_name})
            
            if response.status_code == 200:
                res_data = response.json()
                docentes = res_data.get("data", {}).get("docentes", [])
                
                if docentes:
                    return docentes[0].get("id")
                    
            logger.warning(f"No match found in Docente service for: {clean_name}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to talk to Docente microservice: {str(e)}")
            return None