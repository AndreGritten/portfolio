// Tema do portfólio de André Gritten — Ônix & Carmim.
//
// A paleta e a tipografia estão especificadas e medidas em
// https://claude.ai/code/artifact/1ad93ee9-1dfb-473b-90d5-df49b25847d6
// e conferidas por `python tools/conferir_cores.py`, que reprova se algum par
// cair abaixo do piso. Mudar um valor aqui sem rodar o conferidor é como
// mudar um cálculo sem refazer a conta.
//
// Uso:
//   npm run css        (uma vez)
//   npm run css:watch  (enquanto se mexe no layout)
//
// O CSS gerado é versionado, então quem clona o repositório não precisa de
// Node para rodar o site.

const path = require('path')

const raiz = path.resolve(__dirname, '..')

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    path.join(raiz, 'templates/**/*.html'),
    path.join(raiz, 'apps/**/*.py'),
    path.join(raiz, 'static/js/**/*.js'),
  ],

  // Rede de segurança: classes que só existem dentro de expressões
  // JavaScript — alternadas em tempo de execução pelo `:class` do Alpine ou
  // montadas pelo GSAP — escapam do scanner, que lê texto e não executa nada.
  safelist: [
    'translate-x-0', 'translate-x-full', '-translate-x-full',
    'opacity-0', 'opacity-100',
    'pointer-events-none', 'pointer-events-auto',
    'hidden', 'flex', 'grid',
    // Estados do filtro de projetos e das mensagens de erro montadas em JS.
    'tag-ativa', 'input-erro', 'erro-campo',
    // Tamanhos do monograma: o partial compõe `monograma-{{ tamanho }}`, então
    // o scanner nunca vê o nome inteiro.
    'monograma-sm', 'monograma-md', 'monograma-lg',
  ],

  theme: {
    extend: {
      colors: {
        // ===================================================================
        // A RAMPA
        //
        // São VARIÁVEIS, e não hexadecimais, por dois motivos concretos:
        //
        // 1. `<alpha-value>` é o que mantém `bg-onix/85` e `border-osso/10`
        //    funcionando. Com hexadecimal fixo, cada variante de opacidade
        //    exigiria uma entrada própria.
        // 2. Trocar a rampa inteira (um tema alternativo, um ajuste de matiz)
        //    passa a ser sete linhas de CSS em vez de sobrescrever cada
        //    utilidade uma a uma — bg-, text-, border-, from-, via-, to-,
        //    ring-, e toda variante de opacidade de cada uma.
        //
        // Os valores vivem em theme/input.css, como canais RGB separados por
        // espaço.
        // ===================================================================

        // Superfícies, do mais fundo ao mais claro.
        'onix':  'rgb(var(--onix) / <alpha-value>)',
        'breu':  'rgb(var(--breu) / <alpha-value>)',
        'fundo': 'rgb(var(--fundo) / <alpha-value>)',

        // Fios. Os dois existem separados porque têm exigências diferentes de
        // contraste: `borda` só separa (não precisa passar em nada), enquanto
        // `borda-forte` delimita um CONTROLE e precisa de 3:1 — ver a regra 4
        // em theme/input.css.
        'borda':       'rgb(var(--borda) / <alpha-value>)',
        'borda-forte': 'rgb(var(--borda-forte) / <alpha-value>)',

        // O acento, em dois papéis que a medição separou. `carmim` NUNCA é
        // texto (2,94:1 sobre o fundo dos cartões); `carmim-claro` é o que se
        // lê (4,76:1 na pior superfície).
        'carmim':       'rgb(var(--carmim) / <alpha-value>)',
        'carmim-claro': 'rgb(var(--carmim-claro) / <alpha-value>)',

        // Tinta.
        'osso':       'rgb(var(--osso) / <alpha-value>)',
        'secundaria': 'rgb(var(--secundaria) / <alpha-value>)',

        // Estados. Nenhum é usado sozinho: mensagem de erro leva ícone e
        // borda de 2px, porque o erro é vermelho e o acento da marca também.
        'erro':    'rgb(var(--erro) / <alpha-value>)',
        'aviso':   'rgb(var(--aviso) / <alpha-value>)',
        'sucesso': 'rgb(var(--sucesso) / <alpha-value>)',
        'info':    'rgb(var(--info) / <alpha-value>)',
      },

      fontFamily: {
        // Bricolage Grotesque tem eixo óptico (opsz): nos tamanhos grandes ela
        // fecha o espacejamento e mostra os detalhes que dão personalidade;
        // nos pequenos, abre e fica legível. `font-optical-sizing: auto` no
        // input.css é o que liga isso.
        display: ['Bricolage Grotesque', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        sans: ['Instrument Sans', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Consolas', 'monospace'],
      },

      // Uma escada de espaçamento vertical entre seções, para o ritmo da
      // página não virar um número solto por template.
      spacing: {
        'secao': '7rem',
        'secao-lg': '10rem',
      },

      keyframes: {
        aparecer: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        subir: {
          '0%': { transform: 'translateY(14px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        crescer: {
          '0%': { transform: 'scale(.96)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
      animation: {
        aparecer: 'aparecer .3s ease-in-out',
        subir: 'subir .35s ease-out',
        crescer: 'crescer .15s ease-out',
      },
    },
  },

  plugins: [],
}
