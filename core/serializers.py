from rest_framework import serializers
from .models import TipoResiduo, CalculoCredito, Condominio, ParametroCalculo

class TipoResiduoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoResiduo
        fields = '__all__'

class CalculoCreditoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalculoCredito
        fields = '__all__'

class CondominioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Condominio
        fields = '__all__'

class ParametroCalculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParametroCalculo
        fields = '__all__'

class CalculoCreditoSerializer(serializers.ModelSerializer):
    tipo_residuo_nome = serializers.ReadOnlyField(source='tipo_residuo.nome')
    condominio_nome = serializers.ReadOnlyField(source='condominio.nome')
    
    class Meta:
        model = CalculoCredito
        fields = [
            'id', 
            'condominio', 
            'condominio_nome',
            'tipo_residuo', 
            'tipo_residuo_nome',
            'peso_residuo',
            'data_coleta',
            'emissao_carbono_atual',
            'emissao_carbono_reciclagem',
            'economia_carbono',
            'custo_descarte_atual',
            'custo_reciclagem'
        ]
        read_only_fields = ['economia_carbono', 'emissao_carbono_atual', 'emissao_carbono_reciclagem']  # Calculado automaticamente no model e na view


