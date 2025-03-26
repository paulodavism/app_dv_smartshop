from selenium import webdriver
from selenium.webdriver.chrome.options import Options  # Importar Options para configurar o navegador
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv
import os
import pandas as pd
import re
import time


class MercosWebScraping():

    def __init__(self):
        self.df_filtrado = pd.DataFrame()

    def carrega_dados_mercos(self) -> pd.DataFrame:
        
        start_time = time.time()

        # Carregar variáveis do arquivo .env
        load_dotenv()

        # Configurar opções do Chrome para modo headless
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Executar em modo invisível
        chrome_options.add_argument("--disable-gpu")  # Desabilitar GPU (recomendado para headless)
        chrome_options.add_argument("--window-size=1920,1080")  # Definir tamanho da janela (opcional)

        # Inicializar o WebDriver com as opções configuradas
        driver = webdriver.Chrome(options=chrome_options)

        try:
            # === LOGIN ===
            driver.get("https://app.mercos.com/login")

            # Preencher credenciais
            email = os.getenv("MERCOS_EMAIL")
            senha = os.getenv("MERCOS_SENHA")
            
            input_email = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "id_usuario"))
            )
            input_email.send_keys(email)
            
            input_senha = driver.find_element(By.ID, "id_senha")
            input_senha.send_keys(senha)    
            
            driver.find_element(By.ID, "botaoEfetuarLogin").click()
            
            # Verificação ajustada para URL real
            try:
                WebDriverWait(driver, 20).until(
                    EC.url_contains("/327426/indicadores/")  # <<<< Use sua URL real
                )
                print("✅ Login realizado com sucesso!")
            except TimeoutException:
                print("❌ Falha no login")
                driver.quit()
                exit()

            # === ACESSO À PÁGINA DE PRODUTOS ===
            PRODUTOS_URL = "https://app.mercos.com/industria/327426/produtos/"  # <<<< Use seu ID
            
            try:
                driver.get(PRODUTOS_URL)
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#listagem_produto"))
                )
                print("✅ Acesso direto aos produtos realizado!")
            except TimeoutException:
                print("⚠️ Acesso direto falhou. Tentando navegação via menu...")
                
                # Navegar via menu
                menu_produtos = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/produtos')]"))
                )
                menu_produtos.click()
                
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#listagem_produto"))
                )
                print("✅ Navegação via menu concluída!")

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
                print("⚠️ Erro ao aplicar filtro:", str(e))

            # === EXTRAÇÃO DE TODAS AS PÁGINAS ===
            produtos = []
            pagina = 1

            while True:
                print(f"🔄 Extraindo página {pagina}...")
                
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
                    print("⏹ Todas as páginas extraídas!")
                    break

            # === TRATAR OS DADOS COM PANDAS ===
            df = pd.DataFrame(produtos)

            # Filtrar apenas produtos com estoque maior que zero
            df_filtrado = df[df['Estoque'] > 0]

            # Salvar CSV com os dados filtrados
            df_filtrado.to_csv("produtos_mercos.csv", index=False)    
            print(f"✅ Dados salvos! Total: {len(produtos)} produtos")

            
        except Exception as e:
            print(f"❌ ERRO: {str(e)}")
            self.df_filtrado = pd.DataFrame()
            
        finally:
            # Registrar o momento de término do processo
            end_time = time.time()
            
            # Calcular o tempo total
            tempo_total = end_time - start_time
            print(f"⏰ Tempo total do processo: {tempo_total:.2f} segundos")            
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