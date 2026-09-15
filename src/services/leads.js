// Grava o lead em /leads no Realtime Database.
// O Firebase é importado dinamicamente: o visitante só baixa o SDK se
// realmente enviar o formulário.
// Se as regras do banco bloquearem escrita anônima (ou a rede falhar), o
// chamador recebe erro e oferece o WhatsApp como saída — nenhum lead
// é perdido em silêncio.
export async function enviarLead({ nome, empresa, email, mensagem }) {
  const [{ ref, push, serverTimestamp }, { db }] = await Promise.all([
    import('firebase/database'),
    import('../firebase'),
  ])

  await push(ref(db, 'leads'), {
    nome: nome.trim(),
    empresa: empresa.trim(),
    email: email.trim(),
    mensagem: mensagem.trim(),
    origem: 'landing',
    criadoEm: serverTimestamp(),
  })
}

export function resumoParaWhatsapp({ nome, empresa, email, mensagem }) {
  return [
    'Olá, João. Vim pelo site da Zylo.',
    '',
    `Nome: ${nome}`,
    `Empresa: ${empresa}`,
    `E-mail: ${email}`,
    '',
    mensagem,
  ].join('\n')
}
