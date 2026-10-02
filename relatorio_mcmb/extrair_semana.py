#!/usr/bin/env python3
"""
Monta o rascunho dados.json da semana a partir de:
  - board.json : saída do Trello (cards do quadro "OBRAS- MCMB", com list/due/desc)
  - o relatório anterior (.docx) : define QUAIS obras entram, na ordem, e de onde
    vêm os campos que não estão no Trello (% físico, SANEMAR, próxima semana,
    observações) — esses são copiados da semana anterior para revisão.

Uso (board.json = saída do Trello via conector, OU semana_trello.json do baixar_fotos_trello.py):
    python extrair_semana.py board.json MODELO.docx 28/09/2026 02/10/2026 dados.json

Regras:
  - Cada lista do quadro = uma obra (casada pelo código RF, ex.: "RF 128B").
  - Cada card "Diário" = um dia; a data é o "due" convertido para America/Sao_Paulo.
  - Atividades da semana = linhas da descrição dos cards do período, na ordem
    dos dias, sem repetição.
  - "figuras" sai vazio; é preenchido depois da seleção das fotos.
"""
import json, re, sys, unicodedata
from datetime import datetime, timedelta, timezone

import docx
from docx.oxml.ns import qn

BRT = timezone(timedelta(hours=-3))


def codigo_rf(nome):
    m = re.search(r'RF\s*[-–]?\s*(\d+\s*[A-Z]?)\b', nome.upper())
    return m.group(1).replace(' ', '') if m else None


def eh_diario(nome):
    s = unicodedata.normalize('NFKD', nome).encode('ascii', 'ignore').decode()
    return s.strip().upper() == 'DIARIO'


def linhas_desc(desc):
    out = []
    for l in (desc or '').splitlines():
        l = re.sub(r'^\s*[-•*]\s*', '', l).strip()
        if l:
            out.append(l if l.endswith('.') else l + '.')
    return out


def obras_do_modelo(modelo):
    d = docx.Document(modelo)
    body = list(d.element.body.iterchildren())
    obras, atual = [], None
    for el in body:
        tag = el.tag.split('}')[1]
        if tag == 'p':
            sty = el.find('.//' + qn('w:pStyle'))
            t = ''.join(x.text or '' for x in el.iter(qn('w:t'))).strip()
            if sty is not None and sty.get(qn('w:val')) == 'Heading1' and re.match(r'\d+\.\s*RF', t):
                atual = {'titulo': re.sub(r'^\d+\.\s*', '', t)}
                obras.append(atual)
        elif tag == 'tbl' and atual is not None and 'fisico' not in atual:
            vals = []
            for tr in el.findall(qn('w:tr')):
                tc = tr.findall(qn('w:tc'))[1]
                ls = [''.join(x.text or '' for x in p.iter(qn('w:t'))) for p in tc.findall(qn('w:p'))]
                ls = [re.sub(r'^\s*•\s*', '', l).strip() for l in ls]
                vals.append([l for l in ls if l])
            vals += [[]] * (5 - len(vals))   # tabela com menos linhas que o esperado
            atual['fisico'] = (vals[0] or [''])[0]
            atual['sanemar'] = (vals[2] or [''])[0]
            atual['proxima'] = vals[3] or ['Sem atividade.']
            atual['observacoes'] = ' '.join(vals[4])
    return obras


def main(board_json, modelo, ini, fim, saida):
    di = datetime.strptime(ini, '%d/%m/%Y').date()
    df = datetime.strptime(fim, '%d/%m/%Y').date()
    bruto = json.load(open(board_json, encoding='utf-8'))
    por_rf = {}
    if 'obras' in bruto:   # saída do baixar_fotos_trello.py (semana_trello.json)
        for cod, ob in bruto['obras'].items():
            for dd in ob['dias']:
                dia = datetime.fromisoformat(dd['iso']).date()
                if di <= dia <= df:
                    por_rf.setdefault(codigo_rf(cod), []).append({
                        'data': dd['data'], 'iso': dd['iso'], 'url': dd['url'], 'lista': ob['lista'],
                        'atividades': linhas_desc(dd['descricao']), 'fotos': dd['fotos']})
    nodes = bruto['cards']['nodes'] if 'cards' in bruto else []
    for c in nodes:
        if c.get('closed') or not c.get('due') or not eh_diario(c['name']):
            continue
        dia = datetime.fromisoformat(c['due'].replace('Z', '+00:00')).astimezone(BRT).date()
        if not (di <= dia <= df):
            continue
        rf = codigo_rf(c['list']['name'])
        por_rf.setdefault(rf, []).append({
            'data': dia.strftime('%d/%m'), 'iso': dia.isoformat(),
            'card_id': c['id'], 'url': c['url'], 'lista': c['list']['name'],
            'atividades': linhas_desc(c['desc']),
        })

    obras = obras_do_modelo(modelo)
    usados = set()
    for ob in obras:
        rf = codigo_rf(ob['titulo'])
        usados.add(rf)
        dias = sorted(por_rf.get(rf, []), key=lambda x: x['iso'])
        ativ = []
        for dd in dias:
            for a in dd['atividades']:
                if a.lower() not in [x.lower() for x in ativ]:
                    ativ.append(a)
        ob['atividades'] = ativ or ['Sem atividade.']
        ob['dias'] = dias
        ob['figuras'] = []

    fora = {rf: v for rf, v in por_rf.items() if rf not in usados}
    out = {'inicio': ini, 'fim': fim, 'obras': obras,
           'obras_com_diario_fora_do_relatorio': {
               str(rf): [f"{x['data']}: {' '.join(x['atividades'])}" for x in v] for rf, v in fora.items()}}
    json.dump(out, open(saida, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'{len(obras)} obras do modelo; dias no período: '
          + ', '.join(f"{codigo_rf(o['titulo'])}={len(o['dias'])}" for o in obras))
    if fora:
        print('ATENÇÃO — listas com diário no período que NÃO estão no relatório:',
              ', '.join(sorted({x['lista'] for v in fora.values() for x in v})))


if __name__ == '__main__':
    if len(sys.argv) != 6:
        sys.exit(__doc__)
    main(*sys.argv[1:])
