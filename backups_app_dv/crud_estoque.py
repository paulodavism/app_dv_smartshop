from sqlmodel import Session, select
from typing import Tuple, Dict, Optional, List, Any
from datetime import datetime
from .models import Estoque, Deposito, Produto, TipoEstoque
from src.db.database import get_session
import logging

# Configuração básica do logging
logging.basicConfig(level=logging.DEBUG)

def registrar_movimentacao(
    sku: str,
    deposito_id: int,
    quantidade: int,
    tipo: TipoEstoque,
    observacoes: Optional[str] = None
) -> Estoque:
    """
    Registra entrada/saída de estoque com validação de saldo.
    Retorna o registro atualizado ou cria um novo se não existir.
    """
    with get_session() as session:  # Gerencia a sessão automaticamente
        try:
            produto = session.get(Produto, sku)
            deposito = session.get(Deposito, deposito_id)

            if not produto or not deposito:
                raise ValueError("Produto ou Depósito inválido")

            registro = session.exec(
                select(Estoque)
                .where(Estoque.sku == sku)
                .where(Estoque.deposito_id == deposito_id)
            ).first()

            if registro:
                novo_saldo = registro.quantidade + quantidade
                if novo_saldo < 0:
                    raise ValueError("Saldo não pode ser negativo")
                registro.quantidade = novo_saldo
                registro.tipo = tipo
                registro.data_hora = datetime.now()
                registro.observacoes = observacoes
            else:
                if quantidade < 0:
                    raise ValueError("Estoque inicial não pode ser negativo")
                registro = Estoque(
                    sku=sku,
                    deposito_id=deposito_id,
                    quantidade=quantidade,
                    tipo=tipo,
                    data_hora=datetime.now(),
                    observacoes=observacoes
                )

            session.add(registro)
            session.commit()
            session.refresh(registro)

            logging.debug(f"Movimentação de estoque registrada: {registro}")
            return registro

        except Exception as e:
            logging.error(f"Erro ao registrar movimentação de estoque: {str(e)}", exc_info=True)
            session.rollback()  # Garante rollback em caso de erro
            raise

def transferir_estoque(
    sku: str,
    origem_id: int,
    destino_id: int,
    quantidade: int,
    observacoes: Optional[str] = None
) -> Tuple[Estoque, Estoque]:
    """
    Transferência segura entre depósitos com verificação de saldo.
    Retorna os registros atualizados da origem e destino.
    """
    with get_session() as session:  # Gerencia a sessão automaticamente
        try:
            if origem_id == destino_id:
                raise ValueError("Origem e destino devem ser diferentes")

            origem = session.get(Deposito, origem_id)
            destino = session.get(Deposito, destino_id)
            produto = session.get(Produto, sku)

            if not all([origem, destino, produto]):
                raise ValueError("Parâmetros inválidos")

            estoque_origem = session.exec(
                select(Estoque)
                .where(Estoque.sku == sku)
                .where(Estoque.deposito_id == origem_id)
            ).first()

            if not estoque_origem or estoque_origem.quantidade < quantidade:
                raise ValueError("Saldo insuficiente na origem")

            # Atualiza origem
            estoque_origem.quantidade -= quantidade
            estoque_origem.tipo = TipoEstoque.SAIDA
            estoque_origem.data_hora = datetime.now()
            estoque_origem.observacoes = observacoes

            # Atualiza destino
            estoque_destino = session.exec(
                select(Estoque)
                .where(Estoque.sku == sku)
                .where(Estoque.deposito_id == destino_id)
            ).first()

            if estoque_destino:
                estoque_destino.quantidade += quantidade
                estoque_destino.tipo = TipoEstoque.ENTRADA
                estoque_destino.data_hora = datetime.now()
                estoque_destino.observacoes = observacoes
            else:
                estoque_destino = Estoque(
                    sku=sku,
                    deposito_id=destino_id,
                    quantidade=quantidade,
                    tipo=TipoEstoque.ENTRADA,
                    data_hora=datetime.now(),
                    observacoes=observacoes
                )

            session.add_all([estoque_origem, estoque_destino])
            session.commit()
            session.refresh(estoque_origem)
            session.refresh(estoque_destino)

            logging.debug(f"Transferência de estoque realizada: Origem={estoque_origem}, Destino={estoque_destino}")
            return estoque_origem, estoque_destino

        except Exception as e:
            logging.error(f"Erro ao transferir estoque: {str(e)}", exc_info=True)
            session.rollback()  # Garante rollback em caso de erro
            raise


def consultar_estoque(sku=None, deposito_id=None):
    """
    Consulta o estoque com base nos parâmetros fornecidos.
    
    Args:
        sku (str, opcional): O SKU do produto a ser consultado. Se None, consulta todos os produtos.
        deposito_id (int, opcional): O ID do depósito a ser consultado. Se None, consulta todos os depósitos.
    
    Returns:
        tuple: Total de itens encontrados e uma lista detalhada de registros.
    """
    try:
        with get_session() as db:
            statement = select(Estoque, Deposito.nome.label("Depósito"), Produto.nome.label("Produto")).join(Deposito, Estoque.deposito_id == Deposito.id).join(Produto, Estoque.sku == Produto.sku)
            
            if sku:
                statement = statement.where(Estoque.sku == sku)
            if deposito_id:
                statement = statement.where(Estoque.deposito_id == deposito_id)
            
            resultados = db.exec(statement).all()
            
            detalhado = [
                {
                    "Depósito": registro.Depósito,
                    "SKU": registro.Estoque.sku,
                    "Nome do Produto": registro.Produto,
                    "Quantidade": int(registro.Estoque.quantidade)
                }
                for registro in resultados
            ]
            
            total = len(detalhado)
            return total, detalhado
    
    except Exception as e:
        print(f"Erro ao consultar estoque: {str(e)}")
        return 0, []        


def consultar_historico_movimentacoes(
    sku: Optional[str] = None,
    deposito_id: Optional[int] = None,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None
) -> List[Estoque]:
    """
    Consulta o histórico de movimentações de estoque, permitindo filtrar por SKU, depósito, e período.

    Args:
        sku: SKU do produto para filtrar. Se None, não filtra por SKU.
        deposito_id: ID do depósito para filtrar. Se None, não filtra por depósito.
        data_inicio: Data de início para filtrar. Se None, não filtra por data de início.
        data_fim: Data de fim para filtrar. Se None, não filtra por data de fim.

    Returns:
        Uma lista de objetos Estoque que correspondem aos critérios de filtro.
    """
    with get_session() as session:
        try:
            query = select(Estoque).order_by(Estoque.data_hora.desc())

            if sku is not None:
                query = query.where(Estoque.sku == sku)
            if deposito_id is not None:
                query = query.where(Estoque.deposito_id == deposito_id)
            if data_inicio is not None:
                query = query.where(Estoque.data_hora >= data_inicio)
            if data_fim is not None:
                query = query.where(Estoque.data_hora <= data_fim)

            registros = session.exec(query).all()

            logging.debug(f"Histórico de movimentações consultado: {len(registros)} registros encontrados")
            return registros

        except Exception as e:
            logging.error(f"Erro ao consultar histórico de movimentações: {str(e)}", exc_info=True)
            raise        