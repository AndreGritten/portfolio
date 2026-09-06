/*
 * O brilho que segue o cursor pelos textos da página.
 *
 * O desenho é todo do CSS (`.texto-brilho`, no input.css): um gradiente
 * radial recortado no texto, com a cor de repouso vinda do background-color
 * atrás dele. Este arquivo só informa ONDE está o ponteiro e QUANTO o efeito
 * deve estar aceso, escrevendo três variáveis por elemento.
 *
 * COMEÇOU SÓ NO NOME e cresceu para os títulos. A generalização é barata
 * porque o custo não está no número de elementos marcados, e sim em quantos
 * estão VISÍVEIS: um IntersectionObserver mantém a lista ativa, e só ela é
 * percorrida a cada quadro. Uma página com cinquenta títulos paga por dois
 * ou três de cada vez.
 *
 * POR QUE NÃO NO campo.js — que já escuta o mouse: o campo se REMOVE inteiro
 * abaixo de 768px de largura, com um `return` antes de registrar qualquer
 * listener. Pendurar o brilho nele mataria o efeito em toda janela mais
 * estreita que isso, inclusive num desktop redimensionado, que tem mouse e
 * merece o efeito. Os portões são genuinamente diferentes: o campo corta por
 * LARGURA (um canvas custa memória), o brilho corta por PONTEIRO.
 *
 * A classe é marcada aqui, e não no HTML, pelo mesmo motivo do movimento.js:
 * é o que garante que sem JavaScript o texto nasça na cor certa em vez de
 * transparente — `color: transparent` sem o gradiente é texto invisível, e
 * esse é o único jeito de errar feio neste efeito.
 */

(function () {
  'use strict'

  var alvos = document.querySelectorAll('[data-brilho]')
  if (!alvos.length) return

  /* A mesma classe que o movimento.js marca em <html>. Quem pediu movimento
     reduzido não recebe o efeito — e como a classe do brilho só é ligada
     abaixo, os textos ficam na cor sólida. */
  if (!document.documentElement.classList.contains('movimento')) return

  /* Sem ponteiro fino não há o que seguir: num toque o `mousemove` só
     chegaria no tap, deixando o brilho aceso e parado onde o dedo encostou. */
  if (!(window.matchMedia && window.matchMedia('(pointer: fine)').matches)) {
    return
  }

  /* A MARGEM DE APROXIMAÇÃO, em px.
   *
   * O listener vive na JANELA, e não em cada elemento, e é isso que faz o
   * brilho responder ao cursor PERTO do texto em vez de só em cima dele.
   * Preso ao elemento, o mousemove só chegava dentro da caixa — e como a
   * caixa de um título é justa, era preciso encostar na letra.
   *
   * Fora da caixa o ponto é PROJETADO na borda mais próxima, e a intensidade
   * cai com a distância até zerar aqui. */
  var MARGEM = 160

  var itens = []
  Array.prototype.forEach.call(alvos, function (el) {
    el.classList.add('texto-brilho')
    itens.push({ el: el, forca: 0, visivel: false, aceso: false })
  })

  /* Só os elementos na tela entram no laço.
   *
   * Sem isto, cada quadro leria a caixa de todos os títulos da página —
   * inclusive os que estão a três seções de distância e nunca poderiam
   * estar sob o cursor. Com o observador, o laço percorre os dois ou três
   * que realmente cabem na janela. */
  if ('IntersectionObserver' in window) {
    var observador = new IntersectionObserver(
      function (entradas) {
        entradas.forEach(function (entrada) {
          for (var i = 0; i < itens.length; i++) {
            if (itens[i].el === entrada.target) {
              itens[i].visivel = entrada.isIntersecting
              break
            }
          }
        })
      },
      /* A margem generosa evita que um título entre em cena já devendo
         brilho: ele começa a ser observado antes de aparecer. */
      { rootMargin: '200px' }
    )
    itens.forEach(function (item) {
      observador.observe(item.el)
    })
  } else {
    itens.forEach(function (item) {
      item.visivel = true
    })
  }

  var mouseX = -99999
  var mouseY = -99999
  var agendado = false

  function aplicar() {
    agendado = false

    for (var i = 0; i < itens.length; i++) {
      var item = itens[i]

      if (!item.visivel) {
        /* Fora da tela: apaga uma vez e para de tocar no estilo. Sem a
           trava `aceso`, este ramo reescreveria as mesmas variáveis a cada
           quadro para todo elemento fora de vista. */
        if (item.aceso) {
          item.el.style.setProperty('--forca', 0)
          item.el.style.setProperty('--mx', '-9999px')
          item.aceso = false
        }
        continue
      }

      var caixa = item.el.getBoundingClientRect()

      /* A distância até a CAIXA: zero quando o cursor está dentro dela, e o
         afastamento em cada eixo quando está fora. Medir contra a caixa, e
         não contra o centro, é o que mantém o comportamento igual ao longo
         de um título largo — contra o centro, a ponta precisaria de um
         cursor muito mais perto que o meio. */
      var dx = Math.max(caixa.left - mouseX, 0, mouseX - caixa.right)
      var dy = Math.max(caixa.top - mouseY, 0, mouseY - caixa.bottom)
      var distancia = Math.sqrt(dx * dx + dy * dy)

      if (distancia > MARGEM) {
        if (item.aceso) {
          item.el.style.setProperty('--forca', 0)
          item.el.style.setProperty('--mx', '-9999px')
          item.aceso = false
        }
        continue
      }

      /* Dentro da caixa a força é cheia; fora, decai até zerar na margem. O
         quadrado faz a queda ser suave perto do texto e rápida longe dele,
         que é como uma luz real se comporta. */
      var t = 1 - distancia / MARGEM
      item.el.style.setProperty('--forca', t * t)

      /* Projetado na caixa: o brilho nasce na borda mais próxima do cursor,
         e não num ponto solto fora do texto. */
      item.el.style.setProperty(
        '--mx',
        Math.min(Math.max(mouseX - caixa.left, 0), caixa.width) + 'px'
      )
      item.el.style.setProperty(
        '--my',
        Math.min(Math.max(mouseY - caixa.top, 0), caixa.height) + 'px'
      )
      item.aceso = true
    }
  }

  window.addEventListener(
    'mousemove',
    function (evento) {
      mouseX = evento.clientX
      mouseY = evento.clientY

      /* Escrever no rAF, e não aqui: o mousemove dispara mais de uma vez por
         quadro, e cada `setProperty` sujaria o estilo à toa. */
      if (!agendado) {
        agendado = true
        requestAnimationFrame(aplicar)
      }
    },
    { passive: true }
  )

  /* O ponteiro saiu da janela: apaga tudo, em vez de deixar o último título
     congelado aceso. */
  document.addEventListener('mouseleave', function () {
    mouseX = -99999
    mouseY = -99999
    if (!agendado) {
      agendado = true
      requestAnimationFrame(aplicar)
    }
  })
})()
