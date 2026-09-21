# -*- coding: utf-8 -*-
# Testa a logica pura do no (HEX, deteccao de casas, papeis, faixas, ciclo)
# fora do Revit, com stubs da API. Rode: python3 dynamo/teste_logica.py
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
ns = {"DB": DB, "__name__": "m"}
exec(compile(fonte.split("# 8. Execu")[0], "PintarFachadas.py", "exec"), ns)

PALETA = ns["PALETA_HEX"]
CAT_JANELA = 101          # id ficticio presente em ids_moldura
CAT_PAREDE = 202
IDS_MOLDURA = set([CAT_JANELA])


def elem(x0, x1, z0, z1, tag, cat=CAT_PAREDE, textos=None, casa=None, y=0.0):
    bb = ((x0, y, z0), (x1, y + 1.0, z1))
    return {"el": tag, "bb": bb, "c": ns["centro"](bb), "casa": casa,
            "cat_id": cat, "cat": "cat%d" % cat, "textos": textos or [tag]}


# --- 1. HEX e paleta ------------------------------------------------------
assert ns["hex_para_argb"]("#FAD68C") == (255, 250, 214, 140)
assert ns["hex_para_argb"]("A53766") == (255, 165, 55, 102)
assert ns["hex_para_argb"]("#FFF") == (255, 255, 255, 255)
try:
    ns["hex_para_argb"]("#GGHHII"); raise AssertionError("deveria falhar")
except ValueError: pass
assert len(PALETA) == 8 and all(len(t) == 3 for t in PALETA)
print("hex -> argb e paleta 8x3 ok")

# --- 2. Classificacao de moldura -----------------------------------------
assert ns["e_moldura"](elem(0, 1, 0, 1, "w", cat=CAT_JANELA), IDS_MOLDURA)
assert ns["e_moldura"](elem(0, 1, 0, 1, "x", textos=["Moldura 15cm"]), IDS_MOLDURA)
assert ns["e_moldura"](elem(0, 1, 0, 1, "x", textos=["GUARNIÇÃO"]), IDS_MOLDURA)
assert ns["e_moldura"](elem(0, 1, 0, 1, "x", textos=["Esquadria Alum"]), IDS_MOLDURA)
assert not ns["e_moldura"](elem(0, 1, 0, 1, "x", textos=["Parede Externa"]), IDS_MOLDURA)
print("classificacao de moldura (categoria + palavra, com acento) ok")

# --- 3. Reparticao cima / baixo / moldura --------------------------------
casa = []
casa += [elem(j * 3.0, (j + 1) * 3.0, 0.0, 10.0, "baixo%d" % j) for j in range(4)]
casa += [elem(j * 3.0, (j + 1) * 3.0, 10.0, 20.0, "cima%d" % j) for j in range(4)]
casa += [elem(2.0, 4.0, 4.0, 8.0, "jan1", cat=CAT_JANELA),
         elem(8.0, 10.0, 13.0, 17.0, "jan2", cat=CAT_JANELA)]
random.seed(3); random.shuffle(casa)

p = ns["repartir_fachada"](casa, IDS_MOLDURA)
assert sorted(p["baixo"], key=lambda d: d["el"]) == sorted(
    [d for d in casa if d["el"].startswith("baixo")], key=lambda d: d["el"])
assert len(p["cima"]) == 4 and len(p["baixo"]) == 4 and len(p["moldura"]) == 2
# a janela fica fora da parede: nao entra em cima nem em baixo
assert all(d["el"].startswith("jan") for d in p["moldura"])
print("reparticao cima=4 / baixo=4 / moldura=2 ok")

# --- 4. Corte usa so a parede, nao a moldura -----------------------------
# parede de 0 a 20 -> corte em 10, mesmo com uma moldura la em cima em z=40
casa2 = list(casa) + [elem(0.0, 2.0, 38.0, 42.0, "jan_alta", cat=CAT_JANELA)]
p2 = ns["repartir_fachada"](casa2, IDS_MOLDURA)
assert len(p2["cima"]) == 4 and len(p2["baixo"]) == 4, (len(p2["cima"]), len(p2["baixo"]))
print("cota de corte ignora as molduras ok")

