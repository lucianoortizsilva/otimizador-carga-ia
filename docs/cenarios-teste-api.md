# Cenarios de teste da API

## POST /otimizar-carga

### Request

```json
{
  "skus": [
    {"id_sku": 1, "id_origem": 10, "id_destino": 20, "quantidade": 30, "criterios": [{ "codigo": 1, "valor": 5.430 }]},
    {"id_sku": 2, "id_origem": 10, "id_destino": 20, "quantidade": 50, "criterios": [{ "codigo": 1, "valor": 4.490 }]},
    {"id_sku": 3, "id_origem": 10, "id_destino": 20, "quantidade": 150, "criterios": [{ "codigo": 1, "valor": 2.160 }]},
    {"id_sku": 4, "id_origem": 10, "id_destino": 20, "quantidade": 100, "criterios": [{ "codigo": 1, "valor": 15.800 }]},
    {"id_sku": 5, "id_origem": 10, "id_destino": 20, "quantidade": 50, "criterios": [{ "codigo": 1, "valor": 2.808 }]},
    {"id_sku": 6, "id_origem": 10, "id_destino": 20, "quantidade": 100, "criterios": [{ "codigo": 1, "valor": 4.775 }]},
    {"id_sku": 7, "id_origem": 10, "id_destino": 20, "quantidade": 6, "criterios": [{ "codigo": 1, "valor": 10.000 }]}
  ],
  "regraCaminhao": {
    "id_origem": 10,
    "id_destino": 20,
    "criterios": [
      { "codigo": 1, "valorMinimo": 2500, "valorMaximo": 3000, "tipoCalculo": "Abs" }
    ]
  }
}
```

### Response esperado

```json
{
  "caminhoes": [
    {
      "id_origem": 10,
      "id_destino": 20,
      "ids_sku_formatado": "1,2,3,4,5,6,7",
      "qtd_total_skus": 7,
      "todos_criterios_aprovados": true,
      "criterio1_valor_total": 2969.30,
      "criterio1_aprovado": true,
      "criterio1_percentual": 98.98
    }
  ]
}
```

### Cálculo passo a passo (critério 1 — valorMaximo: 3000)

| SKU | quantidade × valor | Total SKU | Acumulado | Cabe? |
|-----|--------------------|-----------|-----------|-------|
| 1   | 30 × 5.430         | 162.90    | 162.90    | ✓     |
| 2   | 50 × 4.490         | 224.50    | 387.40    | ✓     |
| 3   | 150 × 2.160        | 324.00    | 711.40    | ✓     |
| 4   | 100 × 15.800       | 1580.00   | 2291.40   | ✓     |
| 5   | 50 × 2.808         | 140.40    | 2431.80   | ✓     |
| 6   | 100 × 4.775        | 477.50    | 2909.30   | ✓     |
| 7   | 6 × 10.000         | 60.00     | 2969.30   | ✓     |

- `criterio1_valor_total` = 2969.30
- `criterio1_aprovado` = **true**
- `criterio1_percentual` = (2969.30 / 3000) com 10 casas HALF_UP → 0.9897666667 × 100 = **98.98**
- `todos_criterios_aprovados` = 2500 ≤ 2969.30 ≤ 3000 → **true**

As regras usadas para geração da resposta estão em `system_message.md`.

## Regra de `tipoCalculo` (`Abs` e `%`)

### Como o backend valida `todos_criterios_aprovados`

- Para `tipoCalculo: "Abs"`:
  - mínimo aceitável = `valorMinimo` (valor absoluto)
- Para `tipoCalculo: "%"`:
  - mínimo aceitável = `(valorMinimo / 100) * valorMaximo`
  - exemplo: `valorMinimo=80` e `valorMaximo=3000` -> mínimo absoluto = `2400.00`

A validação final do caminhão por critério segue:

- `criterio{codigo}_aprovado = true` quando `minimo_aceitavel <= valor_total <= valorMaximo`
- `criterio{codigo}_aprovado = false` caso contrário
- `todos_criterios_aprovados = true` quando `minimo_aceitavel <= valor_total <= valorMaximo`
- caso contrário, `todos_criterios_aprovados = false`

## Exemplo de otimização em múltiplos caminhões

### Request

```json
{
  "skus": [
    {"id_sku": 1, "id_origem": 10, "id_destino": 20, "quantidade": 100, "criterios": [{ "codigo": 1, "valor": 15.800 }]},
    {"id_sku": 2, "id_origem": 10, "id_destino": 20, "quantidade": 50, "criterios": [{ "codigo": 1, "valor": 2.808 }]},
    {"id_sku": 3, "id_origem": 10, "id_destino": 20, "quantidade": 40, "criterios": [{ "codigo": 1, "valor": 4.775 }]},
    {"id_sku": 4, "id_origem": 10, "id_destino": 20, "quantidade": 100, "criterios": [{ "codigo": 1, "valor": 10.000 }]},
    {"id_sku": 5, "id_origem": 10, "id_destino": 20, "quantidade": 30, "criterios": [{ "codigo": 1, "valor": 5.430 }]},
    {"id_sku": 6, "id_origem": 10, "id_destino": 20, "quantidade": 50, "criterios": [{ "codigo": 1, "valor": 4.490 }]},
    {"id_sku": 7, "id_origem": 10, "id_destino": 20, "quantidade": 150, "criterios": [{ "codigo": 1, "valor": 2.160 }]}
  ],
  "regraCaminhao": {
    "id_origem": 10,
    "id_destino": 20,
    "criterios": [
      { "codigo": 1, "valorMinimo": 2500, "valorMaximo": 3000, "tipoCalculo": "Abs" }
    ]
  }
}
```

### Response esperado

```json
{
  "caminhoes": [
    {
      "id_origem": 10,
      "id_destino": 20,
      "ids_sku_formatado": "1,3,4,6",
      "qtd_total_skus": 4,
      "todos_criterios_aprovados": true,
      "criterio1_valor_total": 2995.50,
      "criterio1_aprovado": true,
      "criterio1_percentual": 99.85
    },
    {
      "id_origem": 10,
      "id_destino": 20,
      "ids_sku_formatado": "2,5,7",
      "qtd_total_skus": 3,
      "todos_criterios_aprovados": false,
      "criterio1_valor_total": 627.30,
      "criterio1_aprovado": false,
      "criterio1_percentual": 20.91
    }
  ]
}
```

