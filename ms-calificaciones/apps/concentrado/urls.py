from django.urls import path
from .views import ConcentradoView

urlpatterns = [
    path('concentrado/<uuid:materia_id>/', ConcentradoView.as_view(), name='concentrado'),
]