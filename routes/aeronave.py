from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import joinedload  # Import necessário para o joinedload
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from models.aeronave import Aeronave
from models.cia import Cia
from database import get_session
from models.voo import Voo

router = APIRouter(
    prefix="/aeronaves",  # Prefixo para todas as rotas
    tags=["Aeronaves"],  # Tag para documentação automática
)

# Create
@router.post("/", response_model=Aeronave)
def create_aeronave(aeronave_data: Aeronave, session: Session = Depends(get_session)):
    # Converter campos datetime, se forem strings
    if isinstance(aeronave_data.last_check, str):
        aeronave_data.last_check = datetime.fromisoformat(aeronave_data.last_check.replace("Z", "+00:00"))
    if isinstance(aeronave_data.next_check, str):
        aeronave_data.next_check = datetime.fromisoformat(aeronave_data.next_check.replace("Z", "+00:00"))
    
    # Adicionar ao banco de dados
    session.add(aeronave_data)
    session.commit()
    session.refresh(aeronave_data)
    
    return aeronave_data

# Read (sem filtros)
@router.get("/listar", response_model=list[Aeronave])
def read_aeronaves(
    offset: int = 0,
    limit: int = Query(default=10, le=100),  
    session: Session = Depends(get_session)):
    return session.exec(select(Aeronave).offset(offset).limit(limit)).all()

# Read (com filtros)
@router.get("/", response_model=list[Aeronave])
def read_aeronaves_filtro(
    id: int = Query(None, description="Buscar por ID"),
    modelo: str = Query(None, description="Filtrar por modelo da aeronave"),
    capacidade: int = Query(None, description="Filtrar por capacidade da aeronave"),
    cia_id: int = Query(None, description="Filtrar por companhia aérea ID"),
    session: Session = Depends(get_session)
):
    statement = select(Aeronave)

    # Filtro por ID da aeronave
    if id is not None:
        statement = statement.where(Aeronave.id == id)

    # Filtro por modelo da aeronave
    if modelo:
        statement = statement.where(Aeronave.modelo.ilike(f"%{modelo}%"))

    # Filtro por capacidade
    if capacidade is not None:
        statement = statement.where(Aeronave.capacidade == capacidade)

    # Filtro por companhia aérea ID
    if cia_id is not None:
        statement = statement.where(Aeronave.cia_id == cia_id)

    # Execução da consulta
    aeronaves = session.exec(statement).all()

    # Verifica se encontrou alguma aeronave
    if not aeronaves:
        raise HTTPException(status_code=404, detail="Aeronave não encontrada")

    return aeronaves

# Update
@router.put("/{id}", response_model=Aeronave)
def update_aeronave(id: int, aeronave_data: Aeronave, session: Session = Depends(get_session)):
    # Busca a aeronave pelo ID
    aeronave = session.get(Aeronave, id)
    if not aeronave:
        raise HTTPException(status_code=404, detail="Aeronave não encontrada")

    # Atualiza os dados da aeronave
    aeronave.modelo = aeronave_data.modelo
    aeronave.capacidade = aeronave_data.capacidade
    aeronave.last_check = aeronave_data.last_check
    aeronave.next_check = aeronave_data.next_check
    aeronave.cia_id = aeronave_data.cia_id

    # Commit para salvar as alterações
    session.commit()
    session.refresh(aeronave)  # Atualiza o objeto com as alterações

    return aeronave

# Delete
@router.delete("/{aeronave_id}", response_model=Aeronave)
def delete_aeronave(aeronave_id: int, session: Session = Depends(get_session)):
    # Query para buscar a aeronave pelo ID
    db_aeronave = session.get(Aeronave, aeronave_id)
    if not db_aeronave:
        # Retorna um erro 404 se a aeronave não for encontrada
        raise HTTPException(status_code=404, detail="Aeronave não encontrada")
    
    # Deleta a aeronave
    session.delete(db_aeronave)
    session.commit()
    return db_aeronave

@router.get("/contagem-aeronaves-por-voos", response_model=dict)
def contar_aeronaves_por_voos(session: Session = Depends(get_session)):
    statement = select(Aeronave.modelo, func.count(Voo.id).label("total_voos"))
    statement = statement.join(Voo, Voo.aeronave_id == Aeronave.id)  # Faz o join entre Voo e Aeronave
    statement = statement.group_by(Aeronave.modelo)  # Agrupa pela aeronave (modelo)

    # Executa a consulta e retorna os resultados
    resultados = session.exec(statement).all()
    
    # Retorna como um dicionário com o modelo da aeronave e a contagem de voos
    return {result[0]: result[1] for result in resultados}

# Informações completas das aeronaves
@router.get("/aeronaves-completas", response_model=list[dict])
def aeronaves_completas(session: Session = Depends(get_session)):
    statement = select(Aeronave).options(joinedload(Aeronave.cia))  # Carrega também a cia associada
    resultados = session.exec(statement).unique().all()  # Aplica unique() para garantir resultados únicos

    aeronaves_completas = []
    for aeronave in resultados:
        aeronaves_completas.append({
            "id": aeronave.id,
            "modelo": aeronave.modelo,
            "capacidade": aeronave.capacidade,
            "last_check": aeronave.last_check,
            "next_check": aeronave.next_check,
            "cia": {
                "id": aeronave.cia.id,
                "nome": aeronave.cia.nome,
                "cod_iata": aeronave.cia.cod_iata,
            }
        })

    return aeronaves_completas

# Buscar Aeronave pelo ID
@router.get("/{aeronave_id}", response_model=Aeronave)
def get_aeronave(aeronave_id: int, session: Session = Depends(get_session)):
    aeronave = session.get(Aeronave, aeronave_id)
    if not aeronave:
        raise HTTPException(status_code=404, detail="Aeronave não encontrada")
    return aeronave
