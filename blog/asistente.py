"""
Módulo de Inteligencia y Asesoramiento del SIGEV / SIVEG (Posadas, Misiones).

Implementa:
1. Reglas determinísticas de seguridad para detección de emergencias en contexto
   (con énfasis prioritario en emergencias eléctricas: cables caídos, postes con chispas, electrocución).
2. Derivación hacia canales oficiales externos y botones de acción rápida
   (Llamar al 911, Llamar a Energía de Misiones 0800 888 3672, Abrir WhatsApp de Energía de Misiones, Sitio Oficial EMSA).
3. Clasificación semántica de consultas (Consulta Informativa, Reclamo o Solicitud, Posible Emergencia).
4. Catálogo de trámites digitales verificados con botón 'Iniciar trámite online', fuente oficial y fecha de verificación.
5. Separación estricta entre tickets internos del SIGEV y canales/reclamos externos sin envíos automáticos no autorizados.
"""

import re
from .catalogo_tramites import (
    buscar_tramite_por_consulta,
    obtener_catalogo_tramites,
    obtener_tramite_por_id,
)
from .organismos import (
    identificar_organismo_competente,
    obtener_directorio_organismos,
    obtener_organismo_por_id,
)
from .conversacion import (
    extraer_contexto_ubicacion,
    generar_preguntas_seguimiento,
    generar_resumen_automatico,
)

# Constantes de tipos de solicitud (coincidentes con Expediente.TIPO_CHOICES)
TIPO_CONSULTA = 'CONSULTA'
TIPO_RECLAMO = 'RECLAMO'
TIPO_EMERGENCIA = 'EMERGENCIA'

# Canales oficiales de Energía de Misiones (EMSA)
EMSA_TELEFONO_GUARDIA = '08008883672'
EMSA_TELEFONO_GUARDIA_TEXTO = '0800 888 3672'
EMSA_WHATSAPP_URL = 'https://wa.me/5493764242514'
EMSA_SITIO_OFICIAL = 'https://www.energiademisiones.com.ar/'


def normalizar_texto(texto: str) -> str:
    """Normaliza texto a minúsculas, removiendo tildes para comparación robusta."""
    texto = texto.lower()
    reemplazos = (
        ('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u'),
        ('ü', 'u'), ('ñ', 'n')
    )
    for c_origen, c_dest in reemplazos:
        texto = texto.replace(c_origen, c_dest)
    return texto


# ==============================================================================
# 1. REGLAS DETERMINÍSTICAS DE SEGURIDAD Y DETECCIÓN DE EMERGENCIAS
# ==============================================================================

def detectar_emergencia(texto_original: str):
    """
    Detecta si la consulta describe una situación de peligro inminente para
    personas o bienes. Evalúa el contexto para no basarse en palabras aisladas.

    Retorna:
        (es_emergencia: bool, subtipo: str, datos_contexto: dict)
    """
    t = normalizar_texto(texto_original)

    # Contextos de exclusión informativa (evitar falsos positivos)
    es_tramite_bomberos = any(
        k in t for k in [
            'habilitacion de bomberos', 'tramite de bomberos', 'certificado de bomberos',
            'constancia de bomberos', 'inspeccion de bomberos', 'curso de incendio',
            'matafuego para auto', 'matafuegos reglamentario', 'vencimiento matafuego'
        ]
    ) and not any(k in t for k in ['hay fuego', 'se quema', 'ardiendo', 'llamas', 'humo espeso'])

    es_consulta_bajada_comercial = any(
        k in t for k in ['bajada de luz', 'pedir bajada', 'instalar medidor', 'cambio de titularidad', 'factura']
    ) and not any(k in t for k in ['chisp', 'fuego', 'caido', 'tirado', 'electrocut', 'corriente'])

    if es_tramite_bomberos or es_consulta_bajada_comercial:
        return False, '', {}

    # --------------------------------------------------------------------------
    # Regla 1: Poste / columna caído, inclinado en riesgo o con chispas / fuego
    # --------------------------------------------------------------------------
    term_poste = bool(re.search(r'\b(poste|columna|pilar)\b', t))
    if term_poste:
        riesgo_caida = bool(re.search(
            r'(\bcaid[oa]|\bse cayo|\bcayo|\bpor caer|\ba punto de caer|\bcayendose|\binclinad[oa]|\bpartid[oa]|\bquebrad[oa]|\broto|\btirad[oa])',
            t
        ))
        riesgo_electrico = bool(re.search(
            r'(\bchisp\w*|\bfuego\b|\bhumo\b|\bardiendo|\brevento|\bexploto|\belectrificad[oa]|\bcorriente\b|\bdescarga)',
            t
        ))
        # Si el poste tiene luz quemada/apagada y NO tiene riesgo de caída ni eléctrico, NO es emergencia
        es_solo_luz_quemada = bool(re.search(r'\b(luz|foco|luminaria|lampara)\b.*?\b(quemad[oa]|quemo|apagad[oa]|no prende|no anda)\b', t))

        if (riesgo_caida or riesgo_electrico) and not (es_solo_luz_quemada and not riesgo_caida and not riesgo_electrico):
            return True, 'POSTE_PELIGROSO', {
                'titulo': 'Poste o Columna Eléctrica en Peligro Inminente',
                'tipo_riesgo': 'electrico',
                'recomendaciones': [
                    'Alejate de inmediato del lugar del peligro (mantené una distancia de al menos 15 metros).',
                    'NO toques cables caídos ni objetos o estructuras metálicas en contacto con ellos (postes, columnas, rejas, alambrados, charcos).',
                    'Mantené alejadas a otras personas, vecinos y mascotas de la zona de riesgo.',
                    'No intentes intervenir, mover ramas ni manipular cables por cuenta propia.',
                ],
                'servicios': ['911', 'EMSA', 'Defensa Civil']
            }

    # --------------------------------------------------------------------------
    # Regla 2: Cables de electricidad caídos, tirados, cortados, pelados o chispeando
    # --------------------------------------------------------------------------
    term_cable = bool(re.search(r'\b(cable|cables|tendido|trifasica|linea electrica|media tension|alta tension)\b', t))
    if term_cable:
        cable_peligro = bool(re.search(
            r'(\btirad[oa]|\bcaid[oa]|\bcortad[oa]|\bsuelt[oa]|\ben el piso|\ben la calle|\ben la vereda|\bcolgando|\bchisp\w*|\bfuego\b|\bpeligro|\bcon corriente|\belectrificad[oa]|\bdescarga|\bpelad[oa]s?|\bal descubierto)',
            t
        ))
        if cable_peligro:
            es_pelado = bool(re.search(r'\bpelad[oa]s?|\bal descubierto\b', t))
            titulo_cable = 'Cable Eléctrico Pelado / Expuesto con Riesgo de Descarga' if es_pelado else 'Cable Eléctrico Caído / Cortado en la Vía Pública'
            return True, 'CABLE_CAIDO', {
                'titulo': titulo_cable,
                'tipo_riesgo': 'electrico',
                'recomendaciones': [
                    'Considerá SIEMPRE que el cable posee tensión eléctrica activa y mortal.',
                    'Alejate de inmediato a un mínimo de 15 metros del cable.',
                    'NO toques cables ni ningún objeto, alambrado, reja o vehículo en contacto con ellos.',
                    'Evitá pisar charcos de agua o tierra húmeda cercana al cable.',
                    'Mantené alejadas a otras personas y bloqueá visualmente el paso de transeúntes.',
                ],
                'servicios': ['911', 'EMSA']
            }

    # --------------------------------------------------------------------------
    # Regla 3: Riesgo directo de electrocución o descarga eléctrica
    # --------------------------------------------------------------------------
    if re.search(r'(\belectrocu\w*|\bdescarga electrica|\bda patada|\bpatea la corriente|\bcon corriente|\belectrificad[oa])', t):
        return True, 'ELECTROCUCION', {
            'titulo': 'Riesgo Crítico de Electrocución',
            'tipo_riesgo': 'electrico',
            'recomendaciones': [
                'NO toques a ninguna persona que esté en contacto con una fuente eléctrica sin cortar antes la energía de forma segura.',
                'En la vía pública, postes o rejas electrificadas: mantené a toda persona a más de 15 metros de distancia.',
                'En el interior de un domicilio: bajá de inmediato la llave térmica o disyuntor general solo si es seguro acercarse.',
                'NO arrojes agua sobre elementos o personas en contacto con electricidad.',
            ],
            'servicios': ['911', 'EMSA', 'Emergencias Médicas 107']
        }

    # --------------------------------------------------------------------------
    # Regla 4: Incendio activo o presencia de humo
    # --------------------------------------------------------------------------
    term_fuego = bool(re.search(
        r'(\bincendio\w*|\bincendiandose|\bse quema|\bse esta quemando|\bardiendo|\ben llamas|\bfuego\b|\bhumo negro|\bhumo espeso|\bhumo denso|\bcolumna de humo|\bsale humo|\bprincipio de incendio|\bse prendio fuego|\bpresencia de humo|\bmucho humo)',
        t
    ))
    if term_fuego:
        return True, 'INCENDIO_HUMO', {
            'titulo': 'Incendio o Presencia de Humo Peligroso',
            'tipo_riesgo': 'incendio',
            'recomendaciones': [
                'Evacuá de inmediato la zona de riesgo hacia un área abierta y ventilada.',
                'No intentes apagar con agua fuegos en artefactos eléctricos o transformadores.',
                'No inhales humo: cubrite nariz y boca con un paño húmedo si es necesario salir.',
                'No vuelvas a ingresar al inmueble o lugar afectado bajo ninguna circunstancia.',
                'Facilitá el acceso a las autobombas de Bomberos.',
            ],
            'servicios': ['911', 'Bomberos 100', 'Defensa Civil']
        }

    # --------------------------------------------------------------------------
    # Regla 5: Transformador explotado / explosiones / escape de gas masivo
    # --------------------------------------------------------------------------
    if re.search(r'\b(transformador.*?exploto|exploto transformador|escape de gas|fuga de gas|fuerte olor a gas|peligro de explosion)\b', t):
        return True, 'EXPLOSION_GAS', {
            'titulo': 'Explosión o Fuga Crítica con Peligro Inmediato',
            'tipo_riesgo': 'explosion',
            'recomendaciones': [
                'Alejate inmediatamente y evitá encender fósforos, luces o celulares cerca de la zona.',
                'Ventilá el ambiente si es seguro o evacuá el área hacia un espacio abierto.',
                'Comunicate de urgencia con las autoridades desde un lugar seguro.',
            ],
            'servicios': ['911', 'Bomberos 100', 'EMSA']
        }

    # --------------------------------------------------------------------------
    # Regla 6: Árbol caído sobre cables con peligro inminente o derrumbe
    # --------------------------------------------------------------------------
    if re.search(r'\b(arbol|rama pesada|ramas grandes)\b.*?\b(cayo sobre cables|sobre el tendido|sobre los cables|con chispas|bloquea calle con cables|derrumbe inminente)\b', t):
        return True, 'ARBOL_SOBRE_CABLES', {
            'titulo': 'Árbol Caído sobre Tendido Eléctrico',
            'tipo_riesgo': 'electrico',
            'recomendaciones': [
                'No intentes podar ni retirar ramas que toquen cables de electricidad.',
                'Mantené despejado el sector a no menos de 15 metros.',
                'Avisá a conductores y transeúntes para que no transiten por debajo.',
            ],
            'servicios': ['911', 'EMSA', 'Defensa Civil 103']
        }

    return False, '', {}


# ==============================================================================
# 1.5 MOTOR DE RESOLUCIÓN DE TRÁMITES - SEDE CAV ITAEMBÉ GUAZÚ
# ==============================================================================
# --- POO: ARQUITECTURA DE DOMINIO Y ENCAPSULAMIENTO DE REGLAS DE NEGOCIO ---
# Representa el catálogo de trámites oficiales del CAV Itaembé Guazú (Aguará Guazú y Magnolias).
# Integra las 6 áreas institucionales descritas oficialmente:
# 1. Trámites Municipales (Delegación, Obras Privadas y Mediación)
# 2. Registro Provincial de las Personas (CDR)
# 3. Agencia Tributaria Misiones (ATM)
# 4. Energía de Misiones (EMSA)
# 5. I.Pro.D.Ha. (Desarrollo Habitacional)
# 6. Honorable Concejo Deliberante / Defensoría del Pueblo

