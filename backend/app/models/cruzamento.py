from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, JSON, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Cruzamento(Base):
    __tablename__ = "cruzamentos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contratacao_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("contratacoes.id"), index=True, default=None
    )
    cnae_divisao: Mapped[Optional[str]] = mapped_column(index=True, default=None)
    cnae_descricao: Mapped[Optional[str]] = mapped_column(default=None)
    uf: Mapped[Optional[str]] = mapped_column(index=True, default=None)
    municipio_ibge: Mapped[Optional[str]] = mapped_column(default=None)
    qtd_mpes_regiao: Mapped[Optional[int]] = mapped_column(default=None)
    sinal: Mapped[str] = mapped_column(nullable=False)
    score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=5, scale=2), default=None
    )
    detalhes: Mapped[Optional[dict]] = mapped_column(JSON, default=None)
    created_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())

    # Relationships
    contratacao: Mapped[Optional["Contratacao"]] = relationship(back_populates="cruzamentos")
