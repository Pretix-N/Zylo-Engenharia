const APPS_SCRIPT_URL = "https://script.google.com/macros/s/SEU_ID_AQUI/exec";

export async function enviarContato({ nome, email, telefone, mensagem, assunto }) {
  const resposta = await fetch(APPS_SCRIPT_URL, {
    method: "POST",
    headers: { "Content-Type": "text/plain" },
    body: JSON.stringify({ nome, email, telefone, mensagem, assunto }),
  });

  if (!resposta.ok) throw new Error("Falha na requisição");

  const dados = await resposta.json();
  if (!dados.sucesso) throw new Error(dados.mensagem);

  return dados;
}
