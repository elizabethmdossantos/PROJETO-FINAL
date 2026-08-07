# PDV Enxuto — Projeto Integrador (Módulo III)

Sistema de gestão comercial (ERP enxuto / PDV) com back-end em **FastAPI + MySQL** (autenticação com `bcrypt` + `PyJWT`)
e front-end em **Flask + Jinja2**.

> **Status atual:**
Todas as funcionalidades previstas no roteiro (login por perfil, caixa/turno, terminal de venda, cadastro/edição de
produtos, cancelamento de venda, filtro por período, paginação e dashboard administrativo) estão implementadas,
incluindo a **Feira Online**: um catálogo público onde o cliente monta a própria lista de compras, paga uma taxa de
serviço de 8% para que um funcionário monte a feira, e retira tudo pronto na loja.
Veja `DOCUMENTACAO_TECNICA.md` para o detalhamento completo de cada parte do código.

## Como funciona a Feira Online

A Feira Online é o canal de venda pela internet: um catálogo público (`/loja`, sem
necessidade de login) onde qualquer cliente pode montar uma lista de compras e
pagar para retirar tudo pronto na loja — o que no mercado é chamado de
**Click & Collect / BOPIS**.

1. O catálogo (`GET /catalogo`) só mostra produtos **ativos e marcados pelo
   admin como "disponível na loja online"** (novo campo `disponivel_loja` em
   `Produto`, editável em `/admin/produtos`). O estoque exato nunca é
   exposto — só uma faixa (`disponivel` / `poucas_unidades` / `indisponivel`).
2. Ao tentar colocar uma quantidade maior do que existe no carrinho, só *nesse
   momento* a API informa o máximo disponível (`POST /catalogo/verificar-quantidade`)
   — o catálogo continua sem mostrar números fixos.
3. O carrinho fica na sessão do Flask (nunca em `localStorage`). Na tela de
   checkout o cliente vê o **subtotal dos produtos**, a **taxa de serviço de
   8%** e o **total a pagar** antes de confirmar — pode simular quanto vai
   gastar sem nem chegar a fazer o pedido.
4. Ao confirmar (`POST /pedidos-online`), o pagamento é simulado como já
   aprovado: o estoque é debitado **na hora** (evita vender a mesma última
   unidade duas vezes) e o cliente recebe um **número de pedido** único (ex.:
   `F260802A1B2C`) — é o comprovante que ele apresenta no balcão.
5. O cliente não tem conta/login: a "senha" dele é o par **número do
   pedido + telefone usado na compra**, usado para consultar
   (`POST /pedidos-online/consultar`) ou cancelar o pedido depois.
6. Se o cliente cancelar antes da retirada (`POST /pedidos-online/cancelar`),
   os itens voltam ao estoque, mas é cobrada uma **taxa de cancelamento de
   15%** sobre o valor total — o comprovante mostra o valor exato que seria
   devolvido.
7. Um funcionário logado (operador ou admin) vê a fila de pedidos pendentes em
   `/pdv/pedidos-online` e confirma a retirada só depois do cliente aparecer
   com o número do pedido. Confirmar retirada (`POST /pedidos-online/{id}/retirar`)
   **gera uma venda de verdade** (forma de pagamento `online`) vinculada ao
   caixa aberto do funcionário — a feira online entra no faturamento e no
   fechamento de caixa igual a qualquer outra venda, sem debitar o estoque de
   novo (ele já saiu no passo 4).

## Como funciona o login

1. O usuário informa **login** e **senha** (sempre).
2. Uma chave "Entrar como" alterna entre **Operador de caixa** e **Administrador**.
3. Se marcar **Administrador**, aparece um segundo campo: a **senha
   administrativa** — um segundo fator que só quem deve abrir a visão
   completa do sistema conhece (definida em `ADMIN_MASTER_KEY`, no `.env` da API).
4. A API sempre confia no perfil salvo no **banco de dados**, nunca no que
   vem do formulário — isso impede que alguém force acesso de admin só
   marcando a caixinha.
5. Administrador correto → `/admin/dashboard` (visão completa: vendas, estoque, valores).
   Operador correto → `/pdv/caixa` (abertura de caixa → terminal de venda).

## Como funciona o Caixa/Vendas

1. Ao logar como operador, o sistema leva para `/pdv/caixa`. Se não houver
   turno aberto, pede o **fundo de troco** (valor de abertura) e cria um
   novo `Caixa` (status `aberto`) vinculado a esse operador.
