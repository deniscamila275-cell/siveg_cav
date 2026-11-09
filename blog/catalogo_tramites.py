"""
Catálogo Configurable de Trámites Digitales y Canales Oficiales.
Municipalidad de Posadas / Provincia de Misiones.

Organizado según el ecosistema web municipal:
1. Autogestión Tributaria y Pagos (con y sin clave fiscal) - sistema.posadas.gov.ar
2. Trámites de Licencia de Conducir - posadas.gov.ar/turnos y posadas.gov.ar/guiatramite
3. Gestión de Obras Privadas (Sistema GOP) - Planificación Territorial posadas.gov.ar/planurbano/guia-de-tramites
4. Habilitaciones Comerciales y de Eventos - datos.posadas.gov.ar/habilitaciones-municipales
5. Trámites Generales y Comunitarios - posadas.gov.ar/guiatramite
6. Organismos presentes en Sede CAV Itaembé Guazú (Obras Privadas/GOP, IProDHa, Registro Civil, ATM, HCD, Defensoría)
"""

import re

CATALOGO_TRAMITES = [
    {
        'id': 'patente_automotor',
        'nombre': 'Generar Boleta de Patente (IPA) y Pago Online - DGR Sin Clave Fiscal',
        'categoria': 'Hacienda y Tributos',
        'organismo_responsable': 'DGR / Agencia Tributaria Misiones (ATM) - Municipalidad de Posadas',
        'descripcion': 'Acceso directo al portal oficial DGR - Sin Clave Fiscal para la emisión de boleta del Impuesto Provincial al Automotor (IPA / Patente) y pago online inmediato con tarjeta de crédito o débito (incluye el programa Ahora Patente con cuotas y reintegros).',
        'requisitos': [
            'Número de dominio (patente del vehículo sin guiones ni espacios).',
            'Seleccionar municipio de radicación (Posadas).',
            'Tarjeta de débito o crédito para pago inmediato online o impresión de boleta para pago presencial.',
            'Trámite directo sin clave fiscal ni turnos previos.'
        ],
        'enlace_oficial': 'https://sinclavefiscal.atm.misiones.gob.ar/sc/automotor/emision_ba_ipa',
        'fecha_verificacion': '2026-11-04',
        'tramite_online': True,
        'texto_boton': 'DGR - Sin Clave Fiscal (Generar boleta y pagar)',
        'fuente': 'DGR - Sin Clave Fiscal (Agencia Tributaria Misiones)',
        'palabras_clave': [
            'patente', 'patenet', 'automotor', 'auto', 'moto', 'vehiculo', 'ipa',
            'generar boleta patente', 'generar boleta de patente', 'generar boleta automotor',
            'boleta patente', 'boleta de patente', 'boleta del auto', 'boleta automotor',
            'emision de boleta patente', 'emision boleta patente', 'emision boleta automotor',
            'emision de boleta', 'sacar boleta patente', 'imprimir boleta patente',
            'pagar patente', 'pago de patente', 'pagar mi patente', 'pagar la patente',
            'deuda de patente', 'deuda automotor', 'patente online', 'dgr sin clave fiscal'
        ],
        'canales_presenciales': 'Cajas en sedes CAV Itaembé Guazú (Calle Aguará Guazú y Magnolias) y CAV Las Heras de 07:00 a 18:00 hs. Sede Central ATM: San Martín 1754 (07:00 a 13:00 hs).',
        'telefono_contacto': '(0376) 428-2000 (WhatsApp Oficial) | 0810-444-5505 (Mesa de Ayuda)'
    },
    {
        'id': 'licencia_conducir',
        'nombre': 'Centro de Emisión de Licencia Nacional de Conducir (Turnos y Tarifario)',
        'categoria': 'Tránsito y Movilidad Urbana',
        'organismo_responsable': 'Municipalidad de Posadas - Dirección de Tránsito',
        'descripcion': 'Trámites para Primera Licencia y Renovación para Clases Particulares (A, B, G), Licencia para Clases Profesionales (C, D, E) y consulta de costos y tasas según vigencia. Turnos online en https://posadas.gov.ar/turnos/ y Guía de Trámites en https://posadas.gov.ar/guiatramite.',
        'requisitos': [
            'DNI con domicilio actualizado en la ciudad de Posadas.',
            'Libre deuda de infracciones del Tribunal Municipal de Faltas (sin multas pendientes).',
            'Certificado Nacional de Antecedentes de Tránsito (Boleta CENAT online previa obligatoria: https://boletadepago.seguridadvial.gob.ar/).',
            'Examen psicofísico y teórico-práctico según la clase solicitada (particular o profesional).'
        ],
        'enlace_oficial': 'https://posadas.gov.ar/turnos/',
        'fecha_verificacion': '2026-11-04',
        'tramite_online': True,
        'texto_boton': 'Iniciar trámite online',
        'fuente': 'Municipalidad de Posadas - Guía de Trámites y Turnos Online',
        'palabras_clave': ['licencia', 'carnet', 'conducir', 'manejar', 'cenat', 'registro de conducir', 'turno licencia', 'renovar licencia', 'renovacion carnet', 'renovar carnet', 'primera licencia', 'clases particulares', 'clases profesionales', 'tarifa licencia', 'costo licencia'],
        'canales_presenciales': 'Centros Emisores CAV Las Heras (Av. Las Heras 3929) y CAV Itaembé Guazú de 07:00 a 18:00 hs.',
        'telefono_contacto': '0800-888-2483 (Línea CIUDAD Gratuita)'
    },
    {
        'id': 'multas_transito',
        'nombre': 'Consulta y Regularización de Infracciones de Tránsito',
        'categoria': 'Tribunal de Faltas',
        'organismo_responsable': 'Municipalidad de Posadas - Tribunal Municipal de Faltas',
        'descripcion': 'Consulta directa de infracciones registradas en Posadas, estado de actas de tránsito, fotomultas y regularización de pagos mediante autogestión sin clave fiscal en https://sistema.posadas.gov.ar/mp_sistemas/autogestion/consultarmultadominio.',
        'requisitos': [
            'Número de patente del vehículo o DNI del conductor.',
            'Número de acta de infracción (en caso de notificación previa).',
            'Para descargos: presentación escrita ante el Juzgado de Faltas correspondiente.'
        ],
        'enlace_oficial': 'https://sistema.posadas.gov.ar/mp_sistemas/autogestion/consultarmultadominio',
        'fecha_verificacion': '2026-11-04',
        'tramite_online': True,
        'texto_boton': 'Consultar Infracciones por Dominio / DNI',
        'fuente': 'Municipalidad de Posadas - Sistema de Autogestión / Tribunal de Faltas',
        'palabras_clave': ['multa', 'multas', 'infraccion', 'infracciones', 'tribunal de faltas', 'juzgado de faltas', 'acta de transito', 'fotomulta', 'alcoholemia'],
        'canales_presenciales': 'Calle San Martín N° 1555 (entre Rivadavia y Buenos Aires), Posadas (07:00 a 19:00 hs). Módulo en sedes CAV.',
        'telefono_contacto': '(0376) 443-7705 | Línea CIUDAD: 0800-888-2483'
    },
    {
        'id': 'obras_privadas',
        'nombre': 'Gestión de Obras Privadas - Sistema GOP (Planificación Territorial)',
        'categoria': 'Obras y Urbanismo',
        'organismo_responsable': 'Municipalidad de Posadas - Secretaría de Planificación Estratégica y Territorial',
        'descripcion': 'Trámites directos del Sistema GOP: orientación sobre regularización de obras, presentación y visado de mensuras para Catastro, cambio de categoría (baldío a edificado), comodato precario, certificado de funcionamiento comercial, vallados de obras, Plan Mejor Vivir, regularización de construcciones existentes sin permiso, certificado final de obra, números de finca e indicadores urbanos en https://posadas.gestiondeobrasprivadas.com.ar/ y guía técnica en https://posadas.gov.ar/planurbano/guia-de-tramites/.',
        'requisitos': [
            'Presentación digital mediante el Sistema GOP con usuario habilitado.',
            'Planos de obra suscriptos por profesional matriculado (arquitecto o maestro mayor de obras).',
            'Título de propiedad, boleto de compraventa sellado o constancia registral del inmueble.',
            'Libre deuda municipal de Tasa General de Inmuebles (TGI).'
        ],
        'enlace_oficial': 'https://posadas.gestiondeobrasprivadas.com.ar/',
        'fecha_verificacion': '2026-11-04',
        'tramite_online': True,
        'texto_boton': 'Acceder al Sistema GOP Posadas (Obras Privadas)',
        'fuente': 'Municipalidad de Posadas (posadas.gov.ar) - Secretaría de Planificación Estratégica y Territorial',
        'palabras_clave': ['sistema gop', 'gop', 'obras privadas', 'planificacion territorial', 'plan urbano', 'mensura', 'visado de mensura', 'baldio a edificado', 'cambio de categoria', 'comodato precario', 'funcionamiento comercial', 'vallados de obras', 'vallado de obra', 'mejor vivir', 'plan mejor vivir', 'regularizacion de construcciones', 'construccion existente', 'obra sin permiso', 'regularizacion de obra', 'certificado final de obra', 'final de obra', 'indicadores urbanos', 'numero de finca', 'numeros de finca', 'inspecciones tecnicas', 'ampliar casa', 'ampliar mi casa', 'construir', 'empezar una obra', 'empezar obra', 'iniciar obra', 'iniciar una obra', 'hacer una obra', 'hacer obra', 'obra nueva', 'nueva obra', 'obra', 'obras', 'empezar a construir', 'iniciar construccion', 'comenzar una obra', 'comenzar obra', 'permiso para construir', 'permiso para edificar', 'permiso de obra', 'hacer planos', 'presentar planos', 'aprobar planos'],
        'canales_presenciales': 'Módulo en CAV Itaembé Guazú (Calle Aguará Guazú y Magnolias) y CAV Las Heras (07:00 a 18:00 hs). Edificio Central: San Martín 1579.',
        'telefono_contacto': '0800-888-2483 (Línea CIUDAD Gratuita) | (0376) 444-9000'
    },
    {
        'id': 'denuncia_obras',
        'nombre': 'Denuncia de Obras Clandestinas, Medianeras y Control de Construcciones',
        'categoria': 'Obras Públicas y Control Urbano',
        'organismo_responsable': 'Municipalidad de Posadas - Obras Públicas',
        'descripcion': 'Atención e inspección municipal por construcciones sin permiso, invasión o apoyo antirreglamentario en muros medianeros, ampliaciones no autorizadas y obras en contravención al Código de Edificación.',
        'requisitos': [
            'Dirección exacta o ubicación del inmueble denunciado (barrio, calle, altura y referencias).',
            'Descripción clara del hecho (invasión de muro, ampliación no autorizada, falta de cartel de obra o riesgos linderos).',
            'Fotografías o documentación que acredite la afectación (opcional para facilitar la inspección municipal).',
            'Constatación presencial por parte del cuerpo de inspectores de Obras Públicas de la Municipalidad de Posadas.'
        ],
        'enlace_oficial': 'https://posadas.gestiondeobrasprivadas.com.ar/',
        'fecha_verificacion': '2026-11-05',
        'tramite_online': True,
        'texto_boton': 'Portal de Obras Posadas (Sistema GOP)',
        'fuente': 'Municipalidad de Posadas - Secretaría de Obras Públicas / Planificación',
        'palabras_clave': [
            'denuncia de obra', 'denunciar obra', 'denunciar vecina', 'denunciar vecino',
            'obra clandestina', 'obra sin permiso', 'construccion sin permiso', 'construccion clandestina',
            'muro', 'muros', 'medianera', 'medianeras', 'muro medianero', 'ocupo mi muro', 'ocupo muro',
            'apoyo en mi muro', 'apoyo sobre mi muro', 'amplio su casa', 'amplio por mi muro',
            'ampliacion', 'amplaicion', 'pared lindera', 'pared medianera', 'invasion de terreno',
            'construccion ilegal', 'obra antirreglamentaria', 'ampliacion ilegal', 'pared de mi vecina',
            'muro del vecino', 'muro de la vecina'
        ],
        'canales_presenciales': 'Secretaría de Obras Públicas / Obras Privadas: Edificio Central Municipal (San Martín 1579). Módulo en CAV Itaembé Guazú y CAV Las Heras.',
        'telefono_contacto': '0800-888-2483 (Línea CIUDAD Gratuita) | (0376) 444-9000'
    },
    {
        'id': 'denuncia_ruidos_molestos',
        'nombre': 'Denuncia por Ruidos Molestos y Música Fuerte (Ordenanza VI – Nº 14)',
        'categoria': 'Control Comunal y Convivencia Urbana',
        'organismo_responsable': 'Municipalidad de Posadas - Dirección de Control Comunal (Guardia de Ruidos Molestos)',
        'descripcion': 'La emisión de ruidos molestos, música a volumen desmedido y perturbaciones al descanso vecinal está tipificada como infracción bajo la Ordenanza VI – Nº 14 del Digesto Municipal de Posadas. '
                       'Podés radicar tu reclamo formal para inspección y sonometría municipal o comunicarte directamente con la Guardia de Ruidos Molestos.',
        'requisitos': [
            'Dirección exacta o altura del inmueble o vecino denunciado (calle, número o entrecalles, barrio en Posadas).',
            'Nombre o datos de la vecina o vecino infractor (si se conocen, o características visibles de la propiedad).',
            'Relato circunstanciado: días y horarios en que ocurren los ruidos y tipo de sonido perturbador.',
            'Datos de contacto del vecino denunciante (para seguimiento del inspector actuante).'
        ],
        'enlace_oficial': 'https://wa.me/5493764134650',
        'fecha_verificacion': '2026-11-08',
        'tramite_online': True,
        'texto_boton': 'Guardia de Ruidos Molestos (WhatsApp Oficial)',
        'fuente': 'Municipalidad de Posadas - Ordenanza VI – Nº 14 / Guardia de Control Comunal',
        'palabras_clave': [
            'ruidos molestos', 'ruido molesto', 'musica fuerte', 'musica alta', 'musica a todo volumen',
            'musica al taco', 'musica a alto volumen', 'vecina ruidosa', 'vecino ruidoso', 'denunciar ruidos',
            'denuncia por ruidos', 'ordenanza vi 14', 'ordenanza ruidos', 'denunciar a mi vecina',
            'denunciar vecina', 'denunciar vecino', 'vecina que escucha musica', 'vecino que escucha musica',
            'escucha musica fuerte', 'escuchan musica fuerte', 'ruido de cualquier indole', 'ruidos de cualquier indole'
        ],
        'canales_presenciales': 'Guardia de Control Comunal Municipal / Sede Central: San Martín 1579, Posadas.',
        'telefono_contacto': 'WhatsApp Guardia: (376) 413-4650 | Línea CIUDAD: 0800-888-2483'
    },
    {
        'id': 'habilitaciones_comerciales',
        'nombre': 'Habilitaciones Comerciales, Obras Privadas (Sistema GOP) y Habilitación Eventual Online',
        'categoria': 'Comercio, Industria y Obras Privadas',
        'organismo_responsable': 'Municipalidad de Posadas - Dirección General de Habilitaciones Comerciales / Secretaría de Planificación y Obras Privadas (Sistema GOP)',
        'descripcion': (
            'Gestión integral para habilitar un negocio o local comercial en Posadas: '
            '1) Verificación edilicia, planos y Certificado de Funcionamiento Comercial / Uso Conforme ante Obras Privadas (Sistema GOP: https://posadas.gestiondeobrasprivadas.com.ar/ y https://posadas.gov.ar/planurbano/guia-de-tramites/), con atención presencial en el CAV Itaembé Guazú; y '
            '2) Alta comercial en la Dirección General de Habilitaciones Comerciales (https://posadas.gov.ar/guiatramite y https://datos.posadas.gov.ar/habilitaciones-municipales/), incluyendo comercios nuevos, mudanzas, cambios de rubro y Habilitación Eventual Online para espectáculos o eventos masivos.'
        ),
        'requisitos': [
            'Certificado de Funcionamiento Comercial / Factibilidad de Uso Conforme y planos aprobados o visados en Obras Privadas - Sistema GOP (https://posadas.gestiondeobrasprivadas.com.ar/).',
            'DNI del titular o estatuto/poder y constancia de CUIT / inscripción en ATM y ARCA (ex AFIP).',
            'Contrato de locación sellado, comodato o título de propiedad del inmueble / local.',
            'Libre deuda municipal de Tasa General de Inmuebles (TGI) del local.',
            'Certificado de seguridad contra incendios emitido por Bomberos de la Policía de Misiones.',
            'Certificado de aptitud de Bromatología y Carnet Sanitario (se liquida en el CAV Itaembé Guazú) para locales gastronómicos o de alimentos.',
            'Para habilitación eventual: póliza de seguro de responsabilidad civil, plan de contingencia y certificado digital.'
        ],
        'enlace_oficial': 'https://posadas.gestiondeobrasprivadas.com.ar/',
        'fecha_verificacion': '2026-11-08',
        'tramite_online': True,
        'texto_boton': 'Sistema GOP - Obras Privadas y Funcionamiento Comercial',
        'fuente': 'Municipalidad de Posadas - Obras Privadas (Sistema GOP) y Dirección General de Habilitaciones Comerciales',
        'palabras_clave': [
            'habilitacion comercial', 'habilitaciones comerciales', 'habilitacion digital', 'habilitacion eventual',
            'evento', 'espectaculo', 'eventos masivos', 'habilitar negocio', 'habilitar un negocio', 'habilitar local',
            'habilitar comercio', 'habilitar', 'abrir local', 'abrir negocio', 'comercio', 'local comercial',
            'bromatologia', 'habilitacion de negocio', 'nuegocio', 'nogio', 'negosio', 'negcio', 'neogcio'
        ],
        'canales_presenciales': 'Módulo de Obras Privadas y Delegación Municipal en CAV Itaembé Guazú (Calle Aguará Guazú y Magnolias), CAV Las Heras y Edificio Central (San Martín 1579).',
        'telefono_contacto': '0800-888-2483 (Línea CIUDAD) | (0376) 444-9056'
    },
    {
        'id': 'sem_estacionamiento',
        'nombre': 'Sistema de Estacionamiento Medido (SEM Posadas) - Pago Online y Saldo',
        'categoria': 'Tránsito y Movilidad Urbana',
        'organismo_responsable': 'Municipalidad de Posadas - Secretaría de Movilidad Urbana',
        'descripcion': 'Gestión directa del estacionamiento en el radio céntrico de Posadas: carga de crédito, consulta de saldo, pago online de cuentas, fraccionamiento por minuto y regularización de infracciones SEM en el sistema de autogestión https://sistema.posadas.gov.ar/mp_sistemas/autogestion.',
        'requisitos': [
            'Número de teléfono móvil registrado o patente del vehículo.',
            'Aplicación móvil SEM Posadas o acceso al portal de autogestión.',
            'Medio de pago electrónico (tarjeta de débito/crédito, Mercado Pago, billeteras virtuales o comercios adheridos).'
        ],
        'enlace_oficial': 'https://sistema.posadas.gov.ar/mp_sistemas/autogestion/consultatasaestacionamientomedido',
        'fecha_verificacion': '2026-11-04',
        'tramite_online': True,
        'texto_boton': 'Consultar Saldo e Infracciones SEM Posadas',
        'fuente': 'Municipalidad de Posadas - SEM (Sistema de Estacionamiento Medido)',
        'palabras_clave': ['sem', 'estacionamiento medido', 'estacionamiento', 'saldo sem', 'app sem', 'pagar sem', 'estacionar en el centro', 'infraccion sem'],
        'canales_presenciales': 'Puntos de venta adheridos en el radio céntrico de Posadas y puestos de atención SEM en el microcentro.',
        'telefono_contacto': '0800-888-2483 | WhatsApp SEM: (376) 412-2555'
    },
    {
        'id': 'tasas_municipales_autogestion',
        'nombre': 'Sistema de Autogestión Tributaria y Pagos de Posadas (Con y Sin Clave Fiscal)',
        'categoria': 'Hacienda y Recaudación',
        'organismo_responsable': 'Municipalidad de Posadas - Secretaría de Hacienda',
        'descripcion': 'Portal unificado de pagos y trámites sin clave fiscal: Tasa General de Inmuebles (TGI), Certificado de Libre Deuda, Adhesión al Débito Automático, Canon por Venta de Bebidas Alcohólicas, Tasa de Cementerio, Publicidad y Propaganda, Convenios Formalizados, Gestión de Comprobantes Emitidos y consulta de Expedientes de Interés Público en https://sistema.posadas.gov.ar/mp_sistemas/autogestion.',
        'requisitos': [
            'Número de partida inmobiliaria o cuenta municipal del contribuyente.',
            'DNI o CUIT del titular registral.',
            'Medio de pago electrónico habilitado (débito, crédito, banca virtual o volante electrónico).'
        ],
        'enlace_oficial': 'https://sistema.posadas.gov.ar/mp_sistemas/autogestion/consultatasageneralinmueble',
        'fecha_verificacion': '2026-11-04',
        'tramite_online': True,
        'texto_boton': 'Consultar y Pagar TGI Online (Sin Clave Fiscal)',
        'fuente': 'Municipalidad de Posadas - Portal de Autogestión Tributaria',
        'palabras_clave': ['autogestion', 'tasas municipales', 'tasa municipal', 'tgi', 'tasa general de inmuebles', 'libre deuda', 'debito automatico', 'canon por venta de bebidas', 'bebidas alcoholicas', 'tasa de cementerio', 'cementerio', 'publicidad y propaganda', 'carteleria', 'convenios formalizados', 'plan de pago', 'comprobantes emitidos', 'expedientes de interes publico', 'domicilio fiscal'],
        'canales_presenciales': 'Cajas municipales en Edificio Central (San Martín 1579) y módulos en sedes CAV Las Heras y CAV Itaembé Guazú.',
        'telefono_contacto': '0800-888-2483 | Mesa de Ayuda Tributaria: (0376) 444-9022'
    },
    {
        'id': 'actas_transito_informe',
        'nombre': 'Actas de Tránsito / Pago Online y Solicitud de Informes',
        'categoria': 'Tribunal de Faltas',
        'organismo_responsable': 'Municipalidad de Posadas - Tribunal Municipal de Faltas',
        'descripcion': 'Consulta, liquidación y pago online de actas de infracción de tránsito labradas en Posadas y Solicitud de Informe de Infracciones asociadas a una patente o DNI en el portal municipal posadas.gov.ar.',
        'requisitos': [
            'Número de dominio (patente del vehículo) o DNI del conductor.',
            'Número de acta de infracción (en caso de notificación previa).',
            'Medio de pago electrónico habilitado.'
        ],
        'enlace_oficial': 'https://sistema.posadas.gov.ar/mp_sistemas/autogestion/consultarmultadominio',
        'fecha_verificacion': '2026-11-04',
        'tramite_online': True,
        'texto_boton': 'Consultar y Pagar Actas de Tránsito Online',
        'fuente': 'Municipalidad de Posadas - Tribunal de Faltas / Autogestión',
        'palabras_clave': ['actas de transito', 'acta de transito', 'solicitud de informe', 'informe de infracciones', 'libre deuda de transito', 'pago de acta', 'multa de transito posadas'],
        'canales_presenciales': 'San Martín 1555 (entre Rivadavia y Buenos Aires), Posadas (07:00 a 19:00 hs). Módulo en sedes CAV.',
        'telefono_contacto': '(0376) 443-7705 | 0800-888-2483'
    },
    {
        'id': 'tramites_comunitarios',
        'nombre': 'Trámites Generales y Comunitarios de Posadas',
        'categoria': 'Comunidad y Participación Ciudadana',
        'organismo_responsable': 'Municipalidad de Posadas',
        'descripcion': 'Guía de trámites generales: requisitos para Notas Varias (Mesa de Entradas), recolección de ramas y residuos voluminosos, inscripción a la Escuela Municipal de Danza, mediación comunitaria vecinal, trámites de la Dirección de Automotores, presentación de Declaraciones Juradas y Presupuesto Participativo.',
        'requisitos': [
            'DNI del vecino solicitante.',
            'Para notas varias: presentación formal dirigida al área municipal correspondiente.',
            'Para Escuela de Danza: formulario de matriculación y certificado de aptitud física.',
            'Para Presupuesto Participativo: residencia en el barrio y proyecto comunitario formulado.'
        ],
        'enlace_oficial': 'https://posadas.gov.ar/guiatramite',
        'fecha_verificacion': '2026-11-04',
        'tramite_online': True,
        'texto_boton': 'Guía Oficial de Trámites Posadas',
        'fuente': 'Municipalidad de Posadas - Guía Oficial de Trámites',
        'palabras_clave': ['tramites generales', 'notas varias', 'mesa de entradas', 'recoleccion de ramas', 'residuos voluminosos', 'escuela municipal de danza', 'danza', 'escuela de danza', 'mediacion comunitaria', 'automotores', 'declaraciones juradas', 'presupuesto participativo', 'proyectos vecinales'],
        'canales_presenciales': 'Mesa General de Entradas (San Martín 1579) y sedes CAV.',
        'telefono_contacto': '0800-888-2483 (Línea CIUDAD Gratuita)'
    },
    {
        'id': 'hcd_posadas_tramite',
        'nombre': 'Honorable Concejo Deliberante de Posadas (HCD) - Atención y Proyectos',
        'categoria': 'Legislativo y Participación',
        'organismo_responsable': 'Honorable Concejo Deliberante de la Ciudad de Posadas',
        'descripcion': 'Atención al público presencial en el CAV Itaembé Guazú, recepción de notas e iniciativas de ordenanza comunitaria, asesoramiento sobre ordenanzas vigentes y consulta de digesto jurídico en https://hcdposadas.gob.ar/.',
        'requisitos': [
            'DNI del vecino solicitante.',
            'Nota o proyecto vecinal fundamentado por escrito.'
        ],
        'enlace_oficial': 'https://hcdposadas.gob.ar/',
        'fecha_verificacion': '2026-11-04',
        'tramite_online': True,
        'texto_boton': 'Portal Oficial HCD Posadas',
        'fuente': 'Honorable Concejo Deliberante de Posadas - Portal Oficial',
        'palabras_clave': ['concejo deliberante', 'hcd', 'honorable concejo deliberante', 'ordenanzas', 'proyectos ciudadanos', 'atencion hcd', 'digesto juridico'],
        'canales_presenciales': 'Módulo de Atención al Público en CAV Itaembé Guazú (Calle Aguará Guazú y Magnolias). Sede Central HCD: Calle Bolívar N° 1588.',
        'telefono_contacto': '(0376) 449-0800 | 0800-888-2483'
    },
    {
        'id': 'cav_itaembe_guazu',
        'nombre': 'Centro de Atención Vecinal (CAV) Itaembé Guazú - Organismos y Servicios',
        'categoria': 'Atención Ciudadana Descentralizada',
        'organismo_responsable': 'Municipalidad de Posadas - Centro de Atención Vecinal',
        'descripcion': 'El CAV Itaembé Guazú (ubicado en Calle Aguará Guazú y Magnolias) cuenta con atención integral de 6 organismos y entidades:\n'
                       '1. Secretaría de Planificación Estratégica y Territorial / Obras Privadas (orientación sobre regularización de obras, sistema GOP, indicadores urbanos, números de finca e inspecciones)\n'
                       '2. Instituto Provincial de Desarrollo Habitacional - IProDHa (viviendas sociales, cuotas y regularización)\n'
                       '3. Registro Provincial de las Personas (tramitación de DNI y solicitudes de partidas)\n'
                       '4. Agencia Tributaria Misiones - ATM (puestos de pago y asesoramiento tributario)\n'
                       '5. Honorable Concejo Deliberante - HCD (atención al público y proyectos vecinales)\n'
                       '6. Defensoría del Pueblo de Posadas (mediación comunitaria y defensa de derechos).',
        'requisitos': [
            'DNI físico.',
            'Documentación específica o comprobante de la tasa/trámite a realizar según el organismo competente.'
        ],
        'enlace_oficial': 'https://posadas.gov.ar/',
        'fecha_verificacion': '2026-11-04',
        'tramite_online': False,
        'texto_boton': 'Ver información en portal oficial',
        'fuente': 'Municipalidad de Posadas - Red de Centros de Atención Vecinal',
        'palabras_clave': ['cav itaembe', 'cav de itaembe', 'cav itaembe guazu', 'organismos del cav', 'que hay en el cav', 'que organismos hay en el cav', 'organismos presentes en el cav', 'entidades del cav', 'itaembe guazu organismos', 'itaembe guazu cav', 'horario cav itaembe'],
        'canales_presenciales': 'CAV Itaembé Guazú: Calle Aguará Guazú y Magnolias, Posadas. Horario: Lunes a Viernes de 07:00 a 18:00 hs.',
        'telefono_contacto': '(0376) 440-9050 | 0800-888-2483 (Línea CIUDAD)'
    },
    {
        'id': 'operativo_descacharrado',
        'nombre': 'Información de Operativo Descacharrado (Prevención Dengue)',
        'categoria': 'Salud y Prevención Ambiental',
        'organismo_responsable': 'Municipalidad de Posadas - Secretaría de Salud y Calidad de Vida',
        'descripcion': 'Cronograma semanal por chacras y barrios de los operativos de descacharrado y retiro de recipientes en desuso para la prevención del Dengue, Chikungunya y Zika.',
        'requisitos': [
            'Revisar el cronograma correspondiente a su chacra o barrio en el portal municipal.',
            'Sacar a la vereda en los días estipulados chatarras, neumáticos, botellas, baldes rotos y recipientes en desuso que acumulen agua.',
            'No sacar ramas de poda ni escombros en los operativos exclusivos de descacharrado.'
        ],
        'enlace_oficial': 'https://posadas.gov.ar/',
        'fecha_verificacion': '2026-11-04',
        'tramite_online': False,
        'texto_boton': 'Ver información en portal oficial',
        'fuente': 'Municipalidad de Posadas - Salud y Calidad de Vida',
        'palabras_clave': ['descacharrado', 'operativo descacharrado', 'dengue', 'cacharros', 'aedes aegypti', 'cronograma descacharrado', 'fumigacion dengue', 'criaderos de mosquito'],
        'canales_presenciales': 'Centros de Integración Territorial (CIT), Delegaciones Municipales y CAVs.',
        'telefono_contacto': '0800-888-2483 (Línea CIUDAD Gratuita) | (0376) 444-9054'
    },
    {
        'id': 'oficina_empleo',
        'nombre': 'Oficina Municipal de Empleo - Búsqueda de Trabajo y Programas de Inserción',
        'categoria': 'Empleo y Desarrollo Económico',
        'organismo_responsable': 'Municipalidad de Posadas - Dirección de la Oficina de Empleo',
        'descripcion': 'Intermediación laboral gratuita para vecinos en búsqueda activa de empleo, registro y carga de CV en la plataforma municipal oficial https://sistemaempleo.posadas.gov.ar/ y portal institucional https://posadas.gov.ar/, programas de capacitación en oficios y entrenamiento para el trabajo.',
        'requisitos': [
            'DNI con domicilio en Posadas.',
            'Constancia de CUIL emitida por ANSES.',
            'Currículum Vitae (CV) actualizado en formato digital o impreso.',
            'Ser mayor de 18 años (o entre 18 y 24 para programas específicos de empleo joven).'
        ],
        'enlace_oficial': 'https://sistemaempleo.posadas.gov.ar/',
        'fecha_verificacion': '2026-11-04',
        'tramite_online': True,
        'texto_boton': 'Registrar CV en el Sistema de Empleo Posadas',
        'fuente': 'Municipalidad de Posadas (https://posadas.gov.ar/) - Oficina de Empleo',
        'palabras_clave': ['oficina de empleo', 'buscar trabajo', 'empleo', 'conseguir trabajo', 'trabajo', 'cv', 'curriculum', 'cargar cv', 'empleo joven', 'bolsa de trabajo', 'capacitacion laboral'],
        'canales_presenciales': 'Oficina de Empleo: Calle Félix de Azara N° 1660 (entre Sarmiento y San Martín), Posadas. Lunes a Viernes de 07:00 a 19:00 hs.',
        'telefono_contacto': '(0376) 443-4254 | Línea CIUDAD: 0800-888-2483'
    },
    {
        'id': 'guia_tramites_muni',
        'nombre': 'Guía General de Trámites y Servicios Municipales',
        'categoria': 'Atención Ciudadana',
        'organismo_responsable': 'Municipalidad de Posadas',
        'descripcion': 'Directorio integral con los requisitos, aranceles, formularios y pasos a seguir para todos los trámites ante las diferentes secretarías y direcciones municipales de la ciudad de Posadas en https://posadas.gov.ar/guiatramite.',
        'requisitos': [
            'Seleccionar el trámite deseado en el buscador de la guía oficial.',
            'DNI del vecino solicitante.'
        ],
        'enlace_oficial': 'https://posadas.gov.ar/guiatramite',
        'fecha_verificacion': '2026-11-04',
        'tramite_online': True,
        'texto_boton': 'Consultar Guía de Trámites de Posadas',
        'fuente': 'Municipalidad de Posadas - Portal Oficial',
        'palabras_clave': ['guia de tramites', 'tramites municipales', 'guia tramites', 'servicios de la muni', 'tramites de la municipalidad', 'servicios municipales'],
        'canales_presenciales': 'Mesa General de Entradas (San Martín 1579) y sedes del Centro de Atención Vecinal (CAV).',
        'telefono_contacto': '0800-888-2483 (Línea CIUDAD Gratuita)'
    },
    {
        'id': 'emsa_factura',
        'nombre': 'Facturación, Pago Online y Consultas de Energía de Misiones',
        'categoria': 'Servicios Eléctricos Comerciales',
        'organismo_responsable': 'Energía de Misiones S.A. (EMSA)',
        'descripcion': 'Descarga directa de facturas de luz, consulta de saldo adeudado y pago electrónico en el Portal de Clientes (https://clientes.energiademisiones.com.ar/). Sitio oficial de Energía de Misiones: https://www.energiademisiones.com.ar/.',
        'requisitos': [
            'Número de usuario y conexión (figuran en el encabezado de la boleta de luz).',
            'DNI o CUIT del titular del servicio.',
            'Medio de pago electrónico habilitado.'
        ],
        'enlace_oficial': 'https://clientes.energiademisiones.com.ar/',
        'fecha_verificacion': '2026-11-04',
        'tramite_online': True,
        'texto_boton': 'Iniciar trámite online',
        'fuente': 'Energía de Misiones S.A. (EMSA) - Sitio Oficial (https://www.energiademisiones.com.ar/)',
        'palabras_clave': ['factura de luz', 'boleta de luz', 'emsa', 'tarifa social', 'pagar luz', 'pago de luz', 'energia de misiones'],
        'canales_presenciales': 'Sedes comerciales EMSA y módulo en el CAV de Lunes a Viernes de 06:30 a 13:00 hs.',
        'telefono_contacto': '(376) 433-4010 (WhatsApp Oficial Comercial)'
    },
    {
        'id': 'iprodha_tramites',
        'nombre': 'Inscripción a Sorteos de Viviendas Sociales y Trámites del IPRODHA',
        'categoria': 'Vivienda y Hábitat',
        'organismo_responsable': 'Instituto Provincial de Desarrollo Habitacional (IProDHa)',
        'descripcion': 'Inscripción digital y actualización de ficha social para participar en sorteos públicos de viviendas ("ganar una casa"), postulación a convocatorias activas (botón PARTICIPAR), pago de cuotas mensuales, regularización dominial y ampliaciones autorizadas ante el IProDHa en https://sistema.iprodha.misiones.gob.ar/ y portal institucional https://iprodha.misiones.gob.ar/.',
        'requisitos': [
            'Crear cuenta o ingresar con CUIL y contraseña en el portal oficial del IPRODHA (https://sistema.iprodha.misiones.gob.ar/).',
            'Completar la Ficha de Inscripción online con datos del grupo familiar, ingresos demostrables y codeudor solidario (garante).',
            'Requisito excluyente: No ser titular ni propietario de ningún inmueble o vivienda social ningún miembro del grupo conviviente.',
            'Residencia legal y continua en la Provincia de Misiones (localidad de Posadas para sorteos locales).',
            'Paso indispensable: Cuando se abra una convocatoria pública para Posadas, ingresar a la cuenta y presionar el botón "PARTICIPAR" antes del cierre del padrón.',
            'Para adjudicatarios actuales: consulta de cuotas, escrituración y autorización previa para ampliaciones.'
        ],
        'enlace_oficial': 'https://sistema.iprodha.misiones.gob.ar/',
        'fecha_verificacion': '2026-11-04',
        'tramite_online': True,
        'texto_boton': 'Inscripción y Ficha Social IPRODHA Online',
        'fuente': 'IProDHa - Gobierno de la Provincia de Misiones (https://iprodha.misiones.gob.ar/)',
        'palabras_clave': [
            'iprodha', 'ganar una casa', 'ganar la casa', 'ganar casa', 'anotarme para una casa', 'anotarme a una casa',
            'anotarme en una casa', 'anotarse para una casa', 'anotarse a una casa', 'anotarme para la casa',
            'donde me anoto para una casa', 'donde se anota para una casa', 'donde anotarse para una casa',
            'como anotarme para una casa', 'donde uno se anota', 'donde anotarse', 'donde me anoto', 'donde me inscribo',
            'inscribirme para una casa', 'inscripcion para vivienda', 'inscripcion de vivienda', 'inscripcion a vivienda',
            'inscripcion a viviendas', 'sorteo de casas', 'sorteo de casa', 'sorteos de casas',
            'sorteo de vivienda', 'sorteos de viviendas', 'sorteo habitacional', 'sorteos habitacionales',
            'sorteo iprodha', 'sorteos iprodha', 'adjudicacion de vivienda', 'adjudicar casa', 'adjudicar vivienda',
            'postularme para una casa', 'postularme a una casa', 'postularse para una casa',
            'vivienda social', 'viviendas sociales', 'plan de viviendas', 'planes de vivienda',
            'como tener una casa', 'conseguir una casa', 'conseguir casa', 'pedir una casa', 'sacar una casa',
            'adjudicatario iprodha', 'cuota iprodha', 'barrio iprodha', 'vivienda iprodha', 'escritura iprodha', 'terreno iprodha'
        ],
        'canales_presenciales': 'Delegación en CAV Itaembé Guazú (Calle Aguará Guazú y Magnolias) y CAV Las Heras (07:00 a 13:00 hs). Sede Central: Av. Roque Pérez y Santa Fe, Posadas.',
        'telefono_contacto': '(0376) 444-7930 | WhatsApp: (376) 490-7605'
    },
    {
        'id': 'registro_civil',
        'nombre': 'Solicitud de Turnos DNI, Pasaporte y Actas (Portal Oficial)',
        'categoria': 'Identidad y Documentación',
        'organismo_responsable': 'Registro Provincial de las Personas de Misiones',
        'descripcion': 'Gestión de trámites de DNI, pasaporte, actas y partidas de nacimiento, matrimonio y defunción a través del portal oficial https://www.registrocivil.misiones.gov.ar/ y delegaciones presenciales en Posadas (Sede Central en Chacra 32-33, CAV Itaembé Guazú y CAV Las Heras).',
        'requisitos': [
            'Para DNI y Pasaporte: DNI vigente o acta de nacimiento según la edad.',
            'Para Actas/Partidas: nombres y apellidos del titular, fecha aproximada del hecho y datos de inscripción.',
            'Abono del arancel provincial correspondiente.'
        ],
        'enlace_oficial': 'https://www.registrocivil.misiones.gov.ar/',
        'fecha_verificacion': '2026-11-08',
        'tramite_online': True,
        'texto_boton': 'Portal Oficial Registro Civil Misiones',
        'fuente': 'Registro Provincial de las Personas de Misiones (https://www.registrocivil.misiones.gov.ar/)',
        'palabras_clave': ['dni', 'documento', 'partida', 'acta', 'nacimiento', 'matrimonio', 'defuncion', 'pasaporte', 'registro civil'],
        'canales_presenciales': 'Sede Central: Av. Andresito s/n (Chacra 32-33 / Bº Cristo Rey). Delegaciones: CAV Itaembé Guazú y CAV Las Heras (07:00 a 13:00 hs).',
        'telefono_contacto': '(0376) 445-8235 / (0376) 445-8226 / (0376) 444-4200'
    },
    {
        'id': 'defensoria_pueblo',
        'nombre': 'Mediación Vecinal Gratuita y Defensa de Derechos',
        'categoria': 'Derechos y Mediación',
        'organismo_responsable': 'Defensoría del Pueblo de la Ciudad de Posadas',
        'descripcion': 'Asesoramiento 100% gratuito, mediación pacífica en conflictos comunitarios entre vecinos y reclamos por servicios públicos en https://defensoriadelpueblodeposadas.gob.ar/acceso-a-justicia-y-mediacion/ y portal web https://defensoriaposadas.gob.ar/.',
        'requisitos': [
            'DNI del vecino solicitante.',
            'Relato sucinto del conflicto o situación vecinal.',
            'Es un servicio público gratuito sin necesidad de patrocinio letrado.'
        ],
        'enlace_oficial': 'https://defensoriadelpueblodeposadas.gob.ar/acceso-a-justicia-y-mediacion/',
        'fecha_verificacion': '2026-11-08',
        'tramite_online': True,
        'texto_boton': 'Solicitar Mediación Comunitaria Online',
        'fuente': 'Defensoría del Pueblo de Posadas (https://defensoriaposadas.gob.ar/ y https://defensoriadelpueblodeposadas.gob.ar/)',
        'palabras_clave': ['defensor', 'defensoria', 'mediacion', 'conflicto barrial', 'problemas vecinales'],
        'canales_presenciales': 'Puesto en CAV Itaembé Guazú (Calle Aguará Guazú y Magnolias) y Sede: Félix de Azara 2438 / Buenos Aires N° 1441, Posadas (07:00 a 13:00 hs). Ubicación: https://www.google.com/maps/search/Defensoria+del+Pueblo+Posadas+Misiones',
        'telefono_contacto': '(0376) 443-3241 / (0376) 444-6580 | WhatsApp: (376) 412-5611'
    },
    {
        'id': 'atencion_cav',
        'nombre': 'Atención General al Vecino y Trámites Integrados CAV',
        'categoria': 'Atención Ciudadana',
        'organismo_responsable': 'Municipalidad de Posadas - Centro de Atención Vecinal (CAV)',
        'descripcion': 'Atención presencial integral, cajas de cobro descentralizadas, asesoramiento municipal y recepción de documentación.',
        'requisitos': [
            'DNI físico.',
            'Comprobante o datos del trámite o tasa a abonar/consultar.'
        ],
        'enlace_oficial': 'https://posadas.gov.ar/',
        'fecha_verificacion': '2026-10-15',
        'tramite_online': False,
        'texto_boton': 'Ver información en portal oficial',
        'fuente': 'Municipalidad de Posadas - Centro de Atención Vecinal',
        'palabras_clave': ['cav', 'centro de atencion vecinal', 'sede cav', 'horario cav', 'las heras', 'itaembe guazu'],
        'canales_presenciales': 'CAV Las Heras (Av. Las Heras 3929) y CAV Itaembé Guazú (Calle Aguará Guazú y Magnolias) de Lunes a Viernes de 07:00 a 18:00 hs.',
        'telefono_contacto': '(0376) 440-9050 | 0800-888-2483'
    },
    {
        'id': 'samsa_factura',
        'nombre': 'Pago de Factura y Consulta de Deuda de Agua - SAMSA',
        'categoria': 'Servicios Públicos / Agua Potable',
        'organismo_responsable': 'Servicios de Aguas de Misiones S.A. (SAMSA)',
        'descripcion': (
            'Gestión y pago de facturas del servicio de agua potable y desagües cloacales. '
            'SAMSA es una empresa privada concesionaria y NO está vinculada al CAV '
            'ni cuenta con oficinas o cajas de cobro en el Centro de Atención al Vecino (CAV) Itaembé Guazú.'
        ),
        'requisitos': [
            'Número de Cuenta SAMSA (figura en el margen superior derecho de tu factura de agua).',
            'Medios de pago electrónicos habilitados (Mercado Pago, Macro Click, Red Link, Banelco, tarjeta de débito o crédito).'
        ],
        'enlace_oficial': 'https://samsa.com.ar/paga-tu-factura/',
        'fecha_verificacion': '2026-11-08',
        'tramite_online': True,
        'texto_boton': 'Pagar Factura SAMSA Online',
        'fuente': 'SAMSA - Servicios de Aguas de Misiones S.A.',
        'palabras_clave': [
            'samsa', 'pagar el agua', 'pagar agua', 'pago de agua', 'pago del agua',
            'factura de agua', 'boleta de agua', 'factura del agua', 'boleta del agua',
            'deuda de agua', 'saldo de agua', 'servicio de agua', 'pagar samsa',
            'factura de samsa', 'boleta de samsa', 'cuenta de agua', 'medidor de agua'
        ],
        'canales_presenciales': 'Sede Central Comercial SAMSA: Av. López y Planes N° 2552, Posadas (06:30 a 14:00 hs). SAMSA NO atiende en el CAV Sede Itaembé Guazú.',
        'telefono_contacto': '0800-888-9980 (Línea gratuita 24 hs) | (0376) 442-8888'
    }
]


