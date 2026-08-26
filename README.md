# Portfólio — André Gritten

Site pessoal em Django: trajetória, certificações, projetos e contato, todos
editáveis pelo admin. Página única, tema escuro, narrativa conduzida pela
rolagem.

**Identidade:** Ônix & Carmim. A paleta e a tipografia estão especificadas e
medidas — ver [Design](#design) abaixo.

---

## Rodar localmente

Precisa de Python 3.12+ e nada além disso. Sem `.env`, sem banco a subir, sem
Node: o CSS compilado, os ícones e as fontes são versionados.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

pip install -r requirements.txt
python manage.py migrate
python manage.py semear         # carrega o conteúdo do currículo
python manage.py createsuperuser
python manage.py runserver
```

O site fica em <http://127.0.0.1:8000/> e o admin em `/jarvis/`.

`semear` é idempotente: rodar de novo atualiza o que existe em vez de duplicar.
Ele **não** cria projetos — inventar um portfólio de projetos seria mentir
sobre o que existe. Cadastre os seus em `/jarvis/portfolio/projeto/`.

---

## Estrutura

```
config/          settings, urls, wsgi
apps/
  core/          templatetags ({% icone %}, {% estatico %}), identidade do site
  portfolio/     models, admin, views, forms, testes
templates/       base + partials + a home
static/          css compilado, fontes .woff2, js, imagens, o PDF do currículo
theme/           fonte do Tailwind e os scripts de build
tools/           conferidor de contraste e gerador do card de compartilhamento
```

### O que é gerado e o que é fonte

| Gerado | A partir de | Comando |
|---|---|---|
| `static/css/app.css` | `theme/input.css` + `theme/tailwind.config.js` | `npm run css` |
| `static/css/fontes.css` + `static/fonts/*.woff2` | Google Fonts | `npm run fontes` |
| `apps/core/icones.json` | `lucide-static` | `npm run icones` |
| `static/img/og-image.png` | `tools/gerar_og.py` | `python tools/gerar_og.py` |

Todos são **versionados**, de propósito: quem clona o repositório roda o site
sem instalar Node. Node só é necessário para mexer no visual.

---

## Design

A especificação completa, com o contraste medido par a par, está em
<https://claude.ai/code/artifact/1ad93ee9-1dfb-473b-90d5-df49b25847d6>.

### A rampa

| Token | Hex | Papel |
|---|---|---|
| `onix` | `#0B0A0C` | corpo da página |
| `breu` | `#141216` | seções alternadas |
| `fundo` | `#1E1B22` | cartões e painéis |
| `borda` | `#322D38` | fio decorativo |
| `borda-forte` | `#726980` | contorno de campo e de controle |
| `carmim` | `#C2263C` | **só preenchimento** |
| `carmim-claro` | `#E5566B` | texto, fio, marcador, link |
| `osso` | `#F2EDE6` | tinta |
| `secundaria` | `#A39BA8` | texto de apoio |

### As quatro regras do carmim

O carmim laca reprova como texto: **2,94:1** sobre o fundo dos cartões, contra
um piso de 4,5:1. Clareá-lo até passar sozinho o transformaria em rosa e
destruiria a qualidade fosca que define a marca. Por isso são dois tokens com
papéis fixos:

1. **O laca só preenche.** Botão, selo, marcador cheio. Osso em cima: 4,96:1.
2. **O claro é o que se lê.** Link, fio, marcador, rótulo: 4,76:1 na pior
   superfície.
3. **Bloco carmim não pousa em cartão.** Ou fica sobre ônix/breu, ou ganha 1px
   de carmim-claro (`.btn-carmim-em-cartao`).
4. **Campo tem borda própria.** `borda-forte` (3,28:1), não a decorativa
   (1,48:1).

```bash
python tools/conferir_cores.py
```

Reproduz as medições e **falha** se algum par cair abaixo do piso — ou se um
uso proibido passar a ser válido, o que significaria que a regra ficou
obsoleta. Rode sempre que mexer num token de `theme/input.css`.

Uma consequência a não esquecer: a cor de erro é vermelha e o acento da marca
também. Nenhuma mensagem de estado depende só de cor — cada uma leva ícone, e
o campo com erro engrossa a borda para 2px.

### Tipografia

**Bricolage Grotesque** nos títulos (caixa-alta, `letter-spacing: -.02em`),
**Instrument Sans** no texto, **JetBrains Mono** nos rótulos técnicos.
Auto-hospedadas — o site não faz nenhuma requisição a fonts.googleapis.com.

O `text-transform: uppercase` mora no **CSS**, nunca no conteúdo: o banco
guarda "Sistema de registro CAU-Uni" com a grafia normal. Gravar em maiúsculas
faria leitor de tela soletrar as siglas letra por letra.

### Movimento

GSAP + ScrollTrigger + Lenis, em `static/js/narrativa.js`. Com
`prefers-reduced-motion: reduce` esse arquivo **não faz nada** — e não é
delicadeza: sem o scroll guiado que lhes dá sentido, uma seção grudada vira
uma tela parada e os blocos escondidos esperam um gatilho que nunca dispara.
O `movimento.js` também não marca a classe que os esconde, então o conteúdo
nasce visível e empilhado.

Duas medidas do `.revelar` andam juntas e não podem ser mexidas separadas: o
deslocamento de entrada (`--revelar-deslocamento`, 14px) tem de ser **menor
que o menor `gap`** dos contêineres que o usam. `translateY` não tira o bloco
do fluxo — a caixa fica onde está e só o desenho desce. Passando do gap, o
cartão ainda invisível fica dentro do cartão de baixo, e a invasão aparece
durante a animação ou de vez, se o gatilho falhar.

### O campo

`static/js/campo.js` desenha a malha viva atrás das três seções que respiram
(topo, projetos, contato) — nós geométricos numa treliça de 112px, ligados por
traços ortogonais que só aparecem perto do cursor. Parado, fica no mesmo peso
da `.malha-tecnica` e praticamente não se enxerga.

A reação tem duas camadas, e a distinção é o que evita o efeito de cursor
genérico: a **deriva** é global (o campo inteiro translada 14px sob o mouse,
como uma câmera) e a **revelação** é por proximidade. Como os traços seguem a
grade, o recorte revelado tem contorno escalonado, nunca um círculo.

O laço **para** quando tudo chega ao repouso, e o buffer do canvas só existe
para a seção que está na tela. Abaixo de 768px o canvas é removido do DOM:
sem cursor não há o que revelar, e a malha já é o repouso do desenho.

---

## Testes

```bash
python manage.py test
```

Cobrem o que quebraria em silêncio: contato perdendo mensagem quando o SMTP
falha, projeto despublicado aparecendo, filtro listando tecnologia que não
filtra nada, e o `semear` duplicando registros.

---

## Deploy no Render

| Campo | Valor |
|---|---|
| Build Command | `./build.sh` |
| Start Command | `gunicorn config.wsgi` |
| Runtime | ver `runtime.txt` (Python 3.12) |

Variáveis de ambiente — as duas primeiras são obrigatórias:

| Variável | Para quê |
|---|---|
| `SECRET_KEY` | O settings **recusa subir** com `DEBUG=False` e a chave de desenvolvimento |
| `DEBUG` | `False` |
| `DATABASE_URL` | A *Internal Database URL* do PostgreSQL. Sem ela, cai em SQLite |
| `CLOUDINARY_URL` | Sem ela, imagens e PDFs enviados pelo admin somem no deploy seguinte — o disco do Render é efêmero |
| `EMAIL_*` | SMTP do formulário. Sem eles, o e-mail sai no console; a mensagem é gravada no banco de qualquer forma |

`ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` se configuram sozinhos a partir de
`RENDER_EXTERNAL_HOSTNAME`. Ver `.env.example` para a lista completa.

---

## Notas de manutenção

- **Ícone novo numa tela?** Acrescente o nome em `theme/extrair-icones.js` e
  rode `npm run icones`. A templatetag falha alto se o ícone não existir —
  um ícone que some da página é o tipo de defeito que ninguém nota.
- **Mexeu em `theme/input.css`?** `npm run css` **e** `python
  tools/conferir_cores.py`.
- **Diminuiu o `gap` de alguma grade de cartões?** Confira contra o
  `--revelar-deslocamento` (14px). Gap menor que o deslocamento devolve a
  sobreposição — ver [Movimento](#movimento).
- **Mexeu no `favicon.svg`?** O `favicon.ico` é rasterizado a partir dele em
  seis tamanhos e **não se regenera sozinho** — os dois vão divergir em
  silêncio. Ambos e mais o `marca.svg` saem do mesmo glifo traçado; só a
  espessura do traço muda (2,4 na marca a 36px, 4,5 no ícone que desce a
  16px).
- **Campo numa seção nova?** O `.campo` vai dentro de uma `<section>` com
  `relative overflow-hidden`, e o conteúdo dela precisa de `relative z-10`,
  senão o canvas pinta por cima. O `overflow-hidden` mora na seção e nunca no
  `.campo`: overflow entre o canvas preso e a rolagem desliga o `sticky`, e o
  buffer volta a ter a altura inteira da seção.
- **Categoria de tecnologia nova?** Acrescente em `Tecnologia.ORDEM_DO_QUADRO`,
  senão ela aparece no fim do quadro de habilidades.
- **Não regrave `requirements.txt` com `pip freeze >` no PowerShell**: o
  redirecionamento grava em UTF-16 e apaga os comentários que explicam cada
  pino.
- `cau-uni/` é referência de método (o sistema do CAU/PR, com o próprio `.git`)
  e está no `.gitignore`. Não é código deste projeto.
