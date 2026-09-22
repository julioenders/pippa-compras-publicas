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

    # --- Catalogo (Alta na matriz) ---
    catmat_catser: Mapped[Optional[str]] = mapped_column(index=True, default=None)
    tipo_catalogo: Mapped[Optional[str]] = mapped_column(default=None)

    # --- Descricao (Altissima na matriz) ---
    descricao: Mapped[Optional[str]] = mapped_column(Text, default=None)
    material_ou_servico: Mapped[Optional[str]] = mapped_column(default=None)

    # --- Quantidades e valores (Altissima na matriz) ---
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

    # --- NCM/NBS (Alta na matriz) ---
    ncm: Mapped[Optional[str]] = mapped_column(default=None)
    nbs: Mapped[Optional[str]] = mapped_column(default=None)

    # --- Beneficio MPE por item (Altissima na matriz) ---
    beneficio_mpe: Mapped[Optional[str]] = mapped_column(default=None)
    cota_reservada: Mapped[Optional[bool]] = mapped_column(default=False)

    # --- Mapeamento economico ---
    cnae_mapeado: Mapped[Optional[str]] = mapped_column(default=None)

    # --- Resultado por item (Analitica na matriz) ---
    valor_unitario_adjudicado: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=15, scale=2), default=None
    )
    beneficio_mpe_aplicado: Mapped[Optional[bool]] = mapped_column(default=None)

    # --- Relationships ---
    contratacao: Mapped["Contratacao"] = relationship(back_populates="items")
