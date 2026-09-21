# -*- coding: utf-8 -*-
"""
PintarFachadas — nó Python para Dynamo (Revit)
==============================================

Aplica uma paleta de 8 trios de cores a fachadas de casas dispostas lado a lado.
Cada CASA recebe EXATAMENTE 3 CORES, não importa de quantos elementos ela seja feita.
A partir da casa 9 a paleta reinicia (ciclo por módulo).

ENTRADAS DO NÓ (portas IN):
    IN[0]  eixo      : "AUTO" | "X" | "Y"   — eixo em que a fileira se estende.
    IN[1]  modo      : "override" | "material" | "paint" | "limpar"
    IN[2]  casas     : como separar uma casa da outra —
                       "grupo"      -> cada Group (bloco) do Revit é uma casa  [melhor]
                       um NÚMERO    -> divide a fileira nesse nº de casas iguais
                       "gap"        -> quebra onde há vão entre as casas
                       "parametro"  -> agrupa pelo valor de PARAM_GRUPO
                       "trios"      -> modo antigo: fatia de 3 em 3 elementos
    IN[3]  faixas    : como repartir as 3 cores DENTRO da casa —
                       "fachada"    -> cor1 = parede de CIMA
                                       cor2 = parede de BAIXO
                                       cor3 = MOLDURAS das esquadrias
                       "EIXO"|"X"|"Y"|"Z"|"AUTO" -> 3 faixas geométricas no eixo
    IN[4]  executar  : bool -> False = simulação (nada é alterado no modelo)

SAÍDA (OUT):
    [resumo (list<str>), detalhe (list<list>)]
    detalhe = casa | trio | papel | regra | hex | id | nome

SELEÇÃO:
    O script lê a seleção ativa do Revit (uidoc.Selection). Selecione os blocos
    (ou os elementos) no Revit, volte ao Dynamo e rode.

Engine recomendada: CPython3 (Dynamo 2.7+). O código também roda em IronPython2.
"""

import clr

clr.AddReference('RevitAPI')
clr.AddReference('RevitServices')

import Autodesk.Revit.DB as DB
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager


# ---------------------------------------------------------------------------
# 1. PALETA — 8 trios em HEX
# ---------------------------------------------------------------------------

PALETA_HEX = [
    ["#FAD68C", "#D54938", "#F3D1E2"],  # Trio 1
    ["#F9EE9E", "#F89C13", "#F5A992"],  # Trio 2
    ["#AFDCB1", "#FFD300", "#FAD68C"],  # Trio 3
    ["#CDE7F6", "#61BB5B", "#F9EE9E"],  # Trio 4
    ["#A6B3D5", "#38A5CC", "#AFDCB1"],  # Trio 5
    ["#C5A3D5", "#36558B", "#CDE7F6"],  # Trio 6
    ["#F3D1E2", "#5B266C", "#A6B3D5"],  # Trio 7
    ["#F5A992", "#A53766", "#C5A3D5"],  # Trio 8
]


# ---------------------------------------------------------------------------
# 2. AJUSTES — edite aqui, não precisa mexer no resto
# ---------------------------------------------------------------------------

# Qual cor do trio vai para qual papel. Troque a ordem para inverter as cores
# sem mexer na lógica. Papéis válidos: "cima", "baixo", "moldura".
PAPEL_DAS_CORES = ["cima", "baixo", "moldura"]   # cor1, cor2, cor3

# Se True, o script PARA quando não há nada selecionado no Revit, em vez de
# sair pintando tudo que estiver na vista ativa. Deixe True.
EXIGIR_SELECAO = True

# Regra 1 para separar cima de baixo: PELO NOME. Se o nome do elemento, do tipo
# ou da família contiver uma destas expressões, o papel é decidido na hora e a
# geometria nem é consultada. Comparação sem acento e sem maiúsculas.
# CUIDADO ao acrescentar palavras curtas: "embasamento" parece indicar a base
# da parede, mas em modelo de orçamento costuma ser erro de grafia de
# "emassamento" (o serviço). Só ponha aqui o que indica POSIÇÃO, não serviço.
PALAVRAS_BAIXO = ["parede de baixo", "de baixo", "em baixo", "embaixo",
                  "inferior", "terreo", "pavimento terreo"]
PALAVRAS_CIMA = ["parede de cima", "de cima", "em cima", "superior",
                 "pavimento superior", "oitao", "platibanda"]

# Regra 2a: se as paredes da casa estao em NIVEIS diferentes do Revit, o nivel
# mais baixo e "baixo" e os demais sao "cima". E a divisao que a referencia
# mostra: terreo numa cor, pavimento superior em outra. Vale mais que qualquer
# corte por altura, porque segue a arquitetura em vez de adivinhar.
CORTE_POR_NIVEL = True

# Se, depois do corte, TODAS as paredes da casa caírem do mesmo lado (acontece
# quando as paredes da casa estão todas na mesma altura), redivide pela mediana
# de Z para que cima e baixo fiquem ambos preenchidos. Só age quando um dos dois
# ficaria vazio; casa com uma parede só continua sem salvação.
EQUILIBRAR_FAIXAS = True

# Regra 2 (usada quando o nome não decide): onde a parede se divide entre
# "baixo" e "cima", como fração da altura da casa. 0.5 = na metade.
CORTE_ALTURA = 0.5
# Se você preferir um nível fixo, ponha a cota Z em PÉS aqui (ignora CORTE_ALTURA).
CORTE_ABSOLUTO = None

# O que conta como "moldura de esquadria". Primeiro pela categoria, depois por
# palavra no nome do elemento / tipo / família. Rode em simulação: o resumo
# imprime o inventário de categorias da seleção para você ajustar isto.
CATEGORIAS_MOLDURA = [
    DB.BuiltInCategory.OST_Windows,
    DB.BuiltInCategory.OST_Doors,
]
PALAVRAS_MOLDURA = [
    "moldura", "esquadria", "marco", "guarnic", "peitoril", "verga",
    "frame", "trim", "jamb", "sill", "casing", "batente",
]
# Em modelo de orçamento existem PAREDES que representam a pintura de portões,
# janelas e metais ("PINTURA ESMALTE SINTÉTICO PARA PORTÃO DE METAL"). Por
# padrão elas contam como parede. Para mandá-las para a cor da moldura,
# descomente a linha abaixo:
# PALAVRAS_MOLDURA += ["portao", "janela de metal", "para metais", "vidro"]

# Faixas geométricas (quando faixas != "fachada"):
#   "extensao" -> divide a largura/altura da casa em 3 partes iguais
#   "quantil"  -> as 3 faixas ficam com ~o mesmo nº de elementos
FAIXAS_METODO = "extensao"

INVERTER_ORDEM_FAIXAS = False
INVERTER_ORDEM_CASAS = False

