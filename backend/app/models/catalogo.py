from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CatalogoMaterial(Base):
    __tablename__ = "catalogo_materiais"

    codigo: Mapped[str] = mapped_column(primary_key=True)
    descricao: Mapped[Optional[str]] = mapped_column(Text, default=None)
    grupo: Mapped[Optional[str]] = mapped_column(default=None)
    classe: Mapped[Optional[str]] = mapped_column(default=None)
    cnae_mapeado: Mapped[Optional[str]] = mapped_column(default=None)
    atualizado_em: Mapped[Optional[datetime]] = mapped_column(default=None)


class CatalogoServico(Base):
    __tablename__ = "catalogo_servicos"

    codigo: Mapped[str] = mapped_column(primary_key=True)
    descricao: Mapped[Optional[str]] = mapped_column(Text, default=None)
    grupo: Mapped[Optional[str]] = mapped_column(default=None)
    classe: Mapped[Optional[str]] = mapped_column(default=None)
    cnae_mapeado: Mapped[Optional[str]] = mapped_column(default=None)
    atualizado_em: Mapped[Optional[datetime]] = mapped_column(default=None)
