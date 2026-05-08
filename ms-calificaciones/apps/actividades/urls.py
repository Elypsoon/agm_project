from django.urls import path
from .views import ActividadView

urlpatterns = [
    path('actividades/', ActividadView.as_view(), name='actividades'),
]