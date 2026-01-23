"""
Motor de Grafos para Recomendaciones Inteligentes de Amigos

Este módulo implementa algoritmos de grafos para:
1. Construir el grafo social
2. Buscar amigos a N niveles de distancia usando BFS
3. Calcular amigos en común
4. Generar recomendaciones inteligentes basadas en puntuación
"""

from collections import deque, defaultdict
from django.contrib.auth.models import User
from django.db.models import Q


class GrafoSocial:
    """
    Clase que representa el grafo social de la red.
    
    - Nodos: Usuarios
    - Aristas: Amistades confirmadas (no dirigidas)
    """
    
    def __init__(self):
        # Diccionario de adyacencia: {usuario_id: set(amigos_ids)}
        self.grafo = defaultdict(set)
        self._construido = False
    
    def construir_grafo(self):
        """
        Construye el grafo social a partir de la base de datos.
        Cada usuario es un nodo y cada amistad es una arista.
        """
        from .models import Amistad
        
        self.grafo.clear()
        
        # Agregar todos los usuarios como nodos
        for user in User.objects.all():
            self.grafo[user.id]  # Asegura que el nodo existe
        
        # Agregar las aristas (amistades)
        for amistad in Amistad.objects.all():
            self.grafo[amistad.usuario1_id].add(amistad.usuario2_id)
            self.grafo[amistad.usuario2_id].add(amistad.usuario1_id)
        
        self._construido = True
        return self
    
    def obtener_amigos(self, usuario_id):
        """Retorna los IDs de los amigos directos de un usuario."""
        if not self._construido:
            self.construir_grafo()
        return self.grafo.get(usuario_id, set())
    
    def bfs_niveles(self, usuario_id, nivel_maximo=2):
        """
        Implementación de BFS (Breadth-First Search) para encontrar
        usuarios a N niveles de distancia.
        
        Args:
            usuario_id: ID del usuario origen
            nivel_maximo: Profundidad máxima de búsqueda
            
        Returns:
            dict: {nivel: set(usuario_ids)} - Usuarios organizados por nivel
        """
        if not self._construido:
            self.construir_grafo()
        
        visitados = {usuario_id}
        cola = deque([(usuario_id, 0)])
        niveles = defaultdict(set)
        
        while cola:
            actual, nivel = cola.popleft()
            
            if nivel >= nivel_maximo:
                continue
            
            for vecino in self.grafo.get(actual, set()):
                if vecino not in visitados:
                    visitados.add(vecino)
                    niveles[nivel + 1].add(vecino)
                    cola.append((vecino, nivel + 1))
        
        return niveles
    
    def amigos_en_comun(self, usuario1_id, usuario2_id):
        """
        Calcula los amigos en común entre dos usuarios.
        
        Returns:
            set: Conjunto de IDs de amigos en común
        """
        if not self._construido:
            self.construir_grafo()
        
        amigos1 = self.grafo.get(usuario1_id, set())
        amigos2 = self.grafo.get(usuario2_id, set())
        
        return amigos1.intersection(amigos2)
    
    def distancia_entre_usuarios(self, origen_id, destino_id, max_distancia=5):
        """
        Calcula la distancia mínima entre dos usuarios usando BFS.
        
        Returns:
            int: Distancia en el grafo, -1 si no hay conexión
        """
        if not self._construido:
            self.construir_grafo()
        
        if origen_id == destino_id:
            return 0
        
        visitados = {origen_id}
        cola = deque([(origen_id, 0)])
        
        while cola:
            actual, distancia = cola.popleft()
            
            if distancia >= max_distancia:
                continue
            
            for vecino in self.grafo.get(actual, set()):
                if vecino == destino_id:
                    return distancia + 1
                
                if vecino not in visitados:
                    visitados.add(vecino)
                    cola.append((vecino, distancia + 1))
        
        return -1  # No hay conexión


