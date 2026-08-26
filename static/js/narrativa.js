/*
 * A narrativa da página: o que a rolagem conduz.
 *
 * Quatro coisas, e nenhuma delas é enfeite solto:
 *   1. Lenis dá inércia à rolagem, e é o que faz a página parecer uma peça só.
 *   2. Os blocos se revelam ao entrar na tela, em cascata.
 *   3. Os números do "Sobre" contam a partir do zero.
 *   4. A seção de projetos GRUDA enquanto os cartões correm na horizontal.
 *
 * Carregado só na home (templates/portfolio/home.html), com defer, depois do
 * gsap, do ScrollTrigger e do lenis.
 *
 * REGRA QUE MANDA EM TUDO: com `prefers-reduced-motion: reduce` este arquivo
 * não faz NADA. Não é delicadeza — é aritmética. Sem o scroll guiado que dá
 * sentido a elas, uma seção grudada vira uma tela parada que não responde à
 * roda, e os blocos escondidos esperam um gatilho que nunca dispara. O
 * `movimento.js` já não marcou a classe que os esconde, então o conteúdo está
 * visível e empilhado, que é a versão certa da página nesse caso.
 */

(function () {
  'use strict'

  var reduzido =
    window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  if (reduzido) return

  if (!window.gsap || !window.ScrollTrigger) {
    /* Sem GSAP não há revelação possível, e os elementos ficariam invisíveis
       para sempre. Tirar a classe devolve a página estática — pior que a
       animada, muito melhor que uma página em branco. */
    document.documentElement.classList.remove('movimento')
    return
  }

  gsap.registerPlugin(ScrollTrigger)

  /* =====================================================================
   * 1. Rolagem suave
   * ================================================================== */

  var lenis = null

  if (window.Lenis) {
    lenis = new Lenis({
      duration: 1.05,
      /* Curva exponencial: rápida no começo, longa no fim. É o que dá a
         sensação de peso sem atrasar a resposta ao gesto. */
      easing: function (t) {
        return Math.min(1, 1.001 - Math.pow(2, -10 * t))
      },
      /* O toque no celular fica NATIVO. A rolagem por inércia do sistema já
         é boa, e sobrepor a nossa a ela produz um atraso que o dedo sente. */
      smoothWheel: true,
      smoothTouch: false,
    })

    lenis.on('scroll', ScrollTrigger.update)

    /* E TAMBÉM no evento nativo, que não é redundância.
     *
     * O Lenis avisa o ScrollTrigger quando é ELE quem rola. Só que nem toda
     * rolagem passa por ele: o salto de âncora do próprio navegador, o
     * "localizar na página", End/Home e a restauração de posição ao voltar
     * são nativos. Nesses casos o ScrollTrigger não recebia nada, os
     * gatilhos nunca disparavam, e quem abrisse /#trajetoria direto via uma
     * PÁGINA PRETA — a seção certa na tela, com todo o conteúdo ainda em
     * opacidade zero esperando um aviso que não vinha.
     *
     * `ScrollTrigger.update` é idempotente: chamá-la duas vezes no mesmo
     * quadro não custa nada além da segunda comparação. */
    window.addEventListener('scroll', ScrollTrigger.update, { passive: true })

    /* O ticker do GSAP como relógio único. Dois requestAnimationFrame
       independentes — um do Lenis, outro do ScrollTrigger — leem posições de
       quadros diferentes, e o resultado é tremor nos elementos presos. */
    gsap.ticker.add(function (tempo) {
      lenis.raf(tempo * 1000)
    })
    gsap.ticker.lagSmoothing(0)
  }

  /* =====================================================================
   * 1b. Entrada por link de seção — ANTES de criar qualquer gatilho
   *
   * Alguém compartilha "meu portfólio, seção de projetos" e o endereço chega
   * com #projetos. O navegador salta sozinho enquanto analisa o documento,
   * muito antes deste arquivo rodar.
   *
   * A ORDEM aqui é a correção inteira, e ela custou uma página preta para
   * ser encontrada: o ScrollTrigger mede a posição de cada gatilho no
   * momento em que ele é CRIADO. Criando-os antes de acertar a rolagem, as
   * medidas saíam calculadas para o topo — e um elemento que já estava na
   * tela ficava com o gatilho lá embaixo, esperando uma rolagem que nunca
   * viria. O resultado era a seção certa visível e todo o conteúdo dela em
   * opacidade zero.
   *
   * Acertando a posição primeiro, os gatilhos nascem medindo o lugar certo,
   * e os que já foram passados disparam na própria criação.
   * ================================================================== */
  function posicionarNaAncora() {
    if (!window.location.hash) return

    var alvo
    try {
      alvo = document.querySelector(window.location.hash)
    } catch (erro) {
      // Um hash que não é seletor válido (#!/algo) não é um alvo nosso.
      return
    }
    if (!alvo) return

    if (lenis) {
      lenis.scrollTo(alvo, { offset: -80, immediate: true, force: true })
    } else {
      alvo.scrollIntoView()
    }
  }

  posicionarNaAncora()

  /* Âncoras clicadas. Com o Lenis ativo, o salto nativo do navegador o deixa
     fora de sincronia — ele continua achando que está onde estava. `scrollTo`
     do próprio Lenis mantém os dois no mesmo lugar.
     O deslocamento de 80px é a altura do cabeçalho fixo. */
  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    link.addEventListener('click', function (evento) {
      var alvo = document.querySelector(link.getAttribute('href'))
      if (!alvo) return
      evento.preventDefault()
      if (lenis) {
        lenis.scrollTo(alvo, { offset: -80 })
      } else {
        alvo.scrollIntoView({ behavior: 'smooth' })
      }
    })
  })

  /* =====================================================================
   * 2. Revelação
   *
   * Em cascata dentro de cada grupo `[data-revelar-grupo]`, e individual
   * fora dele. O agrupamento importa: seis cartões aparecendo juntos é um
   * salto; seis aparecendo com 80ms entre eles é um movimento.
   * ================================================================== */

  function revelar(elementos, gatilho) {
    gsap.to(elementos, {
      opacity: 1,
      y: 0,
      duration: 0.7,
      ease: 'power2.out',
      stagger: 0.08,
      scrollTrigger: {
        trigger: gatilho,
        /* "quando o topo do elemento chega a 85% da altura da tela" — ou
           seja, um pouco antes de entrar de fato, para o movimento terminar
           quando a pessoa olhar. */
        start: 'top 85%',
        once: true,
      },
    })
  }

  document.querySelectorAll('[data-revelar-grupo]').forEach(function (grupo) {
    var filhos = grupo.querySelectorAll('.revelar')
    if (filhos.length) revelar(filhos, grupo)
  })

  document.querySelectorAll('.revelar').forEach(function (elemento) {
    if (elemento.closest('[data-revelar-grupo]')) return
    revelar(elemento, elemento)
  })

  gsap.utils.toArray('.revelar-simples').forEach(function (elemento) {
    gsap.to(elemento, {
      opacity: 1,
      duration: 0.9,
      ease: 'power1.out',
      scrollTrigger: { trigger: elemento, start: 'top 90%', once: true },
    })
  })

  /* =====================================================================
   * 3. Contadores
   *
   * O alvo vem do `data-contador`, que o template preenche a partir do
   * banco — o número não é escrito à mão em lugar nenhum.
   * ================================================================== */

  document.querySelectorAll('[data-contador]').forEach(function (elemento) {
    var alvo = parseInt(elemento.getAttribute('data-contador'), 10)
    if (isNaN(alvo)) return

    var estado = { valor: 0 }

    gsap.to(estado, {
      valor: alvo,
      duration: 1.4,
      ease: 'power2.out',
      scrollTrigger: { trigger: elemento, start: 'top 88%', once: true },
      onUpdate: function () {
        elemento.textContent = Math.round(estado.valor)
      },
    })
  })

  /* =====================================================================
   * 4. Parallax do topo
   *
   * Deslocamento pequeno e em elementos DECORATIVOS apenas. Texto com
   * parallax se descola do que está em volta e fica difícil de ler durante
   * a rolagem.
   * ================================================================== */

  gsap.utils.toArray('[data-parallax]').forEach(function (elemento) {
    var forca = parseFloat(elemento.getAttribute('data-parallax')) || 0.2

    gsap.to(elemento, {
      yPercent: forca * 100,
      ease: 'none',
      scrollTrigger: {
        trigger: elemento.closest('section') || elemento,
        start: 'top top',
        end: 'bottom top',
        scrub: true,
      },
    })
  })

  /* =====================================================================
   * 5. A esteira horizontal dos projetos
   *
   * A seção gruda e os cartões correm de lado enquanto a rolagem continua.
   *
   * Só no desktop, e a razão é de espaço: num celular a esteira teria dois
   * cartões de largura e o efeito não se lê — vira uma seção travada sem
   * motivo aparente. Abaixo de 1024px os cartões viram uma grade comum.
   * ================================================================== */

  var esteira = document.querySelector('[data-esteira]')
  var trilho = document.querySelector('[data-trilho]')

  if (esteira && trilho) {
    var animacaoTrilho = null

    ScrollTrigger.matchMedia({
      '(min-width: 1024px)': function () {
        animacaoTrilho = gsap.to(trilho, {
          /* Funções, e não números: com `invalidateOnRefresh` elas são
             recalculadas a cada refresh. É o que faz o filtro de tecnologia
             funcionar aqui dentro — esconder cartões muda a largura do
             trilho, e um valor fixo deixaria a esteira parando cedo demais
             ou correndo no vazio. */
          x: function () {
            return -(trilho.scrollWidth - esteira.offsetWidth)
          },
          ease: 'none',
          scrollTrigger: {
            trigger: esteira,
            pin: true,
            scrub: 1,
            invalidateOnRefresh: true,
            end: function () {
              return '+=' + (trilho.scrollWidth - esteira.offsetWidth)
            },
          },
        })

        return function () {
          if (animacaoTrilho) {
            animacaoTrilho.scrollTrigger && animacaoTrilho.scrollTrigger.kill()
            animacaoTrilho.kill()
            gsap.set(trilho, { x: 0 })
            animacaoTrilho = null
          }
        }
      },
    })

    /* O filtro esconde cartões, e a largura do trilho muda com isso. Sem
       este refresh, a esteira continuaria calculada para a lista inteira e
       sobraria um vão vazio no fim. O evento é disparado pelo Alpine, em
       templates/portfolio/home.html. */
    document.addEventListener('projetos:filtrados', function () {
      /* Um quadro de espera: o `x-show` do Alpine ainda não tirou os cartões
         do fluxo quando o evento chega, e medir agora daria a largura velha. */
      requestAnimationFrame(function () {
        ScrollTrigger.refresh()
      })
    })
  }

  /* Depois que as fontes carregam, as alturas mudam — e todo gatilho medido
     antes disso está calculado sobre a métrica do fallback. */
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(function () {
      posicionarNaAncora()
      ScrollTrigger.refresh()
    })
  }

  /* =====================================================================
   * 6. A rede de segurança
   *
   * Nada acima pode deixar um bloco invisível para sempre, e a razão é o
   * tamanho da consequência: `.revelar` nasce em opacidade zero, então um
   * gatilho que não dispara não degrada a animação — apaga o conteúdo.
   *
   * Esta rede não substitui o ScrollTrigger; ela cobre o que ele não tem
   * como prever. Dois segundos depois da carga, tudo que já está DENTRO da
   * tela e continua invisível é revelado à força. Se a narrativa funcionou,
   * não sobra nada para ela fazer.
   * ================================================================== */
  setTimeout(function () {
    var atrasados = []

    document.querySelectorAll('.revelar, .revelar-simples').forEach(function (el) {
      if (parseFloat(getComputedStyle(el).opacity) > 0.01) return

      var caixa = el.getBoundingClientRect()
      var naTela = caixa.top < window.innerHeight && caixa.bottom > 0
      if (naTela) atrasados.push(el)
    })

    if (atrasados.length) {
      gsap.to(atrasados, { opacity: 1, y: 0, duration: 0.4, stagger: 0.04 })
    }
  }, 2000)
})()
