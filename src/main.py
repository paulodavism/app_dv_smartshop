import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sys
import os
import logging
from functools import _lru_cache_wrapper
import gc
import time
import pytz

logging.basicConfig(level=logging.DEBUG)

# Configurações iniciais
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.mercadolivre import MercadoLivreAPI
from src.api.amazon import AmazonAPI
from src.api.mercos import MercosWebScraping

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
    'Mercado Livre (Full)': '#FFFF00',#'#00B8A9',
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
    Carrega os dados de estoque interno do arquivo conciliado do mercos
    
    Returns:
        pd.DataFrame: Um DataFrame contendo os dados de estoque interno, com colunas padronizadas.
    """
    try:                            
        df_mercos = pd.read_csv("produtos_mercos.csv")
        df_mercos_conciliado = pd.read_csv("produtos_mercos_conciliados.csv")         
                                        
        # 1. Filtrar linhas onde 'sku_ml_amazon' está preenchida
        df_filtrado = df_mercos_conciliado[df_mercos_conciliado['sku_ml_amazon'].notna() & (df_mercos_conciliado['sku_ml_amazon'] != '')].copy()

        # 2. Padronizar nomes das colunas
        df_filtrado.rename(columns={'sku_ml_amazon': 'SKU',
                                    'produto': 'Produto',
                                    'deposito_mercos': 'Depósito',
                                    'estoque_mercos': 'Estoque'}, inplace=True)
                
        # 3. Verificar se houve atualização de estoque
        for index_mercos, reg_mercos in df_mercos.iterrows():
            for index_conciliado, reg_conciliado in df_filtrado.iterrows():
                if reg_mercos['SKU'] == reg_conciliado['sku_mercos']:
                    if reg_mercos['Estoque'] != reg_conciliado['Estoque']:
                        df_filtrado.loc[index_conciliado, 'Estoque'] = reg_mercos['Estoque']
                        print(f"Estoque do produto {reg_conciliado['Produto']} atualizado de {reg_conciliado['Estoque']} para {reg_mercos['Estoque']}.", flush=True)                        
                         
        # 4. Selecionar apenas as colunas desejadas
        df_estoque = df_filtrado[['SKU', 'Produto', 'Depósito', 'Estoque']]
                            
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
                
                #Dados do ML como referência para conciliação com Mercos                
                ml_data.to_csv("skus_mercado_livre_amazon.csv", index=False)

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
        if st.button("🔄 Atualizar Dados", help="Atualizar dados de todos os depósitos", use_container_width=True):
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
            height=1200
        )

def limpar_cache():
    
    for obj in gc.get_objects():
        if isinstance(obj, _lru_cache_wrapper):
            obj.cache_clear()

def reset_estado_estoque():
    """Reseta as variáveis de estado da tela de Gestão de Estoque."""
    for key in ['etapa', 'produtos_selecionados', 'deposito_nome', 'tipo', 'origem_nome', 'destino_nome']:
        if key in st.session_state:
            del st.session_state[key]


def exibir_gestao_estoque():
    st.header("📦 Gestão de Estoque")

    
    # Exibir mensagens de sucesso, se houver
    if getattr(st.session_state, "mensagem_sucesso", None):
        # Exibe a mensagem como um toast
        st.toast(st.session_state.mensagem_sucesso, icon="✅")
        del st.session_state.mensagem_sucesso  # Limpa a mensagem após exibi-la

    # Menu lateral para navegar entre as funcionalidades
    menu_opcao = st.sidebar.selectbox(
        "Selecione uma operação",
        ["Consultar Estoque Próprio" , "Conciliar SKUs"],
    )

    # Verifica se o menu foi alterado e reseta o estado 
    if st.session_state.get('menu_opcao_anterior') != menu_opcao:
        reset_estado_estoque()
        # Reseta o histórico, forçando a tela do histórico a ficar limpa
        if 'historico' in st.session_state:
            del st.session_state['historico']
        st.session_state.menu_opcao_anterior = menu_opcao
    
    def atualizar_dados_mercos():
        mercos_rasp = MercosWebScraping()        

        return mercos_rasp.carrega_dados_mercos()
    

    def exibir_tabela_mercos():

        df_estoque_mercos = pd.read_csv("produtos_mercos.csv")        
        #st.table(df_estoque_mercos)

        # Garante que a coluna 'Estoque' seja numérica
        df_estoque_mercos['Estoque'] = pd.to_numeric(df_estoque_mercos['Estoque'], errors='coerce')
        
        # Ordena os dados por estoque em ordem decrescente
        df_estoque_mercos = df_estoque_mercos.sort_values(by='Estoque', ascending=False)
        
        # Define a formatação personalizada para a coluna 'Estoque'
        st.dataframe(
            df_estoque_mercos,
            column_config={
                "Estoque": st.column_config.NumberColumn(
                    "Estoque",
                    format="%d",  # Formato inteiro com separador de milhar
                ),
            },
            use_container_width=True,
            height=600
        )
        
            
    if menu_opcao == "Consultar Estoque Próprio":
        st.subheader("🔍 Consultar Estoque Próprio (Mercos)")                
        
        try:
            filepath = "produtos_mercos.csv"
            timezone = pytz.timezone('America/Sao_Paulo')
            last_modified_timestamp = os.path.getmtime(filepath)
            last_modified_datetime = datetime.fromtimestamp(last_modified_timestamp, tz=timezone)
            st.info(f"Última atualização: {last_modified_datetime.strftime('%d/%m/%Y %H:%M')}")
        except FileNotFoundError:
            st.info("Arquivo 'produtos_mercos.csv' não encontrado.")
        except Exception as e:
            st.error(f"Erro ao obter a data da última atualização: {e}")


        st.markdown("---")

        # Inicializa o estado da sessão
        if "confirmacao_ativa" not in st.session_state:
            st.session_state.confirmacao_ativa = False

        # Botão principal para iniciar o processo de atualização
        if st.button("🔄 Atualizar Dados", help="Obter dados do sistema Mercos"):
            st.session_state.confirmacao_ativa = True

        # Exibe a mensagem de confirmação se a flag estiver ativa
        if st.session_state.confirmacao_ativa:
            # Cria um containers temporário para a mensagem e os botões
            confirm_container = st.empty()
            
            with confirm_container.container():
                st.warning("Atenção! Este processo pode levar alguns minutos. Confirma a operação?")
                # Layout horizontal para os botões "Sim" e "Não"
                col1, col2 = st.columns([1, 25])
                confirmar = col1.button("Sim", key="confirmar_atualizacao")
                cancelar = col2.button("Não", key="cancelar_atualizacao")
            
            if confirmar:
                # Remove a mensagem e botões antes de iniciar o processamento
                confirm_container.empty()            
                #msgs_novos_produtos_container.empty()
                # Desabilita interações adicionais utilizando um spinner de bloqueio
                with st.spinner("Coletando dados do sistema Mercos..."):
                    try:
                        # Chamada para a função que atualiza os dados
                        atualizar_dados_mercos()                         
                        #time.sleep(5)                        
                        st.toast("Dados atualizados com sucesso!", icon="✅")     
                        # Atualiza a data/hora da última atualização
                        st.session_state.ultima_atualizacao = datetime.now(pytz.utc)                                           

                    except Exception as e:
                        st.error(f"Erro ao atualizar os dados do Mercos: {str(e)}")                    
                st.session_state.confirmacao_ativa = False
                time.sleep(2)
                st.rerun()
            
            elif cancelar:
                confirm_container.empty()
                st.session_state.confirmacao_ativa = False
                st.rerun()
                                                                   
        exibir_tabela_mercos() 
                                    
    elif menu_opcao == "Conciliar SKUs":
        st.subheader("🔄 Conciliação de Produtos")
        
        # Carregar arquivo de referência para o online
        try:
            skus_referencia = pd.read_csv("skus_mercado_livre_amazon.csv")
        except FileNotFoundError:
            st.error("Arquivo 'skus_mercado_livre_amazon.csv' não encontrado.")
            st.stop()
        
        # Carregar os produtos do Mercos
        produtos_mercos = pd.read_csv("produtos_mercos.csv")
        try:
            produtos_conciliados = pd.read_csv("produtos_mercos_conciliados.csv")
        except FileNotFoundError:
            produtos_conciliados = pd.DataFrame(columns=[
                "sku_mercos", "sku_ml_amazon", "produto", "deposito_mercos", "estoque_mercos"
            ])
        
        # Mescla os DataFrames com base nas colunas correspondentes
        produtos_mercos = produtos_mercos.merge(
            produtos_conciliados[["sku_mercos", "sku_ml_amazon"]],
            left_on="SKU",
            right_on="sku_mercos",
            how="left"
        )
        
        # Preenche os valores ausentes com strings vazias
        produtos_mercos["sku_ml_amazon"] = produtos_mercos["sku_ml_amazon"].fillna("")
        
        # Filtro aplicado para visualizar: Todos, Conciliados ou Não Conciliados
        filtro_status = st.selectbox("Filtrar por:", ["Todos", "Conciliados", "Não Conciliados"])
        
        # Aplica o filtro
        if filtro_status == "Conciliados":
            df_form = produtos_mercos[produtos_mercos["sku_ml_amazon"].str.strip() != ""].copy()
        elif filtro_status == "Não Conciliados":
            df_form = produtos_mercos[produtos_mercos["sku_ml_amazon"].str.strip() == ""].copy()
        else:
            df_form = produtos_mercos.copy()
        
        # Totalizadores
        total_mercos = len(produtos_mercos)
        total_conciliados = len(produtos_mercos[produtos_mercos["sku_ml_amazon"].str.strip() != ""])
        total_nao_conciliados = total_mercos - total_conciliados
        st.info(f"Total Produtos Mercos: {total_mercos} | Conciliados: {total_conciliados} | Não Conciliados: {total_nao_conciliados}")
        
        with st.form("conciliacao_form"):
            conciliacoes = []
            skus_online_selecionados = []  # Garante que cada SKU online seja escolhida apenas uma vez
            
            for idx, row in df_form.iterrows():
                # Dividindo a linha em 4 colunas:
                col_fisico_sku, col_fisico_prod, col_online_sku, col_online_prod = st.columns(4)
                
                with col_fisico_sku:
                    st.text_input("SKU Mercos", value=row["SKU"], disabled=True, key=f"fisico_sku_{idx}")
                with col_fisico_prod:
                    st.text_input("Produto Mercos", value=row["Produto"], disabled=True, key=f"fisico_prod_{idx}")
                
                # Lista de SKUs já conciliados (excluindo o SKU atual, se existir)
                skus_conciliados = produtos_conciliados["sku_ml_amazon"].tolist()
                if row["sku_ml_amazon"] != "":
                    skus_conciliados.remove(row["sku_ml_amazon"])
                
                # Lista de SKUs disponíveis para conciliação
                skus_disponiveis = skus_referencia[~skus_referencia["SKU"].isin(skus_conciliados)]["SKU"].tolist()
                
                # Adiciona o SKU atual (se existir) e a opção vazia
                available_options = [""] + [row["sku_ml_amazon"]] if row["sku_ml_amazon"] != "" else [""]
                available_options += skus_disponiveis
                
                # Remove duplicatas e garante a ordem
                available_options = list(dict.fromkeys([opt.strip() for opt in available_options]))
                
                # Converte explicitamente para string para evitar ambiguidade
                sku_mercos_val = str(row["sku_ml_amazon"])
                
                label_online = "SKU Online" + (" ✅" if sku_mercos_val != "" else "")
                with col_online_sku:
                    # Use st.session_state para armazenar o valor selecionado
                    key_online_sku = f"online_sku_{idx}"
                    
                    # Obtém o valor do st.session_state, se existir, senão usa o valor da linha
                    default_value = st.session_state.get(key_online_sku, row["sku_ml_amazon"] if row["sku_ml_amazon"] in available_options else "")
                    
                    sku_online = st.selectbox(
                        label_online,
                        options=available_options,
                        index=available_options.index(default_value) if default_value in available_options else 0,
                        key=key_online_sku
                    )
                    
                    # Remove espaços em branco do valor selecionado
                    sku_online = sku_online.strip()
                    
                if sku_online != "":
                    skus_online_selecionados.append(sku_online)
                
                # Auto-preenche o Produto Online, caso um SKU seja selecionado
                try:
                    produto_online = skus_referencia.loc[skus_referencia["SKU"] == sku_online, "Produto"].iloc[0] if sku_online != "" else ""
                except IndexError:
                    produto_online = ""
                with col_online_prod:
                    st.text_input("Produto Online", value=str(produto_online), disabled=True, key=f"online_prod_{idx}")
                
                conciliacoes.append({
                    "sku_mercos": row["SKU"],
                    "sku_ml_amazon": sku_online,
                    "produto": row["Produto"],
                    "deposito_mercos": row["Depósito"],
                    "estoque_mercos": row["Estoque"]
                })
            
            submitted = st.form_submit_button("💾 Salvar Conciliação")
        
        if submitted:
            # Cria um DataFrame com as novas conciliações
            df_novos = pd.DataFrame([c for c in conciliacoes])
            
            # Carrega o arquivo de conciliações existente
            try:
                produtos_conciliados = pd.read_csv("produtos_mercos_conciliados.csv")
            except FileNotFoundError:
                produtos_conciliados = pd.DataFrame(columns=[
                    "sku_mercos", "sku_ml_amazon", "produto", "deposito_mercos", "estoque_mercos"
                ])
            
            # Identifica os SKUs que foram "desconciliados" (SKU online removido)
            skus_desconciliados = df_novos[df_novos["sku_ml_amazon"] == ""]["sku_mercos"].tolist()
            
            # Remove as linhas do arquivo existente que correspondem aos SKUs que foram conciliados agora
            produtos_conciliados = produtos_conciliados[~produtos_conciliados["sku_mercos"].isin(df_novos["sku_mercos"])]
            
            # Remove as linhas dos produtos que foram desconciliados
            produtos_conciliados = produtos_conciliados[~produtos_conciliados["sku_mercos"].isin(skus_desconciliados)]
            
            # Filtra apenas as novas conciliações que possuem SKU online preenchido
            df_novos = df_novos[df_novos["sku_ml_amazon"] != ""]
            
            # Concatena as conciliações antigas com as novas
            produtos_conciliados = pd.concat([produtos_conciliados, df_novos], ignore_index=True)
            
            # Salva o arquivo com todas as conciliações
            produtos_conciliados.to_csv("produtos_mercos_conciliados.csv", index=False)
            st.success("✅ Conciliação concluída. Arquivo 'produtos_mercos_conciliados.csv' atualizado.")
            st.rerun()


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
                            
    # Controle de exibição
    if opcao == "Dashboard - Visão Integrada de Estoque":
        apis = {
            'ml': MercadoLivreAPI(),
            'amazon': AmazonAPI()
        }
        exibir_visao_integrada(apis)
    elif opcao == "Gestão Estoque Próprio":
        exibir_gestao_estoque()     

if __name__ == "__main__":
    main()