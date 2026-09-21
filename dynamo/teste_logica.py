# -*- coding: utf-8 -*-
# Testa a logica pura do no (HEX, ordenacao, agrupamento, ciclo) fora do Revit,
# com stubs da API. Rode: python3 dynamo/teste_logica.py
import sys, types

# --- stubs mínimos da API ---
class _Fake:
    def __init__(self, n="X"): self._n = n
    def __getattr__(self, k): return _Fake(k)
    def __call__(self, *a, **k): return _Fake(self._n)
    def __eq__(self, o): return False
DB = _Fake("DB")
class _Group: pass
DB.Group = _Group
for nome in ("clr",):
    m = types.ModuleType(nome); m.AddReference = lambda *a: None; sys.modules[nome] = m
for nome in ("Autodesk", "Autodesk.Revit", "Autodesk.Revit.DB",
             "RevitServices", "RevitServices.Persistence", "RevitServices.Transactions"):
    sys.modules[nome] = types.ModuleType(nome)
sys.modules["Autodesk.Revit.DB"] = DB
sys.modules["RevitServices.Persistence"].DocumentManager = _Fake()
sys.modules["RevitServices.Transactions"].TransactionManager = _Fake()

fonte = open("/home/user/Zylo-Engenharia/dynamo/PintarFachadas.py", encoding="utf-8").read()
prefixo = fonte.split("# 7. EXECU")[0].split("# 7. Execu")[0]
ns = {"DB": DB, "__name__": "m"}
exec(compile(prefixo, "PintarFachadas.py", "exec"), ns)

# 1. HEX -> ARGB
assert ns["hex_para_argb"]("#FAD68C") == (255, 250, 214, 140)
assert ns["hex_para_argb"]("A53766") == (255, 165, 55, 102)
assert ns["hex_para_argb"]("#FFF")   == (255, 255, 255, 255)
try:
    ns["hex_para_argb"]("#GGHHII"); raise AssertionError("deveria falhar")
except ValueError: pass
print("hex -> argb ok")

# 2. paleta completa
assert len(ns["PALETA_ARGB"]) == 8 and all(len(t) == 3 for t in ns["PALETA_ARGB"])
print("paleta 8x3 ok")

# 3. cenario A: 10 casas, 3 faixas LADO A LADO (X distinto), fora de ordem
def d(x, y, z, tag): return {"el": tag, "bb": None, "c": (x, y, z)}
dados = []
for casa in range(10):
    for faixa in range(3):
        dados.append(d(casa * 30.0 + faixa * 10.0, 0.0, 0.0, "c%d_f%d" % (casa+1, faixa+1)))
import random; random.seed(1); random.shuffle(dados)
grupos = ns["agrupar_trios"](dados, 0)
assert len(grupos) == 10
assert [g[0]["el"] for g in grupos][:3] == ["c1_f1", "c2_f1", "c3_f1"]
ei = ns["eixo_interno"](grupos)
assert ei == 0, ei
plano = []
for i, g in enumerate(grupos):
    trio = ns["PALETA_HEX"][i % 8]
    for pos, item in enumerate(sorted(g, key=lambda q: q["c"][ei])):
        plano.append((item["el"], i + 1, (i % 8) + 1, trio[pos]))
assert plano[0]  == ("c1_f1", 1, 1, "#FAD68C")
assert plano[2]  == ("c1_f3", 1, 1, "#F3D1E2")
assert plano[24] == ("c9_f1", 9, 1, "#FAD68C"), plano[24]   # ciclo reinicia na casa 9
assert plano[27] == ("c10_f1", 10, 2, "#F9EE9E")
print("cenario lado-a-lado + ciclo casa9->trio1 ok")

# 4. cenario B: faixas EMPILHADAS (mesmo X, Z distinto) -- o caso que quebra o grafo OOTB
dados = []
for casa in range(9):
    for faixa in range(3):
        dados.append(d(casa * 30.0, 0.0, faixa * 9.0, "c%d_f%d" % (casa+1, faixa+1)))
random.shuffle(dados)
grupos = ns["agrupar_trios"](dados, 0)
ei = ns["eixo_interno"](grupos)
assert ei == 2, ei                                   # detectou que o trio varia em Z
ordem = [q["el"] for q in sorted(grupos[0], key=lambda q: q["c"][ei])]
assert ordem == ["c1_f1", "c1_f2", "c1_f3"], ordem
assert ns["PALETA_HEX"][8 % 8][0] == "#FAD68C"       # casa 9 -> trio 1
print("cenario empilhado (desempate por Z) ok")

# 5. agrupamento por gap, com casas de largura irregular
dados = []
for casa, base in enumerate([0.0, 100.0, 203.0, 400.0]):
    for faixa in range(3):
        dados.append(d(base + faixa * 8.0, 0.0, 0.0, "c%d_f%d" % (casa+1, faixa+1)))
log = []
grupos = ns["agrupar_gap"](dados, 0, log)
assert [len(g) for g in grupos] == [3, 3, 3, 3], [len(g) for g in grupos]
print("agrupamento por gap ok ->", log)

# 6. contagem que nao e multipla de 3 tem que ser detectada
dados = [d(i * 10.0, 0.0, 0.0, "e%d" % i) for i in range(10)]
grupos = ns["agrupar_trios"](dados, 0)
fora = [(i + 1, len(g)) for i, g in enumerate(grupos) if len(g) != 3]
assert fora == [(4, 1)], fora
print("deteccao de grupo incompleto ok")

# 7. eixo AUTO
dados = [d(i * 10.0, i * 0.1, 0.0, i) for i in range(20)]
assert ns["escolher_eixo"](dados, "AUTO", []) == 0
dados = [d(i * 0.1, i * 10.0, 0.0, i) for i in range(20)]
assert ns["escolher_eixo"](dados, "AUTO", []) == 1
assert ns["escolher_eixo"](dados, "X", []) == 0
print("escolha de eixo ok")
print("\nTODOS OS TESTES PASSARAM")
