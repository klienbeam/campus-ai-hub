from django.urls import path
from . import views

app_name = 'rag'

urlpatterns = [
    path('qa/', views.QAView.as_view(), name='qa'),
    path('api/ask/', views.QAView.as_view(), name='ask'),
    path('api/refresh/', views.refresh_knowledge_base, name='refresh'),
    path('api/history/', views.qa_history, name='history'),
]









