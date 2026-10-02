#!/usr/bin/env python3
"""
Gera o Relatório Semanal MCMB a partir do relatório da semana anterior (modelo)
e de um arquivo JSON com os dados da semana.

Uso:
    python gerar_relatorio.py MODELO.docx dados.json SAIDA.docx

Formato de dados.json:
{
  "inicio": "21/09/2026",
  "fim": "25/09/2026",
  "obras": [
    {
      "titulo": "RF 38 – TATIANE SANTOS DA SILVA",
      "fisico": "45%",
      "atividades": ["Contrapiso área de serviço.", "..."],
      "sanemar": "Finalizado",
      "proxima": ["Sem atividade."],
      "observacoes": "",
      "figuras": [
        {"legenda": "Contrapiso área de serviço", "data": "21/09", "imagem": "fotos/rf38_2109_1.jpg"}
      ]
    }
  ]
}

Tudo que é formatação (capa, cabeçalho, rodapé, estilos, tabela, legenda,
"Fonte: Elaboração própria.", tamanho das fotos 15 x 10 cm) é clonado do modelo.
Só mudam: datas da capa, sumário, títulos, conteúdo das tabelas, fotos e legendas.
"""
import copy, json, os, re, subprocess, sys, tempfile
from io import BytesIO

import docx
from docx.oxml.ns import qn
from PIL import Image, ImageOps

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R_EMBED = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed'
FIG_CX, FIG_CY = 5399730, 3600000          # 15 x 10 cm, igual ao modelo
FIG_RATIO = FIG_CX / FIG_CY
SEM_FOTO = 'Sem registro fotográfico disponível para o período.'
FONTE = 'Fonte: Elaboração própria.'


def texto(el):
    return ''.join(t.text or '' for t in el.iter(qn('w:t')))


def set_texto_unico(p, novo):
    """Coloca `novo` no primeiro w:t do parágrafo e apaga os demais textos."""
    ts = list(p.iter(qn('w:t')))
    ts[0].text = novo
    ts[0].set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    for t in ts[1:]:
        t.text = ''


def manter_com_proximo(p):
    """Liga 'manter com o próximo' no parágrafo (evita título/tabela/foto partidos)."""
    ppr = p.find(qn('w:pPr'))
    if ppr is None:
        ppr = p.makeelement(qn('w:pPr'), {}); p.insert(0, ppr)
    kn = ppr.find(qn('w:keepNext'))
    if kn is None:
        kn = ppr.makeelement(qn('w:keepNext'), {}); ppr.insert(0, kn)
    kn.set(qn('w:val'), '1')


def preparar_foto(caminho):
    """Corrige rotação EXIF, recorta ao centro em 3:2 (mesmo quadro 15x10 do
    modelo, sem distorcer) e reduz para 1600 px de largura."""
    im = ImageOps.exif_transpose(Image.open(caminho)).convert('RGB')
    w, h = im.size
    if w / h > FIG_RATIO:
        nw = int(h * FIG_RATIO); x = (w - nw) // 2
        im = im.crop((x, 0, x + nw, h))
    else:
        nh = int(w / FIG_RATIO); y = (h - nh) // 2
        im = im.crop((0, y, w, y + nh))
    im = im.resize((1600, int(1600 / FIG_RATIO)), Image.LANCZOS)
    buf = BytesIO(); im.save(buf, 'JPEG', quality=85); buf.seek(0)
    return buf


def achar_sumario(body):
    """sdtContent do sumário (docPartGallery 'Table of Contents'); senão, o 1º sdt."""
    for sdt in body.iter(qn('w:sdt')):
        g = sdt.find('.//' + qn('w:docPartGallery'))
        if g is not None and 'Contents' in (g.get(qn('w:val')) or ''):
            return sdt.find(qn('w:sdtContent'))
    return body.find('.//' + qn('w:sdtContent'))


def localizar_prototipos(body):
    els = list(body.iterchildren())
    proto = {}
    for i, el in enumerate(els):
        tag = el.tag.split('}')[1]
        if tag == 'p':
            sty = el.find('.//' + qn('w:pStyle'))
            t = texto(el).strip()
            if sty is not None and sty.get(qn('w:val')) == 'Heading1' and re.match(r'\d+\.\s*RF', t) and 'heading' not in proto:
                proto['heading'] = el; proto['i_inicio'] = i
            elif t.startswith('Figura') and el.find('.//' + qn('w:drawing')) is not None and 'figura' not in proto:
                proto['figura'] = el
            elif t.startswith('Fonte') and 'fonte' not in proto:
                proto['fonte'] = el
            elif t == SEM_FOTO and 'semfoto' not in proto:
                proto['semfoto'] = el
        elif tag == 'tbl' and 'tabela' not in proto and 'heading' in proto:
            proto['tabela'] = el
            proto['espaco'] = els[i + 1]
    faltando = {'heading', 'figura', 'fonte', 'tabela'} - proto.keys()
    if faltando:
        sys.exit(f'Modelo sem elementos esperados: {faltando}')
    return proto


