from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Alerta(Base):
    __tablename__ = "alertas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    perfil: Mapped[str] = mapped_column(nullable=False)
    tipo: Mapped[Optional[str]] = mapped_column(default=None)
    titulo: Mapped[str] = mapped_column(nullable=False)
    corpo: Mapped[Optional[str]] = mapped_column(Text, default=None)
    uf: Mapped[Optional[str]] = mapped_column(index=True, default=None)
    cnae_divisao: Mapped[Optional[str]] = mapped_column(default=None)
    contratacao_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("contratacoes.id"), default=None
    )
    cruzamento_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("cruzamentos.id"), default=None
    )
    lido: Mapped[Optional[bool]] = mapped_column(default=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())
