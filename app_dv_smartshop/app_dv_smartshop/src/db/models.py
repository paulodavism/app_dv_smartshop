from sqlmodel import SQLModel, Field

class Produto(SQLModel, table=True):
    sku: str = Field(primary_key=True, index=True)
    nome: str
    descricao: str = None

class Deposito(SQLModel, table=True):
    id: int = Field(primary_key=True, index=True)
    nome: str
    tipo: str  # Pode ser 'Próprio' ou 'Temporário'
    observacoes: str = None

class Estoque(SQLModel, table=True):
    sku: str = Field(foreign_key="produto.sku", primary_key=True)
    deposito_id: int = Field(foreign_key="deposito.id", primary_key=True)
    saldo: int
    data_hora: str  # Data e hora da última atualização