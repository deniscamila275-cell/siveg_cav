"""
================================================================================
CAPA DE PERSISTENCIA Y MODELO DE DOMINIO (POO - Programación Orientada a Objetos)
================================================================================
OBJETIVO DEL PROYECTO:
    Sistema Integrado de Vecinos y Gestión (SIVEG / SIGEV Posadas).
    Permite centralizar la recepción y canalización de reclamos barriales,
    orientación inteligente en trámites ciudadanos, seguimiento de expedientes
    mediante tickets únicos y articulación descentralizada con organismos públicos
    y sedes barriales (ej. Sede CAV Itaembé Guazú, EMSA, ATM, IPRODHA, etc.).

SOPORTE DEL SISTEMA:
    Implementado sobre el patrón arquitectónico MVT (Modelo - Vista - Template)
    de Django. Esta capa define los Modelos de Datos, que encapsulan las entidades
    del negocio mediante Clases de POO y se mapean automáticamente a tablas y columnas
    relacionales a través del ORM (Object-Relational Mapping).
================================================================================
"""

from django.db import models


# ==============================================================================
# CONCEPTO POO: CLASE ABSTRACTA / MOLDE BASE (Herencia y Polimorfismo)
# ==============================================================================
class ModeloBaseAuditoria(models.Model):
    """
    CLASE ABSTRACTA:
    En POO, una clase abstracta define una estructura y contrato común que no se
    instancia directamente, sino que es heredada por las clases hijas concretas.
    En Django ORM, 'abstract = True' en la clase interna Meta indica que no debe
    crearse una tabla física en la base de datos para esta clase; solo se heredan
    sus miembros a las subclases.
    """
    class Meta:
        abstract = True

    # MÉTODO ABSTRACTO / POLIMÓRFICO:
    # Las clases derivadas deben implementar o sobrescribir este método
    def obtener_resumen_identificador(self) -> str:
        """Método abstracto/polimórfico: cada subclase define su representación identificatoria."""
        raise NotImplementedError("Las subclases concretas deben implementar este método.")


# ==============================================================================
# CONCEPTO POO: CLASE CategoriaReclamo (Entidad de Catálogo)
# ==============================================================================
class CategoriaReclamo(ModeloBaseAuditoria):
    """
    CLASE: CategoriaReclamo
    Molde que representa las distintas categorías operativas municipales (Alumbrado, Obras, etc.).
    Hereda de ModeloBaseAuditoria (Herencia en POO) y models.Model.
    """

    # --- ATRIBUTOS DE CLASE / COLUMNAS EN BASE DE DATOS (Mapeo ORM) ---
    # En Django ORM, cada atributo definido a nivel de clase representa una COLUMNA física en la tabla:
    cod_categoria = models.IntegerField(primary_key=True)   # Columna: Clave Primaria (Primary Key / PK)
    nombre_categoria = models.CharField(max_length=100)     # Columna: VARCHAR(100) - Nombre descriptivo
    organismo_default = models.CharField(max_length=100, default='Obras Públicas') # Columna: Área predeterminada

    # --- CONSTRUCTOR EN POO: ---
    # En Django ORM, el método constructor (__init__) es provisto por la superclase models.Model.
    # Permite instanciar objetos pasando argumentos nombrados:
    #   instancia = CategoriaReclamo(cod_categoria=10, nombre_categoria='Bacheo')

    # --- MÉTODOS DE INSTANCIA (Comportamiento del Objeto) ---
    def __str__(self):
        """
        Método especial (dunder) de Python sobrescrito (Polimorfismo).
        Define cómo se representa el objeto instanciado al ser convertido a cadena de texto.
        """
        return f"{self.cod_categoria} - {self.nombre_categoria}"

    def obtener_resumen_identificador(self) -> str:
        """Implementación concreta del método polimórfico heredado de la clase abstracta."""
        return f"CAT-{self.cod_categoria}: {self.nombre_categoria}"


