/*
 * Marca <html class="movimento"> antes de qualquer pintura.
 *
 * É essa classe que faz `.revelar` nascer invisível, esperando o
 * ScrollTrigger. Escondê-los só quando o JavaScript está de fato comandando
 * é o que garante a degradação: com JS desligado, com este script falhando ou
 * com movimento reduzido, ninguém marca nada e todo o conteúdo nasce visível.
 *
 * Carregado SEM `defer` (templates/base.html), e é a única exceção à regra de
 * defer do projeto: com defer, a página apareceria por um instante com tudo
 * visível e só depois esconderia — uma piscada em cima da primeira coisa que
 * se vê. O arquivo não toca o DOM além do elemento <html>, que já existe
 * quando esta linha roda.
 */

(function () {
  'use strict'

  var reduzido =
    window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  if (!reduzido) {
    document.documentElement.classList.add('movimento')
  }
})()
