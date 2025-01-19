from sqlalchemy.orm import joinedload # Import necessário para o joinedload
from sqlalchemy import func, or_
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from models.voo import Voo
from models.aeronave import Aeronave
from models.cia import Cia
from database import get_session
from datetime import datetime


router = APIRouter(
    prefix="/voos",  # Prefixo para todas as rotas
    tags=["Voos"],  # Tag para documentação automática
)
# Create
@router.post("/", response_model=Voo)
def create_voo(voo_data: Voo, session: Session = Depends(get_session)):
    # Converter campos datetime, se forem strings
    if isinstance(voo_data.hr_partida, str):
        voo_data.hr_partida = datetime.fromisoformat(voo_data.hr_partida.replace("Z", "+00:00"))
    if isinstance(voo_data.hr_chegada, str):
        voo_data.hr_chegada = datetime.fromisoformat(voo_data.hr_chegada.replace("Z", "+00:00"))
    
    session.add(voo_data)
    session.commit()
    session.refresh(voo_data)
    return voo_data

# Consultas 
@router.get("/", response_model=list[Voo])
def read_voos(
    busca_texto: str = Query(None, description="Busca por texto parcial no nome da origem ou destino"),
    companhia_nome: str = Query(None, description="Nome da companhia aérea para filtrar"),
    id: int = Query(None, description="ID do voo para filtrar"),
    ano: int = Query(None, description="Ano de partida dos voos"),
    data_inicio: str = Query(None, description="Data de início para filtrar os voos (formato YYYY-MM-DD)"),
    data_fim: str = Query(None, description="Data de fim para filtrar os voos (formato YYYY-MM-DD)"),
    ordenacao: str = Query(None, description="Campo para ordenação: 'hr_partida' ou 'hr_chegada'"),
    contagem: bool = Query(False, description="Se True, retorna a contagem de voos por companhia"),
    incluir_aeronave: bool = Query(False, description="Se True, inclui informações da aeronave nos voos"),
    session: Session = Depends(get_session)
):
    statement = select(Voo)

    # Filtro por ID do voo
    if id:
        statement = statement.where(Voo.id == id)

    # Filtro por ano de partida
    if ano:
        statement = statement.where(Voo.hr_partida.year == ano)

    # Filtro por data de início
    if data_inicio:
        data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
        statement = statement.where(Voo.hr_partida >= data_inicio_dt)

    # Filtro por data de fim
    if data_fim:
        data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d")
        statement = statement.where(Voo.hr_partida <= data_fim_dt)

    # Filtro por companhia aérea
    if companhia_nome:
        statement = statement.join(Cia).where(Cia.nome == companhia_nome)

    # Busca por texto parcial nos campos 'origem' ou 'destino'
    if busca_texto:
        statement = statement.where(
            or_(
                Voo.origem.ilike(f"%{busca_texto}%"),
                Voo.destino.ilike(f"%{busca_texto}%")
            )
        )

    # Incluir dados da aeronave nos resultados, caso necessário
    if incluir_aeronave:
        statement = statement.join(Aeronave)  # Assume-se que Voo tem uma relação com Aeronave

    # Ordenação
    if ordenacao:
        if ordenacao == "hr_partida":
            statement = statement.order_by(Voo.hr_partida)
        elif ordenacao == "hr_chegada":
            statement = statement.order_by(Voo.hr_chegada)

    # Contagem de voos por companhia (agregação)
    if contagem:
        statement = select(Cia.nome, func.count(Voo.id).label("qtd_voos")).join(Voo).group_by(Cia.id)
        resultados = session.exec(statement).all()
        return resultados

    # Execução da consulta e retorno dos voos
    voos = session.exec(statement).all()
    return voos