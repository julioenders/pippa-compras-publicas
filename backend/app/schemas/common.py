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
    PRE_QUALIFICACAO = "pre_qualificacao"
    EDITAL = "edital"
    RESULTADO = "resultado"
    CONTRATO = "contrato"


class Urgencia(str, Enum):
    PLANEJADO = "planejado"
    NORMAL = "normal"
    URGENTE = "urgente"


class SituacaoContratacao(str, Enum):
    FUTURA = "futura"
    ABERTA = "aberta"
    EM_JULGAMENTO = "em_julgamento"
    SUSPENSA = "suspensa"
    REVOGADA = "revogada"
    ANULADA = "anulada"
    ENCERRADA = "encerrada"
    DESERTA = "deserta"
    FRACASSADA = "fracassada"


class BeneficioMPE(str, Enum):
    EXCLUSIVA = "exclusiva"
    COTA_RESERVADA = "cota_reservada"
    SUBCONTRATACAO = "subcontratacao"
    SEM_BENEFICIO = "sem_beneficio"


class TipoInstrumento(str, Enum):
    AVISO_LICITACAO = "aviso_licitacao"
    PREGAO_ELETRONICO = "pregao_eletronico"
    CONCORRENCIA = "concorrencia"
    CONCURSO = "concurso"
    DIALOGO_COMPETITIVO = "dialogo_competitivo"
    DISPENSA_ELETRONICA = "dispensa_eletronica"
    DISPENSA_RATIFICACAO = "dispensa_ratificacao"
    INEXIGIBILIDADE = "inexigibilidade"
    LICITACAO_SRP = "licitacao_srp"
    CREDENCIAMENTO = "credenciamento"
    CHAMAMENTO_PUBLICO = "chamamento_publico"
    PRE_QUALIFICACAO = "pre_qualificacao"
    ATA_REGISTRO_PRECOS = "ata_registro_precos"
    CONTRATO = "contrato"
    ADITIVO = "aditivo"


class CriterioJulgamento(str, Enum):
    MENOR_PRECO = "menor_preco"
    MAIOR_DESCONTO = "maior_desconto"
    MELHOR_TECNICA = "melhor_tecnica"
    TECNICA_PRECO = "tecnica_e_preco"
    MAIOR_LANCE = "maior_lance"
    MAIOR_RETORNO = "maior_retorno"
    NAO_SE_APLICA = "nao_se_aplica"


class ModoDisputa(str, Enum):
    ABERTO = "aberto"
    FECHADO = "fechado"
    ABERTO_FECHADO = "aberto_fechado"
    FECHADO_ABERTO = "fechado_aberto"
    NAO_SE_APLICA = "nao_se_aplica"


class TipoEvento(str, Enum):
    PUBLICACAO = "publicacao"
    RETIFICACAO = "retificacao"
    REABERTURA = "reabertura"
    ADIAMENTO = "adiamento"
    SUSPENSAO = "suspensao"
    REVOGACAO = "revogacao"
    ANULACAO = "anulacao"
    RESULTADO = "resultado"
    ADJUDICACAO = "adjudicacao"
    HOMOLOGACAO = "homologacao"


class FonteDados(str, Enum):
    PNCP = "pncp"
    DOU_SECAO3 = "dou_secao3"
    QUERIDO_DIARIO = "querido_diario"
    DADOS_ABERTOS = "dados_abertos"


class PaginacaoParams(BaseModel):
    pagina: int = 1
    tamanho: int = 50


class PaginacaoResponse(BaseModel):
    total_registros: int
    total_paginas: int
    pagina_atual: int
    paginas_restantes: int
