import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app


class _FakeLLMResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChat:
    def invoke(self, _messages):
        # Retorna com 1 casa decimal para validar normalizacao final da API.
        return _FakeLLMResponse(
            '{"caminhoes":[{"id_origem":10,"id_destino":20,'
            '"ids_sku_formatado":"1,2,3,4,5,6,7","qtd_total_skus":7,'
            '"regra_aprovada":true,"criterio1_valor_total":2969.3,'
            '"criterio1_percentual":98.98}]}'
        )


class AppDecimalResponseFormatTests(unittest.TestCase):
    def test_post_otimizar_carga_returns_two_decimal_places_in_raw_json(self) -> None:
        payload = {
            "skus": [
                {
                    "id_sku": 1,
                    "id_origem": 10,
                    "id_destino": 20,
                    "quantidade": 30,
                    "criterios": [{"codigo": 1, "valor": 5.430}],
                }
            ],
            "regraCaminhao": {
                "id_origem": 10,
                "id_destino": 20,
                "criterios": [
                    {
                        "codigo": 1,
                        "valorMinimo": 2500,
                        "valorMaximo": 3000,
                        "tipoCalculo": "Abs",
                    }
                ],
            },
        }

        with patch("service._get_chat", return_value=_FakeChat()):
            client = TestClient(app)
            response = client.post("/otimizar-carga", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertIn('"criterio1_valor_total": 2969.30', response.text)
        self.assertIn('"criterio1_percentual": 98.98', response.text)


if __name__ == "__main__":
    unittest.main()
