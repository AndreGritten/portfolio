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

  /* ---------------------------------------------------------------------
   * Modal de projeto: detalhes + vídeo, no MESMO escopo.
   *
   * Um `<li>` só aceita um `x-data` — por isso os dois diálogos do cartão
   * de projeto (a descrição longa e o vídeo de demonstração) vivem num
   * componente só, com dois booleanos independentes (`detalhesAberto`,
   * `videoAberto`) em vez de dois componentes separados brigando pelo
   * mesmo elemento. O botão "Ver vídeo" DE DENTRO do modal de detalhes
   * fecha um e abre o outro — por isso as duas ações moram juntas, e não
   * cada uma isolada como o `modal` genérico do certificado.
   *
   * PARAR DE TOCAR ao fechar o vídeo: um <iframe> do YouTube continua
   * rodando mesmo escondido atrás do `x-show` — `display: none` não pausa
   * mídia, só o esconde. A técnica é zerar o `src` do iframe ao fechar e
   * recolocá-lo ao abrir; não há API do player para "pausar de fora" um
   * iframe simples sem carregar o SDK do YouTube só para isto.
   * ------------------------------------------------------------------- */
  Alpine.data('modalProjeto', function (idYoutube) {
    return {
      detalhesAberto: false,
      videoAberto: false,
      idYoutube: idYoutube,

      abrirDetalhes() {
        this.detalhesAberto = true
        document.body.style.overflow = 'hidden'
        this.$nextTick(() => {
          if (this.$refs.dialogoDetalhes) this.$refs.dialogoDetalhes.focus()
        })
      },

      fecharDetalhes() {
        this.detalhesAberto = false
        // Só devolve a rolagem se o vídeo também não estiver aberto por
        // cima — trocar de modal (detalhes -> vídeo) não deve deixar a
        // página rolar por trás no instante entre um fechar e o outro abrir.
        if (!this.videoAberto) document.body.style.overflow = ''
        if (this.$refs.gatilhoDetalhes) this.$refs.gatilhoDetalhes.focus()
      },

      abrirVideo() {
        // Fecha o de detalhes por baixo: dois `fixed inset-0` empilhados
        // deixariam o primeiro clicável por trás do overlay do segundo.
        this.detalhesAberto = false
        this.videoAberto = true
        document.body.style.overflow = 'hidden'
        this.$nextTick(() => {
          if (this.$refs.dialogoVideo) this.$refs.dialogoVideo.focus()
        })
      },

      fecharVideo() {
        this.videoAberto = false
        document.body.style.overflow = ''
        // O foco volta para quem abriu o vídeo — o gatilho do cartão
        // quando havia descrição também (o vídeo foi aberto a partir do
        // modal de detalhes, já fechado), senão o botão "Ver vídeo" do
        // próprio cartão.
        const alvo = this.$refs.gatilhoDetalhes || this.$refs.gatilhoVideo
        if (alvo) alvo.focus()
      },

      /* O `src` do template chama isto em vez de escrever a URL direto,
         para a query string (autoplay, controles) morar num lugar só. */
      urlEmbed() {
        if (!this.videoAberto) return ''
        return (
          'https://www.youtube.com/embed/' +
          this.idYoutube +
          '?autoplay=1&rel=0'
        )
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
