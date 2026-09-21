# -*- coding: utf-8 -*-
"""Roda o ARQUIVO INTEIRO de PintarFachadas.py (inclusive o corpo principal)
contra um Revit falso, para pegar erro de execucao que os testes de funcao pura
nao pegam. Rode: python3 dynamo/teste_integracao.py"""
import sys, types


# --------------------------------------------------------------------------
# Revit falso
# --------------------------------------------------------------------------
class Id(object):
    def __init__(self, v): self.Value = v; self.IntegerValue = v
    def __eq__(self, o): return isinstance(o, Id) and o.Value == self.Value
    def __ne__(self, o): return not self.__eq__(o)
    def __hash__(self): return hash(self.Value)
    def __repr__(self): return "Id(%s)" % self.Value


class P(object):
    def __init__(self, x, y, z): self.X, self.Y, self.Z = x, y, z


class T(object):
    def OfPoint(self, p): return p


class BBox(object):
    def __init__(self, mn, mx): self.Min, self.Max, self.Transform = mn, mx, T()


class Face(object):
    def __init__(self, nx, ny, nz, area):
        self.FaceNormal, self.Area = P(nx, ny, nz), area


class Faces(list):
    @property
    def Size(self): return len(self)


class Solid(object):
    def __init__(self, faces): self.Faces, self.Volume = Faces(faces), 1.0


class Cat(object):
    def __init__(self, i, nome): self.Id, self.Name = Id(i), nome


class Par(object):
    StorageType = 2                      # DB.StorageType.String
    def __init__(self, valor=""): self.valor, self.IsReadOnly = valor, False
    @property
    def HasValue(self): return bool(self.valor)
    def AsString(self): return self.valor
    def AsValueString(self): return self.valor
    def AsElementId(self): return Id(-1)
    def Set(self, v): self.valor = v; return True


class Nivel(object):
    def __init__(self, eid, elev): self.Id, self.Elevation = Id(eid), elev


class Elem(object):
    Parameters = []
    def __init__(self, eid, nome, cat, bb, group=None, nivel=None, tipo_id=None):
        self.Id, self.Name, self.Category, self._bb = Id(eid), nome, cat, bb
        # tipos propositalmente COMPARTILHADOS entre casas, como no modelo real
        self._tipo_id = tipo_id if tipo_id is not None else (6000 + hash(nome) % 3)
        self.GroupId = Id(group) if group is not None else Id(-1)
        self.LevelId = Id(nivel) if nivel is not None else Id(-1)
        self._pars = {"Comentários": Par()}
    def get_BoundingBox(self, v): return self._bb
    def GetTypeId(self): return Id(self._tipo_id)
    def get_Geometry(self, opt):
        return [Solid([Face(0.0, -1.0, 0.0, 10.0), Face(0.0, 1.0, 0.0, 10.0),
                       Face(0.0, 0.0, 1.0, 30.0)])]
    def get_Parameter(self, bip): return None
    def LookupParameter(self, n): return self._pars.get(n)


class TipoGrupo(object):
    def __init__(self, eid, marca):
        self.Id, self.Name, self._marca = Id(eid), "TipoCasa%s" % marca, str(marca)
    def get_Parameter(self, bip):
        return Par(self._marca) if bip == "TYPEMARK" else None
    def LookupParameter(self, n): return None


class Group(Elem):
    def __init__(self, eid, membros, bb, tipo=None):
        Elem.__init__(self, eid, "Grupo %s" % eid, Cat(-2, "Grupos"), bb)
        self._m, self._tipo = membros, tipo
    def GetMemberIds(self): return [Id(m) for m in self._m]
    def GetTypeId(self): return Id(self._tipo) if self._tipo else Id(-1)


class View(object):
    Id = Id(1)
    Name = "Elevacao Sul"
    ViewType = "ThreeD"
    DisplayStyle = "HLR"          # Linha Oculta: material NAO aparece
    def __init__(self): self.overrides = {}
    def AreGraphicsOverridesAllowed(self): return True
    def SetElementOverrides(self, eid, ogs): self.overrides[eid.Value] = ogs


