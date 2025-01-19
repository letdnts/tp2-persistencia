from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .cia import Cia
    from .aeronave import Aeronave

class VooBase(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    numero_voo: int
    origem: str
    destino: str
    hr_partida: datetime
    hr_chegada: datetime
    status: str

class Voo(VooBase, table=True):
    aeronave_id: int = Field(foreign_key="aeronave.id")
    aeronave: "Aeronave" = Relationship(back_populates="voos")
    cia_id: int = Field(foreign_key="cia.id")
    cia: "Cia" = Relationship(back_populates="voos")  # Relacionamento com Cia
