from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


# URLs da aplicação
urlpatterns = [
    # Inclui todas as rotas geradas pelo router    
    # Exemplos de URLs personalizadas para outras funcionalidades específicas
    path('dashboard-condominios/', views.dashboard_condominios, name='dashboard-condominios'),
    path('relatorio-economia/', views.relatorio_economia, name='relatorio-economia'),
]