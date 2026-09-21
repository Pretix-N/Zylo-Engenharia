# -*- coding: utf-8 -*-
"""Gera dynamo/Diagnostico.dyn a partir de dynamo/Diagnostico.py.

O JSON sai em ASCII puro (ensure_ascii=True): os acentos viram escapes \\uXXXX.
Assim o arquivo sobrevive a copiar/colar e a editor salvando em ANSI, que e o
jeito classico de corromper um .dyn. O Dynamo decodifica os escapes de volta.
"""
import json, os, uuid

RAIZ = os.path.dirname(os.path.abspath(__file__))


def g():
    return str(uuid.uuid4())


def porta(nome, desc):
    return {"Id": g(), "Name": nome, "Description": desc, "UsingDefaultValue": False,
            "Level": 2, "UseLevels": False, "KeepListStructure": False}


codigo = open(os.path.join(RAIZ, "Diagnostico.py"), encoding="utf-8").read()

py = {
    "ConcreteType": "PythonNodeModels.PythonNode, PythonNodeModels",
    "NodeType": "PythonScriptNode", "Code": codigo,
    "Engine": "CPython3", "EngineName": "CPython3",
    "VariableInputPorts": True, "Id": g(),
    "Inputs": [],
    "Outputs": [porta("OUT", "Result of the python script")],
    "Replication": "Disabled",
    "Description": "Runs an embedded Python script.",
}
wt_in, wt_out = porta("", "Node to show output from"), porta("", "Node output")
wt = {
    "ConcreteType": "CoreNodeModels.Watch, CoreNodeModels",
    "NodeType": "ExtensionNode", "Id": g(),
    "Inputs": [wt_in], "Outputs": [wt_out], "Replication": "Disabled",
    "Description": "Visualizes a node's output.",
}

grafo = {
    "Uuid": g(), "IsCustomNode": False,
    "Description": "Diagnostico de ambiente e API: cada etapa num try proprio.",
    "Name": "Diagnostico", "ElementResolver": {"ResolutionMap": {}},
    "Inputs": [], "Outputs": [],
    "Nodes": [py, wt],
    "Connectors": [{"Start": py["Outputs"][0]["Id"], "End": wt_in["Id"],
                    "Id": g(), "IsHidden": "False"}],
    "Dependencies": [], "NodeLibraryDependencies": [],
    "EnableLegacyPolyCurveBehavior": True, "Thumbnail": "",
    "GraphDocumentationURL": None, "ExtensionWorkspaceData": [], "Author": "",
    "Linting": {"activeLinter": "None",
                "activeLinterId": "7b75fb44-43fd-4631-a878-29f4d5d8399a",
                "warningCount": 0, "errorCount": 0},
    "Bindings": [],
    "View": {
        "Dynamo": {"ScaleFactor": 1.0, "HasRunWithoutCrash": False,
                   "IsVisibleInDynamoLibrary": True, "Version": "2.13.1.3887",
                   "RunType": "Manual", "RunPeriod": "1000"},
        "Camera": {"Name": "_Background Preview", "EyeX": -17.0, "EyeY": 24.0,
                   "EyeZ": 50.0, "LookX": 12.0, "LookY": -13.0, "LookZ": -58.0,
                   "UpX": 0.0, "UpY": 1.0, "UpZ": 0.0},
        "ConnectorPins": [],
        "NodeViews": [
            {"Id": py["Id"], "Name": "Diagnostico", "IsSetAsInput": False,
             "IsSetAsOutput": False, "Excluded": False, "ShowGeometry": True,
             "X": 0.0, "Y": 0.0},
            {"Id": wt["Id"], "Name": "resultado", "IsSetAsInput": False,
             "IsSetAsOutput": False, "Excluded": False, "ShowGeometry": True,
             "X": 360.0, "Y": 0.0},
        ],
        "Annotations": [], "X": 120.0, "Y": 120.0, "Zoom": 1.0,
    },
}

destino = os.path.join(RAIZ, "Diagnostico.dyn")
with open(destino, "w", encoding="ascii") as f:
    json.dump(grafo, f, indent=2, ensure_ascii=True)
print("gerado:", destino, os.path.getsize(destino), "bytes")
