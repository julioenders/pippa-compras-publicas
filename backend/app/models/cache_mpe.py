from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CacheMPE(Base):
    __tablename__ = "cache_mpes"

    __table_args__ = (
        UniqueConstraint(
            "uf", "municipio_ibge", "cnae_divisao", "cnae_subclasse",
            name="uq_cache_mpe_uf_mun_cnae",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uf: Mapped[str] = mapped_column(nullable=False, index=True)
    municipio_ibge: Mapped[Optional[str]] = mapped_column(index=True, default=None)
    cnae_divisao: Mapped[str] = mapped_column(nullable=False, index=True)
    cnae_subclasse: Mapped[Optional[str]] = mapped_column(default=None)
    qtd_mpes: Mapped[int] = mapped_column(nullable=False)
    periodo_referencia: Mapped[Optional[str]] = mapped_column(default=None)
    atualizado_em: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())
