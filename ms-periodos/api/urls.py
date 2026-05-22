"""
URL routing for MS-Periodos API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PeriodoViewSet, MateriaViewSet

router = DefaultRouter()
router.register(r'periodos', PeriodoViewSet, basename='periodo')
router.register(r'materias', MateriaViewSet, basename='materia')

urlpatterns = [
    path('', include(router.urls)),
]
