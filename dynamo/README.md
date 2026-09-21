# PintarFachadas — paleta de 8 trios em fachadas lado a lado (Dynamo / Revit)

Cada **casa** recebe **3 cores** do trio da vez:

| Cor do trio | Vai para |
|---|---|
| cor 1 | parede **de cima** |
| cor 2 | parede **de baixo** |
| cor 3 | **molduras** das esquadrias |

A partir da casa 9 a paleta reinicia (ciclo por módulo).

| Arquivo | O que é |
|---|---|
| `PintarFachadas.dyn` | Grafo pronto: 4 Code Blocks + 1 Boolean + 1 nó Python + 1 Watch. Abra e rode. |
| `PintarFachadas.py` | O código do nó Python, versionado à parte para poder ser revisado/diffado. |
| `gerar_dyn.py` | Regenera o `.dyn` depois que você editar o `.py`. `python3 dynamo/gerar_dyn.py`. |
| `teste_logica.py` | Testa HEX, detecção de casas, papéis e ciclo fora do Revit (stubs da API). |
| `teste_integracao.py` | Roda o script **inteiro** contra um Revit falso, em 13 cenários, para pegar erro de execução que os testes de função pura não pegam. |

---

## Leia antes: a condição que o modelo precisa cumprir

O script classifica cada elemento pelo **centro do bounding box**. Consequência direta:

> **Se a fachada da casa for UMA parede única do piso ao topo, não dá para pintar
> em cima e embaixo com cores diferentes.** A parede inteira tem um centro só, cai
> num lado só, e a casa sai com 2 cores em vez de 3.

Para ter a faixa de cima e a de baixo você precisa de **dois elementos separados** —
duas paredes empilhadas, ou a parede dividida em **Parts** (`Modify > Create Parts`,
depois `Divide Parts` na altura da faixa). Não tem contorno: override gráfico atua no
elemento inteiro, não em meia face.

O resumo avisa quando isso acontece: `AVISO: N casa(s) com algum papel vazio`.

---

## Entradas

| Porta | Valores | Padrão |
|---|---|---|
| `eixo` | `"AUTO"`, `"X"`, `"Y"` — eixo em que a fileira se estende | `"AUTO"` |
| `modo` | `"override"`, `"material"`, `"paint"`, `"limpar"` | `"override"` |
| `casas` | `"grupo"`, um **número**, `"gap"`, `"parametro"`, `"trios"` | `"grupo"` |
| `faixas` | `"fachada"`, `"EIXO"`, `"X"`, `"Y"`, `"Z"`, `"AUTO"` | `"fachada"` |
| `executar` | `true` / `false` | `false` (simulação) |

### `casas` — como separar uma casa da outra

| Valor | Como funciona | Quando usar |
|---|---|---|
| **`"grupo"`** | Cada **Group (bloco)** do Revit é uma casa. | **Melhor opção.** Não depende de geometria, tolerância nem contagem. Selecione os blocos (ou os elementos dentro deles) e pronto. Elementos fora de bloco são reportados e descartados. |
| **número** (ex.: `24;`) | Divide a extensão total da fileira nesse nº de fatias iguais. | Geminadas de largura uniforme, sem blocos. |
| `"gap"` | Quebra onde há vão livre maior que metade da largura típica do elemento. | Casas isoladas com recuo. Avisa se achar uma casa só. |
| `"parametro"` | Agrupa pelo valor de `PARAM_GRUPO` (padrão `Comentários`). | Fileira irregular, sem blocos. |
| `"trios"` | Modo antigo: fatia de 3 em 3. | Só se cada casa tiver exatamente 3 elementos. |

### `faixas` — como as 3 cores se distribuem dentro da casa

- **`"fachada"`** (padrão): cor1 = parede de cima, cor2 = parede de baixo,
  cor3 = molduras das esquadrias.
- `"Z"` / `"EIXO"` / `"X"` / `"Y"` / `"AUTO"`: modo geométrico antigo — 3 faixas
  iguais ao longo do eixo, ignorando o papel do elemento.