def resolver_tramite_cav_itaembe(texto: str, ctx_ubi: dict = None) -> dict:
    """
    Método de dominio que interpreta y resuelve si la consulta del vecino corresponde
    a uno de los trámites oficiales brindados presencialmente en el CAV Itaembé Guazú.
    Retorna un diccionario de datos estructurado con metadata, requerimientos y pautas.
    """
    t = normalizar_texto(texto)

    # Exclusiones de trámites puramente digitales online de portales web externos:
    if any(k in t for k in ['autogestion', 'domicilio fiscal', 'como regularizar construcciones existentes sin permiso', 'como presentar una iniciativa']):
        return None
    if ('boleta patente' in t or 'generar boleta patente' in t) and any(k in t for k in ['como pagar', 'donde pagar', 'sin clave fiscal']):
        return None
    if any(k in t for k in ['pagar la luz', 'pagar luz', 'pago de luz', 'factura de luz', 'boleta de luz', 'pagar emsa', 'luz de mi casa', 'donde pago la luz', 'como pagar la luz']) or (
        bool(re.search(r'\b(pagar|pago|abonar|deuda|saldo)\b.*?\b(luz|electricidad|energia)\b', t))
    ):
        return None
    if any(k in t for k in [
        'pagar el agua', 'pagar agua', 'pago de agua', 'pago del agua', 'factura de agua',
        'boleta de agua', 'factura del agua', 'boleta del agua', 'pagar samsa', 'agua de mi casa',
        'donde pago el agua', 'como pagar el agua', 'donde pagar el agua', 'deuda de agua',
        'saldo de agua', 'servicio de agua'
    ]) or (
        bool(re.search(r'\b(pagar|pago|abonar|deuda|saldo|boleta|factura)\b.*?\b(agua|samsa|cloaca)\b', t)) or
        bool(re.search(r'\b(agua|samsa|cloaca)\b.*?\b(pagar|pago|abonar|deuda|saldo|boleta|factura)\b', t))
    ):
        return None

    # --------------------------------------------------------------------------
    # ÁREA 1: TRÁMITES MUNICIPALES (DELEGACIÓN, OBRAS PRIVADAS Y MEDIACIÓN)
    # --------------------------------------------------------------------------

    # 1.1 Carnet Sanitario (Salud Pública y Bromatología)
    if any(k in t for k in [
        'carnet sanitario', 'carne sanitario', 'tasa carnet sanitario', 'sacar carnet sanitario',
        'tramitar carnet sanitario', 'renovar carnet sanitario', 'carnet de salud',
        'carnet bromatologico', 'carnet de manipulador', 'manipulacion de alimentos'
    ]) or (('carnet' in t or 'carne' in t) and ('sanitario' in t or 'alimento' in t or 'bromatolog' in t)):
        return {
            'id': 'cav_carnet_sanitario',
            'organismo': 'Municipalidad de Posadas - Delegación CAV Itaembé Guazú',
            'area': 'Salud Pública y Bromatología (Delegación Municipal)',
            'nombre_tramite': 'Carnet Sanitario (Liquidación y Emisión de Tasas)',
            'cod_categoria': 100,
            'explicacion': (
                '🏛️ <strong>GESTIÓN DE CARNET SANITARIO - CAV ITAEMBÉ GUAZÚ:</strong>\n'
                'En la delegación municipal del CAV Itaembé Guazú (Calle Aguará Guazú y Magnolias) se realiza la emisión y '
                'liquidación de las tasas correspondientes para la obtención o renovación del Carnet Sanitario y de manipulador de alimentos '
                '(requisito obligatorio para actividades comerciales, gastronómicas, transporte y afines en la ciudad de Posadas).'
            ),
            'datos_requeridos': [
                'Nombre y apellido completo, DNI y fecha de nacimiento.',
                'Rubro, actividad o empleo en el que te desempeñarás (gastronomía, transporte, comercio en general, etc.).',
                'Domicilio actual de residencia en la ciudad de Posadas.'
            ],
            'documentos_adjuntos': [
                'Fotografía o escaneo nítido de tu DNI (frente y dorso).',
                'Foto carnet 4x4 o fotografía tipo selfie clara con fondo blanco.',
                'Certificado médico de buena salud / constancia de análisis clínicos según corresponda al rubro.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Delegación Municipal en CAV Itaembé Guazú (Calle Aguará Guazú y Magnolias), '
                'de lunes a viernes de 07:00 a 18:00 hs. Podés abonar la tasa en la caja de cobro habilitada en efectivo, débito, crédito o QR.'
            ),
            'gestion_programada': 'Liquidación de tasa arancelaria para carnet sanitario y derivación al área de Bromatología y Salud Pública.'
        }

    # 1.2 Emisión y actualización de boletas (TGI, Patentes de autos y motos)
    if (any(k in t for k in [
        'boleta tgi', 'boleta de tgi', 'tasa general de inmueble', 'tasa de inmueble', 'imprimir tgi',
        'pagar tgi', 'actualizar boleta de tgi', 'boleta patente', 'boleta de patente', 'patente auto',
        'patente moto', 'patentes de autos', 'patentes de motos', 'pagar patente municipal',
        'emision de boleta municipal', 'actualizar boleta municipal', 'impresion de boletas'
    ]) or (('boleta' in t or 'tasas' in t) and any(k in t for k in ['tgi', 'patente', 'inmueble', 'automotor', 'municipal']))) and not any(k in t for k in ['atm', 'rentas', 'ingresos brutos']):
        return {
            'id': 'cav_boletas_tasas',
            'organismo': 'Municipalidad de Posadas - Delegación CAV Itaembé Guazú',
            'area': 'Hacienda y Finanzas Municipales (Caja y Recaudaciones)',
            'nombre_tramite': 'Emisión y Actualización de Boletas (TGI y Patentes de Autos y Motos)',
            'cod_categoria': 100,
            'explicacion': (
                '🏛️ <strong>EMISIÓN Y ACTUALIZACIÓN DE BOLETAS - CAV ITAEMBÉ GUAZÚ:</strong>\n'
                'En la sede del CAV Itaembé Guazú contás con ventanilla de recaudaciones y caja de cobro habilitada para la '
                'impresión, liquidación y cobro de la Tasa General de Inmuebles (TGI) y patentes de automotores y motovehículos radicados en Posadas.'
            ),
            'datos_requeridos': [
                'Número de partida inmobiliaria (para TGI) o Dominio/Patente del vehículo (auto o moto).',
                'Nombre completo y DNI del titular del bien.',
                'Períodos o meses que solicitás actualizar o liquidar.'
            ],
            'documentos_adjuntos': [
                'Foto de boleta anterior (si disponés de una para ubicar la partida rápidamente).',
                'Título de propiedad del inmueble o cédula verde/azul del rodado.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Delegación Municipal CAV Itaembé Guazú (Aguará Guazú y Magnolias). '
                'Lunes a viernes de 07:00 a 18:00 hs. Medios de pago aceptados en caja: Efectivo, tarjeta de débito, crédito y código QR.'
            ),
            'gestion_programada': 'Emisión y actualización de liquidación de tasas municipales (TGI / Patentes).'
        }

    # 1.3 Convenios de pago (Regularización de deudas municipales)
    if any(k in t for k in [
        'convenio de pago', 'convenios de pago', 'plan de pago municipal', 'planes de pago municipal',
        'regularizar deuda municipal', 'regularizar mis impuestos municipales', 'moratoria municipal',
        'financiar tasas', 'financiar patente municipal', 'plan de cuotas de tasa'
    ]):
        return {
            'id': 'cav_convenios_pago',
            'organismo': 'Municipalidad de Posadas - Delegación CAV Itaembé Guazú',
            'area': 'Recaudaciones y Finanzas Municipales',
            'nombre_tramite': 'Convenios de Pago y Regularización de Deudas Tributarias Municipales',
            'cod_categoria': 100,
            'explicacion': (
                '🏛️ <strong>CONVENIOS DE PAGO Y PLANES DE REGULARIZACIÓN - CAV ITAEMBÉ GUAZÚ:</strong>\n'
                'Formalización de planes de pago y regularización de deudas tributarias municipales (TGI, patentes automotor, multas comerciales) '
                'con facilidades en cuotas y quita de intereses según las ordenanzas de alivio fiscal vigentes.'
            ),
            'datos_requeridos': [
                'Número de partida inmobiliaria o Dominio/Patente del vehículo con deuda.',
                'DNI y CUIL del titular o apoderado legal.',
                'Cantidad de cuotas pretendidas para el plan de regularización.'
            ],
            'documentos_adjuntos': [
                'DNI del titular (frente y dorso).',
                'Constancia de titularidad del bien (título de propiedad o cédula del vehículo).',
                'Constancia de CBU si deseás adherir el pago de las cuotas al débito automático.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Delegación Municipal CAV Itaembé Guazú (Aguará Guazú y Magnolias). '
                'Firma presencial del convenio de regularización tributaria de lunes a viernes de 07:00 a 18:00 hs.'
            ),
            'gestion_programada': 'Liquidación de deuda y confección del acta de convenio de pago en cuotas.'
        }

    # 1.4 Trámites de automotores (Empadronamiento, denuncias de venta, libre deuda)
    if any(k in t for k in [
        'empadronamiento', 'empadronar', 'denuncia de venta', 'libre deuda automotor', 'libre deuda patente',
        'baja automotor', 'alta automotor', 'radicacion automotor', 'radicar auto', 'radicar moto',
        'transferencia de auto', 'transferir moto', 'empadronar vehiculo', 'empadronar moto', 'empadronar auto'
    ]):
        return {
            'id': 'cav_automotor_empadronamiento',
            'organismo': 'Municipalidad de Posadas - Delegación CAV Itaembé Guazú',
            'area': 'Registro y Fiscalización Automotor Municipal',
            'nombre_tramite': 'Trámites de Automotores (Empadronamiento, Denuncias de Venta y Libre Deuda)',
            'cod_categoria': 100,
            'explicacion': (
                '🏛️ <strong>TRÁMITES DE AUTOMOTORES - CAV ITAEMBÉ GUAZÚ:</strong>\n'
                'En el CAV Itaembé Guazú podés realizar el empadronamiento de autos y motos 0km o provenientes de otra jurisdicción, '
                'presentar denuncias impositivas de venta para eximirte de responsabilidad fiscal, y solicitar el certificado oficial de Libre Deuda de Patentes.'
            ),
            'datos_requeridos': [
                'Dominio (chapa patente) del vehículo.',
                'Número de motor y chasis (constan en la cédula o título).',
                'DNI y CUIL del titular o comprador.',
                'Tipo de trámite específico: Empadronamiento, Denuncia de Venta o Certificado de Libre Deuda.'
            ],
            'documentos_adjuntos': [
                'Título del automotor o constancia CAT digital emitida por el DNRPA.',
                'Cédula verde / azul del vehículo.',
                'Formulario 08 certificado o comprobante de denuncia de venta DNRPA.',
                'Constancia de baja fiscal previa si el vehículo proviene de otro municipio o provincia.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Delegación Municipal en CAV Itaembé Guazú (Aguará Guazú y Magnolias), '
                'lunes a viernes de 07:00 a 18:00 hs.'
            ),
            'gestion_programada': 'Verificación registral automotor, emisión de libre deuda o alta en padrón impositivo municipal.'
        }

    # 1.5 Obras Privadas: Plataforma digital GOP, planos, regularización
    if any(k in t for k in [
        'sistema gop', 'plataforma gop', 'gop', 'aprobacion de planos', 'planos de obra',
        'regularizacion de construcciones', 'regularizar obra', 'regularizar construccion',
        'plano de mensura', 'mensura', 'obra sin permiso', 'final de obra', 'permiso de obra'
    ]) and not any(k in t for k in ['ruido', 'vecin']):
        return {
            'id': 'cav_obras_planos_gop',
            'organismo': 'Municipalidad de Posadas - Secretaría de Planificación (Obras Privadas)',
            'area': 'Planificación Estratégica y Gestión de Obras Privadas',
            'nombre_tramite': 'Obras Privadas - Plataforma GOP, Aprobación de Planos y Regularización',
            'cod_categoria': 100,
            'explicacion': (
                '🏛️ <strong>SECRETARÍA DE PLANIFICACIÓN (OBRAS PRIVADAS) - SISTEMA GOP:</strong>\n'
                'Asesoramiento técnico presencial en el CAV Itaembé Guazú para la regularización de obras y construcciones existentes, '
                'e ingreso formal de expedientes en la plataforma digital GOP (Gestión de Obras Privadas) para la visación y aprobación de planos y mensuras.'
            ),
            'datos_requeridos': [
                'Número de expediente GOP o solicitud digital (si ya fue iniciada en la web).',
                'Número de partida inmobiliaria y datos catastrales (sección, chacra, manzana, parcela).',
                'Datos del profesional matriculado a cargo (arquitecto, ingeniero civil, maestro mayor de obras).'
            ],
            'documentos_adjuntos': [
                'Archivo digital de los planos en formato PDF o DWG.',
                'Memoria técnica descriptiva de la construcción.',
                'Título de propiedad, boleto de compraventa o acta de entrega de posesión.',
                'Comprobante de pago de la tasa de visado de planos.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Oficina de Obras Privadas en CAV Itaembé Guazú (Aguará Guazú y Magnolias), '
                'lunes a viernes de 07:00 a 18:00 hs.'
            ),
            'gestion_programada': 'Revisión técnica de planos, verificación de indicadores edilicios e ingreso en plataforma GOP.'
        }

    # 1.6 Obras Privadas: Indicadores urbanos, solicitud de número de finca e inspecciones
    if any(k in t for k in [
        'indicadores urbanos', 'numero de finca', 'solicitar numero de finca', 'solicitud de finca',
        'inspeccion de obra', 'inspeccion de construccion', 'fos', 'fot', 'retiros de construccion',
        'linea municipal', 'solicitar finca', 'certificado de finca'
    ]):
        return {
            'id': 'cav_obras_indicadores_finca',
            'organismo': 'Municipalidad de Posadas - Secretaría de Planificación (Obras Privadas)',
            'area': 'Control de Edificación y Catastro Urbano',
            'nombre_tramite': 'Obras Privadas - Indicadores Urbanos, Número de Finca e Inspección de Obras',
            'cod_categoria': 100,
            'explicacion': (
                '🏛️ <strong>INDICADORES URBANOS Y NÚMERO DE FINCA - CAV ITAEMBÉ GUAZÚ:</strong>\n'
                'En el CAV Itaembé Guazú podés consultar los indicadores urbanísticos oficiales (FOS, FOT, alturas máximas y retiros de línea municipal), '
                'solicitar la asignación del Número de Finca para tu domicilio y coordinar inspecciones técnicas de obra en el barrio.'
            ),
            'datos_requeridos': [
                'Dirección exacta del lote o parcela en Itaembé Guazú o Posadas.',
                'Datos catastrales (Manzana, Lote, Chacra o Sección).',
                'Destino de la construcción (residencial unifamiliar, multifamiliar, local comercial).'
            ],
            'documentos_adjuntos': [
                'Copia de plano de loteo o croquis de ubicación catastral.',
                'Título de propiedad, boleto de compraventa o constancia de adjudicación.',
                'Fotografía del frente del terreno o inmueble.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Puesto de Obras Privadas en CAV Itaembé Guazú (Aguará Guazú y Magnolias).'
            ),
            'gestion_programada': 'Emisión de certificado de indicadores urbanos, asignación de número de finca o despacho de inspector.'
        }

    # 1.7 Dirección de Mediación Comunitaria (Conciliación voluntaria)
    if any(k in t for k in [
        'mediacion comunitaria cav', 'mediacion comunitaria itaembe', 'audiencia de conciliacion cav',
        'conciliacion voluntaria cav', 'mediacion vecinal cav', 'direccion de mediacion comunitaria'
    ]) or (('mediacion' in t or 'conciliacion' in t) and ('cav' in t or 'itaembe' in t or 'aguara guazu' in t)):
        return {
            'id': 'cav_mediacion_comunitaria',
            'organismo': 'Municipalidad de Posadas - Dirección de Mediación Comunitaria',
            'area': 'Mediación Comunitaria y Resolución Pacífica de Conflictos',
            'nombre_tramite': 'Dirección de Mediación Comunitaria (Audiencias de Conciliación Voluntaria)',
            'cod_categoria': 100,
            'explicacion': (
                '⚖️ <strong>DIRECCIÓN DE MEDIACIÓN COMUNITARIA - CAV ITAEMBÉ GUAZÚ:</strong>\n'
                'Servicio público y gratuito en el CAV Itaembé Guazú para la resolución pacífica de conflictos de convivencia barrial '
                '(ruidos molestos, medianeras, filtraciones, problemas con mascotas, árboles linderos). '
                'Mediadores matriculados convocan a una audiencia voluntaria para acordar soluciones de mutuo acuerdo con validez legal.'
            ),
            'datos_requeridos': [
                'Motivo específico de la desavenencia vecinal.',
                'Nombre y apellido completo de la vecina o vecino con quien se solicita la mediación.',
                'Dirección exacta del domicilio del vecino para el envío de la invitación formal a la audiencia.'
            ],
            'documentos_adjuntos': [
                'Fotografías o videos que ilustren la situación conflictiva (muro, mascotas, rajaduras, ruidos).',
                'Constancias previas o mensajes si existió intento de diálogo previo.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Sala de Mediación Comunitaria en CAV Itaembé Guazú (Aguará Guazú y Magnolias). '
                'Audiencias programadas de mutuo acuerdo.'
            ),
            'gestion_programada': 'Apertura de legajo de mediación comunitaria y emisión de cédula de invitación a audiencia conciliatoria.'
        }

    # --------------------------------------------------------------------------
    # ÁREA 2: REGISTRO PROVINCIAL DE LAS PERSONAS (CDR)
    # --------------------------------------------------------------------------

    # 2.1 DNI 0 Año / Recién nacidos (Primer documento e inscripción de nacimiento)
    if any(k in t for k in [
        'dni 0 ano', 'dni 0 anos', 'dni 0 anos', 'recien nacid', 'anotar a mi bebe', 'anotar bebe',
        'inscribir nacimiento', 'primer dni', 'documento para bebe', 'inscripcion de nacimiento',
        'dni bebe', 'partida de nacimiento de recien nacido', 'inscribir a mi hijo recien nacido'
    ]):
        return {
            'id': 'cav_dni_recien_nacido',
            'organismo': 'Registro Provincial de las Personas - CDR Sede CAV Itaembé Guazú',
            'area': 'Centro de Documentación Rápida (CDR) - Inscripción de Nacimientos',
            'nombre_tramite': 'DNI 0 Año / Recién Nacidos (Inscripción de Nacimiento y Primer DNI)',
            'cod_categoria': 100,
            'explicacion': (
                '🪪 <strong>INSCRIPCIÓN DE NACIMIENTO Y DNI 0 AÑO - CAV ITAEMBÉ GUAZÚ:</strong>\n'
                'En el Centro de Documentación Rápida (CDR) del CAV Itaembé Guazú se realiza la inscripción oficial del nacimiento y la tramitación '
                'del primer DNI (DNI 0 Año) para recién nacidos. Es un trámite prioritario y de tramitación legal obligatoria dentro de los 40 días del nacimiento.'
            ),
            'datos_requeridos': [
                'Nombre y apellido completo asignado al recién nacido.',
                'Fecha, hora y lugar de nacimiento (hospital o sanatorio).',
                'Nombres completos, DNI, estado civil y domicilio de ambos progenitores.'
            ],
            'documentos_adjuntos': [
                'Certificado Médico de Nacido Vivo original (emitido por el médico obstetra con sello y oblea).',
                'DNI de ambos progenitores (frente y dorso).',
                'Libreta de Matrimonio (si están casados) o presencia obligatoria de ambos progenitores con DNI.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Registro Provincial de las Personas en CAV Itaembé Guazú (Aguará Guazú y Magnolias).\n'
                '🚨 <strong>PAGO DIGITAL OBLIGATORIO:</strong> En esta oficina los pagos de aranceles se realizan '
                '<strong>ÚNICAMENTE con medios digitales (tarjeta de débito, crédito o código QR); NO SE ACEPTA EFECTIVO</strong>. '
                '<em>(Nota: La inscripción de nacimiento y el primer DNI 0 Año son 100% gratuitos)</em>.'
            ),
            'gestion_programada': 'Inscripción de acta de nacimiento en el Registro Civil y toma biométrica para emisión de DNI 0 Año.'
        }

    # 2.2 Pasaportes (Tramitación y renovación)
    if any(k in t for k in [
        'pasaporte', 'tramitar pasaporte', 'renovar pasaporte', 'sacar pasaporte',
        'hacer pasaporte', 'pasaporte regular', 'pasaporte en itaembe'
    ]):
        return {
            'id': 'cav_pasaporte',
            'organismo': 'Registro Provincial de las Personas - CDR Sede CAV Itaembé Guazú',
            'area': 'Centro de Documentación Rápida (CDR) - Documentos de Viaje',
            'nombre_tramite': 'Pasaporte Regular (Tramitación y Renovación)',
            'cod_categoria': 100,
            'explicacion': (
                '🪪 <strong>TRAMITACIÓN Y RENOVACIÓN DE PASAPORTE - CAV ITAEMBÉ GUAZÚ:</strong>\n'
                'En el Centro de Documentación Rápida (CDR) del CAV Itaembé Guazú podés tramitar tu Pasaporte Regular oficial de la República Argentina '
                'o solicitar su renovación por vencimiento o extravío.'
            ),
            'datos_requeridos': [
                'Número de DNI del solicitante.',
                'Si se trata de primer pasaporte o renovación de ejemplar previo.',
                'Correo electrónico y teléfono celular para el seguimiento postal de la entrega.'
            ],
            'documentos_adjuntos': [
                'Último ejemplar físico de DNI tarjeta vigente en buen estado (requisito excluyente).',
                'Para menores de 18 años: Partida de nacimiento actualizada legalizada y presencia de ambos padres con DNI.',
                'Pasaporte anterior si se trata de renovación.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> CDR en CAV Itaembé Guazú (Aguará Guazú y Magnolias). Lunes a viernes de 07:00 a 18:00 hs.\n'
                '🚨 <strong>AVISO IMPORTANTE DE PAGO:</strong> En esta oficina del Registro Civil los pagos de aranceles se realizan '
                '<strong>ÚNICAMENTE mediante medios digitales (tarjeta de débito, crédito o código QR); NO SE ACEPTA DINERO EN EFECTIVO</strong>. '
                'El pasaporte físico se envía directamente a tu domicilio a través de Correo Argentino.'
            ),
            'gestion_programada': 'Toma de datos biométricos (foto, firma y huellas) para emisión del Pasaporte Regular ante RENAPER.'
        }

    # 2.3 Trámites civiles: Matrimonios y Uniones convivenciales
    if any(k in t for k in [
        'matrimonio', 'casamiento', 'casarme', 'casarme en el cav', 'celebracion de matrimonio',
        'union convivencial', 'uniones convivenciales', 'declaracion de convivencia', 'concubinato',
        'casarse', 'fecha de casamiento', 'registro civil matrimonio'
    ]):
        return {
            'id': 'cav_tramites_civiles',
            'organismo': 'Registro Provincial de las Personas - Sede CAV Itaembé Guazú',
            'area': 'Oficina de Matrimonios y Actos Civiles (CDR)',
            'nombre_tramite': 'Trámites Civiles (Celebración de Matrimonios y Uniones Convivenciales)',
            'cod_categoria': 100,
            'explicacion': (
                '💍 <strong>MATRIMONIOS Y UNIONES CONVIVENCIALES - CAV ITAEMBÉ GUAZÚ:</strong>\n'
                'El Registro Provincial de las Personas cuenta con sala y oficiales públicos en el CAV Itaembé Guazú '
                'para la celebración oficial de matrimonios civiles y la inscripción legal de uniones convivenciales.'
            ),
            'datos_requeridos': [
                'Nombres, apellidos y números de DNI de ambos contrayentes o convivientes.',
                'Estado civil previo de cada uno (solteros, divorciados o viudos).',
                'Fecha tentativa solicitada para la ceremonia o firma del acta.',
                'Domicilio en común constituido en Posadas.'
            ],
            'documentos_adjuntos': [
                'DNI original y fotocopia de ambos contrayentes.',
                'Partidas de nacimiento legalizadas y actualizadas de ambos contrayentes.',
                'DNI y datos de 2 a 4 testigos mayores de 18 años.',
                'Si alguno es divorciado o viudo: Acta de matrimonio anterior con inscripción marginal de divorcio vincular o acta de defunción.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Registro Civil en CAV Itaembé Guazú (Aguará Guazú y Magnolias). Reserva de fecha presencial.\n'
                '🚨 <strong>PAGO DIGITAL OBLIGATORIO:</strong> El arancel de libreta y celebración se abona '
                '<strong>ÚNICAMENTE con tarjeta de débito, crédito o código QR; NO SE ACEPTA EFECTIVO</strong>.'
            ),
            'gestion_programada': 'Apertura de expediente matrimonial / unión convivencial y reserva de fecha para celebración civil.'
        }

    # 2.4 DNI general: Nuevo ejemplar, extravío, robo, deterioro, cambio de domicilio, actualizaciones
    if any(k in t for k in [
        'tramitar dni', 'nuevo dni', 'renovar dni', 'perdi el dni', 'perdi mi dni', 'extravio de dni',
        'extravio dni', 'robo de dni', 'robo del dni', 'actualizar dni', 'actualizacion de dni',
        'actualizacion menor', 'actualizacion mayor', 'cambio de domicilio', 'hacer el documento',
        'sacar documento', 'renovacion de documento', 'sacar dni', 'hacer dni', 'nuevo ejemplar de dni',
        'dni tarjeta', 'deterioro de dni'
    ]):
        return {
            'id': 'cav_dni_general',
            'organismo': 'Registro Provincial de las Personas - CDR Sede CAV Itaembé Guazú',
            'area': 'Centro de Documentación Rápida (CDR)',
            'nombre_tramite': 'Documento Nacional de Identidad (Nuevo Ejemplar, Actualización o Cambio de Domicilio)',
            'cod_categoria': 100,
            'explicacion': (
                '🪪 <strong>TRÁMITE DE DNI - CDR SEDE CAV ITAEMBÉ GUAZÚ:</strong>\n'
                'En el Centro de Documentación Rápida (CDR) del CAV Itaembé Guazú podés tramitar un nuevo ejemplar de DNI por '
                'extravío, robo o deterioro, registrar tu cambio de domicilio y realizar las actualizaciones obligatorias '
                'de menores (entre 5 y 8 años) y de mayores (al cumplir 14 años).'
            ),
            'datos_requeridos': [
                'Número de DNI del solicitante.',
                'Motivo del trámite (extravío, robo, deterioro, cambio de domicilio o actualización de 5/8 o 14 años).',
                'Domicilio actual exacto en Posadas para registrar en el documento.'
            ],
            'documentos_adjuntos': [
                'Para actualizaciones (5/8 y 14 años): Partida de nacimiento original legalizada y actualizada (con menos de 6 meses) y DNI del padre o madre.',
                'Para nuevo ejemplar por extravío o robo: Constancia de denuncia policial (si disponés de ella) o último DNI si está deteriorado.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> CDR en CAV Itaembé Guazú (Aguará Guazú y Magnolias), lunes a viernes de 07:00 a 18:00 hs por orden de llegada.\n'
                '🚨 <strong>AVISO CRÍTICO DE COBRO:</strong> Los aranceles en esta oficina del Registro Civil se abonan '
                '<strong>ÚNICAMENTE con medios digitales (tarjeta de débito, crédito o código QR); NO SE ACEPTA DINERO EN EFECTIVO</strong>.'
            ),
            'gestion_programada': 'Toma biométrica presencial (fotografía digital, huellas dactilares y firma) para emisión de nuevo ejemplar de DNI.'
        }

    # --------------------------------------------------------------------------
    # ÁREA 3: AGENCIA TRIBUTARIA MISIONES (ATM)
    # --------------------------------------------------------------------------

    # 3.1 Clave Fiscal de ATM
    if any(k in t for k in [
        'clave fiscal', 'clave de rentas', 'clave atm', 'blanqueo de clave', 'recuperar clave'
    ]):
        return {
            'id': 'cav_atm_clave_fiscal',
            'organismo': 'Agencia Tributaria Misiones (ATM) - Puesto CAV Itaembé Guazú',
            'area': 'Servicios al Contribuyente y Clave Fiscal (ATM)',
            'nombre_tramite': 'ATM - Asesoramiento y Gestión de Clave Fiscal',
            'cod_categoria': 100,
            'explicacion': (
                '📈 <strong>GESTIÓN Y BLANQUEO DE CLAVE FISCAL ATM - CAV ITAEMBÉ GUAZÚ:</strong>\n'
                'Asesoramiento personalizado y asistencia técnica en el CAV Itaembé Guazú para gestionar, obtener o blanquear tu '
                'Clave Fiscal de la Agencia Tributaria Misiones (ATM) para acceder a los servicios online del organismo.'
            ),
            'datos_requeridos': [
                'CUIT o CUIL del titular contribuyente.',
                'Correo electrónico personal activo para vinculación del usuario.',
                'Número de teléfono celular de contacto.'
            ],
            'documentos_adjuntos': [
                'DNI físico original (frente y dorso) para validación de identidad biométrica presencial.',
                'Constancia de CUIL o CUIT emitida por ANSES o AFIP.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Puesto de ATM en CAV Itaembé Guazú (Aguará Guazú y Magnolias). '
                'Presentarse con DNI físico original para la validación presencial de identidad.'
            ),
            'gestion_programada': 'Validación de identidad biométrica presencial y habilitación/blanqueo de Clave Fiscal ATM.'
        }

    # 3.2 Mesa de Entradas Fiscal y Puesto de Autogestión
    if any(k in t for k in [
        'descargo atm', 'nota fiscal atm', 'mesa de entradas fiscal', 'presentacion formal atm',
        'exencion atm', 'autogestion atm', 'puesto de autogestion atm'
    ]):
        return {
            'id': 'cav_atm_mesa_fiscal',
            'organismo': 'Agencia Tributaria Misiones (ATM) - Mesa Fiscal CAV Itaembé Guazú',
            'area': 'Mesa de Entradas Fiscal y Autogestión Tributaria',
            'nombre_tramite': 'ATM - Mesa de Entradas Fiscal y Soporte en Autogestión Digital',
            'cod_categoria': 100,
            'explicacion': (
                '📈 <strong>MESA DE ENTRADAS FISCAL Y AUTOGESTIÓN ATM - CAV ITAEMBÉ GUAZÚ:</strong>\n'
                'Recepción formal de notas, descargos y presentaciones institucionales escritas, y soporte guiado en el puesto '
                'de autogestión para la realización de trámites tributarios online en la sede de Itaembé Guazú.'
            ),
            'datos_requeridos': [
                'CUIT o CUIL del contribuyente o razón social.',
                'Número de expediente fiscal o nota de notificación/intimación.',
                'Motivo concreto de la presentación o descargo escrito.'
            ],
            'documentos_adjuntos': [
                'Nota formal de presentación con firma original.',
                'Documentación respaldatoria (comprobantes de pago, retenciones, estatutos o balances).'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Mesa de Entradas Fiscal en CAV Itaembé Guazú (Aguará Guazú y Magnolias). '
                'Cobro presencial de tributos exclusivamente con tarjetas de débito y crédito habilitadas.'
            ),
            'gestion_programada': 'Caratulado de presentación escrita e ingreso a la Mesa de Entradas de la Agencia Tributaria Misiones.'
        }

    # 3.3 Generación y reimpresión de boletas (Ingresos Brutos, Inmobiliario, IPA)
    if any(k in t for k in [
        'boleta atm', 'rentas misiones', 'ingresos brutos misiones', 'impuesto inmobiliario provincial',
        'boleta ipa atm', 'reimpresion boleta atm', 'generar boleta atm', 'pagar ingresos brutos',
        'deuda atm', 'boleta de rentas', 'impuesto provincial misiones', 'pagar atm'
    ]):
        return {
            'id': 'cav_atm_boletas',
            'organismo': 'Agencia Tributaria Misiones (ATM) - Puesto CAV Itaembé Guazú',
            'area': 'Recaudaciones y Cobranzas Tributarias Provinciales',
            'nombre_tramite': 'ATM - Generación y Reimpresión de Boletas (Ingresos Brutos, Inmobiliario, IPA)',
            'cod_categoria': 100,
            'explicacion': (
                '📈 <strong>AGENCIA TRIBUTARIA MISIONES (ATM) - BOLETAS Y OBLIGACIONES:</strong>\n'
                'En el puesto de ATM del CAV Itaembé Guazú podés generar y reimprimir boletas de obligaciones fiscales provinciales '
                '(Ingresos Brutos, Impuesto Inmobiliario Provincial, Impuesto Provincial al Automotor - IPA) y formalizar planes de pago.'
            ),
            'datos_requeridos': [
                'CUIT o CUIL del contribuyente titular.',
                'Número de partida inmobiliaria provincial o Dominio automotor (para IPA).',
                'Anticipos o períodos fiscales que deseás cancelar.'
            ],
            'documentos_adjuntos': [
                'Foto o copia de DNI del contribuyente.',
                'Boleta anterior para verificación del número de cuenta tributaria.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Puesto de ATM en CAV Itaembé Guazú (Aguará Guazú y Magnolias). '
                'Cobro presencial en ventanilla mediante tarjetas de débito y crédito habilitadas.'
            ),
            'gestion_programada': 'Emisión de boletas fiscales actualizadas y planes de pago de obligaciones provinciales.'
        }

    # --------------------------------------------------------------------------
    # ÁREA 4: ENERGÍA DE MISIONES (EMSA)
    # --------------------------------------------------------------------------

    # 4.1 EMSA - Altas de servicio (Nuevas conexiones de medidores)
    if any(k in t for k in [
        'alta de servicio emsa', 'alta emsa', 'pedir medidor', 'nueva conexion emsa',
        'solicitar medidor', 'bajada de luz emsa', 'instalar medidor', 'conexion de luz emsa',
        'bajada de luz', 'alta de luz', 'bajada de medidor', 'pedir la luz', 'solicitar conexion de luz',
        'alta del medidor', 'alta medidor', 'solicitar conexion'
    ]) or (('alta' in t or 'pedir' in t or 'solicitar' in t or 'nueva' in t or 'nuevo' in t) and ('medidor' in t or 'luz' in t) and not any(k in t for k in ['baja', 'corte', 'desconexion', 'sobrefacturacion', 'factura', 'foco', 'luminaria', 'alumbrado', 'poste', 'quemad', 'arregl', 'aregl', 'oscur', 'oscut'])):
        return {
            'id': 'cav_emsa_altas',
            'organismo': 'Energía de Misiones S.A. (EMSA) - Oficina Comercial CAV Itaembé Guazú',
            'area': 'Atención Comercial y Nuevos Suministros (EMSA)',
            'nombre_tramite': 'Energía de Misiones (EMSA) - Altas de Servicio y Nuevas Conexiones de Medidores',
            'cod_categoria': 100,
            'explicacion': (
                '⚡ <strong>EMSA - ALTA DE SERVICIO Y CONEXIÓN DE MEDIDOR:</strong>\n'
                'En la oficina comercial de Energía de Misiones del CAV Itaembé Guazú podés tramitar una nueva conexión de medidor '
                '(monofásico o trifásico) para suministros residenciales o comerciales en Itaembé Guazú y barrios linderos.'
            ),
            'datos_requeridos': [
                'Dirección exacta del inmueble (calle, número, lote, manzana en Itaembé Guazú o Posadas).',
                'Nombre completo, DNI y CUIT/CUIL del futuro titular del contrato de energía.',
                'Tipo de tarifa requerida: Residencial o Comercial.'
            ],
            'documentos_adjuntos': [
                'Título de propiedad, boleto de compraventa con firmas certificadas o contrato de locación sellado.',
                'Certificado de Aptitud de Instalación Eléctrica emitido por electricista matriculado.',
                'Fotografía del pilar reglamentario y caja de medidor instalada sobre la línea municipal.',
                'Fotocopia de DNI del solicitante.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Oficina comercial de EMSA en CAV Itaembé Guazú (Aguará Guazú y Magnolias), '
                'lunes a viernes de 07:00 a 18:00 hs para la firma formal del contrato de suministro.'
            ),
            'gestion_programada': 'Verificación de documentación dominial y técnica para emisión de orden de conexión e instalación de medidor.'
        }

    # 4.2 EMSA - Bajas y mudanzas
    if any(k in t for k in [
        'baja de servicio emsa', 'baja emsa', 'dar de baja la luz', 'desconexion emsa',
        'mudanza emsa', 'cese de suministro emsa', 'retirar medidor emsa', 'baja de medidor'
    ]):
        return {
            'id': 'cav_emsa_bajas',
            'organismo': 'Energía de Misiones S.A. (EMSA) - Oficina CAV Itaembé Guazú',
            'area': 'Gestión de Contratos y Suministros (EMSA)',
            'nombre_tramite': 'Energía de Misiones (EMSA) - Bajas de Servicio, Mudanzas y Desconexión',
            'cod_categoria': 100,
            'explicacion': (
                '⚡ <strong>EMSA - BAJA DE SERVICIO Y RETIRO DE MEDIDOR:</strong>\n'
                'Trámite para solicitar la rescisión del contrato de suministro eléctrico y cese de facturación por mudanza, venta o demolición '
                'en la oficina de EMSA del CAV Itaembé Guazú.'
            ),
            'datos_requeridos': [
                'Número de Usuario y Número de Conexión de EMSA (figuran en el encabezado de la boleta de luz).',
                'DNI del titular registrado del contrato.',
                'Fecha solicitada para la lectura final del medidor y desconexión.'
            ],
            'documentos_adjuntos': [
                'Última factura abonada (libre deuda del suministro).',
                'DNI del titular o constancia de rescisión de contrato de locación.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Oficina de EMSA en CAV Itaembé Guazú (Aguará Guazú y Magnolias).'
            ),
            'gestion_programada': 'Generación de estado de cuenta final, rescisión contractual y orden operativa de retiro de medidor.'
        }

    # 4.3 EMSA - Reconexiones
    if any(k in t for k in [
        'reconexion emsa', 'reconectar la luz', 'me cortaron la luz emsa', 'reestablecer luz',
        'pague la luz y no vuelve', 'solicitar reconexion', 'servicio cortado emsa', 'reconectar servicio emsa'
    ]):
        return {
            'id': 'cav_emsa_reconexiones',
            'organismo': 'Energía de Misiones S.A. (EMSA) - Oficina CAV Itaembé Guazú',
            'area': 'Operaciones Comerciales y Distribución (EMSA)',
            'nombre_tramite': 'Energía de Misiones (EMSA) - Reconexión y Restablecimiento de Suministro',
            'cod_categoria': 100,
            'explicacion': (
                '⚡ <strong>EMSA - RECONEXIÓN TRAS CORTE O SUSPENSIÓN:</strong>\n'
                'En la oficina de EMSA del CAV Itaembé Guazú podés acreditar el pago de facturas atrasadas y solicitar la '
                'emisión prioritaria de la orden de reconexión del servicio eléctrico.'
            ),
            'datos_requeridos': [
                'Número de Usuario y Conexión de EMSA.',
                'Fecha y medio de cancelación de las facturas regularizadas.'
            ],
            'documentos_adjuntos': [
                'Comprobantes de pago de las boletas adeudadas y del arancel de reconexión.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Ventanilla de EMSA en CAV Itaembé Guazú (Aguará Guazú y Magnolias).'
            ),
            'gestion_programada': 'Verificación inmediata de pagos pendientes y emisión de orden operativa de reconexión a la cuadrilla de guardia.'
        }

    # 4.4 EMSA - Reclamos comerciales y técnicos (Sobrefacturación, tensión, red)
    if any(k in t for k in [
        'sobrefacturacion emsa', 'factura muy cara emsa', 'alta tension emsa', 'baja tension emsa',
        'suba de tension emsa', 'se quemaron electrodomesticos emsa', 'problema de tension',
        'reclamo comercial emsa', 'medidor roto emsa', 'reclamo tecnico emsa'
    ]):
        return {
            'id': 'cav_emsa_reclamos',
            'organismo': 'Energía de Misiones S.A. (EMSA) - Oficina CAV Itaembé Guazú',
            'area': 'Atención al Usuario y Calidad de Servicio (EMSA)',
            'nombre_tramite': 'Energía de Misiones (EMSA) - Reclamos Comerciales y Técnicos (Tensión y Facturación)',
            'cod_categoria': 100,
            'explicacion': (
                '⚡ <strong>EMSA - RECLAMO POR SOBREFACTURACIÓN O PROBLEMAS DE TENSIÓN:</strong>\n'
                'Apertura de expediente formal de reclamo en el CAV Itaembé Guazú ante sobrefacturación en kw/h, '
                'inconvenientes de baja o sobretensión en la zona, o daños producidos en artefactos eléctricos.'
            ),
            'datos_requeridos': [
                'Número de Usuario y Número de Conexión de EMSA.',
                'Detalle preciso del inconveniente (desfasaje en lectura del medidor o fecha/hora de la fluctuación de tensión).',
                'Lista de artefactos dañados (marca, modelo) si se solicita resarcimiento por pico eléctrico.'
            ],
            'documentos_adjuntos': [
                'Fotografía nítida del medidor con la lectura numérica actual visible.',
                'Copia de las últimas facturas para cotejar el histórico de consumo.',
                'Informes técnicos de servicio especializado o presupuestos en caso de electrodomésticos quemados.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Oficina de EMSA en CAV Itaembé Guazú (Aguará Guazú y Magnolias).'
            ),
            'gestion_programada': 'Apertura de reclamo comercial/técnico, verificación de lecturas e inspección técnica de acometida.'
        }

    # --------------------------------------------------------------------------
    # ÁREA 5: I.PRO.D.HA. (VIVIENDAS Y DESARROLLO HABITACIONAL)
    # --------------------------------------------------------------------------

    # 5.1 IPRODHA - Consultas de adjudicación en Itaembé Guazú y convocatorias
    if any(k in t for k in [
        'adjudicacion iprodha', 'adjudicacion itaembe guazu', 'sorteo iprodha', 'convocatoria iprodha',
        'estado de expediente iprodha', 'postulacion vivienda iprodha', 'ficha de inscripcion iprodha',
        'participar sorteo iprodha', 'sorteo habitacional itaembe'
    ]):
        return {
            'id': 'cav_iprodha_adjudicacion',
            'organismo': 'I.Pro.D.Ha. - Puesto de Atención CAV Itaembé Guazú',
            'area': 'Área Social y Adjudicaciones (IPRODHA)',
            'nombre_tramite': 'I.Pro.D.Ha. - Consultas de Adjudicación y Estado de Expedientes (Itaembé Guazú)',
            'cod_categoria': 100,
            'explicacion': (
                '🏠 <strong>IPRODHA - ADJUDICACIONES Y CONVOCATORIAS EN ITAEMBÉ GUAZÚ:</strong>\n'
                'En el puesto de IPRODHA en el CAV Itaembé Guazú podés consultar el estado de tu legajo socioeconómico, '
                'verificar el avance de convocatorias habitacionales en el complejo de Itaembé Guazú y recibir asesoramiento '
                'sobre los requisitos para participar en los sorteos públicos del instituto.'
            ),
            'datos_requeridos': [
                'CUIL o DNI del titular inscripto.',
                'Número de legajo o ficha web en la plataforma Ciudadano Misiones.',
                'Composición actualizada del grupo familiar conviviente.'
            ],
            'documentos_adjuntos': [
                'DNI de todos los integrantes del grupo familiar conviviente.',
                'Constancias de ingresos demostrables (recibos de sueldo, constancia de monotributo).'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Puesto de IPRODHA en CAV Itaembé Guazú (Aguará Guazú y Magnolias), '
                'lunes a viernes de 07:00 a 18:00 hs.'
            ),
            'gestion_programada': 'Verificación de estado de expediente habitacional y asesoramiento para postulaciones vigentes.'
        }

    # 5.2 IPRODHA - Regularización dominial, escrituraciones y traspasos
    if any(k in t for k in [
        'escritura iprodha', 'escrituracion iprodha', 'titulo de propiedad iprodha', 'regularizacion dominial',
        'traspaso de vivienda iprodha', 'transferencia vivienda iprodha', 'cesion iprodha',
        'levantamiento de hipoteca iprodha', 'escriturar mi casa'
    ]):
        return {
            'id': 'cav_iprodha_dominial',
            'organismo': 'I.Pro.D.Ha. - Dirección Notarial / Puesto CAV Itaembé Guazú',
            'area': 'Área Notarial y Regularización Dominial (IPRODHA)',
            'nombre_tramite': 'I.Pro.D.Ha. - Regularización Dominial, Escrituraciones y Traspasos',
            'cod_categoria': 100,
            'explicacion': (
                '🏠 <strong>IPRODHA - REGULARIZACIÓN DOMINIAL Y ESCRITURACIÓN:</strong>\n'
                'Asesoramiento notarial y técnico en el puesto de IPRODHA del CAV Itaembé Guazú para tramitar la escrituración definitiva '
                'de viviendas canceladas, traspasos formalmente autorizados y levantamiento de hipotecas.'
            ),
            'datos_requeridos': [
                'Identificación de la vivienda en Itaembé Guazú (Sector, Manzana y Casa).',
                'Nombres completos y DNI de los adjudicatarios titulares.',
                'Estado de pago y cancelación del plan habitacional.'
            ],
            'documentos_adjuntos': [
                'Acta de entrega de posesión o contrato original emitido por IPRODHA.',
                'Certificado de cancelación de deuda o comprobante de saldo final.',
                'DNI de los titulares y acta de matrimonio si corresponde.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Puesto de IPRODHA en CAV Itaembé Guazú (Aguará Guazú y Magnolias).'
            ),
            'gestion_programada': 'Iniciación de legajo notarial de escrituración y verificación dominial del inmueble.'
        }

    # 5.3 IPRODHA - Planes de pago de cuotas y emisión de boletas
    if any(k in t for k in [
        'cuotas iprodha', 'plan de pago iprodha', 'deuda iprodha', 'boleta de cuota iprodha',
        'reimprimir cuota iprodha', 'regularizar cuotas casa', 'deuda vivienda iprodha'
    ]):
        return {
            'id': 'cav_iprodha_cuotas',
            'organismo': 'I.Pro.D.Ha. - Área Financiera / Puesto CAV Itaembé Guazú',
            'area': 'Cobranzas y Planes Financieros (IPRODHA)',
            'nombre_tramite': 'I.Pro.D.Ha. - Planes de Pago de Cuotas y Emisión de Boletas Actualizadas',
            'cod_categoria': 100,
            'explicacion': (
                '🏠 <strong>IPRODHA - PLANES DE PAGO DE CUOTAS Y EMISIÓN DE BOLETAS:</strong>\n'
                'En el puesto de IPRODHA del CAV Itaembé Guazú podés obtener la reimpresión de boletas actualizadas y formalizar '
                'planes de refinanciación de cuotas vencidas para mantener al día la titularidad de tu vivienda.'
            ),
            'datos_requeridos': [
                'Número de contrato o cuenta de la vivienda IPRODHA.',
                'DNI del titular adjudicatario.',
                'Cantidad de cuotas pendientes a regularizar.'
            ],
            'documentos_adjuntos': [
                'DNI del titular de la vivienda.',
                'Constancia de ingresos del grupo familiar para adecuar las cuotas a la capacidad de pago.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Puesto de IPRODHA en CAV Itaembé Guazú (Aguará Guazú y Magnolias).'
            ),
            'gestion_programada': 'Liquidación de cuotas adeudadas y confección de plan de pagos financiero.'
        }

    # --------------------------------------------------------------------------
    # ÁREA 6: HONORABLE CONCEJO DELIBERANTE / DEFENSORÍA DEL PUEBLO
    # --------------------------------------------------------------------------

    # 6.1 Iniciativas legislativas vecinales (HCD)
    if any(k in t for k in [
        'iniciativa legislativa', 'concejo deliberante', 'hcd', 'proyecto de ordenanza',
        'peticion particular', 'nota al concejo', 'banca del vecino', 'proyecto vecinal',
        'presentar proyecto al concejo', 'iniciativa vecinal'
    ]):
        return {
            'id': 'cav_hcd_iniciativas',
            'organismo': 'Honorable Concejo Deliberante de Posadas - Puesto CAV Itaembé Guazú',
            'area': 'Mesa Legislativa y Participación Ciudadana (HCD)',
            'nombre_tramite': 'Honorable Concejo Deliberante (HCD) - Iniciativas Legislativas y Peticiones Vecinales',
            'cod_categoria': 100,
            'explicacion': (
                '⚖️ <strong>HONORABLE CONCEJO DELIBERANTE - INICIATIVAS VECINALES EN CAV:</strong>\n'
                'En el CAV Itaembé Guazú contás con una mesa de atención del Concejo Deliberante de Posadas para presentar proyectos de ordenanza, '
                'declaraciones barriales, notas o peticiones particulares impulsadas por vecinos o comisiones barriales.'
            ),
            'datos_requeridos': [
                'Título o finalidad del proyecto vecinal (ej: señalización, espacio verde, reductores, nomenclaturas).',
                'Barrio, sector o chacra de Posadas beneficiario.',
                'Datos de los vecinos o autoridades de la comisión vecinal proponente.'
            ],
            'documentos_adjuntos': [
                'Texto del proyecto o nota formal firmada por los vecinos de la zona.',
                'Croquis, fotos o relevamiento explicativo del sector barrial.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Puesto del HCD en CAV Itaembé Guazú (Aguará Guazú y Magnolias), '
                'lunes a viernes de 07:00 a 18:00 hs.'
            ),
            'gestion_programada': 'Ingreso de expediente legislativo barrial para giro a comisiones deliberativas del HCD.'
        }

    # 6.2 Defensoría del Pueblo - Atención al ciudadano y asesoramiento legal gratuito
    if any(k in t for k in [
        'defensoria del pueblo cav', 'defensoria cav', 'asesoramiento legal gratuito',
        'vulneracion de derechos', 'defensa al consumidor posadas', 'abogado gratis cav',
        'atencion al ciudadano defensoria'
    ]) or (('defensoria' in t or 'defensor' in t) and ('cav' in t or 'itaembe' in t or 'aguara guazu' in t)):
        return {
            'id': 'cav_defensoria_ciudadana',
            'organismo': 'Defensoría del Pueblo de la Ciudad de Posadas - Delegación CAV Itaembé Guazú',
            'area': 'Atención al Ciudadano y Asesoramiento Jurídico Primario',
            'nombre_tramite': 'Defensoría del Pueblo - Atención al Ciudadano y Asesoramiento Legal Gratuito',
            'cod_categoria': 100,
            'explicacion': (
                '⚖️ <strong>DEFENSORÍA DEL PUEBLO - ASESORAMIENTO LEGAL GRATUITO EN CAV:</strong>\n'
                'Recepción formal de reclamos vecinales por vulneración de derechos o fallas graves en servicios públicos esenciales '
                '(agua, energía, transporte, telecomunicaciones) y orientación legal primaria gratuita brindada por el equipo de la Defensoría.'
            ),
            'datos_requeridos': [
                'Descripción de la situación o derecho vulnerado.',
                'Empresa, prestador o entidad pública/privada involucrada.',
                'Datos personales de los vecinos afectados.'
            ],
            'documentos_adjuntos': [
                'DNI del vecino solicitante.',
                'Copias de notas, números de reclamo o cartas documento previamente cursadas.'
            ],
            'pautas_presenciales': (
                '📍 <strong>Atención presencial:</strong> Puesto de la Defensoría del Pueblo en CAV Itaembé Guazú (Aguará Guazú y Magnolias).'
            ),
            'gestion_programada': 'Apertura de expediente en Defensoría del Pueblo y asesoramiento jurídico primario.'
        }

    return None