def normalizar_texto_catalogo(texto: str) -> str:
    """Normaliza texto a minúsculas y remueve tildes."""
    texto = texto.lower()
    for o, d in [('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u'), ('ü', 'u'), ('ñ', 'n')]:
        texto = texto.replace(o, d)
    return texto


def obtener_catalogo_tramites():
    """Retorna la lista completa y configurable de trámites digitales verificados."""
    return CATALOGO_TRAMITES


def obtener_tramite_por_id(tramite_id: str):
    """Busca un trámite específico por su identificador único."""
    for t in CATALOGO_TRAMITES:
        if t['id'] == tramite_id:
            return t
    return None


def buscar_tramite_por_consulta(texto_consulta: str):
    """
    Busca el trámite más relevante del catálogo para la consulta del vecino.
    Prioriza coincidencias específicas sobre las genéricas.
    """
    t = normalizar_texto_catalogo(texto_consulta)

    # 1. Búsqueda de Organismos presentes en el CAV Itaembé Guazú
    if any(k in t for k in [
        'cav itaembe', 'cav de itaembe', 'itaembe guazu cav', 'organismos del cav',
        'que hay en el cav', 'que organismos hay en el cav', 'organismos presentes en el cav',
        'organismos presentes en el cav de itaembe', 'entidades del cav', 'entidades presentes en el cav',
        'servicios del cav itaembe'
    ]):
        return obtener_tramite_por_id('cav_itaembe_guazu')

    # 2. IPRODHA: Inscripción a sorteos de viviendas ("ganar una casa"), cuotas, adjudicaciones y consultas
    if any(k in t for k in [
        'iprodha', 'ganar una casa', 'ganar la casa', 'ganar casa', 'anotarme para una casa', 'anotarme a una casa',
        'anotarme en una casa', 'anotarse para una casa', 'anotarse a una casa', 'anotarme para la casa',
        'donde me anoto para una casa', 'donde se anota para una casa', 'donde anotarse para una casa',
        'como anotarme para una casa', 'donde uno se anota', 'donde anotarse', 'donde me anoto', 'donde me inscribo',
        'inscribirme para una casa', 'inscripcion para vivienda', 'inscripcion de vivienda', 'inscripcion a vivienda',
        'inscripcion a viviendas', 'sorteo de casas', 'sorteo de casa', 'sorteos de casas',
        'sorteo de vivienda', 'sorteos de viviendas', 'sorteo habitacional', 'sorteos habitacionales',
        'sorteo iprodha', 'sorteos iprodha', 'adjudicacion de vivienda', 'adjudicar casa', 'adjudicar vivienda',
        'postularme para una casa', 'postularme a una casa', 'postularse para una casa',
        'vivienda social', 'viviendas sociales', 'plan de viviendas', 'planes de vivienda',
        'como tener una casa', 'conseguir una casa', 'conseguir casa', 'pedir una casa', 'sacar una casa',
        'adjudicatario iprodha', 'cuota iprodha', 'barrio iprodha', 'vivienda iprodha', 'escritura iprodha', 'terreno iprodha'
    ]):
        return obtener_tramite_por_id('iprodha_tramites')

    # 3. Generar boleta patente / Pagar patente (IPA) - DGR Sin Clave Fiscal
    es_excluido_patente = any(k in t for k in [
        'multa', 'infraccion', 'acta de transito', 'licencia', 'carnet', 'conducir', 'manejar',
        'sem', 'estacionamiento', 'curriculum', 'trabajo', 'empleo', 'danza', 'presupuesto participativo',
        'tgi', 'tasas municipales', 'barrido y limpieza', 'inmuebles', 'mejoras', 'cementerio'
    ])
    if not es_excluido_patente:
        es_consulta_patente = any(k in t for k in [
            'generar boleta patente', 'generar boleta de patente', 'generar boleta automotor',
            'boleta patente', 'boleta de patente', 'boleta del auto', 'boleta automotor',
            'emision de boleta patente', 'emision boleta patente', 'emision boleta automotor',
            'emision de boleta', 'sacar boleta patente', 'imprimir boleta patente',
            'patente', 'patenet', 'automotor', 'vehiculo',
            'pagar patente', 'pago de patente', 'pagar mi patente', 'pagar la patente',
            'deuda de patente', 'deuda automotor', 'patente online', 'dgr sin clave fiscal'
        ]) or bool(re.search(r'\b(ipa|auto|moto)\b', t))
        if es_consulta_patente:
            return obtener_tramite_por_id('patente_automotor')

    # 4. Denuncia por Ruidos Molestos y Música Fuerte (Ordenanza VI – Nº 14 - Control Comunal)
    if any(k in t for k in [
        'ruidos molestos', 'ruido molesto', 'musica fuerte', 'musica alta', 'musica a todo volumen',
        'musica al taco', 'musica a alto volumen', 'vecina ruidosa', 'vecino ruidoso', 'denunciar ruidos',
        'denuncia por ruidos', 'denunciar por ruidos', 'ordenanza vi 14', 'ordenanza ruidos',
        'escucha musica fuerte', 'escuchan musica fuerte', 'ruido de cualquier indole', 'ruidos de cualquier indole'
    ]) or (
        bool(re.search(r'\b(ruido\w*|musica)\b', t)) and bool(re.search(r'\b(molest\w*|fuerte|alta|taco|volumen|noche|vecin\w*|escucha|escuchan)\b', t))
    ):
        return obtener_tramite_por_id('denuncia_ruidos_molestos')

    # 5. Denuncia de Obras Clandestinas, Medianeras y Control de Construcciones (Obras Públicas)
    if any(k in t for k in [
        'denunciar obra', 'denuncia de obra', 'denuncia obra', 'obra clandestina', 'obra sin permiso',
        'construccion clandestina', 'construccion sin permiso', 'muro', 'muros', 'medianera', 'medianeras',
        'pared lindera', 'ocupo mi muro', 'ocuparon mi muro', 'ocupo el muro', 'apoyo en mi muro',
        'apoyo sobre mi muro', 'amplio su casa', 'amplio por mi muro', 'ampliacion de mi vecina',
        'ampliacion del vecino', 'amplaicion', 'construyo sobre mi muro', 'edifico sobre mi muro',
        'levantando pared', 'pared del vecino', 'pared de la vecina', 'obra antirreglamentaria', 'construccion ilegal'
    ]) or (
        bool(re.search(r'\b(muro|medianera|pared)\b', t)) and bool(re.search(r'\b(vecin\w*|ocup\w*|apoy\w*|ampli\w*|ampl\w*|rompi\w*|tir\w*|edific\w*|constru\w*|invad\w*)\b', t))
    ) or (
        bool(re.search(r'\b(denuncia\w*|queja|reclamo)\b', t)) and bool(re.search(r'\b(obra|obras|construccion|ampliacion|amplaicion|amplio|muro|medianera)\b', t))
    ):
        return obtener_tramite_por_id('denuncia_obras')

    # 5. Obras Privadas / Sistema GOP / Planificación Territorial (Secretaría de Planificación)
    if any(k in t for k in [
        'sistema gop', 'gop', 'planurbano', 'plan urbano', 'obras privadas', 'obra privada',
        'planificacion territorial', 'indicadores urbanos', 'numero de finca', 'numeros de finca',
        'baldio a edificado', 'cambio de categoria', 'mensura', 'visado de mensura', 'comodato precario',
        'funcionamiento comercial', 'vallado de obra', 'vallados de obras', 'mejor vivir',
        'plan mejor vivir', 'regularizacion de construcciones', 'construccion existente',
        'obra sin permiso', 'regularizacion de obra', 'regularizacion de obras', 'certificado final de obra',
        'final de obra', 'inspecciones tecnicas', 'ampliar casa', 'ampliar mi casa', 'ampliacion',
        'ampliar la casa', 'agrandar la casa', 'construir mi casa', 'construir', 'construccion',
        'permiso de obra', 'permiso de edificacion', 'planos de obra', 'plano de construccion',
        'edificacion', 'refaccion', 'arquitectura',
        'empezar una obra', 'empezar obra', 'iniciar una obra', 'iniciar obra', 'hacer una obra',
        'arrancar una obra', 'arrancar obra', 'nueva obra', 'obra nueva', 'empezar a construir',
        'iniciar construccion', 'comenzar una obra', 'comenzar obra', 'permiso para construir',
        'permiso para edificar', 'hacer planos', 'presentar planos', 'aprobar planos'
    ]) or bool(re.search(r'\b(empezar|iniciar|arrancar|hacer|comenzar)\b.*?\b(obra|obras|construccion|plano|planos)\b', t)) or (
        bool(re.search(r'\b(obra|obras|construir|construccion|edificar|edificacion)\b', t)) and not any(k in t for k in ['bache', 'asfalto', 'cordon', 'cuadrilla', 'pozo'])
    ):
        if 'iprodha' in t:
            return obtener_tramite_por_id('iprodha_tramites')
        return obtener_tramite_por_id('obras_privadas')

    # 3. Habilitaciones Comerciales e Industriales / Obras Privadas (Funcionamiento Comercial) / Habilitación Eventual Online
    if any(k in t for k in [
        'habilitacion comercial', 'habilitaciones comerciales', 'habilitacion eventual',
        'habilitacion digital', 'habilitacion', 'habilitaciones', 'habilitar negocio',
        'habilitar local', 'abrir local', 'abrir negocio', 'espectaculo', 'evento masivo',
        'eventos masivos', 'comercio', 'local comercial', 'bromatologia', 'habilitacion de negocio',
        'abrir un negocio', 'abrir un local', 'abrir un comercio', 'poner un negocio', 'poner un local',
        'poner un kiosco', 'quise abrir un negocio', 'quiero abrir un negocio', 'iniciar un negocio',
        'abrir comercio', 'habilitar un negocio', 'negocio', 'nuegocio', 'nogio', 'negosio', 'negcio', 'neogcio',
        'kiosco', 'almacen', 'verduleria', 'emprendimiento', 'habilitar un', 'habilitar mi', 'quiero habilitar', 'como habilitar'
    ]) or bool(re.search(r'\b(habilitar|habilito|abrir|poner|iniciar)\b.*?\b(neg\w*|nueg\w*|nog\w*|comer\w*|local\w*|kiosc\w*|almac\w*|tienda\w*|emprend\w*)\b', t)) or (
        bool(re.search(r'\b(habilitar|habilito)\b', t)) and not any(k in t for k in ['clave', 'medidor', 'luz', 'emsa', 'atm', 'dni', 'licencia'])
    ):
        return obtener_tramite_por_id('habilitaciones_comerciales')

    # 4. Trámites Generales y Comunitarios (Danza, Presupuesto Participativo, Notas varias, Ramas)
    if any(k in t for k in [
        'escuela de danza', 'escuela municipal de danza', 'danza', 'presupuesto participativo',
        'notas varias', 'mesa de entradas', 'recoleccion de ramas', 'residuos voluminosos',
        'declaraciones juradas', 'tramites comunitarios', 'proyectos vecinales'
    ]):
        return obtener_tramite_por_id('tramites_comunitarios')

    # 5. Honorable Concejo Deliberante (HCD)
    if any(k in t for k in [
        'concejo deliberante', 'hcd', 'honorable concejo deliberante', 'ordenanza municipal',
        'proyectos ciudadanos', 'atencion hcd', 'digesto juridico'
    ]):
        return obtener_tramite_por_id('hcd_posadas_tramite')

    # 6. Autogestión Tributaria y Pagos (TGI, débito automático, libre deuda, canon bebidas, cementerio, convenios)
    if any(k in t for k in [
        'autogestion', 'tasas municipales', 'tasa municipal', 'tgi', 'tasa general de inmuebles',
        'libre deuda', 'debito automatico', 'canon por venta de bebidas', 'bebidas alcoholicas',
        'tasa de cementerio', 'cementerio', 'publicidad y propaganda', 'carteleria',
        'convenios formalizados', 'plan de pago', 'comprobantes emitidos', 'expedientes de interes publico',
        'domicilio fiscal', 'domicilio fiscal electronico', 'deuda municipal', 'boleta municipal'
    ]):
        return obtener_tramite_por_id('tasas_municipales_autogestion')

    # 7. SEM Posadas (Sistema de Estacionamiento Medido) - usar límite de palabra \bsem\b para no coincidir con "semana"
    if any(k in t for k in ['estacionamiento medido', 'estacionamiento', 'saldo sem', 'app sem', 'pagar sem']) or bool(re.search(r'\bsem\b', t)):
        return obtener_tramite_por_id('sem_estacionamiento')

    # 8. Operativo Descacharrado / Dengue
    if any(k in t for k in ['descacharrado', 'operativo descacharrado', 'dengue', 'cacharros', 'aedes aegypti', 'criaderos de mosquito']):
        return obtener_tramite_por_id('operativo_descacharrado')

    # 9. Oficina de Empleo / Buscar trabajo
    if any(k in t for k in [
        'oficina de empleo', 'buscar trabajo', 'empleo', 'conseguir trabajo', 'cargar cv',
        'curriculum', 'trabajo', 'cv', 'bolsa de trabajo', 'capacitacion laboral', 'empleo joven'
    ]):
        return obtener_tramite_por_id('oficina_empleo')

    # 10. Actas de tránsito / Solicitud de informe de infracciones
    if any(k in t for k in ['actas de transito', 'acta de transito', 'solicitud de informe', 'informe de infracciones']):
        return obtener_tramite_por_id('actas_transito_informe')

    # 11. Guía de trámites municipales
    if any(k in t for k in ['guia de tramites', 'guia tramites', 'tramites municipales', 'servicios de la muni', 'tramites de la municipalidad']):
        return obtener_tramite_por_id('guia_tramites_muni')

    # 12. Licencia / Renovar registro
    if any(k in t for k in ['licencia', 'carnet', 'conducir', 'manejar', 'cenat', 'registro de conducir', 'renovar']):
        return obtener_tramite_por_id('licencia_conducir')

    # 13. Multas / Infracciones de tránsito
    if any(k in t for k in ['multa', 'infraccion', 'tribunal de faltas', 'juzgado de faltas', 'fotomulta', 'alcoholemia']):
        return obtener_tramite_por_id('multas_transito')

    # 14. Patente / Impuesto Automotor
    if bool(re.search(r'\b(patente|automotor|auto|moto|impuesto|atm|tasas|inmobiliario|rentas|ipa)\b', t)):
        return obtener_tramite_por_id('patente_automotor')

    # 15. IPRODHA (sólo si menciona explícitamente iprodha)
    if 'iprodha' in t:
        return obtener_tramite_por_id('iprodha_tramites')

    # 16. Defensoría del Pueblo
    if any(k in t for k in ['defensor', 'defensoria', 'mediacion', 'conflicto barrial']):
        return obtener_tramite_por_id('defensoria_pueblo')

    # 17. Registro de las personas / DNI
    if any(k in t for k in ['dni', 'documento', 'partida', 'acta', 'nacimiento', 'matrimonio', 'defuncion', 'pasaporte', 'registro civil']):
        return obtener_tramite_por_id('registro_civil')

    # 18. EMSA Comercial (factura, pago de luz, etc.)
    if any(k in t for k in [
        'factura de luz', 'boleta de luz', 'emsa', 'tarifa social', 'pagar luz', 'pago de luz', 'energia de misiones',
        'pagar la luz', 'pago de la luz', 'factura de la luz', 'boleta de la luz', 'deuda de luz', 'pagar mi luz',
        'servicio de luz', 'factura de energia', 'boleta de energia', 'pagar energia', 'pagar la energia',
        'saldo de luz', 'luz de mi casa', 'factura de emsa', 'boleta de emsa', 'pagar emsa', 'donde pago la luz',
        'como pagar la luz', 'donde pagar la luz'
    ]) or (
        bool(re.search(r'\b(pagar|pago|abonar|deuda|saldo|boleta|factura)\b.*?\b(luz|electricidad|energia)\b', t)) or
        bool(re.search(r'\b(luz|electricidad|energia)\b.*?\b(pagar|pago|abonar|deuda|saldo|boleta|factura)\b', t))
    ):
        return obtener_tramite_por_id('emsa_factura')

    # 19. SAMSA (pago de agua, factura de agua, etc.)
    if any(k in t for k in [
        'samsa', 'pagar el agua', 'pagar agua', 'pago de agua', 'pago del agua', 'factura de agua',
        'boleta de agua', 'factura del agua', 'boleta del agua', 'deuda de agua', 'saldo de agua',
        'servicio de agua', 'pagar samsa', 'factura de samsa', 'boleta de samsa', 'donde pago el agua',
        'como pagar el agua', 'donde pagar el agua', 'cuenta de agua', 'medidor de agua'
    ]) or (
        bool(re.search(r'\b(pagar|pago|abonar|deuda|saldo|boleta|factura)\b.*?\b(agua|samsa|cloaca)\b', t)) or
        bool(re.search(r'\b(agua|samsa|cloaca)\b.*?\b(pagar|pago|abonar|deuda|saldo|boleta|factura)\b', t))
    ):
        return obtener_tramite_por_id('samsa_factura')

    # CAV General
    return obtener_tramite_por_id('atencion_cav')
