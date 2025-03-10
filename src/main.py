import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sys
import os
import logging

logging.basicConfig(level=logging.DEBUG)

# Configurações iniciais
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.mercadolivre import MercadoLivreAPI
from src.api.amazon import AmazonAPI
from src.db.database import get_session
from src.db.crud_depositos import criar_deposito, listar_depositos, atualizar_deposito, deletar_deposito
from src.db.crud_produtos import criar_produto, listar_produtos, atualizar_produto, deletar_produto

from src.db.crud_estoque import (
    registrar_movimentacao,
    transferir_estoque,
    consultar_estoque,
    consultar_historico_movimentacoes,
    consultar_saldo,
    atualizar_movimentacao,
    excluir_movimentacao
)

from src.db.models import Estoque, Deposito, Produto,TipoEstoque
from plotly.express.colors import qualitative
from sqlmodel import Session, select
from sqlalchemy import func, and_


st.cache_data.clear()
st.cache_resource.clear()

# Configuração da página
st.set_page_config(
    page_title="DV SmartShop - Gestão Integrada de Estoque",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Constantes
DATE_FORMAT = "%Y-%m-%d %H:%M"
COLOR_SCHEME = {
    'Mercado Livre (Full)': '#00B8A9',
    'Amazon (FBA)': '#FF6B6B',    
    'background': '#F8F9FA'
}


def gerar_paleta_depositos(depositos):
    """Gera cores únicas para cada depósito próprio"""
    cores_base = qualitative.Plotly + qualitative.D3 + qualitative.Light24
    return {dep.nome: cores_base[i % len(cores_base)] for i, dep in enumerate(depositos)}


def setup_environment():
    """Configuração visual do ambiente"""
    st.markdown(f"""
    <style>
        .metric-card {{
            background: {COLOR_SCHEME['background']};
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
        }}
        .stDataFrame {{ 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        .refresh-button {{
            background: #4CAF50 !important;
            color: white !important;
        }}
    </style>
    """, unsafe_allow_html=True)

def formatar_numero(valor):
    """
    Formata um número inteiro ou float para usar o ponto como separador de milhar.
    
    Args:
        valor (int ou float): O número a ser formatado.
    
    Returns:
        str: O número formatado como string.
    """
    try:
        if isinstance(valor, (int, float)):
            return f"{valor:,}".replace(",", ".")  # Substitui vírgula por ponto
        else:
            return str(valor)  # Retorna como string se não for numérico
    except Exception:
        return str(valor)  # Fallback para qualquer erro    


def carregar_estoque_interno():
    """
    Carrega os dados de estoque interno do banco de dados, incluindo informações dos depósitos próprios,
    considerando o saldo mais recente de cada SKU em cada depósito.
    
    Returns:
        pd.DataFrame: Um DataFrame contendo os dados de estoque interno, com colunas padronizadas.
    """
    try:
        with get_session() as db:
            # Subquery para encontrar a data/hora mais recente de cada SKU e depósito
            subquery = (
                select(Estoque.sku, Estoque.deposito_id, func.max(Estoque.data_hora).label("max_data_hora"))
                .group_by(Estoque.sku, Estoque.deposito_id)
                .subquery()
            )

            # Query principal para selecionar os registros mais recentes
            statement = (
                select(
                    Estoque,
                    Deposito.nome.label("Depósito"),
                    Produto.nome.label("Produto")
                )
                .join(Deposito, Estoque.deposito_id == Deposito.id)
                .join(Produto, Estoque.sku == Produto.sku)
                .join(subquery, and_(
                    Estoque.sku == subquery.c.sku,
                    Estoque.deposito_id == subquery.c.deposito_id,
                    Estoque.data_hora == subquery.c.max_data_hora
                ))
                .where(Deposito.tipo == "Próprio")  # Filtra apenas depósitos próprios
            )
            
            # Executa a consulta
            resultados = db.exec(statement).all()
            
            # Transforma os resultados em uma lista de dicionários
            estoque_lista = [
                {
                    "SKU": registro.Estoque.sku,
                    "Produto": registro.Produto,
                    "Depósito": registro.Depósito,
                    "Estoque": int(registro.Estoque.saldo)  # Garante formato inteiro e usa o saldo
                }
                for registro in resultados
            ]
            
            # Converte a lista para um DataFrame Pandas
            df_estoque = pd.DataFrame(estoque_lista)
            df_estoque = df_estoque[df_estoque["Estoque"] > 0]
            
            return df_estoque
    
    except Exception as e:
        print(f"Erro ao carregar estoque interno: {str(e)}")
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro


def criar_card_metrica(titulo, valor, ajuda=None):
    """Componente de métrica estilizado"""
    return f"""
    <div style="border: 1px solid #ddd; border-radius: 8px; padding: 16px; text-align: center; background-color: white;">
        <h3 style="color: black;">{titulo}</h3>
        <p style="font-size: 24px; font-weight: bold; color: black;">{valor}</p>
        {f'<p style="font-size: 12px; color: gray;">{ajuda}</p>' if ajuda else ''}
    </div>
    """

@st.cache_data(ttl=3600, show_spinner=False)
def carregar_dados_completos(_apis):
    """Combina estoque de marketplaces com estoque próprio"""
    # Dados externos
    dados_externos = []
    
    # Mercado Livre
    with st.spinner("Coletando Mercado Livre..."):
        try:
            ml_data = _apis['ml'].gerar_relatorio_estoque()
            if not ml_data.empty:
                ml_data.rename(columns={"Nome": "Produto"}, inplace=True)  # Padroniza nome da coluna
                ml_data['Depósito'] = 'Mercado Livre (Full)'
                dados_externos.append(ml_data)
        except Exception as e:
            st.error(f"Erro ML: {str(e)}")
    
    # Amazon
    with st.spinner("Coletando Amazon..."):
        try:
            amazon_data = _apis['amazon'].gerar_relatorio_estoque()
            if not amazon_data.empty:
                amazon_data.rename(columns={"Nome": "Produto"}, inplace=True)  # Padroniza nome da coluna
                amazon_data['Depósito'] = 'Amazon (FBA)'
                dados_externos.append(amazon_data)
        except Exception as e:
            st.error(f"Erro Amazon: {str(e)}")
    
    # Dados internos
    with st.spinner("Carregando estoque próprio..."):
        interno_df = carregar_estoque_interno()
    
    # Combinação
    externo_df = pd.concat(dados_externos, ignore_index=True) if dados_externos else pd.DataFrame()
    return pd.concat([externo_df, interno_df], ignore_index=True)


def exibir_visao_integrada(apis):
    """Dashboard principal com dados combinados"""
    st.title("📊 Visão Integrada de Estoque")
    st.caption(f"Última atualização: {datetime.now().strftime(DATE_FORMAT)}")
    
    # Inicializa o estado da sessão para controlar o carregamento inicial dos dados
    if 'dados_carregados' not in st.session_state:
        st.session_state.dados_carregados = False

    # Carregamento de dados
    if not st.session_state.dados_carregados or st.session_state.get('atualizar_dados', False):
        with st.spinner("Carregando dados..."):
            df_completo = carregar_dados_completos(apis)
            st.session_state.df_completo = df_completo  # Armazena o DataFrame no estado da sessão
            st.session_state.dados_carregados = True
            st.session_state.atualizar_dados = False  # Reseta o flag
    else:
        df_completo = st.session_state.df_completo  # Recupera o DataFrame do estado da sessão
        
    if df_completo.empty:
        st.warning("Nenhum dado disponível")
        return
    
    # Filtragem das colunas padronizadas
    df_completo = df_completo[['SKU', 'Produto', 'Depósito', 'Estoque']]
    
    # Filtros
    with st.sidebar:

        st.markdown("---")
        if st.button("🔄 Atualizar Dados", help="Recarregar todos os dados", use_container_width=True):
            carregar_dados_completos.clear() 
            st.session_state.atualizar_dados = True
            st.rerun()

        st.header("🔍 Filtros Avançados")
        filtro_deposito = st.multiselect(
            "Depósitos",
            options=df_completo['Depósito'].unique(),
            default=[]
        )
        
        filtro_sku = st.multiselect(
            "SKUs",
            options=df_completo['SKU'].unique(),
            default=[]
        )
    
    # Aplicar filtros
    df_filtrado = df_completo.copy()
    if filtro_deposito:
        df_filtrado = df_filtrado[df_filtrado['Depósito'].isin(filtro_deposito)]
    if filtro_sku:
        df_filtrado = df_filtrado[df_filtrado['SKU'].isin(filtro_sku)]


    # Métricas
    cols = st.columns(3)
    metricas = [
        ("Depósitos", df_filtrado['Depósito'].nunique(), "Total de locais"),
        ("SKUs Únicos", formatar_numero(df_filtrado['SKU'].nunique()), "Produtos diferentes"),
        ("Estoque Total", formatar_numero(df_filtrado['Estoque'].sum()), "Unidades totais")
    ]

    for col, (titulo, valor, ajuda) in zip(cols, metricas):
        col.markdown(criar_card_metrica(titulo, valor, ajuda), unsafe_allow_html=True)    

    
    # Visualizações
    st.markdown("---")
    visao_selecionada = st.radio(
        "Tipo de Visualização:",
        ["📈 Por SKU", "📊 Distribuição", "🗃️ Dados Brutos"],
        horizontal=True,
        label_visibility="collapsed"
    )

    # Gerar paleta dinâmica
    depositos_proprios = [dep for dep in df_completo['Depósito'].unique() if dep not in ['Mercado Livre (Full)', 'Amazon (FBA)']]
    paleta_dinamica = {
        dep: cor for dep, cor in gerar_paleta_depositos([type('obj', (object,), {'nome': dep}) for dep in depositos_proprios]).items()
    }
    paleta_dinamica.update(COLOR_SCHEME)  # Mantém cores fixas para marketplaces

    
    if visao_selecionada == "📈 Por SKU":
        # Agrupar os dados por SKU e Depósito
        df_grouped = df_filtrado.groupby(['SKU', 'Depósito'])['Estoque'].sum().reset_index()

        # Ordena os dados por estoque em ordem decrescente
        df_grouped = df_grouped.sort_values(by='Estoque', ascending=False)

        fig = px.bar(
            df_grouped,
            x='SKU',
            y='Estoque',
            color='Depósito',
            color_discrete_map=paleta_dinamica,
            barmode='group',
            height=600,
            text_auto=True,
            labels={'Estoque': 'Quantidade em Estoque', 'SKU': 'SKU do Produto'} # Melhora os rótulos
        )

        fig.update_layout(
            xaxis_title="SKU do Produto",
            yaxis_title="Quantidade em Estoque",
            title="Distribuição de Estoque por SKU",
            xaxis={'categoryorder':'total descending'}, # Ordena por valor total
            xaxis_tickangle=-45  # Rotaciona os rótulos do eixo X para melhor legibilidade
        )

        st.plotly_chart(fig, use_container_width=True)
    
    elif visao_selecionada == "📊 Distribuição":
        fig = px.pie(
            df_filtrado.groupby('Depósito')['Estoque'].sum().reset_index(),
            names='Depósito',
            values='Estoque',
            color='Depósito',
            color_discrete_map=paleta_dinamica
        )
        st.plotly_chart(fig, use_container_width=True)
        

    else:
        # Garante que a coluna 'Estoque' seja numérica
        df_filtrado['Estoque'] = pd.to_numeric(df_filtrado['Estoque'], errors='coerce')
        
        # Ordena os dados por estoque em ordem decrescente
        df_filtrado = df_filtrado.sort_values(by='Estoque', ascending=False)
        
        # Define a formatação personalizada para a coluna 'Estoque'
        st.dataframe(
            df_filtrado,
            column_config={
                "Estoque": st.column_config.NumberColumn(
                    "Estoque",
                    format="%d",  # Formato inteiro com separador de milhar
                ),
            },
            use_container_width=True,
            height=600
        )

def exibir_gestao_depositos():
    st.header("🏭 Gestão de Depósitos")

    # Função auxiliar para carregar depósitos
    def carregar_depositos():
        try:
            return listar_depositos()
        except Exception as e:
            st.error(f"Erro ao carregar depósitos: {str(e)}")
            return []

    # Carregar depósitos existentes
    depositos = carregar_depositos()

    # Exibir mensagens de sucesso, se houver
    if getattr(st.session_state, "mensagem_sucesso", None):
        # Exibe a mensagem como um toast
        st.toast(st.session_state.mensagem_sucesso, icon="✅")
        del st.session_state.mensagem_sucesso  # Limpa a mensagem após exibi-la

    # Formulário para criar novo depósito
    with st.expander("➕ Novo Depósito", expanded=True):
        with st.form("form_deposito", clear_on_submit=True):
            nome = st.text_input("Nome do Depósito*", max_chars=100)
            tipo = st.selectbox("Tipo*", ["Próprio", "Temporário"])
            observacoes = st.text_area("Observações", max_chars=200)

            if st.form_submit_button("💾 Salvar"):
                if not nome:
                    st.error("Nome é obrigatório")
                else:
                    try:
                        criar_deposito(nome, tipo, observacoes)
                        st.session_state.mensagem_sucesso = "Depósito criado com sucesso!"  # Armazena mensagem
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Erro ao criar depósito: {str(e)}")

    # Exibição dos depósitos cadastrados
    st.markdown("---")
    st.subheader("Depósitos Cadastrados")

    if not depositos:
        st.info("Nenhum depósito cadastrado")
    else:
        for idx, deposito in enumerate(depositos):
            #st.markdown(f"**Depósito ID: {deposito.id}**")
            with st.expander(deposito.nome, expanded=False):  # Sempre colapsado inicialmente
                novo_nome = st.text_input("Nome", value=deposito.nome, key=f"nome_{deposito.id}")
                novo_tipo = st.selectbox(
                    "Tipo",
                    ["Próprio", "Temporário"],
                    index=0 if deposito.tipo == "Próprio" else 1,
                    key=f"tipo_{deposito.id}"
                )
                novas_observacoes = st.text_area("Observações", value=deposito.observacoes or "", key=f"obs_{deposito.id}")

                # Layout para botões "Salvar" e "Excluir"
                cols = st.columns([1, 1, 20])  # Colunas para os botões

                # Botão Salvar
                if cols[0].button("💾 Salvar", key=f"salvar_{deposito.id}"):
                    try:
                        atualizar_deposito(
                            deposito_id=deposito.id,
                            novo_nome=novo_nome,
                            novo_tipo=novo_tipo,
                            novas_observacoes=novas_observacoes,
                        )
                        st.session_state.mensagem_sucesso = "Registro alterado com sucesso!"  # Armazena mensagem
                        st.rerun()  # Recarrega a página para colapsar todos os expanders
                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Erro ao atualizar depósito: {str(e)}")

                # Botão Excluir
                if cols[1].button("❌ Excluir", key=f"excluir_{deposito.id}"):
                    # Armazena o ID do depósito a ser excluído no session_state
                    st.session_state.deposito_para_excluir = deposito.id

            # Verifica se há um depósito marcado para exclusão
            if getattr(st.session_state, "deposito_para_excluir", None) == deposito.id:
                confirmacao = st.warning(f"Confirma a exclusão do depósito '{deposito.nome}'?")
                col_confirmacao = st.columns([1, 1, 20])

                # Botão "Sim, excluir"
                if col_confirmacao[0].button("Sim, excluir", key=f"confirmar_exclusao_{deposito.id}"):
                    try:
                        deletar_deposito(deposito.id)  # Chama a função de exclusão
                        st.session_state.mensagem_sucesso = f"Depósito '{deposito.nome}' excluído com sucesso!"  # Armazena mensagem
                        del st.session_state.deposito_para_excluir  # Remove o estado de confirmação
                        st.rerun()  # Recarrega a página para colapsar todos os expanders
                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Erro ao excluir depósito: {str(e)}")

                # Botão "Cancelar"
                if col_confirmacao[1].button("Cancelar", key=f"cancelar_exclusao_{deposito.id}"):
                    # Não exibe mensagem de "Exclusão cancelada"
                    del st.session_state.deposito_para_excluir  # Remove o estado de confirmação
                    st.rerun()  # Recarrega a página para colapsar todos os expanders


def exibir_gestao_produtos():
    st.header("📦 Gestão de Produtos")

    # Função auxiliar para carregar produtos
    def carregar_produtos(filtro: str = None):
        try:
            return listar_produtos(filtro=filtro)
        except Exception as e:
            st.error(f"Erro ao carregar produtos: {str(e)}")
            return []

    # Exibir mensagens de sucesso, se houver
    if getattr(st.session_state, "mensagem_sucesso", None):
        # Exibe a mensagem como um toast
        st.toast(st.session_state.mensagem_sucesso, icon="✅")
        del st.session_state.mensagem_sucesso  # Limpa a mensagem após exibi-la

    # Campo de filtro
    filtro = st.text_input("🔍 Filtrar produtos por nome ou SKU:")
    produtos = carregar_produtos(filtro=filtro)

    # Formulário para criar novo produto
    with st.expander("➕ Novo Produto", expanded=True):
        with st.form("form_produto", clear_on_submit=True):
            sku = st.text_input("SKU*", max_chars=50)
            nome = st.text_input("Nome do Produto*", max_chars=100)
            descricao = st.text_area("Descrição", max_chars=200)

            if st.form_submit_button("Salvar"):
                if not sku or not nome:
                    st.error("SKU e Nome são obrigatórios")
                else:
                    try:
                        criar_produto(sku, nome, descricao)
                        st.session_state.mensagem_sucesso = "Produto criado com sucesso!"  # Armazena mensagem
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Erro ao criar produto: {str(e)}")

    # Exibição dos produtos cadastrados
    st.markdown("---")
    st.subheader("Produtos Cadastrados")

    if not produtos:
        st.info("Nenhum produto cadastrado")
    else:
        for idx, produto in enumerate(produtos):
            #st.markdown(f"**Produto SKU: {produto.sku}**")
            with st.expander(produto.nome, expanded=False):  # Sempre colapsado inicialmente
                novo_sku = st.text_input("SKU", value=produto.sku, disabled=True, key=f"sku_{produto.sku}")
                novo_nome = st.text_input("Nome", value=produto.nome, key=f"nome_{produto.sku}")
                nova_descricao = st.text_area("Descrição", value=produto.descricao or "", key=f"desc_{produto.sku}")

                # Layout para botões "Salvar" e "Excluir"
                cols = st.columns([1, 1, 20])  # Colunas para os botões

                # Botão Salvar
                if cols[0].button("💾 Salvar", key=f"salvar_{produto.sku}"):
                    try:
                        atualizar_produto(
                            sku=produto.sku,
                            novo_nome=novo_nome,
                            nova_descricao=nova_descricao,
                        )
                        st.session_state.mensagem_sucesso = "Produto alterado com sucesso!"  # Armazena mensagem
                        st.rerun()  # Recarrega a página para colapsar todos os expanders
                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Erro ao atualizar produto: {str(e)}")

                # Botão Excluir
                if cols[1].button("❌ Excluir", key=f"excluir_{produto.sku}"):
                    # Armazena o SKU do produto a ser excluído no session_state
                    st.session_state.produto_para_excluir = produto.sku

            # Verifica se há um produto marcado para exclusão
            if getattr(st.session_state, "produto_para_excluir", None) == produto.sku:
                confirmacao = st.warning(f"Confirma a exclusão do produto '{produto.nome}' (SKU: {produto.sku})?")
                col_confirmacao = st.columns([1, 1, 20])

                # Botão "Sim, excluir"
                if col_confirmacao[0].button("Sim, excluir", key=f"confirmar_exclusao_{produto.sku}"):
                    try:
                        deletar_produto(produto.sku)  # Chama a função de exclusão
                        st.session_state.mensagem_sucesso = f"Produto '{produto.nome}' excluído com sucesso!"  # Armazena mensagem
                        del st.session_state.produto_para_excluir  # Remove o estado de confirmação
                        st.rerun()  # Recarrega a página para colapsar todos os expanders
                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Erro ao excluir produto: {str(e)}")

                # Botão "Cancelar"
                if col_confirmacao[1].button("Cancelar", key=f"cancelar_exclusao_{produto.sku}"):
                    # Não exibe mensagem de "Exclusão cancelada"
                    del st.session_state.produto_para_excluir  # Remove o estado de confirmação
                    st.rerun()  # Recarrega a página para colapsar todos os expanders

  

def exibir_gestao_estoque():
    st.header("📦 Gestão de Estoque")

    # Funções auxiliares para carregar dados
    def carregar_depositos():
        try:
            return listar_depositos()
        except Exception as e:
            st.error(f"Erro ao carregar depósitos: {str(e)}")
            return []

    def carregar_produtos():
        try:
            return listar_produtos()
        except Exception as e:
            st.error(f"Erro ao carregar produtos: {str(e)}")
            return []

    # Exibir mensagens de sucesso, se houver
    if getattr(st.session_state, "mensagem_sucesso", None):
        # Exibe a mensagem como um toast
        st.toast(st.session_state.mensagem_sucesso, icon="✅")
        del st.session_state.mensagem_sucesso  # Limpa a mensagem após exibi-la

    # Menu lateral para navegar entre as funcionalidades
    menu_opcao = st.sidebar.selectbox(
        "Selecione uma operação",
        ["Registrar Movimentação", "Transferir Estoque", "Consultar Estoque", "Histórico de Movimentações"],
    )

    depositos = carregar_depositos()
    produtos = carregar_produtos()

    if not depositos:
        st.warning("Nenhum depósito cadastrado. Cadastre depósitos antes de gerenciar estoque.")
        return

    if not produtos:
        st.warning("Nenhum produto cadastrado. Cadastre produtos antes de gerenciar estoque.")
        return

    # Mapeamento de depósitos e produtos para seleção
    deposito_map = {d.nome: d.id for d in depositos}
    produto_map = {p.nome: p.sku for p in produtos}

    if menu_opcao == "Registrar Movimentação":
        st.subheader("📝 Registrar Movimentação de Estoque")
        if 'etapa' not in st.session_state or st.session_state.get('menu_opcao_anterior') != menu_opcao:
            st.session_state.etapa = 1
            st.session_state.produtos_selecionados = []
            st.session_state.deposito_nome = list(deposito_map.keys())[0]
            st.session_state.tipo = [e.value for e in TipoEstoque][0]
            st.session_state.menu_opcao_anterior = menu_opcao

        if st.session_state.etapa == 1:
            deposito_nome_default = st.session_state.deposito_nome
            tipo_default = st.session_state.tipo

            with st.form("form_selecao", clear_on_submit=False):
                produtos_selecionados = st.multiselect("Produtos*", options=list(produto_map.keys()), default=st.session_state.produtos_selecionados)
                deposito_nome = st.selectbox("Depósito*", options=list(deposito_map.keys()), index=list(deposito_map.keys()).index(deposito_nome_default))
                tipo = st.selectbox("Tipo*", [e.value for e in TipoEstoque], index=[e.value for e in TipoEstoque].index(tipo_default))
                if st.form_submit_button("Próxima Etapa"):
                    if not produtos_selecionados or not deposito_nome or not tipo:
                        st.error("Todos os campos são obrigatórios.")
                    else:
                        st.session_state.produtos_selecionados = produtos_selecionados
                        st.session_state.deposito_nome = deposito_nome
                        st.session_state.tipo = tipo
                        st.session_state.etapa = 2
                        st.rerun()

        elif st.session_state.etapa == 2:            
            st.write("")
            st.write(f"**Depósito:** {st.session_state.deposito_nome}")
            st.write(f"**Tipo:** {st.session_state.tipo}")
            st.write("### Produtos Selecionados")

            with st.form("form_quantidades", clear_on_submit=False):
                quantidades = {}
                observacoes = {}
                for produto_nome in st.session_state.produtos_selecionados:
                    sku = produto_map[produto_nome]
                    deposito_id = deposito_map[st.session_state.deposito_nome]
                    saldo_atual = consultar_saldo(sku, deposito_id)  # Função a ser implementada
                    #st.write(f"**{produto_nome} - Saldo atual: {saldo_atual}**")
                    st.markdown(f"{produto_nome} - Saldo atual (Origem): <span style='color:green; font-weight:bold;'>{saldo_atual}</span>", unsafe_allow_html=True)
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        quantidades[produto_nome] = st.number_input(f"Quantidade*", step=1, min_value=1, max_value=100000, key=f"quantidade_{produto_nome}")
                    with col2:
                        observacoes[produto_nome] = st.text_input(f"Observações", key=f"observacoes_{produto_nome}")

                col1, col2, col3 = st.columns([1,1,10])
                with col1:
                    if st.form_submit_button("💾 Salvar"):
                        deposito_id = deposito_map[st.session_state.deposito_nome]
                        tipo = st.session_state.tipo
                        sucesso = True  # Variável para controlar o sucesso das movimentações
                        for produto_nome in st.session_state.produtos_selecionados:
                            sku = produto_map[produto_nome]
                            quantidade = quantidades[produto_nome]
                            observacao = observacoes[produto_nome]
                            if quantidade == 0:
                                st.error(f"A quantidade para {produto_nome} não pode ser zero.")
                                sucesso = False
                            else:
                                try:
                                    registrar_movimentacao(sku, deposito_id, quantidade, tipo, observacao)
                                except ValueError as e:
                                    st.error(str(e))
                                    sucesso = False
                                except Exception as e:
                                    st.error(f"Erro ao registrar movimentação para {produto_nome}: {str(e)}")
                                    sucesso = False
                        if sucesso:
                            st.session_state.mensagem_sucesso = "Movimentações registradas com sucesso!"
                            st.session_state.etapa = 1
                            st.rerun()
                with col2:
                    if st.form_submit_button("↩  Voltar"):
                        st.session_state.etapa = 1
                        st.rerun()
                #with col3:
                #    if st.form_submit_button("Limpar Campos"):
                #        st.session_state.etapa = 1
                #        st.session_state.produtos_selecionados = []
                #        st.session_state.deposito_nome = list(deposito_map.keys())[0]
                #        st.session_state.tipo = [e.value for e in TipoEstoque][0]
                #        st.rerun()    

    elif menu_opcao == "Transferir Estoque":
        st.subheader("🔄 Transferir Estoque entre Depósitos")

        if 'etapa' not in st.session_state or st.session_state.get('menu_opcao_anterior') != menu_opcao:
            st.session_state.etapa = 1
            st.session_state.produtos_selecionados = []
            st.session_state.origem_nome = list(deposito_map.keys())[0]
            st.session_state.destino_nome = list(deposito_map.keys())[0]  # Inicializa com o primeiro depósito
            st.session_state.menu_opcao_anterior = menu_opcao

        if st.session_state.etapa == 1:
            origem_nome_default = st.session_state.origem_nome
            destino_nome_default = st.session_state.destino_nome

            st.write("Selecione o(s) produto(s) e os depósitos de origem e destino")

            origem_nome = st.selectbox("Origem*", options=list(deposito_map.keys()),
                                        index=list(deposito_map.keys()).index(origem_nome_default),
                                        key="origem_select")

            # Obtenha o ID do depósito de origem selecionado
            origem_id = deposito_map[origem_nome]

            # Filtre os produtos que têm saldo maior que zero no depósito de origem
            produtos_disponiveis = []
            for produto_nome, sku in produto_map.items():
                saldo = consultar_saldo(sku, origem_id)
                if saldo > 0:
                    produtos_disponiveis.append(produto_nome)
                    
            if not produtos_disponiveis:
                st.warning("Não há produtos com saldo disponível neste depósito.")
            else:
                produtos_selecionados = st.multiselect("Produtos*", options=produtos_disponiveis,
                                                        default=[],
                                                        key="produtos_multiselect",
                                                        placeholder="Selecione os produtos para transferência"
                                                      )
                                    

            destino_nome = st.selectbox("Destino*", options=list(deposito_map.keys()),
                                        index=list(deposito_map.keys()).index(destino_nome_default),
                                        key="destino_select"
                                        )  # Exibe todos os depósitos

            if st.button("Próxima Etapa"):
                if not produtos_selecionados and produtos_disponiveis:
                    st.error("Selecione ao menos um produto para transferir.")
                elif not origem_nome or not destino_nome:
                    st.error("Todos os campos são obrigatórios.")
                elif origem_nome == destino_nome:
                    st.error("Os depósitos de origem e destino devem ser diferentes.")
                else:
                    st.session_state.produtos_selecionados = produtos_selecionados
                    st.session_state.origem_nome = origem_nome
                    st.session_state.destino_nome = destino_nome
                    st.session_state.etapa = 2
                    st.rerun()


        elif st.session_state.etapa == 2:
            st.write("")
            st.write(f"**Origem:** {st.session_state.origem_nome}")
            st.write(f"**Destino:** {st.session_state.destino_nome}")
            st.write("### Produtos Selecionados")
            

            with st.form("form_quantidades_transferencia", clear_on_submit=False):
                quantidades = {}
                observacoes = {}
                for produto_nome in st.session_state.produtos_selecionados:
                    sku = produto_map[produto_nome]
                    origem_id = deposito_map[st.session_state.origem_nome]
                    saldo_atual = consultar_saldo(sku, origem_id)  # Obtém o saldo da origem
                    #st.write(f"**{produto_nome} - Saldo atual (Origem): {saldo_atual}**")
                    st.markdown(f"{produto_nome} - Saldo atual (Origem): <span style='color:green; font-weight:bold;'>{saldo_atual}</span>", unsafe_allow_html=True)
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        # Garante que a quantidade não seja maior que o saldo atual
                        max_value = min(100000, saldo_atual)
                        quantidades[produto_nome] = st.number_input(f"Quantidade*", step=1, min_value=1, max_value=max_value, key=f"quantidade_{produto_nome}")
                        if quantidades[produto_nome] > saldo_atual:
                            st.error(f"A quantidade para {produto_nome} não pode ser maior que o saldo atual ({saldo_atual}).")
                    with col2:
                        observacoes[produto_nome] = st.text_input(f"Observações", key=f"observacoes_{produto_nome}", value=f"Transferência: {st.session_state.origem_nome} para {st.session_state.destino_nome} - Coleta FULL")
                    st.markdown("---")    

                col1, col2, col3 = st.columns([1,1,10])
                with col1:
                    if st.form_submit_button("✅ Transferir"):
                        origem_id = deposito_map[st.session_state.origem_nome]
                        destino_id = deposito_map[st.session_state.destino_nome]
                        sucesso = True
                        for produto_nome in st.session_state.produtos_selecionados:
                            sku = produto_map[produto_nome]
                            quantidade = quantidades[produto_nome]
                            observacao = observacoes[produto_nome]
                            if quantidade == 0:
                                st.error(f"A quantidade para {produto_nome} não pode ser zero.")
                                sucesso = False
                            elif quantidade > saldo_atual:
                                st.error(f"A quantidade para {produto_nome} não pode ser maior que o saldo atual ({saldo_atual}).")
                                sucesso = False
                            else:
                                try:
                                    transferir_estoque(sku, origem_id, destino_id, quantidade, observacao)
                                except ValueError as e:
                                    st.error(str(e))
                                    sucesso = False
                                except Exception as e:
                                    st.error(f"Erro ao transferir estoque para {produto_nome}: {str(e)}")
                                    sucesso = False
                        if sucesso:
                            st.session_state.mensagem_sucesso = "Transferências realizadas com sucesso!"
                            st.session_state.etapa = 1
                            st.rerun()
                with col2:
                    if st.form_submit_button("↩  Voltar"):
                        st.session_state.etapa = 1
                        st.rerun()
                #with col3:
                #    if st.form_submit_button("Limpar Campos"):
                #        st.session_state.etapa = 1
                #        st.session_state.produtos_selecionados = []
                #        st.session_state.origem_nome = list(deposito_map.keys())[0]
                #        st.session_state.destino_nome = [d for d in deposito_map.keys() if d != st.session_state.origem_nome][0]
                #        st.rerun()

    elif menu_opcao == "Consultar Estoque":
        st.subheader("🔍 Consultar Estoque Próprio")
        produto_nome = st.selectbox("Produto", options=["Todos"] + list(produto_map.keys()))
        deposito_nome = st.selectbox("Depósito", options=["Todos"] + list(deposito_map.keys()))

        if st.button("Consultar"):
            sku = produto_map[produto_nome] if produto_nome != "Todos" else None
            deposito_id = deposito_map[deposito_nome] if deposito_nome != "Todos" else None

            try:
                total, detalhado = consultar_estoque(sku, deposito_id)

                if detalhado:
                    # Exibir tabela com todos os registros
                    df = pd.DataFrame(detalhado)
                    if not df.empty:
                        df.columns = ["Depósito", "SKU", "Nome do Produto", "Quantidade"]

                        # Filtrar para manter apenas registros com quantidade > 0
                        df = df[df["Quantidade"] > 0]

                        # Ordenar o DataFrame
                        df = df.sort_values(by=["Depósito", "Quantidade"], ascending=[True, False])

                        st.table(df)
                    else:
                        st.info("Nenhum registro encontrado.")
                else:
                    st.info("Nenhum registro encontrado.")
            except Exception as e:
                st.error(f"Erro ao consultar estoque: {str(e)}")

    

    elif menu_opcao == "Histórico de Movimentações":


        def init_session_state():
            if 'historico' not in st.session_state:
                st.session_state.historico = None
            if 'filtros' not in st.session_state:
                st.session_state.filtros = {
                    'produto': "Todos",
                    'deposito': "Todos",
                    'data_inicio': None,
                    'data_fim': None
                }
            if 'confirmar_exclusao' not in st.session_state:
                st.session_state.confirmar_exclusao = None

        def exibir_titulos():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 2, 1, 1, 0.7, 2, 0.7], border=True)
            col1.markdown("**Produto**")
            col2.markdown("**Depósito**")
            col3.markdown("**Tipo**")
            col4.markdown("**Data/Hora**")
            col5.markdown("**Quantidade**")
            col6.markdown("**Observações**")
            col7.markdown("**Ação**")

        def exibir_linha(row):
            
            col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 2, 1, 1, 0.7, 2, 0.7])

            col1.write(row['Produto'])
            col2.write(row['Depósito'])
            col3.write(row['Tipo'])
            col4.write(row['Data/Hora'])
            #col5.write(row['quantidade'])            

            def format_number(value):
                return f'<div style="text-align: center; color: #0e9f6e; font-family: monospace;">{pd.to_numeric(value):,.0f}</div>'

            col5.markdown(format_number(row['quantidade']), unsafe_allow_html=True)

            col6.write(row['observacoes'] or "")
            
            with col7:
                # Exibir o botão de exclusão, mas ocultar outros botões até a confirmação
                if st.session_state.confirmar_exclusao != row['id']:
                    if st.button("❌ Excluir", key=f"excluir_{row['id']}", use_container_width=True):
                        st.session_state.confirmar_exclusao = row['id']
                        st.rerun()
                else:
                    st.warning("Confirma a exclusão do lançamento?")
                    sim, nao = st.columns(2)
                    with sim:
                        if st.button("Sim", key=f"confirma_sim_{row['id']}"):
                            try:
                                excluir_movimentacao(row['id'])                                
                                st.success("Lançamento excluído com sucesso!")
                                st.session_state.confirmar_exclusao = None
                                st.session_state.historico = None  # Força o recarregamento do histórico
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao excluir lançamento: {str(e)}")
                    with nao:
                        if st.button("Não", key=f"confirma_nao_{row['id']}"):
                            st.session_state.confirmar_exclusao = None
                            st.rerun()

        def carregar_historico(sku, deposito_id, data_inicio, data_fim):
            historico = consultar_historico_movimentacoes(sku, deposito_id, data_inicio, data_fim)
            if historico and isinstance(historico, list):
                df = pd.DataFrame(historico)
                df['Data/Hora'] = pd.to_datetime(df['data_hora']).dt.strftime("%d/%m/%Y %H:%M:%S")
                df['Depósito'] = df['deposito_id'].apply(lambda id: next((d.nome for d in depositos if d.id == id), "Desconhecido"))
                df['Produto'] = df['sku'].apply(lambda sku: next((p.nome for p in produtos if p.sku == sku), "Desconhecido"))
                df['Tipo'] = df['tipo'].apply(lambda tipo: tipo.value if hasattr(tipo, 'value') else tipo)
                return df
            return None

        init_session_state()
        st.subheader("📋 Histórico de Movimentações")
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.filtros['produto'] = st.selectbox("Produto", options=["Todos"] + list(produto_map.keys()), key="produto_select")
        with col2:
            st.session_state.filtros['deposito'] = st.selectbox("Depósito", options=["Todos"] + list(deposito_map.keys()), key="deposito_select")
        
        col3, col4 = st.columns(2)
        with col3:
            st.session_state.filtros['data_inicio'] = st.date_input("Data Início", value=st.session_state.filtros['data_inicio'], key="data_inicio_input")
        with col4:
            st.session_state.filtros['data_fim'] = st.date_input("Data Fim", value=st.session_state.filtros['data_fim'], key="data_fim_input")

        if st.button("Consultar Histórico") or st.session_state.historico is not None:
            sku = produto_map.get(st.session_state.filtros['produto']) if st.session_state.filtros['produto'] != "Todos" else None
            deposito_id = deposito_map.get(st.session_state.filtros['deposito']) if st.session_state.filtros['deposito'] != "Todos" else None
            data_inicio = datetime.combine(st.session_state.filtros['data_inicio'], datetime.min.time()) if st.session_state.filtros['data_inicio'] else None
            data_fim = datetime.combine(st.session_state.filtros['data_fim'], datetime.max.time()) if st.session_state.filtros['data_fim'] else None

            st.session_state.historico = carregar_historico(sku, deposito_id, data_inicio, data_fim)

            if st.session_state.historico is not None:
                exibir_titulos()
                for _, row in st.session_state.historico.iterrows():
                    exibir_linha(row)                    
            else:
                st.info("Nenhuma movimentação encontrada.")

    

def main():
    setup_environment()
    
    # Menu principal
    with st.sidebar:
        st.header("📦 Menu Principal")
        opcao = st.radio(
            "Selecione o módulo:",
            ["Dashboard - Visão Integrada de Estoque", "Gestão Estoque Próprio"],
            index=0
        )

        if opcao == "Gestão Estoque Próprio":
            opcao_gestao = st.radio(
                "Selecione a opção:",
                ["Depósitos", "Produtos", "Estoque"],
                index=0
            )
        
        #st.markdown("---")
        #if st.button("🔄 Atualizar Dados", help="Recarregar todos os dados", use_container_width=True):
        #    carregar_dados_completos.clear()
        #    st.rerun()
    
    # Controle de exibição
    if opcao == "Dashboard - Visão Integrada de Estoque":
        apis = {
            'ml': MercadoLivreAPI(),
            'amazon': AmazonAPI()
        }
        exibir_visao_integrada(apis)
    elif opcao == "Gestão Estoque Próprio":
        if opcao_gestao == "Depósitos":
            exibir_gestao_depositos()
        elif opcao_gestao == "Produtos":
            exibir_gestao_produtos()
        elif opcao_gestao == "Estoque":
            exibir_gestao_estoque()     

if __name__ == "__main__":
    main()