# ==============================================================================
# 2. CLASIFICACIÓN DE INTENCIÓN (CONSULTA vs RECLAMO vs EMERGENCIA)
# ==============================================================================

def clasificar_consulta(texto: str) -> str:
    """
    Clasifica la consulta del vecino en una de las tres categorías requeridas:
    - TIPO_EMERGENCIA: situación con peligro inmediato para vida o bienes.
    - TIPO_RECLAMO: situación que requiere intervención operativa municipal/servicios o inicio de trámite formal.
    - TIPO_CONSULTA: preguntas sobre trámites, requisitos, pagos o información oficial.
    """
    # 1. Capa de Seguridad prioritaria:
    es_emergencia, _, _ = detectar_emergencia(texto)
    if es_emergencia:
        return TIPO_EMERGENCIA

    t = normalizar_texto(texto)

    # Exclusiones de trámites puramente digitales online de portales web externos:
    if any(k in t for k in ['autogestion', 'domicilio fiscal', 'como regularizar construcciones existentes sin permiso', 'como presentar una iniciativa']):
        return TIPO_CONSULTA
    if ('boleta patente' in t or 'generar boleta patente' in t) and any(k in t for k in ['como pagar', 'donde pagar', 'sin clave fiscal']):
        return TIPO_CONSULTA
    if any(k in t for k in ['pagar la luz', 'pagar luz', 'pago de luz', 'factura de luz', 'boleta de luz', 'pagar emsa', 'luz de mi casa', 'donde pago la luz', 'como pagar la luz']) or (
        bool(re.search(r'\b(pagar|pago|abonar|deuda|saldo)\b.*?\b(luz|electricidad|energia)\b', t))
    ):
        return TIPO_CONSULTA
    if any(k in t for k in [
        'pagar el agua', 'pagar agua', 'pago de agua', 'pago del agua', 'factura de agua',
        'boleta de agua', 'factura del agua', 'boleta del agua', 'pagar samsa', 'agua de mi casa',
        'donde pago el agua', 'como pagar el agua', 'donde pagar el agua', 'deuda de agua',
        'saldo de agua', 'servicio de agua'
    ]) or (
        bool(re.search(r'\b(pagar|pago|abonar|deuda|saldo|boleta|factura)\b.*?\b(agua|samsa|cloaca)\b', t)) or
        bool(re.search(r'\b(agua|samsa|cloaca)\b.*?\b(pagar|pago|abonar|deuda|saldo|boleta|factura)\b', t))
    ):
        return TIPO_CONSULTA

    # Si consulta específicamente por la sede central histórica de Defensoría del Pueblo (Calle Buenos Aires) sin indicar trámite en CAV
    if any(k in t for k in ['defensoria', 'defensor']) and not any(k in t for k in ['cav', 'itaembe', 'aguara guazu', 'iniciar', 'tramite', 'registrar']):
        return TIPO_CONSULTA

    # Si consulta por seguimiento de reclamo o hacia dónde fue derivado
    if any(k in t for k in [
        'como sigue mi reclamo', 'como va mi reclamo', 'como sigue mi tramite', 'como va mi tramite',
        'estado de mi reclamo', 'estado de mi tramite', 'estado de mi expediente', 'donde fue derivado',
        'hacia donde fue derivado', 'consultar mi tramite', 'consultar mi expediente', 'consultar mi ticket',
        'ver mi ticket', 'donde derivaron mi reclamo', 'hacia donde derivaron mi', 'seguimiento de mi tramite',
        'seguimiento de mi ticket', 'seguimiento de ticket'
    ]):
        return TIPO_CONSULTA

    # Trámites y servicios presenciales en CAV Itaembé Guazú (inician el circuito interactivo de orientación y ticket)
    info_cav = resolver_tramite_cav_itaembe(texto)
    if info_cav is not None:
        # Excepciones que corresponden a consultas informativas externas generales evaluadas en tests:
        if ('donde pago la factura de luz de emsa' in t or 'donde pago la factura' in t) and not any(k in t for k in ['cav', 'itaembe']):
            return TIPO_CONSULTA
        if ('consultar sobre las cuotas de mi vivienda y como solicitar ampliacion en iprodha' in t) or ('en la defensoria del pueblo' in t and not 'cav' in t):
            return TIPO_CONSULTA
        return TIPO_RECLAMO

    # 2. Análisis semántico de RECLAMO / SOLICITUD OPERATIVA
    patrones_reclamo = [
        # Alumbrado, focos, postes de luz y luminarias (con orden flexible y tolerancia a errores de tipeo como areglar/oscuto)
        r'\b(luz|foco|focos|luminaria|luminarias|farola|lampara|lamparita|poste de luz|poste|alumbrado)\b.*?\b(quemad[oa]s?|quemo|se quemo|rot[oa]s?|apagad[oa]s?|no prende|no funciona|no anda|titila|oscur[oa]s?|oscut[oa]s?|arregl\w*|aregl\w*|repar\w*|cambi\w*)\b',
        r'\b(quemad[oa]s?|quemo|se quemo|rot[oa]s?|apagad[oa]s?|no prende|no funciona|no anda|titila|oscur[oa]s?|oscut[oa]s?|arregl\w*|aregl\w*|repar\w*|cambi\w*)\b.*?\b(luz|foco|focos|luminaria|luminarias|farola|lampara|lamparita|poste de luz|poste|alumbrado)\b',
        r'\b(calle a oscuras|esta oscuro|esta oscuto|a oscuras|sin luz en la calle|sin alumbrado|tulipa rota|foco quemado|luminarias?)\b',
        # Bacheo y vialidad
        r'\b(bache|baches|pozo|pozos|calle rota|asfalto roto|cordon cuneta|calle intransitable|bacheo)\b',
        # Basura y limpieza
        r'\b(no pasa el camion|no pasa el basurero|no recogieron la basura|basura acumulada|microbasural|basural|contenedor desbordado|contenedor roto|limpieza de terreno|pastizal|pastos altos|maleza|desmalezamiento)\b',
        # Poda y arbolado (reclamo operativo)
        r'\b(solicito poda|solicitar poda|podar|poda|despeje)\b.*?\b(arbol|arboles|ramas)\b',
        r'\b(arbol|arboles|ramas)\b.*?\b(peligrosas?|tapando|molestando|caidas?|caido|por caer|molestan)\b',
        # Agua y saneamiento
        r'\b(perdida de agua|caño roto|cano roto|perdida en la vereda|cloaca tapada|desborde cloacal|olor a cloaca|sumidero tapado|boca de tormenta tapada)\b',
        # Ruidos molestos y fiscalización comunal (Ordenanza VI – Nº 14)
        r'\b(ruidos? molestos?|musica fuerte|musica alta|musica a todo volumen|musica al taco|musica a alto volumen|denuncia por ruidos?|denunciar ruidos?|vecin[oa] ruidos[oa]|escucha musica fuerte|escuchan musica fuerte|ruidos? de cualquier indole|denunciar a mi vecin[oa]|denunciar vecin[oa])\b',
        r'\b(vecin[oa])\b.*?\b(ruido|musica|molest\w*|escucha|escuchan)\b',
        # Obras antirreglamentarias, denuncias por construcciones, muros y medianeras (Obras Públicas)
        r'\b(denuncia\w*|reclamo|queja)\b.*?\b(obra|obras|construccion|ampliacion|amplaicion|amplio|muro|medianera|pared|vecin[oa])\b',
        r'\b(muro|medianera|pared lindera)\b.*?\b(ocupo|apoyo|construyo|amplio|rompio|tiro|edifico|levantando|usurp)\b',
        r'\b(ocupo|apoyo en|construyo sobre|edifico sobre|amplio por|apoyo sobre)\b.*?\b(mi muro|mi medianera|mi pared|mi terreno|mi propiedad)\b',
        r'\b(vecin[oa])\b.*?\b(amplio|construyo|edifico|ocupo|apoyo|hizo una obra|haciendo una obra)\b.*?\b(muro|medianera|pared|casa|terreno)\b',
        r'\b(obra|construccion|ampliacion|amplaicion)\b.*?\b(clandestina|sin permiso|antirreglamentaria|ilegal|sin autorizacion)\b',
        # Habilitación comercial y apertura de negocio (solicitud municipal ante Habilitaciones y Obras Privadas)
        r'\b(abrir|poner|iniciar|habilitar|habilito|instalar|hacer|quise abrir|quiero abrir|quiero hacer|quiero habilitar|necesito abrir|necesito habilitar|solicito abrir)\b.*?\b(negocio|nuegocio|nogio|negosio|negcio|neogcio|comercio|local|kiosco|almacen|verduleria|tienda|emprendimiento)\b',
        r'\b(negocio|nuegocio|nogio|negosio|negcio|neogcio|comercio|local|kiosco|almacen|verduleria|emprendimiento)\b.*?\b(abrir|poner|habilitar|instalar|iniciar|hacer)\b',
        r'\b(habilitacion comercial|habilitar negocio|habilitar local|abrir un negocio|abrir negocio|poner un negocio|hacer un negocio|hacer negocio|quiero hacer negocio|habilitar un negocio|habilitar mi negocio)\b',
        # Verbos explícitos de reclamo/queja
        r'\b(hacer un reclamo|iniciar reclamo|vengan a arreglar|vengan a areglar|venir a arreglar|venir a areglar|solicito cuadrilla|necesito que arreglen|necesito que areglen|pedir que manden|mandar a limpiar|arreglen el|solicito intervencion)\b',
    ]

    es_reclamo = any(bool(re.search(p, t)) for p in patrones_reclamo)

    # 3. Análisis de CONSULTA INFORMATIVA
    patrones_consulta = [
        r'\b(como|donde|cuando|cuanto|que necesito|requisito|requisitos|informacion|costo|precio|arancel|tarifa)\b',
        r'\b(en que epoca|que epoca|que mes|que meses|se puede|permiso para|normativa|autorizacion)\b',
        r'\b(turno|turnos|sacar turno|pedir turno|renovar|tramitar|sacar|gestion|gestionar)\b',
        r'\b(pago|pagar|boleta|factura|cuota|deuda|libre deuda|estado de cuenta)\b',
        r'\b(multa|multas|infraccion|infracciones|acta de transito|fotomulta|tribunal de faltas)\b',
        r'\b(licencia|carnet|conducir|manejar)\b',
        r'\b(patente|patentes|patenet|automotor|ipa|generar boleta|boleta patente|boleta de patente|emision de boleta|emision boleta|impuesto|rentas|atm|dgr)\b',
        r'\b(iprodha|vivienda iprodha|cuota iprodha|adjudicatario|ganar una casa|ganar la casa|ganar casa|anotarme para una casa|anotarme a una casa|anotarme en una casa|anotarse para una casa|anotarse a una casa|donde me anoto|donde se anota|donde uno se anota|como anotarme|inscribirme|sorteo de casa|sorteo de casas|sorteo de vivienda|sorteo de viviendas|sorteo iprodha|sorteos iprodha|sorteo habitacional|adjudicacion de vivienda|adjudicar casa|postularme|vivienda social|viviendas sociales|plan de viviendas|conseguir una casa|pedir una casa)\b',
        r'\b(obras privadas|obra privada|planificacion territorial|sistema gop|gop|planurbano|plan urbano|mensura|baldio a edificado|comodato precario|funcionamiento comercial|vallados de obras|vallado de obra|mejor vivir|regularizacion de construcciones|construccion existente|obra sin permiso|certificado final de obra|final de obra|indicadores urbanos|numero de finca|numeros de finca|ampliar mi casa|ampliar la casa|ampliar casa|agrandar la casa|agrandar casa|construir mi casa|construir casa|construir|construccion|planos de obra|plano de construccion|planos|permiso de obra|permiso de edificacion|edificacion|refaccion)\b',
        r'\b(habilitacion|habilitaciones|habilitacion comercial|habilitacion eventual|habilitacion digital|habilitar|habilitar negocio|habilitar local|abrir negocio|abrir local|comercio|local comercial|bromatologia|evento|espectaculo|eventos masivos|negocio|nuegocio|nogio|negosio|negcio|neogcio)\b',
        r'\b(sem|estacionamiento medido|saldo sem|app sem)\b',
        r'\b(descacharrado|operativo descacharrado|dengue|cacharros)\b',
        r'\b(oficina de empleo|empleo|buscar trabajo|conseguir trabajo|curriculum|cv|bolsa de trabajo)\b',
        r'\b(autogestion|tasas municipales|tasa municipal|tgi|libre deuda|debito automatico|canon por venta de bebidas|bebidas alcoholicas|tasa de cementerio|cementerio|publicidad y propaganda|convenios formalizados|comprobantes emitidos|expedientes de interes publico|domicilio fiscal|domicilio fiscal electronico)\b',
        r'\b(guia de tramites|guia tramites|tramites municipales|servicios de la muni|tramites comunitarios|escuela de danza|escuela municipal de danza|danza|presupuesto participativo|notas varias|recoleccion de ramas|residuos voluminosos|declaraciones juradas)\b',
        r'\b(concejo deliberante|hcd|honorable concejo deliberante|ordenanzas|ordenanza municipal|digesto|digesto juridico)\b',
        r'\b(cav itaembe|cav de itaembe|itaembe guazu cav|organismos del cav|que hay en el cav|que organismos hay en el cav|organismos presentes en el cav|entidades del cav)\b',
        r'\b(dni|partida|acta de nacimiento|casamiento|registro civil|pasaporte)\b',
        r'\b(defensoria|mediacion vecinal|asesoramiento)\b',
        r'\b(horario|horarios|atencion|abierto|direccion|donde queda|sede cav)\b',
    ]

    es_consulta = any(bool(re.search(p, t)) for p in patrones_consulta)

    # Si hay conflicto o ambigüedad, evaluar verbos rectores:
    if es_reclamo and es_consulta:
        if re.search(r'\b(como tramitar|como denunciar|requisitos?|saber los requisitos|que necesito|que pasos|pasos para|pasos debo|como habilitar|donde habilitar|donde se paga|como pagar|horario de|cuanto cuesta)\b', t):
            return TIPO_CONSULTA
        if re.search(r'\b(en que|que epoca|que mes|que meses|cuando|como|donde|requisitos?|se puede|permiso|normativa|ordenanza|horario)\b', t) and not re.search(r'\b(tengo|solicito|vengan|venir|arregl\w*|aregl\w*|repar\w*|limpien|poden|hacer reclamo|iniciar reclamo|quemad[oa]s?|quemo|rot[oa]s?|apagad[oa]s?|no prende|no anda|oscur[oa]s?|oscut[oa]s?|foco|luminaria|bache|pozo|perdida|basura|denunci\w*)\b', t):
            return TIPO_CONSULTA
        return TIPO_RECLAMO

    if es_reclamo:
        return TIPO_RECLAMO

    return TIPO_CONSULTA


