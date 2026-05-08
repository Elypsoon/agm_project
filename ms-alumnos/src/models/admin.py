"""Registro de modelos en el admin de Django."""

from django.contrib import admin
from src.models.alumno import Alumno
from src.models.docente import Docente
from src.models.inscripcion import Inscripcion


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ("matricula", "nombre_completo", "correo", "tipo_formacion", "created_at")
    search_fields = ("matricula", "nombre_completo", "correo")
    list_filter = ("tipo_formacion",)
    readonly_fields = ("id", "created_at")


@admin.register(Docente)
class DocenteAdmin(admin.ModelAdmin):
    list_display = ("nombre_completo", "correo_institucional", "cubiculo", "created_at")
    search_fields = ("nombre_completo", "correo_institucional")
    readonly_fields = ("id", "created_at")


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ("alumno", "materia_id", "activo", "fecha_baja", "created_at")
    list_filter = ("activo",)
    readonly_fields = ("id", "created_at")
