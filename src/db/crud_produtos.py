from sqlmodel import Session, select
from typing import List, Optional
from .models import Produto
from src.db.database import get_session
import logging

# Configuração básica do logging
logging.basicConfig(level=logging.DEBUG)

def criar_produto(sku: str, nome: str, descricao: Optional[str] = None) -> Produto:
    """
    Cadastra novo produto com validação de SKU único.
    Retorna o produto criado ou levanta um erro caso o SKU já exista.
    """
    with get_session() as session:  # Gerencia a sessão automaticamente
        try:
            # Verifica se já existe um produto com o mesmo SKU
            existing = session.get(Produto, sku)
            if existing:
                raise ValueError(f"SKU '{sku}' já cadastrado. Por favor, use um SKU diferente.")
            
            # Cria um novo produto
            novo_produto = Produto(sku=sku, nome=nome, descricao=descricao)
            session.add(novo_produto)
            session.commit()
            session.refresh(novo_produto)
            
            logging.debug(f"Novo produto criado: {novo_produto}")
            return novo_produto
        
        except Exception as e:
            logging.error(f"Erro ao criar produto: {str(e)}", exc_info=True)
            session.rollback()  # Garante rollback em caso de erro
            raise

def listar_produtos(filtro: Optional[str] = None) -> List[Produto]:
    """
    Lista produtos com filtro opcional por nome ou SKU.
    Retorna uma lista de produtos ordenados pelo SKU.
    """
    with get_session() as session:  # Gerencia a sessão automaticamente
        try:
            query = select(Produto).order_by(Produto.sku)
            if filtro:
                query = query.where(Produto.nome.ilike(f"%{filtro}%") | Produto.sku.ilike(f"%{filtro}%"))
            
            return session.exec(query).all()
        
        except Exception as e:
            logging.error(f"Erro ao listar produtos: {str(e)}", exc_info=True)
            raise

def atualizar_produto(
    sku: str, 
    novo_nome: Optional[str] = None, 
    nova_descricao: Optional[str] = None
) -> Produto:
    """
    Atualiza dados do produto de forma parcial.
    Retorna o produto atualizado ou levanta um erro caso o SKU não seja encontrado.
    """
    with get_session() as session:  # Gerencia a sessão automaticamente
        try:
            produto = session.get(Produto, sku)
            if not produto:
                raise ValueError(f"Produto com SKU '{sku}' não encontrado.")
            
            if novo_nome and novo_nome != produto.nome:
                produto.nome = novo_nome
            
            if nova_descricao is not None:  # Permite definir descrição como uma string vazia
                produto.descricao = nova_descricao
            
            session.add(produto)
            session.commit()
            session.refresh(produto)
            
            logging.debug(f"Produto atualizado: {produto}")
            return produto
        
        except Exception as e:
            logging.error(f"Erro ao atualizar produto: {str(e)}", exc_info=True)
            session.rollback()  # Garante rollback em caso de erro
            raise

def deletar_produto(sku: str) -> bool:
    """
    Remove um produto e todo seu estoque associado (CASCADE).
    Retorna True se o produto for excluído com sucesso, False caso contrário.
    """
    with get_session() as session:  # Gerencia a sessão automaticamente
        try:
            produto = session.get(Produto, sku)
            if not produto:
                raise ValueError(f"Produto com SKU '{sku}' não encontrado.")
            
            logging.debug(f"Tentando excluir produto com SKU: {sku}")
            session.delete(produto)
            session.commit()  # Confirma a transação
            
            return True
        
        except ValueError as e:
            logging.error(f"Erro ao deletar produto: {str(e)}")
            session.rollback()  # Garante rollback em caso de erro
            raise
        
        except Exception as e:
            logging.error(f"Erro inesperado ao deletar produto: {str(e)}", exc_info=True)
            session.rollback()  # Garante rollback em caso de erro
            raise