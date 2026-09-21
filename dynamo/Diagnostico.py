# -*- coding: utf-8 -*-
"""Diagnóstico do nó Python do Dynamo.

Nenhuma etapa pode derrubar as outras: cada uma tem seu próprio try.
Se ESTE nó também devolver null, o problema é o nó/engine, não o script.
"""

etapas = []
DB = None
DocumentManager = None


def passo(rotulo, fn):
    try:
        etapas.append(u"OK      {0}: {1}".format(rotulo, fn()))
    except Exception as erro:
        etapas.append(u"FALHOU  {0}: {1}: {2}".format(rotulo, type(erro).__name__, erro))


try:
    import sys
    etapas.append(u"OK      01 python: {0}".format(sys.version.replace("\n", " ")))
except Exception as erro:
    etapas.append(u"FALHOU  01 python: {0}".format(erro))

try:
    etapas.append(u"OK      02 acentos: ação, coração, portão, área — em dash")
except Exception as erro:
    etapas.append(u"FALHOU  02 acentos: {0}".format(erro))

try:
    import clr
    clr.AddReference('RevitAPI')
    clr.AddReference('RevitServices')
    etapas.append(u"OK      03 clr + AddReference")
except Exception as erro:
    etapas.append(u"FALHOU  03 clr: {0}: {1}".format(type(erro).__name__, erro))

try:
    import Autodesk.Revit.DB as _DB
    from RevitServices.Persistence import DocumentManager as _DM
    from RevitServices.Transactions import TransactionManager as _TM
    DB, DocumentManager = _DB, _DM
    etapas.append(u"OK      04 imports Revit")
except Exception as erro:
    etapas.append(u"FALHOU  04 imports Revit: {0}: {1}".format(type(erro).__name__, erro))

if DB is not None and DocumentManager is not None:
    passo(u"05 documento", lambda: DocumentManager.Instance.CurrentDBDocument.Title)
    passo(u"06 vista ativa", lambda: u"{0}  /  tipo {1}".format(
        DocumentManager.Instance.CurrentDBDocument.ActiveView.Name,
        DocumentManager.Instance.CurrentDBDocument.ActiveView.ViewType))
    passo(u"07 overrides na vista", lambda:
          DocumentManager.Instance.CurrentDBDocument.ActiveView.AreGraphicsOverridesAllowed())
    passo(u"08 seleção", lambda: u"{0} elemento(s)".format(len(list(
        DocumentManager.Instance.CurrentUIApplication
        .ActiveUIDocument.Selection.GetElementIds()))))
    passo(u"09 BuiltInCategory", lambda: u"{0}, {1}".format(
        DB.BuiltInCategory.OST_Walls, DB.BuiltInCategory.OST_Parts))
    passo(u"10 Category.GetCategory", lambda: DB.Category.GetCategory(
        DocumentManager.Instance.CurrentDBDocument,
        DB.BuiltInCategory.OST_Windows).Name)
    passo(u"11 OverrideGraphicSettings", lambda: u"criado, tem "
          u"SetSurfaceForegroundPatternColor={0}".format(
              hasattr(DB.OverrideGraphicSettings(), 'SetSurfaceForegroundPatternColor')))
    passo(u"12 DB.Color", lambda: u"{0}".format(DB.Color(250, 214, 140)))
    passo(u"13 SpecTypeId", lambda: u"{0}".format(DB.SpecTypeId.Reference.Material))
    passo(u"14 ElementId.Value", lambda: u"{0}".format(
        getattr(DB.ElementId(7), 'Value', getattr(DB.ElementId(7), 'IntegerValue', '?'))))
    passo(u"15 isinstance DB.Group", lambda: isinstance(object(), DB.Group))

    # o que o script de verdade faz no primeiro passo
    def _primeiro_elemento():
        doc = DocumentManager.Instance.CurrentDBDocument
        uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument
        ids = list(uidoc.Selection.GetElementIds())
        if not ids:
            return u"nada selecionado"
        el = doc.GetElement(ids[0])
        bb = el.get_BoundingBox(None)
        try:
            nome = el.Name
        except Exception as e:
            nome = u"<Name lança {0}>".format(type(e).__name__)
        return u"id={0} nome={1} categoria={2} bbox={3}".format(
            ids[0], nome, el.Category.Name, u"ok" if bb is not None else u"None")
    passo(u"16 primeiro selecionado", _primeiro_elemento)

etapas.append(u"--- fim do diagnóstico, {0} etapas ---".format(len(etapas)))
OUT = etapas
