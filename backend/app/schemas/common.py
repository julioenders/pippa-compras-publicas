from enum import Enum

from pydantic import BaseModel


class Esfera(str, Enum):
    FEDERAL = "F"
    ESTADUAL = "E"
    MUNICIPAL = "M"


class SinalOportunidade(str, Enum):
    OPORTUNIDADE = "oportunidade"
    COMPETITIVO = "competitivo"
    CAUTELA = "cautela"
    SATURADO = "saturado"
    DESERTO = "deserto"


class FaixaValor(str, Enum):
    MICRO = "micro"        # até R$ 59.906
    PEQUENO = "pequeno"    # até R$ 80.000
    MEDIO = "medio"        # até R$ 480.000
    GRANDE = "grande"      # acima


class Perfil(str, Enum):
    GESTOR_PUBLICO = "gestor_publico"
    SEBRAE_NACIONAL = "sebrae_nacional"
    SEBRAE_UF = "sebrae_uf"
    MPE = "mpe"


class Momento(str, Enum):
    PCA = "pca"
    IRP = "irp"
    EDITAL = "edital"
    RESULTADO = "resultado"
    CONTRATO = "contrato"


class Urgencia(str, Enum):
    PLANEJADO = "planejado"
    NORMAL = "normal"
    URGENTE = "urgente"


class PaginacaoParams(BaseModel):
    pagina: int = 1
    tamanho: int = 50


class PaginacaoResponse(BaseModel):
    total_registros: int
    total_paginas: int
    pagina_atual: int
    paginas_restantes: int
