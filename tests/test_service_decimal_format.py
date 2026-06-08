import unittest

from service import _enforce_two_decimal_places


class ServiceDecimalFormatTests(unittest.TestCase):
    def test_enforce_two_decimal_places_preserves_trailing_zero(self) -> None:
        raw_json = (
            '{"caminhoes":[{"id_origem":10,"id_destino":20,'
            '"ids_sku_formatado":"1,2,3","qtd_total_skus":3,'
            '"regra_aprovada":true,"criterio1_valor_total":2969.3,'
            '"criterio1_percentual":98.976}]}'
        )

        result = _enforce_two_decimal_places(raw_json)

        self.assertIn('"criterio1_valor_total": 2969.30', result)
        self.assertIn('"criterio1_percentual": 98.98', result)


if __name__ == "__main__":
    unittest.main()
