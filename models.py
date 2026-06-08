from decimal import Decimal
from typing import List, Literal

from pydantic import BaseModel, Field


class CriterioSKU(BaseModel):
    codigo: int
    valor: Decimal


class CriterioTotal(BaseModel):
    codigo: int
    total: Decimal


class SKU(BaseModel):
    id_sku: int
    id_origem: int
    id_destino: int
    quantidade: Decimal
    criterios: List[CriterioSKU] = Field(default_factory=list)
    totais_criterios: List[CriterioTotal] = Field(
        default_factory=list, alias="totaisCriterios"
    )

    model_config = {"populate_by_name": True}


class CriterioCaminhao(BaseModel):
    codigo: int
    valor_minimo: Decimal = Field(alias="valorMinimo", max_digits=18, decimal_places=4)
    valor_maximo: Decimal = Field(alias="valorMaximo", max_digits=18, decimal_places=4)
    tipo_calculo: Literal["%", "Abs"] = Field(alias="tipoCalculo")

    model_config = {"populate_by_name": True}


class RegraCaminhao(BaseModel):
    id_origem: int
    id_destino: int
    criterios: List[CriterioCaminhao] = Field(default_factory=list)


class Caminhao(BaseModel):
    id_origem: int
    id_destino: int
    skus: List[SKU] = Field(default_factory=list)
    totais_criterios: List[CriterioTotal] = Field(
        default_factory=list, alias="totaisCriterios"
    )

    model_config = {"populate_by_name": True}


class OtimizarCargaRequest(BaseModel):
    skus: List[SKU]
    regra_caminhao: RegraCaminhao = Field(alias="regraCaminhao")

    model_config = {"populate_by_name": True}


class CaminhaoResumo(BaseModel):
    id_origem: int
    id_destino: int
    ids_sku_formatado: str
    qtd_total_skus: int
    regra_aprovada: bool

    # Permite campos dinâmicos como criterio1_valor_total, criterio1_percentual,
    # criterio2_valor_total, etc.
    model_config = {"extra": "allow"}


class OtimizarCargaResponse(BaseModel):
    caminhoes: List[CaminhaoResumo] = Field(default_factory=list)