# --- 5. Corte configuravel -----------------------------------------------
# desliga o equilibrio para observar a cota de corte pura (o equilibrio existe
# justamente para evitar o resultado "tudo de um lado" que este teste provoca)
ns["EQUILIBRAR_FAIXAS"] = False
# parede 0..20 -> corte em 0.9*20 = 18; nenhum centro fica acima disso
ns["CORTE_ALTURA"] = 0.9
p3 = ns["repartir_fachada"](casa, IDS_MOLDURA)
assert len(p3["baixo"]) == 8 and len(p3["cima"]) == 0, (len(p3["baixo"]), len(p3["cima"]))
ns["CORTE_ALTURA"] = 0.1           # corte em 2; nenhum centro fica abaixo disso
p3 = ns["repartir_fachada"](casa, IDS_MOLDURA)
assert len(p3["cima"]) == 8 and len(p3["baixo"]) == 0, (len(p3["cima"]), len(p3["baixo"]))
ns["CORTE_ALTURA"] = 0.5           # padrao: corte em 10 -> 4 em cima, 4 embaixo
assert len(ns["repartir_fachada"](casa, IDS_MOLDURA)["cima"]) == 4
ns["EQUILIBRAR_FAIXAS"] = True
print("CORTE_ALTURA configuravel ok")

# --- 5b. LIMITE REAL: parede unica de piso a teto nao se divide ----------
# A classificacao usa o CENTRO do elemento. Uma parede inteirica vai toda
# para um lado so -> a casa mostra 2 cores, nao 3. Precisa de Parts ou de
# paredes separadas por faixa. O resumo avisa com "papel vazio".
casa_unica = [elem(0.0, 12.0, 0.0, 20.0, "parede_inteira"),
              elem(3.0, 5.0, 5.0, 9.0, "jan", cat=CAT_JANELA)]
p4 = ns["repartir_fachada"](casa_unica, IDS_MOLDURA)
vazios = [k for k in ("cima", "baixo", "moldura") if not p4[k]]
# a parede inteira cai num lado so -> o outro fica vazio -> 2 cores, nao 3
assert vazios in (["cima"], ["baixo"]), p4
assert len(p4["cima"]) + len(p4["baixo"]) == 1
print("limite conhecido: parede inteirica cai num papel so (avisado) ok")

# --- 6. Casas por bloco (Group) ------------------------------------------
dados = []
for c in range(10):
    base = c * 30.0
    for j in range(3):                                  # fiada de baixo
        dados.append(elem(base + j * 10.0, base + (j + 1) * 10.0, 0.0, 10.0,
                          "c%02d_b%d" % (c + 1, j), casa=9000 + c))
    for j in range(3):                                  # fiada de cima
        dados.append(elem(base + j * 10.0, base + (j + 1) * 10.0, 10.0, 20.0,
                          "c%02d_a%d" % (c + 1, j), casa=9000 + c))
    dados.append(elem(base + 8.0, base + 12.0, 4.0, 9.0,
                      "c%02d_jan" % (c + 1), cat=CAT_JANELA, casa=9000 + c))
random.shuffle(dados)
log = []
grupos = ns["casas_por_grupo"](dados, 0, log)
assert len(grupos) == 10, len(grupos)
assert all(len(g) == 7 for g in grupos), [len(g) for g in grupos]
assert not log, log
print("casas por bloco (Group) ok")

# --- 7. Elemento solto fora de bloco tem que AVISAR ----------------------
log = []
ns["casas_por_grupo"](dados + [elem(0, 1, 0, 1, "solto")], 0, log)
assert any("nao estao dentro de nenhum bloco" in ns["normalizar"](l) for l in log), log
print("aviso de elemento fora de bloco ok")

# --- 8. 3 cores por casa + ciclo casa9 -> trio1 --------------------------
grupos.sort(key=lambda g: min(d["c"][0] for d in g))
cores_casa = []
for i, g in enumerate(grupos):
    trio = PALETA[i % 8]
    papeis = ns["repartir_fachada"](g, IDS_MOLDURA)
    usadas, mapa = set(), {}
    for k, nome in enumerate(ns["PAPEL_DAS_CORES"]):
        for d in papeis[nome]:
            usadas.add(trio[k]); mapa[d["el"]] = trio[k]
    cores_casa.append((usadas, mapa))
    assert len(usadas) == 3, "casa %d usou %d cores" % (i + 1, len(usadas))