MATERIAIS = []
ASSETS = []


class Mat(object):
    def __init__(self, eid, nome):
        self.Id, self.Name = Id(eid), nome
        self.Color = self.AppearanceAssetId = None
        self.UseRenderAppearanceForShading = True
        self.Transparency = 50
        self.SurfaceForegroundPatternId = self.SurfaceForegroundPatternColor = None


class Collector(object):
    def __init__(self, *a): self._c = None
    def OfClass(self, c): self._c = c; return self
    def OfCategory(self, c): return self
    def WhereElementIsNotElementType(self): return self
    def __iter__(self):
        if self._c is DBMod.Material:
            return iter(MATERIAIS)
        if self._c is DBMod.AppearanceAssetElement:
            return iter(ASSETS)
        return iter([])


class OGS(object):
    def __init__(self): self.set = []
    def __getattr__(self, nome):
        if nome.startswith("Set"):
            def f(*a): self.set.append(nome); return self
            return f
        raise AttributeError(nome)


class Doc(object):
    def __init__(self, elementos):
        self._m = dict((e.Id.Value, e) for e in elementos)
        self.ActiveView = View()
    def GetElement(self, eid):
        return self._m.get(eid.Value)
    def __init_pintura__(self):
        self.pintado = {}
    def IsPainted(self, eid, face): return eid.Value in getattr(self, "pintado", {})
    def Paint(self, eid, face, mid):
        if not hasattr(self, "pintado"): self.pintado = {}
        self.pintado[eid.Value] = mid.Value
    def RemovePaint(self, eid, face): getattr(self, "pintado", {}).pop(eid.Value, None)


class Sel(object):
    def __init__(self, ids): self._ids = [Id(i) for i in ids]
    def GetElementIds(self): return self._ids


class DBMod(types.ModuleType):
    Group = Group
    ElementId = type("EId", (), {"InvalidElementId": Id(-1)})
    OverrideGraphicSettings = OGS
    FilteredElementCollector = Collector
    FillPatternElement = type("FPE", (), {})
    Material = Mat
    Solid = Solid
    GeometryInstance = type("GI", (), {})
    PlanarFace = Face
    Options = type("Opt", (), {})
    ViewDetailLevel = type("VDL", (), {"Fine": 1})
    DisplayStyle = type("DS", (), {"ShadingWithEdges": "ShadingWithEdges"})
    FillPatternTarget = type("FPT", (), {"Drafting": 1})
    StorageType = type("ST", (), {"ElementId": 1, "String": 2})
    SpecTypeId = type("STI", (), {"Reference": type("R", (), {"Material": 1})})
    BuiltInParameter = type("BIP", (), {"ALL_MODEL_TYPE_MARK": "TYPEMARK",
                                        "ALL_MODEL_MARK": "MARK"})
    Category = type("C", (), {"GetCategory": staticmethod(lambda doc, bic: Cat(bic, "cat"))})
    def Color(self, *a): return a


DB = DBMod("Autodesk.Revit.DB")
DB.BuiltInCategory = type("BIC", (), dict(
    (n, i) for i, n in enumerate(
        ["OST_Walls", "OST_Parts", "OST_GenericModel", "OST_Windows", "OST_Doors",
         "OST_Roofs", "OST_Fascia", "OST_Gutter", "OST_RoofSoffit"], 1)))
DB.Color = lambda r, g, b: ("cor", r, g, b)


def _criar_material(doc, nome):
    m = Mat(7000 + len(MATERIAIS), nome)
    MATERIAIS.append(m)
    doc._m[m.Id.Value] = m
    return m.Id


Mat.Create = staticmethod(_criar_material)
DB.Material = Mat


