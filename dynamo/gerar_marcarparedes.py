# -*- coding: utf-8 -*-
"""Gera dynamo/MarcarParedes.dyn a partir de dynamo/MarcarParedes.py.
JSON em ASCII puro para sobreviver a copiar/colar e a editor em ANSI."""
import json, os, uuid

RAIZ = os.path.dirname(os.path.abspath(__file__))
g = lambda: str(uuid.uuid4())


def porta(nome, desc):
    return {"Id": g(), "Name": nome, "Description": desc, "UsingDefaultValue": False,
            "Level": 2, "UseLevels": False, "KeepListStructure": False}


def code_block(code, desc):
    return {"ConcreteType": "Dynamo.Graph.Nodes.CodeBlockNodeModel, DynamoCore",
            "NodeType": "CodeBlockNode", "Code": code, "Id": g(), "Inputs": [],
            "Outputs": [porta("", "Value of expression at line 1")],
            "Replication": "Disabled", "Description": desc}


def boolean(valor):
    return {"ConcreteType": "CoreNodeModels.Input.BoolSelector, CoreNodeModels",
            "NodeType": "BooleanInputNode", "InputValue": valor, "Id": g(), "Inputs": [],
            "Outputs": [porta("", "Boolean")], "Replication": "Disabled",
            "Description": "Selection between a true and false."}


entradas = [porta("IN[{0}]".format(i), "Input #{0}".format(i)) for i in range(4)]
py = {"ConcreteType": "PythonNodeModels.PythonNode, PythonNodeModels",
      "NodeType": "PythonScriptNode",
      "Code": open(os.path.join(RAIZ, "MarcarParedes.py"), encoding="utf-8").read(),
      "Engine": "CPython3", "EngineName": "CPython3", "VariableInputPorts": True,
      "Id": g(), "Inputs": entradas,
      "Outputs": [porta("OUT", "Result of the python script")],
      "Replication": "Disabled", "Description": "Runs an embedded Python script."}

cb_escopo = code_block('"modelo";', 'escopo: "modelo", "vista" ou "selecao"')
cb_texto = code_block('"PARAM_MARCA0";', 'texto a gravar; "" limpa o parametro')
cb_param = code_block('"Comentarios";', 'nome do parametro de texto')
bl_exec = boolean(False)
wt_in, wt_out = porta("", "Node to show output from"), porta("", "Node output")
wt = {"ConcreteType": "CoreNodeModels.Watch, CoreNodeModels", "NodeType": "ExtensionNode",
      "Id": g(), "Inputs": [wt_in], "Outputs": [wt_out], "Replication": "Disabled",
      "Description": "Visualizes a node's output."}

fontes = [cb_escopo, cb_texto, cb_param, bl_exec]
nos = fontes + [py, wt]
conexoes = [{"Start": o["Outputs"][0]["Id"], "End": d["Id"], "Id": g(), "IsHidden": "False"}
            for o, d in zip(fontes, entradas)]
conexoes.append({"Start": py["Outputs"][0]["Id"], "End": wt_in["Id"],
                 "Id": g(), "IsHidden": "False"})

titulos = [(cb_escopo, "escopo", 0, 0), (cb_texto, "texto", 0, 110),
           (cb_param, "parametro", 0, 220), (bl_exec, "executar", 0, 330),
           (py, "MarcarParedes", 400, 120), (wt, "resumo", 760, 120)]
node_views = [{"Id": n["Id"], "Name": nome, "IsSetAsInput": False, "IsSetAsOutput": False,
               "Excluded": False, "ShowGeometry": True, "X": float(x), "Y": float(y)}
              for n, nome, x, y in titulos]

grafo = {
    "Uuid": g(), "IsCustomNode": False,
    "Description": "Grava um texto no parametro de todas as paredes do escopo.",
    "Name": "MarcarParedes", "ElementResolver": {"ResolutionMap": {}},
    "Inputs": [], "Outputs": [], "Nodes": nos, "Connectors": conexoes,
    "Dependencies": [], "NodeLibraryDependencies": [],
    "EnableLegacyPolyCurveBehavior": True, "Thumbnail": "",
    "GraphDocumentationURL": None, "ExtensionWorkspaceData": [], "Author": "",
    "Linting": {"activeLinter": "None",
                "activeLinterId": "7b75fb44-43fd-4631-a878-29f4d5d8399a",
                "warningCount": 0, "errorCount": 0},
    "Bindings": [],
    "View": {"Dynamo": {"ScaleFactor": 1.0, "HasRunWithoutCrash": False,
                        "IsVisibleInDynamoLibrary": True, "Version": "2.13.1.3887",
                        "RunType": "Manual", "RunPeriod": "1000"},
             "Camera": {"Name": "_Background Preview", "EyeX": -17.0, "EyeY": 24.0,
                        "EyeZ": 50.0, "LookX": 12.0, "LookY": -13.0, "LookZ": -58.0,
                        "UpX": 0.0, "UpY": 1.0, "UpZ": 0.0},
             "ConnectorPins": [], "NodeViews": node_views, "Annotations": [],
             "X": 60.0, "Y": 60.0, "Zoom": 0.9}}

destino = os.path.join(RAIZ, "MarcarParedes.dyn")
with open(destino, "w", encoding="ascii") as f:
    json.dump(grafo, f, indent=2, ensure_ascii=True)
print("gerado:", destino, os.path.getsize(destino), "bytes")
