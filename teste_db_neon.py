from src.db.database import init_db, get_session

# Inicializa o banco de dados (cria as tabelas)
init_db()

# Testa a conexão
with get_session() as session:
    # Aqui você pode fazer uma query simples para testar
    # Por exemplo, se você tiver um modelo User:
    # users = session.query(User).all()
    # print(f"Número de usuários: {len(users)}")
    print("Conexão com o banco de dados bem-sucedida!")