---

## Ordem das regras de classificação

Cada elemento passa por estas quatro regras, na ordem. A primeira que decidir, manda.

1. **Moldura por categoria** — `CATEGORIAS_MOLDURA`, padrão `OST_Windows` e `OST_Doors`.
2. **Moldura por nome** — `PALAVRAS_MOLDURA`: `moldura`, `esquadria`, `marco`,
   `guarnic`, `peitoril`, `verga`, `frame`, `trim`, `jamb`, `sill`, `casing`, `batente`.
3. **Cima/baixo por nome** — `PALAVRAS_CIMA` / `PALAVRAS_BAIXO`. Se o modelo já
   nomeia a parede pela posição (`... PAREDE DE BAIXO`, `... EM BAIXO`), o nome
   vence a geometria. Nome que bate nas duas listas cai para a regra 4.
4. **Cima/baixo pela cota de corte** — `CORTE_ALTURA` (fração da altura da casa,
   padrão `0.5`) ou `CORTE_ABSOLUTO` (cota Z fixa em pés).
5. **Equilíbrio** (`EQUILIBRAR_FAIXAS = True`) — se depois do corte todas as paredes
   da casa caírem do mesmo lado, redivide pela mediana de Z para que cima e baixo
   fiquem ambos preenchidos. Só age quando um dos dois ficaria vazio. Casa com uma
   parede só continua sem divisão: não há o que dividir.

O relatório diz quantos elementos cada regra decidiu:

```
Como cada elemento foi classificado: moldura por categoria=132, moldura por nome=0,
parede por nome=2, parede pela cota de corte=175, parede redividida pela mediana=14.
```

Cuidado ao acrescentar palavras curtas em `PALAVRAS_BAIXO`: em modelo de orçamento,
`embasamento` costuma ser erro de grafia de `emassamento` (o serviço), não a base da
parede. Só entre nessa lista o que indica **posição**, nunca serviço.

Modelo de levantamento de serviço costuma ter **paredes** que representam a pintura
de portões e janelas (`PINTURA ESMALTE SINTÉTICO PARA PORTÃO DE METAL`). Por padrão
contam como parede; para mandá-las para a cor da moldura, descomente no `.py`:

```python
PALAVRAS_MOLDURA += ["portao", "janela de metal", "para metais", "vidro"]
```

Rodando em simulação, o resumo imprime o **inventário de categorias** da seleção:

```
Categorias na seleção:
   Paredes: 288
   Janelas: 96
   Modelos genéricos: 48
```

É com essa lista que você ajusta as duas regras sem adivinhar. Se as molduras estiverem
modeladas como Modelo Genérico chamado "Moldura 15", a regra 2 já pega. Se estiverem
com outro nome, acrescente a palavra em `PALAVRAS_MOLDURA`.

---

## Onde a parede se divide entre cima e baixo

`CORTE_ALTURA = 0.5` — fração da altura da casa. `0.6` faz a faixa de baixo ocupar 60%.
A cota é calculada **por casa**, a partir da altura da própria parede (as molduras não
entram na conta), então terreno em desnível não estraga o resultado.
Se preferir um nível fixo, ponha a cota Z em pés em `CORTE_ABSOLUTO`.

Para trocar qual cor vai para qual papel, reordene `PAPEL_DAS_CORES`:

```python
PAPEL_DAS_CORES = ["cima", "baixo", "moldura"]   # cor1, cor2, cor3
```

---

## Se o nó der erro

O script inteiro roda dentro de um `try`. Qualquer exceção não tratada vira relatório
em `OUT[0]`, com o traceback completo, em vez de o nó devolver `null`:

```
=== ERRO NAO TRATADO — copie o bloco abaixo ===
Traceback (most recent call last):
  File "PintarFachadas.py", line ...
```

Se mesmo assim o Watch mostrar `null`, o erro é anterior ao `try` (import do `clr`,
engine errada no nó). Nesse caso a mensagem está no ⚠ do próprio nó Python: passe o
mouse em cima.

---

## Seleção é obrigatória

