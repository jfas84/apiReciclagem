from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.models import User
from rest_framework import routers, serializers, viewsets
from core import views


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'is_staff']

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'tipos-residuos', views.TipoResiduoViewSet)
router.register(r'condominios', views.CondominioViewSet)
router.register(r'parametros-calculo', views.ParametroCalculoViewSet)
router.register(r'calculos-credito', views.CalculoCreditoViewSet)


urlpatterns = [
    path('api/v1/', include('core.urls')),
    path('api/v1/', include(router.urls)),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    # URLs do dj-rest-auth para login, logout, reset de senha e tokens JWT
    path('api/auth/', include('dj_rest_auth.urls')),
    # URLs para registro
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

"""
Autenticação básica:

/api/auth/login/ - Login (POST)
/api/auth/logout/ - Logout (POST)
/api/auth/password/reset/ - Solicitar reset de senha (POST)
/api/auth/password/reset/confirm/ - Confirmar reset de senha (POST)
/api/auth/password/change/ - Alterar senha (POST)
/api/auth/user/ - Obter/atualizar usuário atual (GET, PUT, PATCH)
/api/auth/token/refresh/ - Renovar token JWT (POST)
/api/auth/token/verify/ - Verificar token JWT (POST)

Registro (se implementado):

/api/auth/registration/ - Registrar novo usuário (POST)
/api/auth/registration/verify-email/ - Verificar email (POST)
"""