# casas == "gap": 0 = deriva da largura típica do elemento.
TOLERANCIA_GAP = 0.0

# casas == "parametro": nome do parâmetro de texto que identifica a casa.
PARAM_GRUPO = "Comentários"

# Categorias que NUNCA recebem cor. Telhado fica fora: a fachada é parede e
# esquadria. Tire da lista o que você quiser que seja pintado.
CATEGORIAS_IGNORADAS = [
    DB.BuiltInCategory.OST_Roofs,
    DB.BuiltInCategory.OST_Fascia,
    DB.BuiltInCategory.OST_Gutter,
    DB.BuiltInCategory.OST_RoofSoffit,
]

# casas == "marcatipo": de onde sai o número do trio. O script lê a "Marca de
# tipo" (ALL_MODEL_TYPE_MARK) do TIPO do grupo; se não achar, tenta a "Marca"
# da instância; se não achar, este parâmetro pelo nome.
# O número entra em ciclo: 1..8 = trios 1..8, 9 = trio 1, 10 = trio 2.
PARAM_MARCA_TIPO = "Marca de tipo"

# Usado quando a seleção do Revit está vazia.
CATEGORIAS_FALLBACK = [
    DB.BuiltInCategory.OST_Walls,
    DB.BuiltInCategory.OST_Parts,
    DB.BuiltInCategory.OST_GenericModel,
    DB.BuiltInCategory.OST_Windows,
    DB.BuiltInCategory.OST_Doors,
]

# modo == "paint": direção para onde a fachada olha.
# None = deduz do eixo da fileira (fileira em X -> fachada em -Y; em Y -> -X).
DIRECAO_FACHADA = None

PREFIXO_MATERIAL = "ZYLO_FACHADA_"

# modo == "marcar" grava a decisao do script neste parametro de texto, no
# formato  ZYLO:casa=7;papel=cima  — dai voce revisa numa tabela do Revit,
# corrige o que ficou errado na mao, e roda de novo com casas="marcacao" e
# faixas="parametro" para pintar exatamente o que a tabela diz.
# ATENCAO: sobrescreve o conteudo atual do parametro nos elementos do plano.
PARAM_MARCACAO = "Comentários"
PREFIXO_MARCACAO = "ZYLO:"

FAIXAS_POR_CASA = 3


# ---------------------------------------------------------------------------
# 3. Utilitários
# ---------------------------------------------------------------------------

def _entrada(indice, padrao):
    try:
        valor = IN[indice]  # noqa: F821  (injetado pelo nó Python)
    except Exception:
        return padrao
    if valor is None:
        return padrao
    if isinstance(valor, str) and not valor.strip():
        return padrao
    return valor


def hex_para_argb(texto, alfa=255):
    """'#FAD68C' -> (255, 250, 214, 140). Aceita 3 ou 6 dígitos, com ou sem '#'."""
    h = str(texto).strip().lstrip('#')
    if len(h) == 3:
        h = ''.join([c * 2 for c in h])
    if len(h) != 6:
        raise ValueError(u"HEX inválido: {0}".format(texto))
    return (alfa, int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def cor_revit(hex_texto):
    """Equivalente ao Color.ByARGB do Dynamo, já em Autodesk.Revit.DB.Color."""
    _, r, g, b = hex_para_argb(hex_texto)
    return DB.Color(r, g, b)


PALETA_ARGB = [[hex_para_argb(h) for h in trio] for trio in PALETA_HEX]

_ACENTOS = {u'á': u'a', u'à': u'a', u'ã': u'a', u'â': u'a', u'ä': u'a',
            u'é': u'e', u'ê': u'e', u'è': u'e', u'í': u'i', u'î': u'i',
            u'ó': u'o', u'ô': u'o', u'õ': u'o', u'ö': u'o',
            u'ú': u'u', u'ü': u'u', u'ç': u'c'}


def normalizar(texto):
    t = (texto or u"").lower()
    for acento, simples in _ACENTOS.items():
        t = t.replace(acento, simples)
    return t


def nome_seguro(elemento):
    """Element.Name lança exceção para alguns tipos de elemento no Revit —
    e isso, dentro de um laço sobre todos os elementos, mata o script inteiro."""
    try:
        return elemento.Name
    except Exception:
        return u"(sem nome)"


def id_valor(element_id):
    """ElementId.Value (Revit 2024+) ou .IntegerValue (anteriores)."""
    for nome in ('Value', 'IntegerValue'):
        try:
            return getattr(element_id, nome)
        except Exception:
            continue
    return -1


def caixa(elemento, doc):
    """BoundingBox em coordenadas do modelo, já com o Transform aplicado."""
    bb = None
    try:
        bb = elemento.get_BoundingBox(None)
    except Exception:
        bb = None
    if bb is None:
        try:
            bb = elemento.get_BoundingBox(doc.ActiveView)
        except Exception:
            bb = None
    if bb is None:
        return None
    try:
        t = bb.Transform
        p1, p2 = t.OfPoint(bb.Min), t.OfPoint(bb.Max)
    except Exception:
        p1, p2 = bb.Min, bb.Max
    return (
        (min(p1.X, p2.X), min(p1.Y, p2.Y), min(p1.Z, p2.Z)),
        (max(p1.X, p2.X), max(p1.Y, p2.Y), max(p1.Z, p2.Z)),
    )


def centro(bb):
    (x0, y0, z0), (x1, y1, z1) = bb
    return ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0)


def mediana(valores):
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    meio = len(ordenados) // 2
    if len(ordenados) % 2:
        return ordenados[meio]
    return (ordenados[meio - 1] + ordenados[meio]) / 2.0


def extensao(itens, eixo):
    """(min, max) da união dos bounding boxes ao longo de um eixo."""
    return (min(d['bb'][0][eixo] for d in itens),
            max(d['bb'][1][eixo] for d in itens))


# ---------------------------------------------------------------------------
# 4. Coleta — cada elemento guarda de qual BLOCO veio
# ---------------------------------------------------------------------------

def expandir(elemento, doc, chave_casa, marca_casa=None):
    """Group do Revit vira seus membros, carimbados com a chave do bloco e com
    a Marca de tipo do GroupType — que e de onde sai o numero do trio."""
    if isinstance(elemento, DB.Group):
        chave = id_valor(elemento.Id)
        marca = marca_de_tipo(elemento, doc)
        saida = []
        for mid in elemento.GetMemberIds():
            membro = doc.GetElement(mid)
            if membro is not None:
                saida.extend(expandir(membro, doc, chave, marca))
        return saida
    return [(elemento, chave_casa, marca_casa)]


def _chave_do_grupo(elemento):
    """Se o elemento já pertence a um Group, usa o id do Group como chave."""
    try:
        gid = elemento.GroupId
        if gid is not None and id_valor(gid) > 0:
            return id_valor(gid)
    except Exception:
        pass
    return None


