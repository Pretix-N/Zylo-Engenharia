# -*- coding: utf-8 -*-
"""
Zylo Engenharia — Gerador de casa térrea no Revit
==================================================

Modela automaticamente uma casa térrea de 10m x 8m (80 m²) com:
  - Níveis (Térreo e Cobertura)
  - Paredes externas e internas
  - Piso
  - Telhado 4 águas com beiral de 50 cm
  - Portas e janelas (usa as famílias já carregadas no template)

Ambientes gerados:
  - Sala + Cozinha integradas ... 6,00 x 8,00 m (48,0 m²)
  - Quarto 1 (suíte-master) ..... 4,00 x 4,00 m (16,0 m²)
  - Banheiro .................... 4,00 x 1,50 m ( 6,0 m²)
  - Quarto 2 .................... 4,00 x 2,50 m (10,0 m²)

Como rodar: veja o README.md nesta pasta (pyRevit, RevitPythonShell ou Dynamo).
Requer um projeto aberto criado a partir de um template de arquitetura
(pt-BR ou en), pois o script usa os tipos padrão de parede/piso/telhado
e as primeiras famílias de porta e janela que encontrar carregadas.
"""

import clr

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

from Autodesk.Revit.DB import (
    BuiltInCategory,
    BuiltInParameter,
    CurveArray,
    ElementTypeGroup,
    FamilySymbol,
    FilteredElementCollector,
    Level,
    Line,
    ModelCurveArray,
    Transaction,
    UnitUtils,
    Wall,
    XYZ,
)
from Autodesk.Revit.DB.Structure import StructuralType

# ---------------------------------------------------------------------------
# PARÂMETROS DA CASA — ajuste aqui e rode de novo
# ---------------------------------------------------------------------------
LARGURA = 10.0        # dimensão X externa, em metros
PROFUNDIDADE = 8.0    # dimensão Y externa, em metros
PE_DIREITO = 2.80     # altura das paredes, em metros
BEIRAL = 0.50         # projeção do telhado além das paredes, em metros
INCLINACAO_TELHADO = 0.30   # 30% (rise/run)
PEITORIL_JANELA = 1.00      # altura do peitoril das janelas comuns, em metros
PEITORIL_BANHEIRO = 1.50    # peitoril da janela do banheiro, em metros

# Divisões internas (coordenadas em metros a partir do canto inferior esquerdo)
X_DIVISAO = 6.0       # parede que separa a área social dos quartos
Y_QUARTO2 = 2.5       # parede entre quarto 2 e banheiro
Y_BANHEIRO = 4.0      # parede entre banheiro e quarto 1

# ---------------------------------------------------------------------------
# Ambiente de execução: pyRevit / RevitPythonShell ou Dynamo
# ---------------------------------------------------------------------------
IS_DYNAMO = False
try:
    doc = __revit__.ActiveUIDocument.Document  # noqa: F821 (pyRevit / RPS)
except NameError:
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager

    doc = DocumentManager.Instance.CurrentDBDocument
    IS_DYNAMO = True


def metros(valor):
    """Converte metros para as unidades internas do Revit (pés decimais)."""
    try:
        from Autodesk.Revit.DB import UnitTypeId  # Revit 2021+
        return UnitUtils.ConvertToInternalUnits(valor, UnitTypeId.Meters)
    except ImportError:
        from Autodesk.Revit.DB import DisplayUnitType  # Revit <= 2021
        return UnitUtils.ConvertToInternalUnits(valor, DisplayUnitType.DUT_METERS)


def ponto(x, y, z=0.0):
    return XYZ(metros(x), metros(y), metros(z))


def obter_ou_criar_nivel(nome, elevacao_m):
    """Reaproveita um nível existente na elevação pedida, senão cria um novo."""
    elevacao = metros(elevacao_m)
    for nivel in FilteredElementCollector(doc).OfClass(Level):
        if abs(nivel.Elevation - elevacao) < 0.001:
            return nivel
    novo = Level.Create(doc, elevacao)
    try:
        novo.Name = nome
    except Exception:
        pass  # já existe nível com esse nome; a elevação é o que importa
    return novo


def primeiro_simbolo(categoria):
    """Primeira família carregada da categoria (portas ou janelas)."""
    simbolo = (
        FilteredElementCollector(doc)
        .OfCategory(categoria)
        .OfClass(FamilySymbol)
        .FirstElement()
    )
    if simbolo and not simbolo.IsActive:
        simbolo.Activate()
        doc.Regenerate()
    return simbolo


def criar_parede(p1, p2, nivel, altura_m):
    tipo = doc.GetDefaultElementTypeId(ElementTypeGroup.WallType)
    linha = Line.CreateBound(ponto(*p1), ponto(*p2))
    return Wall.Create(doc, linha, tipo, nivel.Id, metros(altura_m), 0.0, False, False)


def inserir_instancia(simbolo, xy, parede, nivel, peitoril_m=None):
    inst = doc.Create.NewFamilyInstance(
        ponto(xy[0], xy[1]), simbolo, parede, nivel, StructuralType.NonStructural
    )
    if peitoril_m is not None:
        param = inst.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)
        if param and not param.IsReadOnly:
            param.Set(metros(peitoril_m))
    return inst


