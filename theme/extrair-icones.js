/*
 * Extrai de `lucide-static` o SVG de cada ícone usado nos templates e grava
 * apps/core/icones.json.
 *
 * Uso (a partir da raiz do repositório):
 *   npm run icones
 *
 * O JSON gerado é versionado, então renderizar um ícone não depende de Node.
 * Só é preciso rodar de novo quando um ícone novo entrar na lista abaixo.
 *
 * Por que `lucide-static` e não `lucide-react`: o pacote React exigiria
 * instalar react + react-dom só para renderizar SVG em tempo de build. O
 * `lucide-static` entrega os mesmos desenhos como arquivos .svg prontos, e o
 * nome do arquivo já é o nome-com-hífen que a classe `lucide-<nome>` usa.
 */

const fs = require('fs')
const path = require('path')

const raiz = path.resolve(__dirname, '..')
const pastaSvg = path.join(raiz, 'node_modules', 'lucide-static', 'icons')

// Nome em PascalCase (como se escreve no template) -> arquivo em kebab-case.
//
// Alguns nomes do lucide mudaram e o pacote mantém os dois arquivos; onde o
// nome que o template usa não é a tradução direta, o alvo vai escrito à mão
// para o SVG sair com a classe certa.
const ICONES = {
  // Identidade e contato
  Github: 'github',
  Linkedin: 'linkedin',
  Mail: 'mail',
  Phone: 'phone',
  MapPin: 'map-pin',
  Send: 'send',

  // Navegação e ações
  Menu: 'menu',
  X: 'x',
  ArrowRight: 'arrow-right',
  ArrowUpRight: 'arrow-up-right',
  ChevronRight: 'chevron-right',
  ChevronDown: 'chevron-down',
  Download: 'download',
  ExternalLink: 'external-link',
  Filter: 'filter',
  Link: 'link',

  // Trajetória e certificações
  Briefcase: 'briefcase',
  GraduationCap: 'graduation-cap',
  Award: 'award',
  Calendar: 'calendar',
  Clock: 'clock',
  Building2: 'building-2',
  FileText: 'file-text',
  Star: 'star',

  // Habilidades técnicas, uma por categoria
  Code2: 'code-xml',        // renomeado: Code2 -> code-xml
  Database: 'database',
  Layers: 'layers',
  Terminal: 'terminal',

  // Estados de formulário
  Check: 'check',
  CheckCircle: 'circle-check-big',   // renomeado: CheckCircle -> circle-check-big
  AlertCircle: 'circle-alert',       // renomeado: AlertCircle -> circle-alert
  Info: 'info',
}

if (!fs.existsSync(pastaSvg)) {
  console.error(
    'lucide-static não encontrado em node_modules/.\n' +
    'Rode `npm install` antes de `npm run icones`.'
  )
  process.exit(1)
}

const saida = {}
const faltando = []

for (const [nome, arquivo] of Object.entries(ICONES)) {
  const caminho = path.join(pastaSvg, `${arquivo}.svg`)

  if (!fs.existsSync(caminho)) {
    faltando.push(`${nome} (procurado como ${arquivo}.svg)`)
    continue
  }

  const svg = fs.readFileSync(caminho, 'utf8')

  // Só o miolo: os <path>, <circle>, <line>. O <svg> de fora é montado pela
  // templatetag, que é quem sabe o tamanho e a classe de cada uso.
  const interno = svg
    .replace(/^[\s\S]*?<svg[^>]*>/, '')
    .replace(/<\/svg>\s*$/, '')
    .replace(/\s+/g, ' ')
    .trim()

  saida[nome] = { classe: arquivo, interno }
}

if (faltando.length) {
  console.error('Ícones não encontrados em lucide-static:\n  ' + faltando.join('\n  '))
  process.exit(1)
}

const destino = path.join(raiz, 'apps', 'core', 'icones.json')
fs.writeFileSync(destino, JSON.stringify(saida, null, 2) + '\n', 'utf8')
console.log(`${Object.keys(saida).length} ícones extraídos para ${path.relative(raiz, destino)}`)
