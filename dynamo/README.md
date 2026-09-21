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
| `Diagnostico.dyn` / `.py` | Grafo de uma página só, sem entradas, que testa o ambiente do nó Python etapa por etapa. Use quando o nó principal devolver `null`. |
| `MarcarParedes.dyn` / `.py` | Grava um texto no parâmetro de texto de todas as paredes do escopo (modelo / vista / seleção). Útil para limpar ou padronizar `Comentários` antes do ciclo `marcar`. |

---

## Leia antes: a condição que o modelo precisa cumprir

O script classifica cada elemento pelo **centro do bounding box**. Consequência direta:

> **Se a fachada da casa for UMA parede única do piso ao topo, não dá para pintar
> em cima e embaixo com cores diferentes.** A parede inteira tem um centro só, cai
> num lado só, e a casa sai com 2 cores em vez de 3.

Isso nem sempre é defeito: numa fileira real, as casas térreas de volume simples
costumam aparecer mesmo com corpo + esquadria (2 cores), enquanto a divisão em duas
faixas aparece nas de dois pavimentos. O aviso `papel vazio` é informação, não erro —
compare com a referência antes de tentar forçar 3 cores em toda casa.

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
| `modo` | `"override"`, `"material"`, `"paint"`, `"marcar"`, `"limpar"` | `"override"` |
| `casas` | `"grupo"`, `"marcacao"`, um **número**, `"gap"`, `"parametro"`, `"trios"` | `"grupo"` |
| `faixas` | `"fachada"`, `"parametro"`, `"EIXO"`, `"X"`, `"Y"`, `"Z"`, `"AUTO"` | `"fachada"` |
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

## Quando a adivinhação não converge: marcar, revisar, pintar

Em modelo de levantamento de serviço, as paredes são nomeadas pelo serviço
(`LIMPEZA NO AZULEIJO`, `PINTURA ACRILICA`), não pela posição. Nenhuma regra automática
acerta 100% das casas nesse tipo de modelo — e insistir em ajustar a regra é o caminho
para dez scripts ruins seguidos.

O ciclo que converge:

1. **Marcar** — `modo = "marcar"`, `executar = true`. O script grava a decisão dele em
   `PARAM_MARCACAO` (padrão `Comentários`) no formato:

   ```
   ZYLO:casa=7;papel=cima;regra=nivel
   ```

   **Sobrescreve o conteúdo atual do parâmetro** nos elementos do plano.

2. **Revisar só os chutes** — no Revit, tabela (Schedule) de Paredes com as colunas
   `Comentários` + `Família e tipo`, ordenada por `Comentários`.

   O campo `regra=` diz o quanto confiar em cada linha, e é o que torna a revisão
   viável — você filtra em vez de ler 300 linhas:

   | `regra=` | Confiança | Revisar? |
   |---|---|---|
   | `marcado` | você mesmo decidiu numa rodada anterior | não |
   | `moldura-categoria` | é Porta ou Janela no Revit | não |
   | `nome` | o nome do elemento diz a posição | quase nunca |
   | `nivel` | níveis diferentes no Revit: térreo × superior | raramente |
   | `moldura-nome` | palavra no nome | conferir por amostragem |
   | **`corte`** | **chute pela altura** | **sim** |
   | **`mediana`** | **chute, e o corte já tinha falhado** | **sim, primeiro** |

   Filtre a tabela por `Comentários contém "regra=mediana"`, corrija, depois
   `regra=corte`. As demais regras você só confere por amostragem.

   Corrigir = editar o texto na célula: trocar `papel=cima` por `papel=baixo`, mudar o
   número da casa. Pode deixar o `regra=` como está — ele é ignorado na leitura.

3. **Pintar** — `casas = "marcacao"`, `faixas = "parametro"`. Agora o script não adivinha
   nada: pinta exatamente o que a tabela diz. Elemento sem marcação cai nas regras
   automáticas e é contado separadamente no relatório.

A partir daí o resultado é reprodutível e auditável: se uma casa sair errada, você vê
na tabela por quê, corrige a linha e roda de novo.

---

## Ordem das regras de classificação

Cada elemento passa por estas regras, na ordem. A primeira que decidir, manda.

1. **Moldura por categoria** — `CATEGORIAS_MOLDURA`, padrão `OST_Windows` e `OST_Doors`.
2. **Moldura por nome** — `PALAVRAS_MOLDURA`: `moldura`, `esquadria`, `marco`,
   `guarnic`, `peitoril`, `verga`, `frame`, `trim`, `jamb`, `sill`, `casing`, `batente`.
