import json
import logging
import os
import re
from decimal import ROUND_HALF_UP, Decimal

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from models import OtimizarCargaRequest, OtimizarCargaResponse

load_dotenv()

logger = logging.getLogger("otimizador-carga.service")

# Lê o system_message do arquivo .md
def _read_system_message() -> str:
    system_message_path = os.path.join(
        os.path.dirname(__file__), "system_message.md"
    )
    with open(system_message_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Remove o título (primeira linha) se existir
    lines = content.split("\n")
    if lines[0].startswith("#"):
        content = "\n".join(lines[1:]).strip()
    return content

system_message = SystemMessage(content=_read_system_message())

modelo = os.getenv("OPENAI_MODEL", "gpt-5.4")
chat = None


def _get_chat() -> ChatOpenAI:
    global chat
    if chat is None:
        chat = ChatOpenAI(model=modelo, temperature=0)
    return chat

_DECIMAL_COMMA_VALUE_RE = re.compile(r"^\s*-?\d+,\d+\s*$")
_CRITERIO_FIELD_RE = re.compile(r"^criterio\d+_(valor_total|percentual)$")


def _normalize_decimal_comma_json(raw_json: str) -> str:
    """Converte 222,90 -> 222.90 somente em valores numéricos JSON fora de strings."""
    chars = list(raw_json)
    i = 0
    in_string = False
    escaped = False

    while i < len(chars):
        ch = chars[i]

        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            in_string = True
            i += 1
            continue

        if ch == ":":
            j = i + 1
            while j < len(chars) and chars[j].isspace():
                j += 1

            k = j
            while k < len(chars) and chars[k] not in [",", "}", "]"]:
                k += 1

            value_segment = "".join(chars[j:k])
            if _DECIMAL_COMMA_VALUE_RE.match(value_segment):
                normalized = value_segment.replace(",", ".")
                chars[j:k] = list(normalized)
                i = j + len(normalized)
                continue

        i += 1

    return "".join(chars)


def _enforce_two_decimal_places(raw_json: str) -> str:
    """Garante exatamente 2 casas decimais (HALF_UP) em criterioN_valor_total e criterioN_percentual.

    O float do Python remove zeros à direita (2969.30 → 2969.3) ao serializar via json.dumps.
    Por isso, após o json.dumps, aplicamos regex para reformatar os campos afetados.
    """
    try:
        data = json.loads(raw_json)
        for caminhao in data.get("caminhoes", []):
            for key in list(caminhao.keys()):
                if _CRITERIO_FIELD_RE.match(key):
                    value = Decimal(str(caminhao[key]))
                    caminhao[key] = float(
                        value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    )
        result = json.dumps(data, ensure_ascii=False)

        # Garante exatamente 2 casas decimais na string JSON para campos de critério,
        # pois float("2969.30") == 2969.3 e json.dumps emitiria "2969.3".
        def _fmt(match: re.Match) -> str:
            return f'"{match.group(1)}": {float(match.group(2)):.2f}'

        result = re.sub(
            r'"(criterio\d+_(?:valor_total|percentual))"\s*:\s*(-?\d+(?:\.\d+)?)',
            _fmt,
            result,
        )
        return result
    except Exception:
        return raw_json


def otimizar_carga(payload: OtimizarCargaRequest) -> str:
    logger.info(
        "Processando otimização: %d SKU(s), rota %d->%d",
        len(payload.skus),
        payload.regra_caminhao.id_origem,
        payload.regra_caminhao.id_destino,
    )

    payload_json = payload.model_dump_json(by_alias=True)
    schema_json = json.dumps(
        OtimizarCargaResponse.model_json_schema(by_alias=True),
        ensure_ascii=False,
    )

    mensagens = [
        system_message,
        HumanMessage(content=(
            f"Dados recebidos via API (JSON):\n{payload_json}\n\n"
            "Aplique as regras descritas e devolva APENAS um JSON válido "
            "(sem markdown, sem comentários, sem texto adicional) que respeite "
            f"o schema abaixo:\n{schema_json}\n\n"
            "Retorne exatamente no formato {'caminhoes': [...]} e use os campos "
            "id_origem, id_destino, ids_sku_formatado, qtd_total_skus e "
            "regra_aprovada para cada caminhão. "
            "Inclua também os campos de critério no padrão "
            "criterio{codigo}_valor_total e criterio{codigo}_percentual "
            "(ex.: criterio1_valor_total, criterio1_percentual). "
            "Use números JSON com ponto decimal e SEMPRE 2 casas decimais "
            "(ex.: 2969.30, 98.98), nunca vírgula."
        )),
    ]

    resposta = _get_chat().invoke(mensagens)
    conteudo = resposta.content.strip()

    if conteudo.startswith("```"):
        conteudo = conteudo.strip("`").strip()
        if conteudo.lower().startswith("json"):
            conteudo = conteudo[4:].strip()

    normalized_conteudo = _normalize_decimal_comma_json(conteudo)
    if normalized_conteudo != conteudo:
        logger.debug("Resposta do LLM normalizada: vírgula decimal convertida para ponto.")
        conteudo = normalized_conteudo

    conteudo = _enforce_two_decimal_places(conteudo)

    logger.debug("Resposta bruta do LLM: %s", conteudo)

    # Valida o contrato, mas retorna o JSON bruto para preservar formatação
    # (ex.: 2969.30 em vez de 2969.3).
    OtimizarCargaResponse.model_validate_json(conteudo)
    return conteudo