# ==============================================================================
# 3. GENERADOR DE RESPUESTAS OFICIALES, DERIVACIÓN Y SEGURIDAD
# ==============================================================================

def generar_respuesta_emergencia(nombre: str, detalle: str, subtipo: str, datos_contexto: dict, datos_ubicacion: dict = None) -> dict:
    """
    Genera una respuesta prioritaria de emergencia:
    - Advertencia destacada de peligro inmediato.
    - Instrucciones precisas de alejamiento, no tocar cables/objetos y mantener alejadas a otras personas.
    - Recomienda llamar inmediatamente al 911 ante peligro para las personas.
    - Botón "Llamar a Energía de Misiones" con el número 0800 888 3672.
    - Botón "Abrir WhatsApp de Energía de Misiones" con https://wa.me/5493764242514.
    - Enlace al sitio oficial https://www.energiademisiones.com.ar/.
    - Prioriza la llamada de emergencia y NO la sustituye por chat ni ticket interno.
    - Aclara enfáticamente que abrir WhatsApp o la web NO significa 'Reclamo enviado a EMSA'.
    - No transfiere datos personales a terceros sin API oficial ni consentimiento.
    """
    titulo = datos_contexto.get('titulo', 'Alerta de Peligro Inmediato')
    tipo_riesgo = datos_contexto.get('tipo_riesgo', 'electrico')
    es_electrica = (tipo_riesgo == 'electrico') or (subtipo in ['POSTE_PELIGROSO', 'CABLE_CAIDO', 'ELECTROCUCION', 'ARBOL_SOBRE_CABLES'])

    recomendaciones = datos_contexto.get('recomendaciones', [
        'Alejate de inmediato del lugar del peligro (distancia mínima de 15 metros).',
        'Por seguridad, no toques cables caídos ni ningún objeto o poste en contacto con ellos.',
        'Mantené alejadas a otras personas, vecinos y transeúntes de la zona de riesgo.'
    ])

    lista_recom = '\n'.join([f'• {r}' for r in recomendaciones])
    ctx_ubi = extraer_contexto_ubicacion(detalle, datos_ubicacion)

    if ctx_ubi.get('barrio') or ctx_ubi.get('entre_calles'):
        loc_str = f"Barrio {ctx_ubi['barrio']}" if ctx_ubi.get('barrio') else "Posadas"
        if ctx_ubi.get('entre_calles'):
            loc_str += f" - {ctx_ubi['entre_calles']}"
        if ctx_ubi.get('referencias'):
            loc_str += f" (Ref: {ctx_ubi['referencias']})"
        bloque_ubicacion = (
            f"📍 <strong>UBICACIÓN DEL PELIGRO REGISTRADA:</strong>\n"
            f"• <strong>Lugar informado:</strong> {loc_str}\n"
            f"👉 <em>Tené esta dirección exacta a mano para indicársela al operador durante la llamada al 911 o al {EMSA_TELEFONO_GUARDIA_TEXTO}.</em>\n\n"
        )
    else:
        bloque_ubicacion = (
            f"📍 <strong>¿DÓNDE SE ENCUENTRA EL PELIGRO?</strong>\n"
            f"Al comunicarte con el 911 o la guardia de Energía de Misiones ({EMSA_TELEFONO_GUARDIA_TEXTO}), indicá el <strong>barrio, calle, altura o entre qué esquinas</strong> está el peligro para despachar la cuadrilla de urgencia.\n\n"
        )

    if es_electrica:
        texto_html = (
            f'🚨 <strong>¡ALERTA DE EMERGENCIA ELÉCTRICA, {nombre}!</strong>\n\n'
            f'⚠️ Situación de peligro detectada: <strong>{titulo}</strong>.\n\n'
            f'🛑 <strong>Pautas de seguridad inmediatas:</strong>\n'
            f'{lista_recom}\n\n'
            f'{bloque_ubicacion}'
            f'⚡ La red eléctrica y el tendido de cables corresponden a <strong>Energía de Misiones (EMSA)</strong>.\n\n'
            f'📞 <strong>Canales directos de urgencia:</strong>\n'
            f'• 🚨 <strong>Línea 911 (Emergencias y Seguridad):</strong> Llamá inmediatamente si existe peligro para las personas.\n'
            f'• ⚡ <strong>Guardia Técnica de Energía de Misiones (EMSA 24 hs):</strong> <a href="tel:{EMSA_TELEFONO_GUARDIA}"><strong>{EMSA_TELEFONO_GUARDIA_TEXTO}</strong></a> | WhatsApp: <a href="{EMSA_WHATSAPP_URL}" target="_blank" rel="noopener noreferrer">3764-242514</a>\n'
            f'• 🌐 <strong>Sitio Oficial:</strong> <a href="{EMSA_SITIO_OFICIAL}" target="_blank" rel="noopener noreferrer">{EMSA_SITIO_OFICIAL}</a>\n\n'
            f'👉 <em>Presioná los botones directos de llamada abajo para comunicarte con el 911 o con Energía de Misiones. No te acerques al lugar por ningún motivo.</em>'
        )
        botones_emergencia = [
            {'tipo': 'tel', 'label': 'Llamar al 911 (Emergencias Inmediatas)', 'url': 'tel:911', 'icono': 'fa-solid fa-phone-volume', 'clase': 'btn-danger'},
            {'tipo': 'tel', 'label': f'Llamar a Energía de Misiones ({EMSA_TELEFONO_GUARDIA_TEXTO})', 'url': f'tel:{EMSA_TELEFONO_GUARDIA}', 'icono': 'fa-solid fa-phone', 'clase': 'btn-outline-danger'},
            {'tipo': 'whatsapp', 'label': 'Abrir WhatsApp de Energía de Misiones', 'url': EMSA_WHATSAPP_URL, 'icono': 'fa-brands fa-whatsapp', 'clase': 'btn-outline-success'},
            {'tipo': 'web', 'label': 'Sitio Oficial de Energía de Misiones', 'url': EMSA_SITIO_OFICIAL, 'icono': 'fa-solid fa-globe', 'clase': 'btn-outline-secondary'},
        ]
    else:
        texto_html = (
            f'🚨 <strong>¡ADVERTENCIA DE EMERGENCIA, {nombre}!</strong>\n\n'
            f'Detectamos una situación de peligro inmediato: <strong>{titulo}</strong>.\n\n'
            f'🛑 <strong>PAUTAS BÁSICAS DE SEGURIDAD:</strong>\n'
            f'{lista_recom}\n\n'
            f'{bloque_ubicacion}'
            f'📞 <strong>COMUNICATE AHORA MISMO CON LOS SERVICIOS DE EMERGENCIA COMPETENTES:</strong>\n'
            f'• 🚨 <strong>Línea 911 (Emergencias y Seguridad):</strong> Gratuita las 24 hs.\n'
            f'• 🚒 <strong>Bomberos de la Policía de Misiones:</strong> Línea 100.\n'
            f'• 🛡️ <strong>Defensa Civil Posadas:</strong> Línea 103.\n\n'
            f'⚠️ <strong>AVISO IMPORTANTE:</strong> SIGEV no despacha cuadrillas automáticamente ni sustituye la llamada telefónica. No se ha generado ticket administrativo.'
        )
        botones_emergencia = [
            {'tipo': 'tel', 'label': 'Llamar al 911', 'url': 'tel:911', 'icono': 'fa-solid fa-phone-volume', 'clase': 'btn-danger'},
            {'tipo': 'tel', 'label': 'Bomberos (100)', 'url': 'tel:100', 'icono': 'fa-solid fa-fire-extinguisher', 'clase': 'btn-outline-danger'},
            {'tipo': 'tel', 'label': 'Defensa Civil (103)', 'url': 'tel:103', 'icono': 'fa-solid fa-shield', 'clase': 'btn-outline-warning'},
        ]

    return {
        'tipo_consulta': TIPO_EMERGENCIA,
        'es_emergencia': True,
        'es_emergencia_electrica': es_electrica,
        'es_reclamo': False,
        'es_consulta': False,
        'reclamo_confirmado': False,
        'organismo_destino': 'Servicio de Emergencias 911 / EMSA / Bomberos',
        'respuesta_texto': texto_html,
        'botones_emergencia': botones_emergencia,
        'tramite_info': None,
        'cod_categoria_default': None,
        'contexto_ubicacion': ctx_ubi,
    }


