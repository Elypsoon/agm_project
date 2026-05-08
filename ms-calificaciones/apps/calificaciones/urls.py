from django.urls import path
from .views import CalificacionView

urlpatterns = [
    path('calificaciones/', CalificacionView.as_view(), name='calificaciones'),
]