def montar_tabela(proto_tbl, ob):
    tbl = copy.deepcopy(proto_tbl)
    rows = tbl.findall(qn('w:tr'))
    valores = [
        [ob.get('fisico', '')],
        ob.get('atividades') or ['Sem atividade.'],
        [ob.get('sanemar', '')],
        ob.get('proxima') or ['Sem atividade.'],
        [ob.get('observacoes', '') or ' '],
    ]
    for row, linhas in zip(rows, valores):
        tc = row.findall(qn('w:tc'))[1]
        ps = tc.findall(qn('w:p'))
        modelo_p = ps[0]
        for p in ps:
            tc.remove(p)
        for linha in linhas:
            p = copy.deepcopy(modelo_p)
            ts = list(p.iter(qn('w:t')))
            # linha "• <tab> texto": mantém o marcador e troca só o último texto
            ts[-1].text = linha
            ts[-1].set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            if not texto(modelo_p).lstrip().startswith('•'):
                for t in ts[:-1]:
                    t.text = ''
            tc.append(p)
    for i, row in enumerate(rows):
        trpr = row.find(qn('w:trPr'))
        cs = trpr.find(qn('w:cantSplit')) if trpr is not None else None
        if cs is not None:
            cs.set(qn('w:val'), '1')
        if i < len(rows) - 1:
            for p in row.iter(qn('w:p')):
                manter_com_proximo(p)
    return tbl


def gerar(modelo, dados, saida):
    d = docx.Document(modelo)
    body = d.element.body
    proto = localizar_prototipos(body)

    # 1) capa: período
    periodo = f"{dados['inicio']} - {dados['fim']}"
    for t in body.iter(qn('w:t')):
        if re.fullmatch(r'\s*\d{2}/\d{2}/\d{4}\s*[-–]\s*\d{2}/\d{2}/\d{4}\s*', t.text or ''):
            t.text = periodo

    # 2) apaga o conteúdo das obras (do 1º Heading1 até antes do sectPr final)
    els = list(body.iterchildren())
    sect_final = els[-1]
    for el in els[proto['i_inicio']:-1]:
        body.remove(el)

    docpr_id = 5000
    n_fig = 0
    bookmarks = []
    for k, ob in enumerate(dados['obras'], 1):
        titulo = f"{k}. {ob['titulo']}"
        h = copy.deepcopy(proto['heading'])
        set_texto_unico(h, titulo)
        manter_com_proximo(h)
        bm = f'_heading=h.mcmb{k:03d}'
        for b in h.iter(qn('w:bookmarkStart')):
            b.set(qn('w:name'), bm); b.set(qn('w:id'), str(900 + k))
        for b in h.iter(qn('w:bookmarkEnd')):
            b.set(qn('w:id'), str(900 + k))
        bookmarks.append((titulo, bm))
        sect_final.addprevious(h)
        sect_final.addprevious(montar_tabela(proto['tabela'], ob))
        sect_final.addprevious(copy.deepcopy(proto['espaco']))

        figs = ob.get('figuras') or []
        if not figs:
            p = copy.deepcopy(proto['semfoto'] if proto.get('semfoto') is not None else proto['fonte'])
            set_texto_unico(p, SEM_FOTO)
            sect_final.addprevious(p)
            sect_final.addprevious(copy.deepcopy(proto['espaco']))
        for fig in figs:
            n_fig += 1
            p = copy.deepcopy(proto['figura'])
            set_texto_unico(p, f"Figura {n_fig} – {fig['legenda']} ({fig['data']})")
            rid, _ = d.part.get_or_add_image(preparar_foto(fig['imagem']))
            for blip in p.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}blip'):
                blip.set(R_EMBED, rid)
            for dp in p.iter('{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr'):
                docpr_id += 1
                dp.set('id', str(docpr_id)); dp.set('name', f'foto{n_fig}.jpg')
            for ext in p.iter('{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}extent'):
                ext.set('cx', str(FIG_CX)); ext.set('cy', str(FIG_CY))
            for ext in p.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}ext'):
                if ext.get('cx'):
                    ext.set('cx', str(FIG_CX)); ext.set('cy', str(FIG_CY))
            manter_com_proximo(p)
            sect_final.addprevious(p)
            f = copy.deepcopy(proto['fonte']); set_texto_unico(f, FONTE)
            sect_final.addprevious(f)
            sect_final.addprevious(copy.deepcopy(proto['espaco']))

    # 3) sumário: uma entrada por obra (clona a 1ª entrada do modelo)
    # Só as entradas (parágrafos com hyperlink) são trocadas; o título "Sumário"
    # e parágrafos que só carregam o início/fim do campo TOC ficam onde estão.
    sdt = achar_sumario(body)
    entradas = [p for p in sdt.findall(qn('w:p')) if p.find(qn('w:hyperlink')) is not None]
    if not entradas:
        sys.exit('Sumário do modelo sem entradas (hyperlinks) para clonar.')
    base = copy.deepcopy(entradas[0])
    depois = entradas[-1].getnext()
    run_fim = None
    for p in entradas:
        for r in p.iter(qn('w:r')):
            if any(fc.get(qn('w:fldCharType')) == 'end' for fc in r.findall(qn('w:fldChar'))):
                run_fim = copy.deepcopy(r)
        sdt.remove(p)
    novos = []
    for idx, (titulo, bm) in enumerate(bookmarks):
        p = copy.deepcopy(base)
        if idx > 0:  # só a 1ª entrada carrega o início do campo TOC
            for r in list(p.findall(qn('w:r'))):
                if r.find(qn('w:fldChar')) is not None or r.find(qn('w:instrText')) is not None:
                    p.remove(r)
        hl = p.find(qn('w:hyperlink'))
        hl.set(qn('w:anchor'), bm)
        ts = list(hl.iter(qn('w:t')))
        ts[0].text = titulo; ts[-1].text = ''
        if depois is not None:
            depois.addprevious(p)
        else:
            sdt.append(p)
        novos.append(p)
    if run_fim is not None and novos:
        novos[-1].append(run_fim)

    # 4) remove imagens antigas que não são mais usadas
    usados = set(re.findall(r'r:embed="(rId\d+)"', d.element.xml)) | set(re.findall(r'r:id="(rId\d+)"', d.element.xml))
    for rid, rel in list(d.part.rels.items()):
        if rel.reltype.endswith('/image') and rid not in usados:
            d.part.drop_rel(rid) if hasattr(d.part, 'drop_rel') else d.part.rels.pop(rid)

    d.save(saida)
    preencher_paginas_sumario(saida, [t for t, _ in bookmarks])
    return n_fig