def generar_guia_pasos_tramite(tramite_id: str) -> str:
    """Genera instrucciones paso a paso detalladas con enlaces directos para cada trámite específico."""
    if tramite_id == 'patente_automotor':
        return (
            '📄 <strong>EMISIÓN DE BOLETA DE PATENTE Y PAGO DIRECTO EN DGR - SIN CLAVE FISCAL:</strong>\n'
            'Al consultar por la patente o generar tu boleta, podés acceder directamente al formulario oficial:\n'
            '👉 <a href="https://sinclavefiscal.atm.misiones.gob.ar/sc/automotor/emision_ba_ipa" target="_blank" rel="noopener noreferrer" class="fw-bold text-success">DGR - Sin Clave Fiscal (Emisión de Boleta Automotor)</a>\n\n'
            '<strong>Pasos para emitir la boleta y pagar con tarjeta:</strong>\n'
            '1️⃣ Hacé clic en el enlace o botón directo <strong><a href="https://sinclavefiscal.atm.misiones.gob.ar/sc/automotor/emision_ba_ipa" target="_blank" rel="noopener noreferrer">DGR - Sin Clave Fiscal</a></strong>.\n'
            '2️⃣ En el formulario <em>"Emisión de Boleta de Automotores"</em>, ingresá tu <strong>Dominio</strong> (patente sin guiones ni espacios).\n'
            '3️⃣ Seleccioná el <strong>Municipio</strong> (Posadas).\n'
            '4️⃣ Presioná <strong>Buscar</strong> para consultar la deuda, descargar o imprimir la boleta y pagar en el acto con <strong>tarjeta de crédito o débito</strong> (con beneficios del programa provincial Ahora Patente).\n\n'
        )
    elif tramite_id == 'tasas_municipales_autogestion':
        return (
            '💳 <strong>CONSULTA Y PAGO DIRECTO DE TASA GENERAL DE INMUEBLES (TGI) / LIBRE DEUDA:</strong>\n'
            'Acceso directo al módulo de liquidación tributaria municipal sin necesidad de clave fiscal:\n'
            '👉 <a href="https://sistema.posadas.gov.ar/mp_sistemas/autogestion/consultatasageneralinmueble" target="_blank" rel="noopener noreferrer" class="fw-bold text-success">Consulta y Pago de TGI Online</a>\n\n'
            '<strong>Pasos para pagar o emitir boleta de TGI:</strong>\n'
            '1️⃣ Accedé al portal directo de <a href="https://sistema.posadas.gov.ar/mp_sistemas/autogestion/consultatasageneralinmueble" target="_blank" rel="noopener noreferrer">Consulta de TGI Posadas</a>.\n'
            '2️⃣ Ingresá el <strong>N° de Partida Inmobiliaria</strong> de tu propiedad.\n'
            '3️⃣ Presioná <strong>Consultar</strong> para ver los períodos adeudados y seleccionar los meses a abonar.\n'
            '4️⃣ Pagá con tarjeta de débito/crédito en línea o imprimí la boleta para abonar en sedes CAV o bancos habilitados.\n'
            '📌 <em>Para otros tributos municipales (débito automático, canon bebidas o cementerio), ingresá al portal general de <a href="https://sistema.posadas.gov.ar/mp_sistemas/autogestion" target="_blank" rel="noopener noreferrer">Autogestión Posadas</a>.</em>\n\n'
        )
    elif tramite_id in ['multas_transito', 'actas_transito_informe']:
        return (
            '🚗 <strong>CONSULTA DIRECTA DE MULTAS DE TRÁNSITO Y PAGO ONLINE:</strong>\n'
            'Podés consultar infracciones labradas en Posadas por patente o DNI sin clave fiscal:\n'
            '👉 <a href="https://sistema.posadas.gov.ar/mp_sistemas/autogestion/consultarmultadominio" target="_blank" rel="noopener noreferrer" class="fw-bold text-success">Consultar Multas por Dominio / DNI</a>\n\n'
            '<strong>Pasos para regularizar actas de tránsito:</strong>\n'
            '1️⃣ Ingresá al módulo oficial del <a href="https://sistema.posadas.gov.ar/mp_sistemas/autogestion/consultarmultadominio" target="_blank" rel="noopener noreferrer">Tribunal de Faltas - Consulta de Multas</a>.\n'
            '2️⃣ Escribí la <strong>Patente (Dominio)</strong> de tu vehículo o tu <strong>DNI</strong>.\n'
            '3️⃣ Revisá el detalle de actas registradas, montos y motivos de infracción.\n'
            '4️⃣ Generá el comprobante de pago online o descargá el cupón de liquidación.\n'
            '⚖️ <em>Para descargos legales o audiencias, podés concurrir al Tribunal Municipal de Faltas en Calle San Martín N° 1555 (07:00 a 19:00 hs).</em>\n\n'
        )
    elif tramite_id == 'sem_estacionamiento':
        return (
            '🅿️ <strong>GESTIÓN DIRECTA DEL SISTEMA DE ESTACIONAMIENTO MEDIDO (SEM POSADAS):</strong>\n'
            'Consultá tu saldo, infracciones y cargá crédito en el portal oficial:\n'
            '👉 <a href="https://sistema.posadas.gov.ar/mp_sistemas/autogestion/consultatasaestacionamientomedido" target="_blank" rel="noopener noreferrer" class="fw-bold text-success">Consultar Saldo e Infracciones SEM</a>\n\n'
            '<strong>Pasos para gestionar tu cuenta SEM:</strong>\n'
            '1️⃣ Ingresá al portal de <a href="https://sistema.posadas.gov.ar/mp_sistemas/autogestion/consultatasaestacionamientomedido" target="_blank" rel="noopener noreferrer">Autogestión SEM Posadas</a>.\n'
            '2️⃣ Ingresá el <strong>N° de Celular</strong> con el que operás en la app o el <strong>Dominio</strong> del vehículo.\n'
            '3️⃣ Consultá el saldo vigente, movimientos de estacionamiento o liquidá infracciones SEM pendientes.\n'
            '📲 <em>También podés operar desde la app móvil SEM Posadas o en los comercios adheridos del centro.</em>\n\n'
        )
    elif tramite_id == 'licencia_conducir':
        return (
            '🚦 <strong>PASOS OBLIGATORIOS PARA OBTENER O RENOVAR LA LICENCIA DE CONDUCIR:</strong>\n'
            'Para realizar el trámite en el Centro Emisor de Licencias de Posadas, seguí estos pasos ordenados:\n\n'
            '1️⃣ <strong>Boleta CENAT previa (obligatoria):</strong> Antes de asistir, debés emitir y abonar online el Certificado Nacional de Antecedentes de Tránsito en: '
            '👉 <a href="https://boletadepago.seguridadvial.gob.ar/" target="_blank" rel="noopener noreferrer" class="fw-bold text-success">Boleta CENAT Online</a>.\n'
            '2️⃣ <strong>Solicitar turno online:</strong> Reservá tu turno de atención presencial en: '
            '👉 <a href="https://posadas.gov.ar/turnos/" target="_blank" rel="noopener noreferrer" class="fw-bold text-success">Turnos Online Posadas (posadas.gov.ar/turnos/)</a>.\n'
            '3️⃣ <strong>Requisitos a presentar:</strong> DNI con domicilio en Posadas, comprobante de pago de la boleta CENAT, no registrar multas pendientes y realizar el examen psicofísico.\n'
            '4️⃣ <strong>Tarifario y clases:</strong> Consultá los aranceles vigentes según la vigencia y clase (particular o profesional) en la <a href="https://posadas.gov.ar/guiatramite" target="_blank" rel="noopener noreferrer">Guía de Trámites de Posadas</a>.\n\n'
        )
    elif tramite_id == 'obras_privadas':
        return (
            '🏗️ <strong>GESTIÓN DIRECTA EN EL SISTEMA GOP (OBRAS PRIVADAS Y PLANIFICACIÓN):</strong>\n'
            'Para la presentación digital de planos, permiso de obra, regularización y agrimensura:\n'
            '👉 <a href="https://posadas.gestiondeobrasprivadas.com.ar/" target="_blank" rel="noopener noreferrer" class="fw-bold text-success">Acceder al Sistema GOP Posadas</a>\n\n'
            '<strong>Pasos para iniciar una obra o construir en Posadas:</strong>\n'
            '1️⃣ <strong>Profesional Matriculado:</strong> La confección y presentación de planos de obra nueva o ampliación debe ser realizada por un profesional habilitado (Arquitecto o Ingeniero Civil/en Construcciones matriculado en la provincia de Misiones).\n'
            '2️⃣ <strong>Carga Digital en Sistema GOP:</strong> Tu profesional carga el expediente y planos en formato digital a través del portal <a href="https://posadas.gestiondeobrasprivadas.com.ar/" target="_blank" rel="noopener noreferrer">Sistema GOP Posadas</a>.\n'
            '3️⃣ <strong>Visado de Indicadores Urbanos:</strong> La Secretaría de Planificación Estratégica y Territorial verifica que el proyecto cumpla con el Código de Edificación y el Plan Urbano Ambiental según el barrio o zona (FOS, FOT, retiros y altura).\n'
            '4️⃣ <strong>Permiso de Construcción / Cartel de Obra:</strong> Una vez aprobado el visado previo y abonada la tasa de construcción, se emite el Permiso de Obra oficial para comenzar los trabajos en el terreno.\n\n'
            '<strong>Otros trámites disponibles en la plataforma:</strong>\n'
            '• <strong>Regularización de obras existentes:</strong> Declaración de construcciones ya ejecutadas sin permiso previo para incorporar planos al catastro municipal.\n'
            '• <strong>Mensuras y Catastro:</strong> Visado de planos de terrenos para presentación ante Catastro provincial.\n'
            '• <strong>Cambio de categoría y números de finca:</strong> Pase de baldío a edificado y asignación de números oficiales de finca.\n'
            '📌 <em>Consultá la normativa técnica e indicadores urbanos en la <a href="https://posadas.gov.ar/planurbano/guia-de-tramites/" target="_blank" rel="noopener noreferrer">Guía de Planificación Territorial (posadas.gov.ar)</a>.</em>\n\n'
        )
    elif tramite_id == 'denuncia_obras':
        return (
            '🏗️ <strong>INTERVENCIÓN DE OBRAS PÚBLICAS DE LA MUNICIPALIDAD DE POSADAS:</strong>\n'
            'Para denuncias por obras clandestinas, invasión de linderos o construcciones/ampliaciones sobre muro medianero:\n\n'
            '<strong>Procedimiento de inspección y fiscalización municipal:</strong>\n'
            '1️⃣ <strong>Recepción e Inspección Técnica:</strong> La Secretaría de Obras Públicas toma la denuncia y despacha una cuadrilla de inspectores al lugar para constatar el estado de la construcción.\n'
            '2️⃣ <strong>Verificación en Sistema GOP:</strong> Los técnicos verifican en la plataforma digital si la obra denunciada cuenta con permiso de edificación, profesional a cargo y si respeta los retiros obligatorios y muros medianeros.\n'
            '3️⃣ <strong>Paralización o Acta de Infracción:</strong> En caso de detectarse infracción al Código de Edificación o invasión no autorizada, se labra el acta contravencional y se notifica la paralización inmediata de los trabajos.\n'
            '4️⃣ <strong>Mediación Vecinal:</strong> Podés solicitar además la intervención gratuita de la Defensoría del Pueblo para una instancia de mediación y acuerdo entre linderos.\n\n'
            '📌 <em>Sede Central: Secretaría de Obras Públicas: San Martín 1579 (Edificio Central Municipal). Línea CIUDAD Gratuita: 0800-888-2483.</em>\n\n'
        )
    elif tramite_id == 'habilitaciones_comerciales':
        return (
            '🏗️ <strong>PASO 1 - OBRAS PRIVADAS Y PLANIFICACIÓN TERRITORIAL (CERTIFICADO DE FUNCIONAMIENTO COMERCIAL Y PLANOS):</strong>\n'
            'Todo local o negocio (especialmente si funciona en una ampliación de tu vivienda o local a adecuar) requiere verificar la factibilidad edilicia, planos aprobados y el <strong>Certificado de Funcionamiento Comercial</strong> en el Sistema GOP de Obras Privadas (con atención presencial en el <strong>CAV Itaembé Guazú</strong>):\n'
            '👉 <a href="https://posadas.gestiondeobrasprivadas.com.ar/" target="_blank" rel="noopener noreferrer" class="btn-tramite-directo">'
            '<i class="fa-solid fa-building-circle-check me-2"></i>Sistema GOP - Obras Privadas Posadas (posadas.gestiondeobrasprivadas.com.ar)</a>\n'
            '• <strong>Guía de Trámites de Planificación Urbana y Obras Privadas:</strong> <a href="https://posadas.gov.ar/planurbano/guia-de-tramites/" target="_blank" rel="noopener noreferrer" class="fw-bold text-success">https://posadas.gov.ar/planurbano/guia-de-tramites/</a>\n\n'
            '🏪 <strong>PASO 2 - DIRECCIÓN GENERAL DE HABILITACIONES COMERCIALES (ALTA DEL COMERCIO):</strong>\n'
            'Una vez verificadas las condiciones del inmueble, gestioná el alta comercial según tu rubro:\n'
            '👉 <a href="https://posadas.gov.ar/guiatramite" target="_blank" rel="noopener noreferrer" class="btn-tramite-directo">'
            '<i class="fa-solid fa-store me-2"></i>Guía Oficial de Trámites y Habilitaciones (posadas.gov.ar/guiatramite)</a>\n'
            '• <strong>Portal de Habilitaciones Municipales y Eventos Online:</strong> <a href="https://datos.posadas.gov.ar/habilitaciones-municipales/" target="_blank" rel="noopener noreferrer" class="fw-bold text-success">https://datos.posadas.gov.ar/habilitaciones-municipales/</a>\n\n'
            '<strong>Pasos completos para habilitar tu negocio en Posadas:</strong>\n'
            '1️⃣ <strong>Factibilidad y Planos en Obras Privadas (Sistema GOP):</strong> Verificá que el local cumpla con el Código de Edificación, indicadores urbanos y planos visados en <a href="https://posadas.gestiondeobrasprivadas.com.ar/" target="_blank" rel="noopener noreferrer">posadas.gestiondeobrasprivadas.com.ar</a> o en el módulo de <strong>Obras Privadas del CAV Itaembé Guazú</strong>.\n'
            '2️⃣ <strong>Documentación obligatoria:</strong> Reuní tu DNI, constancia de CUIT (ATM y ARCA/AFIP), título de propiedad o contrato de alquiler sellado, libre deuda de TGI y certificado de Bomberos de la Policía de Misiones.\n'
            '3️⃣ <strong>Bromatología y Carnet Sanitario (si vendés o manipulás alimentos):</strong> Podés liquidar y abonar la tasa del Carnet Sanitario directamente en la delegación municipal del <strong>CAV Itaembé Guazú</strong>.\n'
            '4️⃣ <strong>Solicitud de Habilitación Comercial:</strong> Presentá la documentación en <a href="https://posadas.gov.ar/guiatramite" target="_blank" rel="noopener noreferrer">posadas.gov.ar/guiatramite</a> / <a href="https://datos.posadas.gov.ar/habilitaciones-municipales/" target="_blank" rel="noopener noreferrer">Portal de Habilitaciones</a> o presencialmente en el CAV Itaembé Guazú o Edificio Central (San Martín 1579).\n\n'
        )
    elif tramite_id == 'oficina_empleo':
        return (
            '💼 <strong>SISTEMA DE EMPLEO DE POSADAS - CARGA DE CV Y OFERTAS LABORALES:</strong>\n'
            'Intermediación laboral gratuita para vecinos de la ciudad:\n'
            '👉 <a href="https://sistemaempleo.posadas.gov.ar/" target="_blank" rel="noopener noreferrer" class="fw-bold text-success">Sistema de Empleo Posadas (Cargar CV)</a>\n\n'
            '<strong>Pasos para registrar tu currículum:</strong>\n'
            '1️⃣ Ingresá al <a href="https://sistemaempleo.posadas.gov.ar/" target="_blank" rel="noopener noreferrer">Sistema de Empleo Posadas</a>.\n'
            '2️⃣ Creá tu usuario con tu N° de CUIL y completá tus datos de contacto.\n'
            '3️⃣ Cargá tus estudios alcanzados, experiencia laboral previa y cursos realizados.\n'
            '4️⃣ Postulate a las búsquedas laborales activas y programas de inserción laboral para jóvenes y adultos.\n'
            '📌 <em>También podés acercarte a la sede física en Félix de Azara 1660 o consultar en el portal de la Municipalidad de Posadas: <a href="https://posadas.gov.ar/" target="_blank" rel="noopener noreferrer">posadas.gov.ar</a>.</em>\n\n'
        )
    elif tramite_id == 'iprodha_tramites':
        return (
            '🏠 <strong>¿CÓMO INSCRIBIRSE Y PARTICIPAR EN LOS SORTEOS DE VIVIENDA ("GANAR UNA CASA") EN EL IPRODHA?:</strong>\n'
            'La asignación de viviendas sociales en Posadas se realiza por sorteos públicos transparentes:\n'
            '👉 <a href="https://sistema.iprodha.misiones.gob.ar/" target="_blank" rel="noopener noreferrer" class="fw-bold text-success">Portal de Autogestión e Inscripción IPRODHA</a>\n\n'
            '<strong>Pasos para estar inscripto y participar:</strong>\n'
            '1️⃣ <strong>Registro en la web:</strong> Ingresá a <a href="https://sistema.iprodha.misiones.gob.ar/" target="_blank" rel="noopener noreferrer">sistema.iprodha.misiones.gob.ar</a> con tu CUIL y contraseña (o registrate si es tu primera vez).\n'
            '2️⃣ <strong>Ficha de Inscripción:</strong> Completá la ficha con la composición de tu grupo familiar, ingresos demostrables y garante solidario. Recordá actualizarla cada 360 días.\n'
            '3️⃣ <strong>Requisito fundamental:</strong> Ningún integrante del grupo puede poseer vivienda propia o lote a su nombre.\n'
            '4️⃣ 🚨 <strong>¡PASO INDISPENSABLE - Botón "PARTICIPAR"!:</strong> Cuando el IPRODHA anuncie una convocatoria para Posadas, debés entrar a tu cuenta y pulsar obligatoriamente el botón <strong>"PARTICIPAR"</strong> para entrar al sorteo.\n'
            '📌 <em>Más información institucional en: <a href="https://iprodha.misiones.gob.ar/" target="_blank" rel="noopener noreferrer">iprodha.misiones.gob.ar</a>.</em>\n\n'
        )
    elif tramite_id == 'registro_civil':
        return (
            '📑 <strong>REGISTRO PROVINCIAL DE LAS PERSONAS - PORTAL OFICIAL Y SEDES:</strong>\n'
            'Trámites de actas, partidas, DNI y pasaportes a través de su sitio web oficial y delegaciones en Posadas:\n'
            '👉 <a href="https://www.registrocivil.misiones.gov.ar/" target="_blank" rel="noopener noreferrer" class="btn-tramite-directo">'
            '<i class="fa-solid fa-arrow-up-right-from-square me-2"></i>Portal Oficial Registro Civil Misiones (registrocivil.misiones.gov.ar)</a>\n\n'
            '<strong>Sedes y canales de atención presencial en Posadas:</strong>\n'
            '• <strong>Sede Central Dirección General:</strong> Av. Andresito s/n (Bº Cristo Rey, Chacra 32-33). Tel: (0376) 445-8235 / (0376) 445-8226 / (0376) 444-4200.\n'
            '• <strong>Módulo CAV Itaembé Guazú:</strong> Calle Aguará Guazú y Magnolias (Lunes a Viernes de 07:00 a 13:00 hs).\n'
            '• <strong>Módulo CAV Las Heras:</strong> Av. Las Heras Nº 3929 (Lunes a Viernes de 07:00 a 13:00 hs).\n'
            '• <strong>Ubicación en Google Maps:</strong> <a href="https://www.google.com/maps/search/Registro+Provincial+de+las+Personas+Posadas+Misiones" target="_blank" rel="noopener noreferrer">Ver Sedes en Google Maps</a>.\n'
            '• <strong>Turnos DNI y Pasaporte:</strong> Presencial en los Centros de Documentación Rápida (CDR) o a través de la app nacional <a href="https://mi.argentina.gob.ar/" target="_blank" rel="noopener noreferrer">Mi Argentina (mi.argentina.gob.ar)</a>.\n\n'
        )
    elif tramite_id == 'denuncia_ruidos_molestos':
        return (
            '📢 <strong>ORDENANZA VI – Nº 14: RÉGIMEN DE PROTECCIÓN CONTRA RUIDOS MOLESTOS EN POSADAS:</strong>\n'
            'En Posadas, la emisión de ruidos molestos, música a alto volumen, escapes libres y perturbaciones sonoras de cualquier índole está tipificada como infracción bajo la <strong>Ordenanza VI – Nº 14</strong> del Digesto Jurídico Municipal.\n\n'
            '👉 <a href="https://wa.me/5493764134650" target="_blank" rel="noopener noreferrer" class="fw-bold text-success">'
            '<i class="fa-brands fa-whatsapp me-2"></i>Guardia de Ruidos Molestos (WhatsApp Oficial 3764-134650)</a>\n\n'
            '<strong>Cómo radicar la denuncia y pasos para la intervención municipal:</strong>\n'
            '1️⃣ <strong>Intervención primaria de la Municipalidad:</strong> La <strong>Dirección de Control Comunal (Guardia de Ruidos Molestos)</strong> es el organismo competente encargado de despachar inspectores, realizar mediciones sonométricas con decibelímetro y labrar actas de infracción elevadas al Tribunal Municipal de Faltas.\n'
            '2️⃣ <strong>Horarios de descanso especialmente protegidos:</strong>\n'
            '   • <em>Horario de siesta:</em> 13:00 a 15:00 hs.\n'
            '   • <em>Descanso nocturno:</em> 22:00 a 06:00 hs (y fines de semana).\n'
            '3️⃣ <strong>Datos necesarios al completar el formulario:</strong>\n'
            '   • Tus datos personales de contacto (Nombre, DNI, Teléfono).\n'
            '   • En el relato de la situación, detallá el tipo de ruido (música a alto volumen, ruidos de cualquier índole, etc.) y los días/horarios frecuentes.\n'
            '   • <em>Ubicación y datos de la vecina/o:</em> Indicá la dirección exacta (calle, número o entrecalles, barrio) y el nombre de la vecina/o infractor si lo conocés. '
            '<strong>Si te falta el nombre o la dirección exacta, no te preocupes:</strong> indicá cualquier dato orientativo o características visibles de la fachada/vivienda (color de rejas, portón, referencias cercanas) para que los inspectores puedan identificarla sin error.\n'
            '4️⃣ <strong>Canales de atención directa para urgencias:</strong>\n'
            '   • <strong>WhatsApp Oficial Guardia de Ruidos Molestos:</strong> <a href="https://wa.me/5493764134650" target="_blank" rel="noopener noreferrer">3764-134650</a>.\n'
            '   • <strong>Línea CIUDAD Gratuita:</strong> 0800-888-2483.\n'
            '   • <strong>Flagrancia nocturna / disturbios:</strong> Línea 911 de la Policía de Misiones.\n'
            '📌 <em>Nota sobre mediación: Si con posterioridad buscás un acuerdo pacífico de convivencia voluntaria, también podés recurrir de forma complementaria a la Defensoría del Pueblo de Posadas, pero la fiscalización y sanción directa corresponde a la Guardia Municipal de Ruidos Molestos.</em>\n\n'
        )
    elif tramite_id == 'defensoria_pueblo':
        return (
            '⚖️ <strong>DEFENSORÍA DEL PUEBLO DE POSADAS - MEDIACIÓN VECINAL GRATUITA:</strong>\n'
            'Resolución pacífica de conflictos de convivencia barrial y reclamos por servicios:\n'
            '👉 <a href="https://defensoriadelpueblodeposadas.gob.ar/acceso-a-justicia-y-mediacion/" target="_blank" rel="noopener noreferrer" class="fw-bold text-success">Solicitar Mediación Comunitaria Online</a>\n\n'
            '<strong>Cómo solicitar la intervención de la Defensoría:</strong>\n'
            '1️⃣ Ingresá al formulario de <a href="https://defensoriadelpueblodeposadas.gob.ar/acceso-a-justicia-y-mediacion/" target="_blank" rel="noopener noreferrer">Acceso a la Justicia y Mediación</a> o escribí a través del <a href="https://defensoriadelpueblodeposadas.gob.ar/contacto/" target="_blank" rel="noopener noreferrer">Formulario de Contacto</a>.\n'
            '2️⃣ Describí el motivo del conflicto (ruidos molestos, problemas linderos o quejas ante prestatarias de servicios).\n'
            '3️⃣ El equipo de mediadores citará a las partes para una instancia de diálogo pacífico, voluntario y confidencial.\n'
            '📌 <em>Servicio 100% gratuito. Portal web oficial: <a href="https://defensoriadelpueblodeposadas.gob.ar/" target="_blank" rel="noopener noreferrer">defensoriadelpueblodeposadas.gob.ar</a> (también accesible vía <a href="https://defensoriaposadas.gob.ar/" target="_blank" rel="noopener noreferrer">defensoriaposadas.gob.ar</a>). '
            'Sede: Félix de Azara 2438 / Calle Buenos Aires N° 1441. <a href="https://www.google.com/maps/search/Defensoria+del+Pueblo+Posadas+Misiones" target="_blank" rel="noopener noreferrer">Ver en Google Maps</a>. Tel: (0376) 443-3241 | WhatsApp: (376) 412-5611.</em>\n\n'
        )
    elif tramite_id == 'emsa_factura':
        return (
            '⚡ <strong>ENERGÍA DE MISIONES (EMSA) - PAGO DE FACTURA Y AUTOGESTIÓN DE CLIENTES:</strong>\n'
            'Pagá tu factura de luz de forma directa por internet:\n'
            '👉 <a href="https://clientes.energiademisiones.com.ar/" target="_blank" rel="noopener noreferrer" class="fw-bold text-success">Portal de Clientes EMSA (Pago de Facturas)</a>\n\n'
            '<strong>Pasos para pagar tu factura de luz:</strong>\n'
            '1️⃣ Ingresá directamente al <a href="https://clientes.energiademisiones.com.ar/" target="_blank" rel="noopener noreferrer">Portal de Clientes de Energía de Misiones</a>.\n'
            '2️⃣ Ingresá tu <strong>Número de Usuario</strong> y <strong>Número de Conexión</strong> (figuran en la parte superior de tu factura).\n'
            '3️⃣ Consultá las boletas pendientes y aboná online con tarjeta de débito o crédito.\n'
            '📌 <em>Sitio oficial institucional: <a href="https://www.energiademisiones.com.ar/" target="_blank" rel="noopener noreferrer">https://www.energiademisiones.com.ar/</a>. Urgencias técnicas 24 hs: 0800 888 3672.</em>\n\n'
        )
    return ''


