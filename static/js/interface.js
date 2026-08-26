/*
 * Componentes do Alpine e o realce da seção atual no menu.
 *
 * Registra tudo no evento `alpine:init`, por isso este arquivo vem ANTES do
 * alpine.min.js no base.html — os dois com defer, na ordem declarada.
 */

document.addEventListener('alpine:init', function () {
  /* ---------------------------------------------------------------------
   * Cabeçalho
   *
   * O estado vive num store, e não no componente, porque o menu deslizante é
   * IRMÃO do <header> no DOM — não filho. Os dois precisam ler o mesmo
   * `menuAberto` sem um contêiner entre eles.
   * ------------------------------------------------------------------- */
  Alpine.store('cabecalho', {
    rolou: false,
    menuAberto: false,

    alternarMenu() {
      this.menuAberto = !this.menuAberto
      this.travarRolagem()
    },

    fecharMenu() {
      this.menuAberto = false
      this.travarRolagem()
    },

    /* Sem isto, rolar dentro do menu aberto rola a página atrás dele — e ao
       fechar, a pessoa está num lugar que não escolheu. */
    travarRolagem() {
      document.body.style.overflow = this.menuAberto ? 'hidden' : ''
    },
  })

  /* O componente do <header> expõe UMA coisa: se ele está sólido. Tudo que
     mexe no menu fala com o store pelo nome completo, nos templates.
     Ter também um `alternarMenu` aqui criaria dois caminhos para a mesma
     ação, e o atalho só funcionaria em elementos sem `x-data` próprio — que
     foi exatamente como o menu do celular quebrou uma vez. */
  Alpine.data('cabecalho', function () {
    return {
      /* Sólido também com o menu aberto: sobre o topo transparente, o painel
         deslizante ficaria pendurado num cabeçalho invisível. */
      get solido() {
        return this.$store.cabecalho.rolou || this.$store.cabecalho.menuAberto
      },
    }
  })

  /* ---------------------------------------------------------------------
   * Filtro de projetos
   *
   * Roda no navegador: os cartões já chegam renderizados do servidor e o
   * filtro só decide quais mostrar. Recarregar a página para trocar de
   * tecnologia custaria uma viagem ao servidor e perderia a posição de
   * rolagem — numa lista que cabe inteira na memória, não há o que ganhar.
   * ------------------------------------------------------------------- */
  Alpine.data('filtroProjetos', function (lista) {
    return {
      ativo: 'todos',
      /* As tecnologias de cada projeto, na mesma ordem dos cartões. Vem do
         template. Ter a lista em memória é o que permite responder "sobrou
         alguma coisa?" sem inspecionar o DOM — perguntar ao DOM quais nós
         estão visíveis significa depender do formato exato que o `x-show`
         escreve no atributo `style`, e isso quebra na primeira mudança do
         Alpine. */
      lista: lista || [],

      selecionar(slug) {
        this.ativo = slug
        /* A esteira horizontal mede a largura do trilho, e esconder cartões
           muda essa largura. O narrativa.js escuta para remedir. */
        this.$dispatch('projetos:filtrados')
      },

      /* `data-tecnologias` é uma lista separada por espaço. O teste com
         espaços em volta evita que "sql" case dentro de "postgresql". */
      mostrar(slugs) {
        if (this.ativo === 'todos') return true
        return (' ' + slugs + ' ').indexOf(' ' + this.ativo + ' ') !== -1
      },

      /* Um filtro que esvazia a seção sem dizer nada parece um defeito. */
      get vazio() {
        var self = this
        return !this.lista.some(function (slugs) {
          return self.mostrar(slugs)
        })
      },
    }
  })

  /* ---------------------------------------------------------------------
   * Modal de certificado
   * ------------------------------------------------------------------- */
  Alpine.data('modal', function () {
    return {
      aberto: false,

      abrir() {
        this.aberto = true
        document.body.style.overflow = 'hidden'
        /* O foco precisa entrar no diálogo, senão o próximo Tab continua na
           página atrás dele. `$nextTick` espera o x-show pintar — um
           elemento com `display: none` não recebe foco. */
        this.$nextTick(() => {
          const alvo = this.$refs.dialogo
          if (alvo) alvo.focus()
        })
      },

      fechar() {
        this.aberto = false
        document.body.style.overflow = ''
        if (this.$refs.gatilho) this.$refs.gatilho.focus()
      },
    }
  })
})

/* -----------------------------------------------------------------------
 * Estado do cabeçalho ao rolar.
 *
 * Fora do Alpine porque é um listener de janela: registrá-lo dentro de um
 * componente o duplicaria a cada vez que o componente fosse recriado.
 * `passive: true` diz ao navegador que este listener nunca chama
 * preventDefault, o que o libera para rolar sem esperar o JavaScript.
 * --------------------------------------------------------------------- */
window.addEventListener(
  'scroll',
  function () {
    if (!window.Alpine || !Alpine.store('cabecalho')) return
    Alpine.store('cabecalho').rolou = window.scrollY > 24
  },
  { passive: true }
)

/* -----------------------------------------------------------------------
 * Seção atual em destaque no menu.
 *
 * IntersectionObserver, e não ScrollTrigger: isto precisa funcionar mesmo se
 * o GSAP não carregar, e é a única coisa da página que o navegador resolve
 * sozinho sem custo por quadro.
 *
 * `aria-current="true"` acompanha o realce visual — sem ele, quem usa leitor
 * de tela não tem como saber onde está.
 * --------------------------------------------------------------------- */
document.addEventListener('DOMContentLoaded', function () {
  var itens = Array.prototype.slice.call(document.querySelectorAll('.item-menu'))
  if (!itens.length || !('IntersectionObserver' in window)) return

  var porId = {}
  var secoes = []

  itens.forEach(function (item) {
    var id = (item.getAttribute('data-secao') || '').replace('#', '')
    var secao = id && document.getElementById(id)
    if (!secao) return
    porId[id] = item
    secoes.push(secao)
  })

  function realcar(id) {
    itens.forEach(function (item) {
      var ativo = item === porId[id]
      item.classList.toggle('text-osso', ativo)
      item.classList.toggle('text-secundaria', !ativo)
      if (ativo) {
        item.setAttribute('aria-current', 'true')
      } else {
        item.removeAttribute('aria-current')
      }
    })
  }

  var observador = new IntersectionObserver(
    function (entradas) {
      entradas.forEach(function (entrada) {
        if (entrada.isIntersecting) realcar(entrada.target.id)
      })
    },
    {
      /* A faixa fica no terço superior da tela: assim a seção "atual" é a
         que está sendo LIDA, não a que acabou de encostar na borda de baixo. */
      rootMargin: '-20% 0px -70% 0px',
      threshold: 0,
    }
  )

  secoes.forEach(function (secao) {
    observador.observe(secao)
  })
})
