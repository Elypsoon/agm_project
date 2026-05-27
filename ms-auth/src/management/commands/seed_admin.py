import os
from django.core.management.base import BaseCommand
from django.db import IntegrityError


class Command(BaseCommand):
    """
    Crea el usuario administrador inicial a partir de variables de entorno.

    Uso:
        python manage.py seed_admin

    Variables de entorno requeridas:
        ADMIN_EMAIL     — Correo del administrador (usado como username de login)
        ADMIN_PASSWORD  — Contraseña del administrador
        ADMIN_NAME      — Nombre completo del administrador

    Comportamiento:
        - Si el usuario con ese correo ya existe, NO realiza ningún cambio y
          termina sin error (idempotente: seguro de llamar múltiples veces,
          por ejemplo en cada arranque del contenedor Docker).
        - Si el correo no existe, crea la cuenta con role='admin',
          is_staff=True, is_superuser=True y requires_password_change=False.
    """

    help = "Crea el administrador inicial del sistema a partir de variables de entorno."

    def handle(self, *args, **options):
        # Importar aquí para garantizar que Django ya está completamente inicializado
        from src.models.models import User

        email = os.getenv("ADMIN_EMAIL")
        password = os.getenv("ADMIN_PASSWORD")
        nombre = os.getenv("ADMIN_NAME")

        # Validar que todas las variables necesarias estén definidas
        missing = [var for var, val in [
            ("ADMIN_EMAIL", email),
            ("ADMIN_PASSWORD", password),
            ("ADMIN_NAME", nombre),
        ] if not val]

        if missing:
            self.stderr.write(
                self.style.ERROR(
                    f"❌ Faltan variables de entorno para seed_admin: {', '.join(missing)}\n"
                    "   Define ADMIN_EMAIL, ADMIN_PASSWORD y ADMIN_NAME en el archivo .env."
                )
            )
            return

        # Verificar si el administrador ya existe (idempotente)
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  El administrador '{email}' ya existe. No se realizaron cambios."
                )
            )
            return

        # Crear el superusuario con rol admin
        try:
            User.objects.create_superuser(
                email=email,
                password=password,
                nombre=nombre,
                # El admin inicial no necesita cambiar su contraseña; la definió en el .env
                requires_password_change=False,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Administrador '{email}' creado exitosamente con role='admin'."
                )
            )
        except IntegrityError as e:
            self.stderr.write(
                self.style.ERROR(f"❌ Error de integridad al crear el administrador: {e}")
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"❌ Error inesperado en seed_admin: {e}")
            )