def instalar(doc, sel_ids):
    m = types.ModuleType("clr"); m.AddReference = lambda *a: None
    sys.modules["clr"] = m
    for n in ("Autodesk", "Autodesk.Revit", "RevitServices",
              "RevitServices.Persistence", "RevitServices.Transactions"):
        sys.modules[n] = types.ModuleType(n)
    sys.modules["Autodesk.Revit.DB"] = DB

    uidoc = type("UIDoc", (), {"Selection": Sel(sel_ids)})()
    uiapp = type("UIApp", (), {"ActiveUIDocument": uidoc})()
    dm = type("DM", (), {"CurrentDBDocument": doc, "CurrentUIApplication": uiapp})()
    sys.modules["RevitServices.Persistence"].DocumentManager = \
        type("DMH", (), {"Instance": dm})()
    tm = type("TM", (), {"EnsureInTransaction": lambda s, d: None,
                         "TransactionTaskDone": lambda s: None,
                         "ForceCloseTransaction": lambda s: None})()
    sys.modules["RevitServices.Transactions"].TransactionManager = \
        type("TMH", (), {"Instance": tm})()


def rodar(entradas, doc, sel_ids, ajustes=None):
    instalar(doc, sel_ids)
    ns = {"IN": entradas, "__name__": "__main__"}
    fonte = open("dynamo/PintarFachadas.py", encoding="utf-8").read()
    for antes, depois in (ajustes or []):
        assert antes in fonte, "ajuste nao encontrado: %r" % antes
        fonte = fonte.replace(antes, depois, 1)
    exec(compile(fonte, "PintarFachadas.py", "exec"), ns)
    return ns.get("OUT", "<<OUT NUNCA FOI DEFINIDO>>")


# --------------------------------------------------------------------------
# Modelo falso: 10 casas em bloco, cada uma com paredes em duas fiadas + janela
# --------------------------------------------------------------------------
PAREDE = Cat(1, "Paredes")
JANELA = Cat(4, "Janelas")
TELHADO = Cat(6, "Telhados")


def modelo():
    elementos, grupos, tipos, sel = [], [], [], []
    for c in range(10):
        base, membros = c * 30.0, []
        for j in range(3):
            eid = 1000 + c * 100 + j
            elementos.append(Elem(eid, "PINTURA ACRILICA SIMPLES EM PAREDE", PAREDE,
                                  BBox(P(base + j * 10, 0, 0), P(base + (j + 1) * 10, 1, 10)),
                                  group=9000 + c, nivel=500))
            membros.append(eid)
        for j in range(3):
            eid = 1050 + c * 100 + j
            elementos.append(Elem(eid, "EMASSAMENTO, LIXAMENTO E PINTURA", PAREDE,
                                  BBox(P(base + j * 10, 0, 10), P(base + (j + 1) * 10, 1, 20)),
                                  group=9000 + c, nivel=501))
            membros.append(eid)
        eid = 1090 + c * 100
        elementos.append(Elem(eid, "900 x 2100", JANELA,
                              BBox(P(base + 8, 0, 4), P(base + 12, 1, 9)), group=9000 + c))
        membros.append(eid)
        # telhado: NAO pode ser pintado
        eid = 1095 + c * 100
        elementos.append(Elem(eid, "Telhado 2 aguas", TELHADO,
                              BBox(P(base, 0, 20), P(base + 30, 1, 25)), group=9000 + c))
        membros.append(eid)
        tipos.append(TipoGrupo(8000 + c, c + 1))          # Marca de tipo 1..10
        g = Group(9000 + c, membros, BBox(P(base, 0, 0), P(base + 30, 1, 25)),
                  tipo=8000 + c)
        grupos.append(g); sel.append(9000 + c)
    niveis = [Nivel(500, 0.0), Nivel(501, 10.0)]
    return Doc(elementos + grupos + tipos + niveis), sel


falhas = []


