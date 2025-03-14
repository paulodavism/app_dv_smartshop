from sqlmodel import Session, select
from typing import Tuple, Dict, Optional, List, Any
from datetime import datetime
from .models import Estoque, Deposito, Produto, TipoEstoque
from src.db.database import get_session
from sqlalchemy import func, and_
import logging

# Configuração básica do logging
logging.basicConfig(level=logging.DEBUG)

def consultar_saldo(sku: str, deposito_id: int) -> int:
    """
    Consulta o saldo atual de um produto em um determinado depósito.
    """
    with get_session() as session:
        saldo = _calcular_saldo(session, sku, deposito_id)
        return saldo


def _calcular_saldo(session: Session, sku: str, deposito_id: int) -> int:
    """
    Calcula o saldo atual do estoque para um determinado produto e depósito.
    """
    # Encontra o registro de balanço mais recente
    balanco_recente = session.exec(
        select(Estoque)
        .where(Estoque.sku == sku)
        .where(Estoque.deposito_id == deposito_id)
        .where(Estoque.tipo == TipoEstoque.BALANCO)
        .order_by(Estoque.data_hora.desc())
    ).first()

    query = select(Estoque).where(Estoque.sku == sku).where(Estoque.deposito_id == deposito_id)

    if balanco_recente:
        query = query.where(Estoque.data_hora >= balanco_recente.data_hora)
        saldo = balanco_recente.quantidade
    else:
        saldo = 0

    movimentacoes = session.exec(query).all()

    for movimentacao in movimentacoes:
        if movimentacao.tipo == TipoEstoque.ENTRADA:
            saldo += movimentacao.quantidade
        elif movimentacao.tipo == TipoEstoque.SAIDA:
            saldo -= movimentacao.quantidade  # Adiciona a quantidade (que já é negativa para saídas)
        elif movimentacao.tipo == TipoEstoque.BALANCO and movimentacao != balanco_recente:
            saldo = movimentacao.quantidade

    return saldo

def atualizar_movimentacao(
    movimentacao_id: int,
    nova_quantidade: int,
    nova_observacao: str
) -> Estoque:
    """
    Atualiza a quantidade e as observações de um registro de movimentação de estoque.

    Args:
        movimentacao_id: ID do registro de movimentação a ser atualizado.
        nova_quantidade: Nova quantidade do registro.
        nova_observacao: Novas observações do registro.

    Returns:
        O registro de movimentação atualizado.
    """
    with get_session() as session:
        try:
            registro = session.get(Estoque, movimentacao_id)

            if not registro:
                raise ValueError("Registro de movimentação não encontrado")

            # Validar a quantidade
            if registro.tipo == TipoEstoque.SAIDA and nova_quantidade > _calcular_saldo(session, registro.sku, registro.deposito_id):
                raise ValueError("Saldo insuficiente")

            registro.quantidade = nova_quantidade
            registro.observacoes = nova_observacao

            session.add(registro)
            session.commit()
            session.refresh(registro)

            # Recalcular o saldo
            novo_saldo = _calcular_saldo(session, registro.sku, registro.deposito_id)
            registro.saldo = novo_saldo
            session.add(registro)
            session.commit()
            session.refresh(registro)

            logging.debug(f"Movimentação de estoque atualizada: {registro}")
            return registro

        except Exception as e:
            logging.error(f"Erro ao atualizar movimentação de estoque: {str(e)}", exc_info=True)
            session.rollback()
            raise