def preencher_paginas_sumario(saida, titulos):
    """Renderiza com LibreOffice para descobrir a página de cada obra e grava no sumário."""
    try:
        tmp = tempfile.mkdtemp()
        subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', tmp, saida],
                       capture_output=True, timeout=300)
        pdf = os.path.join(tmp, os.path.splitext(os.path.basename(saida))[0] + '.pdf')
        if not os.path.exists(pdf):
            raise RuntimeError('o LibreOffice não gerou o PDF (falta o libreoffice-writer? rode preparar_ambiente.sh)')
        txt =subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True).stdout
        paginas = txt.split('\f')
    except Exception as e:
        print('Aviso: não foi possível calcular as páginas do sumário:', e)
        return
    norm = lambda s: re.sub(r'\s+', ' ', s).strip()
    num = {}
    for t in titulos:
        for i, pg in enumerate(paginas[2:], 3):   # pula capa e sumário
            if norm(t) in norm(pg):
                num[t] = str(i); break
    sem_pag = [t for t in titulos if t not in num]
    if sem_pag:
        print('Aviso: página não encontrada no sumário para:', '; '.join(sem_pag))
    d = docx.Document(saida)
    sdt = achar_sumario(d.element.body)
    for p in sdt.findall(qn('w:p')):
        hl = p.find(qn('w:hyperlink'))
        if hl is None:
            continue
        ts = list(hl.iter(qn('w:t')))
        if ts and ts[0].text in num:
            ts[-1].text = num[ts[0].text]
    d.save(saida)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    modelo, dados_json, saida = sys.argv[1:]
    dados = json.load(open(dados_json, encoding='utf-8'))
    base = os.path.dirname(os.path.abspath(dados_json))
    for ob in dados['obras']:
        for f in ob.get('figuras', []):
            if not os.path.isabs(f['imagem']):
                f['imagem'] = os.path.join(base, f['imagem'])
    n = gerar(modelo, dados, saida)
    print(f'OK: {saida} — {len(dados["obras"])} obras, {n} figuras')