# ==============================================================================
# CONCEPTO POO: CLASE Expediente (Entidad Principal de Negocio / Ticket Vecinal)
# ==============================================================================
class Expediente(ModeloBaseAuditoria):
    """
    CLASE PRINCIPAL: Expediente
    Representa el expediente digital o ticket generado por un vecino para canalizar
    un reclamo, solicitud o emergencia ante el municipio o dependencias asociadas.
    """

    # --- ATRIBUTOS DE CLASE: Constantes compartidas por todos los objetos de la clase ---
    TIPO_CHOICES = [
        ('CONSULTA', 'Consulta'),
        ('RECLAMO', 'Reclamo'),
        ('EMERGENCIA', 'Emergencia Prioriataria'),
    ]

    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente de Validación'),
        ('INGRESADO', 'Ingresado'),
        ('DERIVADO', 'Derivado'),
        ('EN_PROCESO', 'En Proceso'),
        ('RESUELTO', 'Resuelto'),
        ('RECHAZADO', 'Rechazado'),
    ]

    # --- COLUMNAS DE LA BASE DE DATOS (Atributos mapeados por el ORM a la tabla 'blog_expediente') ---
    nro_expediente = models.CharField(max_length=20, unique=True)  # Columna: N° correlativo único (ej: TCK-2026-0001)
    dni_vecino = models.BigIntegerField()                          # Columna: Documento del ciudadano (BIGINT)
    nombre_completo = models.CharField(max_length=100)             # Columna: Nombre y apellido del titular
    telefono_contacto = models.CharField(max_length=20)            # Columna: Teléfono verificado con característica
    tipo_solicitud = models.CharField(max_length=15, choices=TIPO_CHOICES, default='RECLAMO') # Columna: Tipo
    
    # RELACIÓN ENTRE CLASES / ASOCIACIÓN (Clave Foránea / Foreign Key):
    # Asocia cada Expediente con una instancia de la clase CategoriaReclamo (Relación Muchos a Uno).
    categoria = models.ForeignKey(CategoriaReclamo, on_delete=models.SET_NULL, null=True, blank=True)
    
    detalle_consulta = models.TextField()                          # Columna: Descripción completa de la solicitud
    respuesta_ia = models.TextField(blank=True, null=True)         # Columna: Dictamen/orientación técnica brindada
    organismo_destino = models.CharField(max_length=100, blank=True, null=True) # Columna: Dependencia asignada
    estado_actual = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE') # Columna: Estado
    archivo_adjunto = models.FileField(upload_to='adjuntos_tickets/', null=True, blank=True)   # Columna: Ruta archivo
    barrio = models.CharField(max_length=120, blank=True, null=True)     # Columna: Barrio o Chacra en Posadas
    entre_calles = models.CharField(max_length=200, blank=True, null=True) # Columna: Intersección o altura
    referencias = models.CharField(max_length=200, blank=True, null=True)  # Columna: Datos adicionales de ubicación
    fecha_ingreso = models.DateTimeField(auto_now_add=True)               # Columna: Timestamp automático de creación

    # --- MÉTODOS DE INSTANCIA (Comportamiento del Objeto Expediente) ---
    def __str__(self):
        """Sobrescritura de método para representación amigable del objeto."""
        return f"{self.nro_expediente} - {self.nombre_completo}"

    def obtener_resumen_identificador(self) -> str:
        """Implementación concreta del método polimórfico de la clase base abstracta."""
        return f"Ticket N° {self.nro_expediente} ({self.estado_actual})"

    def esta_resuelto(self) -> bool:
        """
        MÉTODO DE INSTANCIA:
        Verifica el estado del objeto en memoria para determinar si el trámite fue resuelto.
        """
        return self.estado_actual == 'RESUELTO'

    def es_prioritario(self) -> bool:
        """
        MÉTODO DE INSTANCIA:
        Determina si el ticket requiere tratamiento de emergencia prioritaria.
        """
        return self.tipo_solicitud == 'EMERGENCIA'