class MotorRecomendaciones:
    """
    Motor de recomendaciones inteligentes basado en análisis de grafos.
    
    Fórmula de puntuación:
    - Amigos en común: +10 puntos por cada uno
    - Distancia en grafo: +5 puntos si nivel 2, +2 si nivel 3
    - Usuarios sin conexión: 0 puntos
    """
    
    def __init__(self):
        self.grafo = GrafoSocial()
    
    def calcular_puntuacion(self, usuario_id, candidato_id):
        """
        Calcula la puntuación de recomendación para un candidato.
        
        Args:
            usuario_id: ID del usuario para quien buscamos recomendaciones
            candidato_id: ID del usuario candidato a recomendar
            
        Returns:
            dict: {puntuacion, amigos_comun, distancia}
        """
        # Amigos en común
        amigos_comun = self.grafo.amigos_en_comun(usuario_id, candidato_id)
        num_amigos_comun = len(amigos_comun)
        
        # Distancia en el grafo
        distancia = self.grafo.distancia_entre_usuarios(usuario_id, candidato_id)
        
        # Calcular puntuación
        puntuacion = 0
        
        # +10 por cada amigo en común
        puntuacion += num_amigos_comun * 10
        
        # Puntos por cercanía en el grafo
        if distancia == 2:
            puntuacion += 5
        elif distancia == 3:
            puntuacion += 2
        elif distancia > 3:
            puntuacion += 1
        
        return {
            'puntuacion': puntuacion,
            'amigos_comun': list(amigos_comun),
            'num_amigos_comun': num_amigos_comun,
            'distancia': distancia
        }
    
    def obtener_recomendaciones(self, usuario, limite=10):
        """
        Obtiene las mejores recomendaciones de amigos para un usuario.
        
        El algoritmo:
        1. Construye el grafo social actualizado
        2. Usa BFS para encontrar usuarios a 2-3 niveles de distancia
        3. Calcula puntuación para cada candidato
        4. Ordena por puntuación y retorna los mejores
        
        Args:
            usuario: Objeto User de Django
            limite: Número máximo de recomendaciones
            
        Returns:
            list: Lista de dicts con {usuario, puntuacion, amigos_comun, distancia}
        """
        from .models import SolicitudAmistad
        
        # Reconstruir el grafo para tener datos actualizados
        self.grafo.construir_grafo()
        
        usuario_id = usuario.id
        
        # Obtener amigos directos (nivel 1) - estos NO son candidatos
        amigos_directos = self.grafo.obtener_amigos(usuario_id)
        
        # Obtener usuarios a nivel 2 y 3 usando BFS
        niveles = self.grafo.bfs_niveles(usuario_id, nivel_maximo=4)
        
        # Candidatos son usuarios en nivel 2, 3 y 4
        candidatos_ids = set()
        for nivel in [2, 3, 4]:
            candidatos_ids.update(niveles.get(nivel, set()))
        
        # Si hay pocos candidatos por conexiones, agregar usuarios sin conexión
        if len(candidatos_ids) < limite:
            todos_usuarios = set(User.objects.values_list('id', flat=True))
            sin_conexion = todos_usuarios - amigos_directos - {usuario_id} - candidatos_ids
            candidatos_ids.update(sin_conexion)
        
        # Excluir usuarios con solicitudes pendientes
        solicitudes_enviadas = set(
            SolicitudAmistad.objects.filter(
                de_usuario=usuario, 
                estado='pendiente'
            ).values_list('para_usuario_id', flat=True)
        )
        solicitudes_recibidas = set(
            SolicitudAmistad.objects.filter(
                para_usuario=usuario,
                estado='pendiente'
            ).values_list('de_usuario_id', flat=True)
        )
        
        candidatos_ids -= solicitudes_enviadas
        candidatos_ids -= solicitudes_recibidas
        
        # Calcular puntuación para cada candidato
        recomendaciones = []
        for candidato_id in candidatos_ids:
            try:
                candidato_user = User.objects.get(id=candidato_id)
                datos = self.calcular_puntuacion(usuario_id, candidato_id)
                
                # Obtener nombres de amigos en común
                amigos_comun_nombres = []
                for amigo_id in datos['amigos_comun'][:3]:  # Máximo 3 para mostrar
                    try:
                        amigo = User.objects.get(id=amigo_id)
                        amigos_comun_nombres.append(amigo.username)
                    except User.DoesNotExist:
                        pass
                
                recomendaciones.append({
                    'usuario': candidato_user,
                    'puntuacion': datos['puntuacion'],
                    'num_amigos_comun': datos['num_amigos_comun'],
                    'amigos_comun_nombres': amigos_comun_nombres,
                    'distancia': datos['distancia']
                })
            except User.DoesNotExist:
                continue
        
        # Ordenar por puntuación (mayor primero)
        recomendaciones.sort(key=lambda x: x['puntuacion'], reverse=True)
        
        return recomendaciones[:limite]
    
    def obtener_estadisticas_grafo(self, usuario):
        """
        Obtiene estadísticas del grafo para mostrar al usuario.
        
        Returns:
            dict: Estadísticas del grafo social
        """
        self.grafo.construir_grafo()
        usuario_id = usuario.id
        
        niveles = self.grafo.bfs_niveles(usuario_id, nivel_maximo=4)
        
        return {
            'amigos_directos': len(self.grafo.obtener_amigos(usuario_id)),
            'nivel_2': len(niveles.get(2, set())),
            'nivel_3': len(niveles.get(3, set())),
            'nivel_4': len(niveles.get(4, set())),
            'total_usuarios': len(self.grafo.grafo),
            'alcance': sum(len(v) for v in niveles.values())
        }
