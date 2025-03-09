# DV SmartShop - Gestão Integrada de Estoque

## Descrição
O DV SmartShop é uma aplicação web desenvolvida com Streamlit para gerenciar depósitos, produtos e estoque de forma integrada. A aplicação permite a visualização de dados em tempo real, gerenciamento de produtos e depósitos, além de registrar movimentações de estoque.

## Estrutura do Projeto
A estrutura do projeto é organizada da seguinte forma:

```
app_dv_smartshop
├── src
│   ├── api
│   │   ├── amazon.py          # Implementação para interagir com a API da Amazon
│   │   └── mercadolivre.py    # Implementação para interagir com a API do Mercado Livre
│   ├── db
│   │   ├── crud_depositos.py  # Funções CRUD para gerenciar depósitos
│   │   ├── crud_estoque.py    # Funções para gerenciar o estoque
│   │   ├── crud_produtos.py    # Funções CRUD para gerenciar produtos
│   │   ├── database.py         # Configuração da conexão com o banco de dados PostgreSQL
│   │   └── models.py          # Definição dos modelos de dados
│   ├── main.py                 # Ponto de entrada da aplicação Streamlit
│   └── utils.py                # Funções utilitárias
├── requirements.txt            # Dependências do projeto
└── README.md                   # Documentação do projeto
```

## Instalação
Para instalar as dependências do projeto, execute o seguinte comando:

```
pip install -r requirements.txt
```

## Uso
Para iniciar a aplicação, execute o seguinte comando:

```
streamlit run src/main.py
```

## Deploy no Streamlit Cloud
Para fazer o deploy da aplicação no Streamlit Cloud, siga os passos abaixo:

1. **Push seu código para o GitHub**: Crie um novo repositório no GitHub e faça o push dos arquivos do projeto.

2. **Configurar o Streamlit Cloud**: Acesse o Streamlit Cloud e faça login com sua conta do GitHub. Crie um novo app selecionando seu repositório.

3. **Configurar variáveis de ambiente**: Se sua aplicação requer strings de conexão com o banco de dados ou chaves de API, configure essas variáveis de ambiente nas configurações do Streamlit Cloud.

4. **Conexão com o banco de dados**: Certifique-se de que seu banco de dados PostgreSQL esteja acessível a partir do Streamlit Cloud. Você pode precisar configurar seu banco de dados para permitir conexões dos endereços IP do Streamlit Cloud.

5. **Deploy**: Após tudo configurado, você pode fazer o deploy da sua aplicação. O Streamlit Cloud instalará automaticamente as dependências listadas em `requirements.txt` e executará seu arquivo `main.py`.

## Contribuição
Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

## Licença
Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para mais detalhes.