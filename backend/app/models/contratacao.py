from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Index, JSON, Numeric, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Contratacao(Base):
    __tablename__ = "contratacoes"

    __table_args__ = (
        UniqueConstraint("orgao_cnpj", "ano", "sequencial", name="uq_contratacao_orgao_ano_seq"),
        Index("ix_contratacoes_situacao", "situacao"),
        Index("ix_contratacoes_srp", "srp"),
        Index("ix_contratacoes_tipo_instrumento", "tipo_instrumento"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # --- Identificacao do orgao ---
    orgao_cnpj: Mapped[str] = mapped_column(index=True)
    orgao_nome: Mapped[Optional[str]] = mapped_column(default=None)
    unidade_codigo: Mapped[Optional[str]] = mapped_column(default=None)
    unidade_nome: Mapped[Optional[str]] = mapped_column(default=None)

    # --- Identificacao da contratacao ---
    ano: Mapped[int] = mapped_column(nullable=False)
    sequencial: Mapped[int] = mapped_column(nullable=False)
    numero_processo: Mapped[Optional[str]] = mapped_column(default=None)
    numero_contratacao: Mapped[Optional[str]] = mapped_column(default=None)

    # --- Objeto (Altissima na matriz) ---
    objeto: Mapped[Optional[str]] = mapped_column(Text, default=None)
    informacao_complementar: Mapped[Optional[str]] = mapped_column(Text, default=None)

    # --- Modalidade e instrumento ---
    modalidade: Mapped[int] = mapped_column(nullable=False)
    modalidade_nome: Mapped[Optional[str]] = mapped_column(default=None)
    tipo_instrumento: Mapped[Optional[str]] = mapped_column(default=None)
    amparo_legal: Mapped[Optional[str]] = mapped_column(default=None)

    # --- Valores (Altissima na matriz) ---
    valor_estimado: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=2), default=None
    )
    orcamento_sigiloso: Mapped[Optional[bool]] = mapped_column(default=False)

    # --- Localizacao (Altissima na matriz) ---
    esfera: Mapped[str] = mapped_column(nullable=False)
    poder: Mapped[Optional[str]] = mapped_column(default=None)
    uf: Mapped[Optional[str]] = mapped_column(index=True, default=None)
    municipio_ibge: Mapped[Optional[str]] = mapped_column(index=True, default=None)
    municipio_nome: Mapped[Optional[str]] = mapped_column(default=None)

    # --- Beneficio MPE (Altissima na matriz) ---
    beneficio_mpe: Mapped[Optional[str]] = mapped_column(default=None)
    exclusiva_mpe: Mapped[Optional[bool]] = mapped_column(default=False)
    cota_reservada: Mapped[Optional[bool]] = mapped_column(default=False)
    subcontratacao_mpe: Mapped[Optional[bool]] = mapped_column(default=False)

    # --- SRP - Sistema de Registro de Precos (Altissima na matriz) ---
    srp: Mapped[Optional[bool]] = mapped_column(default=False)

    # --- Datas do ciclo de vida (Altissima na matriz) ---
    data_publicacao: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_abertura_proposta: Mapped[Optional[date]] = mapped_column(Date, default=None)
    data_encerramento_proposta: Mapped[Optional[date]] = mapped_column(Date, default=None)

    # --- Disputa (Alta na matriz) ---
    criterio_julgamento: Mapped[Optional[str]] = mapped_column(default=None)
    modo_disputa: Mapped[Optional[str]] = mapped_column(default=None)

    # --- Link de participacao (Altissima na matriz) ---
    link_sistema_origem: Mapped[Optional[str]] = mapped_column(Text, default=None)
    link_edital: Mapped[Optional[str]] = mapped_column(Text, default=None)

    # --- Situacao / Ciclo de vida (Alta na matriz) ---
    situacao: Mapped[Optional[str]] = mapped_column(default=None)
    situacao_descricao: Mapped[Optional[str]] = mapped_column(default=None)
    data_ultima_atualizacao: Mapped[Optional[date]] = mapped_column(Date, default=None)

    # --- Margem de preferencia (Alta na matriz) ---
    margem_preferencia: Mapped[Optional[bool]] = mapped_column(default=False)
    margem_preferencia_percentual: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=5, scale=2), default=None
    )
    exigencia_conteudo_nacional: Mapped[Optional[bool]] = mapped_column(default=False)

    # --- Fonte dos dados ---
    fonte: Mapped[Optional[str]] = mapped_column(default="dou_secao3")

    # --- Resultado (Analitica na matriz) ---
    fornecedor_vencedor_cnpj: Mapped[Optional[str]] = mapped_column(default=None)
    fornecedor_vencedor_nome: Mapped[Optional[str]] = mapped_column(default=None)
    fornecedor_vencedor_porte: Mapped[Optional[str]] = mapped_column(default=None)
    valor_adjudicado: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=2), default=None
    )

    # --- Controle ---
    raw_json: Mapped[Optional[dict]] = mapped_column(JSON, default=None)
    created_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now(), default=None)

    # --- Relationships ---
    items: Mapped[list["Item"]] = relationship(back_populates="contratacao", cascade="all, delete-orphan")
    contratos: Mapped[list["Contrato"]] = relationship(back_populates="contratacao")
    cruzamentos: Mapped[list["Cruzamento"]] = relationship(back_populates="contratacao")
    eventos: Mapped[list["EventoContratacao"]] = relationship(back_populates="contratacao", cascade="all, delete-orphan")
