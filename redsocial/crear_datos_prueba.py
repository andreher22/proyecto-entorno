"""
Script para crear usuarios de prueba y demostrar el motor de grafos.
Ejecutar con: python manage.py shell < crear_datos_prueba.py
O simplemente: python manage.py runscript crear_datos_prueba (si tienes django-extensions)
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redsocial.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario, Amistad, SolicitudAmistad


def crear_usuarios_prueba():
    """Crea usuarios de prueba."""
    
    usuarios_data = [
        {'username': 'ana', 'first_name': 'Ana', 'last_name': 'García', 'email': 'ana@test.com', 'bio': 'Desarrolladora web apasionada por la tecnología', 'ubicacion': 'Ciudad de México'},
        {'username': 'carlos', 'first_name': 'Carlos', 'last_name': 'López', 'email': 'carlos@test.com', 'bio': 'Ingeniero de software', 'ubicacion': 'Guadalajara'},
        {'username': 'maria', 'first_name': 'María', 'last_name': 'Hernández', 'email': 'maria@test.com', 'bio': 'Diseñadora UX/UI', 'ubicacion': 'Monterrey'},
        {'username': 'juan', 'first_name': 'Juan', 'last_name': 'Martínez', 'email': 'juan@test.com', 'bio': 'Data Scientist', 'ubicacion': 'Ciudad de México'},
        {'username': 'sofia', 'first_name': 'Sofía', 'last_name': 'Rodríguez', 'email': 'sofia@test.com', 'bio': 'Frontend Developer', 'ubicacion': 'Puebla'},
        {'username': 'diego', 'first_name': 'Diego', 'last_name': 'Sánchez', 'email': 'diego@test.com', 'bio': 'Backend Developer', 'ubicacion': 'Querétaro'},
        {'username': 'lucia', 'first_name': 'Lucía', 'last_name': 'Torres', 'email': 'lucia@test.com', 'bio': 'DevOps Engineer', 'ubicacion': 'Guadalajara'},
        {'username': 'pedro', 'first_name': 'Pedro', 'last_name': 'Ramírez', 'email': 'pedro@test.com', 'bio': 'Mobile Developer', 'ubicacion': 'Monterrey'},
        {'username': 'elena', 'first_name': 'Elena', 'last_name': 'Flores', 'email': 'elena@test.com', 'bio': 'Product Manager', 'ubicacion': 'Ciudad de México'},
        {'username': 'miguel', 'first_name': 'Miguel', 'last_name': 'Díaz', 'email': 'miguel@test.com', 'bio': 'Full Stack Developer', 'ubicacion': 'Tijuana'},
    ]
    
    usuarios_creados = []
    
    for data in usuarios_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'email': data['email'],
            }
        )
        
        if created:
            user.set_password('test1234')
            user.save()
            # Actualizar perfil
            user.perfil.bio = data['bio']
            user.perfil.ubicacion = data['ubicacion']
            user.perfil.save()
            print(f"✓ Usuario creado: {user.username}")
        else:
            print(f"• Usuario existente: {user.username}")
        
        usuarios_creados.append(user)
    
    return usuarios_creados


def crear_amistades(usuarios):
    """
    Crea una red de amistades para demostrar el grafo.
    
    Estructura del grafo:
    
    ana -- carlos -- diego -- miguel
     |       |         |
    maria -- juan   lucia -- pedro
     |                 |
    sofia            elena
    
    """
    amistades = [
        ('ana', 'carlos'),
        ('ana', 'maria'),
        ('carlos', 'juan'),
        ('carlos', 'diego'),
        ('maria', 'juan'),
        ('maria', 'sofia'),
        ('diego', 'lucia'),
        ('diego', 'miguel'),
        ('lucia', 'pedro'),
        ('lucia', 'elena'),
    ]
    
    for user1_name, user2_name in amistades:
        user1 = User.objects.get(username=user1_name)
        user2 = User.objects.get(username=user2_name)
        
        if not Amistad.son_amigos(user1, user2):
            Amistad.objects.create(usuario1=user1, usuario2=user2)
            print(f"✓ Amistad creada: {user1_name} ↔ {user2_name}")
        else:
            print(f"• Amistad existente: {user1_name} ↔ {user2_name}")


def demostrar_grafo():
    """Demuestra el funcionamiento del motor de grafos."""
    from usuarios.graph_engine import MotorRecomendaciones, GrafoSocial
    
    print("\n" + "="*60)
    print("DEMOSTRACIÓN DEL MOTOR DE GRAFOS")
    print("="*60)
    
    # Probar con el usuario 'sofia'
    sofia = User.objects.get(username='sofia')
    motor = MotorRecomendaciones()
    
    print(f"\n📊 Analizando grafo para: {sofia.first_name} {sofia.last_name}")
    
    # Estadísticas
    stats = motor.obtener_estadisticas_grafo(sofia)
    print(f"\n📈 Estadísticas del grafo:")
    print(f"   • Amigos directos (Nivel 1): {stats['amigos_directos']}")
    print(f"   • Nivel 2 (amigos de amigos): {stats['nivel_2']}")
    print(f"   • Nivel 3: {stats['nivel_3']}")
    print(f"   • Alcance total: {stats['alcance']}")
    
    # Recomendaciones
    print(f"\n🎯 Recomendaciones para {sofia.first_name}:")
    recomendaciones = motor.obtener_recomendaciones(sofia, limite=5)
    
    for i, rec in enumerate(recomendaciones, 1):
        print(f"\n   {i}. {rec['usuario'].first_name} {rec['usuario'].last_name}")
        print(f"      • Puntuación: {rec['puntuacion']}")
        print(f"      • Amigos en común: {rec['num_amigos_comun']}")
        print(f"      • Distancia: {rec['distancia']} pasos")
        if rec['amigos_comun_nombres']:
            print(f"      • Conexiones: {', '.join(rec['amigos_comun_nombres'])}")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    print("\n🚀 Creando datos de prueba para GraphNet...\n")
    
    usuarios = crear_usuarios_prueba()
    print()
    crear_amistades(usuarios)
    demostrar_grafo()
    
    print("\n✅ ¡Datos de prueba creados exitosamente!")
    print("   Los usuarios de prueba tienen la contraseña: test1234")
    print("   Puedes iniciar sesión con cualquiera de ellos.\n")
