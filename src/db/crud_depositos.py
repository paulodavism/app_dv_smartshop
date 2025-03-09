from sqlmodel import Session, select
from typing import List, Optional
from .models import Deposito
from src.db.database import get_session
import logging

# Configuração básica do logging
logging.basicConfig(level=logging.DEBUG)

def criar_deposito(nome: str, tipo: str = "Próprio", observacoes: Optional[str] = None) -> Deposito:
    """Cria um novo depósito com validação de unicidade."""
    with get_session() as session:  # Gerencia a sessão automaticamente
        try:
            # Verifica se já existe um depósito com o mesmo nome
            existing = session.exec(select(Deposito).where(Deposito.nome == nome)).first()
            if existing:
                raise ValueError(f"Depósito '{nome}' já existe")
            
            # Cria um novo depósito
            novo_deposito = Deposito(nome=nome, tipo=tipo, observacoes=observacoes)
            session.add(novo_deposito)
            session.commit()  # Corrigido: Adicionado parênteses
            session.refresh(novo_deposito)  # Corrigido: Adicionado parênteses
            
            logging.debug(f"Novo depósito criado: {novo_deposito}")
            return novo_deposito
        
        except Exception as e:
            logging.error(f"Erro ao criar depósito: {str(e)}", exc_info=True)
            session.rollback()  # Garante rollback em caso de erro
            raise

def listar_depositos(filtro: Optional[str] = None) -> List[Deposito]:
    """Lista depósitos com filtro opcional por nome."""
    with get_session() as session:  # Gerencia a sessão automaticamente
        try:
            query = select(Deposito).order_by(Deposito.nome)
            if filtro:
                query = query.where(Deposito.nome.ilike(f"%{filtro}%"))  # Filtro por nome (case-insensitive)
            
            return session.exec(query).all()  # Corrigido: Adicionado .all()
        
        except Exception as e:
            logging.error(f"Erro ao listar depósitos: {str(e)}", exc_info=True)
            raise

def atualizar_deposito(deposito_id: int, novo_nome: Optional[str] = None, 
                       novo_tipo: Optional[str] = None, novas_observacoes: Optional[str] = None) -> Deposito:
    """Atualiza informações do depósito."""
    with get_session() as session:  # Gerencia a sessão automaticamente
        try:
            deposito = session.get(Deposito, deposito_id)
            if not deposito:
                raise ValueError("Depósito não encontrado")
            
            if novo_nome and novo_nome != deposito.nome:
                existing = session.exec(select(Deposito).where(Deposito.nome == novo_nome)).first()
                if existing:
                    raise ValueError(f"Nome '{novo_nome}' já está em uso")
                deposito.nome = novo_nome
            
            if novo_tipo:
                deposito.tipo = novo_tipo
            
            if novas_observacoes is not None:  # Permite definir observações como uma string vazia
                deposito.observacoes = novas_observacoes
            
            session.add(deposito)
            session.commit()  # Corrigido: Adicionado parênteses
            session.refresh(deposito)  # Corrigido: Adicionado parênteses
            
            return deposito
        
        except Exception as e:
            logging.error(f"Erro ao atualizar depósito: {str(e)}", exc_info=True)
            session.rollback()  # Garante rollback em caso de erro
            raise


def deletar_deposito(deposito_id: int) -> bool:
    """Remove depósito apenas se não tiver estoque associado."""
    with get_session() as session:  # Gerencia a sessão automaticamente
        try:
            deposito = session.get(Deposito, deposito_id)
            if not deposito:
                raise ValueError("Depósito não encontrado")
            
            if deposito.estoques:
                raise ValueError("Depósito possui estoque associado. Transfira primeiro.")
            
            logging.debug(f"Tentando excluir depósito com ID: {deposito_id}")
            session.delete(deposito)
            session.commit()  # Confirma a transação
            
            return True
        
        except ValueError as e:
            logging.error(f"Erro ao deletar depósito: {str(e)}")
            session.rollback()  # Garante rollback em caso de erro
            raise
        
        except Exception as e:
            logging.error(f"Erro inesperado ao deletar depósito: {str(e)}", exc_info=True)
            session.rollback()  # Garante rollback em caso de erro
            raise        