def checar(rotulo, entradas, sel_ids, esperado_em=None, nao_pode=None):
    doc, sel = modelo()
    if sel_ids is not None:
        sel = sel_ids
    try:
        out = rodar(entradas, doc, sel)
    except Exception as e:
        falhas.append("%s: EXCECAO %s: %s" % (rotulo, type(e).__name__, e))
        import traceback; traceback.print_exc()
        return None
    if out == "<<OUT NUNCA FOI DEFINIDO>>" or out is None:
        falhas.append("%s: OUT ficou null" % rotulo)
        return None
    texto = "\n".join(out[0])
    if esperado_em and esperado_em not in texto:
        falhas.append("%s: esperava '%s' no resumo.\n---\n%s" % (rotulo, esperado_em, texto))
    if nao_pode and nao_pode in texto:
        falhas.append("%s: NAO podia conter '%s'.\n---\n%s" % (rotulo, nao_pode, texto))
    print("[%s] OUT ok, %d linhas de resumo, %d linhas de detalhe"
          % (rotulo, len(out[0]), len(out[1])))
    return out


print("=== rodando o script inteiro contra um Revit falso ===\n")

out = checar("simulacao padrao", ["AUTO", "override", "grupo", "fachada", False], None,
             esperado_em="10 casa(s)")
if out:
    for linha in out[0]:
        print("   ", linha)

checar("aplicar override", ["AUTO", "override", "grupo", "fachada", True], None,
       esperado_em="Aplicado em")
checar("selecao vazia", ["AUTO", "override", "grupo", "fachada", False], [],
       esperado_em="nada selecionado")
checar("limpar", ["AUTO", "limpar", "grupo", "fachada", True], None,
       esperado_em="Overrides removidos")
checar("modo invalido", ["AUTO", "xyz", "grupo", "fachada", False], None,
       esperado_em="desconhecido")
checar("casas por numero", ["X", "override", 10, "fachada", False], None,
       esperado_em="10 casas iguais")
checar("casas por gap", ["X", "override", "gap", "fachada", False], None)
checar("casas por parametro", ["X", "override", "parametro", "fachada", False], None)
checar("casas por trios", ["X", "override", "trios", "fachada", False], None)
checar("faixas geometricas Z", ["X", "override", "grupo", "Z", False], None,
       esperado_em="faixas horizontais")
checar("faixas AUTO", ["X", "override", "grupo", "AUTO", False], None)
# --- modo material: RGB no material, sem vazar cor entre casas -------------
del MATERIAIS[:]
doc_mt, sel_mt = modelo()
try:
    out_mt = rodar(["X", "material", "marcatipo", "fachada", True], doc_mt, sel_mt)
except Exception as e:
    falhas.append("modo material: EXCECAO %s: %s" % (type(e).__name__, e))
else:
    txt = "\n".join(out_mt[0])
    hexes = sorted(set(l[4] for l in out_mt[1]))
    # 10 casas -> trios 1..8,1,2 -> 8 trios x 3 = 24 cores distintas
    if len(MATERIAIS) != len(hexes):
        falhas.append("materiais criados (%d) != cores do plano (%d)"
                      % (len(MATERIAIS), len(hexes)))
    else:
        print("[material] %d materiais criados, um por cor da paleta" % len(MATERIAIS))

    # o RGB tem que estar gravado no material, nao so no nome
    ruins = [m.Name for m in MATERIAIS if m.Color is None]
    if ruins:
        falhas.append("materiais sem Color: %s" % ruins[:3])
    elif any(m.UseRenderAppearanceForShading for m in MATERIAIS):
        falhas.append("UseRenderAppearanceForShading ficou True: a cor nao aparece")
    else:
        exemplo = MATERIAIS[0]
        print("[material] RGB gravado, ex.: %s -> %s" % (exemplo.Name, exemplo.Color))

    # nome do material tem que ser o HEX da paleta
    nomes = set(m.Name for m in MATERIAIS)
    esperados = set("ZYLO_FACHADA_" + h.lstrip("#").upper() for h in hexes)
    if nomes != esperados:
        falhas.append("nomes de material fora do padrao: %s" % sorted(nomes - esperados)[:3])
    else:
        print("[material] nomes seguem a paleta: ZYLO_FACHADA_<HEX>")

    if "Aplicado em 70" not in txt:
        falhas.append("modo material nao aplicou nos 70:\n%s" % txt)
    else:
        print("[material] aplicado nos 70 elementos")

    if "Como o material foi aplicado" not in txt:
        falhas.append("nao reportou a estrategia usada:\n%s" % txt)

    # nenhuma casa pode ter recebido cor de outra
    por_casa = {}
    for casa, trio, papel, regra, hexa, eid, nome in out_mt[1]:
        por_casa.setdefault(casa, set()).add(hexa)
    ruins = [c for c, v in por_casa.items() if len(v) != 3]
    if ruins:
        falhas.append("casas sem exatamente 3 cores no modo material: %s" % ruins)
    else:
        print("[material] as 10 casas mantiveram exatamente 3 cores")

    # a pintura de face precisa ter acontecido de verdade no documento
    pintados = getattr(doc_mt, "pintado", {})
    if len(pintados) != 70:
        falhas.append("pintura de face nao chegou ao documento: %d de 70" % len(pintados))
    else:
        print("[material] 70 faces pintadas no documento (sem duplicar tipo)")

