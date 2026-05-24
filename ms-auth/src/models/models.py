import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        # set_password aplica el hash (pbkdf2_sha256 por defecto).
        # Si password es None, la cuenta queda sin contraseña válida hasta que se asigne una.
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    # UUID como PK evita IDs secuenciales predecibles en la API
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True, db_index=True)
    nombre = models.CharField(max_length=255)

    ROLES = [
        ('admin', 'Administrador'),
        ('docente', 'Docente'),
        ('alumno', 'Alumno'),
    ]
    role = models.CharField(max_length=10, choices=ROLES, default='alumno')

    # Permite deshabilitar un usuario sin eliminarlo de la base de datos
    activo = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Campos para el flujo de recuperación de contraseña vía enlace de email
    reset_token = models.CharField(max_length=255, null=True, blank=True)
    reset_token_expiry = models.DateTimeField(null=True, blank=True)

    # Cuando es True, el frontend debe redirigir al usuario al flujo de
    # cambio de contraseña antes de permitirle acceder al dashboard.
    # Se establece en False una vez que el usuario define su propia clave.
    requires_password_change = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    class Meta:
        db_table = 'users'