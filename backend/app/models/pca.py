from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PCAItem(Base):
    __tablename__ = "pca_itens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    orgao_cnpj: Mapped[str] = mapped_column(nullable=False, index=True)
    ano: Mapped[int] = mapped_column(nullable=False)
    catmat_catser: Mapped[Optional[str]] = mapped_column(default=None)
    descricao: Mapped[Optional[str]] = mapped_column(Text, default=None)
    valor_estimado: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=2), default=None
    )
    quantidade: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=4), default=None
    )
    unidade: Mapped[Optional[str]] = mapped_column(default=None)
    data_prevista: Mapped[Optional[date]] = mapped_column(Date, default=None)
    status: Mapped[Optional[str]] = mapped_column(default=None)
    created_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())
