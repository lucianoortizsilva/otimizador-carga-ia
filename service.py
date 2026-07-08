import json
import logging
import os
import re
from decimal import ROUND_HALF_UP, Decimal
from itertools import combinations
from typing import Dict, List, Tuple

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


def _quantize_two(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _parse_ids_sku(ids_sku_formatado: str) -> List[int]:
    ids: List[int] = []
    for part in ids_sku_formatado.split(","):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit():
            return []
        ids.append(int(part))
    return ids


def _sku_total_for_codigo(sku, codigo: int) -> Decimal:
    for total in sku.totais_criterios:
        if total.codigo == codigo:
            return Decimal(total.total)

    for criterio in sku.criterios:
        if criterio.codigo == codigo:
            return Decimal(sku.quantidade) * Decimal(criterio.valor)

    return Decimal("0")


def _percentual_criterio(total: Decimal, valor_maximo: Decimal) -> Decimal:
    if valor_maximo <= Decimal("0"):
        return Decimal("0.00")

    razao = (total / valor_maximo).quantize(Decimal("0.0000000001"), rounding=ROUND_HALF_UP)
    return _quantize_two(razao * Decimal("100"))


def _valor_minimo_aceitavel(criterio) -> Decimal:
    valor_minimo = Decimal(criterio.valor_minimo)
    valor_maximo = Decimal(criterio.valor_maximo)

    if criterio.tipo_calculo == "%":
        return _quantize_two((valor_minimo / Decimal("100")) * valor_maximo)

    return valor_minimo


def _is_sku_eligible_for_regra(sku, regra_codigos: set[int]) -> bool:
    return all(criterio.codigo in regra_codigos for criterio in sku.criterios)


def _totais_por_criterio(skus: List[object], criterios: List[object]) -> Dict[int, Decimal]:
    return {
        criterio.codigo: sum(
            (_sku_total_for_codigo(sku, criterio.codigo) for sku in skus),
            Decimal("0"),
        )
        for criterio in criterios
    }


def _subset_fits_max(totais: Dict[int, Decimal], criterios: List[object]) -> bool:
    return all(totais[criterio.codigo] <= Decimal(criterio.valor_maximo) for criterio in criterios)


def _subset_score(totais: Dict[int, Decimal], criterios: List[object]) -> Decimal:
    score = Decimal("0")
    for criterio in criterios:
        valor_maximo = Decimal(criterio.valor_maximo)
        if valor_maximo > Decimal("0"):
            score += totais[criterio.codigo] / valor_maximo
    return score


def _best_subset_for_truck(remaining_skus: List[object], criterios: List[object]) -> List[object]:
    if not remaining_skus:
        return []

    # Busca exata para conjuntos pequenos, garantindo o melhor aproveitamento do limite.
    if len(remaining_skus) <= 20:
        best_subset: List[object] = []
        best_totais: Dict[int, Decimal] = {}
        best_score = Decimal("-1")

        for size in range(1, len(remaining_skus) + 1):
            for subset in combinations(remaining_skus, size):
                subset_list = list(subset)
                totais = _totais_por_criterio(subset_list, criterios)
                if not _subset_fits_max(totais, criterios):
                    continue

                score = _subset_score(totais, criterios)
                is_better = score > best_score
                if not is_better and score == best_score and best_subset:
                    # Critério de desempate: mais SKUs e ordem original estável.
                    is_better = len(subset_list) > len(best_subset)

                if is_better:
                    best_subset = subset_list
                    best_totais = totais
                    best_score = score

        return best_subset

    # Fallback linear para entradas grandes.
    selected: List[object] = []
    totais = {criterio.codigo: Decimal("0") for criterio in criterios}

    for sku in remaining_skus:
        can_add = True
        for criterio in criterios:
            sku_total = _sku_total_for_codigo(sku, criterio.codigo)
            if totais[criterio.codigo] + sku_total > Decimal(criterio.valor_maximo):
                can_add = False
                break
        if can_add:
            selected.append(sku)
            for criterio in criterios:
                totais[criterio.codigo] += _sku_total_for_codigo(sku, criterio.codigo)

    return selected


def _build_optimized_caminhoes(payload: OtimizarCargaRequest) -> List[Dict[str, object]]:
    criterios = payload.regra_caminhao.criterios
    regra_codigos = {criterio.codigo for criterio in criterios}

    remaining = [
        sku
        for sku in payload.skus
        if sku.id_origem == payload.regra_caminhao.id_origem
        and sku.id_destino == payload.regra_caminhao.id_destino
        and _is_sku_eligible_for_regra(sku, regra_codigos)
    ]

    caminhoes: List[Dict[str, object]] = []

    while remaining:
        subset = _best_subset_for_truck(remaining, criterios)
        if not subset:
            break

        ids = [sku.id_sku for sku in subset]
        totais = _totais_por_criterio(subset, criterios)

        caminhao: Dict[str, object] = {
            "id_origem": payload.regra_caminhao.id_origem,
            "id_destino": payload.regra_caminhao.id_destino,
            "ids_sku_formatado": ",".join(str(sku_id) for sku_id in ids),
            "qtd_total_skus": len(ids),
        }

        regra_aprovada = True
        for criterio in criterios:
            total = totais.get(criterio.codigo, Decimal("0"))
            total_duas_casas = _quantize_two(total)
            percentual = _percentual_criterio(total, Decimal(criterio.valor_maximo))
            minimo_aceitavel = _valor_minimo_aceitavel(criterio)
            criterio_aprovado = minimo_aceitavel <= total_duas_casas <= Decimal(criterio.valor_maximo)

            caminhao[f"criterio{criterio.codigo}_valor_total"] = float(total_duas_casas)
            caminhao[f"criterio{criterio.codigo}_percentual"] = float(percentual)
            caminhao[f"criterio{criterio.codigo}_aprovado"] = criterio_aprovado

            if not criterio_aprovado:
                regra_aprovada = False

        caminhao["todos_criterios_aprovados"] = regra_aprovada
        caminhoes.append(caminhao)

        used_ids = set(ids)
        remaining = [sku for sku in remaining if sku.id_sku not in used_ids]

    return caminhoes


def _recalculate_criterios_when_possible(payload: OtimizarCargaRequest, raw_json: str) -> str:
    """Reconstrói a resposta de caminhões com otimização determinística baseada no payload."""
    try:
        data = json.loads(raw_json)
    except Exception:
        data = {}

    data["caminhoes"] = _build_optimized_caminhoes(payload)

    return json.dumps(data, ensure_ascii=False)


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
            "todos_criterios_aprovados para cada caminhão. "
            "Inclua também os campos de critério no padrão "
            "criterio{codigo}_valor_total, criterio{codigo}_percentual e "
            "criterio{codigo}_aprovado "
            "(ex.: criterio1_valor_total, criterio1_percentual, criterio1_aprovado). "
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

    conteudo = _recalculate_criterios_when_possible(payload, conteudo)

    conteudo = _enforce_two_decimal_places(conteudo)

    logger.debug("Resposta bruta do LLM: %s", conteudo)

    # Valida o contrato, mas retorna o JSON bruto para preservar formatação
    # (ex.: 2969.30 em vez de 2969.3).
    OtimizarCargaResponse.model_validate_json(conteudo)
    return conteudo