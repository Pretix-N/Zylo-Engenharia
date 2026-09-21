# -*- coding: utf-8 -*-
"""Diagnostico de ambiente e API — no Python do Dynamo (CPython3).

Regra de ouro: nenhuma etapa derruba as outras. Cada verificacao tem seu
proprio try e escreve uma linha em `etapas`, que vira o OUT.
Se ESTE no devolver null, o problema e o no/engine, nao o script.
"""

etapas = []
DB = None
DocumentManager = None
TransactionManager = None


def passo(rotulo, fn):
    """Executa fn() e registra OK ou FALHOU. Nunca propaga excecao."""
    try:
        etapas.append(u"OK      {0}: {1}".format(rotulo, fn()))
    except Exception as erro:
        etapas.append(u"FALHOU  {0}: {1}: {2}".format(rotulo, type(erro).__name__, erro))


def doc():
    return DocumentManager.Instance.CurrentDBDocument


def uidoc():
    return DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument


# 1 -------------------------------------------------------------------------
try:
    import sys
    etapas.append(u"OK      01 python: {0}".format(sys.version.replace("\n", " ")))
except Exception as erro:
    etapas.append(u"FALHOU  01 python: {0}: {1}".format(type(erro).__name__, erro))

# 2 -------------------------------------------------------------------------
try:
    _acentos = u"acao coracao portao area cedilha traco"
    _reais = u"ação coração portão área çedilha — travessão"
    etapas.append(u"OK      02 encoding: {0} | {1} chars".format(_reais, len(_reais)))
except Exception as erro:
    etapas.append(u"FALHOU  02 encoding: {0}: {1}".format(type(erro).__name__, erro))

# 3 -------------------------------------------------------------------------
try:
    import clr
    clr.AddReference('RevitAPI')
    clr.AddReference('RevitServices')
    etapas.append(u"OK      03 clr + AddReference(RevitAPI, RevitServices)")
except Exception as erro:
    etapas.append(u"FALHOU  03 clr: {0}: {1}".format(type(erro).__name__, erro))

# 4 -------------------------------------------------------------------------
try:
    import Autodesk.Revit.DB as _DB
    from RevitServices.Persistence import DocumentManager as _DM
    from RevitServices.Transactions import TransactionManager as _TM
    DB, DocumentManager, TransactionManager = _DB, _DM, _TM
    etapas.append(u"OK      04 imports: DB, DocumentManager, TransactionManager")
except Exception as erro:
    etapas.append(u"FALHOU  04 imports: {0}: {1}".format(type(erro).__name__, erro))

if DB is None or DocumentManager is None:
    etapas.append(u"        (etapas 05-18 puladas: sem acesso a API do Revit)")
else:
    # 5 ---------------------------------------------------------------------
    passo(u"05 documento", lambda: doc().Title)

    # 6 ---------------------------------------------------------------------
    passo(u"06 vista ativa", lambda: u"{0}  /  tipo {1}".format(
        doc().ActiveView.Name, doc().ActiveView.ViewType))

    # 7 ---------------------------------------------------------------------
    passo(u"07 overrides permitidos na vista",
          lambda: doc().ActiveView.AreGraphicsOverridesAllowed())

    # 8 ---------------------------------------------------------------------
    passo(u"08 selecao", lambda: u"{0} elemento(s)".format(
        len(list(uidoc().Selection.GetElementIds()))))

    # 9 ---------------------------------------------------------------------
    passo(u"09 BuiltInCategory", lambda: u"OST_Walls={0}, OST_Parts={1}".format(
        DB.BuiltInCategory.OST_Walls, DB.BuiltInCategory.OST_Parts))

    # 10 --------------------------------------------------------------------
    def _categoria():
        cat = DB.Category.GetCategory(doc(), DB.BuiltInCategory.OST_Windows)
        if cat is None:
            return u"GetCategory devolveu None (categoria ausente no modelo)"
        return u"OST_Windows -> '{0}'".format(cat.Name)
    passo(u"10 Category.GetCategory", _categoria)

    # 11 --------------------------------------------------------------------
    def _ogs():
        o = DB.OverrideGraphicSettings()
        novo = hasattr(o, 'SetSurfaceForegroundPatternColor')
        velho = hasattr(o, 'SetProjectionFillColor')
        return u"SetSurfaceForegroundPatternColor={0}, SetProjectionFillColor={1}".format(
            novo, velho)
    passo(u"11 OverrideGraphicSettings", _ogs)

    # 12 --------------------------------------------------------------------
    passo(u"12 DB.Color", lambda: u"(250,214,140) -> R={0} G={1} B={2}".format(
        DB.Color(250, 214, 140).Red, DB.Color(250, 214, 140).Green,
        DB.Color(250, 214, 140).Blue))

    # 13 --------------------------------------------------------------------
    passo(u"13 SpecTypeId.Reference.Material",
          lambda: u"{0}".format(DB.SpecTypeId.Reference.Material))

    # 14 --------------------------------------------------------------------
    def _elementid():
        # nao usar getattr com default: isso esconde QUAL das duas existe.
        # Value = Revit 2024+, IntegerValue = 2023 e anteriores (obsoleto depois).
        eid = DB.ElementId(7)
        achados = []
        for nome in ('Value', 'IntegerValue'):
            try:
                achados.append(u"{0}={1}".format(nome, getattr(eid, nome)))
            except Exception as e:
                achados.append(u"{0} indisponivel ({1})".format(nome, type(e).__name__))
        return u", ".join(achados)
    passo(u"14 ElementId", _elementid)

    # 15 --------------------------------------------------------------------
    passo(u"15 isinstance com DB.Group", lambda: u"chamada aceita, objeto comum -> {0}".format(
        isinstance(object(), DB.Group)))

    # 16 --------------------------------------------------------------------
    def _primeiro():
        ids = list(uidoc().Selection.GetElementIds())
        if not ids:
            return u"nada selecionado (selecione algo e rode de novo)"
        el = doc().GetElement(ids[0])
        if el is None:
            return u"GetCategory devolveu None para o id selecionado"
        try:
            nome = el.Name
        except Exception as e:
            nome = u"<Name lanca {0}: {1}>".format(type(e).__name__, e)
        try:
            cat = el.Category.Name
        except Exception as e:
            cat = u"<Category lanca {0}>".format(type(e).__name__)
        try:
            bb = el.get_BoundingBox(None)
            caixa = u"ok" if bb is not None else u"None (sem bbox no modelo)"
        except Exception as e:
            caixa = u"<get_BoundingBox lanca {0}>".format(type(e).__name__)
        return u"id={0} | nome={1} | categoria={2} | bbox={3}".format(
            ids[0], nome, cat, caixa)
    passo(u"16 primeiro selecionado", _primeiro)

    # 17 --------------------------------------------------------------------
    def _versao():
        app = DocumentManager.Instance.CurrentUIApplication.Application
        return u"Revit {0} (build {1})".format(app.VersionNumber, app.VersionBuild)
    passo(u"17 versao do Revit", _versao)

    # 18 --------------------------------------------------------------------
    def _transacao():
        # abre e fecha sem alterar nada: so prova que o TransactionManager responde
        TransactionManager.Instance.EnsureInTransaction(doc())
        TransactionManager.Instance.TransactionTaskDone()
        return u"EnsureInTransaction + TransactionTaskDone responderam"
    passo(u"18 transacao (sem alterar o modelo)", _transacao)

etapas.append(u"--- fim: {0} linhas, {1} falha(s) ---".format(
    len(etapas), len([e for e in etapas if e.startswith(u"FALHOU")])))

OUT = etapas