def marca_de_tipo(elemento, doc):
    """'Marca de tipo' do TIPO do elemento (para um Group, do GroupType).
    Cai para a 'Marca' da instância e depois para PARAM_MARCA_TIPO pelo nome."""
    try:
        tipo = doc.GetElement(elemento.GetTypeId())
    except Exception:
        tipo = None

    for alvo, nome_bip in ((tipo, 'ALL_MODEL_TYPE_MARK'),
                           (elemento, 'ALL_MODEL_MARK')):
        if alvo is None:
            continue
        bip = getattr(DB.BuiltInParameter, nome_bip, None)
        if bip is None:
            continue
        try:
            p = alvo.get_Parameter(bip)
            if p is not None and p.HasValue:
                valor = p.AsString() or p.AsValueString()
                if valor and valor.strip():
                    return valor.strip()
        except Exception:
            continue

    for alvo in (tipo, elemento):
        if alvo is None:
            continue
        try:
            p = alvo.LookupParameter(PARAM_MARCA_TIPO)
            if p is not None and p.HasValue:
                valor = p.AsString() or p.AsValueString()
                if valor and valor.strip():
                    return valor.strip()
        except Exception:
            continue
    return None


def trio_da_marca(marca):
    """'7' -> indice 6.  '9' -> indice 0: a cada 8 a paleta reinicia.
    Aceita texto com numero dentro ('CASA 07' -> 7). None se nao houver numero."""
    if marca is None:
        return None
    digitos = u"".join([c for c in u"{0}".format(marca) if c.isdigit()])
    if not digitos:
        return None
    try:
        n = int(digitos)
    except ValueError:
        return None
    if n <= 0:
        return None
    return (n - 1) % len(PALETA_HEX)


def elevacao_do_nivel(elemento, doc):
    """Cota do nivel de referencia do elemento, ou None se nao houver."""
    candidatos = []
    try:
        candidatos.append(elemento.LevelId)
    except Exception:
        pass
    for nome_bip in ('WALL_BASE_CONSTRAINT', 'FAMILY_LEVEL_PARAM',
                     'SCHEDULE_LEVEL_PARAM', 'INSTANCE_SCHEDULE_ONLY_LEVEL_PARAM'):
        bip = getattr(DB.BuiltInParameter, nome_bip, None)
        if bip is None:
            continue
        try:
            p = elemento.get_Parameter(bip)
            if p is not None:
                candidatos.append(p.AsElementId())
        except Exception:
            continue
    for lid in candidatos:
        try:
            if lid is None or id_valor(lid) <= 0:
                continue
            nivel = doc.GetElement(lid)
            if nivel is not None:
                return float(nivel.Elevation)
        except Exception:
            continue
    return None


def textos_do_elemento(elemento, doc):
    """Nome do elemento, do tipo, da família e da categoria — para classificar."""
    textos = []
    for getter in (lambda: nome_seguro(elemento),
                   lambda: elemento.Category.Name):
        try:
            textos.append(getter())
        except Exception:
            pass
    try:
        tipo = doc.GetElement(elemento.GetTypeId())
        if tipo is not None:
            try:
                textos.append(tipo.Name)
            except Exception:
                pass
            try:
                textos.append(tipo.FamilyName)
            except Exception:
                pass
    except Exception:
        pass
    return [t for t in textos if t]


def coletar(doc, uidoc, log):
    brutos = []
    try:
        for eid in uidoc.Selection.GetElementIds():
            el = doc.GetElement(eid)
            if el is not None:
                brutos.extend(expandir(el, doc, None, None))
    except Exception as erro:
        log.append(u"Não consegui ler a seleção do Revit: {0}".format(erro))

    if not brutos and EXIGIR_SELECAO:
        log.append(u"ERRO: nada selecionado no Revit. Selecione os blocos das casas "
                   u"e rode de novo. (Para pintar tudo que estiver na vista ativa, "
                   u"ponha EXIGIR_SELECAO = False no topo do script.)")
        return []

    if not brutos:
        log.append(u"ATENÇÃO: seleção vazia — pintando TUDO que está na vista ativa "
                   u"(CATEGORIAS_FALLBACK), inclusive o que você não queria.")
        for bic in CATEGORIAS_FALLBACK:
            try:
                col = DB.FilteredElementCollector(doc, doc.ActiveView.Id) \
                        .OfCategory(bic).WhereElementIsNotElementType()
                brutos.extend([(e, None, None) for e in col])
            except Exception:
                continue

    ignoradas = set()
    for bic in CATEGORIAS_IGNORADAS:
        try:
            cat = DB.Category.GetCategory(doc, bic)
            if cat is not None:
                ignoradas.add(id_valor(cat.Id))
        except Exception:
            continue

    dados, vistos, pulados = [], set(), 0
    for el, chave, marca in brutos:
        eid = id_valor(el.Id)
        if eid in vistos:
            continue
        if getattr(el, 'Category', None) is None:
            continue
        try:
            if id_valor(el.Category.Id) in ignoradas:
                vistos.add(eid)
                pulados += 1
                continue
        except Exception:
            pass
        bb = caixa(el, doc)
        if bb is None:
            continue
        vistos.add(eid)
        if chave is None:
            chave = _chave_do_grupo(el)
        if marca is None and chave is not None:
            try:
                grupo = doc.GetElement(DB.ElementId(chave))
                if grupo is not None:
                    marca = marca_de_tipo(grupo, doc)
            except Exception:
                marca = None
        try:
            cat_id = id_valor(el.Category.Id)
            cat_nome = el.Category.Name
        except Exception:
            cat_id, cat_nome = -1, u"?"
        dados.append({'el': el, 'bb': bb, 'c': centro(bb), 'casa': chave,
                      'cat_id': cat_id, 'cat': cat_nome,
                      'nivel': elevacao_do_nivel(el, doc),
                      'marca': marca,
                      'textos': textos_do_elemento(el, doc)})
    if pulados:
        log.append(u"{0} elemento(s) de categoria ignorada (telhado etc.) "
                   u"ficaram de fora — veja CATEGORIAS_IGNORADAS.".format(pulados))
    return dados


def inventario(dados, log, limite=12):
    """Lista as categorias presentes na seleção — é o que permite configurar
    CATEGORIAS_MOLDURA e PALAVRAS_MOLDURA sem adivinhar."""
    contagem = {}
    for d in dados:
        contagem[d['cat']] = contagem.get(d['cat'], 0) + 1
    ordenado = sorted(contagem.items(), key=lambda kv: kv[1], reverse=True)
    log.append(u"Categorias na seleção:")
    for nome, n in ordenado[:limite]:
        log.append(u"   {0}: {1}".format(nome, n))
    if len(ordenado) > limite:
        log.append(u"   ... mais {0} categoria(s)".format(len(ordenado) - limite))


