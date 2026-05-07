import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        # set_password se encarga de convertir el texto plano en el hash
        # Reemplaza tu lógica manual de password_hash
        user.set_password(password) 
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    # Identificador único UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Datos básicos
    email = models.EmailField(unique=True, db_index=True)
    nombre = models.CharField(max_length=255)
    
    # Roles (Usamos CharField con choices para simular tu Enum)
    ROLES = [
        ('admin', 'Administrador'),
        ('docente', 'Docente'),
        ('alumno', 'Alumno'),
    ]
    role = models.CharField(max_length=10, choices=ROLES, default='alumno')
    
    # Estado del usuario
    activo = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) # Requerido para el panel de administración
    
    # Recuperación de contraseña
    reset_token = models.CharField(max_length=255, null=True, blank=True)
    reset_token_expiry = models.DateTimeField(null=True, blank=True)
    
    # Auditoría (auto_now_add se pone solo al crear, auto_now cada que guardas)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    # Configuramos el email como el campo para login
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    class Meta:
        db_table = 'users' # Mantenemos el nombre de la tabla de tu README