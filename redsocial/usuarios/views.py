from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse

from .models import PerfilUsuario, SolicitudAmistad, Amistad
from .forms import (
    FormularioRegistro, 
    FormularioLogin, 
    FormularioEditarPerfil,
    FormularioEditarUsuario,
    FormularioBusqueda
)
from .graph_engine import MotorRecomendaciones


# ============== VISTAS DE AUTENTICACIÓN ==============

def registro_view(request):
    """Vista para registrar nuevos usuarios."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = FormularioRegistro(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'¡Bienvenido/a {user.first_name}! Tu cuenta ha sido creada.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = FormularioRegistro()
    
    return render(request, 'usuarios/registro.html', {'form': form})


def login_view(request):
    """Vista para iniciar sesión."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = FormularioLogin(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'¡Hola de nuevo, {user.first_name}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = FormularioLogin()
    
    return render(request, 'usuarios/login.html', {'form': form})


@login_required
def logout_view(request):
    """Vista para cerrar sesión."""
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('login')


# ============== VISTAS PRINCIPALES ==============

@login_required
def dashboard_view(request):
    """Vista del dashboard principal del usuario."""
    perfil = request.user.perfil
    
    # Obtener estadísticas
    num_amigos = perfil.contar_amigos()
    solicitudes_pendientes = perfil.solicitudes_pendientes_recibidas().count()
    
    # Obtener recomendaciones de amigos
    motor = MotorRecomendaciones()
    recomendaciones = motor.obtener_recomendaciones(request.user, limite=5)
    estadisticas_grafo = motor.obtener_estadisticas_grafo(request.user)
    
    # Obtener lista de amigos para mostrar
    amigos = perfil.obtener_amigos()[:6]
    
    context = {
        'perfil': perfil,
        'num_amigos': num_amigos,
        'solicitudes_pendientes': solicitudes_pendientes,
        'recomendaciones': recomendaciones,
        'estadisticas_grafo': estadisticas_grafo,
        'amigos': amigos,
    }
    
    return render(request, 'usuarios/dashboard.html', context)


@login_required
def perfil_view(request, username=None):
    """Vista del perfil de usuario."""
    if username is None:
        user = request.user
    else:
        user = get_object_or_404(User, username=username)
    
    perfil = user.perfil
    es_propio = user == request.user
    
    # Verificar estado de amistad
    son_amigos = False
    solicitud_enviada = False
    solicitud_recibida = None
    
    if not es_propio:
        son_amigos = Amistad.son_amigos(request.user, user)
        
        # Verificar si hay solicitud pendiente enviada
        solicitud_enviada = SolicitudAmistad.objects.filter(
            de_usuario=request.user,
            para_usuario=user,
            estado='pendiente'
        ).exists()
        
        # Verificar si hay solicitud pendiente recibida
        solicitud_recibida = SolicitudAmistad.objects.filter(
            de_usuario=user,
            para_usuario=request.user,
            estado='pendiente'
        ).first()
    
    # Obtener amigos del usuario
    amigos = perfil.obtener_amigos()
    
    # Amigos en común (si no es el propio perfil)
    amigos_comun = []
    if not es_propio:
        motor = MotorRecomendaciones()
        motor.grafo.construir_grafo()
        amigos_comun_ids = motor.grafo.amigos_en_comun(request.user.id, user.id)
        amigos_comun = User.objects.filter(id__in=amigos_comun_ids)
    
    context = {
        'usuario': user,
        'perfil': perfil,
        'es_propio': es_propio,
        'son_amigos': son_amigos,
        'solicitud_enviada': solicitud_enviada,
        'solicitud_recibida': solicitud_recibida,
        'amigos': amigos,
        'amigos_comun': amigos_comun,
        'num_amigos': len(amigos),
    }
    
    return render(request, 'usuarios/perfil.html', context)


@login_required
def editar_perfil_view(request):
    """Vista para editar el perfil del usuario."""
    perfil = request.user.perfil
    
    if request.method == 'POST':
        form_usuario = FormularioEditarUsuario(request.POST, instance=request.user)
        form_perfil = FormularioEditarPerfil(request.POST, request.FILES, instance=perfil)
        
        if form_usuario.is_valid() and form_perfil.is_valid():
            form_usuario.save()
            form_perfil.save()
            messages.success(request, 'Tu perfil ha sido actualizado.')
            return redirect('perfil')
        else:
            messages.error(request, 'Por favor corrige los errores.')
    else:
        form_usuario = FormularioEditarUsuario(instance=request.user)
        form_perfil = FormularioEditarPerfil(instance=perfil)
    
    context = {
        'form_usuario': form_usuario,
        'form_perfil': form_perfil,
    }
    
    return render(request, 'usuarios/editar_perfil.html', context)


# ============== VISTAS DE AMISTADES ==============

@login_required
def lista_amigos_view(request):
    """Vista de la lista de amigos del usuario."""
    perfil = request.user.perfil
    amigos = perfil.obtener_amigos()
    
    context = {
        'amigos': amigos,
        'num_amigos': len(amigos),
    }
    
    return render(request, 'usuarios/lista_amigos.html', context)


@login_required
def solicitudes_view(request):
    """Vista de solicitudes de amistad pendientes."""
    solicitudes_recibidas = SolicitudAmistad.objects.filter(
        para_usuario=request.user,
        estado='pendiente'
    ).order_by('-fecha_creacion')
    
    solicitudes_enviadas = SolicitudAmistad.objects.filter(
        de_usuario=request.user,
        estado='pendiente'
    ).order_by('-fecha_creacion')
    
    context = {
        'solicitudes_recibidas': solicitudes_recibidas,
        'solicitudes_enviadas': solicitudes_enviadas,
    }
    
    return render(request, 'usuarios/solicitudes.html', context)