# --- tipo compartilhado tem que ser RECUSADO, nao vazar cor ---------------
del MATERIAIS[:]
doc_tp, sel_tp = modelo()
try:
    out_tp = rodar(["X", "material", "marcatipo", "fachada", True], doc_tp, sel_tp,
                   ajustes=[('ESTRATEGIA_MATERIAL = ["instancia", "pintura", "tipo"]',
                             'ESTRATEGIA_MATERIAL = ["tipo"]')])
except Exception as e:
    falhas.append("estrategia tipo: EXCECAO %s: %s" % (type(e).__name__, e))
else:
    txt = "\n".join(out_tp[0])
    if "compartilhados entre casas" not in txt:
        falhas.append("nao recusou os tipos compartilhados:\n%s" % txt)
    elif "Aplicado em 0" not in txt:
        falhas.append("aplicou em tipo compartilhado — a cor vazaria:\n%s" % txt)
    else:
        print("[material] tipo compartilhado entre casas recusado, cor nao vazou")

# --- PERMITIR_TIPO_COMPARTILHADO libera, com o risco assumido -------------
del MATERIAIS[:]
doc_pt, sel_pt = modelo()
try:
    out_pt = rodar(["X", "material", "marcatipo", "fachada", True], doc_pt, sel_pt,
                   ajustes=[('ESTRATEGIA_MATERIAL = ["instancia", "pintura", "tipo"]',
                             'ESTRATEGIA_MATERIAL = ["tipo"]'),
                            ('PERMITIR_TIPO_COMPARTILHADO = False',
                             'PERMITIR_TIPO_COMPARTILHADO = True')])
except Exception as e:
    falhas.append("PERMITIR_TIPO_COMPARTILHADO: EXCECAO %s: %s" % (type(e).__name__, e))
else:
    if "compartilhados entre casas" in "\n".join(out_pt[0]):
        falhas.append("PERMITIR_TIPO_COMPARTILHADO nao liberou")
    else:
        print("[material] PERMITIR_TIPO_COMPARTILHADO libera a gravacao no tipo")

# --- erro nao tratado tem que virar relatorio, nunca null --------------------
class DocQuebrado(object):
    def __init__(self): self._m = {}
    def GetElement(self, eid): return None
    @property
    def ActiveView(self):
        raise RuntimeError("vista ativa explodiu de proposito")


doc_ruim = DocQuebrado()
instalar(doc_ruim, [])
ns = {"IN": ["AUTO", "override", "grupo", "fachada", False], "__name__": "__main__"}
try:
    exec(compile(open("dynamo/PintarFachadas.py", encoding="utf-8").read(),
                 "PintarFachadas.py", "exec"), ns)