# ---------------------------------------------------------------------------
# 5. Passo 1 — separar as CASAS
# ---------------------------------------------------------------------------

EIXOS = {"X": 0, "Y": 1, "Z": 2}


def escolher_eixo(dados, eixo_pedido, log):
    if str(eixo_pedido).upper() in ("X", "Y"):
        return EIXOS[str(eixo_pedido).upper()]
    dispersao = []
    for i in (0, 1):
        valores = [d['c'][i] for d in dados]
        dispersao.append(max(valores) - min(valores))
    eixo = 0 if dispersao[0] >= dispersao[1] else 1
    log.append(u"Eixo da fileira (AUTO) -> {0}  (dispersão X={1:.1f} ft, Y={2:.1f} ft)".format(
        "XY"[eixo], dispersao[0], dispersao[1]))
    return eixo


def _ordenar(dados, eixo):
    secundario = 1 - eixo if eixo in (0, 1) else 1
    return sorted(dados, key=lambda d: (d['c'][eixo], d['c'][secundario], d['c'][2]))


def casas_por_grupo(dados, eixo, log):
    """Cada Group (bloco) do Revit é uma casa. É o modo determinístico:
    não depende de geometria, tolerância nem contagem."""
    baldes, soltos = {}, []
    for d in dados:
        if d['casa'] is None:
            soltos.append(d)
        else:
            baldes.setdefault(d['casa'], []).append(d)
    if soltos:
        log.append(u"AVISO: {0} elemento(s) não estão dentro de nenhum bloco — "
                   u"ficaram de fora. Agrupe-os ou tire-os da seleção.".format(len(soltos)))
    if not baldes:
        log.append(u"ERRO: nenhum bloco encontrado na seleção. Ou as casas não estão "
                   u"agrupadas, ou você selecionou elementos soltos. "
                   u"Use o número de casas em IN[2].")
    return list(baldes.values())


def casas_por_numero(dados, eixo, quantidade, log):
    """Divide a extensão total da fileira em N fatias iguais."""
    vmin, vmax = extensao(dados, eixo)
    largura = (vmax - vmin) / float(quantidade)
    if largura <= 0:
        return [list(dados)]
    grupos = [[] for _ in range(quantidade)]
    for d in dados:
        i = int((d['c'][eixo] - vmin) / largura)
        grupos[max(0, min(i, quantidade - 1))].append(d)
    log.append(u"Fileira de {0:.1f} ft dividida em {1} casas de ~{2:.1f} ft.".format(
        vmax - vmin, quantidade, largura))
    return [g for g in grupos if g]


def casas_por_gap(dados, eixo, log):
    """Quebra a fila onde aparece um vão livre maior que a tolerância."""
    ordenados = _ordenar(dados, eixo)

    # vão livre entre cada elemento e a borda acumulada dos anteriores.
    # Elementos encostados dão vão 0; só a divisa entre casas dá vão real.
    vaos, borda = [], ordenados[0]['bb'][1][eixo]
    for d in ordenados[1:]:
        vaos.append(d['bb'][0][eixo] - borda)
        borda = max(borda, d['bb'][1][eixo])

    tol = TOLERANCIA_GAP
    if tol <= 0:
        # A tolerância vem do tamanho típico do ELEMENTO, não dos vãos —
        # derivar dos vãos é circular e junta tudo numa casa só.
        larguras = [d['bb'][1][eixo] - d['bb'][0][eixo] for d in ordenados]
        tol = max(mediana(larguras) * 0.5, 1e-6)
        log.append(u"Tolerância de vão automática: {0:.2f} ft "
                   u"(metade da largura típica do elemento).".format(tol))

    grupos, atual = [], [ordenados[0]]
    for i, d in enumerate(ordenados[1:]):
        if vaos[i] > tol:
            grupos.append(atual)
            atual = []
        atual.append(d)
    if atual:
        grupos.append(atual)
    if len(grupos) == 1:
        log.append(u"AVISO: o modo 'gap' achou UMA casa só — provavelmente as casas "
                   u"são geminadas (sem vão). Use \"grupo\" ou o número de casas.")
    return grupos


def casas_por_parametro(dados, eixo, log):
    baldes, sem_valor = {}, 0
    for d in dados:
        valor = None
        try:
            p = d['el'].LookupParameter(PARAM_GRUPO)
            if p is not None and p.HasValue:
                valor = p.AsString() or p.AsValueString()
        except Exception:
            valor = None
        if not valor:
            sem_valor += 1
            continue
        baldes.setdefault(valor.strip(), []).append(d)
    if sem_valor:
        log.append(u"{0} elemento(s) sem '{1}' preenchido — ficaram de fora.".format(
            sem_valor, PARAM_GRUPO))
    return list(baldes.values())


def casas_por_trios(dados, eixo, log):
    """Modo antigo: fatia a lista ordenada de 3 em 3."""
    ordenados = _ordenar(dados, eixo)
    if len(dados) % 3:
        log.append(u"AVISO: {0} elementos não é múltiplo de 3 — o modo 'trios' "
                   u"vai deslocar as cores.".format(len(dados)))
    return [ordenados[i:i + 3] for i in range(0, len(ordenados), 3)]


# ---------------------------------------------------------------------------
# 6. Passo 2 — repartir a casa em 3 papéis (ou 3 faixas geométricas)
# ---------------------------------------------------------------------------

PAPEIS = ("cima", "baixo", "moldura")


def _texto(d):
    return u" ".join([normalizar(t) for t in d.get('textos', [])])


def motivo_moldura(d, ids_moldura):
    """None se não é moldura; senão diz por que foi classificada — o motivo
    entra no relatório para você saber qual regra ajustar."""
    if d.get('cat_id') in ids_moldura:
        return "categoria"
    alvo = _texto(d)
    for palavra in PALAVRAS_MOLDURA:
        if palavra in alvo:
            return "nome"
    return None


def e_moldura(d, ids_moldura):
    return motivo_moldura(d, ids_moldura) is not None


def papel_por_nome(d):
    """'cima' / 'baixo' quando o nome do elemento decide, None quando não.
    Nome ambíguo (bate nas duas listas) cai para a regra geométrica."""
    alvo = _texto(d)
    achou_baixo = any(p in alvo for p in PALAVRAS_BAIXO)
    achou_cima = any(p in alvo for p in PALAVRAS_CIMA)
    if achou_baixo and not achou_cima:
        return "baixo"
    if achou_cima and not achou_baixo:
        return "cima"
    return None


