# -*- coding: utf-8 -*-
"""
PintarFachadas — nó Python para Dynamo (Revit)
==============================================

Aplica uma paleta de 8 trios de cores a fachadas de casas dispostas lado a lado.
Cada CASA recebe EXATAMENTE 3 CORES, não importa de quantos elementos ela seja
feita: a casa é dividida em 3 FAIXAS e cada faixa inteira recebe uma cor do trio.
A partir da casa 9 a paleta reinicia (ciclo por módulo).

ENTRADAS DO NÓ (portas IN):
    IN[0]  eixo      : "AUTO" | "X" | "Y"
                       Eixo em que a fileira de casas se estende.
    IN[1]  modo      : "override" | "material" | "paint" | "limpar"
    IN[2]  casas     : como separar uma casa da outra —
                       um NÚMERO inteiro  -> divide a fileira nesse nº de casas iguais
                       "gap"              -> quebra onde há vão entre as casas
                       "parametro"        -> agrupa pelo valor de PARAM_GRUPO
                       "trios"            -> modo antigo: fatia de 3 em 3 elementos
    IN[3]  faixas    : eixo das 3 faixas DENTRO de cada casa —
                       "EIXO" (padrão, mesmo eixo da fileira = listras verticais),
                       "X" | "Y" | "Z" (Z = faixas horizontais empilhadas) | "AUTO"
    IN[4]  executar  : bool -> False = simulação (nada é alterado no modelo)

SAÍDA (OUT):
    [resumo (list<str>), detalhe (list<list>)]
    detalhe = casa | trio | faixa | hex | id | nome

SELEÇÃO:
    O script lê a seleção ativa do Revit (uidoc.Selection). Selecione os elementos
    no Revit, volte ao Dynamo e rode. Grupos do Revit são expandidos em seus membros.
    Se a seleção estiver vazia, cai para CATEGORIAS_FALLBACK na vista ativa.

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

FAIXAS_POR_CASA = 3


# ---------------------------------------------------------------------------
# 2. AJUSTES — edite aqui, não precisa mexer no resto
# ---------------------------------------------------------------------------

# Como as 3 faixas são repartidas dentro da casa:
#   "extensao" -> divide a largura (ou altura) da casa em 3 partes iguais
#   "quantil"  -> divide de modo que as 3 faixas tenham ~o mesmo nº de elementos
FAIXAS_METODO = "extensao"

INVERTER_ORDEM_FAIXAS = False     # inverte cor1/cor2/cor3 dentro da casa
INVERTER_ORDEM_CASAS = False      # percorre as casas da direita para a esquerda

# casas == "gap": distância mínima (em pés) entre elementos vizinhos para
# considerar que começou outra casa. 0 = calcula sozinho a partir da mediana.
# Para casas GEMINADAS (sem vão entre elas) o "gap" não funciona — use o número.
TOLERANCIA_GAP = 0.0

# casas == "parametro": nome do parâmetro de texto que identifica a casa.
PARAM_GRUPO = "Comentários"

# Usado quando a seleção do Revit está vazia.
CATEGORIAS_FALLBACK = [
    DB.BuiltInCategory.OST_Walls,
    DB.BuiltInCategory.OST_Parts,
    DB.BuiltInCategory.OST_GenericModel,
]

# modo == "paint": direção para onde a fachada olha, em coordenadas do modelo.
# None = deduz do eixo da fileira (fileira em X -> fachada em -Y; em Y -> -X).
DIRECAO_FACHADA = None            # ex.: [0.0, -1.0, 0.0]

PREFIXO_MATERIAL = "ZYLO_FACHADA_"


# ---------------------------------------------------------------------------
# 3. Utilitários
# ---------------------------------------------------------------------------

def _entrada(indice, padrao):
    """Lê IN[indice] com fallback, sem quebrar fora do Dynamo."""
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
# 4. Coleta da seleção
# ---------------------------------------------------------------------------

def expandir(elemento, doc):
    """Grupos do Revit viram seus membros; o resto passa direto."""
    if isinstance(elemento, DB.Group):
        saida = []
        for mid in elemento.GetMemberIds():
            membro = doc.GetElement(mid)
            if membro is not None:
                saida.extend(expandir(membro, doc))
        return saida
    return [elemento]


def coletar(doc, uidoc, log):
    brutos = []
    try:
        for eid in uidoc.Selection.GetElementIds():
            el = doc.GetElement(eid)
            if el is not None:
                brutos.extend(expandir(el, doc))
    except Exception as erro:
        log.append(u"Não consegui ler a seleção do Revit: {0}".format(erro))

    if not brutos:
        log.append(u"Seleção vazia — coletando CATEGORIAS_FALLBACK na vista ativa.")
        for bic in CATEGORIAS_FALLBACK:
            try:
                col = DB.FilteredElementCollector(doc, doc.ActiveView.Id) \
                        .OfCategory(bic).WhereElementIsNotElementType()
                brutos.extend(list(col))
            except Exception:
                continue

    validos, vistos = [], set()
    for el in brutos:
        chave = id_valor(el.Id)
        if chave in vistos:
            continue
        if getattr(el, 'Category', None) is None:
            continue
        if caixa(el, doc) is None:
            continue
        vistos.add(chave)
        validos.append(el)
    return validos


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


def casas_por_numero(dados, eixo, quantidade, log):
    """Divide a extensão total da fileira em N fatias iguais. É o modo mais
    confiável para casas geminadas, onde não existe vão para detectar."""
    vmin, vmax = extensao(dados, eixo)
    largura = (vmax - vmin) / float(quantidade)
    if largura <= 0:
        return [list(dados)]
    grupos = [[] for _ in range(quantidade)]
    for d in dados:
        i = int((d['c'][eixo] - vmin) / largura)
        if i < 0:
            i = 0
        if i >= quantidade:
            i = quantidade - 1
        grupos[i].append(d)
    log.append(u"Fileira de {0:.1f} ft dividida em {1} casas de ~{2:.1f} ft.".format(
        vmax - vmin, quantidade, largura))
    return [g for g in grupos if g]


def casas_por_gap(dados, eixo, log):
    """Quebra a fila onde aparece um vão maior que a tolerância.
    Usa a borda do bounding box, não o centro — assim a largura do elemento
    não é confundida com espaçamento."""
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
                   u"são geminadas (sem vão). Troque IN[2] pelo número de casas.")
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
    grupos = list(baldes.values())
    grupos.sort(key=lambda g: min(d['c'][eixo] for d in g))
    return grupos


def casas_por_trios(dados, eixo, log):
    """Modo antigo: fatia a lista ordenada de 3 em 3. Só serve se cada casa
    tiver exatamente 3 elementos."""
    ordenados = _ordenar(dados, eixo)
    grupos = [ordenados[i:i + 3] for i in range(0, len(ordenados), 3)]
    if len(dados) % 3:
        log.append(u"AVISO: {0} elementos não é múltiplo de 3 — o modo 'trios' "
                   u"vai deslocar as cores.".format(len(dados)))
    return grupos


# ---------------------------------------------------------------------------
# 6. Passo 2 — repartir cada casa em 3 FAIXAS (1 cor por faixa)
# ---------------------------------------------------------------------------

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
    else:                                   # "EIXO" e qualquer coisa não prevista
        eixo = eixo_fileira
    log.append(u"Faixas repartidas no eixo {0} ({1}){2}".format(
        "XYZ"[eixo],
        u"listras verticais" if eixo != 2 else u"faixas horizontais empilhadas",
        u", ordem invertida" if INVERTER_ORDEM_FAIXAS else u""))
    return eixo


def repartir_em_faixas(grupo, eixo_faixa, n=FAIXAS_POR_CASA):
    """Devolve n listas. Elementos podem ser 3 ou 300 — a casa continua com n cores."""
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
            k = int(i / corte)
            faixas[min(k, n - 1)].append(d)
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
    nomes_nossos = set()
    for mat in DB.FilteredElementCollector(doc).OfClass(DB.Material):
        if mat.Name.startswith(PREFIXO_MATERIAL):
            nomes_nossos.add(id_valor(mat.Id))
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
casas_pedido = _entrada(2, "gap")
faixas_pedido = _entrada(3, "EIXO")
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
    elementos = coletar(doc, uidoc, resumo)

    if not elementos:
        resumo.append(u"ERRO: nenhum elemento válido. Selecione as fachadas no Revit "
                      u"e rode de novo.")
        OUT = [resumo, detalhe]

    elif modo == "limpar":
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
        dados = []
        for el in elementos:
            bb = caixa(el, doc)
            dados.append({'el': el, 'bb': bb, 'c': centro(bb)})

        eixo = escolher_eixo(dados, eixo_pedido, resumo)

        # --- passo 1: separar as casas ---
        numero_casas = None
        try:
            numero_casas = int(casas_pedido)
        except (TypeError, ValueError):
            numero_casas = None

        if numero_casas is not None and numero_casas > 0:
            grupos = casas_por_numero(dados, eixo, numero_casas, resumo)
            metodo_casas = u"{0} casas iguais".format(numero_casas)
        else:
            chave = str(casas_pedido).lower().strip()
            if chave == "parametro":
                grupos = casas_por_parametro(dados, eixo, resumo)
                metodo_casas = u"parâmetro '{0}'".format(PARAM_GRUPO)
            elif chave == "trios":
                grupos = casas_por_trios(dados, eixo, resumo)
                metodo_casas = u"trios (3 elementos por casa)"
            else:
                grupos = casas_por_gap(dados, eixo, resumo)
                metodo_casas = u"vão entre casas"

        grupos = [g for g in grupos if g]
        grupos.sort(key=lambda g: min(d['c'][eixo] for d in g))
        if INVERTER_ORDEM_CASAS:
            grupos.reverse()

        # --- passo 2: 3 faixas por casa, 1 cor por faixa ---
        eixo_faixa = escolher_eixo_faixa(faixas_pedido, eixo, grupos, resumo)

        plano = []
        distribuicao = []
        for indice_casa, grupo in enumerate(grupos):
            trio_idx = indice_casa % len(PALETA_HEX)          # o ciclo da paleta
            trio = PALETA_HEX[trio_idx]
            faixas = repartir_em_faixas(grupo, eixo_faixa)
            if INVERTER_ORDEM_FAIXAS:
                faixas.reverse()
            distribuicao.append((indice_casa + 1, len(grupo), [len(f) for f in faixas]))
            for k, faixa in enumerate(faixas):
                for d in faixa:
                    plano.append({'casa': indice_casa + 1, 'trio': trio_idx + 1,
                                  'faixa': k + 1, 'hex': trio[k], 'el': d['el']})

        resumo.append(u"{0} elemento(s) -> {1} casa(s) [{2}] -> 3 faixas por casa "
                      u"-> trios 1..8 em ciclo.".format(
                          len(elementos), len(grupos), metodo_casas))
        resumo.append(u"Modo: {0} | eixo da fileira: {1}".format(modo, "XYZ"[eixo]))

        vazias = [(c, b) for c, _, b in distribuicao if 0 in b]
        if vazias:
            resumo.append(u"AVISO: {0} casa(s) ficaram com menos de 3 faixas "
                          u"preenchidas (ex.: casa {1} -> {2}). Essas vão mostrar "
                          u"menos de 3 cores.".format(len(vazias), vazias[0][0], vazias[0][1]))
        resumo.append(u"Distribuição casa -> total (faixa1/faixa2/faixa3):")
        for c, total, bandas in distribuicao[:15]:
            resumo.append(u"   casa {0}: {1} elem ({2})".format(
                c, total, "/".join([str(b) for b in bandas])))
        if len(distribuicao) > 15:
            resumo.append(u"   ... mais {0} casa(s)".format(len(distribuicao) - 15))

        for p in plano:
            detalhe.append([p['casa'], p['trio'], p['faixa'], p['hex'],
                            id_valor(p['el'].Id), p['el'].Name])

        if not executar:
            resumo.insert(0, u"*** SIMULAÇÃO — ligue 'executar' para aplicar. ***")
            OUT = [resumo, detalhe]
        elif modo == "override" and not vista.AreGraphicsOverridesAllowed():
            resumo.append(u"ERRO: a vista '{0}' não aceita sobrescrita de gráficos.".format(
                vista.Name))
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
