"""
Serializers for MS-Periodos API
"""
from rest_framework import serializers
from .models import Periodo, Materia, Horario, EstadoMateria


class HorarioSerializer(serializers.ModelSerializer):
    """Serializer para horarios"""
    
    class Meta:
        model = Horario
        fields = ['id', 'dia', 'hora_inicio', 'hora_fin', 'salon', 'es_virtual']


class MateriaSerializer(serializers.ModelSerializer):
    """Serializer para materias"""
    horarios = HorarioSerializer(many=True, read_only=True)
    
    class Meta:
        model = Materia
        fields = [
            'id', 'nrc', 'clave', 'nombre', 'seccion',
            'docente_nombre', 'docente_id', 'periodo',
            'estado', 'horarios', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MateriaCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar materias"""
    
    class Meta:
        model = Materia
        fields = [
            'nrc', 'clave', 'nombre', 'seccion',
            'docente_nombre', 'docente_id', 'periodo', 'estado'
        ]


class PeriodoSerializer(serializers.ModelSerializer):
    """Serializer para periodos"""
    
    class Meta:
        model = Periodo
        fields = [
            'id', 'nombre', 'fecha_inicio', 'fecha_fin',
            'plan_estudios', 'activo', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PeriodoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar periodos"""
    
    class Meta:
        model = Periodo
        fields = [
            'nombre', 'fecha_inicio', 'fecha_fin',
            'plan_estudios', 'activo'
        ]


class PeriodoWithMateriasSerializer(serializers.ModelSerializer):
    """Serializer para periodos con materias incluidas"""
    materias = MateriaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Periodo
        fields = [
            'id', 'nombre', 'fecha_inicio', 'fecha_fin',
            'plan_estudios', 'activo', 'materias', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PaginatedMateriaResponse(serializers.Serializer):
    """Serializer para respuestas paginadas de materias"""
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    items = MateriaSerializer(many=True)