def criar_piso(nivel):
    cantos = [(0, 0), (LARGURA, 0), (LARGURA, PROFUNDIDADE), (0, PROFUNDIDADE)]
    linhas = [
        Line.CreateBound(ponto(*cantos[i]), ponto(*cantos[(i + 1) % 4]))
        for i in range(4)
    ]
    tipo = doc.GetDefaultElementTypeId(ElementTypeGroup.FloorType)
    try:
        # Revit 2022+
        from Autodesk.Revit.DB import CurveLoop
        from System.Collections.Generic import List

        loop = CurveLoop()
        for linha in linhas:
            loop.Append(linha)
        loops = List[CurveLoop]([loop])
        from Autodesk.Revit.DB import Floor
        return Floor.Create(doc, loops, tipo, nivel.Id)
    except Exception:
        # Revit <= 2021
        arr = CurveArray()
        for linha in linhas:
            arr.Append(linha)
        return doc.Create.NewFloor(arr, False)


def criar_telhado(nivel_cobertura):
    b = BEIRAL
    cantos = [
        (-b, -b),
        (LARGURA + b, -b),
        (LARGURA + b, PROFUNDIDADE + b),
        (-b, PROFUNDIDADE + b),
    ]
    contorno = CurveArray()
    for i in range(4):
        contorno.Append(
            Line.CreateBound(ponto(*cantos[i]), ponto(*cantos[(i + 1) % 4]))
        )
    tipo_id = doc.GetDefaultElementTypeId(ElementTypeGroup.RoofType)
    tipo = doc.GetElement(tipo_id)
    mapa = clr.Reference[ModelCurveArray]()
    telhado = doc.Create.NewFootPrintRoof(contorno, nivel_cobertura, tipo, mapa)
    for curva in mapa.Value:
        telhado.set_DefinesSlope(curva, True)
        telhado.set_SlopeAngle(curva, INCLINACAO_TELHADO)
    return telhado


def modelar_casa():
    terreo = obter_ou_criar_nivel("Térreo", 0.0)
    cobertura = obter_ou_criar_nivel("Cobertura", PE_DIREITO)

    L, P = LARGURA, PROFUNDIDADE

    # Paredes externas (sentido horário a partir do canto inferior esquerdo)
    parede_sul = criar_parede((0, 0), (L, 0), terreo, PE_DIREITO)
    parede_leste = criar_parede((L, 0), (L, P), terreo, PE_DIREITO)
    parede_norte = criar_parede((L, P), (0, P), terreo, PE_DIREITO)
    parede_oeste = criar_parede((0, P), (0, 0), terreo, PE_DIREITO)

    # Paredes internas
    divisoria = criar_parede((X_DIVISAO, 0), (X_DIVISAO, P), terreo, PE_DIREITO)
    criar_parede((X_DIVISAO, Y_QUARTO2), (L, Y_QUARTO2), terreo, PE_DIREITO)
    criar_parede((X_DIVISAO, Y_BANHEIRO), (L, Y_BANHEIRO), terreo, PE_DIREITO)

    criar_piso(terreo)
    criar_telhado(cobertura)

    porta = primeiro_simbolo(BuiltInCategory.OST_Doors)
    janela = primeiro_simbolo(BuiltInCategory.OST_Windows)

    avisos = []
    if porta:
        inserir_instancia(porta, (3.0, 0), parede_sul, terreo)          # entrada
        inserir_instancia(porta, (X_DIVISAO, 6.0), divisoria, terreo)   # quarto 1
        inserir_instancia(porta, (X_DIVISAO, 1.25), divisoria, terreo)  # quarto 2
        inserir_instancia(porta, (X_DIVISAO, 3.25), divisoria, terreo)  # banheiro
    else:
        avisos.append("Nenhuma família de porta carregada — portas não inseridas.")

    if janela:
        inserir_instancia(janela, (1.5, 0), parede_sul, terreo, PEITORIL_JANELA)   # sala
        inserir_instancia(janela, (0, 4.0), parede_oeste, terreo, PEITORIL_JANELA)  # sala
        inserir_instancia(janela, (3.0, P), parede_norte, terreo, PEITORIL_JANELA)  # cozinha
        inserir_instancia(janela, (L, 6.0), parede_leste, terreo, PEITORIL_JANELA)  # quarto 1
        inserir_instancia(janela, (L, 1.25), parede_leste, terreo, PEITORIL_JANELA)  # quarto 2
        inserir_instancia(janela, (L, 3.25), parede_leste, terreo, PEITORIL_BANHEIRO)  # banheiro
    else:
        avisos.append("Nenhuma família de janela carregada — janelas não inseridas.")

    return avisos


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------
if IS_DYNAMO:
    TransactionManager.Instance.EnsureInTransaction(doc)
    avisos = modelar_casa()
    TransactionManager.Instance.TransactionTaskDone()
    OUT = "Casa modelada! " + (" | ".join(avisos) if avisos else "Sem avisos.")
else:
    transacao = Transaction(doc, "Zylo — Modelar casa térrea")
    transacao.Start()
    try:
        avisos = modelar_casa()
        transacao.Commit()
        mensagem = "Casa modelada com sucesso!"
        if avisos:
            mensagem += "\n\nAvisos:\n- " + "\n- ".join(avisos)
        print(mensagem)
    except Exception as erro:
        transacao.RollBack()
        print("Erro ao modelar a casa: {}".format(erro))
        raise