@login_required
def enviar_solicitud_view(request, user_id):
    """Vista para enviar una solicitud de amistad."""
    para_usuario = get_object_or_404(User, id=user_id)
    
    # Verificar que no sea el mismo usuario
    if para_usuario == request.user:
        messages.error(request, 'No puedes enviarte una solicitud a ti mismo.')
        return redirect('perfil', username=para_usuario.username)
    
    # Verificar que no sean ya amigos
    if Amistad.son_amigos(request.user, para_usuario):
        messages.info(request, f'Ya eres amigo de {para_usuario.username}.')
        return redirect('perfil', username=para_usuario.username)
    
    # Verificar que no exista una solicitud pendiente
    solicitud_existente = SolicitudAmistad.objects.filter(
        Q(de_usuario=request.user, para_usuario=para_usuario) |
        Q(de_usuario=para_usuario, para_usuario=request.user),
        estado='pendiente'
    ).first()
    
    if solicitud_existente:
        if solicitud_existente.de_usuario == request.user:
            messages.info(request, 'Ya has enviado una solicitud a este usuario.')
        else:
            messages.info(request, 'Este usuario ya te ha enviado una solicitud. ¡Acéptala!')
        return redirect('perfil', username=para_usuario.username)
    
    # Crear la solicitud
    SolicitudAmistad.objects.create(
        de_usuario=request.user,
        para_usuario=para_usuario
    )
    
    messages.success(request, f'Solicitud de amistad enviada a {para_usuario.username}.')
    return redirect('perfil', username=para_usuario.username)


@login_required
def aceptar_solicitud_view(request, solicitud_id):
    """Vista para aceptar una solicitud de amistad."""
    solicitud = get_object_or_404(
        SolicitudAmistad,
        id=solicitud_id,
        para_usuario=request.user,
        estado='pendiente'
    )
    
    solicitud.aceptar()
    messages.success(request, f'¡Ahora eres amigo de {solicitud.de_usuario.username}!')
    
    return redirect('solicitudes')


@login_required
def rechazar_solicitud_view(request, solicitud_id):
    """Vista para rechazar una solicitud de amistad."""
    solicitud = get_object_or_404(
        SolicitudAmistad,
        id=solicitud_id,
        para_usuario=request.user,
        estado='pendiente'
    )
    
    solicitud.rechazar()
    messages.info(request, 'Solicitud rechazada.')
    
    return redirect('solicitudes')


@login_required
def cancelar_solicitud_view(request, solicitud_id):
    """Vista para cancelar una solicitud enviada."""
    solicitud = get_object_or_404(
        SolicitudAmistad,
        id=solicitud_id,
        de_usuario=request.user,
        estado='pendiente'
    )
    
    solicitud.delete()
    messages.info(request, 'Solicitud cancelada.')
    
    return redirect('solicitudes')


@login_required
def eliminar_amigo_view(request, user_id):
    """Vista para eliminar un amigo."""
    amigo = get_object_or_404(User, id=user_id)
    
    # Buscar y eliminar la amistad
    amistad = Amistad.objects.filter(
        Q(usuario1=request.user, usuario2=amigo) |
        Q(usuario1=amigo, usuario2=request.user)
    ).first()
    
    if amistad:
        amistad.delete()
        messages.info(request, f'Has eliminado a {amigo.username} de tu lista de amigos.')
    else:
        messages.error(request, 'No eres amigo de este usuario.')
    
    return redirect('lista_amigos')


# ============== VISTAS DE RECOMENDACIONES ==============

@login_required
def recomendaciones_view(request):
    """Vista de recomendaciones inteligentes de amigos."""
    motor = MotorRecomendaciones()
    recomendaciones = motor.obtener_recomendaciones(request.user, limite=20)
    estadisticas = motor.obtener_estadisticas_grafo(request.user)
    
    context = {
        'recomendaciones': recomendaciones,
        'estadisticas': estadisticas,
    }
    
    return render(request, 'usuarios/recomendaciones.html', context)


# ============== VISTAS DE BÚSQUEDA ==============

@login_required
def buscar_usuarios_view(request):
    """Vista para buscar usuarios."""
    form = FormularioBusqueda(request.GET)
    resultados = []
    query = ''
    
    if form.is_valid():
        query = form.cleaned_data.get('query', '')
        if query:
            resultados = User.objects.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            ).exclude(id=request.user.id)[:20]
    
    # Agregar información de estado de amistad para cada resultado
    resultados_con_estado = []
    for user in resultados:
        es_amigo = Amistad.son_amigos(request.user, user)
        solicitud_enviada = SolicitudAmistad.objects.filter(
            de_usuario=request.user,
            para_usuario=user,
            estado='pendiente'
        ).exists()
        solicitud_recibida = SolicitudAmistad.objects.filter(
            de_usuario=user,
            para_usuario=request.user,
            estado='pendiente'
        ).exists()
        
        resultados_con_estado.append({
            'usuario': user,
            'es_amigo': es_amigo,
            'solicitud_enviada': solicitud_enviada,
            'solicitud_recibida': solicitud_recibida,
        })
    
    context = {
        'form': form,
        'resultados': resultados_con_estado,
        'query': query,
    }
    
    return render(request, 'usuarios/buscar_usuarios.html', context)


# ============== PÁGINA DE INICIO ==============

def inicio_view(request):
    """Vista de la página de inicio."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'usuarios/inicio.html')
