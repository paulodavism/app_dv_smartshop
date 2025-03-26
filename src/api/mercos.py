from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
from dotenv import load_dotenv
import pandas as pd
import time
import logging


# Configurar o logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MercosWebScraping():

    def __init__(self):
        self.df_filtrado = pd.DataFrame()

    def carrega_dados_mercos(self) -> pd.DataFrame:
        
        start_time = time.time()

        # Carregar variáveis do arquivo .env
        load_dotenv()

        try:
            # Configurar opções do Chrome para modo headless
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Executar em modo invisível
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--remote-debugging-port=9222")

            # Inicializar o WebDriver (sem especificar o caminho do chromedriver)
            driver = webdriver.Chrome(options=chrome_options)
            logging.info("WebDriver inicializado com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao inicializar o WebDriver: {e}")
            return pd.DataFrame()

        try:
            # === LOGIN ===
            driver.get("https://app.mercos.com/login")

            # Preencher credenciais
            email = os.getenv("MERCOS_EMAIL")
            senha = os.getenv("MERCOS_SENHA")

            if not email or not senha:
                logging.error("Credenciais ausentes ou inválidas. Verifique as Secrets no Streamlit Cloud.")
                return pd.DataFrame()

            logging.info("Credenciais carregadas com sucesso.")
            logging.info(f"Email: {email}")
            logging.info(f"Senha: {'*' * len(senha)}")  # Exibir asteriscos para segurança
            
            input_email = driver.find_element(By.ID, "id_usuario")
            input_email.send_keys(email)
            
            input_senha = driver.find_element(By.ID, "id_senha")
            input_senha.send_keys(senha)    
            
            driver.find_element(By.ID, "botaoEfetuarLogin").click()
            
            # Verificação ajustada para URL real
            try:
                WebDriverWait(driver, 20).until(
                    EC.url_contains("/327426/indicadores/")  # <<<< Use sua URL real
                )
                logging.info("Login realizado com sucesso!")
            except TimeoutException:
                logging.error("Falha no login")
                driver.quit()
                return pd.DataFrame()

            # === ACESSO À PÁGINA DE PRODUTOS ===
            PRODUTOS_URL = "https://app.mercos.com/industria/327426/produtos/"  # <<<< Use seu ID
            
            try:
                driver.get(PRODUTOS_URL)
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#listagem_produto"))
                )
                logging.info("Acesso direto aos produtos realizado!")
            except TimeoutException:
                logging.warning("Acesso direto falhou. Tentando navegação via menu...")
                
                # Navegar via menu
                menu_produtos = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/produtos')]"))
                )
                menu_produtos.click()
                
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#listagem_produto"))
                )
                logging.info("Navegação via menu concluída!")

            # === APLICAR FILTRO "TODOS OS PRODUTOS" ===
            try:
                # Abrir o dropdown do filtro
                filtro_dropdown = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".Botao__botao___U8SCw.Botao__padrao___bm8eC.Botao__pequeno___UA6ZN.Dropdown__botaoComolink___X0JBb"))
                )
                filtro_dropdown.click()
                
                # Selecionar "todos os produtos"
                todos_produtos = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//li[text()='todos os produtos']"))  # Ajuste conforme necessário
                )
                todos_produtos.click()
                time.sleep(3)  # Aguardar atualização da tabela
            except Exception as e:
                logging.warning(f"Erro ao aplicar filtro: {e}")

            # === EXTRAÇÃO DE TODAS AS PÁGINAS ===
            produtos = []
            pagina = 1

            while True:
                logging.info(f"Extraindo página {pagina}...")
                
                # Extrair dados da página atual
                tabela = driver.find_element(By.ID, "listagem_produto")
                linhas = tabela.find_elements(By.TAG_NAME, "tr")[1:]
                
                for linha in linhas:
                    colunas = linha.find_elements(By.TAG_NAME, "td")
                    if len(colunas) >= 9:
                        estoque_valor = colunas[6].text.strip().split()[0]  # Pega o primeiro elemento antes do espaço
                        estoque_valor = estoque_valor.replace('.', '')  # Remove o ponto de milhar
                        produtos.append({                            
                            "SKU": colunas[2].text.strip(),
                            "Produto": colunas[3].text.strip(),
                            "Depósito": "Grupo Vision",
                            "Estoque": int(estoque_valor) if estoque_valor.isdigit() else None,  # Converte para int se possível                    
                            #"preco_tabela": colunas[8].text.strip(),
                            #"tabela_vip": colunas[9].text.strip()
                        })
                
                try:
                    # Verificar se há próxima página
                    next_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[text()='Próxima']"))
                    )
                    next_btn.click()
                    time.sleep(3)  # Ajuste conforme necessidade
                    pagina += 1
                except:
                    logging.info("Todas as páginas extraídas!")
                    break

            # === TRATAR OS DADOS COM PANDAS ===
            df = pd.DataFrame(produtos)

            # Filtrar apenas produtos com estoque maior que zero
            df_filtrado = df[df['Estoque'] > 0]

            # Salvar CSV com os dados filtrados
            df_filtrado.to_csv("produtos_mercos.csv", index=False)    
            logging.info(f"Dados salvos! Total: {len(produtos)} produtos")
            self.df_filtrado = df_filtrado
            
        except Exception as e:
            logging.error(f"ERRO: {e}")
            self.df_filtrado = pd.DataFrame()
            
        finally:
            # Registrar o momento de término do processo
            end_time = time.time()
            
            # Calcular o tempo total
            tempo_total = end_time - start_time
            logging.info(f"Tempo total do processo: {tempo_total:.2f} segundos")            
            driver.quit()

        return self.df_filtrado

if __name__ == "__main__":
    try:
        mercos_rasp = MercosWebScraping()
                                         
        #Estoque
        df = mercos_rasp.carrega_dados_mercos()        
        if not df.empty:
            print("\nRelatório de Estoque Mercos - Estoque Próprio")
            print("=" * 60)
            print(df.to_string(index=False))
        else:
            print("Nenhum dado encontrado.")

                    
    except Exception as e:
        print(f"Erro na execução da classe MercosWebScraping: {str(e)}")