def repartir_fachada(grupo, ids_moldura, stats=None):
    """cima / baixo / moldura.

    Cadeia de regras, da mais confiavel para a mais chutada:
      1. moldura por categoria (Portas/Janelas)
      2. moldura por palavra no nome
      3. cima/baixo por palavra no nome
      4. cima/baixo pelo NIVEL do Revit (terreo x pavimento superior)
      5. cima/baixo pela cota de corte da casa
      6. equilibrio pela mediana, se tudo caiu de um lado so
    """
    if stats is None:
        stats = {}
    papeis = {"cima": [], "baixo": [], "moldura": []}
    parede, sobrando = [], []

    for d in grupo:
        motivo = motivo_moldura(d, ids_moldura)
        if motivo is not None:
            d['regra'] = u"moldura-" + motivo
            papeis["moldura"].append(d)
            stats["moldura_" + motivo] = stats.get("moldura_" + motivo, 0) + 1
            continue
        parede.append(d)
        nome = papel_por_nome(d)
        if nome is not None:
            d['regra'] = u"nome"
            papeis[nome].append(d)
            stats["parede_nome"] = stats.get("parede_nome", 0) + 1
        else:
            sobrando.append(d)

    if not sobrando:
        return papeis

    # regra 4: niveis diferentes -> terreo embaixo, o resto em cima
    if CORTE_POR_NIVEL:
        niveis = sorted(set(d['nivel'] for d in sobrando if d.get('nivel') is not None))
        if len(niveis) >= 2:
            base = niveis[0]
            for d in sobrando:
                z = d.get('nivel')
                d['regra'] = u"nivel"
                papeis["baixo" if (z is not None and z <= base + 1e-6) else "cima"].append(d)
            stats["parede_nivel"] = stats.get("parede_nivel", 0) + len(sobrando)
            return papeis

    # regra 5: cota de corte, calculada sobre a parede da casa
    if CORTE_ABSOLUTO is not None:
        corte = float(CORTE_ABSOLUTO)
    else:
        z0 = min(d['bb'][0][2] for d in parede)
        z1 = max(d['bb'][1][2] for d in parede)
        corte = z0 + (z1 - z0) * float(CORTE_ALTURA)

    geom = {"cima": [], "baixo": []}
    for d in sobrando:
        d['regra'] = u"corte"
        geom["cima" if d['c'][2] >= corte else "baixo"].append(d)

    # regra 6: o corte falha quando as paredes estao todas na mesma altura
    ja_tem_os_dois = bool(papeis["cima"]) and bool(papeis["baixo"])
    if (EQUILIBRAR_FAIXAS and not ja_tem_os_dois and len(sobrando) >= 2
            and (not geom["cima"] or not geom["baixo"])):
        ordenados = sorted(sobrando, key=lambda q: q['c'][2])
        for d in ordenados:
            d['regra'] = u"mediana"
        meio = len(ordenados) // 2
        geom = {"baixo": ordenados[:meio], "cima": ordenados[meio:]}
        stats["parede_equilibrada"] = stats.get("parede_equilibrada", 0) + len(ordenados)
    else:
        stats["parede_geom"] = stats.get("parede_geom", 0) + len(sobrando)

    papeis["cima"].extend(geom["cima"])
    papeis["baixo"].extend(geom["baixo"])
    return papeis


def ler_marcacao(d):
    """(casa, papel) gravados por modo='marcar', ou (None, None)."""
    try:
        p = d['el'].LookupParameter(PARAM_MARCACAO)
        if p is None or not p.HasValue:
            return (None, None)
        texto = p.AsString() or u""
    except Exception:
        return (None, None)
    if not texto.startswith(PREFIXO_MARCACAO):
        return (None, None)
    casa, papel = None, None
    for parte in texto[len(PREFIXO_MARCACAO):].split(";"):
        if "=" not in parte:
            continue
        chave, valor = parte.split("=", 1)
        chave, valor = chave.strip().lower(), valor.strip()
        if chave == "casa" and valor:
            casa = valor
        elif chave == "papel" and valor.lower() in PAPEIS:
            papel = valor.lower()
    return (casa, papel)


def escrever_marcacao(elemento, casa, papel, regra=u"?"):
    try:
        p = elemento.LookupParameter(PARAM_MARCACAO)
    except Exception:
        return False
    if p is None or p.IsReadOnly:
        return False
    try:
        if p.StorageType != DB.StorageType.String:
            return False
    except Exception:
        pass
    # a regra vai junto: e o que permite filtrar na tabela do Revit so os
    # elementos que o script CHUTOU (regra=corte / regra=mediana) em vez de
    # revisar linha por linha.
    p.Set(u"{0}casa={1};papel={2};regra={3}".format(
        PREFIXO_MARCACAO, casa, papel, regra))
    return True


def casas_por_marcacao(dados, eixo, log):
    """Cada casa vem do que esta gravado no parametro — zero adivinhacao."""
    baldes, sem = {}, 0
    for d in dados:
        casa, _ = ler_marcacao(d)
        if casa is None:
            sem += 1
            continue
        baldes.setdefault(casa, []).append(d)
    if sem:
        log.append(u"AVISO: {0} elemento(s) sem marcação em '{1}' — ficaram de fora. "
                   u"Rode antes com modo='marcar'.".format(sem, PARAM_MARCACAO))
    if not baldes:
        log.append(u"ERRO: nenhum elemento marcado. Rode primeiro com modo='marcar', "
                   u"revise a tabela no Revit, e só então use casas='marcacao'.")
    return list(baldes.values())


def repartir_por_marcacao(grupo, ids_moldura, stats):
    """Papel lido do parâmetro. O que não estiver marcado cai nas regras
    automáticas, e o relatório diz quantos foram de cada jeito."""
    papeis = {"cima": [], "baixo": [], "moldura": []}
    restantes = []
    for d in grupo:
        _, papel = ler_marcacao(d)
        if papel in papeis:
            d['regra'] = u"marcado"
            papeis[papel].append(d)
            stats["papel_marcado"] = stats.get("papel_marcado", 0) + 1
        else:
            restantes.append(d)
    if restantes:
        automatico = repartir_fachada(restantes, ids_moldura, stats)
        for chave in papeis:
            papeis[chave].extend(automatico[chave])
    return papeis


def escolher_eixo_faixa(pedido, eixo_fileira, grupos, log):
    texto = str(pedido).upper().strip()
    if texto in EIXOS:
        eixo = EIXOS[texto]
    elif texto == "AUTO":
        medias = []
        for i in (0, 1, 2):
            acum = [max(d['c'][i] for d in g) - min(d['c'][i] for d in g)
                    for g in grupos if len(g) > 1]
            medias.append(sum(acum) / len(acum) if acum else 0.0)
        eixo = medias.index(max(medias))
        log.append(u"Eixo das faixas (AUTO) -> {0}".format("XYZ"[eixo]))
    else:
        eixo = eixo_fileira
    log.append(u"Faixas repartidas no eixo {0} ({1}){2}".format(
        "XYZ"[eixo],
        u"listras verticais" if eixo != 2 else u"faixas horizontais empilhadas",
        u", ordem invertida" if INVERTER_ORDEM_FAIXAS else u""))
    return eixo


