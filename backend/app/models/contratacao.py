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
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    orgao_cnpj: Mapped[str] = mapped_column(index=True)
    orgao_nome: Mapped[Optional[str]] = mapped_column(default=None)
    ano: Mapped[int] = mapped_column(nullable=False)
    sequencial: Mapped[int] = mapped_column(nullable=False)
    objeto: Mapped[Optional[str]] = mapped_column(Text, default=None)
    modalidade: Mapped[int] = mapped_column(nullable=False)
    modalidade_nome: Mapped[Optional[str]] = mapped_column(default=None)
    valor_estimado: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=2), default=None
    )
    esfera: Mapped[str] = mapped_column(nullable=False)
    uf: Mapped[Optional[str]] = mapped_column(index=True, default=None)
    municipio_ibge: Mapped[Optional[str]] = mapped_column(index=True, default=None)
    exclusiva_mpe: Mapped[Optional[bool]] = mapped_column(default=False)
    data_publicacao: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_abertura_proposta: Mapped[Optional[date]] = mapped_column(Date, default=None)
    data_encerramento_proposta: Mapped[Optional[date]] = mapped_column(Date, default=None)
    status: Mapped[Optional[str]] = mapped_column(default=None)
    raw_json: Mapped[Optional[dict]] = mapped_column(JSON, default=None)
    created_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now(), default=None)

    # Relationships
    items: Mapped[list["Item"]] = relationship(back_populates="contratacao")
    contratos: Mapped[list["Contrato"]] = relationship(back_populates="contratacao")
    cruzamentos: Mapped[list["Cruzamento"]] = relationship(back_populates="contratacao")
