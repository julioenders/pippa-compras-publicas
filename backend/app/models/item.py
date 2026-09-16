from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Item(Base):
    __tablename__ = "itens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contratacao_id: Mapped[int] = mapped_column(
        ForeignKey("contratacoes.id"), nullable=False, index=True
    )
    numero_item: Mapped[Optional[int]] = mapped_column(default=None)
    catmat_catser: Mapped[Optional[str]] = mapped_column(index=True, default=None)
    descricao: Mapped[Optional[str]] = mapped_column(Text, default=None)
    unidade: Mapped[Optional[str]] = mapped_column(default=None)
    quantidade: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=4), default=None
    )
    valor_unitario_estimado: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=2), default=None
    )
    valor_total_estimado: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=2), default=None
    )
    cnae_mapeado: Mapped[Optional[str]] = mapped_column(default=None)

    # Relationships
    contratacao: Mapped["Contratacao"] = relationship(back_populates="items")
