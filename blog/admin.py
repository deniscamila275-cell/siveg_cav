from django.contrib import admin
from .models import Expediente, CategoriaReclamo, RegistroConsulta, SugerenciaOrganismo

@admin.register(SugerenciaOrganismo)
class SugerenciaOrganismoAdmin(admin.ModelAdmin):
    list_display = ('id', 'texto_sugerencia_resumen', 'nombre_vecino', 'contacto', 'estado', 'fecha_registro')
    list_filter = ('estado', 'fecha_registro')
    search_fields = ('texto_sugerencia', 'nombre_vecino', 'contacto')

    def texto_sugerencia_resumen(self, obj):
        return obj.texto_sugerencia[:60] + ('...' if len(obj.texto_sugerencia) > 60 else '')
    texto_sugerencia_resumen.short_description = 'Propuesta de Organismo'

@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = ('nro_expediente', 'nombre_completo', 'dni_vecino', 'tipo_solicitud', 'estado_actual', 'fecha_ingreso')
    list_filter = ('tipo_solicitud', 'estado_actual', 'fecha_ingreso')
    search_fields = ('nro_expediente', 'nombre_completo', 'dni_vecino', 'detalle_consulta')

@admin.register(RegistroConsulta)
class RegistroConsultaAdmin(admin.ModelAdmin):
    list_display = ('identificador_consulta', 'tipo_consulta', 'resultado', 'evaluacion_vecino', 'fecha_creacion')
    list_filter = ('tipo_consulta', 'resultado', 'evaluacion_vecino')
    search_fields = ('identificador_consulta', 'texto_consultado')

@admin.register(CategoriaReclamo)
class CategoriaReclamoAdmin(admin.ModelAdmin):
    list_display = ('cod_categoria', 'nombre_categoria', 'organismo_default')
