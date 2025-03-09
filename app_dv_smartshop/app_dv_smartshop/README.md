# README.md

# DV SmartShop - Gestão Integrada de Estoque

Este projeto é uma aplicação web desenvolvida com Streamlit para gerenciar o estoque de produtos em depósitos, integrando dados de marketplaces como Amazon e Mercado Livre. A aplicação permite visualizar, registrar e transferir movimentações de estoque, além de gerenciar depósitos e produtos.

## Estrutura do Projeto

O projeto possui a seguinte estrutura de arquivos:

```
app_dv_smartshop
├── src
│   ├── api
│   │   ├── amazon.py          # Implementação da API para interagir com a Amazon
│   │   └── mercadolivre.py    # Implementação da API para interagir com o Mercado Livre
│   ├── db
│   │   ├── crud_depositos.py   # Funções para gerenciar depósitos no banco de dados
│   │   ├── crud_estoque.py     # Funções para gerenciar o estoque
│   │   ├── crud_produtos.py     # Funções para gerenciar produtos
│   │   ├── database.py          # Configuração da conexão com o banco de dados
│   │   └── models.py            # Definição dos modelos de dados
│   └── main.py                  # Ponto de entrada da aplicação Streamlit
├── requirements.txt              # Dependências do projeto
└── README.md                     # Documentação do projeto
```

## Instalação

1. Clone o repositório:
   ```
   git clone https://github.com/seu_usuario/app_dv_smartshop.git
   cd app_dv_smartshop
   ```

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

## Uso

Para iniciar a aplicação, execute o seguinte comando:
```
streamlit run src/main.py
```

A aplicação será iniciada em seu navegador padrão.

## Deploy no Streamlit Cloud

Para fazer o deploy da aplicação no Streamlit Cloud, siga os passos abaixo:

1. Crie um repositório no GitHub e faça o upload do projeto.
2. Verifique se o arquivo `requirements.txt` está correto.
3. Acesse sua conta no Streamlit Cloud e clique em "New App".
4. Selecione o repositório e o branch, e especifique o caminho do arquivo `src/main.py`.
5. Clique em "Deploy" e aguarde a conclusão.

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

## Licença

Este projeto está licenciado sob a MIT License. Veja o arquivo LICENSE para mais detalhes.