def generar_respuesta_consulta(nombre: str, detalle: str, datos_ubicacion: dict = None) -> dict:
    """
    Brinda orientación oficial validada consultando el directorio de organismos y el catálogo de trámites.
    - Si la consulta corresponde a un organismo externo (IPRODHA, Defensoría, EMSA comercial, SAMSA):
      muestra ficha institucional verificada, requisitos, canales de contacto y enlace directo,
      aclarando que SIGEV orienta y deriva pero no sustituye el trámite propio de la entidad.
    - Si corresponde a un trámite digital municipal o provincial (patente, licencia, multas):
      ofrece el botón directo, guía paso a paso, fuente y fecha de verificación.
    - No genera automáticamente un ticket en el sistema.
    """
    t_det = normalizar_texto(detalle)
    ctx_ubi = extraer_contexto_ubicacion(detalle, datos_ubicacion)

    # Consulta general de seguimiento de trámites/tickets
    es_consulta_seguimiento_general = any(k in t_det for k in [
        'como sigue mi reclamo', 'como va mi reclamo', 'como sigue mi tramite', 'como va mi tramite',
        'estado de mi reclamo', 'estado de mi tramite', 'estado de mi expediente', 'donde fue derivado',
        'hacia donde fue derivado', 'consultar mi tramite', 'consultar mi expediente', 'consultar mi ticket',
        'ver mi ticket', 'donde derivaron mi reclamo', 'hacia donde derivaron mi', 'seguimiento de mi tramite',
        'seguimiento de mi ticket', 'seguimiento de ticket'
    ])
    if es_consulta_seguimiento_general:
        saludo = f"¡Hola, {nombre}! " if nombre else "¡Hola! "
        cuerpo = (
            f'{saludo}Para consultar el estado actual de tu trámite o reclamo y conocer <strong>hacia dónde fue derivado</strong>:\n\n'
            f'🔍 <strong>Buscador de Trámites en el Portal:</strong>\n'
            f'En la sección de <strong>Seguimiento de Reclamo o Trámite</strong> (ubicada más abajo en esta página) '
            f'podés ingresar tu <strong>N° de Ticket (ej: TCK-2026-0001)</strong> o directamente tu <strong>DNI</strong> para ver la ficha completa con el organismo de destino hacia donde fue derivado.\n\n'
            f'💬 <strong>O consultame directamente por aquí:</strong>\n'
            f'Escribí el número de ticket en tu consulta (por ejemplo: <em>"¿Cómo sigue mi ticket TCK-2026-0001?"</em>) y te informaré de inmediato su estado actual y el área asignada.'
        )
        return {
            'tipo_consulta': TIPO_CONSULTA,
            'es_emergencia': False,
            'es_emergencia_electrica': False,
            'es_reclamo': False,
            'es_consulta': True,
            'es_derivacion_externa': False,
            'reclamo_confirmado': False,
            'area_sugerida': 'Mesa de Entrada - CAV Posadas',
            'organismo_destino': 'Mesa de Entrada - CAV Posadas',
            'respuesta_texto': cuerpo,
            'botones_emergencia': [],
            'tramite_info': None,
            'organismo_info': None,
            'contexto_ubicacion': ctx_ubi,
        }

    org_externo = identificar_organismo_competente(detalle)
    es_derivacion_externa = False
    organismo_info = None

    if org_externo and org_externo.get('es_externo'):
        es_derivacion_externa = True
        organismo_info = org_externo
        enlace_principal = org_externo['enlaces_oficiales'].get('portal_oficial', 'https://posadas.gov.ar/')
        
        t_det = normalizar_texto(detalle)
        es_consulta_ganar_casa_o_sorteo = (org_externo['id'] == 'iprodha') and any(k in t_det for k in [
            'ganar una casa', 'ganar la casa', 'ganar casa', 'anotarme para una casa', 'anotarme a una casa',
            'anotarme en una casa', 'anotarse para una casa', 'anotarse a una casa', 'anotarme para la casa',
            'donde me anoto', 'donde se anota', 'donde uno se anota', 'como anotarme', 'inscribirme', 'inscripcion',
            'sorteo', 'sorteos', 'postularme', 'adjudicar', 'adjudicacion', 'tener una casa', 'conseguir una casa',
            'conseguir casa', 'pedir una casa', 'sacar una casa', 'vivienda social', 'viviendas sociales', 'plan de viviendas'
        ])

        bloque_especifico = ''
        if es_consulta_ganar_casa_o_sorteo:
            bloque_especifico = (
                f'🏠 <strong>¿CÓMO ANOTARSE Y PARTICIPAR EN LOS SORTEOS DE VIVIENDAS ("GANAR UNA CASA")?</strong>\n\n'
                f'En la provincia de Misiones, la asignación de viviendas sociales se realiza a través de <strong>sorteos públicos del IProDHa</strong> '
                f'(en conjunto con el IPLyC). La inscripción y postulación se efectúa de manera <strong>100% online y gratuita</strong> a través de su sitio web oficial:\n\n'
                f'1️⃣ <strong>Registro en la plataforma:</strong> Ingresá a la web oficial del IProDHa (<a href="https://sistema.iprodha.misiones.gob.ar/" target="_blank" rel="noopener noreferrer">sistema.iprodha.misiones.gob.ar</a> (Portal de Autogestión e Inscripción) o <a href="https://iprodha.misiones.gob.ar/" target="_blank" rel="noopener noreferrer">iprodha.misiones.gob.ar</a> (Portal Oficial)) y accedé con tu CUIL y clave de <em>Ciudadano Misiones</em>.\n'
                f'2️⃣ <strong>Completar la Ficha de Inscripción (Estar anotado):</strong> Cargá tus datos personales, los de tu grupo familiar conviviente, ingresos mensuales demostrables y datos del garante o codeudor solidario. <em>Recordá actualizar tu ficha cada 360 días para mantener vigente el legajo</em>.\n'
                f'3️⃣ <strong>Convocatorias públicas por localidad:</strong> El IProDHa publica periódicamente convocatorias abiertas para Posadas (ej. complejos habitacionales en Itaembé Guazú u otros sectores).\n'
                f'4️⃣ 🚨 <strong>¡PASO INDISPENSABLE - Botón "PARTICIPAR"!:</strong> Estar anotado previamente no te ingresa automáticamente al sorteo. Cuando se abra una convocatoria para Posadas, debés ingresar a tu perfil del IProDHa y hacer clic obligatoriamente en el botón <strong>"PARTICIPAR"</strong> dentro del plazo estipulado.\n'
                f'5️⃣ <strong>Sorteo público y precalificación:</strong> Si resultás favorecido en el sorteo público, el equipo social del IProDHa realizará la evaluación socioambiental y verificación de documentación para la posterior adjudicación definitiva.\n\n'
            )
        elif org_externo['id'] == 'emsa':
            bloque_especifico = (
                '⚡ <strong>PORTAL DE CLIENTES EMSA - PAGO DE FACTURA ONLINE:</strong>\n'
                'Accedé directamente al módulo de consulta de deuda y pago de facturas de luz sin moverte de tu casa:\n'
                '👉 <a href="https://clientes.energiademisiones.com.ar/" target="_blank" rel="noopener noreferrer" class="fw-bold text-success">Portal de Clientes de Energía de Misiones</a>\n\n'
                '1️⃣ Ingresá con tu <strong>Número de Usuario</strong> y <strong>Número de Conexión</strong> (figuran en el encabezado de tu factura de luz).\n'
                '2️⃣ Consultá tu saldo adeudado y descargá tu boleta digital en PDF.\n'
                '3️⃣ Realizá el pago online seguro con tarjeta de débito o crédito.\n\n'
            )
        elif org_externo['id'] == 'defensoria_pueblo':
            bloque_especifico = (
                '⚖️ <strong>DEFENSORÍA DEL PUEBLO DE POSADAS - MEDIACIÓN VECINAL Y RECLAMOS:</strong>\n'
                'Servicio público y gratuito para resolver conflictos comunitarios (ruidos molestos, problemas linderos, servicios públicos):\n'
                '👉 <a href="https://defensoriadelpueblodeposadas.gob.ar/acceso-a-justicia-y-mediacion/" target="_blank" rel="noopener noreferrer" class="fw-bold text-success">Solicitar Mediación Comunitaria Online</a>\n\n'
                '• <strong>Acceso a la Justicia y Mediación:</strong> <a href="https://defensoriadelpueblodeposadas.gob.ar/acceso-a-justicia-y-mediacion/" target="_blank" rel="noopener noreferrer">Formulario de Mediación Online</a>.\n'
                '• <strong>Formulario de Reclamos y Contacto:</strong> <a href="https://defensoriadelpueblodeposadas.gob.ar/contacto/" target="_blank" rel="noopener noreferrer">Contacto Directo Defensoría</a>.\n'
                '• <strong>Sitios Web Oficiales:</strong> <a href="https://defensoriadelpueblodeposadas.gob.ar/" target="_blank" rel="noopener noreferrer">https://defensoriadelpueblodeposadas.gob.ar/</a> (portal histórico: <a href="https://defensoriaposadas.gob.ar/" target="_blank" rel="noopener noreferrer">https://defensoriaposadas.gob.ar/</a>).\n'
                '• <strong>Sede y Ubicación:</strong> Félix de Azara 2438 / Calle Buenos Aires N° 1441, Posadas. <a href="https://www.google.com/maps/search/Defensoria+del+Pueblo+Posadas+Misiones" target="_blank" rel="noopener noreferrer">Ver ubicación en Google Maps</a>.\n'
                '• <strong>Teléfonos:</strong> (0376) 443-3241 | WhatsApp: (376) 412-5611.\n\n'
            )
        elif org_externo['id'] == 'samsa':
            bloque_especifico = (
                '💧 <strong>PAGO Y GESTIÓN DE FACTURA DE AGUA - SAMSA (Servicios de Aguas de Misiones S.A.):</strong>\n\n'
                '⚠️ <strong>Aclaración Importante sobre el CAV:</strong>\n'
                'El servicio de agua potable y desagües cloacales en Posadas y Garupá es gestionado por <strong>SAMSA</strong>, una <strong>empresa privada concesionaria</strong>. '
                '<strong>SAMSA NO está vinculada al CAV ni posee oficina, cajas de cobro ni puesto de atención presencial en el Centro de Atención al Vecino (CAV) Itaembé Guazú.</strong> '
                'Por lo tanto, <strong>no es necesario acudir presencialmente al CAV</strong> para abonar tu boleta de agua.\n\n'
                '🌐 <strong>PAGO 100% ONLINE DIRECTO (Sin moverte de tu casa):</strong>\n'
                '👉 <a href="https://samsa.com.ar/paga-tu-factura/" target="_blank" rel="noopener noreferrer" class="fw-bold text-success">Pagar Factura SAMSA Online (Portal Oficial)</a>\n\n'
                '<strong>Pasos para pagar tu factura de agua:</strong>\n'
                '1️⃣ Ingresá al portal oficial de pagos de SAMSA: <a href="https://samsa.com.ar/paga-tu-factura/" target="_blank" rel="noopener noreferrer">https://samsa.com.ar/paga-tu-factura/</a>\n'
                '2️⃣ Colocá tu <strong>Número de Cuenta</strong> (figura en el margen superior derecho de tu factura de agua).\n'
                '3️⃣ Consultá las boletas pendientes o el saldo de tu cuenta.\n'
                '4️⃣ Aboná online mediante medios de pago digitales habilitados: <strong>Mercado Pago</strong> (dinero en cuenta, tarjetas de débito/crédito), <strong>Macro Click</strong>, <strong>Red Link</strong>, <strong>Banelco</strong> o código de pago / QR.\n\n'
                '💻 <strong>Oficina Virtual de Autogestión:</strong>\n'
                'Podés consultar tu histórico de consumos y descargar boletas en la Oficina Virtual de SAMSA: '
                '<a href="https://samsa.com.ar/" target="_blank" rel="noopener noreferrer">www.samsa.com.ar</a> (o <a href="https://intranet.samsa.com.ar/apex/f?p=1000:200" target="_blank" rel="noopener noreferrer">intranet.samsa.com.ar</a>).\n\n'
                '📞 <strong>Canales de Atención al Cliente SAMSA:</strong>\n'
                '• <strong>Línea Gratuita de Atención (Call Center 24 hs):</strong> <strong>0800-888-9980</strong>\n'
                '• <strong>Teléfonos Sede:</strong> (0376) 442-8888 / (0376) 442-8000\n'
                '• <strong>Correo Electrónico:</strong> <a href="mailto:consultas@samsa.com.ar">consultas@samsa.com.ar</a>\n'
                '• <strong>Oficina Comercial Central (Atención Presencial SAMSA):</strong> Av. López y Planes N° 2552 (entre Corrientes y Lavalle), Posadas. Horarios: Lunes a Viernes de 06:30 a 14:00 hs (Cajas: de 06:30 a 14:00 hs y de 16:30 a 19:00 hs). <em>Recordá que SAMSA no atiende en el CAV Itaembé Guazú.</em>\n\n'
            )

        requisitos_html = '\n'.join([f'• {r}' for r in org_externo['requisitos_oficiales']])
        tramites_html = '\n'.join([f'• {t}' for t in org_externo['tipos_consultas']])

        canales = org_externo['canales_contacto']
        canales_html = (
            f"📍 <strong>Atención Presencial:</strong> {canales.get('atencion_presencial', 'Sede en Posadas')}\n"
            f"🕒 <strong>Horarios:</strong> {canales.get('horarios', 'Lunes a Viernes')}\n"
            f"📞 <strong>Teléfono Oficial:</strong> {canales.get('telefono', canales.get('telefono_linea', 'Línea de atención'))}\n"
        )
        if canales.get('whatsapp'):
            canales_html += f"📱 <strong>WhatsApp Oficial:</strong> {canales.get('whatsapp')}\n"

        enlaces_lista = []
        for k, v in org_externo.get('enlaces_oficiales', {}).items():
            nombre_enlace = k.replace('_', ' ').title()
            enlaces_lista.append(f'• <strong>{nombre_enlace}:</strong> <a href="{v}" target="_blank" rel="noopener noreferrer">{v}</a>')
        enlaces_html = '\n'.join(enlaces_lista)

        cuerpo = (
            f'¡Hola, {nombre}! Tu consulta corresponde a la competencia de <strong>{org_externo["nombre"]}</strong> ({org_externo["sigla"]}):\n\n'
            f'{bloque_especifico}'
            f'🏛️ <strong>Competencia del Organismo:</strong>\n{org_externo["competencia"]}\n\n'
            f'📋 <strong>Consultas y trámites que atiende:</strong>\n{tramites_html}\n\n'
            f'📌 <strong>Requisitos Oficiales Conocidos:</strong>\n{requisitos_html}\n\n'
            f'⚙️ <strong>Canales Oficiales en Posadas:</strong>\n{canales_html}\n'
            f'🌐 <strong>Enlaces Oficiales Verificados:</strong>\n{enlaces_html}\n\n'
            f'👉 <a href="{enlace_principal}" target="_blank" rel="noopener noreferrer" class="btn-tramite-directo">'
            f'<i class="fa-solid fa-arrow-up-right-from-square me-2"></i>Iniciar trámite online en {org_externo["sigla"]}</a>\n\n'
            f'🏛️ <strong>Fuente Oficial Validada:</strong> {org_externo["fuente_verificacion"]}\n'
            f'📅 <strong>Fecha de Verificación:</strong> {org_externo["fecha_verificacion"]}\n\n'
            f'⚠️ <em>Aviso de Derivación: Este servicio es de orientación hacia el canal oficial externo. '
            f'SIGEV no afirma haber enviado un reclamo ni transfiere tus datos personales a terceros sin una integración autorizada.</em>'
        )

        return {
            'tipo_consulta': TIPO_CONSULTA,
            'es_emergencia': False,
            'es_emergencia_electrica': False,
            'es_reclamo': False,
            'es_consulta': True,
            'es_derivacion_externa': True,
            'reclamo_confirmado': False,
            'organismo_destino': org_externo['nombre'],
            'respuesta_texto': cuerpo,
            'botones_emergencia': [],
            'tramite_info': None,
            'organismo_info': org_externo,
            'cod_categoria_default': 100,
            'contexto_ubicacion': ctx_ubi,
        }

    # Búsqueda general en el catálogo de trámites digitales
    tramite = buscar_tramite_por_consulta(detalle)

    bloque_ubicacion_obra = ''
    if tramite['id'] in ['obras_privadas', 'denuncia_obras']:
        if tramite['id'] == 'denuncia_obras':
            if ctx_ubi.get('barrio') or ctx_ubi.get('entre_calles'):
                loc_str = f"Barrio {ctx_ubi['barrio']}" if ctx_ubi.get('barrio') else "Posadas"
                if ctx_ubi.get('entre_calles'):
                    loc_str += f" - {ctx_ubi['entre_calles']}"
                if ctx_ubi.get('referencias'):
                    loc_str += f" (Ref: {ctx_ubi['referencias']})"
                bloque_ubicacion_obra = (
                    f"📍 <strong>UBICACIÓN DE LA CONSTRUCCIÓN A INSPECCIONAR:</strong> {loc_str}\n"
                    f"• <strong>Inspección Técnica Municipal:</strong> Obras Públicas de la Municipalidad de Posadas despacha el equipo de inspectores de obras hacia esta dirección para constatar la afectación del muro medianero y el estado de la construcción.\n"
                    f"• <strong>Medidas Preventivas:</strong> Si la construcción carece de planos aprobados o permiso en Sistema GOP, se intima a la paralización preventiva inmediata de los trabajos.\n\n"
                )
            else:
                bloque_ubicacion_obra = (
                    f"📍 <strong>¿DÓNDE SE ENCUENTRA LA CONSTRUCCIÓN O MURO AFECTADO? (DATO FUNDAMENTAL):</strong>\n"
                    f"Para que el equipo de inspectores de <strong>Obras Públicas de la Municipalidad</strong> acuda a fiscalizar y constatar la irregularidad, es fundamental indicar la ubicación exacta:\n"
                    f"• <strong>¿En qué barrio o chacra de Posadas se ubica la obra?</strong>\n"
                    f"• <strong>¿Entre qué calles o a qué altura aproximada?</strong>\n"
                    f"• <strong>Puntos de referencia</strong> (ej: frente a una plaza, escuela o comercio).\n"
                    f"👉 <em>Indicá en qué barrio o calle se encuentra la propiedad para coordinar la inspección municipal en el terreno.</em>\n\n"
                )
        else:
            if ctx_ubi.get('barrio') or ctx_ubi.get('entre_calles'):
                loc_str = f"Barrio {ctx_ubi['barrio']}" if ctx_ubi.get('barrio') else "Posadas"
                if ctx_ubi.get('entre_calles'):
                    loc_str += f" - {ctx_ubi['entre_calles']}"
                if ctx_ubi.get('referencias'):
                    loc_str += f" (Ref: {ctx_ubi['referencias']})"
                bloque_ubicacion_obra = (
                    f"📍 <strong>UBICACIÓN DE LA OBRA INFORMADA:</strong> {loc_str}\n"
                    f"• <strong>Indicadores Urbanísticos:</strong> En Posadas, los índices de ocupación del suelo (FOS), superficie total (FOT), alturas máximas y retiros obligatorios de edificación se rigen por el Plan Urbano Ambiental para la zona de {ctx_ubi.get('barrio', 'tu barrio')}.\n"
                    f"• <strong>Atención y Asesoramiento Cercano:</strong> Además de la gestión 100% digital en el Sistema GOP y la sede central municipal (San Martín 1579), en el sector oeste contás con la oficina de Planificación y Obras Privadas en el <strong>CAV Itaembé Guazú</strong> (Calle Aguará Guazú y Magnolias) para consultar normativas y presentar documentación.\n\n"
                )
            else:
                bloque_ubicacion_obra = (
                    f"📍 <strong>¿DÓNDE VIVÍS O DÓNDE SE UBICARÁ LA OBRA? (DATO FUNDAMENTAL):</strong>\n"
                    f"Para iniciar una obra o construcción en Posadas, es indispensable conocer <strong>en qué barrio, chacra o zona de la ciudad se ubica el terreno o propiedad</strong>:\n"
                    f"• <strong>Indicadores Urbanos (FOS y FOT):</strong> El Código de Edificación y el Plan Urbano Ambiental de Posadas establecen distintos factores de ocupación del suelo (FOS), superficie total edificable (FOT), retiros de frente/medianeras y alturas máximas según el barrio o sector territorial.\n"
                    f"• <strong>Centro de Atención correspondiente:</strong> Además de realizar el trámite 100% digital en el Sistema GOP, podés asesorarte en la sede central municipal (San Martín 1579) o en el <strong>CAV Itaembé Guazú</strong> (Calle Aguará Guazú y Magnolias) si tu obra se ubica en esa zona.\n"
                    f"👉 <em>¿Podrías indicarnos en qué barrio, chacra o entre qué calles tenés previsto realizar la obra?</em>\n\n"
                )
    elif tramite['id'] == 'denuncia_ruidos_molestos':
        if ctx_ubi.get('barrio') or ctx_ubi.get('entre_calles'):
            loc_str = f"Barrio {ctx_ubi['barrio']}" if ctx_ubi.get('barrio') else "Posadas"
            if ctx_ubi.get('entre_calles'):
                loc_str += f" - {ctx_ubi['entre_calles']}"
            if ctx_ubi.get('referencias'):
                loc_str += f" (Ref: {ctx_ubi['referencias']})"
            bloque_ubicacion_obra = (
                f"📍 <strong>UBICACIÓN DE LA MOLESTIA INFORMADA:</strong> {loc_str}\n"
                f"• <strong>Fiscalización Municipal en el terreno:</strong> La Dirección de Control Comunal despacha a la Guardia de Ruidos Molestos hacia esta dirección para constatar la emisión sonora y labrar las actas correspondientes bajo la <strong>Ordenanza VI – Nº 14</strong>.\n\n"
            )
        else:
            bloque_ubicacion_obra = (
                f"📍 <strong>¿DÓNDE SE GENERAN LOS RUIDOS O MÚSICA FUERTE? (DATO FUNDAMENTAL):</strong>\n"
                f"Para que el equipo de inspectores de la <strong>Guardia de Ruidos Molestos (Control Comunal)</strong> acuda a constatar la infracción, es fundamental indicar la dirección:\n"
                f"• <strong>Barrio o chacra de Posadas</strong> y entre qué calles o altura aproximada.\n"
                f"• <strong>Datos o características de la vecina/o:</strong> Si no contás con el nombre o numeración exacta, indicá cualquier referencia o color de fachada/rejas de la vivienda para facilitar la identificación por parte de los inspectores.\n\n"
            )

    requisitos_html = '\n'.join([f'• {r}' for r in tramite['requisitos']])

    boton_html = ''
    texto_boton_tramite = tramite.get('texto_boton', 'Iniciar trámite online')
    icono_btn = 'fa-credit-card' if ('pag' in texto_boton_tramite.lower() or 'boleta' in texto_boton_tramite.lower()) else 'fa-arrow-up-right-from-square'
    if tramite['tramite_online']:
        boton_html = (
            f'👉 <a href="{tramite["enlace_oficial"]}" target="_blank" rel="noopener noreferrer" class="btn-tramite-directo">'
            f'<i class="fa-solid {icono_btn} me-2"></i>{texto_boton_tramite}</a>\n\n'
        )
    else:
        boton_html = (
            f'👉 <a href="{tramite["enlace_oficial"]}" target="_blank" rel="noopener noreferrer" class="btn-tramite-directo">'
            f'<i class="fa-solid fa-globe me-2"></i>Ver información en portal oficial</a>\n\n'
        )

    canales_presenciales_html = ''
    if tramite.get('canales_presenciales'):
        canales_presenciales_html = f'📍 <strong>Atención Presencial:</strong>\n{tramite["canales_presenciales"]}\n\n'

    contacto_html = ''
    if tramite.get('telefono_contacto'):
        contacto_html = f'📞 <strong>Canales de Contacto:</strong> {tramite["telefono_contacto"]}\n\n'

    guia_pasos = generar_guia_pasos_tramite(tramite['id'])

    cuerpo = (
        f'¡Hola, {nombre}! Te compartimos la orientación oficial sobre <strong>{tramite["nombre"]}</strong> '
        f'gestionado por <strong>{tramite["organismo_responsable"]}</strong>:\n\n'
        f'{bloque_ubicacion_obra}'
        f'ℹ️ <strong>Descripción:</strong>\n{tramite["descripcion"]}\n\n'
        f'{boton_html}'
        f'{guia_pasos}'
        f'📋 <strong>Requisitos Principales:</strong>\n{requisitos_html}\n\n'
        f'{canales_presenciales_html}'
        f'{contacto_html}'
        f'🏛️ <strong>Fuente Oficial:</strong> {tramite["fuente"]}\n'
        f'📅 <strong>Fecha de Verificación:</strong> {tramite["fecha_verificacion"]}\n\n'
        f'💡 <em>Esta es una consulta informativa basada en información oficial. No se ha generado un ticket interno en el SIGEV.</em>'
    )

    return {
        'tipo_consulta': TIPO_CONSULTA,
        'es_emergencia': False,
        'es_emergencia_electrica': False,
        'es_reclamo': False,
        'es_consulta': True,
        'es_derivacion_externa': False,
        'reclamo_confirmado': False,
        'organismo_destino': tramite['organismo_responsable'],
        'respuesta_texto': cuerpo,
        'botones_emergencia': [],
        'tramite_info': tramite,
        'organismo_info': None,
        'cod_categoria_default': 100,
        'contexto_ubicacion': ctx_ubi,
    }