2. Com o caixa aberto, o operador vai para `/pdv/terminal`: digita/bipa o
   **código do produto**, o sistema busca na API (`GET /produtos/codigo/{codigo}`)
   e adiciona ao carrinho (soma quantidade se repetir o código).
3. Ao escolher a forma de pagamento (**Pix, Cartão ou Vale-refeição**) e
   clicar em "Finalizar venda", o carrinho inteiro é enviado para
   `POST /vendas`. A API confere estoque, grava o preço praticado no
   momento (snapshot), debita o estoque e amarra a venda ao caixa aberto —
   tudo em uma única transação (se um item falhar, nada é salvo).
4. Sem caixa aberto, `POST /vendas` é recusado (409) — não dá pra vender
   sem abrir o turno antes.
5. Ao fechar o caixa (`POST /caixa/fechar`), a API soma todas as vendas
   **concluídas** do turno (total geral e por forma de pagamento) e devolve
   esse resumo para o operador conferir contra o valor contado fisicamente.
6. O admin vê tudo isso consolidado em `/admin/dashboard`: todas as vendas
   (com operador e itens, com filtro por período), o estoque atual e o
   histórico de turnos de caixa. Pode cancelar uma venda concluída (devolve
   o estoque automaticamente) e cadastrar/editar produtos em `/admin/produtos`.

## Como rodar

### 1. Banco de dados (MySQL Workbench)

