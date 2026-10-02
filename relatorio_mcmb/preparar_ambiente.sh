#!/usr/bin/env bash
# Instala o que os scripts precisam no container do Claude (ou num Linux Debian/Ubuntu).
# O container da nuvem é descartável: rode isto no início de cada sessão de relatório.
set -euo pipefail
cd "$(dirname "$0")"

pip install -q -r requirements.txt

# gerar_relatorio.py usa soffice (Writer) + pdftotext para numerar o sumário.
# O container vem só com libreoffice-core, que não abre .docx.
if ! dpkg -s libreoffice-writer >/dev/null 2>&1 || ! command -v pdftotext >/dev/null; then
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
        libreoffice-writer poppler-utils >/dev/null
fi

python3 -c "import docx, PIL, requests" && command -v soffice >/dev/null && command -v pdftotext >/dev/null
echo "Ambiente pronto."