except Exception as e:
    falhas.append("erro nao tratado escapou do script: %s" % e)
else:
    saida = ns.get("OUT")
    if saida is None:
        falhas.append("erro nao tratado devolveu OUT null")
    else:
        texto = "\n".join(saida[0])
        if "ERRO NAO TRATADO" not in texto or "explodiu de proposito" not in texto:
            falhas.append("relatorio de erro sem o traceback:\n%s" % texto)
        else:
            print("[erro nao tratado] virou relatorio legivel, nao null")

checar("nivel do Revit decide cima/baixo", ["X", "override", "grupo", "fachada", False],
       None, esperado_em="pelo nível do Revit")

# --- ciclo marcar -> revisar -> pintar pela marcacao ------------------------
doc_m, sel_m = modelo()
saida = None
try:
    saida = rodar(["X", "marcar", "grupo", "fachada", True], doc_m, sel_m)
except Exception as e:
    falhas.append("modo marcar: EXCECAO %s: %s" % (type(e).__name__, e))
if saida:
    texto = "\n".join(saida[0])
    if "Aplicado em 70" not in texto:
        falhas.append("modo marcar nao gravou os 70:\n%s" % texto)
    else:
        print("[marcar] gravou a decisao em 70 elementos")
    # o que foi gravado deve ser lido de volta
    gravados = [e for e in doc_m._m.values()
                if hasattr(e, "_pars") and e._pars["Comentários"].valor.startswith("ZYLO:")]
    if len(gravados) != 70:
        falhas.append("esperava 70 marcados, achei %d" % len(gravados))
    exemplo = gravados[0]._pars["Comentários"].valor
    print("[marcar] exemplo gravado:", exemplo)
    if "regra=" not in exemplo:
        falhas.append("marcacao sem a regra: %s" % exemplo)
    # os chutes tem que ser filtraveis: regra=corte / regra=mediana
    regras = {}
    for e in gravados:
        v = e._pars["Comentários"].valor
        r = [x for x in v.split(";") if x.startswith("regra=")]
        regras[r[0]] = regras.get(r[0], 0) + 1 if r else 0
    print("[marcar] regras gravadas:", regras)
    if not regras:
        falhas.append("nenhuma regra gravada")
    # agora pinta lendo da marcacao, sem adivinhar nada
    try:
        out2 = rodar(["X", "override", "marcacao", "parametro", False], doc_m, sel_m)
    except Exception as e:
        falhas.append("pintar pela marcacao: EXCECAO %s: %s" % (type(e).__name__, e))
    else:
        t2 = "\n".join(out2[0])
        if "papel lido da marcação" not in t2:
            falhas.append("nao leu o papel da marcacao:\n%s" % t2)
        elif "10 casa(s)" not in t2:
            falhas.append("marcacao nao reconstruiu as 10 casas:\n%s" % t2)
        else:
            print("[marcacao] 10 casas e 70 papeis lidos do parametro, zero adivinhacao")

# --- Marca de tipo manda no trio, telhado fica de fora ----------------------
doc_t, sel_t = modelo()
try:
    out_t = rodar(["X", "override", "marcatipo", "fachada", False], doc_t, sel_t)
except Exception as e:
    falhas.append("marcatipo: EXCECAO %s: %s" % (type(e).__name__, e))
