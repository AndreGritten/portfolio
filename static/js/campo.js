/*
 * O campo: a malha viva atrás das seções que respiram.
 *
 * Nós geométricos numa treliça de 112px — o dobro do passo da
 * `.malha-tecnica` — ligados por traços em ângulo reto. Parado, o desenho
 * fica no mesmo peso da malha e praticamente não se enxerga. O movimento do
 * mouse é o que o revela.
 *
 * A REAÇÃO TEM DUAS CAMADAS, e a distinção é o que separa isto de um efeito
 * de cursor genérico:
 *
 *   1. A DERIVA é global. O campo inteiro translada no máximo 14px, num
 *      único `translate`. O mouse é CÂMERA, não holofote: nenhum elemento
 *      persegue o ponteiro, e é daí que vem a sensação de profundidade.
 *
 *   2. A REVELAÇÃO é por proximidade. Cada nó acende conforme a distância, e
 *      acima de um limiar desenha o traço até o vizinho de treliça. Como os
 *      traços seguem a grade, a região revelada tem contorno ESCALONADO —
 *      uma planta, não uma lanterna. É por isso que não vira um círculo.
 *
 * Sem asset externo e sem biblioteca: é desenho por código. Se este script
 * não rodar, o que fica é o degradê com a malha técnica, que já é o repouso
 * do desenho — por isso não existe imagem de reserva a manter.
 */

