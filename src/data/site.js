// Fonte única de conteúdo da landing page.
// Edite este arquivo para alterar textos, contatos e projetos do portfólio.

export const contato = {
  email: 'joao.pereira@zyloengenharia.com',
  whatsappNumero: '5521987560205',
  whatsappExibicao: '(21) 98756-0205',
}

export const whatsappLink = (mensagem) =>
  `https://wa.me/${contato.whatsappNumero}?text=${encodeURIComponent(mensagem)}`

export const CTA_ORCAMENTO = whatsappLink(
  'Olá, João. Vim pelo site da Zylo e quero solicitar um orçamento de modelagem/compatibilização hidrossanitária em Revit.'
)

export const PORTFOLIO_PDF = '/portfolio/portfolio-zylo-hidrossanitario.pdf'

export const hero = {
  titulo: 'Modelagem e compatibilização de instalações hidrossanitárias em Revit.',
  subtitulo:
    'Serviço técnico terceirizado especializado para escritórios de arquitetura e construtoras.',
  // Marcadores de escopo — fatos sobre o serviço, não métricas inventadas.
  marcadores: ['Arquivo Revit (.rvt) nativo', 'Somente hidrossanitário', 'Compatibilização com estrutura e arquitetura'],
}

// Para trocar as imagens: coloque os arquivos em /public/portfolio/ com estes nomes.
// `specs` é opcional — cada item preenchido vira uma linha técnica no card.
// Preencha apenas com dados reais dos projetos.
export const projetos = [
  {
    id: 'estadio',
    titulo: 'Bloco sanitário — Estádio',
    resumo:
      'Modelagem hidrossanitária de bloco sanitário de alta densidade e compatibilização com o modelo estrutural.',
    imagem: '/portfolio/01-estadio-bloco-sanitario.jpg',
    alt: 'Modelo Revit do bloco sanitário de um estádio, com ramais, prumadas e estrutura compatibilizados',
    specs: [],
  },
  {
    id: 'reforma',
    titulo: 'Reforma de banheiro — fossa e filtro',
    resumo:
      'Detalhamento executivo do sistema de tratamento (fossa e filtro) e das prumadas, no nível de detalhe que a obra precisa para executar.',
    imagem: '/portfolio/02-reforma-fossa-filtro.jpg',
    alt: 'Modelo Revit de reforma de banheiro com detalhamento de fossa séptica e filtro anaeróbio',
    specs: [],
  },
]

export const processo = [
  {
    numero: '01',
    titulo: 'Modelagem em Revit',
    texto: 'Transformo seu projeto em um modelo 3D hidrossanitário preciso.',
  },
  {
    numero: '02',
    titulo: 'Compatibilização BIM',
    texto: 'Resolvo interferências com estrutura e arquitetura antes da obra.',
  },
  {
    numero: '03',
    titulo: 'Entrega Nativa',
    texto:
      'Entrego o arquivo em Revit (.rvt) pronto para o RT do seu escritório assinar e aprovar.',
  },
]
