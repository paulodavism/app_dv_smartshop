import json
import httpx
import os

from agno.agent import Agent
from agno.models.groq import Groq

from agno.agent import Agent

def get_sales_data() -> str:
           
    sales_data = [
                {
                    "order_id": 2000009660415964,
                    "product_name": "Colchão Inflável Casal Premium + Bomba De Ar.",
                    "date": "25/10/2024",
                    "sku": "MLB5116413188",
                    "qty": 1,
                    "paid_amount": 167.7,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009660602252,
                    "product_name": "Colchão Inflável Casal Premium + Bomba De Ar.",
                    "date": "25/10/2024",
                    "sku": "MLB5116413188",
                    "qty": 1,
                    "paid_amount": 167.7,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009660587744,
                    "product_name": "Colchão Inflável Casal Premium + Bomba De Ar.",
                    "date": "25/10/2024",
                    "sku": "MLB5116413188",
                    "qty": 1,
                    "paid_amount": 175.93,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009660667924,
                    "product_name": "Furadeira Parafusadeira Gambit Kit Profissional Com Maleta",
                    "date": "25/10/2024",
                    "sku": "MLB3857077621",
                    "qty": 1,
                    "paid_amount": 144.4,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009661056260,
                    "product_name": "Colchão Inflável Casal Premium + Bomba De Ar.",
                    "date": "25/10/2024",
                    "sku": "MLB5116413188",
                    "qty": 1,
                    "paid_amount": 175.93,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009661085402,
                    "product_name": "Colchão Inflável Casal Premium + Bomba De Ar.",
                    "date": "25/10/2024",
                    "sku": "MLB5116413188",
                    "qty": 1,
                    "paid_amount": 179.73,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009661139816,
                    "product_name": "Colchão Inflável Casal Premium + Bomba De Ar.",
                    "date": "25/10/2024",
                    "sku": "MLB5116413188",
                    "qty": 1,
                    "paid_amount": 167.7,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009661223424,
                    "product_name": "Furadeira Parafusadeira Gambit Kit Profissional Com Maleta",
                    "date": "25/10/2024",
                    "sku": "MLB3857077621",
                    "qty": 1,
                    "paid_amount": 144.4,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009663177532,
                    "product_name": "Furadeira Parafusadeira Gambit Kit Profissional Com Maleta",
                    "date": "26/10/2024",
                    "sku": "MLB3857077621",
                    "qty": 1,
                    "paid_amount": 144.4,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009663495850,
                    "product_name": "Furadeira Parafusadeira Gambit Kit Profissional Com Maleta",
                    "date": "26/10/2024",
                    "sku": "MLB3857077621",
                    "qty": 1,
                    "paid_amount": 144.4,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009663840982,
                    "product_name": "Calibrador Compressor Pneu Digital Carro Bike Moto Sem Fio",
                    "date": "26/10/2024",
                    "sku": "MLB4519436306",
                    "qty": 1,
                    "paid_amount": 111.15,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009664096282,
                    "product_name": "Colchão Inflável Casal Premium + Bomba De Ar.",
                    "date": "26/10/2024",
                    "sku": "MLB5116413188",
                    "qty": 1,
                    "paid_amount": 215,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009664278134,
                    "product_name": "Furadeira Parafusadeira Gambit Kit Profissional Com Maleta",
                    "date": "26/10/2024",
                    "sku": "MLB3857077621",
                    "qty": 1,
                    "paid_amount": 144.4,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009664680748,
                    "product_name": "Furadeira Parafusadeira Gambit Kit Profissional Com Maleta",
                    "date": "26/10/2024",
                    "sku": "MLB3857077621",
                    "qty": 1,
                    "paid_amount": 144.4,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009664779386,
                    "product_name": "Furadeira Parafusadeira Gambit Kit Profissional Com Maleta",
                    "date": "26/10/2024",
                    "sku": "MLB3857077621",
                    "qty": 1,
                    "paid_amount": 144.4,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009665075334,
                    "product_name": "Furadeira Parafusadeira Gambit Kit Profissional Com Maleta",
                    "date": "26/10/2024",
                    "sku": "MLB3857077621",
                    "qty": 1,
                    "paid_amount": 144.4,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009665186792,
                    "product_name": "Calibrador Compressor Pneu Digital Carro Bike Moto Sem Fio",
                    "date": "26/10/2024",
                    "sku": "MLB4519436306",
                    "qty": 1,
                    "paid_amount": 111.15,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009665353270,
                    "product_name": "Calibrador Compressor Pneu Digital Carro Bike Moto Sem Fio",
                    "date": "26/10/2024",
                    "sku": "MLB4519436306",
                    "qty": 1,
                    "paid_amount": 111.15,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009665396554,
                    "product_name": "Furadeira Parafusadeira Gambit Kit Profissional Com Maleta",
                    "date": "26/10/2024",
                    "sku": "MLB3857077621",
                    "qty": 1,
                    "paid_amount": 144.4,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009665353986,
                    "product_name": "Furadeira Parafusadeira Gambit Kit Profissional Com Maleta",
                    "date": "26/10/2024",
                    "sku": "MLB3857077621",
                    "qty": 1,
                    "paid_amount": 144.4,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009665406928,
                    "product_name": "Calibrador Compressor Pneu Digital Carro Bike Moto Sem Fio",
                    "date": "26/10/2024",
                    "sku": "MLB4519436306",
                    "qty": 1,
                    "paid_amount": 111.15,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009666202166,
                    "product_name": "Calibrador Compressor Pneu Digital Carro Bike Moto Sem Fio",
                    "date": "26/10/2024",
                    "sku": "MLB4519436306",
                    "qty": 1,
                    "paid_amount": 111.15,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009666324766,
                    "product_name": "Furadeira Parafusadeira Gambit Kit Profissional Com Maleta",
                    "date": "26/10/2024",
                    "sku": "MLB3857077621",
                    "qty": 1,
                    "paid_amount": 144.4,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                
                {
                    "order_id": 2000009666575362,
                    "product_name": "Furadeira Parafusadeira Gambit Kit Profissional Com Maleta",
                    "date": "26/10/2024",
                    "sku": "MLB3857077621",
                    "qty": 1,
                    "paid_amount": 144.4,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                },
                {
                    "order_id": 2000009666879178,
                    "product_name": "Calibrador Compressor Pneu Digital Carro Bike Moto Sem Fio",
                    "date": "26/10/2024",
                    "sku": "MLB4519436306",
                    "qty": 1,
                    "paid_amount": 111.15,
                    "modality": "Flex",
                    "shipping_mode": "Full"
                }
                ]
    
    return json.dumps(sales_data)


if __name__ == "__main__":

    #GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    GROQ_API_KEY="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"
    os.environ['GROQ_API_KEY'] = GROQ_API_KEY

    # Chama a função e armazena o resultado
    #result = get_top_hackernews_stories()
    
    # Converte a string JSON de volta para um objeto Python para formatação
    #formatted_result = json.loads(result)
    
    # Imprime o resultado formatado
    #print(json.dumps(formatted_result, indent=2))

    # Initialize the agent with an LLM via Groq and DuckDuckGoTools
    agent = Agent(
        model=Groq(id="llama-3.3-70b-versatile"),
        #description="You are an enthusiastic news reporter with a flair for storytelling!",
        #description="Você é um agente especialista em analisar qualquer documentação de API. O usuário lhe fornecerá a URL da documentação da API e perguntará como recuperar determinada informação. Vc responderá com um breve resumo e informará o endpoint a ser utilizado.",
        tools=[get_sales_data],      # Add DuckDuckGo tool to search the web
        show_tool_calls=True,           # Shows tool calls in the response, set to False to hide
        markdown=True                   # Format responses in markdown
    )    
    agent.print_response("Gere um relatório, agrupado por produto, que a apresente a quantidade e o valor de produtos vendidos.", stream=True)