"""
Directorio y Base de Conocimiento Verificada de Organismos y Dependencias.
Municipalidad de Posadas y Provincia de Misiones.

Incluye la nómina oficial de entidades con presencia en el Centro de Atención Vecinal (CAV)
Itaembé Guazú (Calle Aguará Guazú y Magnolias) y CAV Las Heras:
1. Secretaría de Planificación Estratégica y Territorial / Obras Privadas (Sistema GOP)
2. Instituto Provincial de Desarrollo Habitacional (IProDHa)
3. Registro Provincial de las Personas (DNI y Partidas)
4. Agencia Tributaria Misiones (ATM) (Puestos de pago y asesoramiento tributario)
5. Honorable Concejo Deliberante (HCD Posadas - Atención al público y proyectos)
6. Defensoría del Pueblo de la Ciudad de Posadas (Mediación comunitaria)
"""

import re

ORGANISMOS = [
    {
        'id': 'mun_obras_privadas',
        'nombre': 'Municipalidad de Posadas - Secretaría de Planificación Estratégica y Territorial / Obras Privadas',
        'sigla': 'Planificación Territorial y Obras Privadas (GOP)',
        'es_externo': False,
        'presente_cav_itaembe': True,
        'competencia': 'Asesoramiento técnico en regularización de obras y construcciones, plataforma digital GOP para aprobación de planos y mensuras, consulta de indicadores urbanos, número de finca e inspección de obras.',
        'tipos_consultas': [
            'Asesoramiento técnico en regularización de obras y construcciones.',
            'Gestiones e ingresos en la plataforma digital GOP (Gestión de Obras Privadas) para la aprobación de planos y mensuras.',
            'Consulta de indicadores urbanos (FOS, FOT, alturas y retiros), solicitud de número de finca e inspección de obras.',
            'Asignación de números de finca e indicadores urbanos en Itaembé Guazú y Posadas.',
            'Trámites de mensura y visado de expediente para la Dirección de Catastro.',
            'Cambio de categoría (de baldío a edificado).',
            'Certificado de funcionamiento comercial e inspecciones de obras.',
            'Solicitud de Certificado Final de Obra.'
        ],
        'requisitos_oficiales': [
            'Presentación de planos digitales visados por profesional matriculado.',
            'Título de propiedad, boleto de compraventa con sellado de ley o constancia registral / adjudicación IPRODHA.',
            'Libre deuda municipal de Tasa General de Inmuebles (TGI).',
            'Comprobante de inicio de trámite en el Sistema GOP.'
        ],
        'enlaces_oficiales': {
            'portal_oficial': 'https://posadas.gestiondeobrasprivadas.com.ar/',
            'guia_tramites': 'https://posadas.gov.ar/planurbano/guia-de-tramites/'
        },
        'canales_contacto': {
            'telefono_gratuito': '0800-888-2483 (Línea CIUDAD)',
            'atencion_presencial': 'Módulo en CAV Itaembé Guazú (Calle Aguará Guazú y Magnolias) y CAV Las Heras. Edificio Central: San Martín 1579.',
            'horarios': 'Lunes a Viernes de 07:00 a 18:00 hs'
        },
        'fuente_verificacion': 'Municipalidad de Posadas - Secretaría de Planificación Estratégica y Territorial',
        'fecha_verificacion': '2026-11-08',
        'palabras_clave': ['obras privadas', 'planificacion territorial', 'sistema gop', 'gop', 'plataforma gop', 'indicadores urbanos', 'numero de finca', 'numeros de finca', 'regularizacion de obras', 'regularizacion de construcciones', 'inspecciones', 'ampliar casa', 'ampliar mi casa', 'construir', 'permiso de obra', 'permiso de edificacion', 'planos de obra', 'final de obra', 'baldio a edificado', 'mensura', 'vallados de obras']
    },
    {
        'id': 'iprodha',
        'nombre': 'Instituto Provincial de Desarrollo Habitacional (IProDHa)',
        'sigla': 'IProDHa',
        'es_externo': True,
        'presente_cav_itaembe': True,
        'competencia': 'Consultas de adjudicación en el complejo habitacional de Itaembé Guazú, regularización dominial y escrituraciones, planes de pago de cuotas e inscripción a sorteos de viviendas en Misiones.',
        'tipos_consultas': [
            'Consultas de adjudicación: Estado de expedientes y avance de solicitudes de viviendas en el complejo habitacional de Itaembé Guazú.',
            'Regularización dominial: Consultas técnicas sobre escrituraciones, títulos de propiedad y traspasos autorizados.',
            'Planes de pago de cuotas: Asesoramiento sobre deudas de viviendas y emisión de boletas de pago actualizadas.',
            'Inscripción digital y actualización de ficha social para participar en sorteos de viviendas ("ganar una casa").',
            'Postulación a convocatorias activas mediante el botón obligatorio "PARTICIPAR" en la web oficial.'
        ],
        'requisitos_oficiales': [
            'Para inscripción y sorteos: no poseer inmuebles propios ningún miembro del grupo conviviente, contar con residencia permanente en Misiones e ingresos mínimos demostrables con codeudor solidario (garante).',
            'Completar o actualizar la Ficha de Inscripción online cada 360 días en la web oficial (https://sistema.iprodha.misiones.gob.ar/).',
            'Paso indispensable: Cuando se publica una convocatoria para Posadas / Itaembé Guazú, ingresar a la cuenta y pulsar "PARTICIPAR".',
            'Para adjudicatarios existentes: DNI del titular y número de cuenta/contrato.',
            'Para ampliación de vivienda IPRODHA: croquis o plano visado por profesional matriculado y no registrar cuotas impagas.'
        ],
        'enlaces_oficiales': {
            'portal_oficial': 'https://iprodha.misiones.gob.ar/',
            'tramite_cuotas': 'https://sistema.iprodha.misiones.gob.ar/',
            'guia_tramites': 'https://iprodha.misiones.gob.ar/',
            'tramite_inscripcion': 'https://sistema.iprodha.misiones.gob.ar/'
        },
        'canales_contacto': {
            'telefono': '(0376) 444-7930',
            'whatsapp': '(376) 490-7605',
            'whatsapp_url': 'https://wa.me/5493764907605',
            'atencion_presencial': 'Delegación CAV Itaembé Guazú (Calle Aguará Guazú y Magnolias) y módulo CAV Las Heras. Sede Central: Av. Roque Pérez y Santa Fe, Posadas.',
            'horarios': 'Lunes a Viernes de 07:00 a 13:00 hs'
        },
        'fuente_verificacion': 'Gobierno de la Provincia de Misiones - IProDHa',
        'fecha_verificacion': '2026-11-04',
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
            'adjudicatario iprodha', 'cuota iprodha', 'barrio iprodha', 'vivienda iprodha', 'escrituracion iprodha',
            'iprodha itaembe'
        ]
    },
    {
        'id': 'registro_civil',
        'nombre': 'Registro Provincial de las Personas de Misiones',
        'sigla': 'Registro Provincial de las Personas',
        'es_externo': True,
        'presente_cav_itaembe': True,
        'competencia': 'Documento Nacional de Identidad (nuevo ejemplar por extravío/deterioro, cambio de domicilio y actualizaciones obligatorias de menores y mayores), DNI 0 Año / recién nacidos, pasaportes regulares y trámites civiles (matrimonios y uniones convivenciales).',
        'tipos_consultas': [
            'Documento Nacional de Identidad: Tramitación de nuevo ejemplar de DNI por extravío, robo o deterioro, cambio de domicilio y actualizaciones obligatorias (tanto de menores como de mayores).',
            'DNI 0 Año / Recién nacidos: Primer documento e inscripción del nacimiento.',
            'Pasaportes: Tramitación y renovación del pasaporte regular (se requiere el último DNI físico).',
            'Trámites civiles: Celebración y registro de matrimonios, así como la gestión de uniones convivenciales.',
            'Solicitud y expedición de partidas y actas de nacimiento, matrimonio y defunción.'
        ],
        'requisitos_oficiales': [
            'Para DNI: DNI anterior o partida de nacimiento original actualizada según la edad (obligatoria para actualizaciones de menores de 5 a 8 años y 14 años).',
            'Para DNI 0 Año / Recién nacidos: Certificado médico de nacimiento original expedido por el hospital/sanatorio y DNI de los progenitores.',
            'Para Pasaportes: DNI tarjeta físico vigente en buen estado.',
            'Para Matrimonios y Uniones Convivenciales: DNI de ambos contrayentes, actas de nacimiento actualizadas y 2 a 4 testigos mayores con DNI.',
            '💳 NOTA IMPORTANTE OBLIGATORIA: Los pagos de aranceles en esta oficina se realizan ÚNICAMENTE con medios digitales (tarjeta de débito, crédito o código QR); NO se acepta dinero en efectivo.'
        ],
        'enlaces_oficiales': {
            'portal_oficial': 'https://www.registrocivil.misiones.gov.ar/',
            'portal_institucional': 'https://www.registrocivil.misiones.gov.ar/',
            'mapa_sedes': 'https://www.google.com/maps/search/Registro+Provincial+de+las+Personas+Posadas+Misiones',
            'tramites_dni': 'https://mi.argentina.gob.ar/'
        },
        'canales_contacto': {
            'telefono': '(0376) 445-8235 / (0376) 445-8226 / (0376) 444-4200',
            'atencion_presencial': 'Sede Central: Av. Andresito s/n (Bº Cristo Rey, Chacra 32-33). Delegaciones CAV: CAV Itaembé Guazú (Calle Aguará Guazú y Magnolias) y CAV Las Heras (07:00 a 13:00 hs). Ver sedes en Google Maps.',
            'horarios': 'Lunes a Viernes de 07:00 a 12:30 hs (CAVs hasta las 13:00 hs)'
        },
        'fuente_verificacion': 'Registro Provincial de las Personas de Misiones',
        'fecha_verificacion': '2026-11-04',
        'palabras_clave': ['registro civil', 'dni', 'partida', 'acta', 'nacimiento', 'matrimonio', 'defuncion', 'pasaporte', 'registro de las personas', 'registro civil itaembe']
    },
    {
        'id': 'atm_misiones',
        'nombre': 'Agencia Tributaria Misiones (ATM)',
        'sigla': 'ATM Misiones',
        'es_externo': True,
        'presente_cav_itaembe': True,
        'competencia': 'Generación y reimpresión de boletas y planes de pago provinciales, gestión y asesoramiento en Clave Fiscal ATM, Mesa de Entradas Fiscal y cobro presencial con tarjetas de débito y crédito habilitadas.',
        'tipos_consultas': [
            'Generación y reimpresión de boletas: Emisión de planes de pago y obligaciones fiscales provinciales (Ingresos Brutos, Impuesto Inmobiliario Provincial, IPA Automotor).',
            'Clave Fiscal: Asesoramiento personalizado y asistencia técnica para gestionar u obtener la clave fiscal de ATM.',
            'Mesa de Entradas Fiscal: Recepción formal de notas, descargos y presentaciones institucionales escritas.',
            'Orientación digital: Soporte guiado para la realización de trámites online y uso del puesto de autogestión en la oficina.',
            'Pagos: Cobro presencial de tributos mediante tarjetas de débito y crédito habilitadas.'
        ],
        'requisitos_oficiales': [
            'Número de dominio (patente del vehículo) para IPA.',
            'DNI o CUIT/CUIL del contribuyente.',
            'Comprobante o volante de pago en caso de trámites presenciales.'
        ],
        'enlaces_oficiales': {
            'portal_oficial': 'https://sinclavefiscal.atm.misiones.gob.ar/sc/automotor/emision_ba_ipa',
            'pago_patente_ipa': 'https://sinclavefiscal.atm.misiones.gob.ar/sc/automotor/emision_ba_ipa',
            'portal_institucional': 'https://www.atm.misiones.gob.ar/'
        },
        'canales_contacto': {
            'telefono': '0810-444-5505',
            'whatsapp': '(0376) 428-2000',
            'atencion_presencial': 'Puesto de cobro y atención en CAV Itaembé Guazú y CAV Las Heras (07:00 a 18:00 hs). Sede Central: San Martín 1754 (07:00 a 13:00 hs).',
            'horarios': 'Lunes a Viernes de 07:00 a 18:00 hs'
        },
        'fuente_verificacion': 'Agencia Tributaria Misiones (ATM) - Portal Oficial',
        'fecha_verificacion': '2026-11-04',
        'palabras_clave': ['atm', 'agencia tributaria misiones', 'rentas', 'impuesto provincial automotor', 'ipa', 'patente atm', 'ingresos brutos', 'sellos', 'atm itaembe']
    },
    {
        'id': 'mun_delegacion_itaembe',
        'nombre': 'Municipalidad de Posadas - Delegación CAV Itaembé Guazú',
        'sigla': 'Delegación Municipal CAV Itaembé Guazú',
        'es_externo': False,
        'presente_cav_itaembe': True,
        'competencia': 'Atención presencial integral: emisión y actualización de boletas (TGI y Patentes), convenios de pago, trámites de automotores (empadronamiento, denuncia de venta, libre deuda), liquidación y emisión de tasas de carnet sanitario, y mesa de entradas y reclamos de servicios públicos.',
        'tipos_consultas': [
            'Emisión y actualización de boletas: Impresión de tasas e impuestos municipales como la Tasa General de Inmuebles (TGI), patentes de autos y motos.',
            'Convenios de pago: Formalización de planes de pago y regularización de deudas tributarias municipales.',
            'Trámites de automotores: Empadronamiento de vehículos, presentación de denuncias de venta y solicitud de certificados de libre deuda.',
            'Habilitaciones comerciales: Asesoramiento general e inicio de gestiones para abrir comercios.',
            'Carnet sanitario: Liquidación y emisión de tasas correspondientes para la gestión y renovación del carnet.',
            'Mesa de entradas y reclamos: Inicio de expedientes, solicitudes de servicios públicos (retiro de árboles, luminarias, etc.) y quejas comunitarias.'
        ],
        'requisitos_oficiales': [
            'DNI del vecino solicitante.',
            'Para automotores: Título o cédula del vehículo, constancia de radicación o formulario 08 / denuncia de venta.',
            'Para TGI: Número de Partida Inmobiliaria de la propiedad.',
            'Para Carnet Sanitario: DNI, foto 4x4 o selfie clara y constancia de manipulación de alimentos (si aplica).',
            'Para Convenios de Pago: CUIT/CUIL y DNI del titular de la cuenta tributaria.'
        ],
        'enlaces_oficiales': {
            'portal_oficial': 'https://posadas.gov.ar/',
            'guiatramite': 'https://posadas.gov.ar/guiatramite'
        },
        'canales_contacto': {
            'telefono': '0800-888-2483 (Línea CIUDAD)',
            'atencion_presencial': 'Sede CAV Itaembé Guazú: Calle Aguará Guazú y Magnolias, Posadas.',
            'horarios': 'Lunes a Viernes de 07:00 a 18:00 hs'
        },
        'fuente_verificacion': 'Municipalidad de Posadas - Centro de Atención Vecinal (CAV) Itaembé Guazú',
        'fecha_verificacion': '2026-11-08',
        'palabras_clave': ['cav itaembe', 'delegacion itaembe', 'carnet sanitario', 'convenio de pago', 'empadronamiento', 'denuncia de venta', 'libre deuda automotor', 'tgi itaembe', 'patente itaembe', 'mesa de entrada itaembe', 'boleta municipal itaembe']
    },
    {
        'id': 'hcd_posadas',
        'nombre': 'Honorable Concejo Deliberante de la Ciudad de Posadas (HCD)',
        'sigla': 'HCD Posadas',
        'es_externo': False,
        'presente_cav_itaembe': True,
        'competencia': 'Recepción de iniciativas legislativas, proyectos de ordenanza, ideas de mejora barrial y peticiones particulares de los vecinos para tratamiento en el Concejo Deliberante.',
        'tipos_consultas': [
            'Iniciativas legislativas: Recepción de proyectos, ideas o peticiones particulares de los vecinos para ser presentadas ante el Concejo Deliberante de Posadas.',
            'Presentación formal de notas e iniciativas de comisiones barriales.',
            'Asesoramiento sobre ordenanzas municipales vigentes y digesto jurídico.'
        ],
        'requisitos_oficiales': [
            'DNI del vecino solicitante.',
            'Nota o proyecto con fundamentación clara y firmas de vecinos de la zona en caso de peticiones comunitarias.',
            'Trámite 100% público y gratuito.'
        ],
        'enlaces_oficiales': {
            'portal_oficial': 'https://hcdposadas.gob.ar/'
        },
        'canales_contacto': {
            'telefono': '(0376) 449-0800',
            'atencion_presencial': 'Puesto de Atención al Público en CAV Itaembé Guazú (Calle Aguará Guazú y Magnolias). Sede Central HCD: Calle Bolívar N° 1588, Posadas.',
            'horarios': 'Lunes a Viernes de 07:00 a 18:00 hs'
        },
        'fuente_verificacion': 'Honorable Concejo Deliberante de Posadas - Portal Oficial',
        'fecha_verificacion': '2026-11-08',
        'palabras_clave': ['concejo deliberante', 'hcd', 'honorable concejo deliberante', 'ordenanza', 'proyecto vecinal', 'iniciativa legislativa', 'digesto', 'hcd itaembe', 'atencion concejo deliberante']
    },
    {
        'id': 'defensoria_pueblo',
        'nombre': 'Defensoría del Pueblo de la Ciudad de Posadas',
        'sigla': 'Defensoría del Pueblo',
        'es_externo': True,
        'presente_cav_itaembe': True,
        'competencia': 'Atención al ciudadano y recepción de reclamos por vulneración de derechos o fallas graves en servicios públicos, asesoramiento legal gratuito y mediación comunitaria voluntaria.',
        'tipos_consultas': [
            'Atención al ciudadano: Recepción de reclamos vecinales relacionados con la vulneración de derechos o fallas graves en servicios públicos (agua, luz, transporte).',
            'Asesoramiento legal gratuito: Orientación jurídica primaria sobre problemáticas barriales, de consumo o administrativas de los ciudadanos.',
            'Dirección de Mediación Comunitaria: Audiencias y conciliación voluntaria para la resolución pacífica de conflictos entre vecinos (ruidos molestos, medianeras, mascotas, etc.).',
            'Orientación y patrocinio en defensa de usuarios y consumidores.'
        ],
        'requisitos_oficiales': [
            'DNI del vecino solicitante.',
            'Domicilio en la ciudad de Posadas.',
            'Relato de los hechos, copias de reclamos previos ante empresas prestadoras o datos del vecino para mediación voluntaria.',
            'Servicio 100% público y gratuito sin patrocinio letrado obligatorio.'
        ],
        'enlaces_oficiales': {
            'portal_oficial': 'https://defensoriadelpueblodeposadas.gob.ar/acceso-a-justicia-y-mediacion/',
            'portal_institucional': 'https://defensoriadelpueblodeposadas.gob.ar/',
            'formulario_contacto': 'https://defensoriadelpueblodeposadas.gob.ar/contacto/',
            'formulario_reclamo': 'https://defensoriadelpueblodeposadas.gob.ar/',
            'mediacion_vecinal': 'https://defensoriadelpueblodeposadas.gob.ar/acceso-a-justicia-y-mediacion/',
            'portal_historico': 'https://defensoriaposadas.gob.ar/'
        },
        'canales_contacto': {
            'telefono': '(0376) 443-3241 / (0376) 444-6580',
            'whatsapp': '+54 9 376 412-5611',
            'whatsapp_url': 'https://wa.me/5493764125611',
            'atencion_presencial': 'Puesto de Atención en CAV Itaembé Guazú (Calle Aguará Guazú y Magnolias). Sede: Félix de Azara 2438 / Buenos Aires N° 1441, Posadas. Ver ubicación en Google Maps.',
            'horarios': 'Lunes a Viernes de 07:00 a 13:00 hs'
        },
        'fuente_verificacion': 'Defensoría del Pueblo de la Ciudad de Posadas - Portal Institucional',
        'fecha_verificacion': '2026-11-04',
        'palabras_clave': ['defensoria', 'defensor', 'conflicto vecinal', 'mediacion', 'problemas con vecinos', 'defensoria itaembe']
    },
    {
        'id': 'mun_ruidos_molestos',
        'nombre': 'Municipalidad de Posadas - Dirección de Control Comunal (Guardia de Ruidos Molestos)',
        'sigla': 'Control Comunal - Ruidos Molestos',
        'es_externo': False,
        'presente_cav_itaembe': False,
        'competencia': 'Recepción de denuncias, mediciones sonométricas y constatación de infracciones por ruidos molestos, música desmedida y afección al descanso bajo la Ordenanza VI – Nº 14 de Posadas.',
        'tipos_consultas': [
            'Denuncias por música alta o ruidos molestos en horario de siesta (13:00 a 15:00 hs) o nocturnidad (22:00 a 06:00 hs).',
            'Fiscalización de actividades con emisión sonora en la vía pública o inmuebles particulares.',
            'Medición de decibeles y labrado de actas de infracción remitidas al Tribunal Municipal de Faltas.',
            'Coordinación con la Guardia Municipal y Línea 911 en flagrancia nocturna.'
        ],
        'requisitos_oficiales': [
            'Dirección exacta o altura del inmueble o vecino denunciado (calle, número o entrecalles, barrio en Posadas).',
            'Nombre del vecino/a o titular si se conoce (o características del inmueble).',
            'Relato circunstanciado: días y horarios en que ocurren los ruidos y tipo de sonido perturbador.',
            'Datos de contacto del vecino denunciante.'
        ],
        'enlaces_oficiales': {
            'portal_oficial': 'https://posadas.gov.ar/',
            'whatsapp_guardia': 'https://wa.me/5493764134650'
        },
        'canales_contacto': {
            'whatsapp': '(376) 413-4650',
            'whatsapp_url': 'https://wa.me/5493764134650',
            'telefono_gratuito': '0800-888-2483 (Línea CIUDAD)',
            'atencion_presencial': 'Dirección General de Control Comunal / Mesa de Entradas: San Martín 1579, Posadas.',
            'horarios': 'Guardia activa en horarios de descanso (siestas y fines de semana). Línea 911 en flagrancia nocturna.'
        },
        'fuente_verificacion': 'Municipalidad de Posadas - Ordenanza VI – Nº 14',
        'fecha_verificacion': '2026-11-08',
        'palabras_clave': [
            'ruidos molestos', 'ruido molesto', 'musica fuerte', 'musica alta', 'musica a todo volumen',
            'musica al taco', 'musica a alto volumen', 'vecina ruidosa', 'vecino ruidoso', 'denunciar ruidos',
            'denuncia por ruidos', 'ordenanza vi 14', 'ordenanza ruidos', 'denunciar a mi vecina',
            'denunciar vecina', 'denunciar vecino', 'vecina que escucha musica', 'vecino que escucha musica',
            'ruidos molestos municipalidad', 'guardia ruidos molestos'
        ]
    },
    {
        'id': 'mun_habilitaciones',
        'nombre': 'Municipalidad de Posadas - Dirección General de Habilitaciones Comerciales',
        'sigla': 'Habilitaciones Comerciales Municipal',
        'es_externo': False,
        'presente_cav_itaembe': False,
        'competencia': 'Otorgamiento y control de habilitaciones comerciales digitales y habilitaciones eventuales para eventos o espectáculos en Posadas.',
        'tipos_consultas': [
            'Habilitación Comercial Digital (alta de comercios nuevos, mudanzas, cambios de rubro o transferencias).',
            'Habilitación Eventual Online (espectáculos o eventos masivos a través del Portal Ciudadano).',
            'Certificaciones de Bromatología e inspección de seguridad en locales.'
        ],
        'requisitos_oficiales': [
            'DNI del titular o estatuto/poder y CUIT de la razón social.',
            'Contrato de locación sellado o título de propiedad del local.',
            'Certificado de seguridad contra incendios expedido por Bomberos de la Policía de Misiones.',
            'Para habilitación eventual: seguros de responsabilidad civil, planos de emergencia y subsanación digital.'
        ],
        'enlaces_oficiales': {
            'portal_oficial': 'https://datos.posadas.gov.ar/habilitaciones-municipales/'
        },
        'canales_contacto': {
            'telefono_gratuito': '0800-888-2483',
            'atencion_presencial': 'San Martín 1579 (Mesa de Entradas) y módulos en sedes CAV.',
            'horarios': 'Lunes a Viernes de 07:00 a 18:00 hs'
        },
        'fuente_verificacion': 'Municipalidad de Posadas - Dirección General de Habilitaciones Comerciales',
        'fecha_verificacion': '2026-11-04',
        'palabras_clave': ['habilitacion comercial', 'habilitacion eventual', 'habilitacion digital', 'habilitaciones', 'habilitar negocio', 'habilitar local', 'abrir local', 'abrir negocio', 'eventos masivos', 'espectaculo', 'bromatologia']
    },
    {
        'id': 'mun_empleo',
        'nombre': 'Municipalidad de Posadas - Dirección de la Oficina de Empleo',
        'sigla': 'Oficina de Empleo Municipal',
        'es_externo': False,
        'presente_cav_itaembe': False,
        'competencia': 'Intermediación laboral gratuita, registro de postulantes, programas de inserción laboral y capacitación técnica en Posadas.',
        'tipos_consultas': [
            'Búsqueda activa de trabajo y registro en la base laboral municipal.',
            'Carga y actualización de Currículum Vitae (CV).',
            'Programas de empleo joven y capacitación en oficios.'
        ],
        'requisitos_oficiales': [
            'DNI con domicilio en Posadas.',
            'Constancia de CUIL emitida por ANSES.',
            'Currículum Vitae actualizado.'
        ],
        'enlaces_oficiales': {
            'portal_oficial': 'https://posadas.gov.ar/'
        },
        'canales_contacto': {
            'telefono': '(0376) 443-4254',
            'telefono_gratuito': '0800-888-2483',
            'atencion_presencial': 'Félix de Azara 1660 (entre Sarmiento y San Martín), Posadas.',
            'horarios': 'Lunes a Viernes de 07:00 a 19:00 hs'
        },
        'fuente_verificacion': 'Municipalidad de Posadas - Oficina de Empleo',
        'fecha_verificacion': '2026-11-04',
        'palabras_clave': ['oficina de empleo', 'buscar trabajo', 'empleo', 'conseguir trabajo', 'curriculum', 'cv', 'cargar cv']
    },
    {
        'id': 'mun_salud_descacharrado',
        'nombre': 'Municipalidad de Posadas - Secretaría de Salud y Calidad de Vida (Operativo Descacharrado)',
        'sigla': 'Salud Municipal - Descacharrado',
        'es_externo': False,
        'presente_cav_itaembe': False,
        'competencia': 'Prevención epidemiológica, operativos barriales de descacharrado y lucha contra el mosquito vector del Dengue en Posadas.',
        'tipos_consultas': [
            'Cronograma barrial del Operativo Descacharrado.',
            'Eliminación de criaderos de mosquitos y recolección de cacharros.',
            'Medidas preventivas contra el Dengue, Chikungunya y Zika.'
        ],
        'requisitos_oficiales': [
            'Colocar recipientes y objetos en desuso en la vereda en las fechas fijadas para su chacra o barrio.'
        ],
        'enlaces_oficiales': {
            'portal_oficial': 'https://posadas.gov.ar/'
        },
        'canales_contacto': {
            'telefono_gratuito': '0800-888-2483',
            'atencion_presencial': 'Centros de Integración Territorial (CIT) y sedes CAV.',
            'horarios': 'Lunes a Viernes de 07:00 a 18:00 hs'
        },
        'fuente_verificacion': 'Municipalidad de Posadas - Salud y Calidad de Vida',
        'fecha_verificacion': '2026-11-04',
        'palabras_clave': ['descacharrado', 'operativo descacharrado', 'dengue', 'cacharros', 'aedes aegypti']
    },
    {
        'id': 'mun_obras_publicas',
        'nombre': 'Municipalidad de Posadas - Secretaría de Obras Públicas',
        'sigla': 'Obras Públicas Municipal',
        'es_externo': False,
        'presente_cav_itaembe': False,
        'competencia': 'Mantenimiento de la trama vial urbana, bacheo de asfalto, perfilado de calles de tierra, cordón cuneta y obras hidráulicas en Posadas.',
        'tipos_consultas': [
            'Reparación de baches y pozos en calles asfaltadas.',
            'Nivelación y entoscado de calles de tierra.',
            'Reparación de sumideros y bocas de tormenta obstruidas o rotas.',
            'Construcción y reparación de cordón cuneta y veredas públicas.'
        ],
        'requisitos_oficiales': [
            'Ubicación precisa: calle, altura o intersección entre calles.',
            'Barrio o Chacra de Posadas.',
            'Fotografía ilustrativa (opcional).'
        ],
        'enlaces_oficiales': {
            'portal_oficial': 'https://posadas.gov.ar/',
            'turnos': 'https://posadas.gov.ar/turnos/'
        },
        'canales_contacto': {
            'telefono_gratuito': '0800-888-2483 (Línea CIUDAD Posadas)',
            'whatsapp_reclamos': '(376) 443-7012',
            'atencion_presencial': 'Centro de Atención Vecinal (CAV) Las Heras y CAV Itaembé Guazú.',
            'horarios': 'Lunes a Viernes de 07:00 a 19:00 hs'
        },
        'fuente_verificacion': 'Municipalidad de Posadas - Secretaría de Obras Públicas',
        'fecha_verificacion': '2026-11-01',
        'palabras_clave': ['bache', 'pozo', 'calle rota', 'asfalto', 'cordon cuneta', 'calle de tierra', 'sumidero']
    },
    {
        'id': 'mun_servicios_urbanos',
        'nombre': 'Municipalidad de Posadas - Secretaría de Servicios Urbanos',
        'sigla': 'Servicios Urbanos Municipal',
        'es_externo': False,
        'presente_cav_itaembe': False,
        'competencia': 'Alumbrado público, recolección de residuos domiciliarios y voluminosos, barrido y limpieza urbana.',
        'tipos_consultas': [
            'Reparación o cambio de luminarias y focos de alumbrado público apagados o titilando.',
            'Recolección especial de residuos voluminosos o restos de poda.',
            'Mantenimiento y reposición de contenedores plásticos/metálicos.',
            'Erradicación de microbasurales en esquinas o terrenos baldíos.'
        ],
        'requisitos_oficiales': [
            'Identificación del poste o columna (número de poste si es visible).',
            'Barrio y entre calles donde se ubica el foco o contenedor.',
            'Fotografía (opcional).'
        ],
        'enlaces_oficiales': {
            'portal_oficial': 'https://posadas.gov.ar/',
            'atencion_vecinal': 'https://posadas.gov.ar/'
        },
        'canales_contacto': {
            'telefono_gratuito': '0800-888-2483 (Línea CIUDAD)',
            'whatsapp_reclamos': '(376) 443-7012',
            'atencion_presencial': 'CAV Las Heras (Av. Las Heras 3929) y CAV Itaembé Guazú.',
            'horarios': 'Lunes a Viernes de 07:00 a 18:00 hs'
        },
        'fuente_verificacion': 'Municipalidad de Posadas - Servicios Urbanos',
        'fecha_verificacion': '2026-11-01',
        'palabras_clave': ['luz quemada', 'luminaria', 'foco', 'farola', 'alumbrado publico', 'basura', 'contenedor', 'microbasural']
    },
    {
        'id': 'mun_espacios_verdes',
        'nombre': 'Municipalidad de Posadas - Dirección de Espacios Verdes',
        'sigla': 'Espacios Verdes Municipal',
        'es_externo': False,
        'presente_cav_itaembe': False,
        'competencia': 'Mantenimiento del arbolado urbano, plazas, bulevares y parques públicos de la ciudad.',
        'tipos_consultas': [
            'Poda de despeje por ramas que obstruyen luminarias o señalización.',
            'Evaluación de árboles secos o con riesgo de desprendimiento de ramas.',
            'Mantenimiento, desmalezado y corte de pasto en plazas barriales.',
            'Retiro de ramas caídas en la calzada o vereda pública tras tormentas.'
        ],
        'requisitos_oficiales': [
            'Dirección y barrio del árbol o predio verde.',
            'Descripción del estado fitosanitario o riesgo de caída.',
            'Nota: la poda particular sin autorización sobre árboles en vereda está sujeta a normativa municipal.'
        ],
        'enlaces_oficiales': {
            'portal_oficial': 'https://posadas.gov.ar/'
        },
        'canales_contacto': {
            'telefono_gratuito': '0800-888-2483',
            'atencion_presencial': 'CAVs Municipales de Lunes a Viernes de 07:00 a 18:00 hs.'
        },
        'fuente_verificacion': 'Municipalidad de Posadas - Espacios Verdes',
        'fecha_verificacion': '2026-11-01',
        'palabras_clave': ['arbol', 'poda', 'ramas', 'plaza', 'desmalezado', 'pasto']
    },
    {
        'id': 'tribunal_faltas',
        'nombre': 'Tribunal Municipal de Faltas de Posadas',
        'sigla': 'Tribunal de Faltas',
        'es_externo': False,
        'presente_cav_itaembe': False,
        'competencia': 'Juzgamiento y resolución de infracciones a ordenanzas municipales de tránsito, bromatología, obras y ambiente.',
        'tipos_consultas': [
            'Consulta de actas de infracción de tránsito y fotomultas.',
            'Presentación de descargos legales ante los Juzgados N° 1, 2 y 3.',
            'Emisión del certificado de Libre Deuda de Faltas (requisito para carnet).',
            'Planes de pago y regularización de multas.'
        ],
        'requisitos_oficiales': [
            'DNI del titular o cédula de identificación del vehículo.',
            'Número de acta o cédula de notificación.',
            'Para descargos: por escrito dentro de los plazos procesales establecidos.'
        ],
        'enlaces_oficiales': {
            'portal_oficial': 'https://posadas.gov.ar/',
            'turnos': 'https://posadas.gov.ar/turnos/'
        },
        'canales_contacto': {
            'telefono': '(0376) 443-7705',
            'atencion_presencial': 'San Martín 1555 (entre Rivadavia y Buenos Aires), Posadas.',
            'horarios': 'Lunes a Viernes de 07:00 a 19:00 hs'
        },
        'fuente_verificacion': 'Tribunal Municipal de Faltas de Posadas',
        'fecha_verificacion': '2026-11-01',
        'palabras_clave': ['multa', 'infraccion', 'tribunal de faltas', 'juzgado de faltas', 'libre deuda', 'fotomulta', 'acta']
    },
    {
        'id': 'emsa',
        'nombre': 'Energía de Misiones S.A. (EMSA)',
        'sigla': 'EMSA',
        'es_externo': True,
        'presente_cav_itaembe': True,
        'competencia': 'Altas de nuevas conexiones residenciales y comerciales, bajas y mudanzas, reconexiones tras corte, gestión de reclamos comerciales o técnicos por sobrefacturación y tensión en Itaembé Guazú y Posadas.',
        'tipos_consultas': [
            'Altas de servicio: Solicitud y tramitación de nuevas conexiones de medidores residenciales o comerciales.',
            'Bajas y mudanzas: Desconexión y cese del suministro eléctrico.',
            'Reconexiones: Solicitud de restablecimiento del servicio eléctrico tras cortes o suspensiones.',
            'Reclamos comerciales y técnicos: Gestión de quejas por sobrefacturación, inconvenientes de tensión o daños en las redes de la zona.',
            'Pago online y descarga de facturas mensuales de suministro eléctrico.'
        ],
        'requisitos_oficiales': [
            'Para Altas de servicio: Título de propiedad, contrato de locación sellado o acta de entrega IPRODHA, DNI del titular y Certificado de Aptitud de Instalación Eléctrica visado por electricista matriculado.',
            'Para Bajas y mudanzas: Número de Usuario y Conexión, DNI del titular y última factura abonada.',
            'Para Reconexiones: Comprobante de pago del saldo regularizado y tasa de reconexión.',
            'Para Reclamos comerciales o técnicos: Número de Usuario y Conexión, detalle de artefactos afectados o factura cuestionada.'
        ],
        'enlaces_oficiales': {
            'portal_oficial': 'https://clientes.energiademisiones.com.ar/',
            'gestion_facturas': 'https://clientes.energiademisiones.com.ar/',
            'portal_institucional': 'https://www.energiademisiones.com.ar/',
            'whatsapp_oficial': 'https://wa.me/5493764242514'
        },
        'canales_contacto': {
            'telefono_urgencias': '0800 888 3672 (Línea de Guardia Técnica 24 hs)',
            'whatsapp': '+54 9 376 424-2514',
            'atencion_presencial': 'Puesto de Atención en CAV Itaembé Guazú (Calle Aguará Guazú y Magnolias) y CAV Las Heras. Sede Comercial Central: Rioja 2051, Posadas.',
            'horarios': 'Comercial: 06:30 a 13:00 hs (CAV hasta las 13:00 hs) | Urgencias Técnicas: 24 hs'
        },
        'fuente_verificacion': 'Energía de Misiones S.A. - Puesto CAV Itaembé Guazú y Canales Oficiales',
        'fecha_verificacion': '2026-11-08',
        'palabras_clave': ['emsa', 'energia de misiones', 'luz', 'factura de luz', 'corte de luz', 'transformador', 'baja tension', 'alta de luz', 'pedir medidor', 'nueva conexion emsa', 'baja de luz', 'reconexion emsa', 'sobrefacturacion emsa', 'emsa itaembe']
    },
    {
        'id': 'samsa',
        'nombre': 'Servicios de Aguas de Misiones S.A. (SAMSA)',
        'sigla': 'SAMSA',
        'es_externo': True,
        'presente_cav_itaembe': False,
        'competencia': 'Empresa privada concesionaria del servicio de agua potable y desagües cloacales en las ciudades de Posadas y Garupá. NO está vinculada al CAV ni cuenta con puesto presencial o cajas de cobro en el Centro de Atención al Vecino (CAV) Sede Itaembé Guazú.',
        'tipos_consultas': [
            'Pago online de facturas y regularización de deuda.',
            'Consulta de saldo y descarga de boleta digital de agua.',
            'Reclamos por pérdidas de agua en vereda o calzada pública.',
            'Falta de presión o interrupción del suministro de agua potable.',
            'Desobstrucción y mantenimiento de redes cloacales en la vía pública.'
        ],
        'requisitos_oficiales': [
            'Número de Cuenta SAMSA (figura en el margen superior derecho de tu factura).',
            'Medios de pago electrónicos habilitados (Mercado Pago, Macro Click, Red Link, Banelco o tarjetas de débito/crédito).',
            'Dirección exacta del suministro o inmueble (calle, número y barrio).'
        ],
        'enlaces_oficiales': {
            'portal_oficial': 'https://samsa.com.ar/paga-tu-factura/',
            'tramite_inscripcion': 'https://samsa.com.ar/paga-tu-factura/',
            'oficina_virtual': 'https://intranet.samsa.com.ar/apex/f?p=1000:200',
            'portal_institucional': 'https://samsa.com.ar/'
        },
        'canales_contacto': {
            'telefono_atencion': '0800-888-9980 (Línea gratuita 24 hs)',
            'telefono_linea': '(0376) 442-8888 / 442-8000',
            'email': 'consultas@samsa.com.ar',
            'atencion_presencial': 'Av. López y Planes N° 2552 (entre Corrientes y Lavalle), Posadas. No posee atención presencial en el CAV Itaembé Guazú.',
            'horarios': 'Lunes a Viernes de 06:30 a 14:00 hs (Cajas: de 06:30 a 14:00 hs y de 16:30 a 19:00 hs)'
        },
        'fuente_verificacion': 'SAMSA - Portal Oficial de Servicios de Aguas de Misiones S.A.',
        'fecha_verificacion': '2026-11-08',
        'palabras_clave': [
            'samsa', 'agua potable', 'perdida de agua', 'cloaca', 'caño roto', 'falta de agua',
            'pagar agua', 'pagar el agua', 'pago de agua', 'pago del agua', 'factura de agua',
            'boleta de agua', 'factura del agua', 'boleta del agua', 'deuda de agua', 'saldo de agua',
            'servicio de agua', 'pagar samsa', 'factura de samsa', 'boleta de samsa',
            'donde pago el agua', 'como pagar el agua', 'donde pagar el agua', 'cuenta de agua', 'medidor de agua'
        ]
    }
]


