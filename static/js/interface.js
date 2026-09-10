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

  /* ---------------------------------------------------------------------
   * As duas faces do site.
   *
   * O topo tem dois botões: "Desenvolvedor de Software Web" (a face técnica,
   * em carmim) e "Conheça o André fora da sua área" (as atividades de
   * representação, clubes e MUN, em azul). Este store guarda qual está
   * valendo.
   *
   * É um STORE e não um `Alpine.data`, pela mesma razão do `cabecalho`: quem
   * lê o estado são elementos IRMÃOS no DOM — o <header> e o <main> —, sem um
   * contêiner comum onde um `x-data` pudesse morar sem envolver a página
   * inteira.
   *
   * AS DUAS FACES CONVIVEM NO HTML, e só a visibilidade muda. Não é
   * desperdício: o narrativa.js monta os ScrollTriggers UMA vez, no
   * arranque, e não tem API de reinicialização. Conteúdo inserido depois
   * ficaria sem gatilho nenhum — e como `html.movimento` deixa todo
   * `.revelar` em opacidade 0, a face nova entraria PERMANENTEMENTE
   * INVISÍVEL. Com as duas no DOM desde o primeiro paint, os gatilhos das
   * duas nascem juntos e a troca só alterna `display`.
   * ------------------------------------------------------------------- */
  Alpine.store('faces', {
    atual: 'dev',

    /* Vira `true` no primeiro clique e nunca mais volta.
     *
     * É o que desliga o halo pulsante da aba não escolhida e o rótulo
     * "escolha por onde começar": os dois existem para avisar que as abas
     * TROCAM a página, e depois que a pessoa trocou uma vez o aviso já
     * cumpriu o papel. Continuar pulsando ali seria ruído permanente no
     * primeiro elemento da tela. */
    jaTrocou: false,

    ehAtual(qual) {
      return this.atual === qual
    },

    trocar(qual) {
      if (this.atual === qual) return
      this.atual = qual
      this.jaTrocou = true

      /* O <html> é quem carrega o tema: `html[data-tema="azul"]` troca
         `--carmim` e `--carmim-claro` (theme/input.css), e com isso toda
         utilidade do Tailwind que use o acento vira azul de uma vez — elas
         resolvem por variável, não por hexadecimal. Remover o atributo (em
         vez de pôr "carmim") devolve o `:root`, que já é a face técnica. */
      if (qual === 'fora') {
        document.documentElement.dataset.tema = 'azul'
      } else {
        delete document.documentElement.dataset.tema
      }

      /* A treliça de fundo lê a cor do CSS uma vez e guarda; sem avisar, ela
         seguiria vermelha num site azul. */
      if (window.__campoRepintar) window.__campoRepintar()

      /* O menu do cabeçalho aponta para as seções da face que está no ar, e
         quem estava destacado some junto com ela. */
      if (window.__recalcularMenu) window.__recalcularMenu()

      /* `Alpine.nextTick` e não `this.$nextTick`: as mágicas com `$` existem
         em componentes (`Alpine.data`), não em stores. Aqui é preciso esperar
         o Alpine aplicar os `x-show` — antes disso a face nova ainda mede
         zero, e medir zero é justamente o problema que a linha seguinte
         conserta. */
      Alpine.nextTick(function () {
        /* O PASSO CRÍTICO. Os gatilhos da face escondida foram criados quando
           ela media zero de altura, então todas as posições que eles guardam
           estão erradas. `refresh()` recalcula tudo com as medidas de agora —
           e funciona porque os gatilhos JÁ EXISTEM; o que não funcionaria
           seria criá-los para nós que acabaram de entrar no DOM. */
        if (window.ScrollTrigger) window.ScrollTrigger.refresh()

        /* Sem isto a pessoa troca de face e cai no meio da página nova, numa
           altura que só fazia sentido na anterior. */
        window.scrollTo({ top: 0, behavior: 'auto' })
      })
    },
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

  /* Um item de menu só conta se a face dele estiver no ar.
   *
   * As duas faces do site convivem no HTML (ver o store `faces`, acima), e
   * cada uma tem seu próprio menu. Sem esta checagem, o menu escondido também
   * receberia `aria-current` — e um leitor de tela anunciaria duas seções
   * atuais, uma delas de uma face que a pessoa nem está vendo.
   *
   * `offsetParent` é nulo para qualquer elemento com `display: none` em si ou
   * num ancestral, que é exatamente o que o `x-show` da face escondida
   * aplica. Vale para o menu do celular também, que fica fechado. */
  function estaVisivel(elemento) {
    return elemento.offsetParent !== null
  }

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
        if (!entrada.isIntersecting) return
        /* A seção pode estar na faixa e mesmo assim pertencer à face
           escondida: `display: none` não impede o observador de reportar uma
           interseção guardada de antes da troca. */
        if (!estaVisivel(entrada.target)) return
        realcar(entrada.target.id)
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

  /* Chamado pelo store `faces` ao trocar de face.
   *
   * Trocar de face leva o destaque junto: o item que estava aceso pertence ao
   * menu que acabou de sumir, e o menu que entrou nasce sem nenhum aceso até
   * a pessoa rolar o bastante para o observador disparar. Limpar tudo deixa o
   * estado honesto — nenhuma seção em destaque até que uma esteja de fato
   * sendo lida — em vez de deixar um realce órfão da face anterior. */
  window.__recalcularMenu = function () {
    realcar(null)
  }
})
