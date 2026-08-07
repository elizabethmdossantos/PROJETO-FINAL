# PDV Enxuto — Documentação Técnica Completa

- Tema: PDV Enxuto / ERP enxuto para gestão comercial
- Integrantes: Elizabeth, Gustavo, Guilherme, Levi, Vitor
- Turma: 002014 Tec. Informática para Internet — Módulo III

---

## Sumário

1. [Visão geral da arquitetura](#1-visão-geral-da-arquitetura)
2. [Banco de dados — modelagem](#2-banco-de-dados--modelagem)
3. [API (FastAPI) — camada por camada](#3-api-fastapi--camada-por-camada)
4. [Aplicação Web (Flask) — camada por camada](#4-aplicação-web-flask--camada-por-camada)
5. [Front-end — templates, CSS e JavaScript](#5-front-end--templates-css-e-javascript)
6. [Testes automatizados (Pytest)](#6-testes-automatizados-pytest)
7. [Scripts de apoio (seeds)](#7-scripts-de-apoio-seeds)
8. [Decisões de arquitetura e trade-offs](#8-decisões-de-arquitetura-e-trade-offs)
9. [Feira Online — catálogo, pedido e retirada em loja](#9-feira-online--catálogo-pedido-e-retirada-em-loja)
10. [Correções aplicadas nesta versão](#10-correções-aplicadas-nesta-versão)

---

## Descrição do projeto e objetivos
  O projeto consiste em um sistema de gestão comercial com foco em operações de ponto de venda (PDV), controle de caixa, vendas e estoque. 
  A proposta foi organizada em duas camadas principais:
- Back-end em FastAPI para regras de negócio, autenticação e persistência de dados.
- Front-end em Flask para interação via páginas web, com fluxo de login por perfil e telas de administração/operador.

  Os objetivos principais são:
- facilitar o registro de vendas e o controle de estoque;
- permitir abertura e fechamento de caixa com rastreio de valores;
- oferecer uma interface administrativa para gestão de produtos e usuários;
- aplicar conceitos de desenvolvimento web, APIs REST, autenticação e testes automatizados.

## Requisitos funcionais e não funcionais
### Requisitos funcionais
- Login com diferentes perfis: operador de caixa e administrador.
- Autenticação com JWT e senha administrativa para acesso de administrador.
- Abertura e fechamento de turnos de caixa.
- Cadastro, listagem (paginada, com busca), edição e desativação de produtos.
- Registro de vendas com múltiplos itens e formas de pagamento.
- Cancelamento de vendas por administrador, com devolução automática ao estoque.
- Dashboard administrativo com filtros por período e visão consolidada de vendas/caixa.
- Gestão de usuários por administrador (criar, editar perfil, ativar/desativar, excluir).
- **Feira Online (diferencial):** catálogo público para o cliente montar uma lista
  de compras, pagar uma taxa de serviço de 8% para que um funcionário monte a
  feira, e retirar tudo pronto na loja apresentando um número de pedido —
  com possibilidade de cancelamento mediante taxa de 15%.

### Requisitos não funcionais
- Segurança: uso de hash de senha com bcrypt e tokens JWT.
- Controle de acesso por perfil (RBAC).
- Consistência transacional nas vendas e no estoque.
- Testabilidade: suíte automatizada com pytest.
- Manutenibilidade: separação entre API, aplicação web e camada de dados.

## Tecnologias utilizadas e justificativas
- FastAPI: criação rápida de API REST com validação automática via Pydantic e documentação interativa.
- SQLAlchemy: mapeamento objeto-relacional para facilitar a manipulação do banco de dados.
- MySQL: armazenamento persistente dos dados do sistema.
- PyJWT e bcrypt: autenticação segura e geração de tokens JWT.
- Flask + Jinja2: camada web simples para renderização de páginas e integração com a API.
- Pytest: automação de testes com foco em validação de regras de negócio.

---

## 1. Visão geral da arquitetura

```
projeto-integrador-pdv/
├── api/                      → Back-end FastAPI + SQLAlchemy + MySQL + JWT
│   ├── app/
│   │   ├── core/              → configuração, conexão com banco, segurança, dependências
│   │   ├── models/             → tabelas do banco (SQLAlchemy ORM)
│   │   ├── schemas/            → formato de entrada/saída da API (Pydantic)
│   │   ├── routers/            → endpoints HTTP (auth, produtos, caixa, vendas, usuários)
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
└── README.md
```

### O caminho de uma requisição

O navegador **nunca fala diretamente com a API**. O fluxo é sempre:

```
Navegador → Flask (web/ em http://localhost:5000) → API (api/ em http://localhost:8000) → MySQL
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

Sete tabelas, todas criadas automaticamente pela API na primeira execução
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
| Coluna           | Tipo              | Observação |
|------------------|-------------------|------------|
| id               | Integer (PK)      | id interno, nunca exposto ao operador |
| codigo           | String(30), único | o que o operador digita/bipa no terminal |
| nome             | String(120)       | |
| preco            | Numeric(10,2)     | preço "de tabela" atual |
| estoque          | Integer           | quantidade disponível |
| ativo            | Boolean           | produto descontinuado não aparece mais no terminal nem na loja |
| disponivel_loja  | Boolean           | controla, **independente de `ativo`**, se o produto aparece no catálogo público da Feira Online — permite vender algo só no balcão físico |

### `caixas` (turno de trabalho do operador)
| Coluna            | Tipo                        | Observação |
|-------------------|-----------------------------|------------|
| id                | Integer (PK)                | |
| usuario_id        | FK → usuarios.id            | quem abriu o turno |
| status            | Enum(`aberto`, `fechado`)   | |
| valor_abertura    | Numeric(10,2)               | fundo de troco |
| valor_fechamento  | Numeric(10,2), opcional     | valor contado fisicamente ao fechar |
| aberto_em / fechado_em | DateTime               | |
| observacoes       | String(255), opcional       | |

### `vendas`
| Coluna           | Tipo                              | Observação |
|------------------|-------------------------------------|------------|
| id               | Integer (PK)                        | |
| caixa_id         | FK → caixas.id                        | a qual turno a venda pertence |
| usuario_id       | FK → usuarios.id                      | quem vendeu (redundante com o caixa, mas útil para consultas diretas) |
| forma_pagamento  | Enum(`pix`, `cartao`, `vale_refeicao`, `online`)  | `online` identifica vendas geradas pela retirada de um pedido da Feira Online |
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

- **Por que existe `preco_unitario` em `itens_venda` em vez de só consultar `produtos.preco` ?** 
- Porque o preço de um produto muda com o tempo (reajustes, promoções). 
- Se o histórico de vendas lesse o preço atual do produto, uma venda de mês passado mudaria de valor sempre que o preço fosse atualizado hoje.
- Guardar o preço praticado no momento da venda ("snapshot") é o que garante que o histórico financeiro seja imutável — um requisito básico de integridade para
qualquer sistema de vendas.

### `pedidos_online` (Feira Online)
| Coluna                        | Tipo                                             | Observação |
|-------------------------------|---------------------------------------------------|------------|
| id                             | Integer (PK)                                     | |
| numero_pedido                  | String(20), único                                 | comprovante mostrado ao cliente (ex.: `F260802A1B2C`) |
| nome_cliente / telefone_cliente | String                                            | cliente não tem conta — esse par funciona como "senha" para consultar/cancelar |
| status                         | Enum(`aguardando_retirada`, `retirado`, `cancelado`) | |
| subtotal                       | Numeric(10,2)                                    | soma dos itens |
| taxa_servico_percentual/valor  | Numeric                                          | snapshot dos 8% cobrados no momento da compra |
| valor_total                    | Numeric(10,2)                                    | subtotal + taxa de serviço |
| taxa_cancelamento_percentual/valor | Numeric, opcionais                          | só preenchidos se o pedido for cancelado (15%) |
| valor_reembolsado              | Numeric(10,2), opcional                          | valor_total − taxa de cancelamento |
| venda_id                       | FK → vendas.id, opcional                          | preenchido quando o pedido é retirado (liga ao registro de venda) |
| criado_em / retirado_em / cancelado_em | DateTime                                 | |

### `itens_pedido_online`
| Coluna          | Tipo             | Observação |
|-----------------|-------------------|------------|
| id              | Integer (PK)      | |
| pedido_id       | FK → pedidos_online.id | |
| produto_id      | FK → produtos.id  | |
| quantidade      | Integer           | |
| preco_unitario  | Numeric(10,2)     | snapshot, mesmo raciocínio de `itens_venda` |
| subtotal        | Numeric(10,2)     | |

### Relacionamentos (resumo do DER)
```
usuarios (1) ───< (N) caixas (1) ───< (N) vendas (1) ───< (N) itens_venda >─── (N) produtos
                                          usuarios (1) ───< (N) vendas

pedidos_online (1) ───< (N) itens_pedido_online >─── (N) produtos
pedidos_online (0..1) ───> (1) vendas   # preenchido só quando o pedido é retirado
```
- Um usuário pode ter vários caixas (turnos) ao longo do tempo, mas **só um
  aberto por vez** — essa regra não está no banco (nenhuma constraint SQL
  impede dois registros com `status=aberto` para o mesmo `usuario_id`), e sim
  na camada de aplicação (`api/app/routers/caixa.py`, função `abrir_caixa`),
  que verifica isso antes de inserir.
- Uma venda pertence a exatamente um caixa e a um usuário (o mesmo dono do caixa).
- Uma venda tem N itens; cada item aponta para um produto.
- Um pedido online tem N itens; cada item aponta para um produto (mesmo
  padrão de `vendas`/`itens_venda`, reaproveitado de propósito).
- Quando um pedido online é retirado, uma `venda` é criada e o pedido passa a
  referenciá-la — assim o faturamento da Feira Online aparece no mesmo
  relatório e no mesmo fechamento de caixa de qualquer outra venda.

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
1. **Hash de senha** com a biblioteca `bcrypt` **diretamente** (sem passar
   por `passlib`): `gerar_hash_senha()` converte a senha para bytes (truncada
   em 72 bytes, o limite do próprio algoritmo bcrypt), gera um "salt"
   aleatório com `bcrypt.gensalt()` e calcula o hash com `bcrypt.hashpw()`.
   `verificar_senha()` faz o caminho inverso com `bcrypt.checkpw()`. Nunca
   comparamos senha em texto puro — comparamos o hash. Bcrypt é resistente a
   ataques de força bruta porque é deliberadamente lento e usa "salt"
   automático. Usar o pacote `bcrypt` diretamente (em vez de `passlib`) evita
   um problema de compatibilidade conhecido entre versões recentes do
   `bcrypt` (4.1+) e o `passlib`, que faz um autoteste interno na primeira
   chamada e passou a falhar nas versões novas.
2. **Token JWT** com `PyJWT` (biblioteca `jwt`, assinatura HMAC/HS256, sem
   depender do pacote `cryptography`): `criar_token_acesso()` monta um
   payload (contendo `sub` = login, `perfil`, `id`) e assina com
   `SECRET_KEY`. `decodificar_token()` faz o caminho inverso e devolve `None`
   se o token for inválido ou tiver expirado. HS256 usa só HMAC (biblioteca
   padrão de Python por baixo dos panos), então não exige compilar nem
   instalar a biblioteca `cryptography` — o que reduz bastante o atrito de
   instalação em máquinas Windows sem permissão de administrador.

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

**`usuarios.py`** (admin, em todos os endpoints)
- `GET /usuarios`, `POST /usuarios`, `PUT /usuarios/{id}`, `DELETE /usuarios/{id}`.
- Todos exigem `Depends(exigir_admin)` — é aqui que perfis são concedidos, o
  ponto mais sensível do sistema (ver seção 10, item 1).
- `DELETE` bloqueia o login `admin` (`400`) e trata `IntegrityError` de quem
  tem caixa/venda vinculada (`409`), em vez de deixar o erro estourar.

**`pedidos_online.py`** (Feira Online — detalhado na seção 9)
- `GET /catalogo`, `POST /catalogo/verificar-quantidade`: públicos, sem
  autenticação.
- `POST /pedidos-online`, `POST /pedidos-online/consultar`,
  `POST /pedidos-online/cancelar`: públicos, protegidos pelo par
  número do pedido + telefone.
- `GET /pedidos-online`, `POST /pedidos-online/{id}/retirar`: exigem
  `Depends(usuario_atual)` (qualquer funcionário logado, não só admin —
  confirmar retirada é uma tarefa operacional de balcão).

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

**`main.py`** — monta o app FastAPI, cria as tabelas (`Base.metadata.create_all`) e inclui os quatro routers. A API também configura CORS, mas no fluxo normal do projeto o navegador não chama a API diretamente: o Flask faz as requisições servidor-servidor para `http://localhost:8000` e devolve a resposta ao navegador. Assim, a política de CORS é mais relevante para testes diretos à API ou futuros clientes que consumam a API sem proxy.

---

## 4. Aplicação Web (Flask) — camada por camada

O Flask **não acessa o banco diretamente** — ele é um cliente HTTP da API,
usando a biblioteca `requests`. Cada blueprint corresponde a uma área da
aplicação.

**`main.py`** — fábrica da aplicação (`criar_app()`): define a `secret_key`
(usada pelo Flask para assinar o cookie de sessão) e registra os cinco
blueprints (`auth`, `admin`, `pdv`, `produtos`, `loja`).

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
- `GET /pdv/pedidos-online` e `POST /pdv/pedidos-online/<id>/retirar`:
  **novas**, tela do funcionário para conferir a fila de pedidos da Feira
  Online e confirmar retiradas (detalhe completo na seção 9).

**`routes/admin.py`** — dashboard, gestão de vendas e gestão de usuários.
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
- `GET /admin/usuarios`, `POST /admin/usuarios/novo`, `POST /admin/usuarios/<id>/editar` e `POST /admin/usuarios/<id>/excluir`: formam a interface de gestão de contas no painel administrativo. O Flask consome a API `/usuarios` para listar, criar, editar e excluir usuários sem acessar o banco diretamente.

**`routes/produtos.py`** — **blueprint novo**, tela de gestão de produtos.
- `GET /admin/produtos`: lista todos os produtos (inclusive inativos, via
  `apenas_ativos=false`) para permitir reativar um produto descontinuado.
- `POST /admin/produtos/novo`: lê o formulário de cadastro e chama
  `POST /produtos` na API.
- `POST /admin/produtos/<id>/editar`: lê os campos da linha da tabela
  (nome, preço, estoque, e a chave de "ativo") e chama `PATCH /produtos/{id}`.

**`routes/loja.py`** — **blueprint novo, público** (nenhuma rota exige
login), o front-end da Feira Online (detalhe completo na seção 9). Guarda o
carrinho em `session["carrinho_feira"]` — no servidor, nunca em
`localStorage`. Todas as chamadas à API usam `try/except
requests.exceptions.RequestException`, então se a API cair o cliente vê uma
mensagem amigável em vez de uma tela de erro.

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
- **`admin/usuarios.html`** — interface administrativa de cadastro e manutenção de contas.
  O formulário superior cria novos usuários com nome, login, senha, perfil
  (`caixa` ou `admin`) e status ativo/inativo. A seção abaixo lista os
  usuários existentes em uma tabela editável: cada linha é um mini-formulário
  que permite alterar nome, login, perfil e status, e tem botões para salvar
  ou excluir. A exclusão está bloqueada para o usuário `admin` de sistema, e
  a ação de remover pede confirmação do administrador antes de enviar a
  requisição para a API. **Corrigido nesta finalização:** a tabela usava um
  `<form>` aberto dentro de um `<td>` sem fechar (HTML inválido, o navegador
  fechava a tag no primeiro `</td>` e login/perfil/status nunca eram
  enviados) — reescrita com o mesmo padrão `form="form-usuario-{id}"` de
  `admin/produtos.html`, e o bloco de mensagens de flash, que estava
  ausente, foi adicionado.
- **`pdv/pedidos_online.html`** — **template novo**: fila de pedidos com
  status `aguardando_retirada`, cada um com um botão "Confirmar retirada"
  desabilitado se o funcionário não tiver caixa aberto.
- **`loja/*.html`** — **templates novos**, front-end público da Feira
  Online: `catalogo.html` (grade de produtos com etiqueta de disponibilidade
  e formulário de adicionar ao carrinho), `carrinho.html` (tabela editável +
  resumo com subtotal/taxa/total), `checkout.html` (formulário de
  nome/telefone com o resumo final antes de confirmar), `comprovante.html`
  (número do pedido em destaque, itens, status, e botão de cancelar quando
  aplicável) e `consultar.html` (formulário de busca por número + telefone).

### 5.2 CSS

- **`main.css`**: variáveis de cor/tipografia (`:root`), estilos da tela de
  login (painel de marca + formulário) e componentes reutilizados em todas
  as telas internas (botões, campos, chave/alternador, mensagens de erro).
- **`loja.css`** — **arquivo novo**: estilos exclusivos da Feira Online
  (grade de produtos, etiquetas de disponibilidade, resumo de totais,
  número de comprovante). Reaproveita as variáveis de cor definidas em
  `main.css` e os componentes genéricos de `terminal.css` (mensagens,
  botões, campos) — por isso todo template de `loja/` carrega os três
  arquivos.
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
durante o desenvolvimento. O `conftest.py` também habilita
`PRAGMA foreign_keys=ON` na conexão SQLite — por padrão o SQLite não aplica
chaves estrangeiras, e sem isso os testes não pegariam problemas de
integridade referencial que só apareceriam de verdade no MySQL de produção.

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

**`test_api_vendas.py`** (11 cenários): venda com sucesso (debita estoque e
calcula total certo), venda com múltiplos itens, venda sem caixa aberto
(`409`), produto inexistente (`404`), estoque insuficiente (`409`, e
confirma que o estoque **não** foi alterado nesse caso), operador vendo
só as próprias vendas vs. admin vendo todas com nome do operador, e os
**cenários novos**: cancelar uma venda devolve o estoque corretamente,
cancelar a mesma venda duas vezes é recusado (`409`), um operador (não-admin)
não pode cancelar uma venda (`403`), e o filtro por período (`data_inicio`/
`data_fim`) exclui corretamente vendas fora do intervalo pedido.

**`test_api_produtos.py`** (7 cenários): cadastro de
produto com sucesso, operador não pode cadastrar (`403`), código duplicado
é recusado (`409`), busca por código ignora produto inativo (`404` mesmo
existindo no banco), atualização de preço/estoque via `PATCH`, operador não
pode listar o estoque completo (`403`), e a listagem por padrão só traz
produtos ativos.

**`test_api_usuarios.py`** (10 cenários, **arquivo novo**): foi este arquivo
que revelou, durante a revisão do projeto, que o router `/usuarios` não
exigia login algum — os primeiros testes (`sem_token_e_recusado`,
`operador_comum_nao_pode`) documentam a correção. Cobre também: admin lista/
cria/atualiza usuários com sucesso, login duplicado é recusado (`409`), o
usuário `admin` padrão não pode ser excluído, e excluir um usuário com caixa
vinculado retorna `409` tratado (em vez de um erro de integridade não
tratado).

**`test_api_pedidos_online.py`** (11 cenários, **arquivo novo**, cobre a
Feira Online): o catálogo público nunca expõe o estoque exato; produto
inativo não aparece no catálogo; `verificar-quantidade` acima do estoque
informa o máximo disponível; criar pedido debita estoque e calcula a taxa de
serviço (8%) corretamente; pedido com estoque insuficiente é recusado
(`409`); consulta com telefone errado não encontra o pedido (`404`);
cancelar devolve o estoque e cobra a taxa de cancelamento (15%) certinha;
cancelar duas vezes é recusado; a fila de retirada exige login; confirmar
retirada sem caixa aberto é recusado (`409`); e confirmar retirada gera a
venda no caixa aberto, refletindo no fechamento de caixa.

No total, **54 cenários de teste** cobrindo autenticação, RBAC, caixa,
vendas (incluindo as regras de estoque e a transação "tudo ou nada"),
produtos, usuários e a Feira Online — com **94% de cobertura** na camada da
API (medido com `pytest --cov`, acima do mínimo de 70% pedido no roteiro).

Para medir cobertura (requisito de 70% mínimo do roteiro):
```bash
cd tests
pytest --cov=app --cov-report=term-missing
```

Execução Detalhada dos Testes (Visão por cenário):
```bash
cd tests
pytest -v
```

---

## 7. Scripts de apoio (seeds)

O banco é sempre um **MySQL real, criado e gerenciado pelo MySQL Workbench**
(ou outra instalação local do MySQL Server) — o projeto não depende de
Docker em nenhum momento. O único passo manual é criar o schema vazio
(`CREATE DATABASE pdv_db;`); todas as tabelas são criadas automaticamente
pela API na primeira execução (`Base.metadata.create_all`).

**`api/seed_usuarios.py`** e **`api/seed_produtos.py`**: scripts idempotentes
(rodar duas vezes não duplica dados — cada um verifica se o registro já
existe antes de inserir) que populam esse banco com os usuários e produtos
de teste usados no roteiro de testes manuais do `README.md`.

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

## 9. Feira Online — catálogo, pedido e retirada em loja

A Feira Online é o diferencial adicionado ao PDV Enxuto: um canal de venda
pela internet no formato **Click & Collect** (compra online, retirada na
loja física), usando a mesma base de produtos e a mesma lógica de estoque já
existente — sem duplicar regra de negócio.

### 9.1 Fluxo completo

```
Cliente (navegador, sem login)              Loja (funcionário logado)
────────────────────────────────            ─────────────────────────
GET  /loja                     ──────►  GET /catalogo (API, público)
  vê produtos + disponibilidade
  (sem estoque exato)

POST /loja/carrinho/adicionar  ──────►  POST /catalogo/verificar-quantidade
  só aqui, se passar do limite,           (informa o máximo só neste momento)
  o cliente sabe a quantidade máxima

GET  /loja/carrinho
  vê subtotal + taxa de serviço (8%) + total

POST /loja/checkout            ──────►  POST /pedidos-online (API)
  informa nome + telefone                 • valida estoque (tudo ou nada)
  recebe nº do pedido (comprovante)        • debita estoque na hora
                                           • calcula subtotal/taxa/total
                                           • gera numero_pedido único

                                         Funcionário logado abre
                                         GET /pdv/pedidos-online
                                         (fila de pedidos "aguardando_retirada")

Cliente chega com o nº do pedido ──────►  POST /pedidos-online/{id}/retirar
                                           • exige caixa aberto do funcionário
                                           • cria uma Venda (forma_pagamento=online)
                                             vinculada ao caixa — SEM debitar
                                             estoque de novo
                                           • pedido passa a status=retirado

  (opcional) POST /loja/pedido/.../cancelar ──►  POST /pedidos-online/cancelar
     antes da retirada                            • devolve o estoque
                                                    • cobra taxa de 15% sobre
                                                      o valor total
                                                    • mostra o valor a devolver
```

### 9.2 Por que o cliente não expõe estoque exato, e o funcionário sim

O catálogo público (`GET /catalogo`, `api/app/routers/pedidos_online.py`)
devolve só uma faixa de disponibilidade (`disponivel` / `poucas_unidades` /
`indisponivel`), calculada a partir de um limite fixo
(`LIMITE_POUCAS_UNIDADES = 5`, mesmo valor usado no alerta de estoque baixo
do dashboard administrativo, para manter a mesma régua). Divulgar o número
exato de unidades em estoque para qualquer visitante do site é uma
informação comercialmente sensível (concorrentes podem monitorar o giro de
produtos) e sem utilidade real para o cliente. Só quando ele tenta colocar
mais do que existe no carrinho (`POST /catalogo/verificar-quantidade`) é que
o número exato aparece — e mesmo assim, só o **máximo disponível para aquele
item**, não o estoque de todo o catálogo.

### 9.3 Por que o estoque é debitado na criação do pedido, e não na retirada

Se o estoque só fosse debitado na retirada, dois clientes poderiam "comprar"
a mesma última unidade ao mesmo tempo pela internet, e um deles chegaria à
loja para descobrir que não tem o produto — mesmo já tendo pago. Debitar o
estoque no momento do pagamento (criação do pedido) garante que todo pedido
com status `aguardando_retirada` tem, de fato, produtos reservados fisicamente
esperando por ele. O preço a pagar por essa escolha é que, se o pedido for
cancelado, o estoque precisa ser devolvido explicitamente — o que o endpoint
de cancelamento já faz.

### 9.4 Por que a retirada gera uma `Venda` de verdade

Em vez de tratar a Feira Online como um sistema paralelo, a confirmação de
retirada (`POST /pedidos-online/{id}/retirar`) cria um registro em `vendas`
(com `forma_pagamento=online`) vinculado ao **caixa aberto do funcionário
que confirma a retirada**. Isso significa que:
- o faturamento da loja (dashboard, filtro por período) já inclui a Feira
  Online automaticamente, sem relatório separado;
- o fechamento de caixa do funcionário reflete essas vendas normalmente;
- a exigência de caixa aberto para confirmar retirada (`409` se não houver)
  reaproveita a mesma regra que já existia para `POST /vendas`.

O estoque **não** é debitado de novo nesse passo — ele já saiu na criação do
pedido (seção 9.3); só os registros de `Venda`/`ItemVenda` são criados a
partir do snapshot salvo em `ItemPedidoOnline`.

### 9.5 Por que cliente não tem conta, e como isso é protegido

Criar um sistema de contas de cliente (cadastro, senha, recuperação de
senha) estava fora do escopo do prazo do projeto. Em vez disso, cada pedido
é identificado pelo par **número do pedido + telefone usado na compra**
(`PedidoOnlineConsultar`). Dois cuidados evitam que isso vire uma falha de
privacidade:
- a mensagem de erro é **idêntica** para "pedido não existe" e "telefone não
  confere" (`_buscar_pedido_ou_404`), então não dá para descobrir por
  tentativa e erro se um número de pedido é válido;
- o número do pedido não é sequencial e previsível — é gerado com data +
  5 caracteres aleatórios de um UUID (`_gerar_numero_pedido`), então não dá
  para "adivinhar" pedidos de outros clientes tentando `F000001`, `F000002`...

### 9.6 Rotas Flask novas

| Blueprint | Rota | O que faz |
|-----------|------|-----------|
| `loja` (público) | `GET /loja` | catálogo com busca |
| `loja` | `POST /loja/carrinho/adicionar` | adiciona item ao carrinho (sessão Flask) |
| `loja` | `GET /loja/carrinho`, `POST .../atualizar`, `POST .../remover` | gerencia o carrinho |
| `loja` | `GET/POST /loja/checkout` | coleta nome/telefone e cria o pedido na API |
| `loja` | `GET /loja/pedido/<numero>` | comprovante (número, itens, totais, status) |
| `loja` | `POST /loja/pedido/<numero>/cancelar` | cancela e mostra o valor a devolver |
| `loja` | `GET/POST /loja/consultar` | formulário de consulta por número + telefone |
| `pdv` (autenticado) | `GET /pdv/pedidos-online` | fila de pedidos aguardando retirada |
| `pdv` | `POST /pdv/pedidos-online/<id>/retirar` | confirma retirada (gera venda) |

O carrinho fica em `session["carrinho_feira"]` no servidor Flask — nunca em
`localStorage`/cookie do navegador — seguindo o mesmo princípio já usado
para o token JWT do login (ver seção 8).

---

## 10. Correções aplicadas nesta versão

Antes de finalizar a entrega, revisamos o projeto e encontramos os seguintes
problemas, todos corrigidos e cobertos por teste (quando aplicável):

| # | Problema | Onde | Correção |
|---|----------|------|----------|
| 1 | Router `/usuarios` sem nenhuma autenticação — qualquer pessoa não logada podia listar, criar (inclusive um admin), editar e excluir usuários | `api/app/routers/usuarios.py` | Adicionado `Depends(exigir_admin)` em todos os endpoints; `test_api_usuarios.py` cobre o bloqueio |
| 2 | Formulário de edição de usuário com HTML inválido — a tag `<form>` abria dentro de um `<td>` e "vazava" para fora, então login/perfil/status não eram enviados de verdade ao salvar | `web/app/templates/admin/usuarios.html` | Reescrito com o padrão `form="id"` (mesmo já usado em produtos) |
| 3 | Tela de usuários não exibia nenhuma mensagem de sucesso/erro (bloco `get_flashed_messages` ausente) | `web/app/templates/admin/usuarios.html` | Bloco de mensagens adicionado, igual às demais páginas |
| 4 | `pdv/caixa.html` nunca carregava `terminal.css` — a página de abertura/fechamento de caixa ficava sem estilo | `web/app/templates/pdv/caixa.html` | Link do `terminal.css` adicionado |
| 5 | Nenhuma listagem tinha paginação, apesar de ser requisito funcional mínimo do roteiro | `produtos.py`, `vendas.py`, `caixa.py`, `usuarios.py`, `pedidos_online.py` (routers) | Parâmetros `skip`/`limit` adicionados em todas as listagens |
| 6 | Excluir um usuário com caixa/venda vinculada estourava um erro de integridade referencial sem tratamento (500) | `api/app/routers/usuarios.py` | `try/except IntegrityError` → `409` com mensagem clara; testado |
| 7 | Porta do Flask divergente do README (`8080` no código vs. `5000` no texto) | `web/app/main.py` | Unificado em `5000` |
| 8 | CORS da API liberava só `http://localhost:8000` (a própria API), nunca o Flask de verdade | `api/app/main.py` | Liberado `http://localhost:5000` |
| 9 | `api/requirements.txt` tinha `flask`, `requests` e `python-dotenv` duplicado — dependências do `web/`, sem uso na API | `api/requirements.txt` | Removidas |
| 10 | `DOCUMENTACAO_TECNICA.md` afirmava "12 cenários" em `test_api_vendas.py` e "34 no total"; o código real tinha 11 e 33 | Este documento | Números corrigidos (e agora atualizados para 54, com os dois arquivos de teste novos) |

---

## Dificuldades, decisões técnicas e aprendizados
- A principal dificuldade foi organizar a comunicação entre a camada web e a API sem expor diretamente a lógica de negócio no front-end.
- A decisão de centralizar as regras de negócio na API e deixar o Flask como cliente autenticado ajudou na separação de responsabilidades.
- O uso de transações para vendas e estoque mostrou-se essencial para manter consistência nos processos de negócio.
- O projeto reforçou conceitos de autenticação, controle de acesso, integração de sistemas e documentação técnica.
- A revisão final do projeto (seção 10) reforçou uma lição à parte: um
  endpoint sem teste é um endpoint sem garantia nenhuma — foi exatamente a
  ausência de testes em `/usuarios` que permitiu a falha de autenticação
  passar despercebida durante o desenvolvimento.

## Referências
- FastAPI Documentation
- Flask Documentation
- SQLAlchemy Documentation
- Pytest Documentation
- MySQL Documentation
- Documentação do projeto em README.md