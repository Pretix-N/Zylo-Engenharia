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
    def __init__(self, eid, nome, cat, bb, group=None, nivel=None):
        self.Id, self.Name, self.Category, self._bb = Id(eid), nome, cat, bb
        self.GroupId = Id(group) if group is not None else Id(-1)
        self.LevelId = Id(nivel) if nivel is not None else Id(-1)
        self._pars = {"Comentários": Par()}
    def get_BoundingBox(self, v): return self._bb
    def GetTypeId(self): return Id(-1)
    def get_Parameter(self, bip): return None
    def LookupParameter(self, n): return self._pars.get(n)


class Group(Elem):
    def __init__(self, eid, membros, bb):
        Elem.__init__(self, eid, "Grupo %s" % eid, Cat(-2, "Grupos"), bb)
        self._m = membros
    def GetMemberIds(self): return [Id(m) for m in self._m]


class View(object):
    Id = Id(1)
    Name = "Elevacao Sul"
    def __init__(self): self.overrides = {}
    def AreGraphicsOverridesAllowed(self): return True
    def SetElementOverrides(self, eid, ogs): self.overrides[eid.Value] = ogs


class Collector(object):
    def __init__(self, *a): pass
    def OfClass(self, c): return self
    def OfCategory(self, c): return self
    def WhereElementIsNotElementType(self): return self
    def __iter__(self): return iter([])


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
    def IsPainted(self, eid, face): return False
    def Paint(self, eid, face, mid): pass
    def RemovePaint(self, eid, face): pass


class Sel(object):
    def __init__(self, ids): self._ids = [Id(i) for i in ids]
    def GetElementIds(self): return self._ids


class DBMod(types.ModuleType):
    Group = Group
    ElementId = type("EId", (), {"InvalidElementId": Id(-1)})
    OverrideGraphicSettings = OGS
    FilteredElementCollector = Collector
    FillPatternElement = type("FPE", (), {})
    Material = type("Mat", (), {})
    Solid = type("Solid", (), {})
    GeometryInstance = type("GI", (), {})
    PlanarFace = type("PF", (), {})
    Options = type("Opt", (), {})
    ViewDetailLevel = type("VDL", (), {"Fine": 1})
    FillPatternTarget = type("FPT", (), {"Drafting": 1})
    StorageType = type("ST", (), {"ElementId": 1, "String": 2})
    SpecTypeId = type("STI", (), {"Reference": type("R", (), {"Material": 1})})
    BuiltInParameter = type("BIP", (), {})
    Category = type("C", (), {"GetCategory": staticmethod(lambda doc, bic: Cat(bic, "cat"))})
    def Color(self, *a): return a


DB = DBMod("Autodesk.Revit.DB")
DB.BuiltInCategory = type("BIC", (), dict(
    (n, i) for i, n in enumerate(
        ["OST_Walls", "OST_Parts", "OST_GenericModel", "OST_Windows", "OST_Doors"], 1)))
DB.Color = lambda r, g, b: ("cor", r, g, b)


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


def rodar(entradas, doc, sel_ids):
    instalar(doc, sel_ids)
    ns = {"IN": entradas, "__name__": "__main__"}
    exec(compile(open("dynamo/PintarFachadas.py", encoding="utf-8").read(),
                 "PintarFachadas.py", "exec"), ns)
    return ns.get("OUT", "<<OUT NUNCA FOI DEFINIDO>>")


# --------------------------------------------------------------------------
# Modelo falso: 10 casas em bloco, cada uma com paredes em duas fiadas + janela
# --------------------------------------------------------------------------
PAREDE = Cat(1, "Paredes")
JANELA = Cat(4, "Janelas")


def modelo():
    elementos, grupos, sel = [], [], []
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
        g = Group(9000 + c, membros, BBox(P(base, 0, 0), P(base + 30, 1, 20)))
        grupos.append(g); sel.append(9000 + c)
    niveis = [Nivel(500, 0.0), Nivel(501, 10.0)]
    return Doc(elementos + grupos + niveis), sel


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
checar("material", ["X", "material", "grupo", "fachada", True], None)

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

print()
if falhas:
    print("=== %d FALHA(S) ===" % len(falhas))
    for f in falhas:
        print(" -", f)
    sys.exit(1)
print("TODOS OS CENARIOS DE INTEGRACAO PASSARAM")
