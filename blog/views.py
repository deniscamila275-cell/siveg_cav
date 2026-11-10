"""
================================================================================
CAPA DE CONTROL Y LÓGICA DE NEGOCIO (VIEWS / MÉTODOS CONTROLADORES)
================================================================================
OBJETIVO DEL PROYECTO:
    Sistema Integrado de Vecinos y Gestión (SIVEG / SIGEV Posadas).
    Orquesta la interacción entre la Interfaz Gráfica (Templates HTML),
    los Modelos de Datos (Base de Datos) y la lógica de negocio para la
    atención ciudadana municipal y articulación con sedes como el CAV Itaembé Guazú.

CONEXIÓN Y PERSISTENCIA EN BASE DE DATOS:
    Las vistas no ejecutan SQL directo; interactúan con el ORM de Django
    (Object-Relational Mapping). Aquí se realizan las operaciones CRUD:
    - Create: Instanciación de objetos y persistencia (Model.objects.create(...) o obj.save()).
    - Read: Consultas y filtros sobre columnas (Model.objects.filter(...), .all(), .get()).
    - Update: Modificación de atributos de la instancia y persistencia (obj.save()).
    - Delete: Eliminación de registros (obj.delete()).

GUÍA DE ARQUITECTURA - CÓMO AGREGAR UNA NUEVA PANTALLA / VISTA AL SISTEMA:
    1. Definir el método controlador aquí en views.py:
       def nueva_pantalla(request):
           # Lógica, obtención de objetos y datos de contexto
           contexto = {'titulo': 'Nueva Sección'}
           return render(request, 'blog/nueva_pantalla.html', contexto)
    2. Registrar la ruta en blog/urls.py:
       path('nueva-pantalla/', views.nueva_pantalla, name='nueva_pantalla')
    3. Crear la plantilla visual en blog/templates/blog/nueva_pantalla.html.
================================================================================
"""

import datetime
import random
import re
from django.shortcuts import render
from django.db.models import Q
from django.utils import timezone
from .models import Expediente, CategoriaReclamo, RegistroConsulta, SugerenciaOrganismo
from .organismos import buscar_organismo_existente
from .asistente import (
    procesar_consulta_vecino,
    resolver_tramite_cav_itaembe,
    TIPO_EMERGENCIA,
    TIPO_RECLAMO,
    TIPO_CONSULTA,
)
from .conversacion import extraer_contexto_ubicacion


# ==============================================================================
# MÉTODOS AUXILIARES DE LÓGICA DE NEGOCIO
# ==============================================================================

def generar_siguiente_nro_ticket() -> str:
  """
  MÉTODO / FUNCIÓN DE NEGOCIO:
  Genera el siguiente número de ticket correlativo anual (Opción 3: TCK-YYYY-XXXX).
  Ej: TCK-2026-0001, TCK-2026-0002, TCK-2026-0003...
  
  CONSULTA A BASE DE DATOS (ORM):
  Consulta la columna 'nro_expediente' en la tabla de la clase Expediente utilizando
  los métodos de consulta filter() y values_list() para obtener el último correlativo.
  """
  anio_actual = timezone.now().strftime('%Y')
  prefijo = f'TCK-{anio_actual}-'
  # Consulta ORM: proyecta solo la columna 'nro_expediente'
  expedientes_anio = Expediente.objects.filter(nro_expediente__startswith=prefijo).values_list('nro_expediente', flat=True)

  max_num = 0
  for nro in expedientes_anio:
    partes = nro.split('-')
    if len(partes) >= 3 and partes[-1].isdigit():
      try:
        max_num = max(max_num, int(partes[-1]))
      except ValueError:
        pass

  siguiente_num = max_num + 1
  nuevo_ticket = f"{prefijo}{siguiente_num:04d}"
  while Expediente.objects.filter(nro_expediente=nuevo_ticket).exists():
    siguiente_num += 1
    nuevo_ticket = f"{prefijo}{siguiente_num:04d}"
  return nuevo_ticket


