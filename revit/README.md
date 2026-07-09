# Modelagem de casa no Revit — Zylo Engenharia

Esta pasta contém o **`casa_terrea.py`**, um script em Python (API do Revit) que
modela automaticamente uma casa térrea completa no seu Revit: níveis, paredes,
piso, telhado 4 águas, portas e janelas.

> O Revit não roda no ambiente do Claude Code — o script foi feito para você
> executar **no seu Revit**, na sua máquina Windows.

## O projeto

Casa térrea de **10 × 8 m (80 m²)**, pé-direito de 2,80 m:

| Ambiente               | Dimensões      | Área    |
| ---------------------- | -------------- | ------- |
| Sala + Cozinha         | 6,00 × 8,00 m  | 48,0 m² |
| Quarto 1               | 4,00 × 4,00 m  | 16,0 m² |
| Banheiro               | 4,00 × 1,50 m  |  6,0 m² |
| Quarto 2               | 4,00 × 2,50 m  | 10,0 m² |

```
(0,8)________________________(10,8)
 |                  |  Quarto 1   |
 |                  |  4,0 x 4,0  |
 |   Sala/Cozinha   |—————————————| y=4,0
 |    6,0 x 8,0     |  Banheiro   |
 |                  |—————————————| y=2,5
 |                  |  Quarto 2   |
 |__________________|_____________|
(0,0)              x=6,0         (10,0)
```

Todas as medidas são parâmetros no topo do script (`LARGURA`, `PROFUNDIDADE`,
`PE_DIREITO`, posições das divisórias etc.) — ajuste e rode de novo.

## Antes de rodar

1. Abra o Revit e crie um **novo projeto** usando um **template de arquitetura**
   (o template pt-BR ou o "Architectural Template" padrão). O script usa os
   tipos padrão de parede/piso/telhado e as primeiras famílias de **porta** e
   **janela** carregadas no template.
2. Salve o projeto vazio antes de rodar (por segurança). Toda a modelagem fica
   dentro de uma única transação — um **Ctrl+Z desfaz a casa inteira**.

## Como rodar

### Opção A — pyRevit (recomendado)

1. Instale o [pyRevit](https://github.com/pyrevitlabs/pyRevit/releases).
2. No Revit: aba **pyRevit → menu (☰) → Run scripts** (ou `pyRevit → Spy →
   Run Script`, conforme a versão).
3. Selecione o `casa_terrea.py` e execute.

### Opção B — RevitPythonShell

1. Instale o [RevitPythonShell](https://github.com/architecture-building-systems/revitpythonshell).
2. Abra o console (**Add-Ins → Interactive Python Shell**), clique em
   *Open* e carregue o `casa_terrea.py`, depois execute.

### Opção C — Dynamo

1. No Revit: **Manage → Dynamo**.
2. Crie um nó **Python Script**, cole o conteúdo do `casa_terrea.py` dentro
   dele e conecte um nó *Watch* na saída `OUT`.
3. Clique em **Run**. O script detecta sozinho que está no Dynamo.

## Depois de rodar

- Abra a vista 3D `{3D}` para ver a casa.
- Abra a planta do nível **Térreo** para conferir o layout.
- Troque os tipos: selecione qualquer parede/porta/janela e mude o tipo no
  *Type Selector* — a modelagem automática usa os tipos padrão só para dar
  o ponto de partida.
- Adicione ambientes (**Architecture → Room**) para gerar os quadros de área.

## Se preferir modelar na mão (roteiro rápido)

1. **Níveis** (vista de elevação): Térreo em 0,00 e Cobertura em +2,80.
2. **Paredes externas** (planta Térreo, `WA`): retângulo 10 × 8 m, altura até
   a Cobertura.
3. **Paredes internas**: divisória vertical em x = 6,0 m; divisórias
   horizontais em y = 2,5 m e y = 4,0 m no lado direito.
4. **Piso** (`Architecture → Floor`): siga o perímetro externo com *Pick Walls*.
5. **Telhado** (`Architecture → Roof → Roof by Footprint`, na Cobertura):
   *Pick Walls* com beiral (overhang) de 0,50 m e inclinação ~30%.
6. **Portas** (`DR`): entrada na fachada sul; uma porta para cada quarto e
   para o banheiro na divisória de x = 6,0 m.
7. **Janelas** (`WN`): uma por ambiente, peitoril 1,00 m (banheiro: 1,50 m).
8. **Ambientes e áreas**: `Room` em cada espaço + `Tag Room`.