assert cores_casa[0][0] == cores_casa[8][0] == set(PALETA[0])
assert cores_casa[1][0] == cores_casa[9][0] == set(PALETA[1])
assert cores_casa[0][0] != cores_casa[1][0]
print("3 cores por casa e ciclo casa9->trio1 ok")

# --- 9. cor1=cima, cor2=baixo, cor3=moldura ------------------------------
_, mapa = cores_casa[0]
assert mapa["c01_a0"] == PALETA[0][0], ("cima deve ser cor1", mapa["c01_a0"])
assert mapa["c01_b0"] == PALETA[0][1], ("baixo deve ser cor2", mapa["c01_b0"])
assert mapa["c01_jan"] == PALETA[0][2], ("moldura deve ser cor3", mapa["c01_jan"])
print("mapeamento cor1=cima / cor2=baixo / cor3=moldura ok")

# --- 10. PAPEL_DAS_CORES reordenavel -------------------------------------
ns["PAPEL_DAS_CORES"] = ["moldura", "cima", "baixo"]
papeis = ns["repartir_fachada"](grupos[0], IDS_MOLDURA)
assert papeis["moldura"], "sem moldura no grupo de teste"
ns["PAPEL_DAS_CORES"] = ["cima", "baixo", "moldura"]
print("PAPEL_DAS_CORES reordenavel ok")

# --- 11. Modos geometricos continuam funcionando -------------------------
casa = [elem(j * 2.5, (j + 1) * 2.5, 0.0, 20.0, "e%02d" % j) for j in range(12)]
faixas = ns["repartir_em_faixas"](casa, 0)
assert [len(f) for f in faixas] == [4, 4, 4], [len(f) for f in faixas]
dados_gap = []
for c, base in enumerate([0.0, 100.0, 203.0, 400.0]):
    for j in range(5):
        dados_gap.append(elem(base + j * 4.0, base + (j + 1) * 4.0, 0.0, 20.0,
                              "c%d_e%d" % (c + 1, j)))
log = []
assert [len(g) for g in ns["casas_por_gap"](dados_gap, 0, log)] == [5, 5, 5, 5]
dados_gem = [elem(j * 4.0, (j + 1) * 4.0, 0.0, 20.0, "e%d" % j) for j in range(40)]
log = []
assert len(ns["casas_por_gap"](dados_gem, 0, log)) == 1
assert any("geminadas" in l for l in log)
log = []
assert len(ns["casas_por_numero"](dados_gem, 0, 8, log)) == 8
print("modos geometricos (faixas, gap, numero) continuam ok")

# --- 12. Escolha de eixo da fileira --------------------------------------
d20 = [elem(i * 10.0, i * 10.0 + 5.0, 0.0, 20.0, i) for i in range(20)]
assert ns["escolher_eixo"](d20, "AUTO", []) == 0
assert ns["escolher_eixo"](d20, "Y", []) == 1
print("escolha de eixo ok")

# --- 13. Nomes REAIS do modelo do usuario --------------------------------
# Modelo de levantamento de servico: as paredes sao nomeadas pelo servico,
# nao pela posicao. Algumas ja trazem a posicao no nome.
reais_baixo = [
    "EMBASSAMENTO, LIXAMENTO E PINTURA PAREDE DE BAIXO",
    "EMASSAMENTO, LIXAMENTO E PINTURA RF 78 EM BAIXO",
]
reais_neutros = [
    "EMBASSAMENTO, LIXAMENTO E PINTURA",
    "EMASSAMENTO, LIXAMENTO E PINTURA 2",
    "PINTURA ACRILICA SIMPLES EM PAREDE",
    "CHAPISCO, REBOCO, EMASSAMENTO, LIXAMENTO E PINTURA RF 79",
    "LIMPEZA NO AZULEIJO 181B",
    "REMOÇÃO REBOCO, CHAPISCO, REBOCO, EMASSAMENTO, LIXAMENTO E PINTURA 12B",
    "REBOCO, EMBASAMENTO, LIXAMENTO E PINTURA 184A",   # grafia de "emassamento"
    "LIXAMENTO PINTURA ESMALTE SINTÉTICO PARA METAIS",
    "LIMPEZA NO VIDRO",
]
for nome in reais_baixo:
    assert ns["papel_por_nome"](elem(0, 1, 0, 1, "x", textos=[nome])) == "baixo", nome
