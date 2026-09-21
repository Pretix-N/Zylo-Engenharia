# -*- coding: utf-8 -*-
"""Valida o Diagnostico.py: ele NUNCA pode lancar excecao nem deixar OUT vazio,
nem com Revit presente, nem sem Revit nenhum.
Rode: python3 dynamo/teste_diagnostico.py"""
import subprocess, sys, textwrap

FONTE = "dynamo/Diagnostico.py"

CENARIO_SEM_REVIT = '''
import sys
for m in ("clr", "Autodesk", "Autodesk.Revit", "Autodesk.Revit.DB",
          "RevitServices", "RevitServices.Persistence", "RevitServices.Transactions"):
    sys.modules.pop(m, None)
ns = {"__name__": "__main__"}
exec(compile(open(%r, encoding="utf-8").read(), "Diagnostico.py", "exec"), ns)
saida = ns.get("OUT")
assert saida is not None, "OUT ficou null"
assert len(saida) >= 5, saida
assert any("FALHOU  03" in l for l in saida), "sem clr deveria falhar na etapa 03"
assert any("puladas" in l for l in saida), "deveria pular 05-18"
assert any(l.startswith("OK      01") for l in saida), "etapa 01 deveria passar"
assert any(l.startswith("OK      02") for l in saida), "etapa 02 deveria passar"
print("SEM REVIT: OUT com %%d linhas, nenhuma excecao escapou" %% len(saida))
for l in saida: print("   ", l)
''' % FONTE

CENARIO_COM_REVIT = '''
# -*- coding: utf-8 -*-
import sys, types

class Id:
    def __init__(s, v): s.Value = v; s.IntegerValue = v
    def __repr__(s): return str(s.Value)
class P:
    def __init__(s, x, y, z): s.X, s.Y, s.Z = x, y, z
class T:
    def OfPoint(s, p): return p
class BB:
    def __init__(s): s.Min, s.Max, s.Transform = P(0,0,0), P(10,1,20), T()
class Cat:
    def __init__(s, n): s.Name = n; s.Id = Id(1)
class El:
    Id = Id(4626124)
    Name = "EMBASSAMENTO, LIXAMENTO E PINTURA"
    Category = Cat("Paredes")
    def get_BoundingBox(s, v): return BB()
class View:
    Name = "Elevacao Sul"; ViewType = "Elevation"
    def AreGraphicsOverridesAllowed(s): return True
class Doc:
    Title = "ZYLO_FACHADAS.rvt"; ActiveView = View()
    def GetElement(s, i): return El()
class Sel:
    def GetElementIds(s): return [Id(4626124)]
class UIDoc:
    Selection = Sel()
class App:
    VersionNumber = "2024"; VersionBuild = "24.0.4.427"
class UIApp:
    ActiveUIDocument = UIDoc(); Application = App()
class Color:
    def __init__(s, r, g, b): s.Red, s.Green, s.Blue = r, g, b
class OGS:
    def SetSurfaceForegroundPatternColor(s, c): pass

m = types.ModuleType("clr"); m.AddReference = lambda *a: None; sys.modules["clr"] = m
for n in ("Autodesk", "Autodesk.Revit", "RevitServices",
          "RevitServices.Persistence", "RevitServices.Transactions"):
    sys.modules[n] = types.ModuleType(n)
DB = types.ModuleType("Autodesk.Revit.DB")
DB.Group = type("Group", (), {})
DB.Color = Color
DB.OverrideGraphicSettings = OGS
DB.ElementId = Id
DB.BuiltInCategory = type("BIC", (), {"OST_Walls": "OST_Walls", "OST_Parts": "OST_Parts",
                                      "OST_Windows": "OST_Windows"})
DB.Category = type("C", (), {"GetCategory": staticmethod(lambda d, b: Cat("Janelas"))})
DB.SpecTypeId = type("S", (), {"Reference": type("R", (), {"Material": "autodesk.spec.reference:material"})})
sys.modules["Autodesk.Revit.DB"] = DB
dm = type("DM", (), {"CurrentDBDocument": Doc(), "CurrentUIApplication": UIApp()})()
sys.modules["RevitServices.Persistence"].DocumentManager = type("H", (), {"Instance": dm})()
tm = type("TM", (), {"EnsureInTransaction": lambda s, d: None,
                     "TransactionTaskDone": lambda s: None})()
sys.modules["RevitServices.Transactions"].TransactionManager = type("H", (), {"Instance": tm})()

ns = {"__name__": "__main__"}
exec(compile(open(%r, encoding="utf-8").read(), "Diagnostico.py", "exec"), ns)
saida = ns.get("OUT")
assert saida is not None, "OUT ficou null"
falhas = [l for l in saida if l.startswith("FALHOU")]
assert not falhas, falhas
for n in ["01","02","03","04","05","06","07","08","09","10",
          "11","12","13","14","15","16","17","18"]:
    assert any(("OK      " + n) in l for l in saida), "etapa %%s faltando" %% n
assert any("Value=7" in l and "IntegerValue=7" in l for l in saida), "etapa 14 incompleta"
print("COM REVIT: 18 etapas OK, nenhuma falha")
for l in saida: print("   ", l)
''' % FONTE

erros = 0
for rotulo, codigo in (("sem revit", CENARIO_SEM_REVIT), ("com revit", CENARIO_COM_REVIT)):
    r = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True)
    print(r.stdout, end="")
    if r.returncode != 0:
        erros += 1
        print("=== FALHA no cenario '%s' ===" % rotulo)
        print(r.stderr)
    print()

if erros:
    sys.exit(1)
print("DIAGNOSTICO VALIDADO NOS DOIS CENARIOS")
