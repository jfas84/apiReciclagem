from rest_framework import viewsets, status
from django.db import transaction
from django.shortcuts import render, redirect
from .models import CalculoCredito, ParametroCalculo, TipoResiduo, Condominio
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
    # Lógica para gerar relatório de economia
    return Response({"message": "Relatório de economia"})
