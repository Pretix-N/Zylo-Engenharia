# -*- coding: utf-8 -*-
"""Roda MarcarParedes.py inteiro contra um Revit falso.
Rode: python3 dynamo/teste_marcarparedes.py"""
import sys, types

class Id:
    def __init__(s, v): s.Value = v; s.IntegerValue = v
class Par:
    def __init__(s, v=u"", ro=False): s.valor, s.IsReadOnly = v, ro
    @property
    def HasValue(s): return bool(s.valor)
    def AsString(s): return s.valor
    def Set(s, v): s.valor = v; return True
class Wall:
    def __init__(s, eid, nome, com=u"", ro=False):
        s.Id, s.Name = Id(eid), nome
        s._p = {"Comentários": Par(com, ro)}
    def get_Parameter(s, bip): return s._p["Comentários"] if bip == "COMMENTS" else None
    def LookupParameter(s, n): return s._p.get(n)
class Outro:
    def __init__(s, eid): s.Id, s.Name = Id(eid), "nao e parede"

PAREDES = []
class Col:
    def __init__(s, *a): s._v = len(a) > 1
    def OfCategory(s, c): return s
    def WhereElementIsNotElementType(s): return s
    def __iter__(s): return iter(PAREDES[:3] if s._v else PAREDES)

def instalar(sel):
    m = types.ModuleType("clr"); m.AddReference = lambda *a: None; sys.modules["clr"] = m
    for n in ("Autodesk", "Autodesk.Revit", "RevitServices",
              "RevitServices.Persistence", "RevitServices.Transactions"):
        sys.modules[n] = types.ModuleType(n)
    DB = types.ModuleType("Autodesk.Revit.DB")
    DB.Wall = Wall
    DB.FilteredElementCollector = Col
    DB.BuiltInCategory = type("B", (), {"OST_Walls": 1})
    DB.BuiltInParameter = type("P", (), {"ALL_MODEL_INSTANCE_COMMENTS": "COMMENTS",
                                         "ALL_MODEL_MARK": "MARK"})
    sys.modules["Autodesk.Revit.DB"] = DB
    mapa = dict((w.Id.Value, w) for w in PAREDES)
    doc = type("D", (), {"GetElement": staticmethod(lambda i: mapa.get(i.Value)),
                         "ActiveView": type("V", (), {"Id": Id(1)})()})()
    uidoc = type("U", (), {"Selection": type("S", (), {
        "GetElementIds": staticmethod(lambda: [Id(i) for i in sel])})()})()
    dm = type("M", (), {"CurrentDBDocument": doc,
                        "CurrentUIApplication": type("A", (), {"ActiveUIDocument": uidoc})()})()
    sys.modules["RevitServices.Persistence"].DocumentManager = type("H", (), {"Instance": dm})()
    tm = type("T", (), {"EnsureInTransaction": lambda s, d: None,
                        "TransactionTaskDone": lambda s: None})()
    sys.modules["RevitServices.Transactions"].TransactionManager = type("H", (), {"Instance": tm})()

FONTE = open("dynamo/MarcarParedes.py", encoding="utf-8").read()

def rodar(entradas, sel=(), apenas_vazios=False):
    instalar(sel)
    ns = {"IN": list(entradas), "__name__": "__main__"}
    codigo = FONTE.replace("APENAS_VAZIOS = False",
                           "APENAS_VAZIOS = %r" % apenas_vazios)
    exec(compile(codigo, "MarcarParedes.py", "exec"), ns)
    out = ns.get("OUT")
    assert out is not None, "OUT ficou null"
    return "\n".join(out[0]), out[1]

def reset():
    del PAREDES[:]
    PAREDES.extend([
        Wall(101, "Parede Externa", u"PINTURA ACRILICA"),      # tem conteudo
        Wall(102, "Parede Externa", u""),                       # vazia
        Wall(103, "Parede Interna", u"PINTURA ACRILICA"),
        Wall(104, "Parede Externa", u"NAO APAGAR"),
        Wall(105, "Parede Externa", u"", ro=True),              # somente leitura
    ])

