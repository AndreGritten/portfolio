/*
 * O cursor da página.
 *
 * Duas peças que se movem em velocidades diferentes, e a diferença entre
 * elas é o efeito inteiro:
 *
 *   O PONTO é exato. Fica na posição real do ponteiro, sem atraso nenhum —
 *   é ele que diz onde o clique vai cair, e um alvo que arrasta é um alvo
 *   que erra.
 *
 *   O ANEL persegue com inércia. É o que dá peso ao movimento: o ponto
 *   chega, o anel alcança. Sobre algo clicável ele ABRE e ganha o carmim;
 *   no resto da página fica pequeno e discreto.
 *
 * A separação importa: um cursor inteiro com atraso parece quebrado, e um
 * cursor inteiro sem atraso não tem graça. Atrasar só o anel dá a sensação
 * de material sem custar precisão.
 *
 * O ACOPLAMENTO COM O CAMPO: este arquivo publica a intensidade corrente em
 * `window.__cursorForca`, e o campo.js soma esse valor ao acender os nós da
 * treliça. Sobre um link, o cursor abre E o desenho de fundo responde junto,
 * como se a mesma luz atingisse os dois. Sem este arquivo carregado a
 * variável não existe, e o campo usa o próprio comportamento de sempre — o
 * acoplamento é opcional dos dois lados, de propósito.
 */

(function () {
  'use strict'

  /* Os mesmos portões do campo.js e do nome.js. Sem ponteiro fino não há
     cursor para substituir, e esconder o nativo deixaria a página sem
     cursor nenhum — o pior resultado possível. */
  if (!document.documentElement.classList.contains('movimento')) return
  if (!(window.matchMedia && window.matchMedia('(pointer: fine)').matches)) {
    return
  }

  /* Ponteiro grosso ou tela de toque não chegam aqui, mas um mouse ligado
     depois do carregamento sim. Não há o que fazer a respeito sem um
     listener permanente; o caso é raro e o nativo continua disponível. */

  var ponto = document.createElement('div')
  ponto.className = 'cursor-ponto'
  ponto.setAttribute('aria-hidden', 'true')

  var anel = document.createElement('div')
  anel.className = 'cursor-anel'
  anel.setAttribute('aria-hidden', 'true')

  document.body.appendChild(ponto)
  document.body.appendChild(anel)

  /* A classe no <html> é o que esconde o cursor nativo, e ela só entra
     DEPOIS de os elementos existirem. Marcá-la no CSS direto deixaria a
     página sem cursor no intervalo entre a pintura e este script. */
  document.documentElement.classList.add('cursor-proprio')

  var alvoX = window.innerWidth / 2
  var alvoY = window.innerHeight / 2
  var anelX = alvoX
  var anelY = alvoY

  /* 0 em repouso, 1 sobre algo clicável. O valor corrente persegue o alvo,
     que é o que faz o anel CRESCER em vez de saltar de tamanho. */
  var alvoForca = 0
  var forca = 0

  var LERP_ANEL = 0.18 /* ~90ms de constante de tempo a 60fps */
  var LERP_FORCA = 0.14

  /* Os dois diâmetros, em px. O anel é desenhado NESTE tamanho — não há
     escala envolvida, justamente para a borda não borrar (ver `quadro`). */
  var TAMANHO_ANEL = 30
  var TAMANHO_ANEL_ABERTO = 58

  var rodando = false
  var dentro = false

  /* O mesmo seletor de "clicável" das regras de cursor no input.css. Se um
     dos dois mudar, o outro precisa acompanhar — é a única duplicação que
     este efeito tem, e ela existe porque o CSS não sabe consultar o JS. */
  var CLICAVEL =
    'a[href], button, [role="button"], summary, label[for], select, ' +
    '.tag-filtro, input[type="submit"], input[type="button"]'

  function quadro() {
    anelX += (alvoX - anelX) * LERP_ANEL
    anelY += (alvoY - anelY) * LERP_ANEL
    forca += (alvoForca - forca) * LERP_FORCA

    ponto.style.transform =
      'translate3d(' + alvoX + 'px,' + alvoY + 'px,0) translate(-50%,-50%)'

    /* O TAMANHO VAI EM width/height, e NUNCA em scale().
     *
     * Com `scale()` o navegador amplia o bitmap já rasterizado do anel: uma
     * borda de 1,5px vira 3px BORRADOS, e o círculo ganha aquele contorno
     * chapado e sujo. Escrevendo a medida real, o anel é redesenhado no
     * tamanho novo a cada quadro e a borda continua com a mesma espessura
     * nítida, aberto ou fechado.
     *
     * O custo é um layout por quadro num elemento `position: fixed`, que
     * não participa do fluxo — barato, e o preço certo pela nitidez. */
    var d = TAMANHO_ANEL + forca * (TAMANHO_ANEL_ABERTO - TAMANHO_ANEL)
    anel.style.width = d + 'px'
    anel.style.height = d + 'px'
    anel.style.transform =
      'translate3d(' + anelX + 'px,' + anelY + 'px,0) translate(-50%,-50%)'
    anel.style.opacity = 0.35 + forca * 0.45

    /* O que o campo.js lê. Publicado a cada quadro para os dois efeitos
       nunca discordarem sobre o estado do cursor. */
    window.__cursorForca = forca

    /* O campo dorme quando estabiliza, e é o mousemove que o acorda. Mas o
       cursor pode abrir com o mouse PARADO — rolando a página, um link
       desliza para baixo do ponteiro. Sem este empurrão a treliça ficaria
       inerte enquanto o anel cresce. */
    if (window.__campoLigar) window.__campoLigar()

    /* Parar o laço quando nada mais se move: um rAF permanente custa bateria
       por um desenho parado. O limiar é o meio pixel — abaixo disso a
       diferença não é pintável. */
    var parado =
      Math.abs(alvoX - anelX) < 0.5 &&
      Math.abs(alvoY - anelY) < 0.5 &&
      Math.abs(alvoForca - forca) < 0.01

    if (parado) {
      rodando = false
      return
    }
    requestAnimationFrame(quadro)
  }

  function ligar() {
    if (rodando) return
    rodando = true
    requestAnimationFrame(quadro)
  }

  window.addEventListener(
    'mousemove',
    function (evento) {
      alvoX = evento.clientX
      alvoY = evento.clientY

      if (!dentro) {
        dentro = true
        /* Ao voltar para a janela o anel é teleportado para o ponteiro, em
           vez de atravessar a tela para alcançá-lo. */
        anelX = alvoX
        anelY = alvoY
        document.documentElement.classList.remove('cursor-fora')
      }

      var sob = evento.target
      alvoForca = sob && sob.closest && sob.closest(CLICAVEL) ? 1 : 0

      ligar()
    },
    { passive: true }
  )

  /* O ponteiro saiu da janela. Sem isto, as duas peças ficam paradas na
     borda como se o mouse ainda estivesse lá. */
  document.addEventListener('mouseleave', function () {
    dentro = false
    alvoForca = 0
    document.documentElement.classList.add('cursor-fora')
    ligar()
  })

  /* O clique dá um retorno tátil no anel: encolhe e volta. É a única
     animação em CSS aqui — o resto é transform escrito por quadro. */
  window.addEventListener(
    'mousedown',
    function () {
      anel.classList.add('cursor-anel-premido')
    },
    { passive: true }
  )
  window.addEventListener(
    'mouseup',
    function () {
      anel.classList.remove('cursor-anel-premido')
    },
    { passive: true }
  )
})()
