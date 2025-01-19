from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .cia import Cia
    from .voo import Voo

class AeronaveBase(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    modelo: str
    capacidade: int
    last_check: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  # Corrigido para usar datetime.now
    next_check: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  # Corrigido para usar datetime.now

class Aeronave(AeronaveBase, table=True):
    cia_id: int = Field(foreign_key="cia.id")
    cia: "Cia" = Relationship(back_populates="aeronaves")  # Relacionamento com Cia
    voos: List["Voo"] = Relationship(back_populates="aeronave")  # Relacionamento com Voo
