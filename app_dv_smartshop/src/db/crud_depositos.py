def criar_deposito(nome: str, tipo: str, observacoes: str):
    from sqlalchemy.orm import Session
    from .database import get_session
    from .models import Deposito

    with get_session() as session:
        novo_deposito = Deposito(nome=nome, tipo=tipo, observacoes=observacoes)
        session.add(novo_deposito)
        session.commit()

def listar_depositos():
    from sqlalchemy.orm import Session
    from .database import get_session
    from .models import Deposito

    with get_session() as session:
        return session.query(Deposito).all()

def atualizar_deposito(deposito_id: int, novo_nome: str, novo_tipo: str, novas_observacoes: str):
    from sqlalchemy.orm import Session
    from .database import get_session
    from .models import Deposito

    with get_session() as session:
        deposito = session.query(Deposito).filter(Deposito.id == deposito_id).first()
        if deposito:
            deposito.nome = novo_nome
            deposito.tipo = novo_tipo
            deposito.observacoes = novas_observacoes
            session.commit()
        else:
            raise ValueError("Depósito não encontrado.")

def deletar_deposito(deposito_id: int):
    from sqlalchemy.orm import Session
    from .database import get_session
    from .models import Deposito

    with get_session() as session:
        deposito = session.query(Deposito).filter(Deposito.id == deposito_id).first()
        if deposito:
            session.delete(deposito)
            session.commit()
        else:
            raise ValueError("Depósito não encontrado.")