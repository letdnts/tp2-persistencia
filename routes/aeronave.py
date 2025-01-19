from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from models.aeronave import Aeronave
from database import get_session

router = APIRouter(
    prefix="/aeronaves",  # Prefixo para todas as rotas
    tags=["Aeronaves"],  # Tag para documentação automática
)

# Create
@router.post("/", response_model=Aeronave)
def create_aeronave(aeronave: Aeronave, session: Session = Depends(get_session)):
    # Converta as strings de data para datetime
    if isinstance(aeronave.last_check, str):
        aeronave.last_check = datetime.fromisoformat(aeronave.last_check.rstrip("Z"))
    if isinstance(aeronave.next_check, str):
        aeronave.next_check = datetime.fromisoformat(aeronave.next_check.rstrip("Z"))
    
    session.add(aeronave)  # Adiciona a instância da aeronave
    session.commit()
    session.refresh(aeronave)  # Atualiza a instância com os dados do banco
    return aeronave

# Read
@router.get("/", response_model=list[Aeronave])
def read_aeronave(
    offset: int = 0,
    limit: int = Query(default=10 , le=100),  
    session: Session = Depends(get_session)):
    
    return session.exec(select(Aeronave).offset(offset).limit(limit)).all()

# Consulta por ID
@router.get("/{aeronave_id}", response_model=Aeronave)
def get_aeronave_by_id(aeronave_id: int, session: Session = Depends(get_session)):
    # Query para buscar o voo pelo ID
    aeronave = session.get(Aeronave, aeronave_id)
    if not aeronave:
        # Retorna um erro 404 se o voo não for encontrado
        raise HTTPException(status_code=404, detail="Cia não encontrada")
    return aeronave