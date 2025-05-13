from rest_framework import viewsets, status
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from .models import CalculoCredito, ParametroCalculo, TipoResiduo, Condominio
from django.db.models import Sum, F, FloatField, ExpressionWrapper
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import (
    TipoResiduoSerializer, 
    CalculoCreditoSerializer, 
    CondominioSerializer, 
    ParametroCalculoSerializer
)

class CalculoCreditoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = CalculoCredito.objects.all()
    serializer_class = CalculoCreditoSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Sobrescreve o método create para realizar o cálculo de crédito de carbono 
        antes de salvar o objeto
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            # Extrair dados validados
            condominio_id = serializer.validated_data.get('condominio').id
            tipo_residuo_id = serializer.validated_data.get('tipo_residuo').id
            peso_residuo = serializer.validated_data.get('peso_residuo')
            
            try:
                # Busca os parâmetros de cálculo para o tipo de resíduo
                parametro = ParametroCalculo.objects.get(tipo_residuo_id=tipo_residuo_id)
                
                # Cálculo de emissão de carbono
                emissao_carbono_atual = peso_residuo * parametro.fator_emissao_padrao
                emissao_carbono_reciclagem = emissao_carbono_atual - (emissao_carbono_atual * (1 - parametro.eficiencia_reciclagem/100))
                
                # Atualiza os valores calculados no serializer
                serializer.validated_data['emissao_carbono_atual'] = emissao_carbono_atual
                serializer.validated_data['emissao_carbono_reciclagem'] = emissao_carbono_reciclagem
                
                # Salva o objeto (o método save do model calculará economia_carbono)
                self.perform_create(serializer)
                
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
                
            except ParametroCalculo.DoesNotExist:
                return Response(
                    {'erro': 'Parâmetros de cálculo não encontrados para este tipo de resíduo.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {'erro': f'Erro no cálculo: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        Sobrescreve o método update para recalcular o crédito de carbono
        antes de atualizar o objeto
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            # Verifica se os campos relevantes para cálculo foram alterados
            recalcular = False
            
            if 'tipo_residuo' in serializer.validated_data or 'peso_residuo' in serializer.validated_data:
                recalcular = True
            
            if recalcular:
                # Obtém os valores atualizados ou usa os existentes se não foram alterados
                tipo_residuo_id = serializer.validated_data.get('tipo_residuo', instance.tipo_residuo).id
                peso_residuo = serializer.validated_data.get('peso_residuo', instance.peso_residuo)
                
                try:
                    # Busca os parâmetros de cálculo para o tipo de resíduo
                    parametro = ParametroCalculo.objects.get(tipo_residuo_id=tipo_residuo_id)
                    
                    # Cálculo de emissão de carbono
                    emissao_carbono_atual = peso_residuo * parametro.fator_emissao_padrao
                    emissao_carbono_reciclagem = emissao_carbono_atual - (emissao_carbono_atual * (1 - parametro.eficiencia_reciclagem/100))

                    
                    # Atualiza os valores calculados no serializer
                    serializer.validated_data['emissao_carbono_atual'] = emissao_carbono_atual
                    serializer.validated_data['emissao_carbono_reciclagem'] = emissao_carbono_reciclagem
                    
                except ParametroCalculo.DoesNotExist:
                    return Response(
                        {'erro': 'Parâmetros de cálculo não encontrados para este tipo de resíduo.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                except Exception as e:
                    return Response(
                        {'erro': f'Erro no cálculo: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            # Salva o objeto (o método save do model calculará economia_carbono)
            self.perform_update(serializer)
            
            if getattr(instance, '_prefetched_objects_cache', None):
                # Se a instância tiver objetos pré-carregados, limpe-os.
                instance._prefetched_objects_cache = {}
            
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class TipoResiduoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = TipoResiduo.objects.all()
    serializer_class = TipoResiduoSerializer

class CondominioViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Condominio.objects.all()
    serializer_class = CondominioSerializer

class ParametroCalculoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = ParametroCalculo.objects.all()
    serializer_class = ParametroCalculoSerializer

# Views adicionais para rotas personalizadas
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_condominios(request):
    # Lógica para gerar dados do dashboard
    return Response({"message": "Dados do dashboard"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def relatorio_economia(request):
    # Obter o condomínio do parâmetro de consulta
    condominio_id = request.query_params.get('condominio_id')
    
    if condominio_id:
        # Buscar o condomínio específico pelo ID
        condominio = get_object_or_404(Condominio, id=condominio_id)
    else:
        condominio = Condominio.objects.first()
        if not condominio:
            return Response({"error": "Nenhum condomínio encontrado no sistema"}, status=404)
        
        # Se o usuário não especificou um condomínio, pegue o primeiro disponível
        # Como seu modelo não tem relação direta com usuários, você pode:
        # 1. Pegar qualquer condomínio (não recomendado para produção)
        # 2. Verificar permissões por outra lógica
        # 3. Exigir que o condomínio_id seja fornecido
        
        # Opção 3: Exigir ID do condomínio
        
        # Alternativa (opção 1 - apenas para testes):
        # condominio = Condominio.objects.first()
        # if not condominio:
        #     return Response({"error": "Nenhum condomínio encontrado no sistema"}, status=404)
    
    # Período do relatório (opcional)
    data_inicio = request.query_params.get('data_inicio')
    data_fim = request.query_params.get('data_fim')
    
    # Filtrar resíduos por condomínio e período (se especificado)
    residuos_query = CalculoCredito.objects.filter(condominio=condominio)
    
    if data_inicio:
        residuos_query = residuos_query.filter(data_coleta__gte=data_inicio)
    if data_fim:
        residuos_query = residuos_query.filter(data_coleta__lte=data_fim)
    
    # Verificar se existem resíduos para este condomínio no período
    if not residuos_query.exists():
        return Response({
            "condominio": {
                "id": condominio.id,
                "nome": condominio.nome,
                "endereco": condominio.endereco
            },
            "message": "Não há dados de resíduos disponíveis para este condomínio no período especificado."
        })
    
    # O restante da função permanece igual...
    # Agrupar por tipo de resíduo e calcular as somas
    resumo_por_tipo = residuos_query.values('tipo_residuo__nome').annotate(
        peso_total=Sum('peso_residuo'),
        emissao_total=Sum('emissao_carbono_atual'),
        emissao_reciclagem_total=Sum('emissao_carbono_reciclagem'),
        economia_total=Sum('economia_carbono')
    ).order_by('tipo_residuo__nome')
    
    # Calcular o total geral
    total_geral = {
        'peso_total': residuos_query.aggregate(Sum('peso_residuo'))['peso_residuo__sum'] or 0,
        'emissao_total': residuos_query.aggregate(Sum('emissao_carbono_atual'))['emissao_carbono_atual__sum'] or 0,
        'emissao_reciclagem_total': residuos_query.aggregate(Sum('emissao_carbono_reciclagem'))['emissao_carbono_reciclagem__sum'] or 0,
        'economia_total': residuos_query.aggregate(Sum('economia_carbono'))['economia_carbono__sum'] or 0
    }
    
    # Verificar se gerou crédito de carbono (economia total negativa)
    credito_carbono = total_geral['economia_total'] < 0
    
    # Estimar valor de mercado do crédito, se aplicável (usando um valor médio de $60 por tonelada)
    valor_credito = abs(total_geral['economia_total'] / 1000) * 60 if credito_carbono else 0
    
    resultado = {
        'condominio': {
            'id': condominio.id,
            'nome': condominio.nome,
            'endereco': condominio.endereco
        },
        'periodo': {
            'data_inicio': data_inicio,
            'data_fim': data_fim
        },
        'resumo_por_tipo': list(resumo_por_tipo),
        'total_geral': total_geral,
        'status_ambiental': 'Crédito de Carbono' if credito_carbono else 'Redução de Emissões',
        'valor_estimado_credito_usd': round(valor_credito, 2) if credito_carbono else 0,
        'recomendacoes': gerar_recomendacoes(resumo_por_tipo, credito_carbono)
    }
    
    return Response(resultado)

def gerar_recomendacoes(resumo_por_tipo, credito_carbono):
    """Gera recomendações baseadas nos dados do relatório"""
    recomendacoes = []
    
    # Converter para lista para manipulação
    tipos_residuos = list(resumo_por_tipo)
    
    # Verificar se há tipos de resíduos com economia positiva (não geram crédito)
    residuos_sem_credito = [r for r in tipos_residuos if r['economia_total'] > 0]
    
    # Verificar se há poucos resíduos com alto potencial (alumínio, plástico)
    residuos_alto_potencial = [r for r in tipos_residuos 
                              if r['tipo_residuo__nome'] in ['Alumínio', 'Plástico', 'Metais Ferrosos']]
    
    # Gerar recomendações específicas
    if residuos_sem_credito:
        nomes = ", ".join([r['tipo_residuo__nome'] for r in residuos_sem_credito])
        recomendacoes.append(
            f"Melhorar os processos de tratamento de {nomes} para aumentar a eficiência."
        )
    
    if not credito_carbono:
        recomendacoes.append(
            "Aumentar a separação e reciclagem de materiais com alto potencial de crédito como alumínio e plástico."
        )
    
    if not residuos_alto_potencial:
        recomendacoes.append(
            "Implementar coleta seletiva específica para alumínio, plástico e metais ferrosos, que possuem alto potencial de geração de crédito de carbono."
        )
    
    # Recomendação geral
    if credito_carbono:
        recomendacoes.append(
            "Manter as práticas atuais e considerar expandir o programa de reciclagem para obter maior crédito de carbono."
        )
    
    return recomendacoes