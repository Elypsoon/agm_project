import os
import psycopg2
import sys

def sync():
    print("[Sync] Iniciando sincronización de réplicas de alumnos desde db-alumnos...")
    
    al_host = "db-alumnos"
    al_port = 5432
    al_user = "postgres"
    al_pass = "alumnos_dev_2026"
    al_db = "agm_alumnos_db"
    
    as_host = os.environ.get("POSTGRES_HOST", "db-asistencias")
    as_port = int(os.environ.get("POSTGRES_PORT", 5432))
    as_user = os.environ.get("POSTGRES_USER", "postgres")
    as_pass = os.environ.get("POSTGRES_PASSWORD", "asistencias_dev_2026")
    as_db = os.environ.get("POSTGRES_DB", "agm_asistencias_db")
    
    try:
        al_conn = psycopg2.connect(
            host=al_host,
            port=al_port,
            user=al_user,
            password=al_pass,
            database=al_db
        )
        al_cur = al_conn.cursor()
        al_cur.execute("SELECT id, user_id, matricula, nombre_completo FROM alumnos")
        alumnos = al_cur.fetchall()
        al_cur.close()
        al_conn.close()
        
        print(f"[Sync] Leídos {len(alumnos)} alumnos desde db-alumnos.")
        
        as_conn = psycopg2.connect(
            host=as_host,
            port=as_port,
            user=as_user,
            password=as_pass,
            database=as_db
        )
        as_cur = as_conn.cursor()
        
        updated_count = 0
        inserted_count = 0
        
        for al_id, user_id, matricula, nombre in alumnos:
            as_cur.execute("SELECT id FROM replica_alumnos WHERE id = %s", (al_id,))
            exists = as_cur.fetchone()
            
            if exists:
                as_cur.execute(
                    "UPDATE replica_alumnos SET user_id = %s, matricula = %s, nombre_completo = %s WHERE id = %s",
                    (user_id, matricula or '', nombre, al_id)
                )
                updated_count += 1
            else:
                as_cur.execute(
                    "INSERT INTO replica_alumnos (id, user_id, matricula, nombre_completo) VALUES (%s, %s, %s, %s)",
                    (al_id, user_id, matricula or '', nombre)
                )
                inserted_count += 1
                
        as_conn.commit()
        as_cur.close()
        as_conn.close()
        
        print(f"[Sync] Sincronización finalizada con éxito. Insertados: {inserted_count}, Actualizados: {updated_count}")
        
    except Exception as e:
        print(f"[Sync] [ERROR] Error durante la sincronización: {str(e)}")

if __name__ == "__main__":
    sync()