`EXIGIR_SELECAO = True` (padrão): sem nada selecionado no Revit, o script **para**
com erro em vez de pintar tudo que estiver na vista ativa. Ponha `False` só se você
realmente quiser colorir a vista inteira — e saiba que isso inclui portas e janelas
internas, que também entram como moldura.

---

## Como usar

1. No Revit, **agrupe cada casa em um bloco** (selecione os elementos da casa → `Create Group`).
2. Abra o `.dyn` no Dynamo (Revit 2021+, engine CPython3).
3. Vá para a **vista onde a cor deve aparecer**.
4. **No Revit**, selecione os blocos das casas.
5. No Dynamo, `executar = false` e rode. **Nada é alterado.** O Watch `resumo`
   mostra a saída; `OUT[0]` é o relatório e `OUT[1]` a tabela por elemento:

```
*** SIMULAÇÃO — ligue 'executar' para aplicar. ***
Categorias na seleção:
   Paredes: 288
   Janelas: 96
Eixo da fileira (AUTO) -> X  (dispersão X=1840.0 ft, Y=32.0 ft)
Repartição por papel: cor1=cima, cor2=baixo, cor3=moldura; corte da parede em 50% da altura.
384 elemento(s) -> 24 casa(s) [blocos (Group) do Revit] -> 3 cores por casa -> trios 1..8 em ciclo.
Distribuição casa -> total (papel: nº de elementos):
   casa 1: 16 elem  (cima=6, baixo=6, moldura=4)
   casa 2: 16 elem  (cima=6, baixo=6, moldura=4)
   ...
```

Confira: o número de casas bate? `moldura` tem elementos? `cima` e `baixo` estão
ambos preenchidos? Se sim, pode aplicar.

6. `executar = true` e rode.

Deu errado? `modo = "limpar"` com `executar = true` remove os overrides e a pintura.

---

## Os quatro modos de pintura

| Modo | O que faz | Limite |
|---|---|---|
| `override` | `View.SetElementOverrides` na vista ativa. | **Só naquela vista.** Não vai para render, schedule ou Realista. Bom para estudo e prancha. |
| `material` | Cria/reusa materiais `ZYLO_FACHADA_<HEX>` no parâmetro de material da instância. | **Parede comum não tem** esse parâmetro na instância. Funciona em Parts, modelos genéricos e famílias preparadas. Falhas reportadas por elemento. |
| `paint` | Cria os materiais e usa `Document.Paint` na face de fachada. | Única via paramétrica em parede sem duplicar tipo. Face escolhida por `DIRECAO_FACHADA`. |
| `limpar` | Remove overrides e a pintura feita por este script. | — |

Valide a separação com `override` antes de partir para `paint`.

---

## Ajustes no `.py`

`PAPEL_DAS_CORES`, `CORTE_ALTURA`, `CORTE_ABSOLUTO`, `CATEGORIAS_MOLDURA`,
`PALAVRAS_MOLDURA`, `FAIXAS_METODO`, `INVERTER_ORDEM_FAIXAS`, `INVERTER_ORDEM_CASAS`,
`TOLERANCIA_GAP`, `PARAM_GRUPO`, `CATEGORIAS_FALLBACK`, `DIRECAO_FACHADA`,
`PREFIXO_MATERIAL`.

Depois de editar, rode `python3 dynamo/gerar_dyn.py` para regenerar o `.dyn`
(ou cole o `.py` direto no nó Python dentro do Dynamo).

---

## Por que não dá para fazer isso só com nós OOTB

`List.SortByKey` + `List.Chop(3)` + `List.Cycle` + `Element.OverrideColorInView` resolve
"3 elementos por casa" e nada além. Não tem como, em nós:

- usar o Group como fronteira da casa;
- classificar elemento como moldura por categoria ou nome;
- calcular a cota de corte por casa e separar parede de cima de parede de baixo.

`List.Chop` fatia por **contagem**, não por posição nem por papel — é o que fazia as
cores escorregarem quando a casa tinha um número variável de elementos.
