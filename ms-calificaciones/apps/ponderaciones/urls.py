from django.urls import path
from .views import PonderacionView

urlpatterns = [
    path("ponderaciones/<uuid:materia_id>/", PonderacionView.as_view(), name="ponderaciones"),
]