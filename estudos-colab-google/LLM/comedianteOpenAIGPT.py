import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

modelo = "gpt-3.5-turbo"

mensagem = [{"role": "user", "content": "Diga-me uma piada"}]

resposta = client.chat.completions.create(model=modelo, messages=mensagem)

textoResposta = resposta.choices[0].message.content

mensagemTraducao = [{"role": "user", "content": f"Traduza o texto a seguir para o português do Brasil:\n\n{textoResposta}"}]

respostaTraduzida = client.chat.completions.create(model=modelo, messages=mensagemTraducao)

textoTraduzido = respostaTraduzida.choices[0].message.content

print(textoTraduzido)
