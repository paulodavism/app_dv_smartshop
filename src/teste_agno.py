import json
import httpx
import os

from agno.agent import Agent
from agno.models.groq import Groq

from agno.agent import Agent

def get_top_hackernews_stories(num_stories: int = 10) -> str:
    """
    Use this function to get top stories from Hacker News.

    Args:
        num_stories (int): Number of stories to return. Defaults to 10.

    Returns:
        str: JSON string of top stories.
    """

    # Fetch top story IDs
    response = httpx.get('https://hacker-news.firebaseio.com/v0/topstories.json')
    story_ids = response.json()

    # Fetch story details
    stories = []
    for story_id in story_ids[:num_stories]:
        story_response = httpx.get(f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json')
        story = story_response.json()
        if "text" in story:
            story.pop("text", None)
        stories.append(story)
    return json.dumps(stories)


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
        tools=[get_top_hackernews_stories],      # Add DuckDuckGo tool to search the web
        show_tool_calls=True,           # Shows tool calls in the response, set to False to hide
        markdown=True                   # Format responses in markdown
    )    
    agent.print_response("Summarize the top 5 stories on hackernews?", stream=True)