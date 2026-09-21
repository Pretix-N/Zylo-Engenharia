# -*- coding: utf-8 -*-
"""
MarcarParedes — grava um texto no parâmetro de todas as paredes do modelo.

ENTRADAS (portas IN):
    IN[0]  escopo    : "modelo"  -> todas as paredes colocadas no documento
                       "vista"   -> só as paredes visíveis na vista ativa
                       "selecao" -> só o que estiver selecionado no Revit
    IN[1]  texto     : o texto a gravar (ex.: "PARAM_MARCA0"). Use "" para LIMPAR.
    IN[2]  parametro : nome do parâmetro de texto (ex.: "Comentários", "Marca")
    IN[3]  executar  : bool -> False = simulação, não altera nada

SAÍDA (OUT):
    [resumo, detalhe]   detalhe = id | tipo | valor_antes | valor_depois

ANTES DE LIGAR 'executar':
    Isto SOBRESCREVE o parâmetro em todas as paredes do escopo. Rode primeiro em
    simulação e GUARDE a coluna 'valor_antes' do detalhe — é o seu backup. Não há
    desfazer no script; no Revit, Ctrl+Z desfaz a transação inteira.

Engine: CPython3.
"""

import clr

clr.AddReference('RevitAPI')
clr.AddReference('RevitServices')

import Autodesk.Revit.DB as DB
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager


# ---------------------------------------------------------------------------
# Ajustes
# ---------------------------------------------------------------------------

# True = só escreve onde o parâmetro está VAZIO. É a opção não destrutiva:
# nenhum valor existente é perdido. Comece por aqui se tiver qualquer dúvida.
APENAS_VAZIOS = False

# Quantas linhas de detalhe imprimir no resumo.
LIMITE_RESUMO = 20


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def _entrada(indice, padrao):
    try:
        valor = IN[indice]  # noqa: F821
    except Exception:
        return padrao
    return padrao if valor is None else valor


def normalizar(texto):
    acentos = {u'á': u'a', u'à': u'a', u'ã': u'a', u'â': u'a', u'é': u'e',
               u'ê': u'e', u'í': u'i', u'ó': u'o', u'ô': u'o', u'õ': u'o',
               u'ú': u'u', u'ç': u'c'}
    t = (texto or u"").lower()
    for a, b in acentos.items():
        t = t.replace(a, b)
    return t


def nome_seguro(elemento):
    try:
        return elemento.Name
    except Exception:
        return u"(sem nome)"


def id_valor(element_id):
    for nome in ('Value', 'IntegerValue'):
        try:
            return getattr(element_id, nome)
        except Exception:
            continue
    return -1


# Parâmetros nativos têm nome traduzido. Buscar pelo BuiltInParameter primeiro
# faz o script funcionar em Revit pt-BR e en-US sem mudar nada.
BIPS_POR_NOME = {
    "comentarios": 'ALL_MODEL_INSTANCE_COMMENTS',
    "comments": 'ALL_MODEL_INSTANCE_COMMENTS',
    "marca": 'ALL_MODEL_MARK',
    "mark": 'ALL_MODEL_MARK',
}


def achar_parametro(elemento, nome):
    chave = normalizar(nome).strip()
    nome_bip = BIPS_POR_NOME.get(chave)
    if nome_bip:
        bip = getattr(DB.BuiltInParameter, nome_bip, None)
        if bip is not None:
            try:
                p = elemento.get_Parameter(bip)
                if p is not None:
                    return p
            except Exception:
                pass
    try:
        return elemento.LookupParameter(nome)
    except Exception:
        return None


def valor_atual(p):
    try:
        if p.HasValue:
            return p.AsString() or u""
    except Exception:
        pass
    return u""


# ---------------------------------------------------------------------------
# Coleta das paredes
# ---------------------------------------------------------------------------

def coletar_paredes(doc, uidoc, escopo, log):
    """Só instâncias colocadas — WhereElementIsNotElementType descarta os tipos
    de parede que existem no projeto mas não foram usados."""
    chave = normalizar(str(escopo)).strip()

    if chave == "selecao":
        saida = []
        try:
            for eid in uidoc.Selection.GetElementIds():
                el = doc.GetElement(eid)
                if el is not None and isinstance(el, DB.Wall):
                    saida.append(el)
        except Exception as erro:
            log.append(u"Não consegui ler a seleção: {0}".format(erro))
        if not saida:
            log.append(u"ERRO: nada selecionado, ou a seleção não tem paredes.")
        return saida

    try:
        if chave == "vista":
            col = DB.FilteredElementCollector(doc, doc.ActiveView.Id)
            log.append(u"Escopo: paredes visíveis na vista ativa.")
        else:
            col = DB.FilteredElementCollector(doc)
            log.append(u"Escopo: TODAS as paredes colocadas no documento.")
        col = col.OfCategory(DB.BuiltInCategory.OST_Walls).WhereElementIsNotElementType()
        return list(col)
    except Exception as erro:
        log.append(u"ERRO ao coletar paredes: {0}".format(erro))
        return []


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------

