from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload  # Import necessário para o joinedload
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from models.aeronave import Aeronave
from models.cia import Cia  # Importe o modelo Voo
from database import get_session
from models.voo import Voo

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

# Read (sem filtros)
@router.get("/listar", response_model=list[Cia])
def read_cia(
    offset: int = 0,
    limit: int = Query(default=10, le=100),  
    session: Session = Depends(get_session)):
    return session.exec(select(Cia).offset(offset).limit(limit)).all()

# Read (com filtros)
@router.get("/", response_model=list[Cia])
def read_cias(
    id: int = Query(None, description="Buscar por ID"),
    cod_iata: str = Query(None, description="Filtrar por código iata"),
    busca_texto: str = Query(None, description="Filtrar por nome da companhia aérea (parcial)"),
    ordenacao: str = Query(None, description="Campo para ordenação: 'nome'"),
    session: Session = Depends(get_session)
):
    statement = select(Cia)

    # Filtro por ID da companhia aérea
    if id is not None:
        statement = statement.where(Cia.id == id)

    # Filtro por código IATA da companhia aérea
    if cod_iata:
        statement = statement.where(Cia.cod_iata == cod_iata)

    # Filtro por nome da companhia aérea (parcial)
    if busca_texto:
        statement = statement.where(Cia.nome.ilike(f"%{busca_texto}%"))

    # Ordenação
    if ordenacao:
        if ordenacao == "nome":
            statement = statement.order_by(Cia.nome)
    
    # Execução da consulta
    cias = session.exec(statement).all()

    # Verifica se encontrou alguma companhia
    if not cias:
        raise HTTPException(status_code=404, detail="Companhia aérea não encontrada")

    return cias

# Update
@router.put("/{id}", response_model=Cia)
def update_cia(id: int, cia_data: Cia, session: Session = Depends(get_session)):
    # Busca a cia pelo ID
    cia = session.get(Cia, id)
    if not cia:
        raise HTTPException(status_code=404, detail="Cia não encontrada")

    # Atualiza os dados da cia
    cia.nome = cia_data.nome
    cia.cod_iata = cia_data.cod_iata

    # Commit para salvar as alterações
    session.commit()
    session.refresh(cia)  # Atualiza o objeto com as alterações

    return cia

# Delete
@router.delete("/{cia_id}", response_model=Cia)
def delete_cia(cia_id: int, session: Session = Depends(get_session)):
    # Query para buscar a cia pelo ID
    db_cia = session.get(Cia, cia_id)
    if not db_cia:
        # Retorna um erro 404 se a cia não for encontrada
        raise HTTPException(status_code=404, detail="Cia não encontrada")
    
    # Deleta a cia
    session.delete(db_cia)
    session.commit()
    return db_cia

# Consultas de contagem por modelo de aeronave
@router.get("/contagem-por-modelo", response_model=list[dict])
def contar_aeronaves_por_modelo(session: Session = Depends(get_session)):
    # Query para contar aeronaves agrupadas por modelo e companhia aérea
    statement = (
        select(Cia.nome, Aeronave.modelo, func.count(Aeronave.id).label("total_aeronaves"))
        .join(Aeronave, Aeronave.cia_id == Cia.id)  # Realiza o JOIN entre Cia e Aeronave
        .group_by(Cia.nome, Aeronave.modelo)  # Agrupa por companhia e modelo
    )
    resultados = session.exec(statement).all()

    # Formata o retorno como uma lista de dicionários
    return [
        {"cia": result[0], "modelo": result[1], "total_aeronaves": result[2]}
        for result in resultados
    ]

# Informações completas das companhias aéreas
@router.get("/cias-completa", response_model=list[dict])
def cias_completas(session: Session = Depends(get_session)):
    statement = select(Cia).options(joinedload(Cia.aeronaves))
    resultados = session.exec(statement).unique().all()  # Aplica unique() para garantir resultados únicos

    cias_completas = []
    for cia in resultados:
        cias_completas.append({
            "id": cia.id,
            "nome": cia.nome,
            "cod_iata": cia.cod_iata,
            "aeronaves": [
                {
                    "id": aeronave.id,
                    "modelo": aeronave.modelo,
                    "capacidade": aeronave.capacidade,
                    "last_check": aeronave.last_check,
                    "next_check": aeronave.next_check,
                }
                for aeronave in cia.aeronaves
            ]
        })

    return cias_completas


# Buscar Companhia Aérea pelo ID
@router.get("/{cia_id}", response_model=Cia)
def get_cia(cia_id: int, session: Session = Depends(get_session)):
    cia = session.get(Cia, cia_id)
    if not cia:
        raise HTTPException(status_code=404, detail="Cia não encontrada")
    return cia
