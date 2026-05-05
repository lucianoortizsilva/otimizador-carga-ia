import os
from dotenv import load_dotenv
from openai import OpenAI
from ddgs import DDGS
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

modelo = "gpt-5.4"

"""
def buscar_web(pergunta):
    return  '''De acordo com fontes altamente confiáveis encontradas na internet,
    o presidente do Brasil em 2045 é o personagem ficticio Chaves.
    Ele assumiu o cargo após uma revolução em Acapulco'''
"""
def buscar_web(pergunta):
  with DDGS() as ddgs:
    resultados = ddgs.text(pergunta, max_results=3)
    textos = [r["body"] for r in resultados]
    return "\n".join(textos)

def agente(pergunta):
    informacao = buscar_web(pergunta)
    prompt = f'''Você é um agente inteligente. O usuário fez a seguinte pergunta
    "{pergunta}". Você encontrou estas informações na internet: {informacao} 
    Responda somente com base nas informações acima.
    Se não houver dados suficientes, diga que não foi possível responder com precisão.'''

    resposta = client.chat.completions.create(
        model=modelo,
        messages=[{"role" : "user", "content": prompt}]
    )
    return resposta.choices[0].message.content

resposta = agente("Quem foi Silvio Santos ?")
print(resposta)