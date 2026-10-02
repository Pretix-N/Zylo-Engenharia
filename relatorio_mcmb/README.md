# Relatório Semanal MCMB

Gera o relatório semanal das obras do quadro Trello **OBRAS- MCMB** a partir do
relatório da semana anterior (.docx usado como modelo).

## O que você me manda

1. **Período**: "semanal 28/09 a 02/10".
2. **Relatório da semana anterior** (.docx): define a formatação, quais obras entram e em que ordem.
3. **Fotos**: o `.zip` gerado pelo `baixar_fotos_trello.py` no seu PC. O container
   na nuvem não acessa trello.com, então as fotos não podem ser baixadas daqui.

### No seu PC (uma vez por semana)

```
pip install requests
python baixar_fotos_trello.py 28/09/2026 02/10/2026
```

Na primeira vez, crie `trello_credenciais.txt` ao lado do script (veja o
cabeçalho do script). **Não anexe esse arquivo no chat.** Anexe só o
`semana_DD-MM_a_DD-MM.zip`.

## O que eu rodo (no container)

```
bash relatorio_mcmb/preparar_ambiente.sh
python3 relatorio_mcmb/extrair_semana.py semana/semana_trello.json modelo.docx 28/09/2026 02/10/2026 semana/dados.json
# escolho as fotos, preencho "figuras" em dados.json
python3 relatorio_mcmb/gerar_relatorio.py modelo.docx semana/dados.json "Relatório_Semanal_28-09_a_02-10.docx"
```

`% Físico`, `SANEMAR`, `Próxima semana` e `Observações` **não estão no Trello**.
Eles são copiados da semana anterior, então revise esses campos.
