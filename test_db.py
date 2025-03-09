from sqlmodel import Session, select, text
from sqlalchemy import create_engine
from src.db.database import SQLModel, init_db
from src.db.crud_depositos import criar_deposito
from src.db.models import Deposito
import os
import unittest
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

class TestDatabase(unittest.TestCase):
    # Modifique apenas o setUpClass
    @classmethod
    def setUpClass(cls):
        # Configuração do engine com isolamento explícito
        cls.engine = create_engine(
            os.getenv("DATABASE_URL"),
            isolation_level="READ COMMITTED",
            echo=True
        )
        init_db()  # Agora sem passar o engine

    def setUp(self):
        # Nova sessão para cada teste
        self.session = Session(self.engine)
        
    def test_persistencia_verificavel(self):
        try:
            # Criação do registro
            dep = criar_deposito(self.session, "Depósito Fantasma")
            self.session.commit()  # Commit explícito

            # Pausa para verificação manual
            print("\n🔥 Execute no PGAdmin durante esta pausa:")
            print("BEGIN;")
            print("SELECT * FROM depositos WHERE nome = 'Depósito Fantasma';")
            print("COMMIT;")
            input("Pressione Enter após verificar...")

            # Verificação programática
            with Session(self.engine) as verifica_session:
                resultado = verifica_session.exec(
                    select(Deposito).where(Deposito.nome == "Depósito Fantasma")
                ).first()
                
                self.assertIsNotNone(resultado, "Registro não encontrado no banco!")
                print(f"\n✅ Registro verificado: ID {resultado.id}")

        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            # Limpeza após verificação
            if 'dep' in locals():
                self.session.delete(dep)
                self.session.commit()
                print("♻️ Registro de teste limpo com sucesso")

    def tearDown(self):
        self.session.close()

    @classmethod
    def tearDownClass(cls):
        # Limpeza final do engine
        cls.engine.dispose()

if __name__ == "__main__":
    unittest.main()