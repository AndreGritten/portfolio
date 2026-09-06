/*
 * O brilho que segue o mouse sobre o nome, no topo.
 *
 * O desenho inteiro é do CSS (`.nome-brilho`, no input.css): um gradiente
 * radial recortado no texto, com a parada externa no mesmo osso do título.
 * Este arquivo só informa ONDE está o ponteiro, escrevendo duas variáveis.
 *
 * POR QUE UM ARQUIVO PRÓPRIO, e não um apêndice ao campo.js — que já escuta
 * o mouse: o campo se REMOVE inteiro abaixo de 768px de largura, com um
 * `return` antes de registrar qualquer listener. Pendurar o brilho nele
 * mataria o efeito em toda janela mais estreita que isso, inclusive num
 * desktop redimensionado, que tem mouse e merece o efeito. Os dois têm
 * portões genuinamente diferentes: o campo corta por LARGURA (um canvas
 * custa memória), o brilho corta por PONTEIRO (sem mouse não há o que
 * seguir).
 *
 * A classe é marcada aqui, e não no HTML, pelo mesmo motivo do movimento.js:
 * é o que garante que sem JavaScript o nome nasça na cor certa em vez de
 * transparente.
 */

(function () {
  'use strict'

  var alvo = document.querySelector('[data-nome-brilho]')
  if (!alvo) return

  /* A mesma classe que o movimento.js marca em <html>. Quem pediu movimento
     reduzido não recebe o efeito — e como a classe do brilho só é ligada
     abaixo, o nome fica em osso sólido. */
  if (!document.documentElement.classList.contains('movimento')) return

  /* Sem ponteiro fino não há o que seguir: num toque o `mousemove` só
     chegaria no tap, deixando o brilho aceso e parado onde o dedo encostou. */
  if (!(window.matchMedia && window.matchMedia('(pointer: fine)').matches)) {
    return
  }

  alvo.classList.add('nome-brilho')

  /* A MARGEM DE APROXIMAÇÃO, em px.
   *
   * O listener vive na JANELA, e não no <h1>, e é isso que faz o brilho
   * responder ao cursor PERTO do nome em vez de só em cima dele. Preso ao
   * elemento, o mousemove só chegava dentro da caixa do texto — e como a
   * caixa de um <h1> é justa, era preciso encostar na letra.
   *
   * Fora da caixa o ponto é PROJETADO na borda mais próxima, e a intensidade
   * cai com a distância até zerar aqui. O efeito é o de um facho que se
   * aproxima: a ponta do nome já acende um pouco antes de o cursor chegar. */
  var MARGEM = 160

  var x = 0
  var y = 0
  var forca = 0
  var agendado = false

  function aplicar() {
    agendado = false
    alvo.style.setProperty('--mx', x + 'px')
    alvo.style.setProperty('--my', y + 'px')
    /* A opacidade é o que traduz "perto, mas não em cima": o gradiente
       continua desenhado no mesmo lugar, só entra mais fraco. Sem isto, o
       ponto projetado na borda acenderia com força total assim que o cursor
       entrasse no raio, e o efeito pularia em vez de crescer. */
    alvo.style.setProperty('--forca', forca)
  }

  window.addEventListener(
    'mousemove',
    function (evento) {
      /* A caixa é lida a cada evento de propósito. O Lenis rola a página com
         transform, então um valor guardado ficaria velho no meio de uma
         rolagem e o brilho apareceria deslocado do cursor. É uma leitura de
         layout de um elemento só — barata o bastante para não valer o cache
         e a invalidação que ele exigiria. */
      var caixa = alvo.getBoundingClientRect()

      var px = evento.clientX - caixa.left
      var py = evento.clientY - caixa.top

      /* A distância até a caixa: zero quando o cursor está dentro dela, e o
         afastamento em cada eixo quando está fora. Medir contra a CAIXA, e
         não contra o centro, é o que mantém o comportamento igual ao longo
         de um título largo — contra o centro, a ponta do nome precisaria de
         um cursor muito mais perto que o meio. */
      var dx = Math.max(caixa.left - evento.clientX, 0, evento.clientX - caixa.right)
      var dy = Math.max(caixa.top - evento.clientY, 0, evento.clientY - caixa.bottom)
      var distancia = Math.sqrt(dx * dx + dy * dy)

      if (distancia > MARGEM) {
        /* Longe o bastante: apaga. O ponto vai para fora da tela para o
           gradiente não ficar pousado na borda do texto. */
        if (forca === 0) return
        forca = 0
        x = -9999
      } else {
        /* Dentro da caixa a força é cheia; fora, decai até zerar na margem.
           O quadrado faz a queda ser suave perto do nome e rápida longe
           dele, que é como uma luz real se comporta. */
        var t = 1 - distancia / MARGEM
        forca = t * t

        /* Projetado na caixa: o brilho nasce na borda mais próxima do
           cursor, e não num ponto solto fora do texto. */
        x = Math.min(Math.max(px, 0), caixa.width)
        y = Math.min(Math.max(py, 0), caixa.height)
      }

      /* Escrever no rAF, e não aqui: o mousemove dispara mais de uma vez por
         quadro, e cada `setProperty` sujaria o estilo à toa. */
      if (!agendado) {
        agendado = true
        requestAnimationFrame(aplicar)
      }
    },
    { passive: true }
  )
})()
