/*
 * Baixa as três famílias do Google Fonts para static/fonts/ e gera o
 * static/css/fontes.css com os @font-face correspondentes.
 *
 * Uso (a partir da raiz do repositório):
 *   npm run fontes
 *
 * Roda uma vez. Os .woff2 e o CSS gerado são versionados, e a partir daí o
 * site não faz nenhuma requisição a fonts.googleapis.com — nem no build, nem
 * em produção. Auto-hospedar não é só uma questão de privacidade: uma fonte
 * que depende de rede de terceiros é uma fonte que pode não chegar, e o
 * fallback silencioso desmancha a tipografia inteira sem avisar ninguém.
 *
 * As três famílias e os eixos pedidos:
 *   Bricolage Grotesque  variável (opsz 12..96, wght 200..800)  títulos
 *   Instrument Sans      variável (wght 400..700)               texto
 *   JetBrains Mono       variável (wght 100..800)               técnico
 */

const fs = require('fs')
const path = require('path')
const https = require('https')

const raiz = path.resolve(__dirname, '..')
const destinoFontes = path.join(raiz, 'static', 'fonts')
const destinoCss = path.join(raiz, 'static', 'css', 'fontes.css')

// O Google devolve woff2 variável só para navegadores que ele reconhece como
// capazes. Com o User-Agent padrão do Node ele entrega .ttf estático, e o
// arquivo fica cinco vezes maior.
const UA =
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
  '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'

const FAMILIAS = [
  {
    nome: 'Bricolage Grotesque',
    arquivo: 'bricolage-grotesque',
    consulta: 'Bricolage+Grotesque:opsz,wght@12..96,200..800',
  },
  {
    nome: 'Instrument Sans',
    arquivo: 'instrument-sans',
    consulta: 'Instrument+Sans:wght@400..700',
  },
  {
    nome: 'JetBrains Mono',
    arquivo: 'jetbrains-mono',
    consulta: 'JetBrains+Mono:wght@100..800',
  },
]

// Só os subconjuntos que o português usa. `latin` cobre os acentos do
// português (ã, ç, é, ô); `latin-ext` entra para nomes próprios estrangeiros
// que possam aparecer num título de projeto. Cirílico, grego e vietnamita
// ficam de fora — são metade do peso e nenhum caractere desta página.
const SUBCONJUNTOS = ['latin', 'latin-ext']

function buscar(url, binario = false) {
  return new Promise((resolve, reject) => {
    https
      .get(url, { headers: { 'User-Agent': UA } }, (res) => {
        if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          return resolve(buscar(res.headers.location, binario))
        }
        if (res.statusCode !== 200) {
          return reject(new Error(`HTTP ${res.statusCode} em ${url}`))
        }
        const pedacos = []
        res.on('data', (d) => pedacos.push(d))
        res.on('end', () =>
          resolve(binario ? Buffer.concat(pedacos) : Buffer.concat(pedacos).toString('utf8'))
        )
      })
      .on('error', reject)
  })
}

/* O CSS do Google vem como uma sequência de blocos, cada um precedido de um
   comentário com o nome do subconjunto:

     /* latin *​/
     @font-face { font-family: 'X'; ... src: url(...) format('woff2'); }

   Este parser lê os pares comentário + bloco e devolve só os que interessam. */
function fatiar(css) {
  const blocos = []
  const re = /\/\*\s*([a-z-]+)\s*\*\/\s*(@font-face\s*\{[^}]*\})/g
  let m
  while ((m = re.exec(css)) !== null) {
    blocos.push({ subconjunto: m[1], corpo: m[2] })
  }
  return blocos
}

async function principal() {
  fs.mkdirSync(destinoFontes, { recursive: true })

  const partes = [
    '/*',
    ' * GERADO por theme/baixar-fontes.js — não editar à mão.',
    ' *',
    ' * As três famílias do portfólio, auto-hospedadas. Rode `npm run fontes`',
    ' * para regerar. Carregado por templates/base.html ANTES do app.css.',
    ' */',
    '',
  ]

  for (const familia of FAMILIAS) {
    const url = `https://fonts.googleapis.com/css2?family=${familia.consulta}&display=swap`
    process.stdout.write(`${familia.nome}… `)

    const css = await buscar(url)
    const blocos = fatiar(css).filter((b) => SUBCONJUNTOS.includes(b.subconjunto))

    if (!blocos.length) {
      throw new Error(
        `Nenhum bloco @font-face para ${familia.nome}. ` +
        `O formato do CSS do Google mudou, ou a família não existe mais com esse nome.`
      )
    }

    for (const bloco of blocos) {
      const urlFonte = (bloco.corpo.match(/url\((https:[^)]+)\)/) || [])[1]
      if (!urlFonte) throw new Error(`Sem url() no bloco de ${familia.nome}`)

      const nomeArquivo = `${familia.arquivo}-${bloco.subconjunto}.woff2`
      const binario = await buscar(urlFonte, true)
      fs.writeFileSync(path.join(destinoFontes, nomeArquivo), binario)

      // Caminho relativo a static/css/, que é onde o CSS gerado mora.
      const corpo = bloco.corpo.replace(
        /url\(https:[^)]+\)/,
        `url('../fonts/${nomeArquivo}')`
      )

      partes.push(`/* ${familia.nome} — ${bloco.subconjunto} */`)
      partes.push(corpo.replace(/;\s*/g, ';\n  ').replace(/\{\s*/, ' {\n  ').replace(/\s*\}$/, '\n}'))
      partes.push('')

      process.stdout.write(`${bloco.subconjunto} (${Math.round(binario.length / 1024)}KB) `)
    }
    process.stdout.write('\n')
  }

  fs.mkdirSync(path.dirname(destinoCss), { recursive: true })
  fs.writeFileSync(destinoCss, partes.join('\n'), 'utf8')
  console.log(`\nGerado ${path.relative(raiz, destinoCss)}`)
}

principal().catch((erro) => {
  console.error('\nFalhou:', erro.message)
  process.exit(1)
})
