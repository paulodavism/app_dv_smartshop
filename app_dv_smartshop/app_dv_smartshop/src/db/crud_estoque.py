from sqlmodel import Session, select
from .models import Estoque
from sqlalchemy.exc import IntegrityError

def registrar_movimentacao(sku: str, deposito_id: int, quantidade: int, tipo: str, observacao: str):
    with Session() as session:
        movimentacao = Estoque(sku=sku, deposito_id=deposito_id, quantidade=quantidade, tipo=tipo, observacao=observacao)
        session.add(movimentacao)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise ValueError("Erro ao registrar movimentação: SKU ou depósito inválido.")

def consultar_estoque(sku: str = None, deposito_id: int = None):
    with Session() as session:
        query = select(Estoque)
        if sku:
            query = query.where(Estoque.sku == sku)
        if deposito_id:
            query = query.where(Estoque.deposito_id == deposito_id)
        resultados = session.exec(query).all()
        return resultados

def transferir_estoque(sku: str, origem_id: int, destino_id: int, quantidade: int, observacao: str):
    with Session() as session:
        # Reduzir da origem
        origem = session.exec(select(Estoque).where(Estoque.sku == sku, Estoque.deposito_id == origem_id)).first()
        if origem.quantidade < quantidade:
            raise ValueError("Quantidade insuficiente no depósito de origem.")
        origem.quantidade -= quantidade
        
        # Aumentar no destino
        destino = session.exec(select(Estoque).where(Estoque.sku == sku, Estoque.deposito_id == destino_id)).first()
        if destino:
            destino.quantidade += quantidade
        else:
            destino = Estoque(sku=sku, deposito_id=destino_id, quantidade=quantidade)
            session.add(destino)
        
        session.commit()