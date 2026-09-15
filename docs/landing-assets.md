# Assets da landing page

Coloque os arquivos abaixo nesta pasta. Os nomes precisam bater exatamente —
são referenciados em `src/data/site.js`.

| Arquivo | O que é | Observação |
|---|---|---|
| `01-estadio-bloco-sanitario.jpg` | Bloco sanitário do estádio | Proporção 4:3, mín. 1600×1200 px |
| `02-reforma-fossa-filtro.jpg` | Reforma de banheiro com fossa e filtro | Proporção 4:3, mín. 1600×1200 px |
| `portfolio-zylo-hidrossanitario.pdf` | Portfólio completo | Alvo do botão principal da seção |

## Comportamento enquanto os arquivos não existem

- **Imagem faltando:** o card mostra um aviso com o caminho esperado, em vez de
  uma imagem quebrada.
- **PDF faltando:** o botão "Baixar Portfólio Completo (PDF)" vira
  "Receber Portfólio Completo (PDF)" e abre o WhatsApp — o CTA principal
  nunca entrega um 404.

Assim que os arquivos entrarem, o comportamento normal volta sozinho. Nenhuma
alteração de código é necessária.

## Formulário de contato

O formulário grava em `/leads` no Firebase Realtime Database. Para funcionar com
visitante anônimo, a regra do banco precisa permitir escrita nesse nó:

```json
{
  "rules": {
    "leads": {
      ".read": "auth != null",
      ".write": true
    }
  }
}
```

Se a escrita for negada, o formulário mostra o erro e oferece o envio da mesma
mensagem pelo WhatsApp — o contato não se perde em silêncio.