def obtener_directorio_organismos():
    """Retorna la lista completa de organismos y dependencias verificadas."""
    return ORGANISMOS


def obtener_organismos_cav_itaembe():
    """Retorna los 6 organismos y entidades con sede de atención confirmada en el CAV Itaembé Guazú."""
    return [org for org in ORGANISMOS if org.get('presente_cav_itaembe')]


def obtener_organismo_por_id(org_id: str):
    """Busca un organismo específico por su id."""
    for org in ORGANISMOS:
        if org['id'] == org_id:
            return org
    return None


def buscar_organismo_existente(texto: str):
    """
    Determina si la propuesta de organismo ingresada por el vecino ya se encuentra
    incorporada en el catálogo y directorio oficial de SIVEG / CAV.
    Retorna el diccionario del organismo existente o None si es una propuesta nueva (ej: ANSES, PAMI, IPS).
    """
    if not texto or not texto.strip():
        return None

    t = texto.lower()
    for o, d in [('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u'), ('ü', 'u'), ('ñ', 'n')]:
        t = t.replace(o, d)

    # 1. Búsqueda por siglas oficiales distintivas
    siglas_distintivas = {
        'iprodha': 'iprodha',
        'atm': 'atm_misiones',
        'hcd': 'hcd_posadas',
        'emsa': 'emsa',
        'samsa': 'samsa',
        'gop': 'mun_obras_privadas',
    }
    for sigla, org_id in siglas_distintivas.items():
        if re.search(r'\b' + re.escape(sigla) + r'\b', t):
            return obtener_organismo_por_id(org_id)

    # 2. Mapeo por patrones institucionales específicos
    patrones_institucionales = [
        (r'\b(iprodha|vivienda social|viviendas sociales|adjudicacion de vivienda|sorteos? de casas?)\b', 'iprodha'),
        (r'\b(registro civil|registro de las personas|partidas? de nacimiento|actas? digitales?)\b', 'registro_civil'),
        (r'\b(atm|agencia tributaria|rentas misiones|rentas provincia|patente automotor|impuesto automotor|impuesto provincial automotor|ipa)\b', 'atm_misiones'),
        (r'\b(hcd|concejo deliberante|ordenanzas? municipales?)\b', 'hcd_posadas'),
        (r'\b(defensori?a del pueblo|defensori?a posadas|mediacion comunitaria|mediacion vecinal)\b', 'defensoria_pueblo'),
        (r'\b(obras? privadas?|sistema gop|planos? de obra|permiso de obra|permiso de edificacion)\b', 'mun_obras_privadas'),
        (r'\b(obras? publicas?|bacheo|vialidad municipal|asfalto|calles rotas)\b', 'mun_obras_publicas'),
        (r'\b(servicios? urbanos?|alumbrado publico|foco quemado|recoleccion de residuos?|limpieza urbana)\b', 'mun_servicios_urbanos'),
        (r'\b(espacios? verdes?|arbolado urbano|poda de arboles|poda municipal)\b', 'mun_espacios_verdes'),
        (r'\b(habilitacion(?:es)? comerciales?|bromatologia municipal)\b', 'mun_habilitaciones'),
        (r'\b(oficina de empleo|empleo municipal)\b', 'mun_empleo'),
        (r'\b(descacharrado|operativo descacharrado|dengue)\b', 'mun_salud_descacharrado'),
        (r'\b(tribunal de faltas|juzgado de faltas|fotomultas?)\b', 'tribunal_faltas'),
        (r'\b(emsa|energia de misiones|empresa de luz)\b', 'emsa'),
        (r'\b(samsa|aguas de misiones|empresa de agua)\b', 'samsa'),
    ]
    for patron, org_id in patrones_institucionales:
        if re.search(patron, t):
            return obtener_organismo_por_id(org_id)

    return None



