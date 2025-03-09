from sqlmodel import Session, select
from .models import Produto

def criar_produto(sku: str, nome: str, descricao: str, db: Session):
    """Cria um novo produto no banco de dados."""
    produto = Produto(sku=sku, nome=nome, descricao=descricao)
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto

def listar_produtos(filtro: str = None, db: Session = None):
    """Lista todos os produtos, com opção de filtro."""
    statement = select(Produto)
    if filtro:
        statement = statement.where(Produto.nome.ilike(f"%{filtro}%"))
    return db.exec(statement).all()

def atualizar_produto(sku: str, novo_nome: str, nova_descricao: str, db: Session):
    """Atualiza as informações de um produto existente."""
    produto = db.exec(select(Produto).where(Produto.sku == sku)).first()
    if produto:
        produto.nome = novo_nome
        produto.descricao = nova_descricao
        db.commit()
        db.refresh(produto)
        return produto
    else:
        raise ValueError("Produto não encontrado.")

def deletar_produto(sku: str, db: Session):
    """Deleta um produto do banco de dados."""
    produto = db.exec(select(Produto).where(Produto.sku == sku)).first()
    if produto:
        db.delete(produto)
        db.commit()
    else:
        raise ValueError("Produto não encontrado.")