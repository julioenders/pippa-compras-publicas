from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Contrato(Base):
    __tablename__ = "contratos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contratacao_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("contratacoes.id"), index=True, default=None
    )
    fornecedor_cnpj: Mapped[str] = mapped_column(nullable=False, index=True)
    fornecedor_nome: Mapped[Optional[str]] = mapped_column(default=None)
    fornecedor_porte: Mapped[Optional[str]] = mapped_column(default=None)
    valor_contrato: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=2), default=None
    )
    data_assinatura: Mapped[Optional[date]] = mapped_column(Date, default=None)
    data_vigencia_inicio: Mapped[Optional[date]] = mapped_column(Date, default=None)
    data_vigencia_fim: Mapped[Optional[date]] = mapped_column(Date, default=None)
    status: Mapped[Optional[str]] = mapped_column(default=None)
    created_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())

    # Relationships
    contratacao: Mapped[Optional["Contratacao"]] = relationship(back_populates="contratos")
