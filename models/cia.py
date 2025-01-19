from sqlmodel import SQLModel, Field, Relationship
from typing import List
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .aeronave import Aeronave
    from .voo import Voo

class CiaBase(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    nome: str
    cod_iata: str

class Cia(CiaBase, table=True):
    # Relacionamento com aeronaves
    aeronaves: List["Aeronave"] = Relationship(back_populates="cia")
    # Relacionamento com voos
    voos: List["Voo"] = Relationship(back_populates="cia")  # Relacionamento com voos
