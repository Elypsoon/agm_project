"""
Django admin configuration for MS-Periodos API
"""
from django.contrib import admin
from .models import Periodo, Materia, Horario


@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'plan_estudios', 'fecha_inicio', 'fecha_fin', 'activo', 'created_at')
    list_filter = ('activo', 'created_at', 'plan_estudios')
    search_fields = ('nombre', 'plan_estudios')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('clave', 'nombre', 'nrc', 'seccion', 'periodo', 'estado', 'created_at')
    list_filter = ('estado', 'periodo', 'created_at')
    search_fields = ('clave', 'nombre', 'nrc')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ('materia', 'dia', 'hora_inicio', 'hora_fin', 'salon', 'es_virtual')
    list_filter = ('dia', 'es_virtual')
    search_fields = ('materia__clave', 'salon')
    readonly_fields = ('id',)