# ==============================================================================
# CONCEPTO POO: CLASE RegistroConsulta (Auditoría y Trazabilidad)
# ==============================================================================
class RegistroConsulta(ModeloBaseAuditoria):
    """
    CLASE: RegistroConsulta
    Entidad de auditoría que registra cada consulta ciudadana resuelta por el sistema,
    permitiendo métricas gerenciales y análisis de recurrencia territorial.
    """
    RESULTADO_CHOICES = [
        ('ASESORAMIENTO', 'Consulta resuelta mediante asesoramiento'),
        ('TRAMITE_DIGITAL', 'Orientada a trámite digital'),
        ('DERIVACION_EXTERNA', 'Derivada a organismo externo'),
        ('TICKET_REGISTRADO', 'Solicitud registrada mediante ticket'),
        ('EMERGENCIA', 'Emergencia prioritaria'),
    ]

    EVALUACION_CHOICES = [
        ('PENDIENTE', 'Sin evaluar'),
        ('SI', 'Sí'),
        ('PARCIAL', 'Parcialmente'),
        ('NO', 'No'),
    ]

    # COLUMNAS DE BASE DE DATOS:
    identificador_consulta = models.CharField(max_length=36, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    tipo_consulta = models.CharField(max_length=20)  # CONSULTA, RECLAMO, EMERGENCIA
    categoria = models.CharField(max_length=120, blank=True, null=True)
    texto_consultado = models.TextField()
    respuesta_brindada = models.TextField()
    fuente_informacion = models.CharField(max_length=200, default='Base de Conocimiento Oficial SIGEV')
    resultado = models.CharField(max_length=25, choices=RESULTADO_CHOICES, default='ASESORAMIENTO')
    
    # ASOCIACIÓN / CLAVE FORÁNEA: Relación opcional con la clase Expediente
    ticket_asociado = models.ForeignKey(
        Expediente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultas_vinculadas'
    )
    barrio_detectado = models.CharField(max_length=120, blank=True, null=True)
    evaluacion_vecino = models.CharField(max_length=15, choices=EVALUACION_CHOICES, default='PENDIENTE')
    fecha_evaluacion = models.DateTimeField(null=True, blank=True)

    # MÉTODOS DE INSTANCIA:
    def __str__(self):
        return f"{self.identificador_consulta} [{self.resultado}] - {self.fecha_creacion.strftime('%d/%m/%Y %H:%M')}"

    def obtener_resumen_identificador(self) -> str:
        return f"Consulta {self.identificador_consulta} ({self.resultado})"


# ==============================================================================
# CONCEPTO POO: CLASE SugerenciaOrganismo (Propuesta Ciudadana para el CAV)
# ==============================================================================
class SugerenciaOrganismo(models.Model):
    """
    CLASE: SugerenciaOrganismo
    Representa propuestas de los vecinos para incorporar nuevos organismos o entidades al CAV.
    """
    # COLUMNAS DE BASE DE DATOS:
    fecha_registro = models.DateTimeField(auto_now_add=True)
    texto_sugerencia = models.TextField(help_text="Organismo, entidad o servicio solicitado por el vecino")
    nombre_vecino = models.CharField(max_length=120, blank=True, null=True)
    contacto = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=20, default='PENDIENTE')  # PENDIENTE, EN_ANALISIS, INCORPORADO

    class Meta:
        verbose_name = 'Sugerencia de Organismo'
        verbose_name_plural = 'Sugerencias de Organismos'
        ordering = ['-fecha_registro']

    # MÉTODOS DE INSTANCIA:
    def __str__(self):
        vecino_txt = f" de {self.nombre_vecino}" if self.nombre_vecino else ""
        return f"Sugerencia #{self.id}{vecino_txt} - {self.fecha_registro.strftime('%d/%m/%Y')}"

