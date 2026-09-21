# -*- coding: utf-8 -*-
# Testa a logica pura do no (HEX, deteccao de casas, faixas, ciclo) fora do Revit,
# com stubs da API. Rode: python3 dynamo/teste_logica.py
import sys, types, random

class _Fake:
    def __init__(self, n="X"): self._n = n
    def __getattr__(self, k): return _Fake(k)
    def __call__(self, *a, **k): return _Fake(self._n)
    def __eq__(self, o): return False
DB = _Fake("DB")
class _Group: pass
DB.Group = _Group
m = types.ModuleType("clr"); m.AddReference = lambda *a: None; sys.modules["clr"] = m
for nome in ("Autodesk", "Autodesk.Revit", "RevitServices",
             "RevitServices.Persistence", "RevitServices.Transactions"):
    sys.modules[nome] = types.ModuleType(nome)
sys.modules["Autodesk.Revit.DB"] = DB
sys.modules["RevitServices.Persistence"].DocumentManager = _Fake()
sys.modules["RevitServices.Transactions"].TransactionManager = _Fake()

fonte = open("dynamo/PintarFachadas.py", encoding="utf-8").read()
prefixo = fonte.split("# 8. Execu")[0]
ns = {"DB": DB, "__name__": "m"}
exec(compile(prefixo, "PintarFachadas.py", "exec"), ns)

PALETA = ns["PALETA_HEX"]


def elem(x0, x1, z0, z1, tag, y=0.0):
    bb = ((x0, y, z0), (x1, y + 1.0, z1))
    return {"el": tag, "bb": bb, "c": ns["centro"](bb)}


def cores_por_casa(grupos, eixo_faixa):
    """Simula o passo 2 e devolve, por casa, o conjunto de cores usadas."""
    saida = []
    for i, g in enumerate(grupos):
        trio = PALETA[i % 8]
        faixas = ns["repartir_em_faixas"](g, eixo_faixa)
        usadas, mapa = set(), {}
        for k, faixa in enumerate(faixas):
            for d in faixa:
                usadas.add(trio[k]); mapa[d["el"]] = trio[k]
        saida.append((usadas, mapa))
    return saida


# --- 1. HEX -> ARGB -------------------------------------------------------
assert ns["hex_para_argb"]("#FAD68C") == (255, 250, 214, 140)
assert ns["hex_para_argb"]("A53766") == (255, 165, 55, 102)
assert ns["hex_para_argb"]("#FFF") == (255, 255, 255, 255)
try:
    ns["hex_para_argb"]("#GGHHII"); raise AssertionError("deveria falhar")
except ValueError: pass
assert len(PALETA) == 8 and all(len(t) == 3 for t in PALETA)
print("hex -> argb e paleta 8x3 ok")

# --- 2. O CASO QUE QUEBROU: casas com MUITOS elementos --------------------
# 10 casas geminadas de 30 ft, cada uma feita de 12 elementos.
dados = []
for casa in range(10):
    base = casa * 30.0
    for j in range(12):
        dados.append(elem(base + j * 2.5, base + (j + 1) * 2.5, 0.0, 20.0,
                          "c%02d_e%02d" % (casa + 1, j + 1)))
random.seed(7); random.shuffle(dados)

log = []
grupos = ns["casas_por_numero"](dados, 0, 10, log)
assert len(grupos) == 10, len(grupos)
assert all(len(g) == 12 for g in grupos), [len(g) for g in grupos]

res = cores_por_casa(grupos, 0)
for i, (usadas, _) in enumerate(res):
    assert len(usadas) == 3, "casa %d usou %d cores" % (i + 1, len(usadas))
    assert usadas == set(PALETA[i % 8]), (i, usadas)
print("12 elementos por casa -> exatamente 3 cores por casa ok")

# --- 3. Ciclo: casa 9 volta ao trio 1 -------------------------------------
assert res[0][0] == res[8][0] == set(PALETA[0])
assert res[1][0] == res[9][0] == set(PALETA[1])
assert res[0][0] != res[1][0]
print("ciclo casa9->trio1 e casa10->trio2 ok")

# --- 4. Faixas na ordem correta dentro da casa ----------------------------
_, mapa = res[0]
assert mapa["c01_e01"] == PALETA[0][0]   # esquerda  -> cor 1
assert mapa["c01_e06"] == PALETA[0][1]   # meio      -> cor 2
assert mapa["c01_e12"] == PALETA[0][2]   # direita   -> cor 3
print("ordem das faixas esquerda->direita ok")

# --- 5. Faixas empilhadas (eixo Z) ---------------------------------------
casa = [elem(0.0, 30.0, j * 5.0, (j + 1) * 5.0, "f%d" % j) for j in range(6)]
faixas = ns["repartir_em_faixas"](casa, 2)
assert [len(f) for f in faixas] == [2, 2, 2], [len(f) for f in faixas]
print("faixas horizontais no eixo Z ok")

# --- 6. Deteccao por vao, com casas separadas -----------------------------
dados = []
for casa, base in enumerate([0.0, 100.0, 203.0, 400.0]):
    for j in range(5):
        dados.append(elem(base + j * 4.0, base + (j + 1) * 4.0, 0.0, 20.0,
                          "c%d_e%d" % (casa + 1, j + 1)))
log = []
grupos = ns["casas_por_gap"](dados, 0, log)
assert [len(g) for g in grupos] == [5, 5, 5, 5], [len(g) for g in grupos]
assert all(len(u) == 3 for u, _ in cores_por_casa(grupos, 0))
print("deteccao por vao ok ->", log[0])

# --- 7. Geminadas sem vao: 'gap' tem que AVISAR, nao mentir ---------------
dados = [elem(j * 4.0, (j + 1) * 4.0, 0.0, 20.0, "e%d" % j) for j in range(40)]
log = []
grupos = ns["casas_por_gap"](dados, 0, log)
assert len(grupos) == 1, len(grupos)
assert any("geminadas" in l for l in log), log
print("aviso de geminadas ok")

# --- 8. Casa com menos elementos que faixas ------------------------------
casa = [elem(0.0, 10.0, 0.0, 20.0, "a"), elem(10.0, 20.0, 0.0, 20.0, "b")]
faixas = ns["repartir_em_faixas"](casa, 0)
assert [len(f) for f in faixas] == [1, 1, 0]
print("casa com 2 elementos nao quebra ok")

# --- 9. Metodo 'quantil' -------------------------------------------------
ns["FAIXAS_METODO"] = "quantil"
casa = [elem(0.0, 1.0, 0.0, 20.0, "p0")]                       # 1 elemento estreito
casa += [elem(50.0 + j, 51.0 + j, 0.0, 20.0, "p%d" % (j + 1)) for j in range(8)]
faixas = ns["repartir_em_faixas"](casa, 0)
assert [len(f) for f in faixas] == [3, 3, 3], [len(f) for f in faixas]
ns["FAIXAS_METODO"] = "extensao"
print("metodo quantil ok")

# --- 10. Escolha de eixo da fileira --------------------------------------
dados = [elem(i * 10.0, i * 10.0 + 5.0, 0.0, 20.0, i) for i in range(20)]
assert ns["escolher_eixo"](dados, "AUTO", []) == 0
assert ns["escolher_eixo"](dados, "Y", []) == 1
print("escolha de eixo ok")

print("\nTODOS OS TESTES PASSARAM")
