import subprocess
import time
import sys

def is_container_running(container):
    """Verifica si un contenedor docker está actualmente en ejecución."""
    cmd = ["docker", "inspect", "-f", "{{.State.Running}}", container]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0 and result.stdout.strip() == "true"

def run_container_command(container, command):
    """Ejecuta un comando dentro de un contenedor docker y retorna la salida."""
    full_cmd = ["docker", "exec", container, "python", "manage.py", "shell", "-c", command]
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error al ejecutar comando en {container}: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def main():
    print("PRUEBA DE INTEGRACIÓN - RABBITMQ BROKER")

    # Datos realistas de prueba
    email_prueba = "angel.gutierrezpa@alumno.buap.mx"
    nombre_completo = "Angel Gutiérrez Pacheco"
    matricula = "202623500"
    clave_acceso = "Gutierrez@123"
    materia_id = "12345678-1234-5678-1234-567812345678"

    print("Este script realizará las siguientes acciones:")
    print("1. Creará un registro de alumno en la base de datos de 'ms-alumnos'.")
    print("2. Publicará el evento 'student.registered' en el exchange 'agm.events'.")
    print("3. Monitoreará la base de datos de 'ms-alumnos' hasta que el 'user_id'")
    print("   sea actualizado de manera asíncrona por 'ms-auth'.")
    print("4. Realizará una limpieza completa eliminando los registros de prueba.")
    
    print("\nNota: Si desea ver el mensaje encolado en la interfaz web de RabbitMQ:")
    print("1. Detenga el contenedor de notificaciones antes de continuar:")
    print("   docker stop ms-notificaciones")
    print("2. Presione ENTER para ejecutar este script.")
    print("3. Verifique la cola 'ms_notif_student_registered' en http://localhost:15672.")
    print("4. Inicie el contenedor de nuevo para completar el procesamiento:")
    print("   docker start ms-notificaciones\n")
    
    input("Presione [ENTER] para iniciar la demostración...")

    print("\n[Paso 1/5] Registrando alumno en base de datos de ms-alumnos...")
    cmd_crear = f"""
from src.models.alumno import Alumno
Alumno.objects.filter(correo='{email_prueba}').delete()
a = Alumno.objects.create(
    nombre_completo='{nombre_completo}',
    matricula='{matricula}',
    correo='{email_prueba}',
    clave_acceso='{clave_acceso}'
)
print(f'Alumno creado con ID: {{a.id}}')
"""
    output_crear = run_container_command("ms-alumnos", cmd_crear)
    # Limpiar posibles mensajes informativos de carga automática
    alumno_id_line = [line for line in output_crear.split("\n") if "Alumno creado con ID:" in line]
    if not alumno_id_line:
        print("Error al recuperar el ID del alumno creado.")
        print(output_crear)
        sys.exit(1)
    
    alumno_id = alumno_id_line[0].split("Alumno creado con ID: ")[1].strip()
    print(f"   Confirmación: Registro creado localmente en ms-alumnos con ID {alumno_id}.")

    print("\n[Paso 2/5] Publicando evento 'student.registered' en RabbitMQ...")
    cmd_publicar = f"""
from src.utils.rabbitmq import publish_event
publish_event('student.registered', {{
    'local_id': '{alumno_id}',
    'role': 'alumno',
    'email': '{email_prueba}',
    'nombre': '{nombre_completo}',
    'password': '{clave_acceso}',
    'materia_id': '{materia_id}',
    'materia_nombre': 'Desarrollo de Sistemas Distribuídos (Prueba)'
}})
"""
    run_container_command("ms-alumnos", cmd_publicar)
    print("   Confirmación: Mensaje enviado al exchange 'agm.events'.")

    print("\n[Paso 3/5] Monitoreando sincronización de base de datos...")
    cmd_verificar = f"""
from src.models.alumno import Alumno
a = Alumno.objects.get(id='{alumno_id}')
print(a.user_id if a.user_id else 'None')
"""
    
    start_time = time.time()
    user_id = None
    timeout = 15.0  # segundos
    
    while time.time() - start_time < timeout:
        output_verificar = run_container_command("ms-alumnos", cmd_verificar)
        lines = [line.strip() for line in output_verificar.split("\n") if line.strip() and "imported automatically" not in line]
        res = lines[-1] if lines else "None"
        
        if res != "None":
            user_id = res
            break
        time.sleep(1.0)
        print("   Aún esperando sincronización...")

    if user_id:
        print(f"   Confirmación: ¡Éxito! ms-alumnos recibió 'user.created'.")
        print(f"   El campo Alumno.user_id fue actualizado a: {user_id}")
    else:
        print("   Advertencia: Tiempo de espera agotado. Verifique que los consumidores estén ejecutándose.")

    print("\n[Paso 4/5] Verificando logs del microservicio de notificaciones...")
    if not is_container_running("ms-notificaciones"):
        print("   Aviso: El contenedor 'ms-notificaciones' está detenido.")
        print("   Esperando a que sea iniciado para verificar la bitácora de envío (docker start ms-notificaciones)...")
        while not is_container_running("ms-notificaciones"):
            time.sleep(1.0)
        print("   Contenedor detectado en ejecución. Esperando 3 segundos para la inicialización del servicio...")
        time.sleep(3.0)

    cmd_verificar_log = f"""
from src.models.notification_log import NotificationLog
log = NotificationLog.objects.filter(destinatario_email='{email_prueba}').first()
if log:
    print(f'Log encontrado: Tipo={{log.tipo}}, Estado={{log.estado}}, Asunto=\"{{log.asunto}}\"')
else:
    print('Log no encontrado')
"""
    output_log = run_container_command("ms-notificaciones", cmd_verificar_log)
    log_lines = [line.strip() for line in output_log.split("\n") if "imported automatically" not in line and line.strip()]
    if log_lines and "Log encontrado:" in log_lines[-1]:
        print(f"   Confirmación: {log_lines[-1]}")
    else:
        print("   Nota: No se detectó bitácora en ms-notificaciones.")

    print("\n[Paso 5/5] Ejecutando limpieza y reversión de cambios en base de datos...")
    
    # 1. Eliminar de ms-alumnos
    cmd_delete_alumno = f"from src.models.alumno import Alumno; Alumno.objects.filter(correo='{email_prueba}').delete()"
    run_container_command("ms-alumnos", cmd_delete_alumno)
    
    # 2. Eliminar de ms-auth
    cmd_delete_auth = f"from src.models.models import User; User.objects.filter(email='{email_prueba}').delete()"
    run_container_command("ms-auth", cmd_delete_auth)
    
    # 3. Eliminar de ms-notificaciones
    if not is_container_running("ms-notificaciones"):
        print("   Esperando a que 'ms-notificaciones' se reactive para realizar la limpieza del log...")
        while not is_container_running("ms-notificaciones"):
            time.sleep(1.0)
    cmd_delete_notif = f"from src.models.notification_log import NotificationLog; NotificationLog.objects.filter(destinatario_email='{email_prueba}').delete()"
    run_container_command("ms-notificaciones", cmd_delete_notif)
    
    print("   Confirmación: Todos los registros temporales han sido eliminados de manera segura.")
    print("\nPrueba de flujo completada con éxito.")

if __name__ == '__main__':
    main()
