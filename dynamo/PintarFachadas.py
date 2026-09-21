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
    detalhe = casa | trio | papel | hex | id | nome

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

# Onde a parede se divide entre "baixo" e "cima", como fração da altura da casa.
# 0.5 = na metade. 0.6 = a faixa de baixo ocupa 60% da altura.
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

def expandir(elemento, doc, chave_casa):
    """Group do Revit vira seus membros, todos carimbados com a chave do bloco."""
    if isinstance(elemento, DB.Group):
        chave = id_valor(elemento.Id)
        saida = []
        for mid in elemento.GetMemberIds():
            membro = doc.GetElement(mid)
            if membro is not None:
                saida.extend(expandir(membro, doc, chave))
        return saida
    return [(elemento, chave_casa)]


def _chave_do_grupo(elemento):
    """Se o elemento já pertence a um Group, usa o id do Group como chave."""
    try:
        gid = elemento.GroupId
        if gid is not None and id_valor(gid) > 0:
            return id_valor(gid)
    except Exception:
        pass
    return None


def textos_do_elemento(elemento, doc):
    """Nome do elemento, do tipo, da família e da categoria — para classificar."""
    textos = []
    for getter in (lambda: elemento.Name,
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
                brutos.extend(expandir(el, doc, None))
    except Exception as erro:
        log.append(u"Não consegui ler a seleção do Revit: {0}".format(erro))

    if not brutos:
        log.append(u"Seleção vazia — coletando CATEGORIAS_FALLBACK na vista ativa.")
        for bic in CATEGORIAS_FALLBACK:
            try:
                col = DB.FilteredElementCollector(doc, doc.ActiveView.Id) \
                        .OfCategory(bic).WhereElementIsNotElementType()
                brutos.extend([(e, None) for e in col])
            except Exception:
                continue

    dados, vistos = [], set()
    for el, chave in brutos:
        eid = id_valor(el.Id)
        if eid in vistos:
            continue
        if getattr(el, 'Category', None) is None:
            continue
        bb = caixa(el, doc)
        if bb is None:
            continue
        vistos.add(eid)
        if chave is None:
            chave = _chave_do_grupo(el)
        try:
            cat_id = id_valor(el.Category.Id)
            cat_nome = el.Category.Name
        except Exception:
            cat_id, cat_nome = -1, u"?"
        dados.append({'el': el, 'bb': bb, 'c': centro(bb), 'casa': chave,
                      'cat_id': cat_id, 'cat': cat_nome,
                      'textos': textos_do_elemento(el, doc)})
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


def e_moldura(d, ids_moldura):
    """Classifica um elemento como moldura de esquadria: por categoria primeiro,
    por palavra no nome depois."""
    if d.get('cat_id') in ids_moldura:
        return True
    alvo = u" ".join([normalizar(t) for t in d.get('textos', [])])
    for palavra in PALAVRAS_MOLDURA:
        if palavra in alvo:
            return True
    return False


def repartir_fachada(grupo, ids_moldura):
    """cima / baixo / moldura. A cota de corte é calculada por casa, a partir
    da altura da própria parede — terreno inclinado não estraga o resultado."""
    papeis = {"cima": [], "baixo": [], "moldura": []}
    parede = []
    for d in grupo:
        if e_moldura(d, ids_moldura):
            papeis["moldura"].append(d)
        else:
            parede.append(d)

    if not parede:
        return papeis

    if CORTE_ABSOLUTO is not None:
        corte = float(CORTE_ABSOLUTO)
    else:
        z0 = min(d['bb'][0][2] for d in parede)
        z1 = max(d['bb'][1][2] for d in parede)
        corte = z0 + (z1 - z0) * float(CORTE_ALTURA)

    for d in parede:
        papeis["cima" if d['c'][2] >= corte else "baixo"].append(d)
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

doc = DocumentManager.Instance.CurrentDBDocument
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument
vista = doc.ActiveView

resumo = []
detalhe = []

MODOS = ("override", "material", "paint", "limpar")

if modo not in MODOS:
    resumo.append(u"ERRO: modo '{0}' desconhecido. Use: {1}.".format(modo, ", ".join(MODOS)))
    OUT = [resumo, detalhe]
else:
    dados = coletar(doc, uidoc, resumo)

    if not dados:
        resumo.append(u"ERRO: nenhum elemento válido. Selecione as casas no Revit "
                      u"e rode de novo.")
        OUT = [resumo, detalhe]

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
                n, vista.Name))
        OUT = [resumo, detalhe]

    else:
        inventario(dados, resumo)
        eixo = escolher_eixo(dados, eixo_pedido, resumo)

        # --- passo 1: separar as casas ---
        try:
            numero_casas = int(casas_pedido)
        except (TypeError, ValueError):
            numero_casas = None

        if numero_casas is not None and numero_casas > 0:
            grupos = casas_por_numero(dados, eixo, numero_casas, resumo)
            metodo_casas = u"{0} casas iguais".format(numero_casas)
        else:
            chave = normalizar(str(casas_pedido)).strip()
            if chave == "grupo":
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
            OUT = [resumo, detalhe]
        else:
            grupos.sort(key=lambda g: min(d['c'][eixo] for d in g))
            if INVERTER_ORDEM_CASAS:
                grupos.reverse()

            # --- passo 2: repartir cada casa ---
            por_papel = normalizar(str(faixas_pedido)).strip() == "fachada"

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
            for indice_casa, grupo in enumerate(grupos):
                trio_idx = indice_casa % len(PALETA_HEX)      # o ciclo da paleta
                trio = PALETA_HEX[trio_idx]

                if por_papel:
                    papeis = repartir_fachada(grupo, ids_moldura)
                    partes = [(PAPEL_DAS_CORES[k], papeis.get(PAPEL_DAS_CORES[k], []))
                              for k in range(3)]
                else:
                    faixas = repartir_em_faixas(grupo, eixo_faixa)
                    if INVERTER_ORDEM_FAIXAS:
                        faixas.reverse()
                    partes = [(u"faixa{0}".format(k + 1), faixas[k]) for k in range(3)]

                distribuicao.append((indice_casa + 1, len(grupo),
                                     [(nome, len(itens)) for nome, itens in partes]))
                for k, (nome, itens) in enumerate(partes):
                    for d in itens:
                        plano.append({'casa': indice_casa + 1, 'trio': trio_idx + 1,
                                      'papel': nome, 'hex': trio[k], 'el': d['el']})

            resumo.append(u"{0} elemento(s) -> {1} casa(s) [{2}] -> 3 cores por casa "
                          u"-> trios 1..8 em ciclo.".format(
                              len(dados), len(grupos), metodo_casas))
            resumo.append(u"Modo: {0} | eixo da fileira: {1}".format(modo, "XYZ"[eixo]))

            vazios = [c for c, _, partes in distribuicao if any(n == 0 for _, n in partes)]
            if vazios:
                resumo.append(u"AVISO: {0} casa(s) com algum papel vazio (vão mostrar "
                              u"menos de 3 cores). Primeiras: {1}".format(
                                  len(vazios), ", ".join([str(c) for c in vazios[:8]])))
            resumo.append(u"Distribuição casa -> total (papel: nº de elementos):")
            for c, total, partes in distribuicao[:15]:
                resumo.append(u"   casa {0}: {1} elem  ({2})".format(
                    c, total, ", ".join([u"{0}={1}".format(n, q) for n, q in partes])))
            if len(distribuicao) > 15:
                resumo.append(u"   ... mais {0} casa(s)".format(len(distribuicao) - 15))

            for p in plano:
                detalhe.append([p['casa'], p['trio'], p['papel'], p['hex'],
                                id_valor(p['el'].Id), p['el'].Name])

            if not executar:
                resumo.insert(0, u"*** SIMULAÇÃO — ligue 'executar' para aplicar. ***")
                OUT = [resumo, detalhe]
            elif modo == "override" and not vista.AreGraphicsOverridesAllowed():
                resumo.append(u"ERRO: a vista '{0}' não aceita sobrescrita de "
                              u"gráficos.".format(vista.Name))
                OUT = [resumo, detalhe]
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
                        if modo == "override":
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

                OUT = [resumo, detalhe]