falhas = []
def checar(cond, msg):
    if not cond: falhas.append(msg)

# 1. simulacao nao altera nada
reset()
txt, det = rodar(["modelo", "PARAM_MARCA0", "Comentários", False])
checar("SIMULA" in txt, "faltou marcar como simulacao")
checar(PAREDES[0]._p["Comentários"].valor == u"PINTURA ACRILICA", "simulacao ALTEROU o modelo!")
checar("4 parede(s) seriam alteradas" in txt, "contagem errada:\n" + txt)
checar("SOBRESCRITO" in txt and "NAO APAGAR" in txt, "nao avisou o que seria perdido:\n" + txt)
checar("somente leitura" in txt, "nao reportou o parametro protegido")
print("[1] simulacao nao altera, avisa o que seria perdido, ve o read-only")

# 2. execucao grava
reset()
txt, det = rodar(["modelo", "PARAM_MARCA0", "Comentários", True])
checar("GRAVADO em 4" in txt, "nao gravou 4:\n" + txt)
checar(all(w._p["Comentários"].valor == u"PARAM_MARCA0" for w in PAREDES[:4]),
       "valores nao gravados")
checar(PAREDES[4]._p["Comentários"].valor == u"", "escreveu em parametro somente leitura!")
checar(det[0][2] == u"PINTURA ACRILICA" and det[0][3] == u"PARAM_MARCA0",
       "detalhe sem valor_antes/valor_depois: %r" % (det[0],))
print("[2] gravou nas 4 editaveis, respeitou o read-only, detalhe tem o backup")

# 3. APENAS_VAZIOS preserva o que existe
reset()
txt, det = rodar(["modelo", "PARAM_MARCA0", "Comentários", True], apenas_vazios=True)
checar(PAREDES[0]._p["Comentários"].valor == u"PINTURA ACRILICA", "APENAS_VAZIOS apagou conteudo!")
checar(PAREDES[1]._p["Comentários"].valor == u"PARAM_MARCA0", "APENAS_VAZIOS nao preencheu o vazio")
checar("GRAVADO em 1" in txt, "esperava 1 gravacao:\n" + txt)
print("[3] APENAS_VAZIOS so preenche os vazios")

# 4. texto vazio limpa
reset()
txt, det = rodar(["modelo", "", "Comentários", True])
checar("VAZIO" in txt and "LIMPAR" in txt, "nao avisou que ia limpar:\n" + txt)
checar(all(w._p["Comentários"].valor == u"" for w in PAREDES[:4]), "nao limpou")
print("[4] texto vazio limpa o parametro, com aviso")

# 5. escopo selecao pega so parede
reset()
txt, det = rodar(["selecao", "X", "Comentários", True], sel=(101, 104))
checar("GRAVADO em 2" in txt, "escopo selecao errado:\n" + txt)
checar(PAREDES[2]._p["Comentários"].valor == u"PINTURA ACRILICA", "saiu do escopo da selecao")
print("[5] escopo 'selecao' altera so o selecionado")

# 6. escopo vista
reset()
txt, det = rodar(["vista", "X", "Comentários", False])
checar("vista ativa" in txt, "nao reportou escopo vista:\n" + txt)
print("[6] escopo 'vista' reconhecido")

# 7. idempotente
reset()
rodar(["modelo", "PARAM_MARCA0", "Comentários", True])
txt, det = rodar(["modelo", "PARAM_MARCA0", "Comentários", True])
checar("4 parede(s) já estavam com esse valor" in txt, "nao detectou idempotencia:\n" + txt)
checar("0 parede(s) seriam alteradas" in txt, "deveria nao ter nada a fazer:\n" + txt)
print("[7] rodar duas vezes nao faz nada na segunda")

print()
if falhas:
    print("=== %d FALHA(S) ===" % len(falhas))
    for f in falhas: print(" -", f)
    sys.exit(1)
print("MARCARPAREDES VALIDADO")
