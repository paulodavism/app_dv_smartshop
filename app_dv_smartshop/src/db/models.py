from sqlmodel import SQLModel, Field

class Deposito(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    nome: str = Field(max_length=100)
    tipo: str = Field(max_length=50)  # Ex: "Próprio" ou "Temporário"
    observacoes: str = Field(default=None, max_length=200)

class Produto(SQLModel, table=True):
    sku: str = Field(default=None, primary_key=True, max_length=50)
    nome: str = Field(max_length=100)
    descricao: str = Field(default=None, max_length=200)

class Estoque(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    sku: str = Field(foreign_key="produto.sku")
    deposito_id: int = Field(foreign_key="deposito.id")
    quantidade: int = Field(default=0)

class TipoEstoque(str):
    ENTRADA = "Entrada"
    SAIDA = "Saída"