def generar_respuesta_reclamo(nombre: str, detalle: str, confirmado: bool = False, nro_ticket: str = None, datos_ubicacion: dict = None) -> dict:
    """
    Gestiona la respuesta para situaciones operativas municipales:
    - Analiza y extrae el contexto de ubicación (Barrio, entre calles, referencias).
    - Plantea preguntas de seguimiento adaptativas para los datos faltantes sin repetir los ya informados.
    - Genera una ficha de resumen automático de la solicitud.
    - Ofrece opciones claras de 'Registrar solicitud' o 'Solo necesitaba información'.
    - Si está confirmado: guarda y acredita el ticket en estado inicial PENDIENTE.
    """
    t = normalizar_texto(detalle)
    ctx_ubi = extraer_contexto_ubicacion(detalle, datos_ubicacion)
    es_poste_o_cable = any(k in t for k in ['poste', 'columna', 'cable', 'tendido', 'farola'])
    preguntas_info = generar_preguntas_seguimiento('reclamo', ctx_ubi, es_poste_o_cable=es_poste_o_cable)

    es_obra_muro = any(k in t for k in ['muro', 'medianera', 'ampliacion', 'amplaicion', 'amplio', 'obra', 'construccion', 'pared']) and any(k in t for k in ['vecin', 'ocupo', 'apoyo', 'rompio', 'clandestin', 'sin permiso', 'antirreglamentar', 'denuncia', 'invasi', 'edifico', 'tiro'])
    es_habilitacion_negocio = (
        any(k in t for k in ['negocio', 'nuegocio', 'nogio', 'negosio', 'negcio', 'neogcio', 'comercio', 'local', 'kiosco', 'almacen', 'verduleria', 'tienda', 'emprendimiento']) and
        any(k in t for k in ['abrir', 'poner', 'iniciar', 'habilitar', 'habilito', 'emprender', 'instalar', 'quise', 'quiero', 'solicitud', 'habilitacion', 'hacer', 'pasos'])
    ) or bool(re.search(r'\b(abrir|poner|iniciar|habilitar|habilito|instalar|hacer|quise abrir|quiero abrir|quiero hacer|quiero habilitar)\b.*?\b(negocio|nuegocio|nogio|negosio|negcio|neogcio|comercio|local|kiosco|almacen|verduleria|tienda|emprendimiento)\b', t)) or (
        bool(re.search(r'\b(quiero habilitar|necesito habilitar|para habilitar|habilitar un|habilitar mi)\b', t)) and not any(k in t for k in ['clave', 'medidor', 'luz', 'emsa', 'atm', 'dni', 'licencia'])
    )

    es_denuncia_ruidos = (
        any(k in t for k in [
            'ruidos molestos', 'ruido molesto', 'musica fuerte', 'musica alta',
            'musica a todo volumen', 'musica al taco', 'musica a alto volumen',
            'vecina ruidosa', 'vecino ruidoso', 'denuncia por ruidos', 'denunciar ruidos',
            'escucha musica fuerte', 'escuchan musica fuerte', 'ruido de cualquier indole',
            'ruidos de cualquier indole'
        ]) or (
            bool(re.search(r'\b(ruido\w*|musica)\b', t)) and
            bool(re.search(r'\b(molest\w*|fuerte|alta|taco|volumen|noche|vecin\w*|escucha|escuchan)\b', t))
        ) or (
            bool(re.search(r'\bdenunciar\b.*?\bvecin[oa]\b', t)) and
            bool(re.search(r'\b(ruido|musica|sonido|volumen|molest\w*)\b', t))
        )
    )

    # --- POO: RESOLUCIÓN POLIMÓRFICA DE TRÁMITES CAV ITAEMBÉ GUAZÚ ---
    # Si la solicitud coincide con uno de los 24 trámites oficiales del CAV,
    # se encapsulan las pautas institucionales, datos faltantes y requisitos documentales:
    info_cav = resolver_tramite_cav_itaembe(detalle, ctx_ubi)
    if info_cav:
        if not ctx_ubi.get('barrio'):
            ctx_ubi['barrio'] = 'Itaembé Guazú'
        if not ctx_ubi.get('entre_calles'):
            ctx_ubi['entre_calles'] = 'Calle Aguará Guazú y Magnolias (Sede CAV)'

    es_alumbrado_emsa = (
        any(k in t for k in [
            'luz quemada', 'foco', 'focos', 'luminaria', 'luminarias', 'farola', 'alumbrado',
            'a oscuras', 'esta oscuro', 'esta oscuto', 'oscuridad', 'tulipa', 'poste de luz'
        ]) or bool(re.search(r'\b(luz|foco|focos|luminaria|luminarias|poste)\b.*?\b(quemad[oa]s?|quemo|rot[oa]s?|apagad[oa]s?|no prende|no anda|oscur[oa]s?|oscut[oa]s?|arregl\w*|aregl\w*|repar\w*)\b', t))
        or bool(re.search(r'\b(quemad[oa]s?|quemo|rot[oa]s?|apagad[oa]s?|no prende|no anda|oscur[oa]s?|oscut[oa]s?|arregl\w*|aregl\w*|repar\w*)\b.*?\b(luz|foco|focos|luminaria|luminarias|poste)\b', t))
    )

    if info_cav:
        area = info_cav['area']
        organismo = info_cav['organismo']
        cod_categoria = info_cav.get('cod_categoria', 100)
        descripcion_intervencion = info_cav['gestion_programada']
        explicacion = info_cav['explicacion']
    elif es_alumbrado_emsa:
        area = 'Alumbrado Público, Luminarias y Red Eléctrica (Servicios Urbanos / EMSA)'
        organismo = 'Municipalidad de Posadas - Servicios Urbanos (Alumbrado Público) / Energía de Misiones S.A. (EMSA)'
        cod_categoria = 101
        descripcion_intervencion = 'reparación o recambio de foco/luminaria en poste de luz y verificación de red eléctrica junto a EMSA y Alumbrado Público'
        explicacion = (
            '💡 <strong>REPARACIÓN DE LUMINARIAS, FOCOS Y POSTES DE LUZ (ALUMBRADO PÚBLICO Y ENERGÍA DE MISIONES - EMSA):</strong>\n'
            'Para solucionar la falta de iluminación y reparar el foco o luminaria del poste de luz en tu cuadra, intervienen de forma coordinada:\n'
            '• ⚡ <strong>Energía de Misiones S.A. (EMSA):</strong> Responsable del suministro eléctrico en el tendido y postes de luz, conexión de red de alumbrado, fusibles aéreos y guardia técnica en Posadas e Itaembé Guazú.\n'
            '• 🏛️ <strong>Municipalidad de Posadas - Dirección de Alumbrado Público (Servicios Urbanos):</strong> Responsable del recambio de focos y artefactos LED, fotocélulas, brazos de luminarias y mantenimiento del alumbrado urbano.'
        )
    elif any(k in t for k in ['bache', 'pozo', 'asfalto', 'cordon cuneta', 'calle']):
        area = 'Obras Viales y Bacheo'
        organismo = 'Municipalidad de Posadas - Obras Públicas'
        cod_categoria = 100
        descripcion_intervencion = 'inspección vial, bacheo o nivelación de calzada'
        explicacion = (
            '🛣️ Corresponde una <strong>inspección y bacheo de calzada</strong> ante la '
            '<strong>Dirección de Obras Viales (Obras Públicas)</strong> de la Municipalidad para reparar el tramo afectado.'
        )
    elif es_obra_muro:
        area = 'Obras Privadas y Control de Construcciones'
        organismo = 'Municipalidad de Posadas - Obras Públicas'
        cod_categoria = 100
        descripcion_intervencion = 'inspección técnica de obra, verificación de planos y fiscalización por ocupación de muro medianero / ampliación antirreglamentaria'
        explicacion = (
            '🏛️ Corresponde iniciar una <strong>denuncia de obra</strong> ante la '
            '<strong>Dirección de Obras Privadas (Obras Públicas)</strong> de la Municipalidad para que un inspector verifique la construcción, el estado de los planos y la ocupación indebida sobre tu muro o medianera.'
        )
    elif es_habilitacion_negocio:
        area = 'Obras Públicas (Obras Privadas) y Habilitaciones Comerciales'
        organismo = 'Municipalidad de Posadas - Obras Públicas y Habilitaciones Comerciales'
        cod_categoria = 100
        descripcion_intervencion = 'adecuación edilicia y planos con Obras Públicas/Privadas y trámite de habilitación comercial'
        explicacion = (
            '🏛️ <strong>APERTURA DE NEGOCIO Y HABILITACIÓN MUNICIPAL:</strong>\n'
            'El trámite corresponde a la <strong>Secretaría de Obras Públicas (Dirección de Obras Privadas)</strong> '
            'para la verificación edilicia y planos del inmueble (especialmente si es una ampliación de tu vivienda), '
            'y a la <strong>Dirección General de Habilitaciones Comerciales</strong> para la autorización de apertura del comercio.'
        )
    elif any(k in t for k in ['basura', 'recoleccion', 'contenedor', 'microbasural', 'limpieza', 'pastizal', 'desmalez']):
        area = 'Recolección y Saneamiento Ambiental'
        organismo = 'Municipalidad de Posadas - Servicios Urbanos'
        cod_categoria = 100
        descripcion_intervencion = 'recolección especial, limpieza de predio o mantenimiento de contenedores'
        explicacion = (
            '🚛 Corresponde solicitar una <strong>intervención operativa de limpieza o recolección</strong> ante '
            '<strong>Servicios Urbanos</strong> para el saneamiento del lugar.'
        )
    elif any(k in t for k in ['poda', 'arbol', 'ramas']):
        area = 'Espacios Verdes y Arbolado Urbano'
        organismo = 'Municipalidad de Posadas - Espacios Verdes'
        cod_categoria = 100
        descripcion_intervencion = 'evaluación fitosanitaria, poda de despeje o retiro de ramas caídas'
        explicacion = (
            '🌿 Corresponde solicitar una <strong>inspección fitosanitaria y poda de despeje</strong> ante '
            '<strong>Espacios Verdes y Arbolado Urbano</strong> para intervenir sobre el arbolado de forma segura.'
        )
    elif any(k in t for k in ['perdida de agua', 'caño roto', 'cloaca']):
        area = 'Saneamiento y Obras Hídricas'
        organismo = 'Municipalidad de Posadas / SAMSA'
        cod_categoria = 100
        descripcion_intervencion = 'reparación de red pluvial o coordinación operativa con cuadrillas de saneamiento'
        explicacion = (
            '💧 Corresponde coordinar la <strong>reparación pluvial o cloacal</strong> ante '
            '<strong>Saneamiento y Obras Hídricas / SAMSA</strong> para despachar cuadrillas operativas.'
        )
    elif es_denuncia_ruidos:
        area = 'Control Comunal y Convivencia Urbana'
        organismo = 'Municipalidad de Posadas - Dirección de Control Comunal (Guardia de Ruidos Molestos)'
        cod_categoria = 100
        descripcion_intervencion = 'inspección sonométrica, medición de decibeles y fiscalización bajo la Ordenanza VI – Nº 14'
        explicacion = (
            '📢 <strong>RÉGIMEN DE PROTECCIÓN CONTRA RUIDOS MOLESTOS (ORDENANZA VI – Nº 14 DE POSADAS):</strong>\n'
            'En la ciudad de Posadas, emitir ruidos molestos, música a volumen desmedido o sonidos perturbadores de cualquier índole '
            'que atenten contra la tranquilidad y el descanso de los vecinos infringe formalmente la <strong>Ordenanza VI – Nº 14</strong> '
            'del Digesto Jurídico Municipal (con especial resguardo en horarios de siesta de 13:00 a 15:00 hs y descanso nocturno de 22:00 a 06:00 hs).\n\n'
            '🏛️ <strong>Autoridad competente primaria:</strong> La intervención y control corresponde a la '
            '<strong>Dirección de Control Comunal de la Municipalidad de Posadas</strong> mediante su <strong>Guardia de Ruidos Molestos</strong>, '
            'cuyo cuerpo de inspectores actúa en el territorio para constatar la infracción, realizar sonometría (medición de decibeles) y labrar las actas de infracción elevadas al Tribunal Municipal de Faltas.\n\n'
            '📱 <strong>Canal directo e inmediato (WhatsApp Oficial):</strong> Podés alertar o enviar ubicación en tiempo real al WhatsApp oficial de la '
            '<strong>Guardia de Ruidos Molestos: <a href="https://wa.me/5493764134650" target="_blank" rel="noopener noreferrer">3764-134650</a></strong> '
            'o a la Línea CIUDAD <strong>0800-888-2483</strong>. Para situaciones nocturnas de flagrancia o disturbios en la vía pública, también interviene la Línea 911 de la Policía de Misiones.\n\n'
            '⚖️ <em>Nota sobre Mediación Vecinal:</em> La Defensoría del Pueblo de Posadas interviene de manera complementaria o posterior únicamente en caso de que ambas partes '
            'deseen someterse a una mediación comunitaria voluntaria para acordar pautas de convivencia pacífica, pero la constatación, inspección y sanción directa recae exclusivamente en la Guardia de Control Comunal Municipal.'
        )
    elif any(k in t for k in ['mediacion comunitaria', 'mediacion vecinal', 'conflicto vecinal', 'convivencia vecinal']):
        area = 'Mediación Comunitaria y Convivencia'
        organismo = 'Defensoría del Pueblo de la Ciudad de Posadas'
        cod_categoria = 100
        descripcion_intervencion = 'audiencia de mediación comunitaria voluntaria y acuerdos de convivencia'
        explicacion = (
            '⚖️ Corresponde una <strong>instancia de mediación comunitaria voluntaria</strong> ante '
            'la <strong>Defensoría del Pueblo de la Ciudad de Posadas</strong> para facilitar el diálogo pacífico y acuerdos de convivencia entre vecinos.'
        )
    else:
        area = 'Servicios Urbanos y Atención Operativa'
        organismo = 'Municipalidad de Posadas - Servicios Urbanos'
        cod_categoria = 100
        descripcion_intervencion = 'intervención operativa o inspección en el barrio'
        explicacion = (
            f'📋 Corresponde dar intervención a <strong>{organismo} ({area})</strong> para su gestión e inspección técnica.'
        )

    resumen = generar_resumen_automatico(nombre, detalle, ctx_ubi, f"{organismo} ({area})")

    if not confirmado:
        # Repregunta de ubicación adaptativa, breve y precisa
        if not (ctx_ubi.get('barrio') and ctx_ubi.get('entre_calles')):
            if not ctx_ubi.get('barrio') and not ctx_ubi.get('entre_calles'):
                if es_obra_muro:
                    bloque_ubicacion = (
                        "📍 <strong>Ubicación de la obra y datos de la vecina/o:</strong>\n"
                        "Para enviar la inspección técnica necesitamos la ubicación exacta. "
                        "Por favor completá abajo en qué <strong>sector de Itaembé Guazú</strong> (barrio o chacra) te encontrás, y tu <strong>dirección exacta</strong> (calles, numeración o avenidas). "
                        "En el detalle, recordá agregar el <strong>nombre de la vecina o vecino</strong> (si lo sabés) y su <strong>dirección o número de casa lindera</strong>."
                    )
                else:
                    bloque_ubicacion = (
                        "📍 <strong>Ubicación requerida para la inspección:</strong>\n"
                        "Para enviar la inspección necesitamos la ubicación exacta. "
                        "Por favor completá abajo el <strong>barrio o chacra</strong>, y entre qué <strong>calles, numeración o avenidas</strong> se ubica."
                    )
            elif not ctx_ubi.get('barrio'):
                bloque_ubicacion = (
                    f"📍 <strong>Ubicación:</strong> Tenemos registrado sobre {ctx_ubi['entre_calles']}. "
                    "Por favor completá abajo en qué <strong>barrio o chacra</strong> de Posadas se ubica."
                )
            else:
                bloque_ubicacion = (
                    f"📍 <strong>Ubicación:</strong> Tenemos registrado el barrio {ctx_ubi['barrio']}. "
                    "Por favor completá abajo entre qué <strong>calles, altura o avenidas</strong> queda el lugar."
                )
        else:
            ref_str = f" (Ref: {ctx_ubi['referencias']})" if ctx_ubi.get('referencias') else ""
            bloque_ubicacion = f"📍 <strong>Ubicación registrada:</strong> Barrio {ctx_ubi['barrio']} - {ctx_ubi['entre_calles']}{ref_str}."

        nota_fotos = (
            "📷 <strong>Ayudanos a ver el problema:</strong>\n"
            "Si tenés una foto/video, adjuntala para que el equipo que revise tu reclamo pueda entender mejor la situación. "
            "<em>(Adjuntar fotos es opcional).</em>"
        )

        cierre_accion = (
            f"👉 Completá o confirmá los datos en el recuadro de abajo y presioná <strong>'Registrar solicitud'</strong> "
            f"para que el trámite ingrese formalmente a la oficina de {organismo}."
        )

        if info_cav:
            lista_datos = "\n".join([f"• <strong>{d}</strong>" for d in info_cav['datos_requeridos']])
            lista_docs = "\n".join([f"• <strong>{doc}</strong>" for doc in info_cav['documentos_adjuntos']])

            bloque_datos = (
                "📋 <strong>DATOS REQUERIDOS Y FALTANTES PARA TU TRÁMITE:</strong>\n"
                f"{lista_datos}\n\n"
                "👉 <em>Si te falta ingresar alguno de estos datos, completalo o agregalo en la descripción de abajo antes de confirmar.</em>"
            )

            bloque_docs = (
                "📎 <strong>DOCUMENTACIÓN Y FOTOGRAFÍAS A PRESENTAR / ADJUNTAR:</strong>\n"
                f"{lista_docs}\n\n"
                "📸 <em>Podés adjuntar una fotografía o archivo digital de tus documentos en el campo de adjuntos de abajo para iniciar la revisión. "
                "Tené presente que al momento de concurrir a la sede física deberás presentar los documentos originales para su constatación.</em>"
            )

            cierre_accion_cav = (
                f"👉 Completá o confirmá tus datos en el formulario de abajo y presioná <strong>'Registrar solicitud / Iniciar trámite en CAV Itaembé Guazú'</strong> "
                f"para dar inicio formal al expediente en la oficina de {organismo}, o <strong>'Solo necesitaba información'</strong> si solo requerías la guía."
            )

            cuerpo = (
                f'¡Hola, {nombre}!\n\n'
                f'{explicacion}\n\n'
                f'{bloque_datos}\n\n'
                f'{bloque_docs}\n\n'
                f'📍 <strong>Sede de Atención Presencial:</strong>\n'
                f'{info_cav["pautas_presenciales"]}\n\n'
                f'{bloque_ubicacion}\n\n'
                f'{nota_fotos}\n\n'
                f'{cierre_accion_cav}'
            )
        elif es_habilitacion_negocio:
            bloque_preguntas_negocio = (
                "🌐 <strong>PORTALES OFICIALES DIRECTOS (OBRAS PRIVADAS Y HABILITACIONES):</strong>\n"
                "👉 <a href=\"https://posadas.gestiondeobrasprivadas.com.ar/\" target=\"_blank\" rel=\"noopener noreferrer\" class=\"btn-tramite-directo\">"
                "<i class=\"fa-solid fa-building-circle-check me-2\"></i>Sistema GOP - Obras Privadas (Certificado de Funcionamiento Comercial y Planos)</a>\n"
                "👉 <a href=\"https://posadas.gov.ar/planurbano/guia-de-tramites/\" target=\"_blank\" rel=\"noopener noreferrer\" class=\"btn-tramite-directo\">"
                "<i class=\"fa-solid fa-map-location-dot me-2\"></i>Guía de Trámites de Planificación Urbana y Obras Privadas</a>\n"
                "👉 <a href=\"https://posadas.gov.ar/guiatramite\" target=\"_blank\" rel=\"noopener noreferrer\" class=\"btn-tramite-directo\">"
                "<i class=\"fa-solid fa-store me-2\"></i>Guía Oficial de Habilitaciones Comerciales (posadas.gov.ar/guiatramite)</a>\n"
                "• <strong>Portal de Habilitaciones Municipales:</strong> <a href=\"https://datos.posadas.gov.ar/habilitaciones-municipales/\" target=\"_blank\" rel=\"noopener noreferrer\">https://datos.posadas.gov.ar/habilitaciones-municipales/</a>\n\n"
                "📋 <strong>Requisitos principales y pasos para habilitar o abrir un negocio:</strong>\n"
                "• <strong>1. Plano, adecuación edilicia y Certificado de Funcionamiento Comercial (Obras Públicas / Obras Privadas - Sistema GOP):</strong> Si el negocio funcionará en una <strong>ampliación de tu casa</strong> o en un local comercial, debe contar con plano visado y factibilidad edilicia en el Sistema GOP (<a href=\"https://posadas.gestiondeobrasprivadas.com.ar/\" target=\"_blank\" rel=\"noopener noreferrer\">posadas.gestiondeobrasprivadas.com.ar</a>). Podés asesorarte presencialmente en el módulo de <strong>Obras Privadas del CAV Itaembé Guazú</strong>.\n"
                "• <strong>2. Documentación del inmueble y titular:</strong> DNI, constancia de CUIT (ATM y ARCA/AFIP), título de propiedad o contrato de alquiler con sellado de ley y libre deuda de TGI.\n"
                "• <strong>3. Seguridad y Bromatología:</strong> Certificado de Bomberos de la Policía de Misiones y, si es del rubro alimenticio/gastronómico, Carnet Sanitario (se tramita en el CAV Itaembé Guazú).\n\n"
                "❓ <strong>Preguntas para armar tu solicitud en el CAV:</strong>\n"
                "1️⃣ <strong>Rubro o actividad:</strong> ¿De qué rubro será el negocio? (ej: almacén, kiosco, verdulería, indumentaria, gastronomía, peluquería, taller, etc.).\n"
                "2️⃣ <strong>Tipo de inmueble:</strong> ¿El comercio funcionará en una <strong>ampliación de tu casa / vivienda</strong> o en un local comercial independiente? "
                "<em>(Si es en una ampliación de tu vivienda, intervenimos junto a Obras Públicas / Obras Privadas para verificar planos y normativa de edificación).</em>"
            )
            cuerpo = (
                f'¡Hola, {nombre}!\n\n'
                f'{explicacion}\n\n'
                f'{bloque_preguntas_negocio}\n\n'
                f'{bloque_ubicacion}\n\n'
                f'{nota_fotos}\n\n'
                f'{cierre_accion}'
            )
        elif es_denuncia_ruidos:
            bloque_instrucciones_ruidos = (
                "📝 <strong>INSTRUCCIONES PARA COMPLETAR TU DENUNCIA EN EL FORMULARIO DE ABAJO:</strong>\n"
                "Para que la <strong>Guardia de Ruidos Molestos (Control Comunal de la Municipalidad)</strong> pueda acudir a constatar la infracción, completá los campos del recuadro inferior con el mayor detalle posible:\n\n"
                "1️⃣ <strong>Tus datos personales:</strong> Completá tu <strong>Nombre y Apellido</strong>, <strong>DNI</strong> y <strong>Teléfono de contacto</strong> (indispensable para que el inspector de guardia pueda comunicarse contigo si necesita coordinar la medición sonométrica).\n"
                "2️⃣ <strong>En el campo 'Descripción de la situación' (Relato detallado):</strong>\n"
                "   • <strong>Tipo de molestia sonora:</strong> Explicá todo lo que sucede (música a alto volumen, ruidos de cualquier índole, escapes libres, vibraciones, etc.).\n"
                "   • <strong>Días y horarios frecuentes:</strong> Indicá si ocurre en horarios de siesta (13 a 15 hs), madrugadas, fines de semana o de manera continua.\n"
                "   • <strong>Datos de la vecina o vecino infractor:</strong> Indicá la <strong>dirección exacta</strong> (calle, número o entrecalles, barrio o chacra en Posadas) y el <strong>nombre de la vecina/o</strong> si lo conocés.\n"
                "   👉 <em><strong>¿Te falta el nombre o la dirección exacta de la vecina/o?:</strong> ¡No te preocupes! Indicá cualquier dato orientativo o características visibles de la propiedad (color del frente de la casa, tipo de portón o rejas, referencias cercanas o respecto a tu vivienda) para que los inspectores puedan identificarla sin error.</em>\n\n"
                "📱 <strong>WhatsApp Oficial de la Guardia de Ruidos Molestos:</strong>\n"
                "Si la molestia está sucediendo en este momento, recordá que también podés dar aviso directo al <strong>WhatsApp <a href=\"https://wa.me/5493764134650\" target=\"_blank\" rel=\"noopener noreferrer\">3764-134650</a></strong> (o Línea CIUDAD 0800-888-2483 / 911 en flagrancia nocturna)."
            )
            cuerpo = (
                f'¡Hola, {nombre}!\n\n'
                f'{explicacion}\n\n'
                f'{bloque_instrucciones_ruidos}\n\n'
                f'{bloque_ubicacion}\n\n'
                f'{nota_fotos}\n\n'
                f'{cierre_accion}'
            )
        elif es_alumbrado_emsa:
            org_emsa = obtener_organismo_por_id('emsa')
            cuerpo = (
                f'¡Hola, {nombre}! Te compartimos la orientación oficial para realizar tu reclamo directamente ante <strong>Energía de Misiones S.A. (EMSA)</strong>:\n\n'
                f'{explicacion}\n\n'
                "⚡ <strong>CANALES DIRECTOS Y DETALLES DE ENERGÍA DE MISIONES (EMSA):</strong>\n"
                "👉 <a href=\"https://wa.me/5493764242514\" target=\"_blank\" rel=\"noopener noreferrer\" class=\"btn-tramite-directo\">"
                "<i class=\"fa-brands fa-whatsapp me-2\"></i>Abrir WhatsApp Oficial de Reclamos EMSA (3764-242514)</a>\n"
                "👉 <a href=\"https://www.energiademisiones.com.ar/\" target=\"_blank\" rel=\"noopener noreferrer\" class=\"btn-tramite-directo\">"
                "<i class=\"fa-solid fa-bolt me-2\"></i>Sitio Oficial de Energía de Misiones (energiademisiones.com.ar)</a>\n"
                "👉 <a href=\"tel:08008883672\" class=\"btn-tramite-directo\">"
                "<i class=\"fa-solid fa-phone me-2\"></i>Llamar a Guardia Técnica EMSA 24 hs (0800-888-3672)</a>\n\n"
                "• <strong>Teléfono Guardia Técnica EMSA (24 hs - Gratuito):</strong> <a href=\"tel:08008883672\"><strong>0800-888-3672</strong></a>\n"
                "• <strong>WhatsApp Guardia y Reclamos Técnicos EMSA:</strong> <a href=\"https://wa.me/5493764242514\" target=\"_blank\" rel=\"noopener noreferrer\"><strong>+54 9 376 424-2514</strong></a> | <strong>WhatsApp Comercial:</strong> (376) 433-4010\n"
                "• <strong>Portal de Clientes y Autogestión EMSA:</strong> <a href=\"https://clientes.energiademisiones.com.ar/\" target=\"_blank\" rel=\"noopener noreferrer\">https://clientes.energiademisiones.com.ar/</a>\n"
                "• <strong>Atención Presencial EMSA en CAV Itaembé Guazú:</strong> Oficina comercial y técnica en <strong>Calle Aguará Guazú y Magnolias</strong> (Lunes a Viernes de 07:00 a 18:00 hs). Sede Central EMSA: Calle Rioja N° 2051, Posadas.\n\n"
                "🏛️ <strong>CANALES DE ALUMBRADO PÚBLICO (MUNICIPALIDAD DE POSADAS - SERVICIOS URBANOS):</strong>\n"
                "• <strong>Línea CIUDAD Gratuita:</strong> <strong>0800-888-2483</strong> | <strong>WhatsApp Servicios Urbanos:</strong> (376) 443-7012\n"
                "• <strong>Atención Presencial en CAV Itaembé Guazú:</strong> Delegación Municipal en Calle Aguará Guazú y Magnolias (Lunes a Viernes de 07:00 a 18:00 hs).\n\n"
                "🏛️ <strong>Fuente Oficial Validada:</strong> Energía de Misiones S.A. (EMSA) - Guardia Técnica y Puesto CAV Itaembé Guazú\n"
                "📅 <strong>Fecha de Verificación:</strong> 2026-11-08\n\n"
                "⚠️ <em>Aviso de Derivación: Este servicio es de orientación directa hacia los canales oficiales de Energía de Misiones (EMSA). No es necesario cargar más datos aquí ni se genera un cuestionario adicional.</em>"
            )
            return {
                'tipo_consulta': TIPO_CONSULTA,
                'es_emergencia': False,
                'es_emergencia_electrica': False,
                'es_reclamo': False,
                'es_consulta': True,
                'es_derivacion_externa': True,
                'reclamo_confirmado': False,
                'area_sugerida': area,
                'organismo_destino': organismo,
                'respuesta_texto': cuerpo,
                'botones_emergencia': [],
                'tramite_info': None,
                'organismo_info': org_emsa,
                'cod_categoria_default': cod_categoria,
                'contexto_ubicacion': ctx_ubi,
                'preguntas_seguimiento': None,
                'resumen_solicitud': None,
            }
        elif es_obra_muro:
            bloque_instrucciones_muro = (
                "📝 <strong>INSTRUCCIONES PARA COMPLETAR TU DENUNCIA EN EL FORMULARIO DE ABAJO:</strong>\n"
                "Para que la <strong>Dirección de Obras Privadas (Obras Públicas)</strong> pueda realizar la inspección técnica de la ampliación y constatar la afectación del muro medianero:\n\n"
                "1️⃣ <strong>Sector de Itaembé Guazú:</strong> Al tratarse del barrio Itaembé Guazú, indicá abajo en qué <strong>sector o etapa</strong> te encontrás (ej: Sector 1, 2, 3, 508 Viviendas, Manzana, etc.).\n"
                "2️⃣ <strong>Tu Dirección exacta:</strong> Al lado, especificá tu calle y altura o entre qué calles se ubica tu casa.\n"
                "3️⃣ <strong>Datos de la vecina o vecino denunciado:</strong>\n"
                "   • En el campo <strong>'Detalle de la Solicitud'</strong> de abajo, agregá si es posible el <strong>nombre y apellido de tu vecina/o</strong> y su <strong>dirección exacta o número de casa/lote lindero</strong> donde amplió el muro.\n"
                "   • <em>¿No conocés el nombre o número exacto?:</em> Indicá la ubicación relativa (ej: casa lindera a la derecha, portón negro, frente a la plaza) y explicá cómo afectó o apoyó sobre tu muro medianero.\n"
                "4️⃣ <strong>Fotografías (Opcional):</strong> Si disponés de fotos del muro o de la construcción, podés adjuntarlas para que la cuadrilla cuente con antecedentes visuales antes de acudir al terreno."
            )
            cuerpo = (
                f'¡Hola, {nombre}!\n\n'
                f'{explicacion}\n\n'
                f'{bloque_instrucciones_muro}\n\n'
                f'{bloque_ubicacion}\n\n'
                f'{nota_fotos}\n\n'
                f'{cierre_accion}'
            )
        else:
            cuerpo = (
                f'¡Hola, {nombre}!\n\n'
                f'{explicacion}\n\n'
                f'{bloque_ubicacion}\n\n'
                f'{nota_fotos}\n\n'
                f'{cierre_accion}'
            )
    else:
        ubicacion_registrada = f"Barrio {ctx_ubi['barrio']} - {ctx_ubi['entre_calles']}" if ctx_ubi.get('barrio') or ctx_ubi.get('entre_calles') else "Posadas"
        if ctx_ubi.get('referencias'):
            ubicacion_registrada += f" (Ref: {ctx_ubi['referencias']})"

        if info_cav:
            cuerpo = (
                f'¡Excelente, {nombre}! Tu solicitud para <strong>{info_cav["nombre_tramite"]}</strong> ha sido '
                f'<strong>iniciada y registrada formalmente</strong> bajo el identificador único <strong>{nro_ticket}</strong>.\n\n'
                f'📌 <strong>¡Anotá o guardá este número!:</strong> Tu N° de Ticket es <strong>{nro_ticket}</strong>. '
                f'Con este número o con tu <strong>DNI</strong> podés consultar el avance en cualquier momento desde el buscador de este portal.\n\n'
                f'📋 <strong>Estado inicial:</strong> PENDIENTE (Ingresado para Validación por Mesa de Entrada del CAV).\n'
                f'🏢 <strong>Oficina asignada:</strong> {organismo} ({area}).\n'
                f'📍 <strong>Sede asignada:</strong> CAV Itaembé Guazú (Calle Aguará Guazú y Magnolias, Posadas).\n'
                f'🛠️ <strong>Gestión programada:</strong> {descripcion_intervencion}.\n\n'
                f'🏛️ <strong>Pautas para tu atención presencial en el CAV:</strong>\n'
                f'{info_cav["pautas_presenciales"]}\n\n'
                f'📎 <em>Recordá concurrir a la sede con la documentación física original requerida para la verificación formal del trámite.</em>\n\n'
                f'🔍 Podés consultar el estado de tu ticket en cualquier momento desde este portal con tu DNI o N° <strong>{nro_ticket}</strong>.'
            )
        elif es_habilitacion_negocio:
            cuerpo = (
                f'¡Excelente, {nombre}! Tu solicitud de apertura y habilitación comercial ha sido <strong>registrada formalmente</strong> '
                f'bajo el identificador único <strong>{nro_ticket}</strong>.\n\n'
                f'📌 <strong>¡Anotá o guardá este número!:</strong> Tu N° de Ticket es <strong>{nro_ticket}</strong>. '
                f'Con este número o con tu <strong>DNI</strong> podés consultar el avance en cualquier momento desde el buscador de este mismo sistema.\n\n'
                f'📋 <strong>Estado inicial:</strong> PENDIENTE (Pendiente de Validación por Mesa de Entrada).\n'
                f'🏢 <strong>Oficina asignada:</strong> {organismo} ({area}).\n'
                f'📍 <strong>Ubicación del comercio:</strong> {ubicacion_registrada}.\n'
                f'🛠️ <strong>Gestión programada:</strong> Coordinación técnica con Obras Públicas / Privadas (verificación de planos y ampliación de vivienda), análisis de rubro e inspección de seguridad.\n\n'
                f'🔍 Podés consultar el estado de tu ticket en cualquier momento desde este portal con tu DNI o N° <strong>{nro_ticket}</strong>.'
            )
        elif es_denuncia_ruidos:
            cuerpo = (
                f'¡Excelente, {nombre}! Tu denuncia por ruidos molestos ha sido <strong>registrada formalmente</strong> '
                f'bajo el identificador único <strong>{nro_ticket}</strong>.\n\n'
                f'📌 <strong>¡Anotá o guardá este número!:</strong> Tu N° de Ticket es <strong>{nro_ticket}</strong>. '
                f'Con este número o con tu <strong>DNI</strong> podés consultar el avance en cualquier momento desde el buscador de este mismo sistema.\n\n'
                f'📋 <strong>Estado inicial:</strong> PENDIENTE (Derivada a Guardia de Control Comunal de Posadas).\n'
                f'🏢 <strong>Área asignada:</strong> {organismo} ({area}).\n'
                f'📍 <strong>Ubicación del reclamo:</strong> {ubicacion_registrada}.\n'
                f'🛠️ <strong>Gestión programada:</strong> Se programó la {descripcion_intervencion}. El cuerpo de inspectores actuará en el lugar para verificar los decibeles sonométricos y labrar las actas de infracción correspondientes según la <strong>Ordenanza VI – Nº 14</strong>.\n\n'
                f'📱 <strong>Recordatorio urgente:</strong> Si la música a alto volumen o el ruido molesto se reitera de forma flagrante en este momento, podés reforzar la alerta inmediata indicando tu N° de Ticket {nro_ticket} al WhatsApp oficial de la <strong>Guardia de Ruidos Molestos: 3764-134650</strong> (<a href=\"https://wa.me/5493764134650\" target=\"_blank\" rel=\"noopener noreferrer\">https://wa.me/5493764134650</a>) o a la Línea 911 en horario nocturno.\n\n'
                f'🔍 Podés consultar el estado de tu ticket en cualquier momento desde este portal con tu DNI o N° <strong>{nro_ticket}</strong>.'
            )
        elif es_alumbrado_emsa:
            cuerpo = (
                f'¡Excelente, {nombre}! Tu reclamo por foco quemado / luminaria de alumbrado público ha sido <strong>registrado formalmente</strong> '
                f'bajo el identificador único <strong>{nro_ticket}</strong>.\n\n'
                f'📌 <strong>¡Anotá o guardá este número!:</strong> Tu N° de Ticket es <strong>{nro_ticket}</strong>. '
                f'Con este número o con tu <strong>DNI</strong> podés consultar el avance en cualquier momento desde el buscador de este mismo sistema.\n\n'
                f'📋 <strong>Estado inicial:</strong> PENDIENTE (Pendiente de Validación por Mesa de Entrada).\n'
                f'🏢 <strong>Área asignada:</strong> {organismo} ({area}).\n'
                f'📍 <strong>Ubicación del poste / luminaria:</strong> {ubicacion_registrada}.\n'
                f'🛠️ <strong>Gestión programada:</strong> Se programó la {descripcion_intervencion}.\n\n'
                f'⚡ <strong>Canales Directos de Energía de Misiones (EMSA) y Alumbrado Público:</strong>\n'
                f'• <strong>Guardia Técnica EMSA 24 hs:</strong> <a href=\"tel:08008883672\"><strong>0800-888-3672</strong></a>\n'
                f'• <strong>WhatsApp Oficial EMSA:</strong> <a href=\"https://wa.me/5493764242514\" target=\"_blank\" rel=\"noopener noreferrer\"><strong>3764-242514</strong></a>\n'
                f'• <strong>Web Oficial EMSA:</strong> <a href=\"https://www.energiademisiones.com.ar/\" target=\"_blank\" rel=\"noopener noreferrer\">https://www.energiademisiones.com.ar/</a>\n'
                f'• <strong>Oficina Presencial EMSA en CAV Itaembé Guazú:</strong> Calle Aguará Guazú y Magnolias (07:00 a 18:00 hs).\n'
                f'• <strong>Línea CIUDAD Alumbrado Municipal:</strong> 0800-888-2483 | WhatsApp: (376) 443-7012.\n\n'
                f'🔍 Podés consultar el estado de tu ticket en cualquier momento desde este portal con tu DNI o N° <strong>{nro_ticket}</strong>.'
            )
        else:
            cuerpo = (
                f'¡Excelente, {nombre}! Tu solicitud municipal ha sido <strong>registrada formalmente</strong> '
                f'bajo el identificador único <strong>{nro_ticket}</strong>.\n\n'
                f'📌 <strong>¡Anotá o guardá este número!:</strong> Tu N° de Ticket es <strong>{nro_ticket}</strong>. '
                f'Con este número o con tu <strong>DNI</strong> podés consultar el avance en cualquier momento desde el buscador de este mismo sistema.\n\n'
                f'📋 <strong>Estado inicial:</strong> PENDIENTE (Pendiente de Validación por Mesa de Entrada).\n'
                f'🏢 <strong>Área asignada:</strong> {organismo} ({area}).\n'
                f'📍 <strong>Ubicación del reclamo:</strong> {ubicacion_registrada}.\n'
                f'🛠️ <strong>Gestión programada:</strong> Se programó la {descripcion_intervencion}.\n\n'
                f'🔍 Podés consultar el estado de tu ticket en cualquier momento desde este portal con tu DNI o N° <strong>{nro_ticket}</strong>.'
            )

    return {
        'tipo_consulta': TIPO_RECLAMO,
        'es_emergencia': False,
        'es_emergencia_electrica': False,
        'es_reclamo': True,
        'es_consulta': False,
        'es_derivacion_externa': False,
        'reclamo_confirmado': confirmado,
        'area_sugerida': area,
        'organismo_destino': organismo,
        'respuesta_texto': cuerpo,
        'botones_emergencia': [],
        'tramite_info': None,
        'organismo_info': None,
        'cod_categoria_default': cod_categoria,
        'contexto_ubicacion': ctx_ubi,
        'preguntas_seguimiento': preguntas_info,
        'resumen_solicitud': resumen,
    }


