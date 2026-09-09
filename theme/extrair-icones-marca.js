/*
 * Extrai de `simple-icons` o path de cada logo de marca usado no quadro de
 * habilidades e grava apps/core/icones_marca.json.
 *
 * Uso (a partir da raiz do repositório):
 *   npm run icones:marca
 *
 * O JSON gerado é versionado, então renderizar um ícone não depende de Node.
 * Só é preciso rodar de novo quando uma tecnologia nova entrar na lista
 * abaixo.
 *
 * Por que `simple-icons` e não lucide: lucide é ícones de INTERFACE (seta,
 * lupa, envelope) — não tem logo de produto nenhum. Simple Icons é o
 * inverso: só logos de marca, um <path> por ícone, pensado para ser tingido
 * de uma cor só (`fill="currentColor"`) — o mesmo espírito do
 * `stroke="currentColor"` que a templatetag `icone` já usa para o lucide,
 * então o logo herda a cor do texto ao redor em vez de trazer a cor oficial
 * da marca (que quebraria a paleta do site).
 *
 * A CHAVE do JSON é o slug de `Tecnologia` (apps/portfolio/models.py) — é
 * assim que o template liga uma tag ao ícone, sem duplicar o nome em dois
 * lugares com grafias que podem divergir (ex. "PostgreSQL" vs "postgresql").
 */

const fs = require('fs')
const path = require('path')
const si = require('simple-icons')

const raiz = path.resolve(__dirname, '..')

// slug de Tecnologia -> nome do ícone no pacote simple-icons (siPython,
// siDjango, ...). Nem toda tecnologia do quadro tem logo — "Modelagem de
// dados", "Engenharia de Requisitos" e "UML" descrevem uma competência, não
// um produto, e ficam de fora de propósito: a tag aparece só com texto.
const ICONES = {
  python: 'siPython',
  django: 'siDjango',
  laravel: 'siLaravel',
  postgresql: 'siPostgresql',
  // "sql" e "etl" ficam de fora de propósito: SQL é uma linguagem, não um
  // produto com logo próprio, e usar o ícone de um SGBD específico (MySQL,
  // por exemplo) para representá-la seria impreciso — a tag não é sobre
  // aquele banco. ETL é um processo, não uma tecnologia com marca.
  javascript: 'siJavascript',
  html: 'siHtml5',
  css: 'siCss',
  git: 'siGit',
}

const saida = {}
const faltando = []

for (const [slug, nomeIcone] of Object.entries(ICONES)) {
  if (!nomeIcone) continue

  const icone = si[nomeIcone]
  if (!icone) {
    faltando.push(`${slug} (procurado como ${nomeIcone})`)
    continue
  }

  saida[slug] = { titulo: icone.title, path: icone.path }
}

if (faltando.length) {
  console.error('Ícones não encontrados em simple-icons:\n  ' + faltando.join('\n  '))
  process.exit(1)
}

const destino = path.join(raiz, 'apps', 'core', 'icones_marca.json')
fs.writeFileSync(destino, JSON.stringify(saida, null, 2) + '\n', 'utf8')
console.log(`${Object.keys(saida).length} ícones de marca extraídos para ${path.relative(raiz, destino)}`)