1. Abra o MySQL Workbench e conecte no seu servidor MySQL local (instale o
   MySQL Server antes, se ainda não tiver: https://dev.mysql.com/downloads/mysql/).
2. Crie um schema vazio, por exemplo `pdv_db`:
   ```sql
   CREATE DATABASE pdv_db;
   ```
3. Não precisa criar tabelas na mão — a API cria todas automaticamente na
   primeira execução (`Base.metadata.create_all`).

### 2. API (FastAPI)
```bash
cd api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # edite DB_USER, DB_PASSWORD, ADMIN_MASTER_KEY etc.
python seed_usuarios.py         # cria um usuário admin e um caixa de teste
python seed_produtos.py         # cria alguns produtos de teste (código, preço, estoque)
uvicorn app.main:app --reload --port 8000
```
Documentação automática: http://localhost:8000/docs

### 3. Aplicação Web (Flask)
```bash
cd web
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python app/main.py
```
Acesse: http://localhost:5000 (área interna) e http://localhost:5000/loja (Feira Online, pública)

### Usuários de teste (criados pelo `seed_usuarios.py`)
| Login     | Senha     | Marcar "Administrador"? | Senha administrativa                   |
|-----------|-----------|--------------------------|---------------------------------------|
| `admin`   | `admin123`| Sim                      | valor de `ADMIN_MASTER_KEY` no `.env` |
| `caixa1`  | `caixa123`| Não                      | —                                     |

## Testes automatizados
```bash
cd tests
pip install pytest httpx pytest-cov
pytest -v
pytest --cov=app --cov-report=term-missing
```
Os testes usam SQLite em memória (não precisam do MySQL rodando, e o SQLite
roda com `PRAGMA foreign_keys=ON` para se comportar como o MySQL de produção).
Cobrem login, caixa, vendas (incluindo cancelamento e filtro por período),
produtos, usuários (incluindo controle de acesso) e a Feira Online (catálogo,
criação/cancelamento de pedido, retirada). São **54 testes**, com **94% de
cobertura** na camada da API. Veja `DOCUMENTACAO_TECNICA.md` para a lista
completa de cenários.

## Endpoints principais da API

| Método | Rota                          | Quem acessa            | O que faz |
|--------|-------------------------------|--------------------------|-----------|
| POST   | `/auth/login`                  | Todos                     | Login (retorna JWT) |
| GET    | `/produtos/codigo/{cod}`       | Autenticado               | Busca produto por código (usado no terminal) |
| GET    | `/produtos?skip&limit&busca`   | Admin                      | Lista de estoque (paginada, com busca) |
| GET    | `/produtos/{id}`                | Admin                      | Detalhe de um produto |
| POST   | `/produtos`                     | Admin                      | Cadastra produto |
| PATCH  | `/produtos/{id}`                | Admin                      | Atualiza nome/preço/estoque/status/disponibilidade na loja |
| POST   | `/caixa/abrir`                   | Autenticado               | Abre turno de caixa (fundo de troco) |
| GET    | `/caixa/atual`                   | Autenticado               | Turno aberto do usuário logado |
| POST   | `/caixa/fechar`                  | Autenticado               | Fecha turno e devolve resumo |
| GET    | `/caixa?skip&limit`              | Admin                      | Histórico de turnos (paginado) |
| POST   | `/vendas`                        | Autenticado               | Registra venda (exige caixa aberto) |
| GET    | `/vendas/minhas`                 | Autenticado               | Vendas do próprio operador |
| GET    | `/vendas?data_inicio&data_fim&skip&limit` | Admin             | Todas as vendas, com operador e itens, filtro por período e paginação |
| GET    | `/vendas/{id}`                   | Dono da venda / Admin      | Detalhe de uma venda |
| POST   | `/vendas/{id}/cancelar`          | Admin                      | Cancela uma venda concluída e devolve o estoque |
| GET    | `/usuarios?skip&limit`           | Admin                      | Lista usuários (paginado) |
| POST   | `/usuarios`                      | Admin                      | Cria usuário (define perfil) |
| PUT    | `/usuarios/{id}`                 | Admin                      | Atualiza nome/login/perfil/status/senha |
| DELETE | `/usuarios/{id}`                 | Admin                      | Exclui usuário (bloqueado p/ `admin` e p/ quem tem histórico) |
| GET    | `/catalogo?busca&skip&limit`     | Público                    | Catálogo da Feira Online (sem estoque exato) |
| POST   | `/catalogo/verificar-quantidade` | Público                    | Confere se a quantidade pedida está disponível |
| POST   | `/pedidos-online`                | Público                    | Cria pedido, debita estoque e calcula a taxa de serviço (8%) |
| POST   | `/pedidos-online/consultar`      | Público (nº pedido + telefone) | Consulta o comprovante do pedido |
| POST   | `/pedidos-online/cancelar`       | Público (nº pedido + telefone) | Cancela o pedido e cobra a taxa de cancelamento (15%) |
| GET    | `/pedidos-online?status_filtro`  | Autenticado                | Fila de pedidos aguardando retirada |
| POST   | `/pedidos-online/{id}/retirar`   | Autenticado                | Confirma retirada e gera a venda no caixa aberto |

## Estrutura de pastas
```
projeto-integrador-pdv/
├── api/                     → FastAPI + SQLAlchemy (MySQL) + JWT (bcrypt + PyJWT)
├── web/                     → Flask + Jinja2, consome a API via HTTP
├── tests/                   → Pytest (cobertura da camada de API)
└── DOCUMENTACAO_TECNICA.md  → documentação técnica completa do projeto
```

## Correções aplicadas nesta versão

Durante uma revisão antes da entrega, encontramos e corrigimos os seguintes
problemas:

- **Segurança crítica:** o router `/usuarios` não exigia autenticação em
  nenhum endpoint — qualquer pessoa não logada conseguia listar, criar,
  editar (inclusive tornar-se admin) e excluir usuários. Agora todos os
  endpoints exigem `Depends(exigir_admin)`.
- **Bug de interface:** o formulário de edição de usuário em
  `/admin/usuarios/novo` tinha HTML inválido (a tag `<form>` "vazava" para
  fora da célula da tabela), então login/perfil/status não eram realmente
  enviados ao salvar. Corrigido usando o mesmo padrão `form="id"` já usado em
  produtos.
- **Página sem estilo:** `pdv/caixa.html` nunca carregava o `terminal.css`.
- **Requisito ausente:** não havia paginação em nenhuma listagem. Adicionada
  em produtos, vendas, caixa, usuários e no catálogo/fila de pedidos online.
- **Erro 500 não tratado:** excluir um usuário com caixas/vendas vinculados
  agora retorna `409` com mensagem clara, em vez de estourar um erro de
  integridade referencial sem tratamento.
- **Config/documentação divergentes:** a porta do Flask (`8080` no código vs.
  `5000` no README) foi unificada em `5000`; o CORS da API, que liberava só a
  própria API, agora libera a origem real do Flask; `api/requirements.txt`
  tinha dependências do `web/` por engano (removidas).

## Documentação técnica

Veja **`DOCUMENTACAO_TECNICA.md`** para uma explicação detalhada, arquivo
por arquivo, de cada camada do sistema (models, schemas, routers, rotas
Flask, templates, testes) e das decisões de arquitetura tomadas.
