from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EventoContratacao(Base):
    """Rastreia eventos do ciclo de vida de uma contratacao.

    Cada mudanca de status (retificacao, suspensao, revogacao, reabertura,
    resultado, adjudicacao, homologacao) gera um registro de evento para
    manter o historico completo e permitir atualizar a situacao da
    contratacao no radar de oportunidades.
    """

    __tablename__ = "eventos_contratacao"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contratacao_id: Mapped[int] = mapped_column(
        ForeignKey("contratacoes.id"), nullable=False, index=True
    )

    tipo: Mapped[str] = mapped_column(nullable=False)
    data_evento: Mapped[Optional[datetime]] = mapped_column(default=None)

    descricao: Mapped[Optional[str]] = mapped_column(Text, default=None)
    campo_alterado: Mapped[Optional[str]] = mapped_column(default=None)
    valor_anterior: Mapped[Optional[str]] = mapped_column(Text, default=None)
    valor_novo: Mapped[Optional[str]] = mapped_column(Text, default=None)

    fonte: Mapped[Optional[str]] = mapped_column(default=None)
    detalhes: Mapped[Optional[dict]] = mapped_column(JSON, default=None)

    created_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())

    contratacao: Mapped["Contratacao"] = relationship(back_populates="eventos")
