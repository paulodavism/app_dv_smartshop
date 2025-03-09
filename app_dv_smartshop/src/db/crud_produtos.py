def criar_produto(sku: str, nome: str, descricao: str):
    """Cria um novo produto no banco de dados."""
    with get_session() as db:
        novo_produto = Produto(sku=sku, nome=nome, descricao=descricao)
        db.add(novo_produto)
        db.commit()
        db.refresh(novo_produto)
        return novo_produto

def listar_produtos(filtro: str = None):
    """Lista todos os produtos no banco de dados, com opção de filtro."""
    with get_session() as db:
        query = select(Produto)
        if filtro:
            query = query.where(Produto.nome.ilike(f"%{filtro}%") | Produto.sku.ilike(f"%{filtro}%"))
        return db.exec(query).all()

def atualizar_produto(sku: str, novo_nome: str, nova_descricao: str):
    """Atualiza as informações de um produto existente."""
    with get_session() as db:
        produto = db.exec(select(Produto).where(Produto.sku == sku)).first()
        if produto:
            produto.nome = novo_nome
            produto.descricao = nova_descricao
            db.commit()
            db.refresh(produto)
            return produto
        else:
            raise ValueError("Produto não encontrado.")

def deletar_produto(sku: str):
    """Remove um produto do banco de dados."""
    with get_session() as db:
        produto = db.exec(select(Produto).where(Produto.sku == sku)).first()
        if produto:
            db.delete(produto)
            db.commit()
        else:
            raise ValueError("Produto não encontrado.")