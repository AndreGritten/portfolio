/*
 * O desenho do topo: um esquema de banco em arame, à deriva.
 *
 * Tabelas ligadas por relações em ângulo reto — o diagrama que existe atrás
 * de qualquer sistema que ele constrói. Não é enfeite genérico: é o assunto
 * da página desenhado.
 *
 * Sem asset externo: geometria por código. Se este script não rodar, o que
 * fica é o gradiente com a malha técnica — o topo nunca aparece vazio, e é
 * por isso que não existe imagem de reserva a manter.
 */

(function () {
  'use strict'

  var canvas = document.querySelector('[data-hero-canvas]')
  if (!canvas || !canvas.getContext) return

  var reduzido =
    window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  var ctx = canvas.getContext('2d')
  var largura = 0
  var altura = 0
  var dpr = 1

  var CARMIM = '229, 86, 107'
  var OSSO = '242, 237, 230'

  /* As tabelas, em coordenadas RELATIVAS (0 a 1). Assim o desenho reflui em
     qualquer proporção de tela sem recalcular a composição — a alternativa
     seria um layout em pixels que quebra no primeiro celular. */
  var TABELAS = [
    { x: 0.08, y: 0.24, l: 0.17, linhas: 4, acento: true },
    { x: 0.36, y: 0.12, l: 0.15, linhas: 3, acento: false },
    { x: 0.63, y: 0.30, l: 0.18, linhas: 5, acento: false },
    { x: 0.31, y: 0.58, l: 0.16, linhas: 3, acento: true },
    { x: 0.78, y: 0.68, l: 0.14, linhas: 2, acento: false },
    { x: 0.06, y: 0.72, l: 0.13, linhas: 2, acento: false },
  ]

  /* Quem se liga a quem, por índice. */
  var RELACOES = [
    [0, 1], [1, 2], [0, 3], [3, 2], [3, 5], [2, 4],
  ]

  var ALTURA_LINHA = 11
  var ALTURA_CABECALHO = 16

  function dimensionar() {
    dpr = Math.min(window.devicePixelRatio || 1, 2)
    var caixa = canvas.getBoundingClientRect()
    largura = caixa.width
    altura = caixa.height
    canvas.width = Math.round(largura * dpr)
    canvas.height = Math.round(altura * dpr)
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }

  function alturaTabela(tabela) {
    return ALTURA_CABECALHO + tabela.linhas * ALTURA_LINHA + 6
  }

  /* A deriva: cada tabela oscila num período próprio, tirado do índice. Como
     os períodos não são múltiplos, o conjunto nunca repete a mesma pose — o
     olho não encontra o laço. */
  function posicao(tabela, indice, t) {
    var fase = indice * 1.7
    return {
      x: tabela.x * largura + Math.sin(t * 0.00021 + fase) * 9,
      y: tabela.y * altura + Math.cos(t * 0.00017 + fase * 1.3) * 7,
      l: tabela.l * largura,
      a: alturaTabela(tabela),
    }
  }

  function retanguloArredondado(x, y, l, a, r) {
    ctx.beginPath()
    ctx.moveTo(x + r, y)
    ctx.arcTo(x + l, y, x + l, y + a, r)
    ctx.arcTo(x + l, y + a, x, y + a, r)
    ctx.arcTo(x, y + a, x, y, r)
    ctx.arcTo(x, y, x + l, y, r)
    ctx.closePath()
  }

  function desenhar(t) {
    ctx.clearRect(0, 0, largura, altura)

    var poses = TABELAS.map(function (tabela, i) {
      return posicao(tabela, i, t)
    })

    /* As relações primeiro, para passarem POR TRÁS das tabelas. */
    ctx.lineWidth = 1
    RELACOES.forEach(function (par) {
      var a = poses[par[0]]
      var b = poses[par[1]]

      var origemX = a.x + a.l
      var origemY = a.y + ALTURA_CABECALHO + 6
      var destinoX = b.x
      var destinoY = b.y + ALTURA_CABECALHO + 6
      var meio = (origemX + destinoX) / 2

      ctx.strokeStyle = 'rgba(' + OSSO + ', 0.20)'
      ctx.beginPath()
      ctx.moveTo(origemX, origemY)
      ctx.lineTo(meio, origemY)
      ctx.lineTo(meio, destinoY)
      ctx.lineTo(destinoX, destinoY)
      ctx.stroke()

      /* O pé-de-galinha da cardinalidade, na ponta que recebe. */
      ctx.beginPath()
      ctx.moveTo(destinoX - 6, destinoY - 4)
      ctx.lineTo(destinoX, destinoY)
      ctx.lineTo(destinoX - 6, destinoY + 4)
      ctx.stroke()
    })

    poses.forEach(function (pose, i) {
      var acento = TABELAS[i].acento

      /* Opacidades medidas na tela, não escolhidas no escuro: a 0,20 as
         tabelas sumiam sob o gradiente do topo e o desenho virava um ruído
         que ninguém identificava. A 0,30 elas se leem como esquema sem
         competir com o nome. */
      ctx.strokeStyle = acento
        ? 'rgba(' + CARMIM + ', 0.55)'
        : 'rgba(' + OSSO + ', 0.30)'
      ctx.lineWidth = 1

      retanguloArredondado(pose.x, pose.y, pose.l, pose.a, 4)
      ctx.stroke()

      /* Fio do cabeçalho. */
      ctx.beginPath()
      ctx.moveTo(pose.x, pose.y + ALTURA_CABECALHO)
      ctx.lineTo(pose.x + pose.l, pose.y + ALTURA_CABECALHO)
      ctx.stroke()

      /* As "colunas": traços de comprimento variável, como texto em maquete. */
      ctx.strokeStyle = acento
        ? 'rgba(' + CARMIM + ', 0.34)'
        : 'rgba(' + OSSO + ', 0.18)'

      for (var linha = 0; linha < TABELAS[i].linhas; linha++) {
        var y = pose.y + ALTURA_CABECALHO + 8 + linha * ALTURA_LINHA
        var comprimento = pose.l * (0.35 + ((linha * 7 + i * 3) % 10) / 22)
        ctx.beginPath()
        ctx.moveTo(pose.x + 8, y)
        ctx.lineTo(pose.x + 8 + comprimento, y)
        ctx.stroke()
      }
    })
  }

  var animando = false

  function quadro(t) {
    desenhar(t)
    if (animando) requestAnimationFrame(quadro)
  }

  dimensionar()

  if (reduzido) {
    /* Uma pose só, parada. O desenho continua existindo — o que sai é o
       movimento, que é exatamente o que foi pedido. */
    desenhar(0)
  } else {
    animando = true
    requestAnimationFrame(quadro)
  }

  canvas.classList.add('opacity-100')

  /* Redimensionar é caro: cada evento reconfigura o buffer do canvas. O
     debounce evita fazer isso sessenta vezes enquanto se arrasta a janela. */
  var temporizador = null
  window.addEventListener('resize', function () {
    clearTimeout(temporizador)
    temporizador = setTimeout(function () {
      dimensionar()
      if (reduzido) desenhar(0)
    }, 160)
  })
})()