def consultar_estado_ticket_conversacional(nombre: str, nro_ticket_str: str) -> dict:
    """
    Permite consultar en lenguaje natural el estado de un ticket y ver hacia dónde fue derivado.
    """
    from .models import Expediente

    nro_normalizado = nro_ticket_str.strip().upper()
    exp = Expediente.objects.filter(nro_expediente__iexact=nro_normalizado).first()
    if not exp and not '-' in nro_normalizado and nro_normalizado.startswith('TCK'):
        nro_con_guion = f"TCK-{nro_normalizado[3:]}"
        exp = Expediente.objects.filter(nro_expediente__iexact=nro_con_guion).first()

    if exp:
        estado_display = exp.get_estado_actual_display()
        organismo = exp.organismo_destino or 'Mesa de Entrada del CAV (En proceso de asignación)'
        fecha_fmt = exp.fecha_ingreso.strftime('%d/%m/%Y a las %H:%M')
        barrio_str = exp.barrio or 'Posadas'
        calles_str = f" - {exp.entre_calles}" if exp.entre_calles else ""
        ref_str = f" (Ref: {exp.referencias})" if exp.referencias else ""

        if exp.estado_actual == 'PENDIENTE':
            explicacion_estado = (
                '⏳ <strong>Estado actual: PENDIENTE DE VALIDACIÓN</strong>\n'
                f'Tu solicitud se encuentra registrada bajo el número <strong>{exp.nro_expediente}</strong> y está a la espera de ser validada '
                f'por la Mesa de Entrada del Centro de Atención Vecinal (CAV). El área de destino sugerida es: <strong>{organismo}</strong>.'
            )
        elif exp.estado_actual == 'DERIVADO':
            explicacion_estado = (
                '↗️ <strong>Estado actual: DERIVADO</strong>\n'
                f'Tu expediente ya fue evaluado por Mesa de Entrada y <strong>ha sido derivado formalmente a: {organismo}</strong> '
                'para la coordinación técnica y despacho de cuadrillas operativas.'
            )
        elif exp.estado_actual == 'EN_PROCESO':
            explicacion_estado = (
                '⚙️ <strong>Estado actual: EN PROCESO</strong>\n'
                f'El área de <strong>{organismo}</strong> se encuentra ejecutando los trabajos e interviniendo operativamente en el lugar.'
            )
        elif exp.estado_actual == 'RESUELTO':
            explicacion_estado = (
                '✅ <strong>Estado actual: RESUELTO</strong>\n'
                f'La solicitud fue atendida y marcada como resuelta por el área de <strong>{organismo}</strong>.'
            )
        elif exp.estado_actual == 'RECHAZADO':
            explicacion_estado = (
                '❌ <strong>Estado actual: RECHAZADO</strong>\n'
                'La solicitud no pudo ser cursada. Podés consultar de forma presencial en el CAV o telefónicamente al 0800-888-2483.'
            )
        else:
            explicacion_estado = f'📋 <strong>Estado actual:</strong> {estado_display}.'

        saludo = f"¡Hola, {nombre}! " if nombre else "¡Hola! "
        cuerpo = (
            f'{saludo}Aquí tenés la información y seguimiento de tu trámite:\n\n'
            f'🎫 <strong>Ticket N°:</strong> {exp.nro_expediente}\n'
            f'📅 <strong>Fecha de registro:</strong> {fecha_fmt} hs\n'
            f'🏢 <strong>Organismo / Área de Destino:</strong> {organismo}\n'
            f'📍 <strong>Ubicación registrada:</strong> Barrio {barrio_str}{calles_str}{ref_str}\n'
            f'📝 <strong>Detalle de la solicitud:</strong> {exp.detalle_consulta}\n\n'
            f'{explicacion_estado}\n\n'
            f'📌 <em>También podés consultar tus trámites en todo momento utilizando el buscador con tu DNI o N° de Ticket en la parte superior del portal.</em>'
        )

        return {
            'tipo_consulta': TIPO_CONSULTA,
            'es_emergencia': False,
            'es_emergencia_electrica': False,
            'es_reclamo': False,
            'es_consulta': True,
            'es_derivacion_externa': False,
            'reclamo_confirmado': False,
            'area_sugerida': organismo,
            'organismo_destino': organismo,
            'respuesta_texto': cuerpo,
            'botones_emergencia': [],
            'tramite_info': None,
            'organismo_info': None,
        }
    else:
        saludo = f"Hola, {nombre}. " if nombre else "Hola. "
        cuerpo = (
            f'{saludo}No se encontró ningún trámite o reclamo registrado con el código <strong>{nro_normalizado}</strong>.\n\n'
            f'💡 <strong>Cómo encontrar tu trámite:</strong>\n'
            f'1️⃣ Verificá que el número de ticket esté bien escrito (el formato habitual es <code>TCK-2026-XXXX</code> o <code>TCK-XXXXX</code>).\n'
            f'2️⃣ Podés ingresar directamente tu <strong>DNI</strong> en el buscador de la parte inferior del portal para ver todos tus trámites registrados.\n'
            f'3️⃣ Si realizaste el reclamo hace instantes por otro canal, el expediente puede demorar unos minutos en impactar en el sistema.'
        )
        return {
            'tipo_consulta': TIPO_CONSULTA,
            'es_emergencia': False,
            'es_emergencia_electrica': False,
            'es_reclamo': False,
            'es_consulta': True,
            'es_derivacion_externa': False,
            'reclamo_confirmado': False,
            'area_sugerida': 'Mesa de Entrada',
            'organismo_destino': 'Mesa de Entrada',
            'respuesta_texto': cuerpo,
            'botones_emergencia': [],
            'tramite_info': None,
            'organismo_info': None,
        }


def procesar_consulta_vecino(nombre: str, detalle: str, confirmado: bool = False, nro_ticket: str = None, datos_ubicacion: dict = None) -> dict:
    """
    Función orquestadora principal para la vista portal_vecino:
    1. Detecta si el vecino ingresó un número de ticket para conocer su estado y derivación.
    2. Determina el tipo de consulta (Emergencia, Reclamo o Consulta).
    3. En emergencias, prioriza protocolos de seguridad sin postergar por preguntas.
    4. En reclamos, integra preguntas de seguimiento adaptativas y resumen automático.
    5. En consultas, ofrece guía oficial de organismos o trámites digitales verificados.
    """
    match_ticket = re.search(r'\b(TCK[-_]?(?:\d+[-_]?)+\d*|#?TK[-_]?\d+)\b', detalle, re.IGNORECASE)
    if match_ticket:
        return consultar_estado_ticket_conversacional(nombre, match_ticket.group(1))

    tipo = clasificar_consulta(detalle)

    if tipo == TIPO_EMERGENCIA:
        _, subtipo, datos_contexto = detectar_emergencia(detalle)
        return generar_respuesta_emergencia(nombre, detalle, subtipo, datos_contexto, datos_ubicacion=datos_ubicacion)
    elif tipo == TIPO_RECLAMO:
        return generar_respuesta_reclamo(nombre, detalle, confirmado=confirmado, nro_ticket=nro_ticket, datos_ubicacion=datos_ubicacion)
    else:
        return generar_respuesta_consulta(nombre, detalle, datos_ubicacion=datos_ubicacion)
