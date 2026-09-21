# PintarFachadas — paleta de 8 trios em fachadas lado a lado (Dynamo / Revit)

Arquivos:

| Arquivo | O que é |
|---|---|
| `PintarFachadas.dyn` | Grafo pronto: 3 Code Blocks + 1 Boolean + 1 nó Python. Abra e rode. |
| `PintarFachadas.py` | O código do nó Python, versionado à parte para poder ser revisado/diffado. |
| `gerar_dyn.py` | Regenera o `.dyn` depois que você editar o `.py`. Rode `python3 dynamo/gerar_dyn.py`. |
| `teste_logica.py` | Testa HEX, ordenação, agrupamento e ciclo fora do Revit (stubs da API). Rode `python3 dynamo/teste_logica.py`. |

---

## Leia isto antes de rodar — 4 problemas da abordagem pedida

**1. `Element.OverrideColorInView` não pinta o modelo, pinta uma vista.**
Ele grava um override gráfico na vista ativa. Não vai para outras vistas, não aparece
em Realista, não vai para renderização, não existe em schedule e some se alguém
resetar os overrides. Para estudo de fachada em elevação serve; para entregar cor
como informação do modelo, não. Por isso o script tem três modos — veja abaixo.

**2. Ordenar tudo pelo X e fatiar de 3 em 3 só funciona se os 3 elementos da casa
estiverem lado a lado no eixo.** Se as 3 faixas forem empilhadas (mesmo X), o X delas
empata e a ordem dentro da casa fica indefinida — a casa recebe as 3 cores certas, mas
embaralhadas, e isso é silencioso: você não vê o erro no relatório, só na tela.
O script resolve com um desempate explícito (eixo principal → eixo secundário → Z) e
com um `ORDEM_INTERNA` que define em qual eixo as cores 1/2/3 são distribuídas.

**3. Fatiar de 3 em 3 é frágil.** Basta você selecionar 1 elemento a mais (uma soleira,
uma parede interna que veio junto) para *todas* as casas a partir dali deslocarem o trio.
Se o total não for múltiplo de 3, o script avisa em vez de aplicar cor errada calado.
Se sua seleção não é confiável, use `agrupamento = "gap"` (quebra pelo vão entre casas)
ou `"parametro"` (agrupa por um parâmetro de texto, ex.: Comentários = "CASA 07") —
esse último é o único 100% determinístico.

**4. `List.Cycle` é desnecessário.** Módulo sobre o índice da casa (`i % 8`) já faz o
ciclo e não depende de você calcular quantas repetições gerar. É o que o script usa.

---

## Como usar

1. Abra o `.dyn` no Dynamo (Revit 2021+ / Dynamo 2.7+, engine CPython3).
2. Vá para a **vista onde a cor deve aparecer** (a elevação da fileira, normalmente).
3. **No Revit**, selecione os elementos das fachadas. O script lê a seleção do Revit,
   não um nó de seleção do Dynamo — assim você troca a seleção e reroda sem remontar
   o grafo. Grupos do Revit são expandidos automaticamente.
4. Volte ao Dynamo e rode com `executar = false`. Isso **não altera nada**: a saída
   `OUT[0]` traz o resumo e `OUT[1]` a tabela `casa | trio | posição | hex | id | nome`.
   Confira que o nº de casas bate e que não apareceu nenhum aviso.
5. Vire `executar = true` e rode.

### Entradas

| Porta | Valores | Padrão |
|---|---|---|
| `eixo` | `"X"`, `"Y"`, `"AUTO"` | `"AUTO"` — usa o eixo de maior dispersão |
| `modo` | `"override"`, `"material"`, `"paint"` | `"override"` |
| `agrupamento` | `"trios"`, `"gap"`, `"parametro"` | `"trios"` |
| `executar` | `true` / `false` | `false` (simulação) |

Os demais ajustes ficam no topo do `.py`, no bloco `2. AJUSTES`:
`ORDEM_INTERNA`, `INVERTER_ORDEM_INTERNA`, `INVERTER_ORDEM_CASAS`, `TOLERANCIA_GAP`,
`PARAM_GRUPO`, `CATEGORIAS_FALLBACK`, `DIRECAO_FACHADA`, `PREFIXO_MATERIAL`.

