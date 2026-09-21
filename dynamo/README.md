# PintarFachadas — paleta de 8 trios em fachadas lado a lado (Dynamo / Revit)

Cada **casa** recebe **exatamente 3 cores**, não importa de quantos elementos ela seja
feita. A casa é repartida em **3 faixas** e a faixa inteira recebe uma cor do trio.
A partir da casa 9 a paleta reinicia.

| Arquivo | O que é |
|---|---|
| `PintarFachadas.dyn` | Grafo pronto: 4 Code Blocks + 1 Boolean + 1 nó Python. Abra e rode. |
| `PintarFachadas.py` | O código do nó Python, versionado à parte para poder ser revisado/diffado. |
| `gerar_dyn.py` | Regenera o `.dyn` depois que você editar o `.py`. Rode `python3 dynamo/gerar_dyn.py`. |
| `teste_logica.py` | Testa HEX, detecção de casas, faixas e ciclo fora do Revit (stubs da API). |

---

## O problema que esta versão resolve

A primeira versão assumia **3 elementos por casa** e fatiava a lista ordenada de 3 em 3.
Numa fachada real a casa tem 8, 12, 30 elementos — o trio escorregava por cima das
divisas e cada casa saía multicolorida.

Agora são dois passos independentes:

1. **Onde termina uma casa e começa a outra** (`casas`)
2. **Repartir cada casa em 3 faixas** (`faixas`) — 1 cor por faixa, N elementos por faixa

Uma casa com 30 elementos continua com 3 cores.

---

## Entradas

| Porta | Valores | Padrão |
|---|---|---|
| `eixo` | `"AUTO"`, `"X"`, `"Y"` — eixo em que a fileira se estende | `"AUTO"` |
| `modo` | `"override"`, `"material"`, `"paint"`, `"limpar"` | `"override"` |
| `casas` | um **número inteiro**, `"gap"`, `"parametro"`, `"trios"` | `"gap"` |
| `faixas` | `"EIXO"`, `"X"`, `"Y"`, `"Z"`, `"AUTO"` | `"EIXO"` |
| `executar` | `true` / `false` | `false` (simulação) |

### `casas` — como separar uma casa da outra

| Valor | Como funciona | Quando usar |
|---|---|---|
| **número** (ex.: `24;`) | Divide a extensão total da fileira nesse número de fatias iguais. | **Casas geminadas** (encostadas) e de largura uniforme. É o modo mais previsível: você conta as casas na elevação e digita. |
| `"gap"` | Quebra onde há vão livre maior que metade da largura típica do elemento. | Casas isoladas, com recuo visível entre elas. Se achar **uma casa só**, ele avisa — é sinal de que são geminadas: use o número. |
| `"parametro"` | Agrupa pelo valor de um parâmetro de texto (`PARAM_GRUPO`, padrão `Comentários`). | O único 100% determinístico. Vale o trabalho de preencher se a fileira for irregular. |
| `"trios"` | Modo antigo: fatia de 3 em 3. | Só se cada casa tiver exatamente 3 elementos. |

### `faixas` — como as 3 cores se distribuem dentro da casa

- `"EIXO"` (padrão) — mesmo eixo da fileira: **3 listras verticais** por casa.
- `"Z"` — **3 faixas horizontais empilhadas** (térreo / meio / topo).
- `"X"` / `"Y"` — força um eixo específico.
- `"AUTO"` — escolhe o eixo de maior dispersão média dentro das casas.

O método de repartição fica em `FAIXAS_METODO` no `.py`:
`"extensao"` (padrão, divide a largura da casa em 3 partes iguais) ou
`"quantil"` (as 3 faixas ficam com ~o mesmo número de elementos).

---

## Como usar

1. Abra o `.dyn` no Dynamo (Revit 2021+ / Dynamo 2.7+, engine CPython3).
2. Vá para a **vista onde a cor deve aparecer**.
3. **No Revit**, selecione os elementos das fachadas. O script lê a seleção do Revit,
   não um nó de seleção do Dynamo. Grupos do Revit são expandidos automaticamente.
4. Volte ao Dynamo, deixe `executar = false` e rode. **Nada é alterado.** Leia `OUT[0]`:

```
*** SIMULAÇÃO — ligue 'executar' para aplicar. ***
Eixo da fileira (AUTO) -> X  (dispersão X=1840.0 ft, Y=32.0 ft)
Tolerância de vão automática: 2.00 ft (metade da largura típica do elemento).
Faixas repartidas no eixo X (listras verticais)
412 elemento(s) -> 24 casa(s) [vão entre casas] -> 3 faixas por casa -> trios 1..8 em ciclo.
Distribuição casa -> total (faixa1/faixa2/faixa3):
   casa 1: 17 elem (6/5/6)
   casa 2: 18 elem (6/6/6)
   ...
```

A linha de **distribuição** é o que vale conferir: se as casas aparecerem com contagens
coerentes entre si, a detecção acertou. Se aparecer `24 casa(s)` quando você tem 24
casas, pode aplicar. Se aparecer `1 casa(s)` ou `180 casa(s)`, troque o `casas`.

5. Vire `executar = true` e rode.

Se o resultado ficar errado, `modo = "limpar"` com `executar = true` remove os overrides
e a pintura dos elementos selecionados.

---

## Os quatro modos de pintura

| Modo | O que faz | Limite |
|---|---|---|
| `override` | `View.SetElementOverrides` na vista ativa: preenchimento de superfície (hachura sólida), corte e linha. | **Só naquela vista.** Não vai para render, schedule ou Realista, e some se resetarem os overrides. Bom para estudo e prancha; ruim como informação de modelo. |
| `material` | Cria/reusa materiais `ZYLO_FACHADA_<HEX>` e grava no parâmetro de material da instância. | **Parede comum não tem** parâmetro de material de instância — está no tipo. Funciona em Parts, modelos genéricos e famílias preparadas. Falhas são reportadas por elemento. |
| `paint` | Cria os materiais e usa `Document.Paint` na face de fachada. | A única via paramétrica que funciona em parede sem duplicar tipo. Escolhe a face pela `DIRECAO_FACHADA` (padrão: −Y se a fileira corre em X). |
| `limpar` | Remove overrides da vista e a pintura feita por este script. | — |

Recomendação: valide a separação das casas com `override` (reversível e barato) antes
de partir para `paint`.

---

## Ajustes no `.py`

`FAIXAS_METODO`, `INVERTER_ORDEM_FAIXAS`, `INVERTER_ORDEM_CASAS`, `TOLERANCIA_GAP`,
`PARAM_GRUPO`, `CATEGORIAS_FALLBACK`, `DIRECAO_FACHADA`, `PREFIXO_MATERIAL`.

Depois de editar, rode `python3 dynamo/gerar_dyn.py` para regenerar o `.dyn`
(ou cole o `.py` direto no nó Python dentro do Dynamo).

---

## Por que não dá para fazer isso só com nós OOTB

O grafo `List.SortByKey` + `List.Chop(3)` + `List.Cycle` + `Element.OverrideColorInView`
resolve o caso "3 elementos por casa" e nada além dele. Ele não tem como:

- descobrir onde uma casa termina (precisa de clusterização por vão ou de fatiar a
  extensão total, nenhum dos dois é um nó);
- repartir N elementos em 3 faixas por coordenada;
- desempatar a ordem quando os elementos da casa compartilham a mesma coordenada.

`List.Chop` fatia por contagem, não por posição — e é exatamente isso que faz as cores
escorregarem quando a casa tem um número variável de elementos.
