from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .forms import ReclamoVecinoForm
from .models import Expediente, CategoriaReclamo, RegistroConsulta, SugerenciaOrganismo
from .organismos import obtener_directorio_organismos, identificar_organismo_competente, obtener_organismos_cav_itaembe
from .conversacion import extraer_contexto_ubicacion, generar_preguntas_seguimiento, generar_resumen_automatico
from .asistente import clasificar_consulta, TIPO_CONSULTA, TIPO_RECLAMO, TIPO_EMERGENCIA
from .catalogo_tramites import CATALOGO_TRAMITES, obtener_catalogo_tramites, buscar_tramite_por_consulta


class ValidacionDatosVecinoTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('portal_vecino')

    def test_nombre_con_numeros_falla_en_vista(self):
        response = self.client.post(self.url, {
            'nombre': 'Juan Perez 123',
            'dni': '38123456',
            'telefono': '3764123456',
            'detalle': 'Consulta de prueba'
        })
        self.assertContains(response, 'El nombre y apellido solo debe contener letras.')

    def test_dni_con_letras_falla_en_vista(self):
        response = self.client.post(self.url, {
            'nombre': 'Juan Perez',
            'dni': '38123456A',
            'telefono': '3764123456',
            'detalle': 'Consulta de prueba'
        })
        self.assertContains(response, 'El DNI solo debe contener números.')

    def test_telefono_con_letras_falla_en_vista(self):
        response = self.client.post(self.url, {
            'nombre': 'Juan Perez',
            'dni': '38123456',
            'telefono': '3764-ABCD',
            'detalle': 'Consulta de prueba'
        })
        self.assertContains(response, 'El teléfono de contacto solo debe contener números.')

    def test_form_validacion(self):
        form_invalido_nombre = ReclamoVecinoForm(data={
            'nombre_completo': 'Carlos 99',
            'dni_vecino': 38123456,
            'telefono_contacto': '3764123456',
            'detalle_consulta': 'Prueba'
        })
        self.assertFalse(form_invalido_nombre.is_valid())
        self.assertIn('nombre_completo', form_invalido_nombre.errors)

        form_invalido_telefono = ReclamoVecinoForm(data={
            'nombre_completo': 'Carlos Gomez',
            'dni_vecino': 38123456,
            'telefono_contacto': 'telefono123',
            'detalle_consulta': 'Prueba'
        })
        self.assertFalse(form_invalido_telefono.is_valid())
        self.assertIn('telefono_contacto', form_invalido_telefono.errors)


class CatalogoTramitesConfigurableTest(TestCase):
    def test_campos_obligatorios_catalogo(self):
        """Verifica que cada trámite contenga nombre, categoria, organismo, descripcion, requisitos, enlace y fecha_verificacion."""
        catalogo = obtener_catalogo_tramites()
        self.assertGreaterEqual(len(catalogo), 5)
        for t in catalogo:
            self.assertIn('nombre', t)
            self.assertIn('categoria', t)
            self.assertIn('organismo_responsable', t)
            self.assertIn('descripcion', t)
            self.assertIn('requisitos', t)
            self.assertIn('enlace_oficial', t)
            self.assertIn('fecha_verificacion', t)
            self.assertTrue(t['enlace_oficial'].startswith('https://'))
            self.assertIsInstance(t['requisitos'], list)
            self.assertGreater(len(t['requisitos']), 0)

    def test_tramites_clave_presentes(self):
        """Verifica la existencia de trámites clave del catálogo configurable."""
        catalogo_ids = [t['id'] for t in obtener_catalogo_tramites()]
        self.assertIn('patente_automotor', catalogo_ids)
        self.assertIn('licencia_conducir', catalogo_ids)
        self.assertIn('multas_transito', catalogo_ids)
        self.assertIn('emsa_factura', catalogo_ids)
        self.assertIn('iprodha_tramites', catalogo_ids)
        self.assertIn('obras_privadas', catalogo_ids)
        self.assertIn('habilitaciones_comerciales', catalogo_ids)
        self.assertIn('sem_estacionamiento', catalogo_ids)
        self.assertIn('tasas_municipales_autogestion', catalogo_ids)
        self.assertIn('actas_transito_informe', catalogo_ids)
        self.assertIn('operativo_descacharrado', catalogo_ids)
        self.assertIn('oficina_empleo', catalogo_ids)
        self.assertIn('guia_tramites_muni', catalogo_ids)
        self.assertIn('tramites_comunitarios', catalogo_ids)
        self.assertIn('hcd_posadas_tramite', catalogo_ids)
        self.assertIn('cav_itaembe_guazu', catalogo_ids)


class ConsultasInformativasTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('portal_vecino')

    def test_consulta_patente_boton_online_y_fuente(self):
        response = self.client.post(self.url, {
            'nombre': 'María Laura González',
            'dni': '38123456',
            'telefono': '3764123456',
            'detalle': 'Necesito consultar sobre el pago de patente del auto'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Consulta Informativa')
        self.assertContains(response, 'DGR - Sin Clave Fiscal')
        self.assertContains(response, 'https://sinclavefiscal.atm.misiones.gob.ar/sc/automotor/emision_ba_ipa')
        self.assertContains(response, 'DGR - Sin Clave Fiscal')
        self.assertContains(response, 'Fuente oficial:')
        self.assertContains(response, 'Verificado:')
        # No debe generar automáticamente un ticket en SIGEV
        self.assertFalse(Expediente.objects.filter(dni_vecino=38123456).exists())

    def test_consulta_licencia_conducir_boton_online(self):
        response = self.client.post(self.url, {
            'nombre': 'Ana Ruiz',
            'dni': '35123456',
            'telefono': '3764001122',
            'detalle': '¿Cómo saco turno para renovar la licencia de conducir?'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Iniciar trámite online')
        self.assertContains(response, 'https://posadas.gov.ar/turnos/')
        self.assertContains(response, 'Requisitos')
        self.assertFalse(Expediente.objects.filter(dni_vecino=35123456).exists())

    def test_consulta_emsa_factura_comercial(self):
        response = self.client.post(self.url, {
            'nombre': 'Jorge Blanco',
            'dni': '30123456',
            'telefono': '3764998877',
            'detalle': 'Quiero pagar la factura de luz de EMSA por internet'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Iniciar trámite online')
        self.assertContains(response, 'https://www.energiademisiones.com.ar/')
        self.assertFalse(Expediente.objects.filter(dni_vecino=30123456).exists())

    def test_consulta_ampliar_casa_dirige_a_obras_privadas_municipalidad(self):
        """Consulta 'quiero ampliar mi casa' debe dirigir a la Municipalidad de Posadas (Planificación y Obras Privadas / GOP), NO a IPRODHA."""
        response = self.client.post(self.url, {
            'nombre': 'Martín Acosta',
            'dni': '34123987',
            'telefono': '3764551122',
            'detalle': 'Hola, quiero saber qué trámites necesito porque quiero ampliar mi casa'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestión de Obras Privadas')
        self.assertContains(response, 'Municipalidad de Posadas')
        self.assertContains(response, 'posadas.gov.ar')
        self.assertNotIn('IPRODHA', response.context['respuesta_ia'])
        self.assertIn('Secretaría de Planificación Estratégica y Territorial', response.context['organismo_destino'])
        self.assertFalse(Expediente.objects.filter(dni_vecino=34123987).exists())

    def test_consulta_habilitacion_comercial_dirige_a_municipalidad(self):
        """Consulta sobre habilitación comercial para abrir local debe dirigir a la Municipalidad de Posadas."""
        response = self.client.post(self.url, {
            'nombre': 'Luciana Benítez',
            'dni': '33888777',
            'telefono': '3764662233',
            'detalle': 'Quiero abrir un local comercial y saber los requisitos de habilitación comercial'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Habilitaciones Comerciales')
        self.assertContains(response, 'Municipalidad de Posadas')
        self.assertContains(response, 'https://datos.posadas.gov.ar/habilitaciones-municipales/')
        self.assertFalse(Expediente.objects.filter(dni_vecino=33888777).exists())

    def test_consulta_sem_estacionamiento_medido(self):
        """Consulta sobre el SEM Posadas debe guiar hacia el pago y carga de saldo online."""
        response = self.client.post(self.url, {
            'nombre': 'Lucas Viera',
            'dni': '37111444',
            'telefono': '3764778899',
            'detalle': 'Cómo cargo saldo en el sistema de estacionamiento medido SEM'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SEM Posadas')
        self.assertContains(response, 'https://sistema.posadas.gov.ar/mp_sistemas/autogestion')

    def test_consulta_operativo_descacharrado_dengue(self):
        """Consulta sobre operativo descacharrado y prevención del dengue."""
        response = self.client.post(self.url, {
            'nombre': 'Valeria Ramos',
            'dni': '32555666',
            'telefono': '3764332211',
            'detalle': 'Quisiera información sobre el cronograma del operativo descacharrado para prevención de dengue'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Operativo Descacharrado')
        self.assertContains(response, 'https://posadas.gov.ar/')

    def test_consulta_oficina_empleo_buscar_trabajo(self):
        """Consulta sobre buscar trabajo y cargar CV en la oficina de empleo."""
        response = self.client.post(self.url, {
            'nombre': 'Federico Maidana',
            'dni': '39444333',
            'telefono': '3764991122',
            'detalle': 'Quiero buscar trabajo y registrar mi curriculum en la oficina de empleo de la municipalidad'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Oficina Municipal de Empleo')
        self.assertContains(response, 'https://posadas.gov.ar/')

    def test_consulta_tasas_municipales_autogestion(self):
        """Consulta sobre autogestión y pago de tasas municipales / domicilio fiscal."""
        response = self.client.post(self.url, {
            'nombre': 'Patricia Duarte',
            'dni': '28999111',
            'telefono': '3764223344',
            'detalle': 'Necesito pagar las tasas municipales TGI por autogestion y constituir mi domicilio fiscal'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Autogestión')
        self.assertContains(response, 'https://sistema.posadas.gov.ar/mp_sistemas/autogestion')

    def test_consulta_actas_transito_solicitud_informe(self):
        """Consulta sobre actas de transito y solicitud de informes."""
        response = self.client.post(self.url, {
            'nombre': 'Diego Silvero',
            'dni': '31222333',
            'telefono': '3764887766',
            'detalle': 'Quiero hacer la solicitud de informe de actas de transito y pago online'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Actas de Tránsito')
        self.assertContains(response, 'posadas.gov.ar')

    def test_consulta_cav_itaembe_guazu_organismos_presentes(self):
        """Verifica que al consultar por el CAV Itaembé Guazú se informen los 6 organismos presentes."""
        response = self.client.post(self.url, {
            'nombre': 'Raúl Cárdenas',
            'dni': '33112233',
            'telefono': '3764556677',
            'detalle': '¿Qué organismos y dependencias hay en el CAV de Itaembé Guazú?'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Itaembé Guazú')
        self.assertContains(response, 'Planificación')
        self.assertContains(response, 'IProDHa')
        self.assertContains(response, 'Registro Provincial de las Personas')
        self.assertContains(response, 'Agencia Tributaria Misiones')
        self.assertContains(response, 'Concejo Deliberante')
        self.assertContains(response, 'Defensoría del Pueblo')

    def test_consulta_sistema_gop_regularizacion_y_planurbano(self):
        """Consulta sobre Sistema GOP y regularización de obras deriva al portal de Planificación Territorial."""
        response = self.client.post(self.url, {
            'nombre': 'Elena Gómez',
            'dni': '36999888',
            'telefono': '3764331122',
            'detalle': 'Cómo regularizar construcciones existentes sin permiso en el sistema GOP y números de finca'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sistema GOP')
        self.assertContains(response, 'https://posadas.gov.ar/planurbano/guia-de-tramites/')

    def test_consulta_habilitacion_eventual_online_espectaculos(self):
        """Consulta sobre habilitación eventual online para eventos masivos."""
        response = self.client.post(self.url, {
            'nombre': 'Ignacio Valdéz',
            'dni': '35444333',
            'telefono': '3764667788',
            'detalle': 'Requisitos de habilitación eventual online para espectáculos y eventos masivos'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Habilitación Eventual')
        self.assertContains(response, 'https://datos.posadas.gov.ar/habilitaciones-municipales/')

    def test_consulta_tramites_comunitarios_escuela_danza_presupuesto(self):
        """Consulta sobre inscripción a Escuela Municipal de Danza y presupuesto participativo."""
        response = self.client.post(self.url, {
            'nombre': 'Florencia Sosa',
            'dni': '38111222',
            'telefono': '3764998833',
            'detalle': 'Quiero información sobre la inscripción a la escuela municipal de danza y proyectos de presupuesto participativo'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Trámites Generales y Comunitarios')
        self.assertContains(response, 'https://posadas.gov.ar/guiatramite')

    def test_consulta_hcd_posadas_ordenanzas_y_proyectos(self):
        """Consulta sobre atención ciudadana y proyectos vecinales en el Honorable Concejo Deliberante."""
        response = self.client.post(self.url, {
            'nombre': 'Guillermo Toledo',
            'dni': '29333444',
            'telefono': '3764123499',
            'detalle': 'Cómo presentar una iniciativa o proyecto vecinal ante el honorable concejo deliberante HCD'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Honorable Concejo Deliberante')
        self.assertContains(response, 'https://hcdposadas.gob.ar/')


class EmergenciasElectricasTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('portal_vecino')

    def test_emergencia_electrica_poste_caido_y_chispas(self):
        response = self.client.post(self.url, {
            'nombre': 'Lucía Fernández',
            'dni': '40123456',
            'telefono': '3764112233',
            'detalle': 'El poste eléctrico se cayó en la esquina y está largando chispas'
        })
        self.assertEqual(response.status_code, 200)
        # 1. Advertencia de emergencia destacada
        self.assertContains(response, 'Emergencia Eléctrica')
        self.assertContains(response, 'PELIGRO INMEDIATO DETECTADO')

        # 2. Instrucciones de seguridad específicas
        self.assertContains(response, 'Alejate')
        self.assertContains(response, 'no toques cables')
        self.assertContains(response, 'alejadas a otras personas')

        # 3. Llamar al 911
        self.assertContains(response, '911')

        # 4. Botón Llamar a Energía de Misiones (0800 888 3672)
        self.assertContains(response, 'Llamar a Energía de Misiones')
        self.assertContains(response, '0800 888 3672')
        self.assertContains(response, 'tel:08008883672')

        # 5. Botón Abrir WhatsApp de Energía de Misiones
        self.assertContains(response, 'Abrir WhatsApp de Energía de Misiones')
        self.assertContains(response, 'https://wa.me/5493764242514')

        # 6. Ofrecer sitio oficial EMSA
        self.assertContains(response, 'https://www.energiademisiones.com.ar/')

        # 7. No afirmar que se envió reclamo a EMSA y no transferir datos
        self.assertNotContains(response, 'Reclamo enviado a EMSA')
        self.assertContains(response, 'Aviso de Canales Externos')

        # 8. No generar ticket administrativo interno
        self.assertFalse(Expediente.objects.filter(dni_vecino=40123456).exists())

    def test_emergencia_cable_tirado_en_calle(self):
        response = self.client.post(self.url, {
            'nombre': 'Mariano Silva',
            'dni': '42123456',
            'telefono': '3764223344',
            'detalle': 'Hay un cable de electricidad tirado en la calle cerca de los autos'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Emergencia Eléctrica')
        self.assertContains(response, '0800 888 3672')
        self.assertContains(response, 'https://wa.me/5493764242514')
        self.assertFalse(Expediente.objects.filter(dni_vecino=42123456).exists())

    def test_emergencia_riesgo_electrocucion(self):
        response = self.client.post(self.url, {
            'nombre': 'Estela Vega',
            'dni': '28123456',
            'telefono': '3764445566',
            'detalle': 'La reja metálica tiene corriente eléctrica, peligro y riesgo de electrocución'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Emergencia Eléctrica')
        self.assertContains(response, '0800 888 3672')
        self.assertFalse(Expediente.objects.filter(dni_vecino=28123456).exists())


class TicketsSIGEVTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('portal_vecino')
        CategoriaReclamo.objects.get_or_create(
            cod_categoria=101,
            defaults={'nombre_categoria': 'Luminarias y Alumbrado Público', 'organismo_default': 'Servicios Urbanos'}
        )
        CategoriaReclamo.objects.get_or_create(
            cod_categoria=100,
            defaults={'nombre_categoria': 'Servicios Urbanos y Viales', 'organismo_default': 'Obras Públicas'}
        )

    def test_escenario_1_consulta_informativa_no_genera_ticket(self):
        """Escenario 1: Consulta informativa brinda asesoramiento y NO genera ticket en la BD."""
        response = self.client.post(self.url, {
            'nombre': 'Valeria Ramos',
            'dni': '36123456',
            'telefono': '3764556677',
            'detalle': '¿Cuáles son los requisitos y costos para renovar la licencia de conducir?'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Consulta Informativa')
        self.assertContains(response, 'no requiere la generación de un ticket')
        self.assertFalse(Expediente.objects.filter(dni_vecino=36123456).exists())

    def test_escenario_2_reclamo_municipal_confirmado_genera_unico_ticket(self):
        """Escenario 2: Reclamo municipal confirmado con 'Registrar solicitud' genera un único ticket con estado PENDIENTE."""
        response = self.client.post(self.url, {
            'nombre': 'Pedro Gómez',
            'dni': '31123456',
            'telefono': '3764889900',
            'detalle': 'Hay un pozo y bache gigante en la calle de mi casa',
            'barrio': 'Villa Sarita',
            'entre_calles': 'San Martín 1200',
            'accion': 'registrar'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ticket Interno N°:')
        self.assertContains(response, 'ESTADO INICIAL: PENDIENTE')
        self.assertContains(response, 'pendiente de validación por Mesa de Entrada')
        self.assertContains(response, 'Área Municipal Sugerida:')
        self.assertContains(response, 'Aviso Institucional:')

        # Verifica en la base de datos
        tickets = Expediente.objects.filter(dni_vecino=31123456)
        self.assertEqual(tickets.count(), 1)
        ticket = tickets.first()
        self.assertTrue(ticket.nro_expediente.startswith('TCK-'))
        self.assertEqual(ticket.estado_actual, 'PENDIENTE')
        self.assertEqual(ticket.tipo_solicitud, 'RECLAMO')
        self.assertEqual(ticket.nombre_completo, 'Pedro Gómez')
        self.assertEqual(ticket.barrio, 'Villa Sarita')
        self.assertEqual(ticket.entre_calles, 'San Martín 1200')
        self.assertIn('bache', ticket.detalle_consulta)

    def test_escenario_3_reclamo_no_confirmado_no_genera_ticket(self):
        """Escenario 3: Reclamo municipal no confirmado muestra dos opciones y NO genera ticket."""
        response = self.client.post(self.url, {
            'nombre': 'Pedro Gómez',
            'dni': '31123456',
            'telefono': '3764889900',
            'detalle': 'Hay un pozo y bache gigante en la calle de mi casa'
        })
        self.assertEqual(response.status_code, 200)
        # Debe mostrar sugerencia de área competente
        self.assertContains(response, 'Área municipal sugerida:')
        self.assertContains(response, 'Obras Públicas')
        # Debe mostrar las dos opciones explícitas
        self.assertContains(response, 'Registrar solicitud')
        self.assertContains(response, 'Solo necesitaba información')
        # No debe haber generado ticket todavía
        self.assertFalse(Expediente.objects.filter(dni_vecino=31123456).exists())

    def test_escenario_4_reclamo_solo_necesitaba_informacion_no_genera_ticket(self):
        """El vecino selecciona 'Solo necesitaba información': no se genera ticket."""
        response = self.client.post(self.url, {
            'nombre': 'Pedro Gómez',
            'dni': '31123456',
            'telefono': '3764889900',
            'detalle': 'Hay un pozo y bache gigante en la calle de mi casa',
            'accion': 'solo_info'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sin Ticket Generado')
        self.assertContains(response, 'solo necesitabas información')
        self.assertFalse(Expediente.objects.filter(dni_vecino=31123456).exists())

    def test_escenario_5_prevencion_duplicados_multiples_clics(self):
        """Múltiples clics rápidos consecutivos generan un único ticket sin duplicar registros."""
        datos = {
            'nombre': 'Estela Benítez',
            'dni': '29123456',
            'telefono': '3764123123',
            'detalle': 'La luminaria de la esquina no prende hace dos semanas',
            'barrio': 'Itaembé Guazú',
            'entre_calles': 'Los Lirios y Las Rosas',
            'accion': 'registrar'
        }
        # Primer clic
        r1 = self.client.post(self.url, datos)
        # Segundo clic (duplicado inmediato)
        r2 = self.client.post(self.url, datos)
        # Tercer clic (duplicado inmediato)
        r3 = self.client.post(self.url, datos)

        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r3.status_code, 200)

        # Debe existir exactamente UN ticket en la base de datos
        tickets = Expediente.objects.filter(dni_vecino=29123456)
        self.assertEqual(tickets.count(), 1)
        ticket = tickets.first()
        self.assertEqual(ticket.estado_actual, 'PENDIENTE')
        self.assertEqual(ticket.barrio, 'Itaembé Guazú')
        self.assertEqual(ticket.entre_calles, 'Los Lirios y Las Rosas')

    def test_escenario_6_registro_ticket_con_archivo_adjunto(self):
        """Permite adjuntar fotos o comprobantes al reclamo registrado."""
        archivo_prueba = SimpleUploadedFile(
            'foto_bache.jpg',
            b'imagen_de_prueba_bytes',
            content_type='image/jpeg'
        )
        response = self.client.post(self.url, {
            'nombre': 'Carlos Cabrera',
            'dni': '32123456',
            'telefono': '3764778899',
            'detalle': 'Bache profundo frente al colegio',
            'barrio': 'Villa Cabello',
            'entre_calles': 'Tambor de Tacuarí y Eva Perón',
            'accion': 'registrar',
            'archivo_adjunto': archivo_prueba
        })
        self.assertEqual(response.status_code, 200)
        ticket = Expediente.objects.filter(dni_vecino=32123456).first()
        self.assertIsNotNone(ticket)
        self.assertTrue(ticket.archivo_adjunto)
        self.assertIn('foto_bache', ticket.archivo_adjunto.name)
        self.assertEqual(ticket.estado_actual, 'PENDIENTE')
        self.assertEqual(ticket.barrio, 'Villa Cabello')
        self.assertEqual(ticket.entre_calles, 'Tambor de Tacuarí y Eva Perón')


class EmergenciasGeneralesYContextoTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('portal_vecino')

    def test_emergencia_incendio_humo(self):
        response = self.client.post(self.url, {
            'nombre': 'Roberto Benítez',
            'dni': '33123456',
            'telefono': '3764334455',
            'detalle': 'Hay un principio de incendio y mucho humo espeso en un terreno baldío'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alerta de Emergencia')
        self.assertContains(response, '100')  # Bomberos
        self.assertFalse(Expediente.objects.filter(dni_vecino=33123456).exists())

    def test_contexto_no_confunde_palabras_aisladas(self):
        tipo_bomberos = clasificar_consulta('Requisitos para la habilitación de bomberos de un local comercial')
        self.assertEqual(tipo_bomberos, TIPO_CONSULTA)

        tipo_alumbrado = clasificar_consulta('El poste de luz de la vereda tiene el foco quemado y no prende')
        self.assertEqual(tipo_alumbrado, TIPO_RECLAMO)

        tipo_factura = clasificar_consulta('¿Dónde pago la factura de luz de EMSA?')
        self.assertEqual(tipo_factura, TIPO_CONSULTA)



class RegistroConsultasTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('portal_vecino')

    def test_registro_independiente_para_consulta_informativa(self):
        """Requisito 1: Cada consulta registra un RegistroConsulta sin generar ticket."""
        response = self.client.post(self.url, {
            'nombre': 'Marina Valdez',
            'dni': '37123456',
            'telefono': '3764887766',
            'detalle': 'Requisitos y aranceles para renovar el carnet de conducir en Posadas'
        })
        self.assertEqual(response.status_code, 200)
        # No genera ticket
        self.assertFalse(Expediente.objects.filter(dni_vecino=37123456).exists())
        # Sí genera RegistroConsulta
        reg = RegistroConsulta.objects.filter(texto_consultado__icontains='carnet de conducir').first()
        self.assertIsNotNone(reg)
        self.assertTrue(reg.identificador_consulta.startswith('CNS-'))
        self.assertEqual(reg.resultado, 'TRAMITE_DIGITAL')
        self.assertIsNone(reg.ticket_asociado)
        self.assertEqual(reg.evaluacion_vecino, 'PENDIENTE')

    def test_registro_consulta_vinculada_a_ticket_confirmado(self):
        """Requisito 1: Si la solicitud se confirma, el RegistroConsulta se vincula al ticket."""
        response = self.client.post(self.url, {
            'nombre': 'Martín Ruiz',
            'dni': '34123456',
            'telefono': '3764332211',
            'detalle': 'Hay un pozo y bache profundo en barrio Villa Sarita sobre calle Roque Pérez',
            'accion': 'registrar'
        })
        self.assertEqual(response.status_code, 200)
        ticket = Expediente.objects.filter(dni_vecino=34123456).first()
        self.assertIsNotNone(ticket)
        reg = RegistroConsulta.objects.filter(ticket_asociado=ticket).first()
        self.assertIsNotNone(reg)
        self.assertEqual(reg.resultado, 'TICKET_REGISTRADO')
        self.assertEqual(reg.ticket_asociado, ticket)


class ConversacionInteligenteYContextoTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('portal_vecino')

    def test_extraccion_contexto_barrio_y_calles(self):
        """Requisito 2 y 3: Extrae barrio y calles del texto sin repetir preguntas ya contestadas."""
        texto = 'Hay una luminaria rota en barrio Villa Sarita entre calle San Martín y Bolívar frente a la plaza'
        ctx = extraer_contexto_ubicacion(texto)
        self.assertEqual(ctx['barrio'], 'Villa Sarita')
        self.assertIn('San Martín', ctx['entre_calles'])
        self.assertIn('Bolívar', ctx['entre_calles'])
        self.assertIn('Frente a la plaza', ctx['referencias'])

        # Preguntas de seguimiento: dado que ya tiene todo, no repite
        preg = generar_preguntas_seguimiento('reclamo', ctx)
        self.assertTrue(preg['informacion_completa'])
        self.assertEqual(len(preg['preguntas_texto']), 0)

    def test_preguntas_adaptativas_cuando_falta_ubicacion(self):
        """Requisito 2: Si falta barrio o calles, formula preguntas adaptativas y nota de fotos segura."""
        texto = 'Se cayó un poste de madera en la vereda'
        ctx = extraer_contexto_ubicacion(texto)
        self.assertEqual(ctx['barrio'], '')
        self.assertEqual(ctx['entre_calles'], '')

        preg = generar_preguntas_seguimiento('reclamo', ctx, es_poste_o_cable=True)
        self.assertFalse(preg['informacion_completa'])
        self.assertIn('barrio', preg['faltantes'])
        self.assertIn('entre_calles', preg['faltantes'])
        # Advertencia de seguridad en fotos para postes
        self.assertIn('NO acercarte', preg['nota_fotos'])

    def test_emergencia_no_posterga_por_preguntas(self):
        """Requisito 2: Ante una emergencia, NUNCA posterga la orientación para completar preguntas."""
        response = self.client.post(self.url, {
            'nombre': 'Valeria Sosa',
            'dni': '39123456',
            'telefono': '3764998811',
            'detalle': 'El poste cayó sobre la calle y hay cables con chispas y peligro de electrocución'
        })
        self.assertEqual(response.status_code, 200)
        # Debe mostrar directo protocolo de seguridad y canales urgentes
        self.assertContains(response, 'PELIGRO INMEDIATO DETECTADO')
        self.assertContains(response, 'Llamar al 911')
        self.assertContains(response, '0800 888 3672')
        # No debe pedir confirmación de ticket ni formulario de preguntas de seguimiento
        self.assertNotContains(response, '¿Deseás registrar formalmente esta solicitud?')

    def test_resumen_automatico_permite_correccion(self):
        """Requisito 3 y 4: Resumen automático antes de confirmar con campos editables de ubicación."""
        response = self.client.post(self.url, {
            'nombre': 'Horacio Quiroga',
            'dni': '27123456',
            'telefono': '3764554433',
            'detalle': 'Bache profundo en el asfalto en barrio Itaembé Guazú'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resumen Automático de la Solicitud')
        self.assertContains(response, 'Itaembé Guazú')
        self.assertContains(response, 'id="barrio"')
        self.assertContains(response, 'id="entre_calles"')
        self.assertContains(response, 'Registrar solicitud')
        self.assertContains(response, 'Solo necesitaba información')


class DirectorioOrganismosTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('portal_vecino')

    def test_directorio_organismos_completitud(self):
        """Requisito 5: Verifica información oficial verificada de IPRODHA, Defensoría, EMSA y dependencias."""
        organismos = obtener_directorio_organismos()
        org_ids = [o['id'] for o in organismos]
        self.assertIn('iprodha', org_ids)
        self.assertIn('defensoria_pueblo', org_ids)
        self.assertIn('emsa', org_ids)
        self.assertIn('samsa', org_ids)
        self.assertIn('mun_obras_publicas', org_ids)
        self.assertIn('mun_servicios_urbanos', org_ids)
        self.assertIn('mun_obras_privadas', org_ids)
        self.assertIn('mun_habilitaciones', org_ids)
        self.assertIn('mun_empleo', org_ids)
        self.assertIn('mun_salud_descacharrado', org_ids)
        self.assertIn('hcd_posadas', org_ids)
        self.assertIn('atm_misiones', org_ids)
        self.assertIn('registro_civil', org_ids)

        for org in organismos:
            self.assertIn('nombre', org)
            self.assertIn('competencia', org)
            self.assertIn('tipos_consultas', org)
            self.assertIn('requisitos_oficiales', org)
            self.assertIn('enlaces_oficiales', org)
            self.assertIn('canales_contacto', org)
            self.assertIn('fuente_verificacion', org)
            self.assertIn('fecha_verificacion', org)

    def test_obtener_organismos_cav_itaembe_retorna_seis_entidades(self):
        """Verifica que la función retorne las entidades con presencia en CAV Itaembé Guazú."""
        itaembe_orgs = obtener_organismos_cav_itaembe()
        self.assertEqual(len(itaembe_orgs), 8)
        ids = [o['id'] for o in itaembe_orgs]
        self.assertIn('mun_obras_privadas', ids)
        self.assertIn('mun_delegacion_itaembe', ids)
        self.assertIn('iprodha', ids)
        self.assertIn('registro_civil', ids)
        self.assertIn('atm_misiones', ids)
        self.assertIn('emsa', ids)
        self.assertIn('hcd_posadas', ids)
        self.assertIn('defensoria_pueblo', ids)

    def test_derivacion_organismo_externo_iprodha_sin_afirmar_reclamo(self):
        """Requisito 6: Deriva a IPRODHA sin afirmar que recibió el reclamo ni transferir datos."""
        response = self.client.post(self.url, {
            'nombre': 'Clara Méndez',
            'dni': '36111222',
            'telefono': '3764111222',
            'detalle': 'Quiero consultar sobre las cuotas de mi vivienda y cómo solicitar ampliación en IPRODHA'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Instituto Provincial de Desarrollo Habitacional')
        self.assertContains(response, 'iprodha.misiones.gob.ar')
        self.assertContains(response, 'Derivación')
        self.assertFalse(Expediente.objects.filter(dni_vecino=36111222).exists())

    def test_derivacion_defensoria_del_pueblo_mediacion(self):
        """Requisito 5 y 6: Deriva a Defensoría del Pueblo para mediación por ruidos molestos."""
        response = self.client.post(self.url, {
            'nombre': 'Susana Ríos',
            'dni': '35111333',
            'telefono': '3764333444',
            'detalle': 'Tengo problemas y conflicto con un vecino por ruidos molestos, quiero pedir mediación en la defensoría del pueblo'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Defensoría del Pueblo')
        self.assertContains(response, 'https://defensoriaposadas.gob.ar/')
        self.assertContains(response, 'Buenos Aires N° 1441')
        self.assertFalse(Expediente.objects.filter(dni_vecino=35111333).exists())


class EvaluacionSatisfaccionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('portal_vecino')

    def test_evaluacion_consulta_vecino(self):
        """Requisito 8: Registra la evaluación (Sí / Parcialmente / No) para estadísticas."""
        # Primero se genera una consulta
        r1 = self.client.post(self.url, {
            'nombre': 'Esteban Morales',
            'dni': '38999888',
            'telefono': '3764999888',
            'detalle': '¿Dónde pago la patente del auto?'
        })
        self.assertEqual(r1.status_code, 200)
        self.assertContains(r1, '¿Pudiste resolver tu consulta?')
        reg = RegistroConsulta.objects.filter(texto_consultado__icontains='patente').first()
        self.assertIsNotNone(reg)
        self.assertEqual(reg.evaluacion_vecino, 'PENDIENTE')

        # Ahora el vecino califica "Sí"
        r2 = self.client.post(self.url, {
            'btn_evaluar_consulta': '1',
            'id_consulta': reg.identificador_consulta,
            'evaluacion': 'SI'
        })
        self.assertEqual(r2.status_code, 200)
        reg.refresh_from_db()
        self.assertEqual(reg.evaluacion_vecino, 'SI')
        self.assertIsNotNone(reg.fecha_evaluacion)
        self.assertContains(r2, '¡Muchas gracias por tu valoración!')

    def test_evaluacion_reclamo_bache_con_ticket_funciona_para_si_parcial_y_no(self):
        """Verifica que al crear un ticket de reclamo (ej. bache) y puntuar 'SI', 'PARCIAL' o 'NO' no falle y registre las 3 valoraciones en estadísticas."""
        for idx, valor in enumerate(['PARCIAL', 'SI', 'NO'], start=1):
            dni_str = f'3610020{idx}'
            r_ticket = self.client.post(self.url, {
                'nombre': 'Juan Carlos Pérez',
                'dni': dni_str,
                'telefono': '3764187444',
                'detalle': f'Hay un bache grande en la calle frente al lote {idx}',
                'barrio': 'Itaembé Guazú',
                'entre_calles': 'Las Magnolias y Aguará Guazú',
                'accion': 'registrar',
            })
            self.assertEqual(r_ticket.status_code, 200)
            id_consulta = r_ticket.context['id_consulta']
            nro_ticket = r_ticket.context['nro_ticket']
            self.assertIsNotNone(id_consulta)
            self.assertIsNotNone(nro_ticket)

            # Puntuar la valoración (PARCIAL, SI, NO) luego de haber generado el ticket
            r_eval = self.client.post(self.url, {
                'btn_evaluar_consulta': '1',
                'id_consulta': id_consulta,
                'evaluacion': valor,
            })
            self.assertEqual(r_eval.status_code, 200)
            self.assertContains(r_eval, '¡Muchas gracias por tu valoración!')
            self.assertContains(r_eval, nro_ticket)
            self.assertContains(r_eval, 'Juan Carlos Pérez')

            reg = RegistroConsulta.objects.get(identificador_consulta=id_consulta)
            self.assertEqual(reg.evaluacion_vecino, valor)
            self.assertIsNotNone(reg.fecha_evaluacion)

        # Verificar que el Panel Gerencial reciba y contabilice correctamente SI, PARCIAL y NO
        r_panel = self.client.get(reverse('panel_gerencial'))
        self.assertEqual(r_panel.status_code, 200)
        self.assertEqual(r_panel.context['satisfaccion_parcial'], 1)
        self.assertEqual(r_panel.context['satisfaccion_si'], 1)
        self.assertEqual(r_panel.context['satisfaccion_no'], 1)
        self.assertEqual(r_panel.context['total_evaluadas'], 3)


class SugerenciaOrganismoTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('portal_vecino')

    def test_seccion_sugerencia_visible_en_portal(self):
        """Verifica que el mensaje y el formulario de sugerencia estén visibles en el portal."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '¿Querés que se agregue algún organismo o entidad presente en el CAV Sede Itaembé Guazú?')
        self.assertContains(response, 'Hacénoslo saber aquí')
        self.assertContains(response, 'sugerencia_organismo')
        self.assertContains(response, 'Enviar sugerencia')

    def test_envio_sugerencia_organismo_exitoso(self):
        """El vecino envía una sugerencia y se guarda en la base de datos."""
        response = self.client.post(self.url, {
            'btn_sugerir_organismo': '1',
            'sugerencia_organismo': 'Me gustaría que incorporen trámites de ANSES y PAMI en el CAV Las Heras',
            'nombre_sugerente': 'Marcos Gimenez',
            'contacto_sugerente': '3764889900'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '¡Muchas gracias por tu propuesta!')
        self.assertContains(response, 'Tu propuesta fue registrada con éxito')
        sug = SugerenciaOrganismo.objects.filter(texto_sugerencia__icontains='ANSES').first()
        self.assertIsNotNone(sug)
        self.assertEqual(sug.nombre_vecino, 'Marcos Gimenez')
        self.assertEqual(sug.contacto, '3764889900')
        self.assertEqual(sug.estado, 'PENDIENTE')

    def test_envio_sugerencia_vacia_error(self):
        """Enviar la sugerencia vacía muestra un mensaje de advertencia sin crear registro."""
        response = self.client.post(self.url, {
            'btn_sugerir_organismo': '1',
            'sugerencia_organismo': '   '
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Por favor, escribí el nombre o detalle del organismo o entidad')
        self.assertEqual(SugerenciaOrganismo.objects.count(), 0)

    def test_sugerencias_visibles_en_mesa_entrada(self):
        """Las sugerencias registradas aparecen en la vista de Mesa de Entrada."""
        SugerenciaOrganismo.objects.create(
            texto_sugerencia='Sumar atención de Registro de la Propiedad Inmueble',
            nombre_vecino='Laura Benítez'
        )
        response = self.client.get(reverse('mesa_entrada'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Registro de la Propiedad Inmueble')
        self.assertContains(response, 'Laura Benítez')

    def test_envio_sugerencia_sin_nombre_o_sin_telefono_error(self):
        """No permite enviar una sugerencia sin completar nombre y teléfono obligatorios."""
        response = self.client.post(self.url, {
            'btn_sugerir_organismo': '1',
            'sugerencia_organismo': 'Sumar delegación de ANSES',
            'nombre_sugerente': '',
            'contacto_sugerente': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ambos son obligatorios')
        self.assertEqual(SugerenciaOrganismo.objects.count(), 0)

    def test_envio_sugerencia_organismo_ya_existente_iprodha(self):
        """Si el vecino sugiere IProDHa, el sistema le informa que ya existe y no crea duplicado."""
        response = self.client.post(self.url, {
            'btn_sugerir_organismo': '1',
            'sugerencia_organismo': 'propuesta de iprodha',
            'nombre_sugerente': 'Camila Denis',
            'contacto_sugerente': '3764187444'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '¡Este organismo ya se encuentra en el sistema!')
        self.assertContains(response, 'ya se encuentra incorporado en el sistema SIVEG')
        self.assertContains(response, 'IProDHa')
        self.assertEqual(SugerenciaOrganismo.objects.count(), 0)

    def test_envio_sugerencia_organismo_ya_existente_emsa(self):
        """Si el vecino sugiere EMSA, el sistema le informa que ya existe y brinda sus detalles oficiales."""
        response = self.client.post(self.url, {
            'btn_sugerir_organismo': '1',
            'sugerencia_organismo': 'Quiero que esté EMSA para pagar la luz',
            'nombre_sugerente': 'Camila Denis',
            'contacto_sugerente': '3764187444'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '¡Este organismo ya se encuentra en el sistema!')
        self.assertContains(response, 'Energía de Misiones')
        self.assertEqual(SugerenciaOrganismo.objects.count(), 0)


    def test_consulta_ganar_casa_dirige_a_iprodha_sorteos(self):
        """Consulta 'quiero ganar una casa' debe derivar a IProDHa con la guía de inscripción y enlace oficial."""
        response = self.client.post(self.url, {
            'nombre': 'Estela Ramírez',
            'dni': '28999111',
            'telefono': '3764112233',
            'detalle': 'Hola, quiero saber cómo hacer porque quiero ganar una casa en Posadas'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'IProDHa')
        self.assertContains(response, 'iprodha.misiones.gob.ar')
        self.assertContains(response, 'GANAR UNA CASA')
        self.assertContains(response, 'PARTICIPAR')
        self.assertContains(response, 'Iniciar trámite online en IProDHa')
        self.assertIn('Instituto Provincial de Desarrollo Habitacional', response.context['organismo_destino'])
        self.assertFalse(Expediente.objects.filter(dni_vecino=28999111).exists())

    def test_consulta_donde_anotarse_casa_dirige_a_iprodha(self):
        """Consulta 'donde uno se anota para una casa' orienta hacia el portal del IPRODHA."""
        response = self.client.post(self.url, {
            'nombre': 'Claudio Fernández',
            'dni': '31222333',
            'telefono': '3764998877',
            'detalle': 'donde uno se anota para una casa'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'IProDHa')
        self.assertContains(response, 'iprodha.misiones.gob.ar')
        self.assertIn('Instituto Provincial de Desarrollo Habitacional', response.context['organismo_destino'])
        self.assertFalse(Expediente.objects.filter(dni_vecino=31222333).exists())

    def test_consulta_generar_boleta_patente_dirige_a_dgr_sin_clave_fiscal(self):
        """Consulta 'al generar boleta patente' debe llevar a [DGR - Sin Clave Fiscal](https://sinclavefiscal.atm.misiones.gob.ar/sc/automotor/emision_ba_ipa)."""
        response = self.client.post(self.url, {
            'nombre': 'Horacio Quiroga',
            'dni': '27123456',
            'telefono': '3764887766',
            'detalle': 'al generar boleta patente quiero saber como pagar'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'DGR - Sin Clave Fiscal')
        self.assertContains(response, 'https://sinclavefiscal.atm.misiones.gob.ar/sc/automotor/emision_ba_ipa')
        self.assertContains(response, 'Dominio')
        self.assertContains(response, 'Posadas')
        self.assertFalse(Expediente.objects.filter(dni_vecino=27123456).exists())


class SeguimientoYDerivacionTicketTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url_portal = reverse('portal_vecino')
        self.url_mesa = reverse('mesa_entrada')

        self.expediente = Expediente.objects.create(
            nro_expediente='TCK-77112',
            dni_vecino=33444555,
            nombre_completo='Valeria Duarte',
            telefono_contacto='3764556677',
            tipo_solicitud='RECLAMO',
            detalle_consulta='Reclamo por falta de luminarias en calle principal y baches',
            organismo_destino='Secretaría de Planificación Estratégica y Territorial / Obras Privadas',
            estado_actual='DERIVADO',
            barrio='Itaembé Guazú',
            entre_calles='Los Lirios y Las Azaleas'
        )

    def test_consulta_estado_ticket_existente_por_numero(self):
        """El vecino ingresa el N° de Ticket y ve su estado actual y hacia dónde fue derivado."""
        response = self.client.post(self.url_portal, {
            'btn_consultar_ticket': '1',
            'busqueda_ticket': 'TCK-77112'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TCK-77112')
        self.assertContains(response, 'DERIVADO')
        self.assertContains(response, 'Secretaría de Planificación Estratégica y Territorial / Obras Privadas')
        self.assertContains(response, 'Valeria Duarte')
        self.assertContains(response, 'Itaembé Guazú')
        self.assertIn('tramites', response.context)
        self.assertEqual(len(response.context['tramites']), 1)

    def test_consulta_estado_ticket_case_insensitive(self):
        """El buscador permite buscar 'tck-77112' en minúsculas y encuentra el expediente."""
        response = self.client.post(self.url_portal, {
            'btn_consultar_ticket': '1',
            'busqueda_ticket': 'tck-77112'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TCK-77112')
        self.assertContains(response, 'DERIVADO')
        self.assertContains(response, 'Secretaría de Planificación Estratégica y Territorial / Obras Privadas')

    def test_consulta_estado_ticket_por_dni(self):
        """El vecino puede consultar el estado de sus trámites ingresando su DNI."""
        response = self.client.post(self.url_portal, {
            'btn_consultar_ticket': '1',
            'busqueda_ticket': '33444555'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TCK-77112')
        self.assertContains(response, 'DERIVADO')
        self.assertContains(response, 'Secretaría de Planificación Estratégica y Territorial / Obras Privadas')

    def test_consulta_ticket_inexistente_muestra_alerta(self):
        """Búsqueda con un número inexistente muestra mensaje de no encontrado."""
        response = self.client.post(self.url_portal, {
            'btn_consultar_ticket': '1',
            'busqueda_ticket': 'TCK-00000'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No se encontraron trámites ni tickets registrados')

    def test_consulta_ticket_conversacional_en_asistente(self):
        """El vecino escribe 'hacia dónde fue derivado mi ticket TCK-77112' en el chat y el asistente responde con el estado y destino."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Valeria Duarte',
            'dni': '33444555',
            'telefono': '3764556677',
            'detalle': 'Hola, quiero saber hacia dónde fue derivado mi ticket TCK-77112'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TCK-77112')
        self.assertContains(response, 'DERIVADO')
        self.assertContains(response, 'Secretaría de Planificación Estratégica y Territorial / Obras Privadas')
        self.assertIn('Secretaría de Planificación', response.context['organismo_destino'])

    def test_consulta_seguimiento_general_orienta_a_buscador(self):
        """Si el vecino pregunta genéricamente cómo sigue su reclamo, se le orienta a usar el buscador con su Ticket o DNI."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Valeria Duarte',
            'dni': '33444555',
            'telefono': '3764556677',
            'detalle': '¿Cómo sigue mi reclamo y dónde fue derivado?'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'hacia dónde fue derivado')
        self.assertContains(response, 'Buscador de Trámites')

    def test_mesa_entrada_puede_derivar_expediente(self):
        """Desde Mesa de Entrada se puede actualizar el organismo de destino y el estado del ticket."""
        response = self.client.post(self.url_mesa, {
            'btn_derivar_expediente': '1',
            'expediente_id': self.expediente.id,
            'organismo_destino': 'Municipalidad de Posadas - Servicios Urbanos (Alumbrado Público)',
            'nuevo_estado': 'EN_PROCESO'
        })
        self.assertEqual(response.status_code, 200)
        self.expediente.refresh_from_db()
        self.assertEqual(self.expediente.estado_actual, 'EN_PROCESO')
        self.assertEqual(self.expediente.organismo_destino, 'Municipalidad de Posadas - Servicios Urbanos (Alumbrado Público)')

    def test_generacion_tickets_correlativos_anuales(self):
        """Los tickets generados son correlativos anuales en formato TCK-YYYY-XXXX."""
        from .views import generar_siguiente_nro_ticket
        t1 = generar_siguiente_nro_ticket()
        self.assertTrue(t1.startswith('TCK-'))
        self.assertIn('-000', t1)

        # Crear expediente con t1 y pedir el siguiente
        Expediente.objects.create(
            nro_expediente=t1,
            dni_vecino=40111222,
            nombre_completo='Vecino Uno',
            telefono_contacto='3764001122',
            detalle_consulta='Prueba correlativo 1'
        )

        t2 = generar_siguiente_nro_ticket()
        # El número final de t2 debe ser exactamente el número de t1 + 1
        num1 = int(t1.split('-')[-1])
        num2 = int(t2.split('-')[-1])
        self.assertEqual(num2, num1 + 1)

    def test_registro_reclamo_asigna_ticket_correlativo(self):
        """Al confirmar un reclamo en el portal se le asigna el siguiente ticket correlativo."""
        from django.utils import timezone
        anio = timezone.now().strftime('%Y')
        response = self.client.post(self.url_portal, {
            'nombre': 'Ramiro Benítez',
            'dni': '39555666',
            'telefono': '3764889911',
            'detalle': 'Hay pozos y baches en la avenida',
            'barrio': 'Centro',
            'entre_calles': 'San Lorenzo y Bolívar',
            'accion': 'registrar'
        })
        self.assertEqual(response.status_code, 200)
        exp = Expediente.objects.filter(dni_vecino=39555666).first()
        self.assertIsNotNone(exp)
        self.assertTrue(exp.nro_expediente.startswith(f'TCK-{anio}-'))
        self.assertContains(response, exp.nro_expediente)

    def test_consulta_conversacional_ticket_formato_anual(self):
        """El asistente reconoce y responde consultas conversacionales con formato anual TCK-2026-0001."""
        from django.utils import timezone
        anio = timezone.now().strftime('%Y')
        nro = f"TCK-{anio}-0088"
        Expediente.objects.create(
            nro_expediente=nro,
            dni_vecino=36777888,
            nombre_completo='Lorena Ríos',
            telefono_contacto='3764223344',
            tipo_solicitud='RECLAMO',
            detalle_consulta='Luz quemada en pasaje',
            organismo_destino='Municipalidad de Posadas - Servicios Urbanos (Alumbrado)',
            estado_actual='DERIVADO'
        )

        response = self.client.post(self.url_portal, {
            'nombre': 'Lorena Ríos',
            'dni': '36777888',
            'telefono': '3764223344',
            'detalle': f'Hola, ¿cómo sigue mi reclamo {nro}?'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, nro)
        self.assertContains(response, 'DERIVADO')
        self.assertContains(response, 'Servicios Urbanos (Alumbrado)')

    def test_consulta_empezar_obra_sin_ubicacion_pregunta_donde_vive(self):
        """Al consultar por 'quiero empezar una obra' sin indicar ubicación, el asistente orienta con Sistema GOP y pregunta dónde vivirá la obra."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Martín Silva',
            'dni': '35123456',
            'telefono': '3764556677',
            'detalle': 'quiero empezar una obra'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sistema GOP')
        self.assertContains(response, 'Secretaría de Planificación Estratégica')
        self.assertContains(response, '¿DÓNDE VIVÍS O DÓNDE SE UBICARÁ LA OBRA?')
        self.assertContains(response, 'FOS y FOT')
        self.assertContains(response, 'CAV Itaembé Guazú')
        self.assertFalse(Expediente.objects.filter(dni_vecino=35123456).exists())

    def test_consulta_empezar_obra_con_ubicacion_informa_zonificacion(self):
        """Al consultar por empezar una obra indicando el barrio, el asistente reconoce el barrio y asesora sobre zonificación."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Martín Silva',
            'dni': '35123456',
            'telefono': '3764556677',
            'detalle': 'quiero empezar una obra en Itaembe Guazu'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sistema GOP')
        self.assertContains(response, 'Itaembe Guazu')
        self.assertContains(response, 'UBICACIÓN DE LA OBRA INFORMADA')
        self.assertContains(response, 'CAV Itaembé Guazú')

    def test_emergencia_cable_pelado_pregunta_ubicacion_para_servicios(self):
        """Avisar sobre un cable pelado activa emergencia eléctrica y consulta dónde se ubica para el 911/EMSA."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Valeria Duarte',
            'dni': '38123456',
            'telefono': '3764332211',
            'detalle': 'hay un cable pelado en la vereda'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Emergencia Eléctrica Crítica')
        self.assertContains(response, 'Llamar al 911')
        self.assertContains(response, '0800 888 3672')
        self.assertContains(response, '¿DÓNDE SE ENCUENTRA EL PELIGRO?')
        self.assertFalse(Expediente.objects.filter(dni_vecino=38123456).exists())

    def test_emergencia_poste_caido_pregunta_ubicacion_para_servicios(self):
        """Avisar sobre un poste caído activa emergencia eléctrica y consulta dónde se encuentra para los equipos de respuesta."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Valeria Duarte',
            'dni': '38123456',
            'telefono': '3764332211',
            'detalle': 'poste caido con peligro'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Emergencia Eléctrica Crítica')
        self.assertContains(response, '0800 888 3672')
        self.assertContains(response, '¿DÓNDE SE ENCUENTRA EL PELIGRO?')
        self.assertFalse(Expediente.objects.filter(dni_vecino=38123456).exists())

    def test_emergencia_cable_pelado_con_ubicacion_especifica_registra_lugar(self):
        """Si el vecino informa el barrio al reportar cable pelado, el asistente registra la ubicación exacta para la llamada al 911/EMSA."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Valeria Duarte',
            'dni': '38123456',
            'telefono': '3764332211',
            'detalle': 'hay un cable pelado en Villa Sarita entre San Martin y Coronel Lopez'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'UBICACIÓN INFORMADA: Barrio Villa Sarita')
        self.assertContains(response, 'UBICACIÓN DEL PELIGRO REGISTRADA')
        self.assertContains(response, '0800 888 3672')

    def test_validacion_nombre_sin_apellido_falla(self):
        """Si el vecino solo ingresa un nombre sin apellido, se rechaza y se le solicita nombre y apellido completo."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Juan',
            'dni': '36268087',
            'telefono': '3764187444',
            'detalle': 'Consulta sobre tasas municipales'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Por favor, ingresá tu nombre y apellido completo')

    def test_validacion_dni_distinto_a_8_numeros_falla(self):
        """El DNI debe contener exactamente 8 números (sin puntos ni letras, ej: 36268087)."""
        response_corto = self.client.post(self.url_portal, {
            'nombre': 'Juan Perez',
            'dni': '362680',
            'telefono': '3764187444',
            'detalle': 'Consulta sobre tasas municipales'
        })
        self.assertEqual(response_corto.status_code, 200)
        self.assertContains(response_corto, 'El DNI debe contener exactamente 8 números')

        response_largo = self.client.post(self.url_portal, {
            'nombre': 'Juan Perez',
            'dni': '36268087123',
            'telefono': '3764187444',
            'detalle': 'Consulta sobre tasas municipales'
        })
        self.assertEqual(response_largo.status_code, 200)
        self.assertContains(response_largo, 'El DNI debe contener exactamente 8 números')

    def test_validacion_telefono_sin_caracteristica_37_falla(self):
        """Teléfonos que no comiencen con la característica 37 (Posadas / Misiones) son rechazados."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Juan Perez',
            'dni': '36268087',
            'telefono': '1144556677',
            'detalle': 'Consulta sobre tasas'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'debe comenzar con la característica 37')

    def test_validacion_telefono_formato_posadas_con_15_y_guiones_valido(self):
        """Acepta teléfonos con formato provincial con 15 y guiones (ej: 3764-15-187444 o 3764187444) normalizándolos."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Juan Perez',
            'dni': '36268087',
            'telefono': '3764-15-187444',
            'detalle': 'Hay un pozo y bache profundo en la calle',
            'barrio': 'Villa Sarita',
            'entre_calles': 'Coronel Álvarez y Arrechea',
            'accion': 'registrar'
        })
        self.assertEqual(response.status_code, 200)
        exp = Expediente.objects.filter(dni_vecino=36268087).first()
        self.assertIsNotNone(exp)
        self.assertEqual(exp.telefono_contacto, '3764187444')
        self.assertEqual(exp.nombre_completo, 'Juan Perez')

    def test_denuncia_ampliacion_muro_vecina_dirige_a_obras_publicas(self):
        """Denunciar una ampliación o construcción de un vecino sobre muro medianero dirige a Obras Públicas, no a trámites del CAV."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Camila Denis',
            'dni': '36268087',
            'telefono': '3764187444',
            'detalle': 'quiero denunciar la amplaicion de mi vecina que ocupó mi muro'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Municipalidad de Posadas - Obras Públicas')
        self.assertNotContains(response, 'Atención General al Vecino y Trámites Integrados CAV')
        self.assertContains(response, 'Reclamo / Solicitud Municipal')
        self.assertContains(response, 'Registrar solicitud')

    def test_denuncia_ampliacion_muro_confirmada_crea_ticket_obras_publicas(self):
        """Al confirmar la denuncia por ocupación de muro medianero, se crea el ticket derivado a Obras Públicas."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Camila Denis',
            'dni': '36268087',
            'telefono': '3764187444',
            'detalle': 'quiero denunciar que una vecina amplió su casa por mi muro',
            'barrio': 'Santa Rita',
            'entre_calles': 'Monseñor D’Andrea y Chacabuco',
            'accion': 'registrar'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ticket Interno N°:')
        exp = Expediente.objects.filter(dni_vecino=36268087, detalle_consulta__contains='muro').first()
        self.assertIsNotNone(exp)
        self.assertEqual(exp.organismo_destino, 'Municipalidad de Posadas - Obras Públicas')
        self.assertEqual(exp.tipo_solicitud, 'RECLAMO')
        self.assertEqual(exp.estado_actual, 'PENDIENTE')

    def test_registro_reclamo_con_ubicacion_vacia_falla_y_no_crea_ticket(self):
        """Al presionar Registrar solicitud sin barrio o sin calles, se rechaza y no se crea ticket."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Juan Perez',
            'dni': '36268087',
            'telefono': '3764187444',
            'detalle': 'quiero denunciar que una vecina amplió su casa por mi muro',
            'barrio': '',
            'entre_calles': '',
            'accion': 'registrar'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Para registrar formalmente tu solicitud es obligatorio indicar el Barrio o Chacra y entre qué calles o altura se ubica.')
        self.assertNotContains(response, 'Ticket Interno N°:')
        self.assertEqual(Expediente.objects.filter(dni_vecino=36268087).count(), 0)

    def test_registro_reclamo_solo_barrio_vacio_falla(self):
        """Al presionar Registrar solicitud con barrio vacío, falla la validación."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Juan Perez',
            'dni': '36268087',
            'telefono': '3764187444',
            'detalle': 'Hay un pozo en la calle',
            'barrio': '',
            'entre_calles': 'San Martín 1200',
            'accion': 'registrar'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Para registrar formalmente tu solicitud es obligatorio indicar el Barrio o Chacra y entre qué calles o altura se ubica.')
        self.assertEqual(Expediente.objects.filter(dni_vecino=36268087).count(), 0)

    def test_registro_reclamo_solo_calles_vacia_falla(self):
        """Al presionar Registrar solicitud con calles vacías, falla la validación."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Juan Perez',
            'dni': '36268087',
            'telefono': '3764187444',
            'detalle': 'Hay un pozo en la calle',
            'barrio': 'Villa Sarita',
            'entre_calles': '',
            'accion': 'registrar'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Para registrar formalmente tu solicitud es obligatorio indicar el Barrio o Chacra y entre qué calles o altura se ubica.')
        self.assertEqual(Expediente.objects.filter(dni_vecino=36268087).count(), 0)

    def test_registro_reclamo_con_ubicacion_completa_crea_ticket(self):
        """Al presionar Registrar solicitud con barrio y calles completos, se genera el ticket con estado PENDIENTE."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Juan Perez',
            'dni': '36268087',
            'telefono': '3764187444',
            'detalle': 'quiero denunciar que una vecina amplió su casa por mi muro',
            'barrio': 'Villa Sarita',
            'entre_calles': 'San Martín y Colón',
            'referencias': 'Frente a la plaza',
            'accion': 'registrar'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ticket Interno N°:')
        exp = Expediente.objects.filter(dni_vecino=36268087).first()
        self.assertIsNotNone(exp)
        self.assertEqual(exp.barrio, 'Villa Sarita')
        self.assertEqual(exp.entre_calles, 'San Martín y Colón')
        self.assertEqual(exp.referencias, 'Frente a la plaza')
        self.assertEqual(exp.estado_actual, 'PENDIENTE')

    def test_respuesta_obra_muro_concisa_y_directa(self):
        """La respuesta de denuncia de obra sobre muro es concisa, indica denuncia en Obras Privadas y repregunta ubicación."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Camila Denis',
            'dni': '36268087',
            'telefono': '3764187444',
            'detalle': 'quiero denunciar que una vecina amplió su casa por mi muro'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'denuncia de obra')
        self.assertContains(response, 'Dirección de Obras Privadas (Obras Públicas)')
        self.assertContains(response, 'barrio o chacra')
        self.assertContains(response, 'calles, numeración o avenidas')
        self.assertContains(response, 'fotos es opcional')
        self.assertContains(response, 'Sector de Itaembé Guazú')
        self.assertContains(response, 'Tu Dirección (Calle y N° / Entre calles)')
        self.assertContains(response, 'nombre de la vecina o vecino')
        self.assertContains(response, 'detalle_confirmar')

    def test_interfaz_portal_vecino_campos_simplificados_y_circulos_fondo(self):
        """El portal vecino incluye círculos decorativos claros y campos con texto limpio y resumido."""
        response = self.client.get(self.url_portal)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'circulo-decorativo')
        self.assertContains(response, 'placeholder="Ej: Camila Denis"')
        self.assertContains(response, 'placeholder="Ej: 36268087"')
        self.assertContains(response, 'placeholder="Ej: 3764187444"')
        self.assertContains(response, 'Ej: Camila Denis</div>')
        self.assertContains(response, 'Ej: 36268087</div>')
        self.assertContains(response, 'Ej: 3764187444</div>')
        self.assertContains(response, 'Nombre y Apellido')
        self.assertNotContains(response, 'Nombre y Apellido Completo')
        self.assertNotContains(response, 'DNI (8 dígitos)')

    def test_seguimiento_en_columna_izquierda_cuando_hay_reclamo(self):
        """Cuando la IA responde con un reclamo (texto largo a la derecha), el buscador de ticket se ubica en la columna izquierda."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Camila Denis',
            'dni': '36268087',
            'telefono': '3764187444',
            'detalle': 'quiero denunciar que una vecina amplió su casa por mi muro'
        })
        self.assertEqual(response.status_code, 200)
        # Debe mostrar el formulario de consulta en la columna izquierda y debajo el seguimiento
        self.assertContains(response, '¿Ya realizaste un reclamo o trámite?')
        self.assertContains(response, 'TCK-2026-0001')

    def test_archivos_adjuntos_servidos_correctamente_sin_404(self):
        """Los archivos adjuntos de tickets (fotos, videos, docs) son servidos vía HTTP con código 200 y accesibles desde Mesa de Entrada."""
        archivo_test = SimpleUploadedFile(
            name="prueba_foto_bache.jpg",
            content=b"datos_ficticios_imagen_jpeg_posadas",
            content_type="image/jpeg"
        )
        expediente = Expediente.objects.create(
            nro_expediente="TCK-2026-9999",
            nombre_completo="Camila Denis",
            dni_vecino=36268087,
            telefono_contacto="3764187444",
            barrio="Villa Sarita",
            entre_calles="San Martín y Colón",
            detalle_consulta="Bache profundo en la esquina",
            organismo_destino="Municipalidad de Posadas - Obras Públicas",
            estado_actual="PENDIENTE",
            archivo_adjunto=archivo_test
        )
        try:
            # 1. Verificar que la URL del archivo responde HTTP 200 y sirve el contenido real
            response_media = self.client.get(expediente.archivo_adjunto.url)
            self.assertEqual(response_media.status_code, 200)
            contenido_recibido = b"".join(response_media.streaming_content)
            self.assertEqual(contenido_recibido, b"datos_ficticios_imagen_jpeg_posadas")
            response_media.close()

            # 2. Verificar que en Mesa de Entrada aparece el botón 'Ver' con el enlace correcto
            response_mesa = self.client.get(reverse('mesa_entrada'))
            self.assertEqual(response_mesa.status_code, 200)
            self.assertContains(response_mesa, expediente.archivo_adjunto.url)
            self.assertContains(response_mesa, 'target="_blank"')
        finally:
            if expediente.archivo_adjunto:
                expediente.archivo_adjunto.delete(save=False)

    def test_consulta_abrir_negocio_deriva_a_habilitaciones_con_preguntas(self):
        """Consulta 'quise abrir un negocio' deriva a Habilitaciones Comerciales preguntando rubro y si es ampliación de casa."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Camila Denis',
            'dni': '36268087',
            'telefono': '3764187444',
            'detalle': 'quise abrir un negocio'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['es_reclamo'])
        self.assertIn('Habilitaciones Comerciales', response.context['organismo_destino'])
        self.assertContains(response, 'Dirección General de Habilitaciones Comerciales')
        self.assertContains(response, 'Rubro o actividad')
        self.assertContains(response, 'ampliación de tu casa')
        self.assertContains(response, 'Registrar solicitud')

    def test_confirmacion_solicitud_abrir_negocio_genera_ticket(self):
        """Confirmar la solicitud de abrir un negocio genera el ticket administrativo para Habilitaciones Comerciales."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Camila Denis',
            'dni': '36268087',
            'telefono': '3764187444',
            'detalle': 'quise abrir un negocio de almacen',
            'barrio': 'Villa Sarita',
            'entre_calles': 'San Martín y Colón',
            'accion': 'registrar'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'solicitud de apertura y habilitación comercial')
        self.assertContains(response, 'Obras Públicas y Habilitaciones Comerciales')
        exp = Expediente.objects.filter(dni_vecino=36268087, detalle_consulta='quise abrir un negocio de almacen').first()
        self.assertIsNotNone(exp)
        self.assertTrue(exp.nro_expediente.startswith('TCK-'))
        self.assertIn('Habilitaciones Comerciales', exp.organismo_destino)

    def test_consulta_quiero_hacer_negocio_obras_publicas_y_requisitos(self):
        """Consulta 'quiero hacer negocio' muestra respuesta de Obras Públicas y Habilitaciones con requisitos y preguntas arriba."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Camila Denis',
            'dni': '36268087',
            'telefono': '3764187444',
            'detalle': 'quiero hacer negocio'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['es_reclamo'])
        self.assertIn('Obras Públicas', response.context['organismo_destino'])
        self.assertIn('Habilitaciones Comerciales', response.context['organismo_destino'])
        self.assertContains(response, 'Obras Públicas')
        self.assertContains(response, 'Requisitos principales')
        self.assertContains(response, 'ampliación de tu casa')
        self.assertContains(response, 'id="seccion-consulta"')
        self.assertContains(response, f'action="{self.url_portal}#seccion-consulta"')
        self.assertContains(response, 'Registrar solicitud')

    def test_portal_vecino_formulario_apunta_a_seccion_consulta(self):
        """El formulario de consulta apunta a #seccion-consulta para no saltar a otras secciones."""
        response = self.client.get(self.url_portal)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="seccion-consulta"')
        self.assertContains(response, f'action="{self.url_portal}#seccion-consulta"')

    def test_organismos_vinculados_incluye_emsa_con_enlace(self):
        """Verifica que en Organismos y Servicios Vinculados se encuentre el logo y enlace oficial de EMSA."""
        response = self.client.get(self.url_portal)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'logo_emsa.webp')
        self.assertContains(response, 'https://www.energiademisiones.com.ar/')
        self.assertContains(response, 'Energía de Misiones - EMSA')

    def test_organismos_vinculados_registro_civil_orienta_a_portal_oficial(self):
        """Verifica que el logo de Registro Provincial de las Personas enlace a su portal oficial."""
        response = self.client.get(self.url_portal)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'https://www.registrocivil.misiones.gov.ar/')
        self.assertContains(response, 'https://defensoriadelpueblodeposadas.gob.ar/')

    def test_consulta_registro_civil_orienta_a_google_maps_y_telefonos(self):
        """Consulta sobre partidas o actas orienta a Google Maps con sedes y teléfonos de Posadas."""
        response = self.client.post(self.url_portal, {
            'nombre': 'Martina Benítez',
            'dni': '34555666',
            'telefono': '3764889900',
            'detalle': 'Cómo solicito una partida de nacimiento en el registro civil'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Registro Provincial de las Personas')
        self.assertContains(response, 'Google Maps')
        self.assertContains(response, 'https://www.google.com/maps/search/Registro+Provincial+de+las+Personas+Posadas+Misiones')
        self.assertContains(response, '445-8235')

    def test_formulario_sugerencia_sin_texto_obligatorio_en_etiquetas(self):
        """El formulario de sugerencia de organismos no muestra la palabra 'obligatorio' en las etiquetas."""
        response = self.client.get(self.url_portal)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="seccion-sugerencia-organismo"')
        self.assertNotContains(response, 'Organismo, entidad o servicio que sugerís sumar: <span class="text-danger fw-bold">* (obligatorio)</span>')
        self.assertNotContains(response, 'Tu Nombre y Apellido: <span class="text-danger fw-bold">* (obligatorio)</span>')
        self.assertNotContains(response, 'Teléfono de Contacto: <span class="text-danger fw-bold">* (obligatorio)</span>')

    def test_envio_sugerencia_totalmente_vacio_indica_campos_obligatorios(self):
        """Al enviar sugerencia vacía, se informa que los campos son obligatorios."""
        response = self.client.post(self.url_portal, {
            'btn_sugerir_organismo': '1',
            'sugerencia_organismo': '',
            'nombre_sugerente': '',
            'contacto_sugerente': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'campo obligatorio')

    def test_portal_vecino_script_deteccion_recarga_y_limpieza(self):
        """El portal cuenta con el script que detecta recargas (F5) para iniciar limpio desde cero."""
        response = self.client.get(self.url_portal)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'esRecarga')
        self.assertContains(response, 'window.location.replace')

    def test_portal_vecino_sede_cav_itaembe_mapa_y_sin_tramites_redundantes(self):
        """La sección unificada Sede CAV Itaembé Guazú muestra la dirección correcta (Aguará Guazú y Magnolias),
        los logos de los organismos, el subtítulo '¡Te indico cómo llegar!' y el mapa embebido con enlace a Google Maps."""
        response = self.client.get(self.url_portal)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Servicios Vinculados Sede CAV Itaembé Guazú')
        self.assertContains(response, 'Calle Aguará Guazú y Magnolias')
        self.assertContains(response, '¡Te indico cómo llegar en Google Maps!')
        self.assertContains(response, 'fa-hand-point-down')
        self.assertContains(response, 'maps.google.com/maps?q=Calle+Aguar%C3%A1+Guaz%C3%BA+y+Magnolias')
        self.assertNotContains(response, 'Ver ubicación en Google Maps')
        self.assertNotContains(response, 'Organismos y dependencias con atención presencial al vecino:')

    def test_navbar_titulo_cav_itaembe_guazu(self):
        """Verifica que el encabezado principal del portal mencione CAV ITAEMBÉ GUAZÚ."""
        response = self.client.get(self.url_portal)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SISTEMA INTEGRAL DE ATENCIÓN Y ASESORAMIENTO AL VECINO - CAV ITAEMBÉ GUAZÚ')

    def test_reclamo_ruidos_molestos_orientacion_control_comunal_y_ordenanza(self):
        """
        Verifica que al denunciar ruidos molestos o música fuerte:
        - Se derive a Dirección de Control Comunal (Guardia de Ruidos Molestos de la Municipalidad).
        - Se asesore citando la Ordenanza VI – Nº 14 de Posadas y horarios de descanso.
        - Se indique el WhatsApp oficial de la Guardia (3764-134650).
        - Se instruya al vecino a completar el formulario con relato detallado y datos de la vecina/o o frente del inmueble.
        """
        response = self.client.post(self.url_portal, {
            'nombre': 'Valeria Ramos',
            'dni': '35123456',
            'telefono': '3764556677',
            'detalle': 'quiero denunciar a mi vecina por ruidos molestos que escucha musica fuerte o que hacen ruido de cualquier indole',
        })
        self.assertEqual(response.status_code, 200)
        # Debe corresponder a la Guardia de Control Comunal Municipal, NO a Defensoría como organismo principal
        self.assertContains(response, 'Municipalidad de Posadas - Dirección de Control Comunal (Guardia de Ruidos Molestos)')
        self.assertContains(response, 'Ordenanza VI – Nº 14')
        self.assertContains(response, '3764-134650')
        self.assertContains(response, 'INSTRUCCIONES PARA COMPLETAR TU DENUNCIA EN EL FORMULARIO DE ABAJO')
        self.assertContains(response, '¿Te falta el nombre o la dirección exacta de la vecina/o?')
        self.assertContains(response, 'Registrar solicitud')

    def test_reclamo_ruidos_molestos_confirmacion_ticket(self):
        """
        Verifica que al confirmar y registrar la denuncia por ruidos molestos:
        - Se genera el ticket en estado PENDIENTE asignado a Control Comunal.
        - Se muestra la confirmación formal con el número de ticket, Ordenanza VI – Nº 14 y WhatsApp.
        """
        response = self.client.post(self.url_portal, {
            'nombre': 'Valeria Ramos',
            'dni': '35123456',
            'telefono': '3764556677',
            'detalle': 'Denuncia por música a todo volumen y ruidos molestos continuos en la casa vecina',
            'barrio': 'Itaembé Guazú',
            'entre_calles': 'Calle Las Magnolias y Aguará Guazú',
            'accion': 'registrar'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tu denuncia por ruidos molestos ha sido <strong>registrada formalmente</strong>')
        self.assertContains(response, 'Ordenanza VI – Nº 14')
        self.assertContains(response, '3764-134650')

        expediente = Expediente.objects.filter(dni_vecino=35123456).first()
        self.assertIsNotNone(expediente)
        self.assertEqual(expediente.estado_actual, 'PENDIENTE')
        self.assertEqual(expediente.organismo_destino, 'Municipalidad de Posadas - Dirección de Control Comunal (Guardia de Ruidos Molestos)')

    def test_consulta_tramite_ruidos_molestos_catalogo_oficial(self):
        """Verifica que una consulta informativa sobre ruidos molestos enlace al WhatsApp oficial y cite la Ordenanza VI – Nº 14."""
        from .asistente import procesar_consulta_vecino
        res = procesar_consulta_vecino('Carlos', '¿Cómo denunciar por ruidos molestos y música alta en Posadas?')
        self.assertEqual(res['tramite_info']['id'], 'denuncia_ruidos_molestos')
        self.assertIn('3764-134650', res['respuesta_texto'])
        self.assertIn('Ordenanza VI – Nº 14', res['respuesta_texto'])


from django.core.files.uploadedfile import SimpleUploadedFile

class TramitesCavItaembeGuazuTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('portal_vecino')

    def test_tramite_cav_carnet_sanitario_solicita_datos_y_documentos(self):
        """Asesora sobre carnet sanitario, solicita datos/fotos y permite iniciar trámite."""
        r1 = self.client.post(self.url, {
            'nombre': 'Martín Acosta',
            'dni': '36111444',
            'telefono': '3764112233',
            'detalle': 'Quiero tramitar el carnet sanitario en el CAV'
        })
        self.assertEqual(r1.status_code, 200)
        self.assertContains(r1, 'Carnet Sanitario')
        self.assertContains(r1, 'DATOS REQUERIDOS Y FALTANTES')
        self.assertContains(r1, 'DOCUMENTACIÓN Y FOTOGRAFÍAS A PRESENTAR / ADJUNTAR')
        self.assertContains(r1, 'Registrar solicitud / Iniciar trámite en CAV Itaembé Guazú')
        self.assertFalse(Expediente.objects.filter(dni_vecino=36111444).exists())

        # El ciudadano confirma el inicio del trámite:
        r2 = self.client.post(self.url, {
            'nombre': 'Martín Acosta',
            'dni': '36111444',
            'telefono': '3764112233',
            'detalle': 'Quiero tramitar el carnet sanitario en el CAV',
            'accion': 'registrar'
        })
        self.assertEqual(r2.status_code, 200)
        self.assertContains(r2, 'iniciada y registrada formalmente')
        self.assertContains(r2, 'PENDIENTE')
        exp = Expediente.objects.filter(dni_vecino=36111444).first()
        self.assertIsNotNone(exp)
        self.assertEqual(exp.estado_actual, 'PENDIENTE')
        self.assertIn('Delegación CAV Itaembé Guazú', exp.organismo_destino)

    def test_tramite_cav_registro_civil_dni_recien_nacido_y_pago_digital(self):
        """Verifica trámite DNI 0 Año, pedido de certificado médico y advertencia de pago digital (sin efectivo)."""
        r1 = self.client.post(self.url, {
            'nombre': 'Romina Benítez',
            'dni': '38222333',
            'telefono': '3764556677',
            'detalle': 'Quiero anotar el nacimiento de mi bebé y sacar el DNI 0 año en el CAV'
        })
        self.assertEqual(r1.status_code, 200)
        self.assertContains(r1, 'Certificado Médico de Nacido Vivo')
        self.assertContains(r1, 'NO SE ACEPTA EFECTIVO')
        self.assertContains(r1, 'Registro Provincial de las Personas')

        r2 = self.client.post(self.url, {
            'nombre': 'Romina Benítez',
            'dni': '38222333',
            'telefono': '3764556677',
            'detalle': 'Quiero anotar el nacimiento de mi bebé y sacar el DNI 0 año en el CAV',
            'accion': 'registrar'
        })
        self.assertEqual(r2.status_code, 200)
        exp = Expediente.objects.filter(dni_vecino=38222333).first()
        self.assertIsNotNone(exp)
        self.assertEqual(exp.estado_actual, 'PENDIENTE')
        self.assertIn('Registro Provincial de las Personas', exp.organismo_destino)

    def test_tramite_cav_emsa_alta_conexion_medidor(self):
        """Verifica asesoramiento y alta de servicio EMSA pidiendo certificado eléctrico y pilar reglamentario."""
        r1 = self.client.post(self.url, {
            'nombre': 'Mariano Silva',
            'dni': '32444555',
            'telefono': '3764889900',
            'detalle': 'Necesito pedir el alta del medidor de luz de EMSA en Itaembé Guazú'
        })
        self.assertEqual(r1.status_code, 200)
        self.assertContains(r1, 'Certificado de Aptitud de Instalación Eléctrica')
        self.assertContains(r1, 'pilar reglamentario')

        r2 = self.client.post(self.url, {
            'nombre': 'Mariano Silva',
            'dni': '32444555',
            'telefono': '3764889900',
            'detalle': 'Necesito pedir el alta del medidor de luz de EMSA en Itaembé Guazú',
            'accion': 'registrar'
        })
        self.assertEqual(r2.status_code, 200)
        exp = Expediente.objects.filter(dni_vecino=32444555).first()
        self.assertIsNotNone(exp)
        self.assertIn('Energía de Misiones S.A. (EMSA)', exp.organismo_destino)

    def test_tramite_cav_atm_clave_fiscal(self):
        """Verifica asesoramiento para Clave Fiscal ATM requiriendo DNI físico presencial y CUIT."""
        r1 = self.client.post(self.url, {
            'nombre': 'Valeria Giménez',
            'dni': '34555777',
            'telefono': '3764221100',
            'detalle': 'Quiero gestionar la clave fiscal de ATM en el CAV'
        })
        self.assertEqual(r1.status_code, 200)
        self.assertContains(r1, 'Clave Fiscal')
        self.assertContains(r1, 'DNI físico original')

        r2 = self.client.post(self.url, {
            'nombre': 'Valeria Giménez',
            'dni': '34555777',
            'telefono': '3764221100',
            'detalle': 'Quiero gestionar la clave fiscal de ATM en el CAV',
            'accion': 'registrar'
        })
        self.assertEqual(r2.status_code, 200)
        exp = Expediente.objects.filter(dni_vecino=34555777).first()
        self.assertIsNotNone(exp)
        self.assertIn('Agencia Tributaria Misiones (ATM)', exp.organismo_destino)

    def test_tramite_cav_iprodha_escrituracion(self):
        """Verifica asesoramiento notarial para escriturar vivienda IPRODHA."""
        r1 = self.client.post(self.url, {
            'nombre': 'Gonzalo Ortiz',
            'dni': '35666888',
            'telefono': '3764332211',
            'detalle': 'Quiero escriturar mi casa de IPRODHA en Itaembé Guazú'
        })
        self.assertEqual(r1.status_code, 200)
        self.assertContains(r1, 'Regularización Dominial')
        self.assertContains(r1, 'Acta de entrega de posesión')

        r2 = self.client.post(self.url, {
            'nombre': 'Gonzalo Ortiz',
            'dni': '35666888',
            'telefono': '3764332211',
            'detalle': 'Quiero escriturar mi casa de IPRODHA en Itaembé Guazú',
            'accion': 'registrar'
        })
        self.assertEqual(r2.status_code, 200)
        exp = Expediente.objects.filter(dni_vecino=35666888).first()
        self.assertIsNotNone(exp)
        self.assertIn('I.Pro.D.Ha.', exp.organismo_destino)

    def test_tramite_cav_mediacion_comunitaria_y_adjunto(self):
        """Verifica audiencia de conciliación voluntaria persistiendo archivo adjunto."""
        archivo_prueba = SimpleUploadedFile("foto_medianera.jpg", b"contenido_de_imagen_falsa", content_type="image/jpeg")
        r = self.client.post(self.url, {
            'nombre': 'Silvia Franco',
            'dni': '31999888',
            'telefono': '3764778899',
            'detalle': 'Quiero pedir una audiencia de mediación comunitaria en el CAV Itaembé Guazú por problemas de medianera con mi vecino',
            'accion': 'registrar',
            'archivo_adjunto': archivo_prueba
        })
        self.assertEqual(r.status_code, 200)
        exp = Expediente.objects.filter(dni_vecino=31999888).first()
        self.assertIsNotNone(exp)
        self.assertEqual(exp.estado_actual, 'PENDIENTE')
        self.assertIn('Mediación Comunitaria', exp.organismo_destino)
        self.assertTrue(bool(exp.archivo_adjunto))

    def test_tramite_cav_solo_necesitaba_informacion_no_crea_ticket(self):
        """Si el vecino presiona 'Solo necesitaba información', no se genera ticket y se audita en RegistroConsulta."""
        r = self.client.post(self.url, {
            'nombre': 'Lorena Ríos',
            'dni': '37444111',
            'telefono': '3764334455',
            'detalle': 'Quiero saber cómo renovar pasaporte en el CAV Itaembé Guazú',
            'accion': 'solo_info'
        })
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'solo necesitabas información')
        self.assertFalse(Expediente.objects.filter(dni_vecino=37444111).exists())
        self.assertTrue(RegistroConsulta.objects.filter(texto_consultado__contains='renovar pasaporte').exists())

    def test_consulta_pago_luz_emsa_online(self):
        """Verifica que consultas para pagar la luz brinden enlace directo a clientes.energiademisiones.com.ar y no obliguen a ir presencial."""
        r = self.client.post(self.url, {
            'nombre': 'Carlos Benítez',
            'dni': '31222333',
            'telefono': '3764112233',
            'detalle': 'quier pagar la luz de mi casa'
        })
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'clientes.energiademisiones.com.ar')
        self.assertContains(r, 'Energía de Misiones')
        # Verificar que no obligue ir presencialmente para abonar la boleta
        self.assertNotIn('Es un trámite 100% presencial', r.content.decode('utf-8'))
        # Verificar que el bloque de satisfacción esté integrado y visible
        self.assertContains(r, 'bloque-evaluacion-consulta')
        self.assertContains(r, '¿Pudiste resolver tu consulta?')

    def test_evaluacion_satisfaccion_mantiene_enlaces_y_registra_voto(self):
        """Verifica que al hacer click en Sí en ¿Pudiste resolver tu consulta? se registre el voto y se mantengan los enlaces y respuesta."""
        r1 = self.client.post(self.url, {
            'nombre': 'Valeria Giménez',
            'dni': '34555777',
            'telefono': '3764221100',
            'detalle': 'quier pagar la luz de mi casa'
        })
        self.assertEqual(r1.status_code, 200)
        reg = RegistroConsulta.objects.order_by('-id').first()
        self.assertIsNotNone(reg)

        # Simular click en 'Sí'
        r2 = self.client.post(self.url, {
            'btn_evaluar_consulta': '1',
            'id_consulta': reg.identificador_consulta,
            'evaluacion': 'SI'
        })
        self.assertEqual(r2.status_code, 200)
        reg.refresh_from_db()
        self.assertEqual(reg.evaluacion_vecino, 'SI')
        self.assertContains(r2, '¡Gracias! Registraste:')
        self.assertContains(r2, 'SI')
        self.assertContains(r2, 'clientes.energiademisiones.com.ar')

    def test_consulta_pago_agua_samsa_empresa_privada_no_cav(self):
        """Verifica que consultas para pagar el agua deriven a SAMSA, aclaren que es empresa privada no vinculada al CAV e incluyan enlaces oficiales."""
        r = self.client.post(self.url, {
            'nombre': 'Camila Denis',
            'dni': '36268087',
            'telefono': '3764187444',
            'detalle': 'quiero pagar el agua'
        })
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Servicios de Aguas de Misiones S.A. (SAMSA)')
        self.assertContains(r, 'empresa privada concesionaria')
        self.assertContains(r, 'NO está vinculada al CAV')
        self.assertContains(r, 'https://samsa.com.ar/paga-tu-factura/')
        self.assertContains(r, '0800-888-9980')
        self.assertNotIn('Es un trámite 100% presencial', r.content.decode('utf-8'))

    def test_emergencia_cable_chispas_detectada_no_crea_ticket_e_incrementa_estadistica_911(self):
        """Verifica que consultas de emergencia como cables con chispas deriven al 911, no generen ticket en Expediente y sumen al contador '911 Detectados' del Panel Gerencial."""
        # 1. Verificar estado inicial en panel gerencial
        r_panel_inicial = self.client.get(reverse('panel_gerencial'))
        self.assertEqual(r_panel_inicial.status_code, 200)
        self.assertContains(r_panel_inicial, '911 Detectados')
        emergencias_previas = r_panel_inicial.context['emergencias_detectadas']
        total_expedientes_previos = Expediente.objects.count()

        # 2. El vecino consulta por una emergencia crítica (cable con chispas)
        r_emergencia = self.client.post(self.url, {
            'nombre': 'Estela Benítez',
            'dni': '29888777',
            'telefono': '3764998877',
            'detalle': 'Hay un cable caído con chispas sobre la vereda frente a casa'
        })
        self.assertEqual(r_emergencia.status_code, 200)
        self.assertContains(r_emergencia, 'Línea 911')
        self.assertContains(r_emergencia, 'Energía de Misiones')

        # 3. Verificar que NO se haya creado un ticket/expediente operativo (no es reclamo convencional)
        self.assertEqual(Expediente.objects.count(), total_expedientes_previos)
        self.assertFalse(Expediente.objects.filter(dni_vecino=29888777).exists())

        # 4. Verificar que se haya registrado en auditoría como emergencia
        registro = RegistroConsulta.objects.filter(texto_consultado__contains='cable caído con chispas').first()
        self.assertIsNotNone(registro)
        self.assertEqual(registro.resultado, 'EMERGENCIA')
        self.assertEqual(registro.tipo_consulta, 'EMERGENCIA')
        self.assertIsNone(registro.ticket_asociado)

        # 5. Verificar que el Panel Gerencial ahora refleje el incremento en '911 Detectados'
        r_panel_despues = self.client.get(reverse('panel_gerencial'))
        self.assertEqual(r_panel_despues.status_code, 200)
        self.assertEqual(r_panel_despues.context['emergencias_detectadas'], emergencias_previas + 1)
        self.assertContains(r_panel_despues, 'Protocolo 911 activado (sin ticket)')

    def test_consulta_habilitar_negocio_con_errores_tipeo_deriva_a_obras_privadas_y_habilitaciones(self):
        """Verifica que consultas como 'quiero habilitar un nuegocio, que pasos debo hacer?' o 'quiero habilitar un nogio'
        orienten a Obras Privadas (Sistema GOP) y Habilitaciones Comerciales con enlaces directos y no caigan en CAV genérico."""
        for texto in [
            'quiero habilitar un nuegocio, que pasos debo hacer?',
            'quiero habilitar un nogio',
            'quiero habilitar un negocio',
        ]:
            r = self.client.post(self.url, {
                'nombre': 'Regina Caballero',
                'dni': '38123456',
                'telefono': '3764123456',
                'detalle': texto
            })
            self.assertEqual(r.status_code, 200)
            self.assertNotContains(r, 'Atención General al Vecino y Trámites Integrados CAV')
            self.assertContains(r, 'Obras Privadas')
            self.assertContains(r, 'Habilitaciones Comerciales')
            self.assertContains(r, 'https://posadas.gestiondeobrasprivadas.com.ar/')
            self.assertContains(r, 'https://posadas.gov.ar/planurbano/guia-de-tramites/')
            self.assertContains(r, 'https://posadas.gov.ar/guiatramite')

    def test_reclamo_foco_quemado_hace_una_semana_no_confunde_con_sem_e_incluye_detalles_emsa(self):
        """Verifica que 'hace una semana' no dispare SEM (Estacionamiento Medido) y que las consultas de
        foco quemado / poste quemado / luminarias / oscuro orienten directamente a EMSA sin pedir datos de la vecina ni formulario extra."""
        for texto in [
            'hay un foco que esta quemado afuera de mi casa hace una semana, cuando pueden venir a arreglar',
            'habia un foco o sea del poste de luz luminarias y queria que vengan a areglar porque esta oscuto',
            'afeura de mi cassa hay un poste quemado, hay mucha oscuridad y aprovechan los chorros',
        ]:
            r = self.client.post(self.url, {
                'nombre': 'Luciana Karajallo',
                'dni': '38123456',
                'telefono': '3764123456',
                'detalle': texto
            })
            self.assertEqual(r.status_code, 200)
            self.assertNotContains(r, 'Sistema de Estacionamiento Medido')
            self.assertNotContains(r, 'SEM Posadas')
            self.assertFalse(r.context['es_reclamo'])
            self.assertTrue(r.context['es_derivacion_externa'])
            self.assertContains(r, 'Energía de Misiones S.A. (EMSA)')
            self.assertContains(r, '0800-888-3672')
            self.assertContains(r, 'https://wa.me/5493764242514')
            self.assertContains(r, 'https://www.energiademisiones.com.ar/')
            self.assertNotContains(r, 'Datos de la vecina')
            self.assertNotContains(r, 'nombre de la vecina')
            self.assertNotContains(r, 'Resumen Automático de la Solicitud')






















