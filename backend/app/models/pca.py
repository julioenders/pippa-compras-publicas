from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Index, Numeric, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PCAItem(Base):
    """Item do Plano de Contratacoes Anual (PCA).

    Representa demanda planejada — sinal antecipado de oportunidade futura.
    Prioridade Alta na matriz: permite antecipar mercados e compras
    que ainda serao licitadas.
    """

    __tablename__ = "pca_itens"

    __table_args__ = (
        UniqueConstraint("orgao_cnpj", "ano", "sequencial_pca", name="uq_pca_orgao_ano_seq"),
        Index("ix_pca_uf", "uf"),
        Index("ix_pca_data_prevista", "data_prevista"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # --- Orgao ---
    orgao_cnpj: Mapped[str] = mapped_column(nullable=False, index=True)
    orgao_nome: Mapped[Optional[str]] = mapped_column(default=None)
    unidade_requisitante: Mapped[Optional[str]] = mapped_column(default=None)

    # --- Identificacao PCA ---
    ano: Mapped[int] = mapped_column(nullable=False)
    sequencial_pca: Mapped[Optional[int]] = mapped_column(default=None)

    # --- Item planejado ---
    catmat_catser: Mapped[Optional[str]] = mapped_column(index=True, default=None)
    categoria: Mapped[Optional[str]] = mapped_column(default=None)
    descricao: Mapped[Optional[str]] = mapped_column(Text, default=None)

    # --- Valores e quantidades ---
    valor_unitario: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=2), default=None
    )
    valor_total: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=2), default=None
    )
    valor_exercicio: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=2), default=None
    )
    quantidade: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=4), default=None
    )
    unidade: Mapped[Optional[str]] = mapped_column(default=None)

    # --- Localizacao ---
    uf: Mapped[Optional[str]] = mapped_column(default=None)
    municipio_ibge: Mapped[Optional[str]] = mapped_column(default=None)

    # --- Planejamento ---
    data_prevista: Mapped[Optional[date]] = mapped_column(Date, default=None)
    status: Mapped[Optional[str]] = mapped_column(default=None)

    # --- Mapeamento ---
    cnae_mapeado: Mapped[Optional[str]] = mapped_column(default=None)

    created_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())
