"""
Módulo de Conversación Inteligente, Contexto y Preguntas de Seguimiento.
Sistema SIGEV - Municipalidad de Posadas.

Funcionalidades:
- Extracción de contexto territorial en Posadas (Barrio, entre calles, referencias).
- Memoria del contexto durante la conversación (no repite preguntas ya respondidas).
- Generación de preguntas de seguimiento adaptativas según la información faltante.
- Construcción de resumen estructurado previo a la confirmación de la solicitud.
- Medidas de seguridad: nunca posterga advertencias de emergencia por preguntas.
"""

import re

BARRIOS_POSADAS_CONOCIDOS = [
    'villa sarita', 'itaembe guazu', 'itaembe mini', 'villa cabello', 'santa rita',
    'centro', 'san lorenzo', 'miguel lanus', 'el palomar', 'palomar', 'riberas del parana',
    'cocomarola', 'cocomarola este', 'cocomarola oeste', 'los paraisos', 'santa clara',
    'aguas corrientes', 'yacyreta', 'san onofre', 'las dolores', 'a4', 'a-4', 'prosol',
    'nemesio parma', 'parque adam', 'villa urquiza', 'el chaquito', 'villa blosset',
    'chacra 32-33', 'chacra 149', 'chacra 181', 'los alamos', 'sol de misiones',
    'san jorge', 'aeroclub', 'san marcos', 'terrazas', 'don pedro', 'belgrano'
]


def normalizar_texto_simple(texto: str) -> str:
    """Normaliza texto a minúsculas y elimina tildes para búsqueda."""
    t = texto.lower()
    for o, d in [('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u'), ('ü', 'u'), ('ñ', 'n')]:
        t = t.replace(o, d)
    return t


def extraer_contexto_ubicacion(texto: str, datos_existentes: dict = None) -> dict:
    """
    Analiza el texto de la consulta o respuestas y extrae información territorial de Posadas:
    - barrio: Barrio, Chacra o zona de Posadas.
    - entre_calles: Altura, intersección o entre qué calles.
    - referencias: Lugares de referencia cercanos (escuela, plaza, comercio).
    
    Respeta datos ya informados previamente (no los sobrescribe si ya fueron validados).
    """
    ctx = {
        'barrio': '',
        'entre_calles': '',
        'referencias': ''
    }
    if datos_existentes:
        ctx['barrio'] = datos_existentes.get('barrio', '').strip()
        ctx['entre_calles'] = datos_existentes.get('entre_calles', '').strip()
        ctx['referencias'] = datos_existentes.get('referencias', '').strip()

    t_norm = normalizar_texto_simple(texto)

    # 1. Extracción de Barrio si aún no está definido
    if not ctx['barrio']:
        # Búsqueda por barrios conocidos de Posadas
        for b in BARRIOS_POSADAS_CONOCIDOS:
            if re.search(r'\b' + re.escape(b) + r'\b', t_norm):
                ctx['barrio'] = b.title()
                break

        # Búsqueda por patrón "barrio X" o "chacra N"
        if not ctx['barrio']:
            m_barrio = re.search(r'\bbarrio\s+([a-zA-Z0-9ÁÉÍÓÚñÑüÜ\s\-]{2,30}?)(?:,|\.|\bentre\b|\bcalle\b|\besquina\b|\bfrente\b|$)', texto, re.IGNORECASE)
            if m_barrio:
                ctx['barrio'] = m_barrio.group(1).strip().title()

        if not ctx['barrio']:
            m_chacra = re.search(r'\b(chacra|ch\.?)\s*(\d+(?:[-\/]\d+)?)\b', texto, re.IGNORECASE)
            if m_chacra:
                ctx['barrio'] = f"Chacra {m_chacra.group(2)}"

    # 2. Extracción de entre calles / altura si aún no está definido
    if not ctx['entre_calles']:
        m_entre = re.search(r'\bentre\s+([^,.;\n]+?)\s+y\s+([^,.;\n]+)', texto, re.IGNORECASE)
        if m_entre:
            ctx['entre_calles'] = f"Entre {m_entre.group(1).strip()} y {m_entre.group(2).strip()}"
        else:
            m_esquina = re.search(r'\besquina\s+([^,.;\n]+)', texto, re.IGNORECASE)
            if m_esquina:
                ctx['entre_calles'] = f"Esquina {m_esquina.group(1).strip()}"
            else:
                m_sobre = re.search(r'\b(?:sobre|en la calle|calle|av(?:enida)?\.?)\s+([^,.;\n]{3,40})(?:\s+(?:al|nro|numero)?\s*(\d+))?', texto, re.IGNORECASE)
                if m_sobre:
                    calle = m_sobre.group(1).strip()
                    altura = m_sobre.group(2)
                    ctx['entre_calles'] = f"{calle} {altura}" if altura else calle

    # 3. Extracción de referencias si aún no está definido
    if not ctx['referencias']:
        m_ref = re.search(r'\b(frente a(?:l)?\s+[^,.;\n]+|cerca de(?:l)?\s+[^,.;\n]+|al lado de(?:l)?\s+[^,.;\n]+|a \d+ metros de(?:l)?\s+[^,.;\n]+|pegado a(?:l)?\s+[^,.;\n]+)', texto, re.IGNORECASE)
        if m_ref:
            ctx['referencias'] = m_ref.group(1).strip().capitalize()

    return ctx


