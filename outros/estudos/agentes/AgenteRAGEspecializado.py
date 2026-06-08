#RAG significa Retrieval-Augmented Generation — em português, algo como Geração Aumentada por Recuperação.

import os

from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(BASE_DIR, "manual_avancado_nobreak_fxp2000.pdf")

loader = PyPDFLoader(PDF_PATH)
documents = loader.load()

embeddings = OpenAIEmbeddings()
#Armazena em vector
vectorestore = FAISS.from_documents(documents, embeddings)
#Recupera informações do vector
retriever = vectorestore.as_retriever()

modelo = "gpt-5.4"
chat = ChatOpenAI(model=modelo, temperature=0)

system_message = SystemMessage(content='''
Você é um assistente virtual especializado no atendimento ao cliente no nobreak FXP-2000.
Responda claramente perguntas técnicas, funcionalidades, garantia, manutenção, atualizações e suporte técnico.
Se a pergunta for irrelevante, responsa educadamente recusando a pergunta.
''')

historicoDaMensagem = {}

"""
    Recupera (ou cria) o historico de mensagens para uma sessao especifica.

    Como funciona:
    - O dicionario global `historicoDaMensagem` guarda um historico por `session_id`.
    - Se a sessao ainda nao existe, criamos um `InMemoryChatMessageHistory` vazio.
    - Retornamos sempre o mesmo objeto para aquela sessao, permitindo conversa continua.

    Efeito pratico:
    - Cada usuario/sessao mantem contexto independente.
    - O estado fica apenas em memoria (se reiniciar o script, o historico e perdido).
    """
def get_session_historico_mensagem(session_id: str):
    # Inicializa o historico na primeira mensagem dessa sessao.
    if session_id not in historicoDaMensagem:
        historicoDaMensagem[session_id] = InMemoryChatMessageHistory()

    # Devolve o historico existente para ser usado na composicao do prompt.
    return historicoDaMensagem[session_id]

"""
    Executa o fluxo RAG completo para responder a pergunta do usuario.

    Etapas detalhadas:
    1) Carrega o historico da sessao para manter continuidade entre perguntas.
    2) Consulta o retriever FAISS para buscar trechos relevantes do manual.
    3) Concatena os principais trechos em um bloco de contexto textual.
    4) Monta a lista final de mensagens com:
       - instrucao de sistema (`system_message`),
       - ultimas interacoes da conversa,
       - pergunta atual com o contexto recuperado.
    5) Envia as mensagens ao modelo de chat.
    6) Salva pergunta e resposta no historico para uso nas proximas interacoes.
    7) Retorna o texto da resposta para exibicao no terminal.
    """
def responder_pergunta(pergunta: str, session_id: str = ""):
    # Recupera o historico da sessao atual (estado da conversa).
    history = get_session_historico_mensagem(session_id)

    # Busca documentos semanticamente proximos da pergunta no vetor FAISS.
    docs = retriever.invoke(pergunta)

    # Limita a 4 trechos para controlar tamanho de contexto e custo de inferencia.
    contexto = "\n\n".join(doc.page_content for doc in docs[:4])

    # Comeca o prompt com a regra de comportamento do assistente.
    mensagens = [system_message]

    # Injeta as ultimas mensagens para manter continuidade sem crescer indefinidamente.
    mensagens.extend(history.messages[-8:])

    # Monta a mensagem do usuario com pergunta + contexto recuperado do manual.
    mensagens.append(
        HumanMessage(
            content=(
                f"Pergunta do cliente: {pergunta}\n\n"
                f"Contexto relevante do manual:\n{contexto}\n\n"
                "Responda apenas com base nesse contexto. "
                "Se a informacao nao estiver no contexto, diga isso claramente."
            )
        )
    )

    # Solicita ao modelo uma resposta final com base nas mensagens montadas.
    resposta = chat.invoke(mensagens)

    # Persiste o turno atual no historico para continuidade de dialogo.
    history.add_user_message(pergunta)
    history.add_ai_message(resposta.content)

    # Retorna apenas o texto da resposta para quem chamou a funcao.
    return resposta.content


if __name__ == "__main__":
    session_id = "sessao-demo-12345"
    while True:
        pergunta = input("Voce: ").strip()
        if pergunta.lower() in ["sair", "quit", "exit"]:
            print("Ate logo!")
            break

        resposta = responder_pergunta(pergunta, session_id=session_id)
        print("Assistente>", resposta)