else:
    txt = "\n".join(out_t[0])
    # 10 casas x (6 paredes + 1 janela) = 70; os 10 telhados NAO entram
    if "70 elemento(s)" not in txt:
        falhas.append("telhado nao foi excluido:\n%s" % txt)
    elif "10 elemento(s) de categoria ignorada" not in txt:
        falhas.append("nao reportou os telhados pulados:\n%s" % txt)
    else:
        print("[marcatipo] 10 telhados excluidos, 70 elementos coloridos")

    # cada casa com exatamente 3 cores, e o trio vindo da marca
    por_casa = {}
    for casa, trio, papel, regra, hexa, eid, nome in out_t[1]:
        por_casa.setdefault(casa, {"cores": set(), "trio": trio})["cores"].add(hexa)
    ruins = [c for c, v in por_casa.items() if len(v["cores"]) != 3]
    if ruins:
        falhas.append("casas sem exatamente 3 cores: %s" % ruins)
    else:
        print("[marcatipo] todas as %d casas com exatamente 3 cores" % len(por_casa))

    # marca 1..8 -> trios 1..8 ; marca 9 -> trio 1 ; marca 10 -> trio 2
    PAL = [["#FAD68C", "#D54938", "#F3D1E2"], ["#F9EE9E", "#F89C13", "#F5A992"]]
    trios_vistos = dict((c, v["trio"]) for c, v in por_casa.items())
    esperado = dict((i + 1, (i % 8) + 1) for i in range(10))
    if trios_vistos != esperado:
        falhas.append("ciclo da marca errado.\n  visto:    %s\n  esperado: %s"
                      % (trios_vistos, esperado))
    else:
        print("[marcatipo] marca 1..8 -> trios 1..8, marca 9 -> trio 1, marca 10 -> trio 2")

    # e as cores da casa 9 tem que ser identicas as da casa 1
    if por_casa[9]["cores"] != por_casa[1]["cores"]:
        falhas.append("casa 9 nao repetiu as cores da casa 1: %s vs %s"
                      % (por_casa[9]["cores"], por_casa[1]["cores"]))
    elif por_casa[10]["cores"] != por_casa[2]["cores"]:
        falhas.append("casa 10 nao repetiu as cores da casa 2")
    elif por_casa[1]["cores"] != set(PAL[0]):
        falhas.append("casa 1 nao usou o trio 1: %s" % por_casa[1]["cores"])
    else:
        print("[marcatipo] casa 9 = cores da casa 1, casa 10 = cores da casa 2")

# --- 3D: avisar quando o estilo da vista nao mostra material ---------------
doc_v, sel_v = modelo()
try:
    out_v = rodar(["X", "material", "marcatipo", "fachada", False], doc_v, sel_v)
except Exception as e:
    falhas.append("diagnostico de vista: EXCECAO %s: %s" % (type(e).__name__, e))
else:
    txt = "\n".join(out_v[0])
    if "Vista ativa:" not in txt:
        falhas.append("nao descreveu a vista:\n%s" % txt)
    elif "Material N" not in txt:      # "Material NAO aparece nesse estilo"
        falhas.append("nao avisou que HLR nao mostra material:\n%s" % txt)
    else:
        print("[3d] avisa que Linha Oculta nao mostra material")

# override tem que gritar que so vale naquela vista
try:
    out_o = rodar(["X", "override", "marcatipo", "fachada", False], doc_v, sel_v)
except Exception as e:
    falhas.append("aviso do override: EXCECAO %s" % e)
else:
    if "pinta S" not in "\n".join(out_o[0]):   # "pinta SO esta vista"
        falhas.append("override nao avisou que e so da vista:\n%s"
                      % "\n".join(out_o[0]))
    else:
        print("[3d] override avisa que vale so na vista ativa")

# todas as faces pintadas: e o que da cor ao volume em 3D
del MATERIAIS[:]
doc_f, sel_f = modelo()
try:
    rodar(["X", "material", "marcatipo", "fachada", True], doc_f, sel_f)
except Exception as e:
    falhas.append("pintar todas as faces: EXCECAO %s" % e)
else:
    if len(getattr(doc_f, "pintado", {})) != 70:
        falhas.append("nem todos os elementos foram pintados")
    else:
        print("[3d] todas as faces pintadas: volume colorido de qualquer angulo")

print()
if falhas:
    print("=== %d FALHA(S) ===" % len(falhas))
    for f in falhas:
        print(" -", f)
    sys.exit(1)
print("TODOS OS CENARIOS DE INTEGRACAO PASSARAM")
