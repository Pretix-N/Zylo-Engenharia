#!/usr/bin/env python3
"""
Baixa do Trello as fotos e descrições dos cards "Diário" do quadro OBRAS- MCMB
para um período, organizadas por obra e por dia. Roda no SEU computador
(o ambiente do Claude não consegue acessar trello.com).

Uso (Windows/Mac/Linux, Python 3.9+ e `pip install requests`):
    python baixar_fotos_trello.py 28/09/2026 02/10/2026

Na primeira vez, crie a chave e o token da API do Trello:
  1. Acesse https://trello.com/power-ups/admin , crie um Power-Up qualquer
     (ex.: "relatorio-mcmb") e gere a "API key".
  2. Na mesma página, clique em "Token" e autorize (só leitura basta).
  3. Salve os dois num arquivo trello_credenciais.txt, ao lado deste script:
        KEY=xxxxxxxx
        TOKEN=yyyyyyyy
Nunca envie esse arquivo para ninguém (nem para o Claude).

Saída: pasta  semana_DD-MM_a_DD-MM/  com
    fotos/RF38/21-09_1.jpg ...
    semana_trello.json   (obra -> dias -> descrição + fotos)
e um .zip da pasta, pronto para anexar no chat.
"""
import json, os, re, shutil, sys, unicodedata
from datetime import datetime, timedelta, timezone

import requests

BOARD = 'lP1D7FL1'                      # https://trello.com/b/lP1D7FL1/obras-mcmb
BRT = timezone(timedelta(hours=-3))
API = 'https://api.trello.com/1'


def credenciais():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trello_credenciais.txt')
    c = dict(l.strip().split('=', 1) for l in open(p, encoding='utf-8') if '=' in l)
    return c['KEY'].strip(), c['TOKEN'].strip()


def eh_diario(nome):
    """'Diário', 'DIARIO', ' diario ' etc."""
    s = unicodedata.normalize('NFKD', nome).encode('ascii', 'ignore').decode()
    return s.strip().upper() == 'DIARIO'


def obter(url, **kw):
    r = requests.get(url, **kw)
    if r.status_code in (401, 403):
        sys.exit(f'Trello recusou o acesso ({r.status_code}): confira KEY/TOKEN em trello_credenciais.txt.')
    r.raise_for_status()
    return r


def rf(nome):
    m = re.search(r'RF\s*[-–]?\s*(\d+\s*[A-Z]?)\b', nome.upper())
    return 'RF' + m.group(1).replace(' ', '') if m else re.sub(r'\W+', '_', nome)[:20]


def main(ini, fim):
    key, token = credenciais()
    auth = {'key': key, 'token': token}
    hdr = {'Authorization': f'OAuth oauth_consumer_key="{key}", oauth_token="{token}"'}
    di = datetime.strptime(ini, '%d/%m/%Y').date()
    df = datetime.strptime(fim, '%d/%m/%Y').date()

    listas = {l['id']: l['name'] for l in
              obter(f'{API}/boards/{BOARD}/lists', params=auth, timeout=60).json()}
    cards = obter(f'{API}/boards/{BOARD}/cards', timeout=120, params={
        **auth, 'fields': 'name,desc,due,idList,closed,url',
        'attachments': 'true', 'attachment_fields': 'name,url,mimeType,isUpload,date'}).json()

    pasta = f"semana_{di:%d-%m}_a_{df:%d-%m}"
    os.makedirs(os.path.join(pasta, 'fotos'), exist_ok=True)
    saida = {'inicio': ini, 'fim': fim, 'obras': {}}
    total = 0
    seq = {}   # (obra, dia) -> nº da última foto; evita colisão com 2 cards no mesmo dia
    for c in cards:
        if c.get('closed') or not c.get('due') or not eh_diario(c['name']):
            continue
        dia = datetime.fromisoformat(c['due'].replace('Z', '+00:00')).astimezone(BRT).date()
        if not (di <= dia <= df):
            continue
        nome_lista = listas.get(c['idList'], '?')
        cod = rf(nome_lista)
        fotos = []
        imgs = [a for a in c.get('attachments', [])
                if a.get('isUpload') and (a.get('mimeType') or '').startswith('image/')]
        for a in sorted(imgs, key=lambda a: a.get('date', '')):
            n = seq[cod, dia] = seq.get((cod, dia), 0) + 1
            ext = os.path.splitext(a['name'])[1].lower() or '.jpg'
            rel = os.path.join('fotos', cod, f"{dia:%d-%m}_{n}{ext}")
            dest = os.path.join(pasta, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if not os.path.exists(dest):
                r = obter(a['url'], headers=hdr, timeout=120)
                open(dest, 'wb').write(r.content)
            fotos.append(rel.replace('\\', '/')); total += 1
        ob = saida['obras'].setdefault(cod, {'lista': nome_lista, 'dias': []})
        ob['dias'].append({'data': f'{dia:%d/%m}', 'iso': dia.isoformat(),
                           'descricao': c['desc'], 'url': c['url'], 'fotos': fotos})
        print(f'{cod:8} {dia:%d/%m}  {len(fotos)} foto(s)')
    for ob in saida['obras'].values():
        ob['dias'].sort(key=lambda d: d['iso'])
    json.dump(saida, open(os.path.join(pasta, 'semana_trello.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    shutil.make_archive(pasta, 'zip', pasta)
    print(f'\nPronto: {total} fotos em {pasta}/  ->  anexe {pasta}.zip no chat.')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