def excluir_movimentacao(movimentacao_id: int) -> None:
    """
    Exclui um registro de movimentação de estoque.

    Args:
        movimentacao_id: ID do registro de movimentação a ser excluído.
    """
    with get_session() as session:
        try:
            registro = session.get(Estoque, movimentacao_id)

            if not registro:
                raise ValueError("Registro de movimentação não encontrado")

            session.delete(registro)
            session.commit()

            # Recalcular o saldo
            novo_saldo = _calcular_saldo(session, registro.sku, registro.deposito_id)
            # registro.saldo = novo_saldo # Não sei se precisa disso
            # session.add(registro) # Não sei se precisa disso
            # session.commit() # Não sei se precisa disso
            # session.refresh(registro) # Não sei se precisa disso

            logging.debug(f"Movimentação de estoque excluída: {registro}")

        except Exception as e:
            logging.error(f"Erro ao excluir movimentação de estoque: {str(e)}", exc_info=True)
            session.rollback()
            raise


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

            # Calcula o saldo atual
            saldo_atual = _calcular_saldo(session, sku, deposito_id)

            # Valida a saída
            if tipo == TipoEstoque.SAIDA and quantidade > saldo_atual:
                raise ValueError("Saldo insuficiente")

            # Remove a lógica de buscar um registro existente
            # registro = session.exec(
            #     select(Estoque)
            #     .where(Estoque.sku == sku)
            #     .where(Estoque.deposito_id == deposito_id)
            #     .where(Estoque.tipo == tipo)  # Adiciona a condição para o tipo
            # ).first()

            # if registro:
            #     novo_saldo = registro.quantidade + quantidade
            #     if novo_saldo < 0:
            #         raise ValueError("Saldo não pode ser negativo")
            #     registro.quantidade = novo_saldo
            #     registro.tipo = tipo
            #     registro.data_hora = datetime.now()
            #     registro.observacoes = observacoes
            # else:
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

            # Atualiza o saldo
            novo_saldo = _calcular_saldo(session, sku, deposito_id)
            registro.saldo = novo_saldo
            session.add(registro)
            session.commit()
            session.refresh(registro)

            logging.debug(f"Movimentação de estoque registrada: {registro}")
            return registro

        except ValueError as e:
            logging.error(f"Erro ao registrar movimentação de estoque: {str(e)}", exc_info=True)
            session.rollback()  # Garante rollback em caso de erro
            raise e  # Re-lança a exceção para que seja tratada na interface do usuário
        
        except Exception as e:
            logging.error(f"Erro ao registrar movimentação de estoque: {str(e)}", exc_info=True)
            session.rollback()  # Garante rollback em caso de erro
            raise  # Re-lança a exceção para que seja tratada na interface do usuário
        
        return None  # Retorna None em caso de falha

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

            # Calcula o saldo atual na origem
            saldo_origem = _calcular_saldo(session, sku, origem_id)
            if saldo_origem < quantidade:
                raise ValueError("Saldo insuficiente na origem")

            # Registra a saída no depósito de origem
            registro_saida = Estoque(
                sku=sku,
                deposito_id=origem_id,
                quantidade=quantidade,  # Quantidade positiva para saída
                tipo=TipoEstoque.SAIDA,
                data_hora=datetime.now(),
                observacoes=observacoes
            )
            session.add(registro_saida)

            # Registra a entrada no depósito de destino
            registro_entrada = Estoque(
                sku=sku,
                deposito_id=destino_id,
                quantidade=quantidade,  # Quantidade positiva para entrada
                tipo=TipoEstoque.ENTRADA,
                data_hora=datetime.now(),
                observacoes=observacoes
            )
            session.add(registro_entrada)

            session.commit()
            session.refresh(registro_saida)
            session.refresh(registro_entrada)

            # Atualiza o saldo na origem
            novo_saldo_origem = _calcular_saldo(session, sku, origem_id)
            registro_saida.saldo = novo_saldo_origem
            session.add(registro_saida)
            session.commit()
            session.refresh(registro_saida)

            # Atualiza o saldo no destino
            novo_saldo_destino = _calcular_saldo(session, sku, destino_id)
            registro_entrada.saldo = novo_saldo_destino
            session.add(registro_entrada)
            session.commit()
            session.refresh(registro_entrada)

            logging.debug(f"Transferência de estoque realizada: Saída={registro_saida}, Entrada={registro_entrada}")
            return registro_saida, registro_entrada

        except Exception as e:
            logging.error(f"Erro ao transferir estoque: {str(e)}", exc_info=True)
            session.rollback()  # Garante rollback em caso de erro
            raise
        
        return None, None  # Retorna None em caso de falha
    
def consultar_estoque(sku=None, deposito_id=None):
    """
    Consulta o estoque, retornando o saldo atual com base no registro mais recente.
    
    Args:
        sku (str, opcional): O SKU do produto a ser consultado. Se None, consulta todos os produtos.
        deposito_id (int, opcional): O ID do depósito a ser consultado. Se None, consulta todos os depósitos.
    
    Returns:
        tuple: Total de itens encontrados e uma lista detalhada de registros com o saldo atual.
    """
    try:
        with get_session() as db:
            # Subquery para encontrar a data/hora mais recente de cada SKU e depósito
            subquery = (
                select(Estoque.sku, Estoque.deposito_id, func.max(Estoque.data_hora).label("max_data_hora"))
                .group_by(Estoque.sku, Estoque.deposito_id)
                .subquery()
            )

            # Query principal para selecionar os registros mais recentes
            statement = (
                select(
                    Estoque,
                    Deposito.nome.label("Depósito"),
                    Produto.nome.label("Produto")
                )
                .join(Deposito, Estoque.deposito_id == Deposito.id)
                .join(Produto, Estoque.sku == Produto.sku)
                .join(subquery, and_(
                    Estoque.sku == subquery.c.sku,
                    Estoque.deposito_id == subquery.c.deposito_id,
                    Estoque.data_hora == subquery.c.max_data_hora
                ))
            )
            
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
                    "Quantidade": int(registro.Estoque.saldo)  # Usar o saldo ao invés da quantidade
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
    data_fim: Optional[datetime] = None,
) -> List[Dict]:
    """
    Consulta o histórico de movimentações de estoque, permitindo filtrar por SKU, depósito e período.

    Args:
        sku: SKU do produto para filtrar as movimentações.
        deposito_id: ID do depósito para filtrar as movimentações.
        data_inicio: Data de início para filtrar as movimentações.
        data_fim: Data de fim para filtrar as movimentações.

    Returns:
        Uma lista de dicionários representando o histórico de movimentações.
    """
    with get_session() as session:
        query = select(Estoque)

        if sku:
            query = query.where(Estoque.sku == sku)
        if deposito_id:
            query = query.where(Estoque.deposito_id == deposito_id)
        if data_inicio:
            query = query.where(Estoque.data_hora >= data_inicio)
        if data_fim:
            query = query.where(Estoque.data_hora <= data_fim)

        query = query.order_by(Estoque.data_hora.desc())

        historico = session.exec(query).all()
        
        # Converte a lista de objetos Estoque para uma lista de dicionários
        historico_lista = []
        for registro in historico:
            historico_lista.append({
                "id": registro.id,
                "sku": registro.sku,
                "deposito_id": registro.deposito_id,
                "quantidade": registro.quantidade,
                "tipo": registro.tipo,
                "data_hora": registro.data_hora,
                "observacoes": registro.observacoes,
                "saldo": registro.saldo,
            })
        
        return historico_lista


