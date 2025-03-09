from sqlmodel import Session, select
from .models import Deposito

def criar_deposito(nome: str, tipo: str, observacoes: str) -> Deposito:
    with Session() as session:
        novo_deposito = Deposito(nome=nome, tipo=tipo, observacoes=observacoes)
        session.add(novo_deposito)
        session.commit()
        session.refresh(novo_deposito)
        return novo_deposito

def listar_depositos() -> list:
    with Session() as session:
        statement = select(Deposito)
        resultados = session.exec(statement).all()
        return resultados

def atualizar_deposito(deposito_id: int, novo_nome: str, novo_tipo: str, novas_observacoes: str) -> None:
    with Session() as session:
        deposito = session.get(Deposito, deposito_id)
        if deposito:
            deposito.nome = novo_nome
            deposito.tipo = novo_tipo
            deposito.observacoes = novas_observacoes
            session.commit()

def deletar_deposito(deposito_id: int) -> None:
    with Session() as session:
        deposito = session.get(Deposito, deposito_id)
        if deposito:
            session.delete(deposito)
            session.commit()