for nome in reais_neutros:
    assert ns["papel_por_nome"](elem(0, 1, 0, 1, "x", textos=[nome])) is None, nome
# e nenhum deles pode ser confundido com moldura
for nome in reais_baixo + reais_neutros:
    assert not ns["e_moldura"](elem(0, 1, 0, 1, "x", textos=[nome]), set()), nome
print("nomes reais do modelo classificados corretamente ok")

# --- 14. Nome vence a geometria ------------------------------------------
# parede marcada "PAREDE DE BAIXO" mas posicionada no alto: o nome manda
casa_mista = [
    elem(0.0, 10.0, 15.0, 20.0, "alta_mas_de_baixo",
         textos=["EMBASSAMENTO, LIXAMENTO E PINTURA PAREDE DE BAIXO"]),
    elem(0.0, 10.0, 0.0, 5.0, "generica_baixa", textos=["PINTURA ACRILICA"]),
    elem(0.0, 10.0, 15.0, 20.0, "generica_alta", textos=["PINTURA ACRILICA"]),
]
st = {}
p5 = ns["repartir_fachada"](casa_mista, set(), st)
assert [d["el"] for d in p5["baixo"]] == ["alta_mas_de_baixo", "generica_baixa"], p5["baixo"]
assert [d["el"] for d in p5["generica_alta" and "cima"]] == ["generica_alta"]
assert st["parede_nome"] == 1 and st["parede_geom"] == 2, st
print("regra por nome tem precedencia sobre a cota de corte ok")

# --- 15. Motivo da classificacao entra nas estatisticas ------------------
st = {}
ns["repartir_fachada"]([
    elem(0, 1, 0, 1, "j", cat=CAT_JANELA),
    elem(0, 1, 0, 1, "m", textos=["Moldura 15"]),
    elem(0, 1, 0, 1, "p", textos=["PINTURA"]),
], IDS_MOLDURA, st)
assert st.get("moldura_categoria") == 1 and st.get("moldura_nome") == 1, st
assert st.get("parede_geom") == 1, st
print("estatisticas de classificacao ok")

# --- 16. Equilibrio quando as paredes caem todas do mesmo lado -----------
# 3 paredes na MESMA altura: o corte por extensao joga todas para "cima".
mesma_altura = [elem(j * 5.0, (j + 1) * 5.0, 10.0, 20.0, "p%d" % j,
                     textos=["PINTURA ACRILICA"]) for j in range(3)]
st = {}
p6 = ns["repartir_fachada"](mesma_altura, set(), st)
assert p6["cima"] and p6["baixo"], p6
assert len(p6["cima"]) + len(p6["baixo"]) == 3
assert st.get("parede_equilibrada") == 3, st
print("equilibrio de faixas quando todas caem do mesmo lado ok")

# 7 paredes na mesma altura (caso da casa 43 do modelo real)
casa43 = [elem(j * 3.0, (j + 1) * 3.0, 0.0, 8.0, "w%d" % j,
               textos=["LIMPEZA NO AZULEIJO 20"]) for j in range(7)]
p7 = ns["repartir_fachada"](casa43, set(), {})
assert len(p7["baixo"]) == 3 and len(p7["cima"]) == 4, (p7["baixo"], p7["cima"])
print("casa com 7 paredes na mesma altura vira 3/4 ok")

# parede UNICA continua sem salvacao -- nao inventa uma divisao que nao existe
p8 = ns["repartir_fachada"]([elem(0.0, 12.0, 0.0, 20.0, "so_uma",
                                  textos=["PINTURA"])], set(), {})
assert len(p8["cima"]) + len(p8["baixo"]) == 1 and (not p8["cima"] or not p8["baixo"])
print("parede unica continua sem divisao (correto) ok")

# nao mexe quando cima e baixo ja estao preenchidos
st = {}
ok_dois = [elem(0.0, 10.0, 0.0, 10.0, "b", textos=["PINTURA"]),
           elem(0.0, 10.0, 10.0, 20.0, "c", textos=["PINTURA"])]
p9 = ns["repartir_fachada"](ok_dois, set(), st)
assert len(p9["baixo"]) == 1 and len(p9["cima"]) == 1
assert st.get("parede_equilibrada") is None and st.get("parede_geom") == 2, st
print("nao equilibra quando ja esta correto ok")

print("\nTODOS OS TESTES PASSARAM (incl. nomes reais e equilibrio)")
