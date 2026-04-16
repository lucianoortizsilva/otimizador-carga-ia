import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

modelo = "gpt-5.4"

#role-system: é o papel
#role-user: contexto do usuário
mensagem1 = [
    {"role": "system", "content": "Você é um assistente de investimentos ficticio"},
    {"role": "user", "content": "Qual é o melhor investimento de baixo risco que você recomenda nesse ano"},
]

resposta1 = client.chat.completions.create(model=modelo, messages=mensagem1)
respostaConteudo1 = resposta1.choices[0].message.content

mensagem2 = [
    {"role": "assistant", "content": respostaConteudo1},
    {"role": "user", "content": "Quais são os riscos associados a esses investimentos ?"},
]

resposta2 = client.chat.completions.create(model=modelo, messages=mensagem2)
respostaConteudo2 = resposta2.choices[0].message.content

print(respostaConteudo2)