def repartir_em_faixas(grupo, eixo_faixa, n=FAIXAS_POR_CASA):
    """3 faixas geométricas. Elementos podem ser 3 ou 300 — 3 cores do mesmo jeito."""
    if not grupo:
        return [[] for _ in range(n)]
    if len(grupo) <= n:
        ordenados = sorted(grupo, key=lambda d: d['c'][eixo_faixa])
        faixas = [[] for _ in range(n)]
        for i, d in enumerate(ordenados):
            faixas[i].append(d)
        return faixas

    if FAIXAS_METODO == "quantil":
        ordenados = sorted(grupo, key=lambda d: d['c'][eixo_faixa])
        corte = len(ordenados) / float(n)
        faixas = [[] for _ in range(n)]
        for i, d in enumerate(ordenados):
            faixas[min(int(i / corte), n - 1)].append(d)
        return faixas

    vmin, vmax = extensao(grupo, eixo_faixa)
    largura = (vmax - vmin) / float(n)
    if largura <= 1e-9:
        return [list(grupo)] + [[] for _ in range(n - 1)]
    faixas = [[] for _ in range(n)]
    for d in grupo:
        k = int((d['c'][eixo_faixa] - vmin) / largura)
        faixas[max(0, min(k, n - 1))].append(d)
    return faixas


# ---------------------------------------------------------------------------
# 7. Aplicação das cores
# ---------------------------------------------------------------------------

def _chamar(obj, nomes, *args):
    """Chama o primeiro método que existir (nomes novos e antigos da API)."""
    for nome in nomes:
        metodo = getattr(obj, nome, None)
        if metodo is None:
            continue
        try:
            metodo(*args)
            return True
        except Exception:
            continue
    return False


def id_hachura_solida(doc):
    alvo = DB.ElementId.InvalidElementId
    try:
        for fp in DB.FilteredElementCollector(doc).OfClass(DB.FillPatternElement):
            padrao = fp.GetFillPattern()
            if padrao.IsSolidFill:
                alvo = fp.Id
                if padrao.Target == DB.FillPatternTarget.Drafting:
                    return fp.Id
    except Exception:
        pass
    return alvo


def montar_override(cor, hachura_id):
    ogs = DB.OverrideGraphicSettings()
    _chamar(ogs, ['SetSurfaceForegroundPatternVisible', 'SetProjectionFillPatternVisible'], True)
    _chamar(ogs, ['SetSurfaceForegroundPatternColor', 'SetProjectionFillColor'], cor)
    _chamar(ogs, ['SetCutForegroundPatternVisible', 'SetCutFillPatternVisible'], True)
    _chamar(ogs, ['SetCutForegroundPatternColor', 'SetCutFillColor'], cor)
    if hachura_id != DB.ElementId.InvalidElementId:
        _chamar(ogs, ['SetSurfaceForegroundPatternId', 'SetProjectionFillPatternId'], hachura_id)
        _chamar(ogs, ['SetCutForegroundPatternId', 'SetCutFillPatternId'], hachura_id)
    _chamar(ogs, ['SetProjectionLineColor'], cor)
    _chamar(ogs, ['SetCutLineColor'], cor)
    _chamar(ogs, ['SetSurfaceTransparency'], 0)
    return ogs


def obter_material(doc, hex_texto, cache, hachura_id):
    nome = PREFIXO_MATERIAL + str(hex_texto).lstrip('#').upper()
    if nome in cache:
        return cache[nome]
    achado = None
    for mat in DB.FilteredElementCollector(doc).OfClass(DB.Material):
        if mat.Name == nome:
            achado = mat
            break
    if achado is None:
        achado = doc.GetElement(DB.Material.Create(doc, nome))
    cor = cor_revit(hex_texto)
    try:
        achado.Color = cor
        achado.UseRenderAppearanceForShading = False
        achado.Transparency = 0
        if hachura_id != DB.ElementId.InvalidElementId:
            achado.SurfaceForegroundPatternId = hachura_id
            achado.SurfaceForegroundPatternColor = cor
    except Exception:
        pass
    cache[nome] = achado
    return achado


BIPS_MATERIAL = ['DPART_MATERIAL_ID_PARAM', 'MATERIAL_ID_PARAM',
                 'STRUCTURAL_MATERIAL_PARAM']


def _param_de_material(p):
    if p.StorageType != DB.StorageType.ElementId or p.IsReadOnly:
        return False
    d = p.Definition
    try:
        return d.GetDataType() == DB.SpecTypeId.Reference.Material
    except Exception:
        pass
    try:
        return str(d.ParameterType) == 'Material'
    except Exception:
        return False


def aplicar_material(elemento, material):
    for nome_bip in BIPS_MATERIAL:
        bip = getattr(DB.BuiltInParameter, nome_bip, None)
        if bip is None:
            continue
        p = elemento.get_Parameter(bip)
        if p is not None and not p.IsReadOnly:
            p.Set(material.Id)
            return True
    for p in elemento.Parameters:
        if _param_de_material(p):
            p.Set(material.Id)
            return True
    return False


def faces_da_fachada(elemento, direcao):
    """Faces planas verticais que melhor apontam para `direcao`."""
    opcoes = DB.Options()
    opcoes.ComputeReferences = True
    opcoes.IncludeNonVisibleObjects = False
    opcoes.DetailLevel = DB.ViewDetailLevel.Fine

    solidos = []

    def varrer(geo):
        for g in geo:
            if isinstance(g, DB.Solid):
                if g.Faces.Size > 0 and g.Volume > 1e-9:
                    solidos.append(g)
            elif isinstance(g, DB.GeometryInstance):
                varrer(g.GetInstanceGeometry())

    try:
        varrer(elemento.get_Geometry(opcoes))
    except Exception:
        return []

    candidatas = []
    for solido in solidos:
        for face in solido.Faces:
            if not isinstance(face, DB.PlanarFace):
                continue
            n = face.FaceNormal
            if abs(n.Z) > 0.35:       # piso/teto
                continue
            alinhamento = n.X * direcao[0] + n.Y * direcao[1] + n.Z * direcao[2]
            if alinhamento <= 0.2:
                continue
            candidatas.append((face.Area * alinhamento, face))
    if not candidatas:
        return []
    candidatas.sort(key=lambda t: t[0], reverse=True)
    melhor = candidatas[0][0]
    return [f for pontuacao, f in candidatas if pontuacao >= melhor * 0.6]


