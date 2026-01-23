from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class PerfilUsuario(models.Model):
    """
    Perfil extendido del usuario con información adicional.
    Se crea automáticamente cuando se registra un nuevo usuario.
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    foto = models.ImageField(upload_to='fotos_perfil/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, default='')
    ubicacion = models.CharField(max_length=100, blank=True, default='')
    fecha_nacimiento = models.DateField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'
    
    def __str__(self):
        return f'Perfil de {self.usuario.username}'
    
    def obtener_amigos(self):
        """Retorna todos los amigos confirmados del usuario."""
        amistades = Amistad.objects.filter(
            models.Q(usuario1=self.usuario) | models.Q(usuario2=self.usuario)
        )
        amigos = []
        for amistad in amistades:
            if amistad.usuario1 == self.usuario:
                amigos.append(amistad.usuario2)
            else:
                amigos.append(amistad.usuario1)
        return amigos
    
    def contar_amigos(self):
        """Retorna el número de amigos."""
        return len(self.obtener_amigos())
    
    def solicitudes_pendientes_recibidas(self):
        """Retorna las solicitudes de amistad pendientes recibidas."""
        return SolicitudAmistad.objects.filter(
            para_usuario=self.usuario,
            estado='pendiente'
        )
    
    def solicitudes_pendientes_enviadas(self):
        """Retorna las solicitudes de amistad pendientes enviadas."""
        return SolicitudAmistad.objects.filter(
            de_usuario=self.usuario,
            estado='pendiente'
        )


class SolicitudAmistad(models.Model):
    """
    Modelo para manejar las solicitudes de amistad entre usuarios.
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    ]
    
    de_usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='solicitudes_enviadas'
    )
    para_usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='solicitudes_recibidas'
    )
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Solicitud de Amistad'
        verbose_name_plural = 'Solicitudes de Amistad'
        unique_together = ('de_usuario', 'para_usuario')
    
    def __str__(self):
        return f'{self.de_usuario.username} → {self.para_usuario.username} ({self.estado})'
    
    def aceptar(self):
        """Acepta la solicitud y crea la amistad."""
        from django.utils import timezone
        self.estado = 'aceptada'
        self.fecha_respuesta = timezone.now()
        self.save()
        # Crear la amistad bidireccional
        Amistad.objects.get_or_create(
            usuario1=self.de_usuario,
            usuario2=self.para_usuario
        )
    
    def rechazar(self):
        """Rechaza la solicitud."""
        from django.utils import timezone
        self.estado = 'rechazada'
        self.fecha_respuesta = timezone.now()
        self.save()


class Amistad(models.Model):
    """
    Modelo para representar una amistad confirmada entre dos usuarios.
    Esta es una arista en el grafo social.
    """
    usuario1 = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='amistades_como_usuario1'
    )
    usuario2 = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='amistades_como_usuario2'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Amistad'
        verbose_name_plural = 'Amistades'
        unique_together = ('usuario1', 'usuario2')
    
    def __str__(self):
        return f'{self.usuario1.username} ↔ {self.usuario2.username}'
    
    @classmethod
    def son_amigos(cls, usuario1, usuario2):
        """Verifica si dos usuarios son amigos."""
        return cls.objects.filter(
            models.Q(usuario1=usuario1, usuario2=usuario2) |
            models.Q(usuario1=usuario2, usuario2=usuario1)
        ).exists()


# Señales para crear automáticamente el perfil cuando se crea un usuario
@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(usuario=instance)


@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    try:
        instance.perfil.save()
    except PerfilUsuario.DoesNotExist:
        PerfilUsuario.objects.create(usuario=instance)