3. **Cima/baixo por nome** — `PALAVRAS_CIMA` / `PALAVRAS_BAIXO`. Se o modelo já
   nomeia a parede pela posição (`... PAREDE DE BAIXO`, `... EM BAIXO`), o nome
   vence a geometria. Nome que bate nas duas listas cai para a regra 4.
4. **Cima/baixo pelo nível do Revit** (`CORTE_POR_NIVEL = True`) — se as paredes da
   casa estão em níveis diferentes, o nível mais baixo é `baixo` e os demais são `cima`.
   É a divisão térreo × pavimento superior, que segue a arquitetura em vez de adivinhar.
5. **Cima/baixo pela cota de corte** — `CORTE_ALTURA` (fração da altura da casa,
   padrão `0.5`) ou `CORTE_ABSOLUTO` (cota Z fixa em pés).
6. **Equilíbrio** (`EQUILIBRAR_FAIXAS = True`) — se depois do corte todas as paredes
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
engine errada, ambiente do nó). Dois caminhos:

1. **Clique no botão `⚠ 1`** na barra inferior do Dynamo (não passe o mouse — clique).
   Ele pula para o nó com aviso e abre a mensagem. Em Dynamo com avisos descartados,
   é a única forma de ver o texto.
2. **Abra o `Diagnostico.dyn`** e rode. Ele não tem entradas e cada etapa roda no seu
   próprio `try`, então sempre devolve resultado. A saída diz exatamente onde para:

```
OK      01 python: 3.9.12 ...
OK      02 acentos: ação, coração, portão, área — em dash
OK      03 clr + AddReference
OK      04 imports Revit
OK      05 documento: NOME_DO_ARQUIVO
OK      06 vista ativa: Elevação Sul  /  tipo Elevation
FALHOU  13 SpecTypeId: AttributeError: ...
```

Se o `Diagnostico.dyn` também devolver `null`, o problema não é o script: é o nó
Python ou a engine da sua instalação.

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
| `marcar` | Grava a decisão do script em `PARAM_MARCACAO` em vez de pintar. | Sobrescreve o parâmetro. É a etapa 1 do ciclo marcar → revisar → pintar. |
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


---

## MarcarParedes — gravar/limpar um parâmetro de texto em todas as paredes

Grafo separado, para preparar o terreno antes do ciclo `marcar`.

| Porta | Valores | Padrão |
|---|---|---|
| `escopo` | `"modelo"` (todas as paredes colocadas), `"vista"`, `"selecao"` | `"modelo"` |
| `texto` | o texto a gravar; `""` **limpa** o parâmetro | `"PARAM_MARCA0"` |
| `parametro` | nome do parâmetro de texto | `"Comentarios"` |
| `executar` | `true` / `false` | `false` |

Só pega **instâncias colocadas** (`WhereElementIsNotElementType`), então tipos de parede
que existem no projeto mas não foram usados ficam de fora.

Parâmetros nativos são buscados primeiro pelo `BuiltInParameter`
(`ALL_MODEL_INSTANCE_COMMENTS`, `ALL_MODEL_MARK`), então funciona em Revit pt-BR e en-US
sem ajuste.

**Isto sobrescreve dado existente.** Três travas:

1. `executar = false` por padrão — a simulação lista quantas paredes seriam alteradas e
   **quais valores seriam perdidos**, agrupados por conteúdo distinto.
2. `OUT[1]` traz `id | tipo | valor_antes | valor_depois`. A coluna `valor_antes` é o
   seu backup — guarde antes de gravar. Não há desfazer no script (no Revit, Ctrl+Z
   desfaz a transação inteira).
3. `APENAS_VAZIOS = True` no topo do `.py`: só escreve onde o parâmetro está vazio.
   Nenhum valor existente é perdido. Comece por aqui se tiver qualquer dúvida.

Parâmetro somente leitura é detectado e pulado, não causa erro. Rodar duas vezes seguidas
não faz nada na segunda.

### Nota sobre o nome

`PARAM_MARCACAO` no `PintarFachadas.py` é o **nome de uma variável do script**, não um
valor para gravar no modelo. A linha `PARAM_MARCACAO = "Comentários"` diz apenas *em qual
parâmetro* o script escreve. Gravar o texto literal `PARAM_MARCA0` em todas as paredes
deixa todas com o mesmo valor, o que torna impossível agrupá-las por ele.