def limpar(doc, vista, elementos):
    """Remove os overrides da vista e a pintura de faces feita por este script."""
    vazio = DB.OverrideGraphicSettings()
    limpos = 0
    for el in elementos:
        try:
            vista.SetElementOverrides(el.Id, vazio)
            limpos += 1
        except Exception:
            pass
        try:
            for face in faces_da_fachada(el, (0.0, 0.0, 0.0)):
                if doc.IsPainted(el.Id, face):
                    doc.RemovePaint(el.Id, face)
        except Exception:
            pass
    return limpos


# ---------------------------------------------------------------------------
# 8. Execução
# ---------------------------------------------------------------------------

eixo_pedido = _entrada(0, "AUTO")
modo = str(_entrada(1, "override")).lower().strip()
casas_pedido = _entrada(2, "grupo")
faixas_pedido = _entrada(3, "fachada")
executar = bool(_entrada(4, False))

# resumo e detalhe ficam no modulo para que o relatorio sobreviva a um erro
resumo = []
detalhe = []


def principal():
    """Todo o trabalho. Devolve [resumo, detalhe]."""
    doc = DocumentManager.Instance.CurrentDBDocument
    uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument
    vista = doc.ActiveView

    MODOS = ("override", "material", "paint", "marcar", "limpar")

    if modo not in MODOS:
        resumo.append(u"ERRO: modo '{0}' desconhecido. Use: {1}.".format(modo, ", ".join(MODOS)))
        return [resumo, detalhe]
    else:
        dados = coletar(doc, uidoc, resumo)

        if not dados:
            resumo.append(u"ERRO: nenhum elemento válido. Selecione as casas no Revit "
                          u"e rode de novo.")
            return [resumo, detalhe]

        elif modo == "limpar":
            elementos = [d['el'] for d in dados]
            if not executar:
                resumo.append(u"*** SIMULAÇÃO — ligue 'executar' para limpar de verdade. ***")
                resumo.append(u"Limparia overrides e pintura de {0} elemento(s).".format(
                    len(elementos)))
            else:
                TransactionManager.Instance.EnsureInTransaction(doc)
                n = limpar(doc, vista, elementos)
                TransactionManager.Instance.TransactionTaskDone()
                resumo.append(u"Overrides removidos de {0} elemento(s) na vista '{1}'.".format(
                    n, nome_seguro(vista)))
            return [resumo, detalhe]

        else:
            inventario(dados, resumo)
            eixo = escolher_eixo(dados, eixo_pedido, resumo)

            # --- passo 1: separar as casas ---
            try:
                numero_casas = int(casas_pedido)
            except (TypeError, ValueError):
                numero_casas = None

            usar_marca = False
            if numero_casas is not None and numero_casas > 0:
                grupos = casas_por_numero(dados, eixo, numero_casas, resumo)
                metodo_casas = u"{0} casas iguais".format(numero_casas)
            else:
                chave = normalizar(str(casas_pedido)).strip()
                if chave == "marcatipo":
                    grupos = casas_por_grupo(dados, eixo, resumo)
                    usar_marca = True
                    metodo_casas = u"blocos + trio pela Marca de tipo"
                elif chave == "marcacao":
                    grupos = casas_por_marcacao(dados, eixo, resumo)
                    metodo_casas = u"marcação em '{0}'".format(PARAM_MARCACAO)
                elif chave == "grupo":
                    grupos = casas_por_grupo(dados, eixo, resumo)
                    metodo_casas = u"blocos (Group) do Revit"
                elif chave == "parametro":
                    grupos = casas_por_parametro(dados, eixo, resumo)
                    metodo_casas = u"parâmetro '{0}'".format(PARAM_GRUPO)
                elif chave == "trios":
                    grupos = casas_por_trios(dados, eixo, resumo)
                    metodo_casas = u"trios (3 elementos por casa)"
                else:
                    grupos = casas_por_gap(dados, eixo, resumo)
                    metodo_casas = u"vão entre casas"

            grupos = [g for g in grupos if g]

            if not grupos:
                return [resumo, detalhe]
            else:
                grupos.sort(key=lambda g: min(d['c'][eixo] for d in g))
                if INVERTER_ORDEM_CASAS:
                    grupos.reverse()

                # --- passo 2: repartir cada casa ---
                chave_faixas = normalizar(str(faixas_pedido)).strip()
                por_marcacao = chave_faixas == "parametro"
                por_papel = por_marcacao or chave_faixas == "fachada"

                ids_moldura = set()
                if por_papel:
                    for bic in CATEGORIAS_MOLDURA:
                        try:
                            cat = DB.Category.GetCategory(doc, bic)
                            if cat is not None:
                                ids_moldura.add(id_valor(cat.Id))
                        except Exception:
                            continue
                    resumo.append(u"Repartição por papel: cor1={0}, cor2={1}, cor3={2}; "
                                  u"corte da parede em {3:.0f}% da altura.".format(
                                      PAPEL_DAS_CORES[0], PAPEL_DAS_CORES[1],
                                      PAPEL_DAS_CORES[2], float(CORTE_ALTURA) * 100))
                else:
                    eixo_faixa = escolher_eixo_faixa(faixas_pedido, eixo, grupos, resumo)

                plano = []
                distribuicao = []
                stats = {}
                sem_marca = []
                for indice_casa, grupo in enumerate(grupos):
                    marca_casa = None
                    if usar_marca:
                        marcas = [d.get('marca') for d in grupo if d.get('marca')]
                        marca_casa = marcas[0] if marcas else None
                        indice = trio_da_marca(marca_casa)
                        if indice is None:
                            indice = indice_casa % len(PALETA_HEX)
                            sem_marca.append(indice_casa + 1)
                        trio_idx = indice
                    else:
                        trio_idx = indice_casa % len(PALETA_HEX)   # ciclo por posicao
                    trio = PALETA_HEX[trio_idx]

                    if por_papel:
                        if por_marcacao:
                            papeis = repartir_por_marcacao(grupo, ids_moldura, stats)
                        else:
                            papeis = repartir_fachada(grupo, ids_moldura, stats)
                        partes = [(PAPEL_DAS_CORES[k], papeis.get(PAPEL_DAS_CORES[k], []))
                                  for k in range(3)]
                    else:
                        faixas = repartir_em_faixas(grupo, eixo_faixa)
                        if INVERTER_ORDEM_FAIXAS:
                            faixas.reverse()
                        partes = [(u"faixa{0}".format(k + 1), faixas[k]) for k in range(3)]

                    exemplo = u""
                    for _, itens in partes:
                        if itens:
                            exemplo = nome_seguro(itens[0]['el'])
                            break
                    distribuicao.append((indice_casa + 1, len(grupo),
                                         [(nome, len(itens)) for nome, itens in partes],
                                         exemplo, marca_casa, trio_idx + 1))
                    for k, (nome, itens) in enumerate(partes):
                        for d in itens:
                            plano.append({'casa': indice_casa + 1, 'trio': trio_idx + 1,
                                          'papel': nome, 'hex': trio[k], 'el': d['el'],
                                          'regra': d.get('regra', u"?")})

                resumo.append(u"{0} elemento(s) -> {1} casa(s) [{2}] -> 3 cores por casa "
                              u"-> trios 1..8 em ciclo.".format(
                                  len(dados), len(grupos), metodo_casas))
                resumo.append(u"Modo: {0} | eixo da fileira: {1}".format(modo, "XYZ"[eixo]))

                if por_papel:
                    resumo.append(u"Como cada elemento foi classificado, da regra "
                                  u"mais confiável para a mais chutada:")
                    for _rot, _ch in (
                            (u"papel lido da marcação (revisado por você)", "papel_marcado"),
                            (u"moldura por categoria (Portas/Janelas)", "moldura_categoria"),
                            (u"moldura por palavra no nome", "moldura_nome"),
                            (u"cima/baixo por palavra no nome", "parede_nome"),
                            (u"cima/baixo pelo nível do Revit", "parede_nivel"),
                            (u"cima/baixo pela cota de corte", "parede_geom"),
                            (u"cima/baixo redividido pela mediana", "parede_equilibrada")):
                        if stats.get(_ch):
                            resumo.append(u"   {0}: {1}".format(_rot, stats[_ch]))

                # quais papéis ficaram vazios, e em quantas casas — é o que diz se o
                # problema é a regra de classificação ou a geometria do modelo
                faltando = {}
                for c, _, partes, _, _, _ in distribuicao:
                    for nome, q in partes:
                        if q == 0:
                            faltando.setdefault(nome, []).append(c)
                if faltando:
                    resumo.append(u"AVISO: papéis vazios (essas casas mostram menos de 3 cores):")
                    for nome in sorted(faltando):
                        lista = faltando[nome]
                        resumo.append(u"   sem '{0}': {1} casa(s) -> {2}{3}".format(
                            nome, len(lista), ", ".join([str(c) for c in lista[:12]]),
                            u" ..." if len(lista) > 12 else u""))

                if usar_marca and sem_marca:
                    resumo.append(u"AVISO: {0} casa(s) sem número na Marca de tipo — "
                                  u"caíram no ciclo por posição, que pode não bater com "
                                  u"as vizinhas: {1}{2}".format(
                                      len(sem_marca),
                                      ", ".join([str(c) for c in sem_marca[:12]]),
                                      u" ..." if len(sem_marca) > 12 else u""))

                resumo.append(u"Distribuição casa -> total (papel: nº de elementos):")
                for c, total, partes, exemplo, marca_c, trio_c in distribuicao[:15]:
                    resumo.append(u"   casa {0}{1}: trio {2} | {3} elem ({4}) | ex.: {5}".format(
                        c,
                        u" (marca {0})".format(marca_c) if marca_c is not None else u"",
                        trio_c, total,
                        ", ".join([u"{0}={1}".format(n, q) for n, q in partes]),
                        exemplo[:45]))
                if len(distribuicao) > 15:
                    resumo.append(u"   ... mais {0} casa(s)".format(len(distribuicao) - 15))

                for p in plano:
                    detalhe.append([p['casa'], p['trio'], p['papel'],
                                    p.get('regra', u"?"), p['hex'],
                                    id_valor(p['el'].Id), nome_seguro(p['el'])])

                if modo == "marcar":
                    resumo.append(u"MODO MARCAR: vai SOBRESCREVER o parâmetro '{0}' de "
                                  u"{1} elemento(s) com a decisão do script. Revise numa "
                                  u"tabela do Revit e depois rode com casas=marcacao e "
                                  u"faixas=parametro.".format(PARAM_MARCACAO, len(plano)))

                if not executar:
                    resumo.insert(0, u"*** SIMULAÇÃO — ligue 'executar' para aplicar. ***")
                    return [resumo, detalhe]
                elif modo == "override" and not vista.AreGraphicsOverridesAllowed():
                    resumo.append(u"ERRO: a vista '{0}' não aceita sobrescrita de "
                                  u"gráficos.".format(nome_seguro(vista)))
                    return [resumo, detalhe]
                else:
                    if DIRECAO_FACHADA:
                        direcao = tuple(DIRECAO_FACHADA)
                    else:
                        direcao = (0.0, -1.0, 0.0) if eixo == 0 else (-1.0, 0.0, 0.0)

                    TransactionManager.Instance.EnsureInTransaction(doc)
                    hachura = id_hachura_solida(doc)
                    cache_mat = {}
                    ok, falhas = 0, []

                    for p in plano:
                        el = p['el']
                        try:
                            if modo == "marcar":
                                if escrever_marcacao(el, p['casa'], p['papel'],
                                                     p.get('regra', u"?")):
                                    ok += 1
                                else:
                                    falhas.append((id_valor(el.Id),
                                                   u"'{0}' não editável".format(PARAM_MARCACAO)))
                            elif modo == "override":
                                vista.SetElementOverrides(
                                    el.Id, montar_override(cor_revit(p['hex']), hachura))
                                ok += 1
                            elif modo == "material":
                                mat = obter_material(doc, p['hex'], cache_mat, hachura)
                                if aplicar_material(el, mat):
                                    ok += 1
                                else:
                                    falhas.append((id_valor(el.Id),
                                                   u"sem parâmetro de material editável"))
                            else:  # paint
                                mat = obter_material(doc, p['hex'], cache_mat, hachura)
                                faces = faces_da_fachada(el, direcao)
                                if not faces:
                                    falhas.append((id_valor(el.Id), u"nenhuma face de fachada"))
                                else:
                                    for face in faces:
                                        try:
                                            if doc.IsPainted(el.Id, face):
                                                doc.RemovePaint(el.Id, face)
                                        except Exception:
                                            pass
                                        doc.Paint(el.Id, face, mat.Id)
                                    ok += 1
                        except Exception as erro:
                            falhas.append((id_valor(el.Id), str(erro)))

                    TransactionManager.Instance.TransactionTaskDone()

                    resumo.append(u"Aplicado em {0} elemento(s).".format(ok))
                    if falhas:
                        resumo.append(u"{0} falha(s):".format(len(falhas)))
                        for eid, msg in falhas[:20]:
                            resumo.append(u"   id {0}: {1}".format(eid, msg))

                    return [resumo, detalhe]


try:
    OUT = principal()
except Exception:
    # sem isto, qualquer erro faz o no devolver null e voce fica sem pista
    import traceback
    resumo.append(u"=== ERRO NAO TRATADO — copie o bloco abaixo ===")
    for _l in traceback.format_exc().splitlines():
        resumo.append(_l)
    OUT = [resumo, detalhe]
