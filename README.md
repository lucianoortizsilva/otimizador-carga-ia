### 🚧 ```PROJETO EM CONSTRUCAO```

### O que e ?

E um projeto web responsavel por otimizar o transporte de SKU's para cada veiculo disponivel.\
SKU (Stock Keeping Unit) e um codigo unico usado para identificar um produto especifico dentro do estoque.\

### Tecnologias

- [Python 3.12.9](https://www.python.org/)
- [RabbitMQ](https://www.rabbitmq.com/)
- [MongoDB](https://www.mongodb.com/)
- [Docker](https://www.docker.com/)

### Cenarios de teste

O cenario detalhado do endpoint `POST /otimizar-carga` foi movido para:

- `docs/cenarios-teste-api.md`

### Regras de aprovacao por criterio

Na resposta da API, o campo de aprovacao do caminhao (`todos_criterios_aprovados`) e calculado por criterio com a regra:

- `minimo_aceitavel <= valor_total <= valorMaximo`

Para cada criterio existente, a API tambem retorna um campo especifico:

- `criterio{codigo}_aprovado` (ex.: `criterio1_aprovado`)

Onde `minimo_aceitavel` depende de `tipoCalculo`:

- `Abs`: `minimo_aceitavel = valorMinimo`
- `%`: `minimo_aceitavel = (valorMinimo / 100) * valorMaximo`

Observacoes:

- `valorMaximo` e o limite usado para decidir se uma SKU cabe no caminhao.
- `valorMinimo` (ou seu equivalente em `%`) e usado na validacao final de aprovacao.
- O detalhamento completo dos cenarios e exemplos esta em `docs/cenarios-teste-api.md`.

### Arquitetura