def validar_datos_vecino(nombre: str, dni: str, telefono: str):
  """
  MÉTODO DE VALIDACIÓN E INTEGRIDAD:
  Valida y normaliza rigurosamente los datos del vecino según la normativa de Posadas / Misiones:
  1. Nombre y Apellido: obligatorio ingresar ambos (al menos 2 palabras), solo letras y espacios, sin textos vacíos ni caracteres idénticos repetidos.
  2. DNI: debe contener exactamente 8 números (sin puntos ni letras, ej: 36268087).
  3. Teléfono: debe corresponder a Posadas o la provincia (inicia con 37 + 2 dígitos de característica, seguido opcionalmente de 15 y número de abonado, ej: 3764187444 o 3764-15-187444).
  """
  nombre = nombre.strip()
  if not nombre:
    return False, 'Por favor, completá todos los campos para poder asesorarte.', None
  if not re.fullmatch(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$', nombre):
    return False, 'El nombre y apellido solo debe contener letras.', None
  partes_nombre = [p for p in nombre.split() if len(p) >= 2]
  if len(partes_nombre) < 2:
    return False, 'Por favor, ingresá tu nombre y apellido completo (al menos un nombre y un apellido, ej: Juan Pérez).', None
  if any(len(set(p.lower())) < 2 for p in partes_nombre):
    return False, 'Por favor, ingresá un nombre y apellido válido y real.', None

  dni = dni.strip()
  if not dni:
    return False, 'Por favor, completá todos los campos para poder asesorarte.', None
  if not dni.isdigit():
    return False, 'El DNI solo debe contener números.', None
  if len(dni) != 8:
    return False, 'El DNI debe contener exactamente 8 números (sin puntos ni letras, ej: 36268087).', None

  telefono_raw = telefono.strip()
  if not telefono_raw:
    return False, 'Por favor, completá todos los campos para poder asesorarte.', None
  if re.search(r'[a-zA-Z]', telefono_raw):
    return False, 'El teléfono de contacto solo debe contener números.', None

  digitos = re.sub(r'\D', '', telefono_raw)
  if digitos.startswith('549'):
    digitos = digitos[3:]
  elif digitos.startswith('54'):
    digitos = digitos[2:]
  if digitos.startswith('0'):
    digitos = digitos[1:]

  if not digitos.startswith('37'):
    return False, 'El teléfono debe corresponder a Posadas o la provincia (debe comenzar con la característica 37, ej: 3764187444 o 3764-15-187444).', None

  tel_norm = None
  if len(digitos) == 10:
    tel_norm = digitos
  elif len(digitos) == 12 and digitos[4:6] == '15':
    tel_norm = digitos[:4] + digitos[6:]
  elif len(digitos) == 12 and digitos[3:5] == '15':
    tel_norm = digitos[:3] + digitos[5:]
  elif len(digitos) == 11 and (digitos[4:6] == '15' or digitos[3:5] == '15'):
    tel_norm = digitos[:4] + digitos[6:] if digitos[4:6] == '15' else digitos[:3] + digitos[5:]

  if not tel_norm or len(tel_norm) != 10:
    return False, 'El formato del teléfono debe contener la característica 37 y su número (ej: 3764187444 o 3764-15-187444).', None

  return True, None, {'nombre': nombre, 'dni': dni, 'telefono': tel_norm}

  return True, '', {'nombre': nombre, 'dni': dni, 'telefono': tel_norm}


def validar_datos_sugerente(nombre: str, telefono: str):
  """
  Valida que los datos del vecino al sugerir un organismo sean obligatorios y válidos:
  - Nombre y apellido completo (solo letras).
  - Teléfono de contacto de Posadas/provincia (inicia con 37).
  """
  nombre = nombre.strip()
  if not nombre:
    return False, 'Por favor, ingresá tu nombre y apellido (es obligatorio).', None
  if not re.fullmatch(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$', nombre):
    return False, 'El nombre y apellido solo debe contener letras.', None
  partes = [p for p in nombre.split() if len(p) >= 2]
  if len(partes) < 2:
    return False, 'Por favor, ingresá tu nombre y apellido completo (al menos un nombre y un apellido, ej: Camila Denis).', None

  telefono_raw = telefono.strip()
  if not telefono_raw:
    return False, 'Por favor, ingresá tu teléfono de contacto (es obligatorio).', None
  if re.search(r'[a-zA-Z]', telefono_raw):
    return False, 'El teléfono de contacto solo debe contener números.', None

  digitos = re.sub(r'\D', '', telefono_raw)
  if digitos.startswith('549'):
    digitos = digitos[3:]
  elif digitos.startswith('54'):
    digitos = digitos[2:]
  if digitos.startswith('0'):
    digitos = digitos[1:]

  if not digitos.startswith('37'):
    return False, 'El teléfono debe corresponder a Posadas o la provincia (debe comenzar con la característica 37, ej: 3764187444 o 3764-15-187444).', None

  tel_norm = None
  if len(digitos) == 10:
    tel_norm = digitos
  elif len(digitos) == 12 and digitos[4:6] == '15':
    tel_norm = digitos[:4] + digitos[6:]
  elif len(digitos) == 12 and digitos[3:5] == '15':
    tel_norm = digitos[:3] + digitos[5:]
  elif len(digitos) == 11 and (digitos[4:6] == '15' or digitos[3:5] == '15'):
    tel_norm = digitos[:4] + digitos[6:] if digitos[4:6] == '15' else digitos[:3] + digitos[5:]

  if not tel_norm or len(tel_norm) != 10:
    return False, 'El formato del teléfono debe contener la característica 37 y su número (ej: 3764187444 o 3764-15-187444).', None

  return True, '', {'nombre': nombre, 'telefono': tel_norm}


# ==============================================================================
# MÉTODO CONTROLADOR PRINCIPAL / VISTA DE INTERFAZ GRÁFICA: portal_vecino
# Recibe la petición HTTP (request), interactúa con los Modelos (Base de Datos)
# y retorna el template renderizado con el diccionario de contexto.
# ==============================================================================
def portal_vecino(request):
  contexto = {}

  if request.method == 'POST':
    # CASO: Sugerencia de nuevo organismo o entidad presente en el CAV
    if 'btn_sugerir_organismo' in request.POST:
      texto_sug = request.POST.get('sugerencia_organismo', '').strip()
      nombre_sug = request.POST.get('nombre_sugerente', '').strip()
      contacto_sug = request.POST.get('contacto_sugerente', '').strip()

      if not texto_sug:
        contexto.update({
            'error_sugerencia': 'Por favor, escribí el nombre o detalle del organismo o entidad que te gustaría agregar (campo obligatorio).',
            'sugerencia_previa': texto_sug,
            'nombre_sug_previo': nombre_sug,
            'contacto_sug_previo': contacto_sug,
        })
        return render(request, 'blog/portal_vecino.html', contexto)

      if not nombre_sug or not contacto_sug:
        contexto.update({
            'error_sugerencia': 'Por favor, completá tu nombre y apellido, y tu teléfono de contacto (ambos son obligatorios).',
            'sugerencia_previa': texto_sug,
            'nombre_sug_previo': nombre_sug,
            'contacto_sug_previo': contacto_sug,
        })
        return render(request, 'blog/portal_vecino.html', contexto)

      es_valido, msg_error, datos_sug = validar_datos_sugerente(nombre_sug, contacto_sug)
      if not es_valido:
        contexto.update({
            'error_sugerencia': msg_error,
            'sugerencia_previa': texto_sug,
            'nombre_sug_previo': nombre_sug,
            'contacto_sug_previo': contacto_sug,
        })
        return render(request, 'blog/portal_vecino.html', contexto)

      # Verificar si el organismo propuesto ya existe en el sistema oficial
      org_existente = buscar_organismo_existente(texto_sug)
      if org_existente:
        contexto.update({
            'sugerencia_ya_existe': True,
            'organismo_existente': org_existente,
            'nombre_sugerente': datos_sug['nombre'],
            'mensaje_existente': (
                f"El organismo o entidad '{org_existente['nombre']}' ({org_existente['sigla']}) "
                f"ya se encuentra incorporado en el sistema SIVEG{' y cuenta con atención en el Centro de Atención Vecinal (CAV)' if org_existente.get('presente_cav_itaembe') else ''}."
            ),
        })
        return render(request, 'blog/portal_vecino.html', contexto)

      # --- POO: INSTANCIACIÓN DE OBJETO Y PERSISTENCIA EN BD (Clase SugerenciaOrganismo) ---
      # Se instancia un nuevo objeto en memoria con los atributos provistos y se guarda en la tabla:
      SugerenciaOrganismo.objects.create(
          texto_sugerencia=texto_sug,
          nombre_vecino=datos_sug['nombre'],
          contacto=datos_sug['telefono'],
      )
      contexto.update({
          'sugerencia_enviada': True,
          'mensaje_sugerencia': (
              f"¡Muchas gracias {datos_sug['nombre']}! Tu propuesta fue registrada con éxito para la coordinación del Centro de Atención Vecinal (CAV)."
          ),
      })
      return render(request, 'blog/portal_vecino.html', contexto)


    # ==============================================================================
    # CONCEPTO POO: ACTUALIZACIÓN DE ESTADO EN INSTANCIA (Requisito 8: Auditoría y Métricas)
    # Método controlador que recupera la instancia de la clase RegistroConsulta y
    # persiste la evaluación ciudadana (columna evaluacion_vecino) en la base de datos.
    # ==============================================================================
    if 'btn_evaluar_consulta' in request.POST:
      id_consulta = request.POST.get('id_consulta', '').strip()
      evaluacion = request.POST.get('evaluacion', '').strip().upper()
      if evaluacion not in ['SI', 'PARCIAL', 'NO']:
        evaluacion = 'SI'

      reg = RegistroConsulta.objects.filter(identificador_consulta=id_consulta).first() if id_consulta else None
      nro_ticket_post = request.POST.get('nro_ticket', '').strip()
      detalle_post = request.POST.get('detalle_consulta', '').strip()
      barrio_post = request.POST.get('barrio_vecino', '').strip()

      if not reg and detalle_post:
        if not id_consulta:
          id_consulta = f"CNS-{timezone.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        exp_asoc = Expediente.objects.filter(nro_expediente=nro_ticket_post).first() if nro_ticket_post else None
        res_temp = procesar_consulta_vecino(
            nombre=request.POST.get('nombre_vecino', '').strip(),
            detalle=detalle_post,
            confirmado=bool(exp_asoc),
            nro_ticket=exp_asoc.nro_expediente if exp_asoc else None,
            datos_ubicacion={'barrio': barrio_post},
        )
        try:
          reg = RegistroConsulta.objects.create(
              identificador_consulta=id_consulta,
              tipo_consulta=res_temp['tipo_consulta'],
              categoria=res_temp.get('area_sugerida') or res_temp.get('organismo_destino') or 'General',
              texto_consultado=detalle_post,
              respuesta_brindada=res_temp['respuesta_texto'],
              fuente_informacion='Base de Conocimiento Oficial SIGEV',
              resultado='TICKET_REGISTRADO' if exp_asoc else 'ASESORAMIENTO',
              ticket_asociado=exp_asoc,
              barrio_detectado=barrio_post,
          )
        except Exception:
          reg = RegistroConsulta.objects.order_by('-id').first()

      if reg:
        # Mutación de atributos de la instancia y persistencia ORM:
        reg.evaluacion_vecino = evaluacion
        reg.fecha_evaluacion = timezone.now()
        reg.save()

        eval_exp = reg.ticket_asociado
        if not eval_exp and nro_ticket_post:
          eval_exp = Expediente.objects.filter(nro_expediente=nro_ticket_post).first()

        if eval_exp:
          eval_nombre = eval_exp.nombre_completo
          eval_dni = str(eval_exp.dni_vecino)
          eval_tel = eval_exp.telefono_contacto
          eval_barrio = eval_exp.barrio or reg.barrio_detectado or ''
          eval_calles = eval_exp.entre_calles or ''
          eval_ref = eval_exp.referencias or ''
        else:
          eval_nombre = request.POST.get('nombre_vecino', '').strip()
          eval_dni = request.POST.get('dni_vecino', '').strip()
          eval_tel = request.POST.get('telefono_vecino', '').strip()
          eval_barrio = barrio_post or reg.barrio_detectado or ''
          eval_calles = request.POST.get('entre_calles_vecino', '').strip()
          eval_ref = request.POST.get('referencias_vecino', '').strip()

        # Reconstrucción del contexto oficial enriquecido para mantener enlaces y botones activos:
        resultado_extra = procesar_consulta_vecino(
            nombre=eval_nombre,
            detalle=reg.texto_consultado,
            datos_ubicacion={
                'barrio': eval_barrio,
                'entre_calles': eval_calles,
                'referencias': eval_ref,
            }
        )

        es_solo_info_eval = request.POST.get('solo_info', '').strip() == '1'
        es_rec_confirmado = bool(eval_exp) or reg.resultado == 'TICKET_REGISTRADO'
        es_rec = False if es_solo_info_eval else (
            es_rec_confirmado or reg.tipo_consulta == 'RECLAMO' or resultado_extra.get('es_reclamo', False)
        )
        es_emg = reg.resultado == 'EMERGENCIA' or resultado_extra.get('es_emergencia', False)

        # Reconstruir la respuesta exacta (con o sin ticket confirmado)
        if es_rec_confirmado and eval_exp:
          resultado_ticket = procesar_consulta_vecino(
              nombre=eval_nombre,
              detalle=reg.texto_consultado,
              confirmado=True,
              nro_ticket=eval_exp.nro_expediente,
              datos_ubicacion={
                  'barrio': eval_barrio,
                  'entre_calles': eval_calles,
                  'referencias': eval_ref,
              },
          )
          respuesta_mostrar = resultado_ticket.get('respuesta_texto') or reg.respuesta_brindada
        else:
          respuesta_mostrar = resultado_extra.get('respuesta_texto') or reg.respuesta_brindada

        etiquetas_eval = {'SI': 'Sí (SI)', 'PARCIAL': 'Parcialmente', 'NO': 'No'}

        contexto.update({
            'evaluacion_guardada': True,
            'evaluacion_valor': etiquetas_eval.get(evaluacion, evaluacion),
            'mensaje_evaluacion': (
                "¡Muchas gracias por tu valoración! Tu respuesta nos ayuda a optimizar la atención ciudadana en el CAV Sede Itaembé Guazú."
            ),
            'id_consulta': reg.identificador_consulta,
            'registro_consulta': reg,
            'respuesta_ia': respuesta_mostrar,
            'tipo_consulta': reg.tipo_consulta,
            'detalle_consulta': reg.texto_consultado,
            'tramite_info': resultado_extra.get('tramite_info'),
            'organismo_info': resultado_extra.get('organismo_info'),
            'es_derivacion_externa': resultado_extra.get('es_derivacion_externa', False),
            'es_emergencia': es_emg,
            'es_emergencia_electrica': resultado_extra.get('es_emergencia_electrica', False),
            'botones_emergencia': resultado_extra.get('botones_emergencia', []),
            'es_reclamo': es_rec,
            'es_consulta': resultado_extra.get('es_consulta', False),
            'reclamo_confirmado': es_rec_confirmado,
            'solo_info': es_solo_info_eval,
            'nro_ticket': eval_exp.nro_expediente if eval_exp else None,
            'expediente_obj': eval_exp,
            'nombre_vecino': eval_nombre,
            'dni_vecino': eval_dni,
            'telefono_vecino': eval_tel,
            'barrio_vecino': eval_barrio,
            'entre_calles_vecino': eval_calles,
            'referencias_vecino': eval_ref,
            'organismo_destino': (eval_exp.organismo_destino if eval_exp and eval_exp.organismo_destino else None) or resultado_extra.get('organismo_destino') or reg.categoria,
            'area_sugerida': resultado_extra.get('area_sugerida'),
        })
      return render(request, 'blog/portal_vecino.html', contexto)

    # --- CONSULTA A BASE DE DATOS (ORM QuerySet / Colección de Objetos): Buscar Trámite ---
    # Recupera colecciones de instancias de la clase Expediente filtrando por columnas de la BD:
    if 'btn_consultar_ticket' in request.POST:
      busqueda = request.POST.get('busqueda_ticket', '').strip()

      if busqueda:
        if busqueda.isdigit():
          tramites_encontrados = Expediente.objects.filter(
              Q(nro_expediente__iexact=busqueda) |
              Q(dni_vecino=int(busqueda)) |
              Q(nro_expediente__icontains=busqueda)
          ).order_by('-fecha_ingreso')
        else:
          tramites_encontrados = Expediente.objects.filter(
              Q(nro_expediente__iexact=busqueda) |
              Q(nro_expediente__icontains=busqueda)
          ).order_by('-fecha_ingreso')

        contexto['tramites'] = tramites_encontrados
        contexto['busqueda_realizada'] = busqueda
        if not tramites_encontrados.exists():
          contexto['error_busqueda'] = (
              f"No se encontraron trámites ni tickets registrados con '{busqueda}'. Verificá el N° de Ticket o tu DNI."
          )
      else:
        contexto['busqueda_realizada'] = ' '
        contexto['error_busqueda'] = (
            'Por favor, ingresá un N° de Ticket (ej: TCK-2026-0001) o DNI válido.'
        )

      return render(request, 'blog/portal_vecino.html', contexto)

    # Si envió un nuevo reclamo/consulta
    else:
      nombre = request.POST.get('nombre', '').strip()
      dni = request.POST.get('dni', '').strip()
      telefono = request.POST.get('telefono', '').strip()
      detalle = request.POST.get('detalle', '').strip()
      confirmar_ticket = request.POST.get('confirmar_ticket', '').strip()

      # Datos contextuales de ubicación territorial en Posadas
      barrio_in = request.POST.get('barrio', '').strip()
      entre_calles_in = request.POST.get('entre_calles', '').strip()
      referencias_in = request.POST.get('referencias', '').strip()
      datos_ubicacion = {
          'barrio': barrio_in,
          'entre_calles': entre_calles_in,
          'referencias': referencias_in,
      }

      if not dni or not nombre or not detalle or not telefono:
        contexto['error'] = (
            'Por favor, completá todos los campos para poder asesorarte.'
        )
        return render(request, 'blog/portal_vecino.html', contexto)

      es_valido, msg_error, datos_norm = validar_datos_vecino(nombre, dni, telefono)
      if not es_valido:
        contexto['error'] = msg_error
        return render(request, 'blog/portal_vecino.html', contexto)

      nombre = datos_norm['nombre']
      dni = datos_norm['dni']
      telefono = datos_norm['telefono']

      # Procesar interpretación y asesoramiento
      accion = request.POST.get('accion', '').strip()
      confirmar_ticket = request.POST.get('confirmar_ticket', '').strip()
      es_registro = bool(accion == 'registrar' or confirmar_ticket == '1' or confirmar_ticket.lower() == 'true')
      es_solo_info = bool(accion == 'solo_info')
      archivo = request.FILES.get('archivo_adjunto')

      # CASO: El vecino explicitó que solo necesitaba información
      if es_solo_info:
        resultado = procesar_consulta_vecino(
            nombre=nombre,
            detalle=detalle,
            confirmado=False,
            datos_ubicacion=datos_ubicacion,
        )

        # Registro de consulta independiente (sin ticket, con minimización de datos)
        id_consulta = f"CNS-{timezone.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        ctx_ubi = resultado.get('contexto_ubicacion', {})
        barrio_cns = barrio_in or (ctx_ubi.get('barrio') if ctx_ubi else '')

        # --- POO: INSTANCIACIÓN DE OBJETO Y PERSISTENCIA (Clase RegistroConsulta) ---
        # Se crea una nueva instancia (objeto en memoria) para auditar la consulta vecinal:
        RegistroConsulta.objects.create(
            identificador_consulta=id_consulta,
            tipo_consulta=resultado['tipo_consulta'],
            categoria=resultado.get('area_sugerida') or resultado.get('organismo_destino') or 'General',
            texto_consultado=detalle,
            respuesta_brindada=resultado['respuesta_texto'],
            fuente_informacion='Guía Operativa - Municipalidad de Posadas',
            resultado='ASESORAMIENTO',
            barrio_detectado=barrio_cns,
        )

        contexto.update({
            'respuesta_ia': resultado['respuesta_texto'],
            'tipo_consulta': resultado['tipo_consulta'],
            'es_emergencia': False,
            'es_emergencia_electrica': False,
            'es_reclamo': False,
            'es_consulta': False,
            'solo_info': True,
            'id_consulta': id_consulta,
            'nombre_vecino': nombre,
            'dni_vecino': dni,
            'telefono_vecino': telefono,
            'detalle_consulta': detalle,
            'organismo_destino': resultado.get('organismo_destino'),
            'area_sugerida': resultado.get('area_sugerida'),
            'barrio_vecino': barrio_cns,
            'entre_calles_vecino': entre_calles_in or (ctx_ubi.get('entre_calles') if ctx_ubi else ''),
            'referencias_vecino': referencias_in or (ctx_ubi.get('referencias') if ctx_ubi else ''),
        })
        return render(request, 'blog/portal_vecino.html', contexto)

      # CASO: Intento de confirmación y registro formal de solicitud / reclamo
      if es_registro:
        # Validación obligatoria: Para registrar formalmente una solicitud/reclamo en el sistema
        # es obligatorio indicar el Barrio o Chacra y entre qué calles o altura se ubica.
        ctx_temp = extraer_contexto_ubicacion(detalle, datos_ubicacion)
        barrio_final = barrio_in or (ctx_temp.get('barrio') if ctx_temp else '')
        calles_final = entre_calles_in or (ctx_temp.get('entre_calles') if ctx_temp else '')

        # Si el trámite corresponde a una gestión oficial del CAV Itaembé Guazú y no se cargó domicilio particular,
        # se asigna automáticamente la sede física oficial del CAV para no bloquear el inicio del trámite:
        info_cav_tramite = resolver_tramite_cav_itaembe(detalle)
        if info_cav_tramite:
          if not barrio_final:
            barrio_final = 'Itaembé Guazú'
          if not calles_final:
            calles_final = 'Calle Aguará Guazú y Magnolias (Sede CAV)'

        if not barrio_final or not calles_final:
          resultado = procesar_consulta_vecino(
              nombre=nombre,
              detalle=detalle,
              confirmado=False,
              datos_ubicacion=datos_ubicacion,
          )
          contexto.update({
              'error_ubicacion': (
                  'Para registrar formalmente tu solicitud es obligatorio indicar el Barrio o Chacra '
                  'y entre qué calles o altura se ubica.'
              ),
              'respuesta_ia': resultado['respuesta_texto'],
              'tipo_consulta': resultado['tipo_consulta'],
              'es_emergencia': False,
              'es_emergencia_electrica': False,
              'botones_emergencia': [],
              'tramite_info': None,
              'organismo_info': None,
              'es_derivacion_externa': False,
              'es_reclamo': True,
              'es_consulta': False,
              'reclamo_confirmado': False,
              'nro_ticket': None,
              'expediente_obj': None,
              'nombre_vecino': nombre,
              'dni_vecino': dni,
              'telefono_vecino': telefono,
              'detalle_consulta': detalle,
              'organismo_destino': resultado.get('organismo_destino'),
              'area_sugerida': resultado.get('area_sugerida'),
              'barrio_vecino': barrio_final,
              'entre_calles_vecino': calles_final,
              'referencias_vecino': referencias_in or (ctx_temp.get('referencias') if ctx_temp else ''),
          })
          return render(request, 'blog/portal_vecino.html', contexto)

      nro_ticket = None
      expediente_creado = None

      if es_registro:
        # Prevención de duplicados por clics múltiples dentro de los últimos 2 minutos
        dni_num = int(dni)
        hace_dos_minutos = timezone.now() - datetime.timedelta(seconds=120)
        expediente_existente = Expediente.objects.filter(
            dni_vecino=dni_num,
            detalle_consulta=detalle,
            fecha_ingreso__gte=hace_dos_minutos,
        ).order_by('-id').first()

        if expediente_existente:
          expediente_creado = expediente_existente
          nro_ticket = expediente_existente.nro_expediente
        else:
          nro_ticket = generar_siguiente_nro_ticket()

      resultado = procesar_consulta_vecino(
          nombre=nombre,
          detalle=detalle,
          confirmado=es_registro,
          nro_ticket=nro_ticket,
          datos_ubicacion=datos_ubicacion,
      )

      # Si es reclamo y fue confirmado formalmente, se persiste en la BD (si no fue recuperado por debounce)
      if resultado['es_reclamo'] and resultado['reclamo_confirmado'] and nro_ticket and not expediente_creado:
        try:
          dni_num = int(dni)
          categoria_obj = None
          cod_cat = resultado.get('cod_categoria_default')
          if cod_cat:
            categoria_obj = CategoriaReclamo.objects.filter(cod_categoria=cod_cat).first()

          ctx_ubi = resultado.get('contexto_ubicacion', {})
          barrio_final = barrio_in or (ctx_ubi.get('barrio') if ctx_ubi else '')
          calles_final = entre_calles_in or (ctx_ubi.get('entre_calles') if ctx_ubi else '')
          ref_final = referencias_in or (ctx_ubi.get('referencias') if ctx_ubi else '')

          info_cav_tramite = resolver_tramite_cav_itaembe(detalle)
          if info_cav_tramite:
            if not barrio_final:
              barrio_final = 'Itaembé Guazú'
            if not calles_final:
              calles_final = 'Calle Aguará Guazú y Magnolias (Sede CAV)'

          # --- POO: INSTANCIACIÓN DE OBJETO PRINCIPAL Y PERSISTENCIA (Clase Expediente) ---
          # 'expediente_creado' es la instancia concreta (objeto en memoria) que representa el ticket.
          # Se inicializa con los valores de los atributos y el ORM genera la sentencia SQL INSERT:
          expediente_creado = Expediente.objects.create(
              nro_expediente=nro_ticket,
              nombre_completo=nombre,
              dni_vecino=dni_num,
              telefono_contacto=telefono,
              tipo_solicitud='RECLAMO',
              categoria=categoria_obj,
              detalle_consulta=detalle,
              respuesta_ia=resultado['respuesta_texto'],
              organismo_destino=resultado['organismo_destino'],
              estado_actual='PENDIENTE',
              archivo_adjunto=archivo,
              barrio=barrio_final,
              entre_calles=calles_final,
              referencias=ref_final,
          )
        except Exception:
          pass

      # Determinar el resultado específico para el Registro de Consultas
      if resultado['es_emergencia']:
        resultado_tipo = 'EMERGENCIA'
        fuente_info = 'Protocolo de Emergencias y Seguridad 911 / EMSA'
      elif resultado['es_reclamo'] and resultado['reclamo_confirmado']:
        resultado_tipo = 'TICKET_REGISTRADO'
        fuente_info = 'Mesa de Entrada - Municipalidad de Posadas'
      elif resultado.get('es_derivacion_externa'):
        resultado_tipo = 'DERIVACION_EXTERNA'
        org_inf = resultado.get('organismo_info') or {}
        fuente_info = org_inf.get('fuente_verificacion', 'Organismo Externo Oficial')
      elif resultado.get('es_consulta') and resultado.get('tramite_info') and resultado['tramite_info'].get('tramite_online'):
        resultado_tipo = 'TRAMITE_DIGITAL'
        fuente_info = resultado['tramite_info'].get('fuente', 'Portal Oficial de Trámites Posadas')
      else:
        resultado_tipo = 'ASESORAMIENTO'
        fuente_info = 'Base de Conocimiento Oficial SIGEV'

      # Registro independiente de consulta (cumplimiento de Requisito 1)
      id_consulta = f"CNS-{timezone.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
      while RegistroConsulta.objects.filter(identificador_consulta=id_consulta).exists():
        id_consulta = f"CNS-{timezone.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

      ctx_ubi = resultado.get('contexto_ubicacion', {})
      barrio_cns = barrio_in or (ctx_ubi.get('barrio') if ctx_ubi else '')

      registro_obj = None
      try:
        registro_obj = RegistroConsulta.objects.create(
            identificador_consulta=id_consulta,
            tipo_consulta=resultado['tipo_consulta'],
            categoria=resultado.get('area_sugerida') or resultado.get('organismo_destino') or 'General',
            texto_consultado=detalle,
            respuesta_brindada=resultado['respuesta_texto'],
            fuente_informacion=fuente_info,
            resultado=resultado_tipo,
            ticket_asociado=expediente_creado,
            barrio_detectado=barrio_cns,
        )
      except Exception:
        pass

      contexto.update({
          'respuesta_ia': resultado['respuesta_texto'],
          'tipo_consulta': resultado['tipo_consulta'],
          'es_emergencia': resultado['es_emergencia'],
          'es_emergencia_electrica': resultado.get('es_emergencia_electrica', False),
          'botones_emergencia': resultado.get('botones_emergencia', []),
          'tramite_info': resultado.get('tramite_info'),
          'organismo_info': resultado.get('organismo_info'),
          'es_derivacion_externa': resultado.get('es_derivacion_externa', False),
          'es_reclamo': resultado['es_reclamo'],
          'es_consulta': resultado['es_consulta'],
          'reclamo_confirmado': resultado['reclamo_confirmado'],
          'nro_ticket': nro_ticket,
          'expediente_obj': expediente_creado,
          'id_consulta': id_consulta,
          'registro_consulta': registro_obj,
          'nombre_vecino': nombre,
          'dni_vecino': dni,
          'telefono_vecino': telefono,
          'detalle_consulta': detalle,
          'organismo_destino': resultado.get('organismo_destino'),
          'area_sugerida': resultado.get('area_sugerida'),
          'contexto_ubicacion': ctx_ubi,
          'preguntas_seguimiento': resultado.get('preguntas_seguimiento'),
          'resumen_solicitud': resultado.get('resumen_solicitud'),
          'barrio_vecino': barrio_in or (ctx_ubi.get('barrio') if ctx_ubi else ''),
          'entre_calles_vecino': entre_calles_in or (ctx_ubi.get('entre_calles') if ctx_ubi else ''),
          'referencias_vecino': referencias_in or (ctx_ubi.get('referencias') if ctx_ubi else ''),
      })

  return render(request, 'blog/portal_vecino.html', contexto)


# ==============================================================================
# MÉTODO CONTROLADOR / PANTALLA: Mesa de Entrada (Gestión de Expedientes)
# Muestra la interfaz para operadores y actualiza el estado de las instancias:
# exp.save() persiste los cambios en la base de datos (SQL UPDATE).
# ==============================================================================
def mesa_entrada(request):
  mensaje_exito = None
  if request.method == 'POST' and 'btn_derivar_expediente' in request.POST:
    expediente_id = request.POST.get('expediente_id')
    nuevo_estado = request.POST.get('nuevo_estado', 'DERIVADO').strip()
    nuevo_organismo = request.POST.get('organismo_destino', '').strip()

    exp = Expediente.objects.filter(id=expediente_id).first()
    if exp:
      if nuevo_estado in dict(Expediente.ESTADO_CHOICES):
        exp.estado_actual = nuevo_estado
      if nuevo_organismo:
        exp.organismo_destino = nuevo_organismo
      exp.save()
      mensaje_exito = (
          f"El expediente {exp.nro_expediente} fue actualizado: Estado '{exp.get_estado_actual_display()}' y derivado a '{exp.organismo_destino}'."
      )

  expedientes = Expediente.objects.all().order_by('-id')
  consultas = RegistroConsulta.objects.all().order_by('-id')[:50]
  sugerencias = SugerenciaOrganismo.objects.all().order_by('-id')[:50]
  return render(
      request,
      'blog/mesa_entrada.html',
      {
          'expedientes': expedientes,
          'consultas': consultas,
          'sugerencias': sugerencias,
          'mensaje_exito': mensaje_exito,
      },
  )


# ==============================================================================
# MÉTODO CONTROLADOR / PANTALLA: Panel Gerencial / Dashboard
# Interfaz gráfica de monitoreo y métricas: recupera colecciones de objetos
# ordenados cronológicamente desde la base de datos.
# ==============================================================================
def panel_gerencial(request):
  # --- POO: MÉTODOS DE CONSULTA Y AGREGACIÓN EN BASE DE DATOS (ORM QuerySets) ---
  # Recuperación de colecciones de instancias para métricas y auditoría gerencial:
  expedientes = Expediente.objects.all().order_by('-id')
  consultas = RegistroConsulta.objects.all().order_by('-id')
  sugerencias = SugerenciaOrganismo.objects.all().order_by('-id')

  # Métricas agregadas: Conteo dinámico de emergencias 911 detectadas (sin crear reclamo/ticket)
  emergencias_detectadas = RegistroConsulta.objects.filter(
      Q(tipo_consulta='EMERGENCIA') | Q(resultado='EMERGENCIA')
  ).count()

  # Conteo de trámites y derivaciones informativas a canales oficiales
  tramites_derivaciones = RegistroConsulta.objects.filter(
      resultado__in=['TRAMITE_DIGITAL', 'DERIVACION_EXTERNA', 'ASESORAMIENTO']
  ).count()

  # Métricas de satisfacción ciudadana (Requisito 8: Sí / Parcialmente / No)
  satisfaccion_si = RegistroConsulta.objects.filter(evaluacion_vecino='SI').count()
  satisfaccion_parcial = RegistroConsulta.objects.filter(evaluacion_vecino='PARCIAL').count()
  satisfaccion_no = RegistroConsulta.objects.filter(evaluacion_vecino='NO').count()
  total_evaluadas = satisfaccion_si + satisfaccion_parcial + satisfaccion_no
  porcentaje_positivas = round((satisfaccion_si / total_evaluadas) * 100) if total_evaluadas > 0 else 0

  return render(
      request,
      'blog/panel_gerencial.html',
      {
          'expedientes': expedientes,
          'consultas': consultas,
          'sugerencias': sugerencias,
          'emergencias_detectadas': emergencias_detectadas,
          'tramites_derivaciones': tramites_derivaciones,
          'satisfaccion_si': satisfaccion_si,
          'satisfaccion_parcial': satisfaccion_parcial,
          'satisfaccion_no': satisfaccion_no,
          'total_evaluadas': total_evaluadas,
          'porcentaje_positivas': porcentaje_positivas,
      },
  )
