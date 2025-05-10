from django.contrib import admin
from .models import TipoResiduo, CalculoCredito, Condominio, ParametroCalculo

@admin.register(TipoResiduo)
class TipoResiduoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'descricao']
    search_fields = ['nome']

@admin.register(Condominio)
class CondominioAdmin(admin.ModelAdmin):
    list_display = ['nome', 'endereco', 'numero_apartamentos']
    search_fields = ['nome', 'endereco']

@admin.register(ParametroCalculo)
class ParametroCalculoAdmin(admin.ModelAdmin):
    list_display = ['tipo_residuo', 'fator_emissao_padrao', 'eficiencia_reciclagem']
    list_select_related = ['tipo_residuo']

@admin.register(CalculoCredito)
class CalculoCreditoAdmin(admin.ModelAdmin):
    list_display = ['condominio', 'tipo_residuo', 'data_coleta', 'peso_residuo', 
                   'economia_carbono', 'custo_descarte_atual', 'custo_reciclagem']
    list_filter = ['condominio', 'tipo_residuo', 'data_coleta']
    search_fields = ['condominio__nome', 'tipo_residuo__nome']
    date_hierarchy = 'data_coleta'
    readonly_fields = ['economia_carbono']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('condominio', 'tipo_residuo', 'data_coleta', 'peso_residuo')
        }),
        ('Cálculos de Emissão', {
            'fields': ('emissao_carbono_atual', 'emissao_carbono_reciclagem', 'economia_carbono')
        }),
        ('Informações Financeiras', {
            'fields': ('custo_descarte_atual', 'custo_reciclagem'),
            'classes': ('collapse',),
        }),
    )