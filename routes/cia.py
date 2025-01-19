from sqlalchemy.orm import joinedload  # Import necessário para o joinedload
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from models.cia import Cia  # Importe o modelo Voo
from database import get_session

router = APIRouter(
    prefix="/cias",  # Prefixo para todas as rotas
    tags=["Cias"],  # Tag para documentação automática
)
# Create
@router.post("/", response_model=Cia)
def create_cia(cia: Cia, session: Session = Depends(get_session)):
    session.add(cia)  # Adiciona a instância do voo
    session.commit()
    session.refresh(cia)  # Atualiza a instância com os dados do banco
    return cia

# Read
@router.get("/", response_model=list[Cia])
def read_cia(
    offset: int = 0,
    limit: int = Query(default=10 , le=100),  
    session: Session = Depends(get_session)):
    
    return session.exec(select(Cia).offset(offset).limit(limit)).all()

# Consulta por ID
@router.get("/{cia_id}", response_model=Cia)
def get_cia_by_id(cia_id: int, session: Session = Depends(get_session)):
    # Query para buscar o voo pelo ID
    cia = session.get(Cia, cia_id)
    if not cia:
        # Retorna um erro 404 se o voo não for encontrado
        raise HTTPException(status_code=404, detail="Cia não encontrada")
    return cia