(function () {
  'use strict'

  var hospedeiros = document.querySelectorAll('[data-campo]')
  if (!hospedeiros.length) return

  /* =====================================================================
   * PORTÕES
   *
   * Lidos UMA vez, antes de qualquer alocação. Cada um tem uma razão
   * diferente e nenhum é decoração.
   * ================================================================== */

  var LARGURA_MINIMA = 768

  /* No celular o canvas é REMOVIDO, não pausado. Não existe cursor para
     revelar coisa alguma, então o efeito não teria o que fazer — e o que
     sobraria seria um buffer do tamanho da tela custando memória para pintar
     um desenho invisível. A `.malha-tecnica` continua lá, e ela já é o
     repouso. É o requisito do celular respondido pela subtração. */
  if (window.innerWidth < LARGURA_MINIMA) {
    Array.prototype.forEach.call(hospedeiros, function (tela) {
      var caixa = tela.closest('.campo')
      if (caixa) caixa.remove()
      else tela.remove()
    })
    return
  }

  /* A mesma classe que o movimento.js marca em <html>. Usá-la em vez de ler
     a media query de novo garante que o campo e a narrativa concordem: se um
     dos dois achar que pode animar e o outro não, a página fica pela metade. */
  var animar = document.documentElement.classList.contains('movimento')

  /* Ponteiro fino. Num tablet grande a media query de largura passa, mas não
     há mouse — o listener nunca receberia nada e o laço rodaria à toa. */
  var temMouse =
    window.matchMedia && window.matchMedia('(pointer: fine)').matches

  var reativo = animar && temMouse

  /* =====================================================================
   * A TRELIÇA
   * ================================================================== */

  var PASSO = 112 /* 2 × os 56px da malha: o ritmo rima sem fingir ser ela */

  /* O raio precisa cobrir três células para a revelação ter BORDA.
   *
   * Medido na tela: com 260px só uns seis nós entravam, e o que aparecia era
   * um retângulo limpo de 2×3 — legível, mas errado. O contorno escalonado
   * que justifica a grade só existe quando há nós suficientes para o limite
   * ficar irregular; com poucos, o olho fecha a forma num quadrado. */
  var RAIO = 330 /* alcance da revelação, em px */
  var DERIVA_MAX = 14 /* deslocamento máximo da câmera, em px */
  var LERP_CAMERA = 0.06 /* ~270ms de constante de tempo a 60fps */
  var LERP_NO = 0.09 /* um pouco mais rápido: a revelação arrasta, mas responde */
  var ALFA_REPOUSO = 0.05 /* o peso da malha — some quando se lê o texto */
  var ALFA_MAX = 0.3
  /* O limiar dos traços é BAIXO de propósito. Ele é o que decide até onde a
     ligação alcança, e portanto o tamanho do recorte. A 0,35 os traços
     morriam a 150px do cursor — uma célula e meia — e sobrava o retângulo.
     A 0,20 alcançam ~220px, o bastante para o limite ficar irregular. */
  var LIMIAR_TRACO = 0.2
  var LIMIAR_ACENTO = 0.55 /* o carmim só entra bem aceso */
  var PROPORCAO_MAXIMA = 2 /* retina sim, os 3× de um celular de topo não */

  /* Parada em repouso: enquanto o maior delta do quadro ficar abaixo disto,
     não há o que redesenhar. Sem a banda morta, a interpolação assintótica
     nunca chega ao alvo e o laço roda para sempre — que é exatamente o
     defeito do canvas que este arquivo substitui. */
  var EPSILON = 0.0015

  var CARMIM_CLARO = '229, 86, 107'
  var OSSO = '242, 237, 230'

  /* Forma e acento saem de um hash das coordenadas, não de Math.random():
     assim a composição é a MESMA a cada carga. Um fundo que se redesenha
     diferente a cada F5 lê como ruído, não como desenho. */
  function embaralhar(gx, gy) {
    var h = (gx * 374761393 + gy * 668265263) | 0
    h = (h ^ (h >>> 13)) * 1274126177
    return ((h ^ (h >>> 16)) >>> 0) / 4294967296
  }

  /* Curva suave nas duas pontas. Uma queda linear deixa uma borda visível no
     limite do raio — o olho encontra a circunferência e o efeito se denuncia. */
  function suavizar(t) {
    return t * t * (3 - 2 * t)
  }

  /* =====================================================================
   * ESTADO COMPARTILHADO
   *
   * O mouse é um par de floats do MUNDO, não de cada canvas: um listener só,
   * para quantos campos existirem na página.
   * ================================================================== */

  var mouseX = -99999
  var mouseY = -99999
  var temPonteiro = false

  var campos = []
  var rodando = false
  var quadro = null

  /* =====================================================================
   * UM CAMPO
   * ================================================================== */

  function criarCampo(tela) {
    var ctx = tela.getContext && tela.getContext('2d')
    if (!ctx) return null

    return {
      tela: tela,
      ctx: ctx,
      nos: [],
      colunas: 0,
      linhas: 0,
      largura: 0,
      altura: 0,
      /* Onde o canvas está na janela. Lido uma vez por quadro, ANTES de
         qualquer escrita — ver a nota no laço. */
      esquerda: 0,
      topo: 0,
      derivaX: 0,
      derivaY: 0,
      alvoDerivaX: 0,
      alvoDerivaY: 0,
      visivel: false,
      alocado: false,
    }
  }

  function medir(campo) {
    var caixa = campo.tela.getBoundingClientRect()
    campo.esquerda = caixa.left
    campo.topo = caixa.top
    return caixa
  }

  /* Aloca o buffer e monta os nós. Chamado ao entrar na tela, não na carga:
     um canvas do tamanho da janela em DPR 2 custa dezenas de MB, e não faz
     sentido manter três deles vivos quando só um está sendo visto. */
  function alocar(campo) {
    var caixa = medir(campo)
    if (!caixa.width || !caixa.height) return false

    var proporcao = Math.min(window.devicePixelRatio || 1, PROPORCAO_MAXIMA)

    campo.largura = caixa.width
    campo.altura = caixa.height
    campo.tela.width = Math.round(caixa.width * proporcao)
    campo.tela.height = Math.round(caixa.height * proporcao)
    campo.ctx.setTransform(proporcao, 0, 0, proporcao, 0, 0)

    montarNos(campo)
    campo.alocado = true
    return true
  }

  /* Devolve a memória. `width = 0` é o que de fato libera o buffer — apenas
     esconder o elemento mantém tudo alocado. */
  function liberar(campo) {
    campo.tela.width = 0
    campo.tela.height = 0
    campo.nos.length = 0
    campo.alocado = false
  }

  function montarNos(campo) {
    /* Uma folga de um passo em cada borda: sem ela, a deriva descobriria uma
       faixa vazia na lateral toda vez que a câmera se deslocasse. */
    campo.colunas = Math.ceil(campo.largura / PASSO) + 2
    campo.linhas = Math.ceil(campo.altura / PASSO) + 2

    var nos = campo.nos
    nos.length = 0

    for (var gy = 0; gy < campo.linhas; gy++) {
      for (var gx = 0; gx < campo.colunas; gx++) {
        var sorte = embaralhar(gx, gy)
        nos.push({
          x: (gx - 1) * PASSO + PASSO / 2,
          y: (gy - 1) * PASSO + PASSO / 2,
          /* Losango em ~1 de cada 3. A alternância quebra a regularidade da
             treliça sem introduzir uma forma nova. */
          losango: sorte > 0.66,
          /* ~1 em 11 é de acento. Menos que isso e o carmim some; mais e o
             fundo começa a competir com os botões, que são a única outra
             coisa vermelha da tela. */
          acento: sorte > 0.91,
          i: 0,
          alvo: 0,
        })
      }
    }
  }

  /* =====================================================================
   * DESENHO
   * ================================================================== */

  function desenhar(campo) {
    var ctx = campo.ctx
    var nos = campo.nos
    var colunas = campo.colunas
    var maiorDelta = 0
    var n

    ctx.clearRect(0, 0, campo.largura, campo.altura)

    /* O mouse em coordenadas DESTE canvas. Fora da tela ele fica no menos
       infinito de `mouseX`, e todos os alvos caem para zero sozinhos. */
    var mx = mouseX - campo.esquerda
    var my = mouseY - campo.topo

    /* --- Intensidades --------------------------------------------------
       O alvo é a queda suave sobre a distância; o valor corrente persegue.
       A perseguição é o que faz a revelação ARRASTAR atrás do cursor e
       decair depois dele, em vez de acender e apagar como um interruptor. */
    for (n = 0; n < nos.length; n++) {
      var no = nos[n]
      var alvo = 0

      if (reativo && temPonteiro) {
        var dx = no.x + campo.derivaX - mx
        var dy = no.y + campo.derivaY - my
        var d2 = dx * dx + dy * dy
        if (d2 < RAIO * RAIO) {
          alvo = suavizar(1 - Math.sqrt(d2) / RAIO)
        }
      }

      no.alvo = alvo
      var delta = alvo - no.i
      no.i += delta * LERP_NO

      var absoluto = delta < 0 ? -delta : delta
      if (absoluto > maiorDelta) maiorDelta = absoluto
    }

    ctx.save()
    ctx.translate(campo.derivaX, campo.derivaY)

    /* --- Traços, primeiro, para passarem POR TRÁS dos nós ---------------
       Só na direção +x e +y: percorrer os quatro vizinhos desenharia cada
       aresta duas vezes, dobrando o custo e a opacidade nas sobreposições. */
    ctx.lineWidth = 1
    ctx.lineCap = 'butt'

    for (n = 0; n < nos.length; n++) {
      var origem = nos[n]
      if (origem.i < LIMIAR_TRACO) continue

      var coluna = n % colunas

      if (coluna < colunas - 1) traco(ctx, origem, nos[n + 1])
      if (n + colunas < nos.length) traco(ctx, origem, nos[n + colunas])
    }

    /* --- Os nós --------------------------------------------------------- */
    for (n = 0; n < nos.length; n++) {
      var atual = nos[n]
      var alfa = ALFA_REPOUSO + atual.i * (ALFA_MAX - ALFA_REPOUSO)
      var lado = 3 + atual.i * 2

      /* REGRA 2 da paleta: o acento aqui é fio e marcador, então é o
         carmim-claro. O laca é preenchimento e não entra em lugar nenhum
         deste arquivo. */
      var tinta =
        atual.acento && atual.i > LIMIAR_ACENTO ? CARMIM_CLARO : OSSO

      ctx.strokeStyle = 'rgba(' + tinta + ', ' + alfa.toFixed(3) + ')'
      ctx.beginPath()

      if (atual.losango) {
        ctx.moveTo(atual.x, atual.y - lado)
        ctx.lineTo(atual.x + lado, atual.y)
        ctx.lineTo(atual.x, atual.y + lado)
        ctx.lineTo(atual.x - lado, atual.y)
        ctx.closePath()
      } else {
        ctx.rect(atual.x - lado, atual.y - lado, lado * 2, lado * 2)
      }

      ctx.stroke()
    }

    ctx.restore()

    return maiorDelta
  }

  /* O traço entre dois vizinhos.
   *
   * Numa treliça regular os vizinhos já estão alinhados nos eixos, então
   * cada segmento é reto — não há cotovelo a desenhar. O contorno ESCALONADO
   * não vem de dobrar cada traço: vem de só uma PARTE da grade acender, e
   * toda ela ser ortogonal. O que se revela é um recorte em degraus, nunca
   * uma circunferência.
   *
   * O recuo nas duas pontas é o que separa isto de uma grade impressa: em
   * desenho técnico a linha de ligação não encosta no símbolo que liga. São
   * 9px de ar de cada lado, e é o detalhe que faz o conjunto ler como
   * traçado em vez de como quadriculado. */
  var RECUO = 9

  function traco(ctx, a, b) {
    var forca = a.i < b.i ? a.i : b.i
    if (forca < LIMIAR_TRACO) return

    var horizontal = a.y === b.y
    var vao = horizontal ? b.x - a.x : b.y - a.y
    if (vao <= RECUO * 2) return

    ctx.strokeStyle = 'rgba(' + OSSO + ', ' + (forca * 0.45).toFixed(3) + ')'
    ctx.beginPath()

    if (horizontal) {
      ctx.moveTo(a.x + RECUO, a.y)
      ctx.lineTo(b.x - RECUO, b.y)
    } else {
      ctx.moveTo(a.x, a.y + RECUO)
      ctx.lineTo(b.x, b.y - RECUO)
    }

    ctx.stroke()
  }

  /* =====================================================================
   * O LAÇO
   * ================================================================== */

  function passo() {
    var maiorDelta = 0

    /* LEITURAS PRIMEIRO, ESCRITAS DEPOIS.
     *
     * Todos os `getBoundingClientRect` acontecem neste bloco, antes de
     * qualquer desenho. A GSAP escreve transforms no mesmo quadro; alternar
     * medida e escrita força o navegador a recalcular o layout no meio do
     * caminho, e a 60Hz isso aparece. */
    for (var c = 0; c < campos.length; c++) {
      if (campos[c].visivel && campos[c].alocado) medir(campos[c])
    }

    for (var d = 0; d < campos.length; d++) {
      var campo = campos[d]
      if (!campo.visivel || !campo.alocado) continue

      var deltaX = campo.alvoDerivaX - campo.derivaX
      var deltaY = campo.alvoDerivaY - campo.derivaY
      campo.derivaX += deltaX * LERP_CAMERA
      campo.derivaY += deltaY * LERP_CAMERA

      var absX = deltaX < 0 ? -deltaX : deltaX
      var absY = deltaY < 0 ? -deltaY : deltaY
      if (absX > maiorDelta) maiorDelta = absX
      if (absY > maiorDelta) maiorDelta = absY

      var deltaNos = desenhar(campo)
      if (deltaNos > maiorDelta) maiorDelta = deltaNos
    }

    /* Chegou. Encosta os valores no alvo — senão a próxima comparação
       reabre o laço por causa do resto que a interpolação deixou. */
    if (maiorDelta < EPSILON) {
      for (var e = 0; e < campos.length; e++) {
        campos[e].derivaX = campos[e].alvoDerivaX
        campos[e].derivaY = campos[e].alvoDerivaY
      }
      parar()
      return
    }

    quadro = requestAnimationFrame(passo)
  }

  function ligar() {
    if (rodando || !animar) return
    rodando = true
    quadro = requestAnimationFrame(passo)
  }

  function parar() {
    rodando = false
    if (quadro) cancelAnimationFrame(quadro)
    quadro = null
  }

  /* Um quadro só, parado. É o que se vê com movimento reduzido, em tela de
     toque e enquanto o mouse não chegou: o desenho continua existindo — o
     que sai é o movimento, que é exatamente o que foi pedido. */
  function pintarRepouso(campo) {
    if (!campo.alocado) return
    medir(campo)
    desenhar(campo)
  }

  /* =====================================================================
   * ENTRADA
   * ================================================================== */

  Array.prototype.forEach.call(hospedeiros, function (tela) {
    var campo = criarCampo(tela)
    if (campo) campos.push(campo)
  })

  if (!campos.length) return

  /* Só existe buffer para o campo que está na tela. O observador é também o
     que liga e desliga o laço — sem ele o desenho continuaria sendo pintado
     três seções acima de onde a pessoa está. */
  if ('IntersectionObserver' in window) {
    var observador = new IntersectionObserver(
      function (entradas) {
        entradas.forEach(function (entrada) {
          var campo = null
          for (var i = 0; i < campos.length; i++) {
            if (campos[i].tela === entrada.target) campo = campos[i]
          }
          if (!campo) return

          campo.visivel = entrada.isIntersecting

          if (campo.visivel) {
            if (!campo.alocado) alocar(campo)
            if (reativo) ligar()
            else pintarRepouso(campo)
          } else {
            liberar(campo)
          }
        })

        /* Sem nenhum campo na tela não há o que desenhar. */
        var algum = campos.some(function (campo) {
          return campo.visivel
        })
        if (!algum) parar()
      },
      { rootMargin: '15% 0px' }
    )

    campos.forEach(function (campo) {
      observador.observe(campo.tela)
    })
  } else {
    campos.forEach(function (campo) {
      campo.visivel = true
      alocar(campo)
      if (!reativo) pintarRepouso(campo)
    })
    if (reativo) ligar()
  }

  if (reativo) {
    /* Um listener, passivo, que grava dois floats e não toca no DOM. O laço
       é o acelerador: não há throttle a fazer aqui. */
    window.addEventListener(
      'mousemove',
      function (evento) {
        mouseX = evento.clientX
        mouseY = evento.clientY
        temPonteiro = true

        /* A deriva é a mesma para todos os campos: a posição no MUNDO,
           normalizada de -1 a 1. É o que faz o conjunto ler como um plano
           só, visto por três janelas. */
        var nx = (evento.clientX / window.innerWidth) * 2 - 1
        var ny = (evento.clientY / window.innerHeight) * 2 - 1

        for (var i = 0; i < campos.length; i++) {
          /* Sinal invertido: o fundo anda CONTRA o cursor, como um plano
             mais distante visto de outro ângulo. Andando junto, o desenho
             pareceria colado no ponteiro. */
          campos[i].alvoDerivaX = -nx * DERIVA_MAX
          campos[i].alvoDerivaY = -ny * DERIVA_MAX
        }

        ligar()
      },
      { passive: true }
    )

    /* O ponteiro saiu da janela: os alvos voltam ao centro e o campo se
       apaga sozinho, em vez de congelar aceso onde o mouse estava. */
    document.addEventListener('mouseleave', function () {
      temPonteiro = false
      for (var i = 0; i < campos.length; i++) {
        campos[i].alvoDerivaX = 0
        campos[i].alvoDerivaY = 0
      }
      ligar()
    })

    document.addEventListener('visibilitychange', function () {
      if (document.hidden) parar()
      else ligar()
    })
  }

  /* Redimensionar reconfigura o buffer, o que é caro. O adiamento evita
     fazer isso sessenta vezes enquanto se arrasta a janela. */
  var temporizador = null
  window.addEventListener(
    'resize',
    function () {
      clearTimeout(temporizador)
      temporizador = setTimeout(function () {
        campos.forEach(function (campo) {
          if (!campo.visivel) return
          liberar(campo)
          alocar(campo)
          if (!reativo) pintarRepouso(campo)
        })
        if (reativo) ligar()
      }, 160)
    },
    { passive: true }
  )
})()