def identificar_organismo_competente(texto_consulta: str):
    """
    Identifica el organismo competente a partir de la consulta del vecino.
    Prioriza coincidencias específicas sobre las genéricas.
    """
    t = texto_consulta.lower()
    for o, d in [('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u'), ('ü', 'u'), ('ñ', 'n')]:
        t = t.replace(o, d)

    # IPRODHA: consultas sobre IProDHa, viviendas sociales, inscripción a sorteos de casas ("ganar una casa"), cuotas, etc.
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
        'como tener una casa', 'conseguir una casa', 'conseguir casa', 'pedir una casa', 'sacar una casa'
    ]):
        return obtener_organismo_por_id('iprodha')

    # Honorable Concejo Deliberante
    if any(k in t for k in ['concejo deliberante', 'hcd', 'honorable concejo deliberante', 'ordenanza', 'proyecto vecinal']):
        return obtener_organismo_por_id('hcd_posadas')

    # ATM (Agencia Tributaria Misiones)
    if any(k in t for k in ['atm', 'agencia tributaria misiones', 'rentas misiones']):
        return obtener_organismo_por_id('atm_misiones')

    # Registro de las Personas
    if any(k in t for k in ['registro provincial de las personas', 'registro civil']):
        return obtener_organismo_por_id('registro_civil')

    # Obras Privadas / Planificación Territorial (Sistema GOP, regularización de obras, etc.)
    if any(k in t for k in [
        'obras privadas', 'obra privada', 'planificacion territorial', 'sistema gop', 'gop',
        'indicadores urbanos', 'numero de finca', 'numeros de finca', 'regularizacion de obra',
        'regularizacion de construccion', 'ampliar casa', 'ampliar mi casa', 'ampliacion',
        'construir', 'construir mi casa', 'permiso de obra', 'permiso de edificacion',
        'planos de obra', 'final de obra', 'baldio a edificado', 'mensura', 'vallados de obras'
    ]):
        return obtener_organismo_por_id('mun_obras_privadas')

    # Habilitaciones Comerciales e Industriales / Eventuales
    if any(k in t for k in [
        'habilitacion comercial', 'habilitaciones comerciales', 'habilitacion eventual',
        'habilitacion digital', 'habilitar negocio', 'habilitar local', 'abrir local',
        'abrir negocio', 'habilitacion', 'habilitaciones', 'comercio', 'local comercial', 'bromatologia',
        'abrir un negocio', 'abrir un local', 'abrir un comercio', 'poner un negocio', 'poner un local',
        'poner un kiosco', 'quise abrir un negocio', 'quiero abrir un negocio', 'iniciar un negocio',
        'abrir comercio', 'habilitar un negocio', 'negocio', 'kiosco', 'almacen', 'verduleria'
    ]):
        return obtener_organismo_por_id('mun_habilitaciones')

    # Oficina Municipal de Empleo
    if any(k in t for k in ['oficina de empleo', 'buscar trabajo', 'empleo', 'conseguir trabajo', 'cargar cv', 'curriculum', 'trabajo']):
        return obtener_organismo_por_id('mun_empleo')

    # Operativo Descacharrado / Salud
    if any(k in t for k in ['descacharrado', 'operativo descacharrado', 'dengue', 'cacharros']):
        return obtener_organismo_por_id('mun_salud_descacharrado')

    # Defensoría del Pueblo (Mediación vecinal y comunitaria voluntaria)
    if any(k in t for k in ['defensor', 'defensoria', 'mediacion']):
        return obtener_organismo_por_id('defensoria_pueblo')

    # Ruidos Molestos / Control Comunal Municipal (Ordenanza VI – Nº 14)
    # Atención: Se deriva prioritariamente al Municipio (Control Comunal / Guardia de Ruidos Molestos)
    if any(k in t for k in [
        'ruidos molestos', 'ruido molesto', 'musica fuerte', 'musica alta', 'musica a todo volumen',
        'musica al taco', 'musica a alto volumen', 'vecina ruidosa', 'vecino ruidoso', 'denuncia por ruidos',
        'denunciar ruidos', 'denunciar por ruidos', 'ordenanza vi 14', 'escucha musica fuerte',
        'escuchan musica fuerte', 'ruidos de cualquier indole'
    ]) or (
        bool(re.search(r'\b(ruido\w*|musica)\b', t)) and bool(re.search(r'\b(molest\w*|fuerte|alta|vecin\w*|escucha)\b', t))
    ):
        return obtener_organismo_por_id('mun_ruidos_molestos')

    # Otros conflictos vecinales generales hacia Defensoría
    if any(k in t for k in ['conflicto vecinal', 'problemas con vecinos', 'problema con vecinos']):
        return obtener_organismo_por_id('defensoria_pueblo')

    # SAMSA (Servicios de Aguas de Misiones S.A. - Empresa Privada Concesionaria)
    if any(k in t for k in [
        'samsa', 'perdida de agua', 'cano roto', 'cloaca', 'falta de agua', 'red de agua',
        'pagar el agua', 'pagar agua', 'pago de agua', 'pago del agua', 'factura de agua',
        'boleta de agua', 'factura del agua', 'boleta del agua', 'deuda de agua', 'saldo de agua',
        'servicio de agua', 'pagar samsa', 'factura de samsa', 'boleta de samsa',
        'donde pago el agua', 'como pagar el agua', 'donde pagar el agua', 'cuenta de agua', 'medidor de agua'
    ]) or (
        bool(re.search(r'\b(pagar|pago|abonar|deuda|saldo|boleta|factura)\b.*?\b(agua|samsa|cloaca)\b', t)) or
        bool(re.search(r'\b(agua|samsa|cloaca)\b.*?\b(pagar|pago|abonar|deuda|saldo|boleta|factura)\b', t))
    ):
        return obtener_organismo_por_id('samsa')

    # EMSA (Energía de Misiones)
    if any(k in t for k in [
        'emsa', 'factura de luz', 'corte de luz', 'energia de misiones', 'boleta de luz', 'tarifa social luz',
        'pagar la luz', 'pagar luz', 'pago de luz', 'pago de la luz', 'factura de la luz', 'boleta de la luz',
        'deuda de luz', 'pagar mi luz', 'servicio de luz', 'factura de energia', 'boleta de energia',
        'pagar energia', 'pagar la energia', 'saldo de luz', 'luz de mi casa', 'factura de emsa', 'boleta de emsa',
        'pagar emsa', 'donde pago la luz', 'como pagar la luz', 'donde pagar la luz'
    ]) or (
        bool(re.search(r'\b(pagar|pago|abonar|deuda|saldo|boleta|factura)\b.*?\b(luz|electricidad|energia)\b', t)) or
        bool(re.search(r'\b(luz|electricidad|energia)\b.*?\b(pagar|pago|abonar|deuda|saldo|boleta|factura)\b', t))
    ):
        return obtener_organismo_por_id('emsa')

    # Tribunal de Faltas
    if any(k in t for k in ['multa', 'infraccion', 'tribunal de faltas', 'juzgado de faltas', 'libre deuda', 'fotomulta']):
        return obtener_organismo_por_id('tribunal_faltas')

    # Luminarias / Residuos
    if any(k in t for k in ['luz quemada', 'luminaria', 'foco', 'farola', 'alumbrado', 'basura', 'contenedor', 'microbasural']):
        return obtener_organismo_por_id('mun_servicios_urbanos')

    # Arbolado / Espacios verdes
    if any(k in t for k in ['arbol', 'poda', 'ramas', 'plaza', 'desmalezado', 'maleza']):
        return obtener_organismo_por_id('mun_espacios_verdes')

    # Obras públicas / bacheo
    if any(k in t for k in ['bache', 'pozo', 'calle rota', 'asfalto', 'cordon cuneta', 'calle de tierra', 'sumidero']):
        return obtener_organismo_por_id('mun_obras_publicas')

    return None
