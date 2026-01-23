from django.contrib import admin
from .models import PerfilUsuario, SolicitudAmistad, Amistad


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'ubicacion', 'fecha_creacion')
    search_fields = ('usuario__username', 'usuario__email', 'ubicacion')
    list_filter = ('fecha_creacion',)


@admin.register(SolicitudAmistad)
class SolicitudAmistadAdmin(admin.ModelAdmin):
    list_display = ('de_usuario', 'para_usuario', 'estado', 'fecha_creacion')
    search_fields = ('de_usuario__username', 'para_usuario__username')
    list_filter = ('estado', 'fecha_creacion')


@admin.register(Amistad)
class AmistadAdmin(admin.ModelAdmin):
    list_display = ('usuario1', 'usuario2', 'fecha_creacion')
    search_fields = ('usuario1__username', 'usuario2__username')
    list_filter = ('fecha_creacion',)
