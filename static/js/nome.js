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

  var x = 0
  var y = 0
  var agendado = false

  function aplicar() {
    agendado = false
    alvo.style.setProperty('--mx', x + 'px')
    alvo.style.setProperty('--my', y + 'px')
  }

  alvo.addEventListener(
    'mousemove',
    function (evento) {
      /* A caixa é lida a cada evento de propósito. O Lenis rola a página com
         transform, então um valor guardado ficaria velho no meio de uma
         rolagem e o brilho apareceria deslocado do cursor. É uma leitura de
         layout de um elemento só — barata o bastante para não valer o cache
         e a invalidação que ele exigiria. */
      var caixa = alvo.getBoundingClientRect()
      x = evento.clientX - caixa.left
      y = evento.clientY - caixa.top

      /* Escrever no rAF, e não aqui: o mousemove dispara mais de uma vez por
         quadro, e cada `setProperty` sujaria o estilo à toa. */
      if (!agendado) {
        agendado = true
        requestAnimationFrame(aplicar)
      }
    },
    { passive: true }
  )

  /* Ao sair, o foco volta para fora da tela — sem isto o brilho ficaria
     congelado na última posição do ponteiro, como uma mancha. */
  alvo.addEventListener(
    'mouseleave',
    function () {
      alvo.style.setProperty('--mx', '-9999px')
    },
    { passive: true }
  )
})()
