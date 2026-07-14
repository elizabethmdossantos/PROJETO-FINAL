# PDV Enxuto — Documentação Técnica Completa

Projeto Integrador — Módulo III — Informática para Internet
Tema: ERP enxuto / gestão comercial (PDV com login por perfil, vendas e caixa)

Este documento explica, arquivo por arquivo, **o que cada parte do código faz,
por que ela existe e como as peças se encaixam**. Ele complementa o `README.md`
(que foca em "como rodar") e serve como material de apoio para a apresentação:
cada integrante pode usar a seção correspondente à sua parte para explicar o
próprio trabalho.

---

## Sumário

1. [Visão geral da arquitetura](#1-visão-geral-da-arquitetura)
2. [Banco de dados — modelagem](#2-banco-de-dados--modelagem)
3. [API (FastAPI) — camada por camada](#3-api-fastapi--camada-por-camada)
4. [Aplicação Web (Flask) — camada por camada](#4-aplicação-web-flask--camada-por-camada)
5. [Front-end — templates, CSS e JavaScript](#5-front-end--templates-css-e-javascript)
6. [Testes automatizados (Pytest)](#6-testes-automatizados-pytest)
7. [Docker Compose e scripts de apoio](#7-docker-compose-e-scripts-de-apoio)
8. [Decisões de arquitetura e trade-offs](#8-decisões-de-arquitetura-e-trade-offs)
9. [O que foi implementado nesta rodada de finalização](#9-o-que-foi-implementado-nesta-rodada-de-finalização)

---

## 1. Visão geral da arquitetura

```
projeto-integrador-pdv/
├── api/                      → Back-end FastAPI + SQLAlchemy + MySQL + JWT
│   ├── app/
│   │   ├── core/              → configuração, conexão com banco, segurança, dependências
│   │   ├── models/             → tabelas do banco (SQLAlchemy ORM)
│   │   ├── schemas/            → formato de entrada/saída da API (Pydantic)
│   │   ├── routers/            → endpoints HTTP (auth, produtos, caixa, vendas)
│   │   └── main.py             → ponto de entrada da API
│   ├── seed_usuarios.py       → cria usuários de teste
│   ├── seed_produtos.py       → cria produtos de teste
│   └── requirements.txt
├── web/                       → Front-end Flask + Jinja2 (consome a API via HTTP)
│   ├── app/
│   │   ├── routes/              → blueprints Flask (auth, admin, pdv, produtos)
│   │   ├── templates/           → páginas HTML (Jinja2)
│   │   ├── static/css, static/js
│   │   └── main.py              → cria e registra a aplicação Flask
│   └── requirements.txt
├── tests/                     → Pytest (SQLite em memória, não depende do MySQL rodando)
├── docker-compose.yml         → sobe um MySQL pronto para desenvolvimento
└── README.md
```

### O caminho de uma requisição

O navegador **nunca fala diretamente com a API**. O fluxo é sempre:

```
Navegador → Flask (web/) → API (api/) → MySQL
```

1. O usuário clica em algo na tela (ex: "Entrar").
2. O Flask recebe esse clique como uma requisição HTTP comum (formulário POST).
3. O Flask repassa a informação para a API via `requests` (biblioteca Python
   de cliente HTTP), anexando o token JWT no header `Authorization: Bearer <token>`
   quando o usuário já está logado.
4. A API valida o token, consulta/grava no MySQL através do SQLAlchemy, e
   devolve JSON para o Flask.
5. O Flask lê esse JSON e renderiza uma página HTML (Jinja2) com esses dados.

Essa separação existe por dois motivos:
- **Segurança**: o token JWT nunca chega ao JavaScript do navegador — ele
  fica guardado na sessão do lado do servidor Flask (`session["token"]`).
  Isso reduz a superfície de ataque (ex: roubo de token via XSS).
- **Separação de responsabilidades**: a API é o único lugar com regra de
  negócio e acesso ao banco; o Flask só cuida de sessão de usuário e
  apresentação. Isso deixa claro, na avaliação do projeto, qual parte é
  "back-end FastAPI" e qual é "front-end Flask".

---

## 2. Banco de dados — modelagem

Cinco tabelas, todas criadas automaticamente pela API na primeira execução
(`Base.metadata.create_all()`, chamado em `api/app/main.py` e nos scripts de
seed). Não é necessário rodar nenhum script SQL manual de criação de tabela.

### `usuarios`
| Coluna        | Tipo                  | Observação |
|---------------|------------------------|------------|
| id            | Integer (PK)           | |
| nome          | String(120)             | |
| login         | String(60), único        | usado para autenticação |
| senha_hash    | String(255)              | hash bcrypt, nunca a senha em texto puro |
| perfil        | Enum(`admin`, `caixa`)  | fonte da verdade sobre permissões |
| ativo         | Boolean                  | permite desativar um usuário sem apagar histórico |
| criado_em     | DateTime                  | preenchido pelo banco (`server_default=func.now()`) |

### `produtos`
| Coluna     | Tipo             | Observação |
|------------|-------------------|------------|
| id         | Integer (PK)      | id interno, nunca exposto ao operador |
| codigo     | String(30), único  | o que o operador digita/bipa no terminal |
| nome       | String(120)        | |
| preco      | Numeric(10,2)       | preço "de tabela" atual |
| estoque    | Integer             | quantidade disponível |
| ativo      | Boolean             | produto descontinuado não aparece mais no terminal |

### `caixas` (turno de trabalho do operador)
| Coluna            | Tipo                        | Observação |
|-------------------|------------------------------|------------|
| id                | Integer (PK)                 | |
| usuario_id        | FK → usuarios.id              | quem abriu o turno |
| status            | Enum(`aberto`, `fechado`)      | |
| valor_abertura    | Numeric(10,2)                  | fundo de troco |
| valor_fechamento  | Numeric(10,2), opcional         | valor contado fisicamente ao fechar |
| aberto_em / fechado_em | DateTime                   | |
| observacoes       | String(255), opcional           | |

### `vendas`
| Coluna           | Tipo                              | Observação |
|------------------|-------------------------------------|------------|
| id               | Integer (PK)                        | |
| caixa_id         | FK → caixas.id                        | a qual turno a venda pertence |
| usuario_id       | FK → usuarios.id                      | quem vendeu (redundante com o caixa, mas útil para consultas diretas) |
| forma_pagamento  | Enum(`pix`, `cartao`, `vale_refeicao`)  | |
| status           | Enum(`concluida`, `cancelada`)         | usado pelo cancelamento de venda |
| valor_total      | Numeric(10,2)                          | soma dos itens no momento da venda |
| criado_em        | DateTime                                | usado no filtro por período do dashboard |

### `itens_venda`
| Coluna          | Tipo                | Observação |
|-----------------|----------------------|------------|
| id              | Integer (PK)          | |
| venda_id        | FK → vendas.id          | |
| produto_id      | FK → produtos.id        | |
| quantidade      | Integer                 | |
| preco_unitario  | Numeric(10,2)            | **snapshot** do preço do produto na hora da venda |
| subtotal        | Numeric(10,2)            | quantidade × preco_unitario |

**Por que existe `preco_unitario` em `itens_venda` em vez de só consultar
`produtos.preco`?** Porque o preço de um produto muda com o tempo (reajustes,
promoções). Se o histórico de vendas lesse o preço atual do produto, uma venda
de mês passado mudaria de valor sempre que o preço fosse atualizado hoje. Guardar
o preço praticado no momento da venda ("snapshot") é o que garante que o
histórico financeiro seja imutável — um requisito básico de integridade para
qualquer sistema de vendas.

### Relacionamentos (resumo do DER)
```
usuarios (1) ───< (N) caixas (1) ───< (N) vendas (1) ───< (N) itens_venda >─── (N) produtos
                                          usuarios (1) ───< (N) vendas
```
- Um usuário pode ter vários caixas (turnos) ao longo do tempo, mas **só um
  aberto por vez** — essa regra não está no banco (nenhuma constraint SQL
  impede dois registros com `status=aberto` para o mesmo `usuario_id`), e sim
  na camada de aplicação (`api/app/routers/caixa.py`, função `abrir_caixa`),
  que verifica isso antes de inserir.
- Uma venda pertence a exatamente um caixa e a um usuário (o mesmo dono do caixa).
- Uma venda tem N itens; cada item aponta para um produto.

---

## 3. API (FastAPI) — camada por camada

A API é organizada em quatro camadas, cada uma com uma responsabilidade única.
Essa separação (em vez de colocar tudo dentro das rotas) é o que torna o
código testável e fácil de estender.

### 3.1 `app/core/` — infraestrutura transversal

**`config.py`** — Lê variáveis de ambiente do `.env` (via `python-dotenv`) e
expõe uma única instância `settings` usada em todo o resto do código. Contém:
- Dados de conexão com o MySQL (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`)
  e a propriedade `DATABASE_URL`, que monta a string de conexão no formato
  que o SQLAlchemy espera (`mysql+pymysql://usuario:senha@host:porta/banco`).
- `SECRET_KEY` e `ALGORITHM` — usados para assinar/verificar o token JWT.
- `ACCESS_TOKEN_EXPIRE_MINUTES` — validade do token (padrão: 480 min = 8h,
  o tamanho de um turno de trabalho).
- `ADMIN_MASTER_KEY` — a "segunda senha" exigida de quem tenta entrar como
  administrador. Fica só no `.env` da API, nunca é enviada para o front-end
  além do próprio formulário de login.

**`database.py`** — Cria o `engine` do SQLAlchemy (a conexão real com o MySQL)
e a fábrica de sessões `SessionLocal`. Define `Base`, a classe da qual todos
os models herdam. A função `get_db()` é um *generator* usado como dependência
do FastAPI: ele abre uma sessão, entrega (`yield`) para a rota usar, e garante
que a sessão é fechada no `finally` — mesmo se a rota lançar uma exceção. Isso
evita conexões "vazando" com o banco.

**`security.py`** — Duas responsabilidades:
1. **Hash de senha** com `bcrypt` (via `passlib`): `gerar_hash_senha()` e
   `verificar_senha()`. Nunca comparamos senha em texto puro — comparamos o
   hash. Bcrypt é resistente a ataques de força bruta porque é deliberadamente
   lento e usa "salt" automático.
2. **Token JWT** com `python-jose`: `criar_token_acesso()` monta um payload
   (contendo `sub` = login, `perfil`, `id`) e assina com `SECRET_KEY`.
   `decodificar_token()` faz o caminho inverso e devolve `None` se o token
   for inválido ou tiver expirado.

**`deps.py`** — Dependências do FastAPI reutilizadas nas rotas:
- `usuario_atual()` — extrai e decodifica o token do header `Authorization`
  (via `OAuth2PasswordBearer`, que o Swagger entende automaticamente). Se o
  token for inválido, devolve `401`.
- `exigir_admin()` — reaproveita `usuario_atual()` e adicionalmente verifica
  se `perfil == "admin"`, devolvendo `403` caso contrário. Toda rota
  restrita a administrador usa essa dependência (`Depends(exigir_admin)`).

Esse padrão (`Depends`) é o que implementa RBAC (controle de acesso por
perfil) de forma declarativa: basta declarar `_admin: dict = Depends(exigir_admin)`
como parâmetro da rota, e o FastAPI garante que a rota só executa se a
verificação passar.

### 3.2 `app/models/` — tabelas do banco (SQLAlchemy ORM)

Cada arquivo mapeia uma tabela para uma classe Python (ver seção 2 para os
campos). Destaques de implementação:

- `usuario.py` define o `Enum` Python `PerfilUsuario` (`ADMIN`, `CAIXA`), que
  o SQLAlchemy traduz para um `ENUM` no MySQL. Usar um Enum em vez de uma
  string livre impede que um valor inválido (ex: `"administrador"` com erro
  de digitação) seja gravado no banco.
- `caixa.py` e `venda.py` seguem o mesmo padrão com `StatusCaixa` e
  (`StatusVenda`, `FormaPagamento`).
- Os relacionamentos (`relationship(...)`) permitem navegar objetos Python
  sem escrever SQL manual — por exemplo, `venda.itens` devolve a lista de
  `ItemVenda` daquela venda, e `item.produto` devolve o `Produto` relacionado.
  Isso é usado extensivamente no router de vendas para montar as respostas
  detalhadas (nome do produto, nome do operador etc.).

### 3.3 `app/schemas/` — contratos de entrada e saída (Pydantic)

Os schemas definem exatamente o que a API aceita receber e o que promete
devolver — são a "fronteira" entre o mundo externo (JSON) e o modelo interno
(objetos SQLAlchemy). Separar schema de model é o que permite, por exemplo,
que `ProdutoOut` exponha `id`, mas `ProdutoCriar` não aceite `id` do cliente
(quem decide o `id` é o banco).

- **`usuario.py`**: `LoginRequest` (o que o formulário de login envia:
  `login`, `senha`, `perfil_solicitado`, e opcionalmente `senha_admin`),
  `UsuarioOut` (o que a API devolve sobre o usuário logado) e `TokenResponse`
  (token + dados do usuário).
- **`produto.py`**: `ProdutoCriar` (cadastro — exige todos os campos),
  `ProdutoAtualizar` (edição — todos os campos opcionais, só atualiza o que
  for enviado) e `ProdutoOut`.
- **`caixa.py`**: `CaixaAbrir`, `CaixaFechar`, `CaixaOut` e `CaixaResumo`
  (que estende `CaixaOut` com os totais calculados no fechamento).
- **`venda.py`**: `VendaCriar` (recebe forma de pagamento + lista de itens,
  cada item identificado por `codigo_produto`, não por `id` — é isso que
  permite que o terminal use o código de barras diretamente), `VendaOut`
  (resposta simples, usada por quem acabou de vender) e `VendaDetalhada`
  (usada na listagem do admin, já traz o nome do operador e o nome de cada
  produto, evitando que o Flask precise fazer requisições extras só para
  "traduzir" ids em nomes).

Um detalhe de validação: `VendaCriar` usa um `field_validator` para garantir
que a lista de itens não venha vazia — uma venda sem nenhum item não faz
sentido de negócio, e é melhor rejeitar isso na borda (antes de tocar no
banco) do que descobrir depois.

### 3.4 `app/routers/` — os endpoints HTTP

**`auth.py` — `POST /auth/login`**
Fluxo:
1. Busca o usuário pelo `login`. Se não existir ou estiver inativo → `401`
   genérico (propositalmente a mesma mensagem de "senha incorreta", para não
   revelar quais logins existem).
2. Confere a senha com `verificar_senha()`.
3. **Se o formulário pediu perfil `admin`**: confere se o perfil salvo no
   banco realmente é `admin` (→ `403` se não for) e se a `senha_admin`
   enviada bate com `ADMIN_MASTER_KEY` (→ `401` se não bater). Este é o
   ponto-chave de segurança do sistema: **a API nunca decide o perfil pelo
   que o formulário pediu, só pelo que está gravado no banco.** Um operador
   marcando a caixinha "Administrador" no formulário, mesmo manipulando a
   requisição diretamente (ex: via `curl`/Postman), não consegue token de
   admin sem 1) ter perfil admin no banco e 2) saber a senha administrativa.
4. Gera o token JWT com o perfil **confirmado** (nunca o solicitado) e
   devolve junto com os dados do usuário.

**`produtos.py`**
- `POST /produtos` (admin): cria produto, rejeita código duplicado (`409`).
- `GET /produtos` (admin): lista o estoque; parâmetro opcional
  `apenas_ativos` (default `true`) permite à tela de gestão de produtos
  mostrar também os inativos, quando precisar reativá-los.
- `GET /produtos/codigo/{codigo}` (qualquer autenticado): é a rota que o
  terminal de venda chama a cada código digitado/bipado. Só devolve produtos
  **ativos** — um produto desativado "some" do ponto de vista do operador,
  mesmo que ainda exista no banco (preservando o histórico de vendas antigas
  que o referenciam).
- `GET /produtos/{id}` (admin): busca por id interno — usada internamente
  (e disponível para eventuais telas futuras de detalhe).
- `PATCH /produtos/{id}` (admin): atualização parcial. Usa
  `dados.model_dump(exclude_unset=True)` para só alterar os campos que
  vieram no corpo da requisição — assim a tela de edição pode enviar só
  `{"estoque": 50}` sem precisar reenviar nome e preço.

**`caixa.py`**
- `POST /caixa/abrir`: verifica se o usuário já tem um caixa com
  `status=aberto` (`_buscar_caixa_aberto`) e recusa com `409` se tiver — é
  essa checagem, e não uma constraint de banco, que impede dois caixas
  simultâneos.
- `GET /caixa/atual`: devolve o caixa aberto do usuário logado, ou `404`.
- `POST /caixa/fechar`: busca as vendas do turno com `status=concluida`
  (vendas canceladas **não entram na soma**, propositalmente — ver seção 9),
  soma o total geral e por forma de pagamento, marca o caixa como `fechado`,
  grava `valor_fechamento` e `fechado_em`, e devolve um `CaixaResumo` para o
  operador conferir o dinheiro contado fisicamente contra o que o sistema
  calculou.
- `GET /caixa` (admin): histórico de todos os turnos, mais recente primeiro.

**`vendas.py`** — o coração do sistema.
- `POST /vendas`:
  1. Confirma que o usuário tem caixa aberto (`_caixa_aberto_do_usuario`,
     senão `409`).
  2. **Para cada item do carrinho**: busca o produto pelo `codigo` (só entre
     os ativos); se não existir → `404` citando o código; se o estoque for
     insuficiente → `409` com uma mensagem que diz quanto tem disponível e
     quanto foi pedido.
  3. Só depois de validar **todos os itens** é que a venda é de fato
     gravada — se qualquer item falhar, nada é persistido (a função só
     começa a montar os objetos `Venda`/`ItemVenda` depois do loop de
     validação, e o `db.commit()` só acontece no final). Isso implementa o
     requisito "se algum item falhar, a venda inteira é recusada".
  4. O preço unitário salvo em cada `ItemVenda` é o `produto.preco` **no
     momento da venda** (snapshot, explicado na seção 2).
  5. O estoque é debitado (`produto.estoque -= quantidade`) na mesma
     transação da venda — um único `db.commit()` no final garante que ou
     tudo é salvo (venda + itens + baixa de estoque), ou nada é.
- `GET /vendas/minhas`: vendas do próprio operador logado.
- `GET /vendas` (admin): **todas** as vendas, já no formato `VendaDetalhada`
  (nome do operador + nome de cada produto). Aceita os parâmetros opcionais
  `data_inicio` e `data_fim` (tipo `date`) para o filtro por período do
  dashboard — se informados, filtra por `Venda.criado_em` usando o início
  (`00:00:00`) e o fim (`23:59:59`) do dia respectivamente, para que o
  filtro seja inclusivo nas duas pontas.
- `GET /vendas/{id}`: detalhe de uma venda — o dono da venda ou um admin
  podem ver; qualquer outro operador recebe `403`.
- `POST /vendas/{id}/cancelar` (admin): **funcionalidade nova** (ver seção
  9) — devolve a quantidade de cada item ao estoque do produto
  correspondente e muda o status da venda para `cancelada`. Uma venda já
  cancelada não pode ser cancelada de novo (`409`). Como o resumo de
  fechamento de caixa (`POST /caixa/fechar`) só soma vendas `concluida`,
  cancelar uma venda depois que o caixa dela já foi fechado não altera
  retroativamente aquele resumo histórico — mas a venda deixa de contar em
  qualquer relatório futuro.

**`main.py`** — monta o app FastAPI, cria as tabelas (`Base.metadata.create_all`),
configura CORS (liberado para `http://localhost:5000`, o endereço do Flask em
desenvolvimento) e inclui os quatro routers. Uma rota `GET /` simples devolve
um status para checagem rápida de saúde da API.

---

## 4. Aplicação Web (Flask) — camada por camada

O Flask **não acessa o banco diretamente** — ele é um cliente HTTP da API,
usando a biblioteca `requests`. Cada blueprint corresponde a uma área da
aplicação.

**`main.py`** — fábrica da aplicação (`criar_app()`): define a `secret_key`
(usada pelo Flask para assinar o cookie de sessão) e registra os quatro
blueprints (`auth`, `admin`, `pdv`, `produtos`).

**`routes/auth.py`**
- `GET /` → redireciona para `/login`.
- `GET/POST /login`: no `GET`, mostra o formulário. No `POST`, monta o
  payload (`login`, `senha`, `perfil_solicitado`, e `senha_admin` só se a
  chave "Administrador" estiver marcada) e chama `POST /auth/login` na API.
  Se a API recusar, mostra a mensagem de erro devolvida por ela (`flash`).
  Se aceitar, guarda `token`, `usuario` (nome) e `perfil` na `session` do
  Flask e redireciona para o dashboard (admin) ou para a tela de caixa
  (operador).
- `GET /logout`: limpa a sessão inteira.

**`routes/pdv.py`** — fluxo do operador de caixa.
- `GET /pdv/caixa`: busca o caixa aberto do usuário (`GET /caixa/atual` na
  API) e decide, no template, se mostra o formulário de abertura, o de
  fechamento, ou nenhum dos dois (quando vem de um resumo de fechamento).
- `POST /pdv/caixa/abrir` e `POST /pdv/caixa/fechar`: repassam os dados do
  formulário para a API e tratam o retorno (mensagem de erro ou redirecionamento).
- `GET /pdv/terminal`: exige caixa aberto (senão redireciona de volta para
  `/pdv/caixa` com uma mensagem).
- `POST /pdv/terminal/buscar-produto` e `POST /pdv/terminal/finalizar`: essas
  duas rotas existem para o JavaScript do terminal (`pdv.js`) não precisar
  saber o endereço da API nem manusear o token — o Flask atua como *proxy*
  autenticado. O JS chama essas rotas Flask via `fetch`, o Flask injeta o
  header `Authorization` (lido da sessão) e repassa para a API, devolvendo a
  resposta como JSON puro para o navegador.

**`routes/admin.py`** — dashboard e gestão de vendas.
- `GET /admin/dashboard`: lê os parâmetros de query `data_inicio`/`data_fim`
  (se o formulário de filtro foi usado) e repassa como parâmetros para
  `GET /vendas` na API; busca também `GET /produtos` e `GET /caixa`.
  Calcula localmente `total_vendido` e `quantidade_vendas` **apenas sobre
  vendas concluídas** (uma venda cancelada aparece na tabela, riscada, mas
  não entra nesses totais) e a lista de produtos com estoque ≤ 5.
- `POST /admin/vendas/<id>/cancelar`: **funcionalidade nova** — chama
  `POST /vendas/{id}/cancelar` na API e redireciona de volta ao dashboard,
  preservando o filtro de período que estava ativo (por isso o formulário
  de cancelamento carrega `data_inicio`/`data_fim` como campos escondidos).

**`routes/produtos.py`** — **blueprint novo**, tela de gestão de produtos.
- `GET /admin/produtos`: lista todos os produtos (inclusive inativos, via
  `apenas_ativos=false`) para permitir reativar um produto descontinuado.
- `POST /admin/produtos/novo`: lê o formulário de cadastro e chama
  `POST /produtos` na API.
- `POST /admin/produtos/<id>/editar`: lê os campos da linha da tabela
  (nome, preço, estoque, e a chave de "ativo") e chama `PATCH /produtos/{id}`.

Em todas as rotas administrativas, a primeira linha verifica
`session.get("perfil") == "admin"` e redireciona para o login caso contrário
— uma segunda camada de proteção no lado do Flask, complementar (não
substituta) à proteção real que já existe na API via `exigir_admin`.

---

## 5. Front-end — templates, CSS e JavaScript

### 5.1 Templates (Jinja2)

- **`base.html`**: esqueleto HTML comum (fontes, CSS global) com os blocos
  `titulo`, `estilos_extra`, `conteudo` e `scripts_extra`, que as demais
  páginas preenchem via `{% extends %}`.
- **`login.html`**: alternador visual "Operador de caixa" / "Administrador"
  (um checkbox estilizado como chave); o campo de senha administrativa só
  fica visível (`campo-admin.aberto`) quando a chave está marcada — controlado
  pelo `login.js`.
- **`pdv/caixa.html`**: um único template para os três estados do fluxo de
  caixa (parâmetros vindos da rota Flask `pdv.caixa`): formulário de abertura
  (`caixa_aberto` é `None` e não há `resumo`), tela com o botão para o
  terminal + formulário de fechamento (`caixa_aberto` existe), ou o recibo de
  resumo pós-fechamento (`resumo` existe).
- **`pdv/terminal.html`**: campo de código com foco automático, tabela de
  carrinho, botões de forma de pagamento e botão de finalizar — a lógica
  fica toda em `pdv.js` (ver 5.3).
- **`admin/dashboard.html`**: cartões de métricas, um **formulário de filtro
  por período** (`<input type="date">` para `data_inicio`/`data_fim`, que
  faz `GET` na própria rota do dashboard), tabela de vendas com uma coluna
  de ação — um botão **Cancelar** por linha, que só aparece em vendas com
  `status == "concluida"` e pede confirmação via `confirm()` do navegador
  antes de enviar o formulário —, tabela de estoque e tabela de turnos de
  caixa. Um menu (`nav-admin`) permite alternar para a tela de produtos.
- **`admin/produtos.html`** — **template novo**: um formulário de cadastro
  no topo (código, nome, preço, estoque inicial) e uma tabela de edição
  inline logo abaixo, onde cada linha já é um mini-formulário de atualização.
  Como HTML não permite colocar um `<form>` diretamente dentro de uma `<tr>`
  de forma válida, cada linha usa o atributo `form="form-produto-{id}"` nos
  seus campos, apontando para um `<form id="form-produto-{id}">` vazio
  declarado antes da tabela — um recurso padrão do HTML5 que permite que um
  campo pertença a um formulário sem estar aninhado dentro dele.

### 5.2 CSS

- **`main.css`**: variáveis de cor/tipografia (`:root`), estilos da tela de
  login (painel de marca + formulário) e componentes reutilizados em todas
  as telas internas (botões, campos, chave/alternador, mensagens de erro).
- **`terminal.css`**: estilos específicos do terminal de venda, do dashboard
  administrativo e — **acrescentados nesta finalização** — da navegação
  entre dashboard/produtos (`.nav-admin`), do formulário de filtro por
  período (`.form-filtro`), da linha/etiqueta de venda cancelada
  (`.linha-cancelada`, `.etiqueta-venda-cancelada`), do formulário de
  cadastro de produto (`.form-produto`) e dos campos de edição inline da
  tabela de produtos.

### 5.3 JavaScript

- **`login.js`**: alterna a visibilidade do campo de senha administrativa
  conforme o estado da chave "Entrar como" e mantém um relógio ao vivo no
  painel de marca (só decoração, não afeta lógica de negócio).
- **`pdv.js`**: o motor do terminal de venda, todo em cima de `fetch`:
  - Ao apertar Enter no campo de código, chama `POST /pdv/terminal/buscar-produto`;
    se encontrar, adiciona ao carrinho (ou soma quantidade, se o código já
    estiver lá) e re-renderiza a tabela.
  - Cada linha do carrinho tem um botão "Remover" (delegação de evento no
    `corpoCarrinho`, não um listener por linha).
  - Os botões de forma de pagamento marcam qual está selecionada.
  - O botão "Finalizar venda" só fica habilitado quando há itens **e** uma
    forma de pagamento escolhida; ao clicar, monta o payload
    (`forma_pagamento` + lista de `{codigo_produto, quantidade}`) e chama
    `POST /pdv/terminal/finalizar`. Em caso de sucesso, mostra
    "Venda #N registrada com sucesso!" e limpa o carrinho; em caso de erro,
    mostra a mensagem devolvida pela API (ex: estoque insuficiente).

---

## 6. Testes automatizados (Pytest)

Todos os testes rodam contra **SQLite em memória** (configurado em
`tests/conftest.py`, que sobrescreve a dependência `get_db` do FastAPI via
`app.dependency_overrides`), então não é necessário ter o MySQL de pé para
rodar `pytest`. Isso é importante para CI/CD e para rodar os testes rápido
durante o desenvolvimento.

**`conftest.py`** define as fixtures reutilizadas por todos os testes:
- `db_session`: cria as tabelas antes de cada teste e as destrói depois —
  garante isolamento total entre testes (nenhum dado "vaza" de um teste
  para o outro).
- `cliente`: um `TestClient` do FastAPI, que simula requisições HTTP sem
  precisar de um servidor rodando de verdade.
- `usuario_admin` / `usuario_caixa`: criam um usuário de cada perfil no
  banco de teste.
- `headers_admin` / `headers_caixa`: geram um token JWT válido para cada
  usuário e devolvem o header `Authorization` pronto para uso.
- `produto_refrigerante` / `produto_agua`: produtos de teste com estoque
  conhecido, usados nos testes de venda.

**`test_api_auth.py`** (6 cenários): login de operador com sucesso, login de
admin com a segunda senha correta, login de admin com segunda senha errada
(recusado), tentativa de um operador de caixa entrar marcando "Administrador"
(recusado mesmo com a segunda senha certa, porque o perfil no banco não é
admin), e senha incorreta.

**`test_api_caixa.py`** (9 cenários): abertura de caixa, bloqueio de um
segundo caixa simultâneo, consulta do turno atual (com e sem turno aberto),
fechamento sem vendas (resumo zerado), fechamento sem turno aberto (`404`),
restrição do histórico de caixas ao admin, e — **cenário novo** — o
fechamento de caixa não soma uma venda que foi cancelada depois de registrada,
confirmando que o cancelamento de vendas não "quebra" o fechamento de caixa
já existente.

**`test_api_vendas.py`** (12 cenários): venda com sucesso (debita estoque e
calcula total certo), venda com múltiplos itens, venda sem caixa aberto
(`409`), produto inexistente (`404`), estoque insuficiente (`409`, e
confirma que o estoque **não** foi alterado nesse caso), operador vendo
só as próprias vendas vs. admin vendo todas com nome do operador, e os
**cenários novos**: cancelar uma venda devolve o estoque corretamente,
cancelar a mesma venda duas vezes é recusado (`409`), um operador (não-admin)
não pode cancelar uma venda (`403`), e o filtro por período (`data_inicio`/
`data_fim`) exclui corretamente vendas fora do intervalo pedido.

**`test_api_produtos.py`** (7 cenários, **arquivo novo**): cadastro de
produto com sucesso, operador não pode cadastrar (`403`), código duplicado
é recusado (`409`), busca por código ignora produto inativo (`404` mesmo
existindo no banco), atualização de preço/estoque via `PATCH`, operador não
pode listar o estoque completo (`403`), e a listagem por padrão só traz
produtos ativos.

No total, **34 cenários de teste** cobrindo autenticação, RBAC, caixa,
vendas (incluindo as regras de estoque e a transação "tudo ou nada") e
produtos.

Para medir cobertura (requisito de 70% mínimo do roteiro):
```bash
cd tests
pytest --cov=app --cov-report=term-missing
```

> **Nota importante:** o ambiente usado nesta rodada de finalização não
> tinha acesso à internet, então não foi possível instalar as dependências
> (`fastapi`, `sqlalchemy`, `pytest` etc.) nem rodar `pytest` de fato. Toda a
> validação foi feita por outras vias: `python -m py_compile` em **todos** os
> arquivos `.py` do projeto (confirmando ausência de erros de sintaxe) e
> renderização isolada de **todos** os templates Jinja2 com dados fictícios
> equivalentes ao que a API devolveria (confirmando que não há erro de
> template). Ainda assim, **rodar `pytest -v` de verdade em um ambiente com
> internet, antes da entrega, continua sendo essencial** — é a única forma de
> confirmar que a lógica está correta de ponta a ponta, e não só
> sintaticamente válida.

---

## 7. Docker Compose e scripts de apoio

**`docker-compose.yml`** (**arquivo novo**): sobe um container MySQL 8 já
com o schema do banco (`MYSQL_DATABASE`) criado, lendo `DB_PASSWORD`,
`DB_NAME` e `DB_PORT` do `.env` na raiz do projeto (ou usando valores padrão
se você não definir um `.env` ali). Um `healthcheck` com `mysqladmin ping`
permite que outras ferramentas (ex: um futuro `docker-compose` que também
suba a API) esperem o banco estar realmente pronto antes de tentar conectar.
Uso:
```bash
docker compose up -d
```
Isso substitui o passo manual de "abrir o Workbench e criar o schema" — a
tabela em si continua sendo criada pela API (`Base.metadata.create_all`),
só o servidor MySQL em si é que passa a subir via Docker.

**`api/seed_usuarios.py`** e **`api/seed_produtos.py`**: scripts idempotentes
(rodar duas vezes não duplica dados — cada um verifica se o registro já
existe antes de inserir) que populam o banco com os usuários e produtos de
teste usados no roteiro de testes manuais do `README.md`.

---

## 8. Decisões de arquitetura e trade-offs

- **Por que o Flask nunca acessa o MySQL diretamente?** Para manter uma
  fronteira única de regra de negócio (a API) e permitir, no futuro, que
  outro cliente (um app mobile, por exemplo) reutilize a mesma API sem
  duplicar lógica.
- **Por que o cancelamento de venda é restrito a admin?** Cancelar uma venda
  mexe em estoque e em histórico financeiro — permitir que qualquer operador
  cancele suas próprias vendas abriria margem para abuso (ex: vender,
  embolsar o dinheiro, cancelar a venda para "sumir" com o registro). Deixar
  essa ação só com o administrador é uma escolha de controle interno comum
  em sistemas de PDV reais. Se a equipe achar necessário permitir que o
  próprio operador cancele (por exemplo, dentro de uma janela curta de
  tempo), isso pode ser adicionado depois como uma regra extra na mesma
  rota (`POST /vendas/{id}/cancelar`), sem mudar a modelagem.
- **Por que vendas canceladas não somem da tela, só ficam riscadas?**
  Transparência: um admin auditando o dia precisa conseguir ver que uma
  venda existiu e foi cancelada, não só que ela "nunca aconteceu". Por isso
  o status `cancelada` é permanente (nunca se deleta uma venda do banco).
- **Por que o filtro de período é só no admin, não no operador?** O operador
  só vê as próprias vendas do dia corrente na prática (o turno de caixa já
  delimita isso naturalmente); o filtro por período é uma ferramenta de
  análise gerencial, então faz mais sentido só no dashboard administrativo.

---

## 9. O que foi implementado nesta rodada de finalização

Partindo da documentação original do projeto (seção "O que ainda falta"),
os seguintes itens foram implementados:

1. **Tela de cadastro/edição de produto pelo admin** — blueprint
   `web/app/routes/produtos.py` + template `admin/produtos.html` + link de
   navegação no dashboard. Antes só era possível via `seed_produtos.py` ou
   diretamente pelo Swagger da API.
2. **Cancelamento de venda** — endpoint `POST /vendas/{id}/cancelar` na API
   (devolve estoque, muda status para `cancelada`, recusa cancelar duas
   vezes) + botão "Cancelar" por linha na tabela de vendas do dashboard
   (só para vendas concluídas, com confirmação antes de enviar).
3. **Filtro por período no dashboard** — parâmetros opcionais
   `data_inicio`/`data_fim` em `GET /vendas` na API + formulário de data no
   dashboard, preservado nos links/formulários da página (inclusive no
   cancelamento de venda, para não perder o filtro ativo).
4. **`docker-compose.yml`** — sobe um MySQL 8 pronto para desenvolvimento,
   sem precisar instalar o MySQL localmente.

O que **ainda depende da equipe rodar** (ambiente sem internet
nesta finalização, listado também no `README.md`):
- `pip install -r requirements.txt` em `api/` e `web/`.
- `pytest -v` e `pytest --cov=app --cov-report=term-missing` (conferir os
  70% mínimos de cobertura).
- Rodar a API contra um MySQL real (via `docker compose up -d` ou Workbench)
  e fazer o teste manual ponta a ponta descrito no `README.md`.
- Montar o DER visual e os prints de tela para a documentação final da
  Sprint 7, e revisar a apresentação para que todos os integrantes saibam
  explicar a própria parte.