### Os três modos

| Modo | O que faz | Quando usar | Limite |
|---|---|---|---|
| `override` | `View.SetElementOverrides` na vista ativa: cor de preenchimento de superfície (hachura sólida), de corte e de linha. | Estudo cromático, prancha de apresentação. | Só naquela vista. Ignorado em Realista. |
| `material` | Cria/reusa materiais `ZYLO_FACHADA_<HEX>` e grava no parâmetro de material da instância. | Partes (Parts), modelos genéricos e famílias com parâmetro de material de instância. | **Parede comum não tem** parâmetro de material de instância — o material está no tipo. Nesses casos o script reporta a falha por elemento em vez de fingir sucesso. |
| `paint` | Cria os materiais e usa `Document.Paint` na face de fachada de cada elemento. | Paredes comuns. É a única forma paramétrica que funciona em parede sem duplicar tipo. | Escolhe a face pela `DIRECAO_FACHADA`. Se a fileira não olha para −Y (eixo X) ou −X (eixo Y), defina o vetor à mão. |

Recomendação: rode `override` primeiro para validar a ordenação visualmente (é
reversível e barato) e só depois troque para `paint`/`material`.

---

## Versão só com nós OOTB (se você quiser o grafo "nativo")

Dá para fazer sem Python. É mais frágil pelos motivos 2 e 3 acima, mas o encadeamento é:

```
Select Model Elements
   └─> Element.BoundingBox ─> BoundingBox.MinPoint ─> Point.X ──┐
   └──────────────────────────────────────────────> List.SortByKey(list, keys)
                                                          └─> .sortedList
```

E um Code Block para a paleta + ciclo, que substitui `List.Cycle` por módulo:

```designscript
paleta = [
  [Color.ByARGB(255,250,214,140), Color.ByARGB(255,213,73,56),  Color.ByARGB(255,243,209,226)], // Trio 1
  [Color.ByARGB(255,249,238,158), Color.ByARGB(255,248,156,19), Color.ByARGB(255,245,169,146)], // Trio 2
  [Color.ByARGB(255,175,220,177), Color.ByARGB(255,255,211,0),  Color.ByARGB(255,250,214,140)], // Trio 3
  [Color.ByARGB(255,205,231,246), Color.ByARGB(255,97,187,91),  Color.ByARGB(255,249,238,158)], // Trio 4
  [Color.ByARGB(255,166,179,213), Color.ByARGB(255,56,165,204), Color.ByARGB(255,175,220,177)], // Trio 5
  [Color.ByARGB(255,197,163,213), Color.ByARGB(255,54,85,139),  Color.ByARGB(255,205,231,246)], // Trio 6
  [Color.ByARGB(255,243,209,226), Color.ByARGB(255,91,38,108),  Color.ByARGB(255,166,179,213)], // Trio 7
  [Color.ByARGB(255,245,169,146), Color.ByARGB(255,165,55,102), Color.ByARGB(255,197,163,213)]  // Trio 8
];

// 24 cores na ordem casa1-cor1, casa1-cor2, ... casa8-cor3
plana = Flatten(paleta, 1);

// um índice por elemento, já ordenado
n     = List.Count(sortedList);
idx   = 0..(n-1);

// o ciclo: casa 9 volta ao trio 1 sem List.Cycle
cores = plana[idx % 24];
```

```
sortedList ──┐
cores      ──┴─> Element.OverrideColorInView   (lacing: Shortest, ambas as listas planas)
```

Duas armadilhas nessa versão:
- `plana[idx % 24]` só está correto se a lista ordenada estiver exatamente na sequência
  `casa1-el1, casa1-el2, casa1-el3, casa2-el1, …`. Com faixas empilhadas (mesmo X) isso
  **não** é garantido — o `List.SortByKey` não define desempate. Aí não tem jeito: ou
  você acrescenta uma segunda chave de ordenação, ou usa o script Python.
- Se `n` não for múltiplo de 3, tudo depois do elemento extra sai deslocado, sem aviso.
