from django.urls import path
from . import views

urlpatterns = [
    # Página de inicio
    path('', views.inicio_view, name='inicio'),
    
    # Autenticación
    path('registro/', views.registro_view, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard y perfil
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('perfil/<str:username>/', views.perfil_view, name='perfil_usuario'),
    path('perfil/editar/', views.editar_perfil_view, name='editar_perfil'),
    
    # Amigos
    path('amigos/', views.lista_amigos_view, name='lista_amigos'),
    path('solicitudes/', views.solicitudes_view, name='solicitudes'),
    
    # Acciones de amistad
    path('amistad/enviar/<int:user_id>/', views.enviar_solicitud_view, name='enviar_solicitud'),
    path('amistad/aceptar/<int:solicitud_id>/', views.aceptar_solicitud_view, name='aceptar_solicitud'),
    path('amistad/rechazar/<int:solicitud_id>/', views.rechazar_solicitud_view, name='rechazar_solicitud'),
    path('amistad/cancelar/<int:solicitud_id>/', views.cancelar_solicitud_view, name='cancelar_solicitud'),
    path('amistad/eliminar/<int:user_id>/', views.eliminar_amigo_view, name='eliminar_amigo'),
    
    # Recomendaciones
    path('recomendaciones/', views.recomendaciones_view, name='recomendaciones'),
    
    # Búsqueda
    path('buscar/', views.buscar_usuarios_view, name='buscar_usuarios'),
]