def generar_preguntas_seguimiento(tipo_problema: str, contexto: dict, es_poste_o_cable: bool = False) -> dict:
    """
    Genera preguntas de seguimiento adaptativas y precisas para la información faltante.
    - Si el vecino ya aportó el dato, no lo vuelve a preguntar.
    - Si se trata de un poste o infraestructura, advierte no acercarse al sacar fotos.
    """
    barrio = contexto.get('barrio')
    entre_calles = contexto.get('entre_calles')
    referencias = contexto.get('referencias')

    faltantes = []
    preguntas_texto = []

    if not barrio:
        faltantes.append('barrio')
        preguntas_texto.append('📍 ¿En qué barrio o chacra de Posadas se encuentra?')

    if not entre_calles:
        faltantes.append('entre_calles')
        if barrio:
            preguntas_texto.append(f'🛣️ ¿Podrías indicarnos entre qué calles o a qué altura del barrio {barrio} se ubica?')
        else:
            preguntas_texto.append('🛣️ ¿Entre qué calles, sobre qué avenida o a qué altura se localiza?')

    if not referencias:
        faltantes.append('referencias')
        preguntas_texto.append('🔍 ¿Disponés de alguna referencia cercana (ej.: frente a una plaza, escuela o comercio)?')

    # Recomendación sobre fotografías con protocolo de seguridad
    if es_poste_o_cable:
        nota_fotos = '📷 Si disponés de fotografías podés adjuntarlas más abajo. Por tu seguridad, recordá NO acercarte si existiera algún riesgo o cable cercano.'
    else:
        nota_fotos = '📷 Si disponés de una foto del inconveniente podés adjuntarla abajo para facilitar la inspección de la cuadrilla.'

    tiene_todo = (len(faltantes) == 0)

    return {
        'faltantes': faltantes,
        'preguntas_texto': preguntas_texto,
        'nota_fotos': nota_fotos,
        'informacion_completa': tiene_todo,
        'barrio_actual': barrio,
        'entre_calles_actual': entre_calles,
        'referencias_actual': referencias
    }


def generar_resumen_automatico(nombre_vecino: str, detalle_problema: str, contexto: dict, organismo_sugerido: str) -> dict:
    """
    Construye la ficha de resumen estructurado previa a la confirmación de la solicitud.
    Permite que el vecino revise, complete o corrija datos antes de dar de alta el ticket.
    """
    barrio = contexto.get('barrio') or 'A precisar por el vecino'
    entre_calles = contexto.get('entre_calles') or 'A precisar por el vecino'
    referencias = contexto.get('referencias') or 'Sin referencias adicionales'

    return {
        'tipo_solicitud': 'Reclamo Operativo Municipal',
        'vecino': nombre_vecino,
        'descripcion': detalle_problema,
        'barrio': barrio,
        'entre_calles': entre_calles,
        'referencias': referencias,
        'organismo_competente': organismo_sugerido,
        'datos_completos': bool(contexto.get('barrio') and contexto.get('entre_calles'))
    }

