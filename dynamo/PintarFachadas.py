# -*- coding: utf-8 -*-
"""
PintarFachadas — nó Python para Dynamo (Revit)
==============================================

Aplica uma paleta de 8 trios de cores a fachadas de casas geminadas / lado a lado.
Cada casa é um grupo de 3 elementos; cada elemento recebe uma cor do trio, na ordem.
A partir da casa 9 a paleta reinicia (ciclo por módulo).

ENTRADAS DO NÓ (portas IN):
    IN[0]  eixo          : "X" | "Y" | "AUTO"        -> eixo de ordenação das casas
    IN[1]  modo          : "override" | "material" | "paint"
    IN[2]  agrupamento   : "trios" | "gap" | "parametro"
    IN[3]  executar      : bool -> False = simulação (nada é alterado no modelo)

SAÍDA (OUT):
    [resumo (list<str>), detalhe (list<list>)]

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

ELEMENTOS_POR_CASA = 3


# ---------------------------------------------------------------------------
# 2. AJUSTES — edite aqui, não precisa mexer no resto
# ---------------------------------------------------------------------------

# Ordem das 3 cores DENTRO de cada casa. "AUTO" escolhe o eixo com maior
# dispersão média entre os 3 elementos (bom tanto para faixas verticais
# lado a lado quanto para faixas empilhadas).
ORDEM_INTERNA = "AUTO"            # "AUTO" | "X" | "Y" | "Z"
INVERTER_ORDEM_INTERNA = False    # True inverte a ordem cor1/cor2/cor3 na casa
INVERTER_ORDEM_CASAS = False      # True percorre as casas da direita para a esquerda

# agrupamento == "gap": distância mínima (em pés) entre centros consecutivos
# para considerar que começou outra casa. 0 = calcula sozinho a partir da mediana.
TOLERANCIA_GAP = 0.0

# agrupamento == "parametro": nome do parâmetro de texto que identifica a casa
# (ex.: "Comentários", "Marca", "Comments", "Mark").
PARAM_GRUPO = "Comentários"

# Usado quando a seleção do Revit está vazia.
CATEGORIAS_FALLBACK = [
    DB.BuiltInCategory.OST_Walls,
    DB.BuiltInCategory.OST_Parts,
    DB.BuiltInCategory.OST_GenericModel,
]

# modo == "paint": direção para onde a fachada olha, em coordenadas do modelo.
# None = deduz do eixo principal (linha em X -> fachada em -Y; linha em Y -> -X).
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
    """Equivalente ao Color.ByARGB do Dynamo, mas já em Autodesk.Revit.DB.Color."""
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

    # descarta o que não tem categoria ou não tem bounding box
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
# 5. Ordenação e agrupamento
# ---------------------------------------------------------------------------

EIXOS = {"X": 0, "Y": 1, "Z": 2}


def escolher_eixo(dados, eixo_pedido, log):
    if str(eixo_pedido).upper() in ("X", "Y"):
        return EIXOS[str(eixo_pedido).upper()]
    espalhamento = []
    for i in (0, 1):
        valores = [d['c'][i] for d in dados]
        espalhamento.append(max(valores) - min(valores))
    eixo = 0 if espalhamento[0] >= espalhamento[1] else 1
    log.append(u"Eixo AUTO -> {0} (dispersão X={1:.2f} ft, Y={2:.2f} ft)".format(
        "XY"[eixo], espalhamento[0], espalhamento[1]))
    return eixo


def agrupar_trios(dados, eixo):
    """Ordena tudo pelo eixo e fatia de 3 em 3 (List.SortByKey + List.Chop)."""
    secundario = 1 - eixo if eixo in (0, 1) else 1
    ordenados = sorted(dados, key=lambda d: (d['c'][eixo], d['c'][secundario], d['c'][2]))
    return [ordenados[i:i + ELEMENTOS_POR_CASA]
            for i in range(0, len(ordenados), ELEMENTOS_POR_CASA)]


def agrupar_gap(dados, eixo, log):
    """Quebra a fila onde aparece um vão maior que a tolerância."""
    secundario = 1 - eixo if eixo in (0, 1) else 1
    ordenados = sorted(dados, key=lambda d: (d['c'][eixo], d['c'][secundario], d['c'][2]))
    gaps = [ordenados[i + 1]['c'][eixo] - ordenados[i]['c'][eixo]
            for i in range(len(ordenados) - 1)]
    tol = TOLERANCIA_GAP
    if tol <= 0:
        base = mediana([g for g in gaps if g > 1e-6]) or 1.0
        tol = base * 2.5
        log.append(u"Tolerância de gap automática: {0:.2f} ft".format(tol))
    grupos, atual = [], [ordenados[0]] if ordenados else []
    for i in range(len(ordenados) - 1):
        if gaps[i] > tol:
            grupos.append(atual)
            atual = []
        atual.append(ordenados[i + 1])
    if atual:
        grupos.append(atual)
    return grupos


def agrupar_parametro(dados, eixo, log):
    """Agrupa pelo valor de PARAM_GRUPO; ordena as casas pelo eixo escolhido."""
    baldes = {}
    sem_valor = 0
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


def eixo_interno(grupos):
    """Descobre em qual eixo os 3 elementos de uma casa se distribuem."""
    if str(ORDEM_INTERNA).upper() in EIXOS:
        return EIXOS[str(ORDEM_INTERNA).upper()]
    medias = []
    for i in (0, 1, 2):
        acumulado = []
        for g in grupos:
            if len(g) < 2:
                continue
            valores = [d['c'][i] for d in g]
            acumulado.append(max(valores) - min(valores))
        medias.append(sum(acumulado) / len(acumulado) if acumulado else 0.0)
    return medias.index(max(medias))


# ---------------------------------------------------------------------------
# 6. Aplicação das cores
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


# ---------------------------------------------------------------------------
# 7. Execução
# ---------------------------------------------------------------------------

eixo_pedido = str(_entrada(0, "AUTO")).upper()
modo = str(_entrada(1, "override")).lower().strip()
agrupamento = str(_entrada(2, "trios")).lower().strip()
executar = bool(_entrada(3, False))

doc = DocumentManager.Instance.CurrentDBDocument
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument
vista = doc.ActiveView

resumo = []
detalhe = []

if modo not in ("override", "material", "paint"):
    resumo.append(u"ERRO: modo '{0}' desconhecido. Use override, material ou paint.".format(modo))
    OUT = [resumo, detalhe]
else:
    elementos = coletar(doc, uidoc, resumo)

    if not elementos:
        resumo.append(u"ERRO: nenhum elemento válido. Selecione as fachadas no Revit e rode de novo.")
        OUT = [resumo, detalhe]
    else:
        dados = []
        for el in elementos:
            bb = caixa(el, doc)
            dados.append({'el': el, 'bb': bb, 'c': centro(bb)})

        eixo = escolher_eixo(dados, eixo_pedido, resumo)

        if agrupamento == "gap":
            grupos = agrupar_gap(dados, eixo, resumo)
        elif agrupamento == "parametro":
            grupos = agrupar_parametro(dados, eixo, resumo)
        else:
            grupos = agrupar_trios(dados, eixo)

        if INVERTER_ORDEM_CASAS:
            grupos.reverse()

        # --- validação: sem isso o trio "escorrega" e tudo sai deslocado ---
        fora_do_padrao = [(i + 1, len(g)) for i, g in enumerate(grupos)
                          if len(g) != ELEMENTOS_POR_CASA]
        if fora_do_padrao:
            resumo.append(u"ATENÇÃO: {0} casa(s) não têm exatamente {1} elementos: {2}".format(
                len(fora_do_padrao), ELEMENTOS_POR_CASA,
                ", ".join([u"casa {0}={1}".format(a, b) for a, b in fora_do_padrao[:10]])))
            resumo.append(u"   As cores desses grupos vão ficar truncadas. "
                          u"Revise a seleção ou troque o agrupamento para 'gap'/'parametro'.")

        eixo_i = eixo_interno(grupos)
        resumo.append(u"Ordem interna do trio: eixo {0}{1}".format(
            "XYZ"[eixo_i], u" (invertida)" if INVERTER_ORDEM_INTERNA else u""))

        if DIRECAO_FACHADA:
            direcao = tuple(DIRECAO_FACHADA)
        else:
            direcao = (0.0, -1.0, 0.0) if eixo == 0 else (-1.0, 0.0, 0.0)

        # --- monta o plano de pintura (ainda sem tocar no modelo) ---
        plano = []
        for indice_casa, grupo in enumerate(grupos):
            trio_idx = indice_casa % len(PALETA_HEX)           # o "ciclo" da paleta
            trio = PALETA_HEX[trio_idx]
            ordenado = sorted(grupo, key=lambda d: d['c'][eixo_i])
            if INVERTER_ORDEM_INTERNA:
                ordenado.reverse()
            for pos, d in enumerate(ordenado):
                if pos >= len(trio):
                    break
                plano.append({
                    'casa': indice_casa + 1,
                    'trio': trio_idx + 1,
                    'pos': pos + 1,
                    'hex': trio[pos],
                    'el': d['el'],
                })

        resumo.append(u"{0} elemento(s) -> {1} casa(s) -> trios 1..8 em ciclo.".format(
            len(elementos), len(grupos)))
        resumo.append(u"Modo: {0} | eixo das casas: {1} | agrupamento: {2}".format(
            modo, "XYZ"[eixo], agrupamento))

        if not executar:
            resumo.insert(0, u"*** SIMULAÇÃO — ligue 'executar' para aplicar. ***")
            for p in plano:
                detalhe.append([p['casa'], p['trio'], p['pos'], p['hex'],
                                id_valor(p['el'].Id), p['el'].Name])
            OUT = [resumo, detalhe]
        else:
            if modo == "override" and not vista.AreGraphicsOverridesAllowed():
                resumo.append(u"ERRO: a vista '{0}' não aceita sobrescrita de gráficos.".format(vista.Name))
                OUT = [resumo, detalhe]
            else:
                TransactionManager.Instance.EnsureInTransaction(doc)
                hachura = id_hachura_solida(doc)
                cache_mat = {}
                ok, falhas = 0, []

                for p in plano:
                    el = p['el']
                    try:
                        if modo == "override":
                            vista.SetElementOverrides(el.Id, montar_override(cor_revit(p['hex']), hachura))
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
                                falhas.append((id_valor(el.Id), u"nenhuma face de fachada encontrada"))
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

                    detalhe.append([p['casa'], p['trio'], p['pos'], p['hex'],
                                    id_valor(el.Id), el.Name])

                TransactionManager.Instance.TransactionTaskDone()

                resumo.append(u"Aplicado em {0} elemento(s).".format(ok))
                if falhas:
                    resumo.append(u"{0} falha(s):".format(len(falhas)))
                    for eid, msg in falhas[:20]:
                        resumo.append(u"   id {0}: {1}".format(eid, msg))

                OUT = [resumo, detalhe]
