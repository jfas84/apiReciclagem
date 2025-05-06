from django.db import models
from django.core.validators import MinValueValidator

class TipoResiduo(models.Model):
    """
    Categorias de resíduos para classificação e cálculo de crédito de carbono
    """
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nome

class CalculoCredito(models.Model):
    """
    Modelo para registrar os cálculos de crédito de carbono por tipo de resíduo
    """
    condominio = models.ForeignKey('Condominio', on_delete=models.CASCADE)
    tipo_residuo = models.ForeignKey(TipoResiduo, on_delete=models.CASCADE)
    
    # Dados de entrada (peso/volume dos resíduos)
    peso_residuo = models.FloatField(
        validators=[MinValueValidator(0)],
        help_text="Peso do resíduo em kg"
    )
    data_coleta = models.DateTimeField(auto_now_add=True)
    
    # Dados de cálculo de crédito de carbono
    emissao_carbono_atual = models.FloatField(
        validators=[MinValueValidator(0)],
        help_text="Emissão de carbono do método atual de descarte (kg CO2)"
    )
    emissao_carbono_reciclagem = models.FloatField(
        validators=[MinValueValidator(0)],
        help_text="Emissão de carbono se reciclado (kg CO2)"
    )
    economia_carbono = models.FloatField(
        validators=[MinValueValidator(0)],
        help_text="Economia de carbono pela reciclagem (kg CO2)"
    )
    custo_descarte_atual = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Custo atual de descarte (R$)"
    )
    custo_reciclagem = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Custo potencial de reciclagem (R$)"
    )
    
    class Meta:
        verbose_name = 'Cálculo de Crédito de Carbono'
        verbose_name_plural = 'Cálculos de Crédito de Carbono'
        unique_together = ['condominio', 'tipo_residuo', 'data_coleta']
    
    def __str__(self):
        return f"{self.condominio} - {self.tipo_residuo} ({self.data_coleta.date()})"
    
    def save(self, *args, **kwargs):
        """
        Calcula automaticamente a economia de carbono ao salvar
        """
        self.economia_carbono = self.emissao_carbono_atual - self.emissao_carbono_reciclagem
        super().save(*args, **kwargs)

class Condominio(models.Model):
    """
    Modelo para representar o condomínio
    """
    nome = models.CharField(max_length=200)
    endereco = models.TextField()
    numero_apartamentos = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Número total de apartamentos no condomínio"
    )
    
    def __str__(self):
        return self.nome

class ParametroCalculo(models.Model):
    """
    Modelo para armazenar parâmetros padrão de cálculo de crédito de carbono
    """
    tipo_residuo = models.OneToOneField(
        TipoResiduo, 
        on_delete=models.CASCADE,
        primary_key=True
    )
    fator_emissao_padrao = models.FloatField(
        validators=[MinValueValidator(0)],
        help_text="Fator de emissão padrão para este tipo de resíduo (kg CO2/kg)"
    )
    eficiencia_reciclagem = models.FloatField(
        validators=[MinValueValidator(0)],
        max_length=100,
        help_text="Porcentagem de redução de emissão pela reciclagem"
    )
    
    def __str__(self):
        return f"Parâmetros para {self.tipo_residuo}"