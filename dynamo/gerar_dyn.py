# -*- coding: utf-8 -*-
"""Gera dynamo/PintarFachadas.dyn a partir de dynamo/PintarFachadas.py."""
import json, os, uuid

RAIZ = "/home/user/Zylo-Engenharia/dynamo"
CODIGO = open(os.path.join(RAIZ, "PintarFachadas.py"), encoding="utf-8").read()

def g(): return str(uuid.uuid4())

def porta(nome, desc, idx):
    return {"Id": g(), "Name": nome, "Description": desc, "UsingDefaultValue": False,
            "Level": 2, "UseLevels": False, "KeepListStructure": False}

def code_block(code, desc):
    saida = porta("", "Value of expression at line 1", 0)
    return {
        "ConcreteType": "Dynamo.Graph.Nodes.CodeBlockNodeModel, DynamoCore",
        "NodeType": "CodeBlockNode", "Code": code, "Id": g(),
        "Inputs": [], "Outputs": [saida], "Replication": "Disabled",
        "Description": desc,
    }

def boolean(valor):
    saida = porta("", "Boolean", 0)
    return {
        "ConcreteType": "CoreNodeModels.Input.BoolSelector, CoreNodeModels",
        "NodeType": "BooleanInputNode", "InputValue": valor, "Id": g(),
        "Inputs": [], "Outputs": [saida], "Replication": "Disabled",
        "Description": "Selection between a true and false.",
    }

entradas = [porta("IN[{0}]".format(i), "Input #{0}".format(i), i) for i in range(5)]
py = {
    "ConcreteType": "PythonNodeModels.PythonNode, PythonNodeModels",
    "NodeType": "PythonScriptNode", "Code": CODIGO,
    "Engine": "CPython3", "EngineName": "CPython3",
    "VariableInputPorts": True, "Id": g(),
    "Inputs": entradas,
    "Outputs": [porta("OUT", "Result of the python script", 0)],
    "Replication": "Disabled",
    "Description": "Runs an embedded Python script.",
}

cb_eixo  = code_block('"AUTO";', 'eixo da fileira: "AUTO", "X" ou "Y"')
cb_modo  = code_block('"override";', 'modo: "override", "material", "paint" ou "limpar"')
cb_casas = code_block('"grupo";', 'casas: "grupo" (bloco do Revit), um numero, "gap", "parametro" ou "trios"')
cb_faixa = code_block('"fachada";', 'cores na casa: "fachada" (cima/baixo/moldura) ou "EIXO"/"X"/"Y"/"Z"/"AUTO"')
bl_exec  = boolean(False)

nos = [cb_eixo, cb_modo, cb_casas, cb_faixa, bl_exec, py]

conexoes = []
for origem, destino in zip([cb_eixo, cb_modo, cb_casas, cb_faixa, bl_exec], entradas):
    conexoes.append({"Start": origem["Outputs"][0]["Id"], "End": destino["Id"],
                     "Id": g(), "IsHidden": "False"})

titulos = {cb_eixo["Id"]: "eixo", cb_modo["Id"]: "modo",
           cb_casas["Id"]: "casas", cb_faixa["Id"]: "faixas",
           bl_exec["Id"]: "executar", py["Id"]: "PintarFachadas"}
posicoes = {cb_eixo["Id"]: (0, 0), cb_modo["Id"]: (0, 110),
            cb_casas["Id"]: (0, 220), cb_faixa["Id"]: (0, 330),
            bl_exec["Id"]: (0, 440), py["Id"]: (400, 170)}

node_views = []
for n in nos:
    x, y = posicoes[n["Id"]]
    node_views.append({"Id": n["Id"], "Name": titulos[n["Id"]], "IsSetAsInput": False,
                       "IsSetAsOutput": False, "Excluded": False, "ShowGeometry": True,
                       "X": float(x), "Y": float(y)})

grafo = {
    "Uuid": g(), "IsCustomNode": False, "Description":
        "8 trios de cores em casas lado a lado: parede de cima, parede de baixo e molduras.",
    "Name": "PintarFachadas",
    "ElementResolver": {"ResolutionMap": {}},
    "Inputs": [], "Outputs": [],
    "Nodes": nos, "Connectors": conexoes,
    "Dependencies": [], "NodeLibraryDependencies": [], "EnableLegacyPolyCurveBehavior": True,
    "Thumbnail": "", "GraphDocumentationURL": None,
    "ExtensionWorkspaceData": [],
    "Author": "", "Linting": {"activeLinter": "None", "activeLinterId":
        "7b75fb44-43fd-4631-a878-29f4d5d8399a", "warningCount": 0, "errorCount": 0},
    "Bindings": [],
    "View": {
        "Dynamo": {"ScaleFactor": 1.0, "HasRunWithoutCrash": False,
                   "IsVisibleInDynamoLibrary": True, "Version": "2.13.1.3887",
                   "RunType": "Manual", "RunPeriod": "1000"},
        "Camera": {"Name": "_Background Preview", "EyeX": -17.0, "EyeY": 24.0, "EyeZ": 50.0,
                   "LookX": 12.0, "LookY": -13.0, "LookZ": -58.0,
                   "UpX": 0.0, "UpY": 1.0, "UpZ": 0.0},
        "ConnectorPins": [], "NodeViews": node_views, "Annotations": [],
        "X": 60.0, "Y": 60.0, "Zoom": 0.9,
    },
}

destino = os.path.join(RAIZ, "PintarFachadas.dyn")
with open(destino, "w", encoding="utf-8") as f:
    json.dump(grafo, f, indent=2, ensure_ascii=False)
print("gerado:", destino, os.path.getsize(destino), "bytes")
