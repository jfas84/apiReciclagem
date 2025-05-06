from django.db import transaction
from django.shortcuts import render, redirect
from .models import CalculoCredito, ParametroCalculo, TipoResiduo, Condominio

class CalculoCreditoView:
    @transaction.atomic
    def calcular_credito_carbono(self, request):
        """
        Método para calcular crédito de carbono baseado nos parâmetros armazenados
        """
        if request.method == 'POST':
            # Dados do formulário
            condominio_id = request.POST.get('condominio')
            tipo_residuo_id = request.POST.get('tipo_residuo')
            peso_residuo = float(request.POST.get('peso_residuo'))
            
            try:
                # Busca os parâmetros de cálculo para o tipo de resíduo
                parametro = ParametroCalculo.objects.get(tipo_residuo_id=tipo_residuo_id)
                
                # Cálculo de emissão de carbono
                # Emissão atual: peso * fator de emissão padrão
                emissao_carbono_atual = peso_residuo * parametro.fator_emissao_padrao
                
                # Emissão na reciclagem: considera a eficiência de redução
                emissao_carbono_reciclagem = emissao_carbono_atual * (1 - parametro.eficiencia_reciclagem/100)
                
                # Cria o registro de cálculo de crédito
                calculo_credito = CalculoCredito.objects.create(
                    condominio_id=condominio_id,
                    tipo_residuo_id=tipo_residuo_id,
                    peso_residuo=peso_residuo,
                    emissao_carbono_atual=emissao_carbono_atual,
                    emissao_carbono_reciclagem=emissao_carbono_reciclagem
                )
                
                return render(request, 'resultado_calculo.html', {
                    'calculo': calculo_credito,
                    'economia_carbono': calculo_credito.economia_carbono
                })
            
            except ParametroCalculo.DoesNotExist:
                # Trata caso não existam parâmetros para o tipo de resíduo
                return render(request, 'erro.html', {
                    'mensagem': 'Parâmetros de cálculo não encontrados para este tipo de resíduo.'
                })
            except Exception as e:
                # Trata outros erros de cálculo
                return render(request, 'erro.html', {
                    'mensagem': f'Erro no cálculo: {str(e)}'
                })

# Exemplo de como popular os parâmetros iniciais
def popular_parametros_calculo():
    """
    Função para popular o banco de dados com parâmetros iniciais de cálculo
    """
    # Tipos de resíduo
    tipos = [
        ('Papel', 'Resíduos de papel e papelão'),
        ('Plástico', 'Resíduos plásticos'),
        ('Vidro', 'Resíduos de vidro'),
        ('Orgânico', 'Resíduos orgânicos')
    ]
    
    for nome, descricao in tipos:
        # Cria o tipo de resíduo se não existir
        tipo_residuo, created = TipoResiduo.objects.get_or_create(
            nome=nome, 
            defaults={'descricao': descricao}
        )
        
        # Cria ou atualiza os parâmetros de cálculo
        ParametroCalculo.objects.update_or_create(
            tipo_residuo=tipo_residuo,
            defaults={
                'fator_emissao_padrao': {
                    'Papel': 0.5,      # kg CO2 por kg de papel
                    'Plástico': 1.5,   # kg CO2 por kg de plástico
                    'Vidro': 0.3,      # kg CO2 por kg de vidro
                    'Orgânico': 0.7    # kg CO2 por kg de orgânico
                }[nome],
                'eficiencia_reciclagem': {
                    'Papel': 70,       # 70% de redução na emissão
                    'Plástico': 60,    # 60% de redução na emissão
                    'Vidro': 75,       # 75% de redução na emissão
                    'Orgânico': 50     # 50% de redução na emissão
                }[nome]
            }
        )