escopo = _entrada(0, "modelo")
texto = _entrada(1, "PARAM_MARCA0")
nome_param = _entrada(2, "Comentários")
executar = bool(_entrada(3, False))

texto = u"" if texto is None else u"{0}".format(texto)

resumo = []
detalhe = []


def principal():
    doc = DocumentManager.Instance.CurrentDBDocument
    uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument

    paredes = coletar_paredes(doc, uidoc, escopo, resumo)
    if not paredes:
        return [resumo, detalhe]

    resumo.append(u"{0} parede(s) no escopo.".format(len(paredes)))
    resumo.append(u"Parâmetro alvo: '{0}'".format(nome_param))
    resumo.append(u"Texto a gravar: {0}".format(
        u"(VAZIO — vai LIMPAR o parâmetro)" if texto == u"" else u"'{0}'".format(texto)))
    if APENAS_VAZIOS:
        resumo.append(u"APENAS_VAZIOS ligado: só grava onde o parâmetro está vazio.")

    # levanta o estado atual antes de qualquer escrita
    plano, sem_param, ja_ok, protegidos = [], 0, 0, 0
    for el in paredes:
        p = achar_parametro(el, nome_param)
        if p is None:
            sem_param += 1
            continue
        if p.IsReadOnly:
            protegidos += 1
            continue
        antes = valor_atual(p)
        if antes == texto:
            ja_ok += 1
            continue
        if APENAS_VAZIOS and antes != u"":
            continue
        plano.append((el, p, antes))

    if sem_param:
        resumo.append(u"{0} parede(s) sem o parâmetro '{1}'.".format(sem_param, nome_param))
    if protegidos:
        resumo.append(u"{0} parede(s) com o parâmetro somente leitura.".format(protegidos))
    if ja_ok:
        resumo.append(u"{0} parede(s) já estavam com esse valor.".format(ja_ok))

    # o que vai ser PERDIDO — é o que importa antes de apertar o botão
    com_conteudo = [(el, antes) for el, _, antes in plano if antes != u""]
    if com_conteudo:
        resumo.append(u"")
        resumo.append(u"ATENÇÃO: {0} parede(s) têm conteúdo em '{1}' que será "
                      u"SOBRESCRITO:".format(len(com_conteudo), nome_param))
        distintos = {}
        for _, antes in com_conteudo:
            distintos[antes] = distintos.get(antes, 0) + 1
        for valor, n in sorted(distintos.items(), key=lambda kv: kv[1], reverse=True)[:10]:
            resumo.append(u"   '{0}'  ({1}x)".format(valor[:60], n))
        if len(distintos) > 10:
            resumo.append(u"   ... mais {0} valor(es) distinto(s)".format(len(distintos) - 10))
        resumo.append(u"Guarde a coluna 'valor_antes' do OUT[1]: é o seu backup.")
        resumo.append(u"")

    for el, _, antes in plano[:LIMITE_RESUMO]:
        detalhe.append([id_valor(el.Id), nome_seguro(el), antes, texto])
    for el, _, antes in plano[LIMITE_RESUMO:]:
        detalhe.append([id_valor(el.Id), nome_seguro(el), antes, texto])

    resumo.append(u"{0} parede(s) seriam alteradas.".format(len(plano)))

    if not executar:
        resumo.insert(0, u"*** SIMULAÇÃO — nada foi alterado. "
                         u"Ligue 'executar' para gravar. ***")
        return [resumo, detalhe]

    TransactionManager.Instance.EnsureInTransaction(doc)
    ok, falhas = 0, []
    for el, p, _ in plano:
        try:
            p.Set(texto)
            ok += 1
        except Exception as erro:
            falhas.append((id_valor(el.Id), str(erro)))
    TransactionManager.Instance.TransactionTaskDone()

    resumo.append(u"GRAVADO em {0} parede(s).".format(ok))
    if falhas:
        resumo.append(u"{0} falha(s):".format(len(falhas)))
        for eid, msg in falhas[:20]:
            resumo.append(u"   id {0}: {1}".format(eid, msg))
    return [resumo, detalhe]


try:
    OUT = principal()
except Exception:
    import traceback
    resumo.append(u"=== ERRO NAO TRATADO — copie o bloco abaixo ===")
    for _l in traceback.format_exc().splitlines():
        resumo.append(_l)
    OUT = [resumo, detalhe]
