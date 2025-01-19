from sqlalchemy.orm import joinedload  # Import necessário para o joinedload
from sqlalchemy import func, or_, literal_column
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

@router.put("/{id}", response_model=Voo)
def update_voo(id: int, voo_data: Voo, session: Session = Depends(get_session)):
    # Busca o voo pelo ID
    voo = session.get(Voo, id)
    if not voo:
        raise HTTPException(status_code=404, detail="Voo não encontrado")

    # Converte as strings para datetime
    if isinstance(voo_data.hr_partida, str):
        voo_data.hr_partida = datetime.fromisoformat(voo_data.hr_partida)
    if isinstance(voo_data.hr_chegada, str):
        voo_data.hr_chegada = datetime.fromisoformat(voo_data.hr_chegada)

    # Atualiza os dados do voo
    voo.numero_voo = voo_data.numero_voo
    voo.origem = voo_data.origem
    voo.destino = voo_data.destino
    voo.hr_partida = voo_data.hr_partida
    voo.hr_chegada = voo_data.hr_chegada
    voo.status = voo_data.status
    voo.aeronave_id = voo_data.aeronave_id
    voo.cia_id = voo_data.cia_id

    # Commit para salvar as alterações
    session.commit()
    session.refresh(voo)  # Atualiza o objeto com as alterações

    return voo
# Delete (DELETE)
@router.delete("/{id}", response_model=str)
def delete_voo(id: int, session: Session = Depends(get_session)):
    voo = session.get(Voo, id)
    if not voo:
        raise HTTPException(status_code=404, detail="Voo não encontrado")

    session.delete(voo)
    session.commit()

    return {"message": "Voo excluído com sucesso"}

# Consultas
@router.get("/", response_model=list[Voo])
def read_voos(
    id: int = Query(None, description="Buscar por ID"),
    data_inicio: str = Query(None, description="Data de início para filtrar os voos (formato YYYY-MM-DD)"),
    data_fim: str = Query(None, description="Data de fim para filtrar os voos (formato YYYY-MM-DD)"),
    companhia_nome: str = Query(None, description="Filtrar por cia"),
    busca_texto: str = Query(None, description="Filtrar por origem ou destino"),
    ordenacao: str = Query(None, description="Campo para ordenação: 'hr_partida' ou 'hr_chegada'"),
    session: Session = Depends(get_session)
):
    statement = select(Voo)

    # Filtro por ID do voo
    if id:
        statement = statement.where(Voo.id == id)

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
        statement = statement.join(Cia).where(Cia.nome.ilike(f"%{companhia_nome}%"))

    # Busca por texto parcial nos campos 'origem' ou 'destino'
    if busca_texto:
        statement = statement.where(
            or_(
                Voo.origem.ilike(f"%{busca_texto}%"),
                Voo.destino.ilike(f"%{busca_texto}%")
            )
        )

    # Ordenação
    if ordenacao:
        if ordenacao == "hr_partida":
            statement = statement.order_by(Voo.hr_partida)
        elif ordenacao == "hr_chegada":
            statement = statement.order_by(Voo.hr_chegada)
    
    # Execução da consulta e retorno dos voos
    voos = session.exec(statement).all()
    return voos

@router.get("/contagem-por-companhia", response_model=dict)
def contar_voos_por_companhia(session: Session = Depends(get_session)):
    statement = select(Cia.nome, func.count(Voo.id).label("total_voos")).join(Voo).group_by(Cia.nome)
    resultados = session.exec(statement).all()
    return {result[0]: result[1] for result in resultados}

@router.get("/voos-completo", response_model=list[dict])
def voos_completo(session: Session = Depends(get_session)):
    statement = (
        select(Voo)
        .select_from(Voo)
        .join(Cia, Voo.cia_id == Cia.id)  # Join explícito entre Voo e Cia
        .join(Aeronave, Voo.aeronave_id == Aeronave.id)  # Join explícito entre Voo e Aeronave
    )
    resultados = session.exec(statement).all()
    
    # Formatação do retorno para incluir todos os dados de Cia e Aeronave
    voos_completos = []
    for voo in resultados:
        voos_completos.append({
            "id": voo.id,
            "numero_voo": voo.numero_voo,
            "origem": voo.origem,
            "destino": voo.destino,
            "hr_partida": voo.hr_partida,
            "hr_chegada": voo.hr_chegada,
            "status": voo.status,
            "cia": {
                "id": voo.cia.id,
                "nome": voo.cia.nome,
                "cod_iata": voo.cia.cod_iata,
                "aeronaves": [
                    {"id": aeronave.id, "modelo": aeronave.modelo, "capacidade": aeronave.capacidade}
                    for aeronave in voo.cia.aeronaves
                ]
            },
            "aeronave": {
                "id": voo.aeronave.id,
                "modelo": voo.aeronave.modelo,
                "capacidade": voo.aeronave.capacidade,
                "last_check": voo.aeronave.last_check,
                "next_check": voo.aeronave.next_check,
                "cia": {
                    "id": voo.aeronave.cia.id,
                    "nome": voo.aeronave.cia.nome,
                    "cod_iata": voo.aeronave.cia.cod_iata
                }
            }
        })
    
    return voos_completos

