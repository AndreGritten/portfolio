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
 * Duas fontes, mesmo padrão de saída. `simple-icons` cobre a maioria — um
 * <path> só, viewBox 24x24, pronto para monocromático. `devicon` entra só
 * onde falta (ex. Java): os SVGs de lá vêm em MULTI-PATH e multicolor
 * (viewBox 128x128), então os `d` de cada <path> são concatenados num só
 * antes de gravar — a cor original de cada parte não importa, porque
 * `fill="currentColor"` sobrescreve todas mesmo assim; o que importa é a
 * FORMA completa (aqui, a xícara de café inteira, não só um pedaço dela).
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
  github: 'siGithub',
  pycharm: 'siPycharm',
  intellij: 'siIntellijidea',
  // "vs-code" fica de fora: o simple-icons não publica o logo do VS Code
  // (Microsoft não libera a marca para esse tipo de catálogo). A tag
  // aparece só com texto, como SQL, UML etc.
}

// slug de Tecnologia -> caminho do .svg dentro de node_modules/devicon.
// Só entra aqui o que falta no simple-icons — "java" não tem logo próprio
// lá (só "OpenJDK", que é uma coisa diferente: a implementação, não a
// linguagem). "-original" é a variante colorida oficial da marca; a forma é
// o que importa, a cor é substituída por currentColor de qualquer jeito.
const ICONES_DEVICON = {
  java: { arquivo: 'icons/java/java-original.svg', titulo: 'Java' },
}

const saida = {}
const faltando = []

for (const [slug, nomeIcone] of Object.entries(ICONES)) {
  if (!nomeIcone) continue

  const icone = si[nomeIcone]
  if (!icone) {
    faltando.push(`${slug} (procurado como ${nomeIcone} em simple-icons)`)
    continue
  }

  saida[slug] = { titulo: icone.title, path: icone.path, viewBox: '0 0 24 24' }
}

for (const [slug, { arquivo: arquivoRelativo, titulo }] of Object.entries(ICONES_DEVICON)) {
  const caminho = path.join(raiz, 'node_modules', 'devicon', arquivoRelativo)

  if (!fs.existsSync(caminho)) {
    faltando.push(`${slug} (procurado em node_modules/devicon/${arquivoRelativo})`)
    continue
  }

  const svg = fs.readFileSync(caminho, 'utf8')
  const viewBoxMatch = svg.match(/viewBox="([^"]+)"/)
  const pathsEncontrados = [...svg.matchAll(/<path[^>]*\sd="([^"]+)"/g)].map((m) => m[1])

  if (!viewBoxMatch || !pathsEncontrados.length) {
    faltando.push(`${slug} (svg do devicon sem viewBox ou sem <path> em ${arquivoRelativo})`)
    continue
  }

  saida[slug] = {
    titulo,
    path: pathsEncontrados.join(' '),
    viewBox: viewBoxMatch[1],
  }
}

if (faltando.length) {
  console.error('Ícones não encontrados:\n  ' + faltando.join('\n  '))
  process.exit(1)
}

const destino = path.join(raiz, 'apps', 'core', 'icones_marca.json')
fs.writeFileSync(destino, JSON.stringify(saida, null, 2) + '\n', 'utf8')
console.log(`${Object.keys(saida).length} ícones de marca extraídos para ${path.relative(raiz, destino)}`)
