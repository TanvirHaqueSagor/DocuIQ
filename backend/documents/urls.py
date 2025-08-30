from django.urls import path
from .views import DocumentListCreateView, DocumentDeleteView

urlpatterns = [
    path('', DocumentListCreateView.as_view()),
    path('<int:pk>', DocumentDeleteView.as_view()),
]
