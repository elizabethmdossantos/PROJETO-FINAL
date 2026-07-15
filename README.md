# PDV Enxuto — Projeto Integrador (Módulo III)

Sistema de gestão comercial (ERP enxuto / PDV) com back-end em **FastAPI + MySQL** (autenticação com `bcrypt` + `PyJWT`)
e front-end em **Flask + Jinja2**.

> **Status atual:** todas as funcionalidades previstas no roteiro (login por
> perfil, caixa/turno, terminal de venda, cadastro/edição de produtos,
> cancelamento de venda, filtro por período e dashboard administrativo)
> estão implementadas. Veja `DOCUMENTACAO_TECNICA.md` para o detalhamento
> completo de cada parte do código.

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
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app/main.py
```
Acesse: http://localhost:5000

### Usuários de teste (criados pelo `seed_usuarios.py`)
| Login     | Senha     | Marcar "Administrador"? | Senha administrativa            |
|-----------|-----------|--------------------------|----------------------------------|
| `admin`   | `admin123`| Sim                      | valor de `ADMIN_MASTER_KEY` no `.env` |
| `caixa1`  | `caixa123`| Não                      | —                                |

## Testes automatizados
```bash
cd tests
pip install pytest httpx pytest-cov
pytest -v
pytest --cov=app --cov-report=term-missing
```
Os testes usam SQLite em memória (não precisam do MySQL rodando). Cobrem
login, caixa, vendas (incluindo cancelamento e filtro por período) e
produtos. Veja `DOCUMENTACAO_TECNICA.md` para a lista completa de cenários.

## Endpoints principais da API

| Método | Rota                          | Quem acessa            | O que faz |
|--------|-------------------------------|--------------------------|-----------|
| POST   | `/auth/login`                  | Todos                     | Login (retorna JWT) |
| GET    | `/produtos/codigo/{cod}`       | Autenticado               | Busca produto por código (usado no terminal) |
| GET    | `/produtos`                     | Admin                      | Lista de estoque completa |
| GET    | `/produtos/{id}`                | Admin                      | Detalhe de um produto |
| POST   | `/produtos`                     | Admin                      | Cadastra produto |
| PATCH  | `/produtos/{id}`                | Admin                      | Atualiza nome/preço/estoque/status |
| POST   | `/caixa/abrir`                   | Autenticado               | Abre turno de caixa (fundo de troco) |
| GET    | `/caixa/atual`                   | Autenticado               | Turno aberto do usuário logado |
| POST   | `/caixa/fechar`                  | Autenticado               | Fecha turno e devolve resumo |
| GET    | `/caixa`                         | Admin                      | Histórico de todos os turnos |
| POST   | `/vendas`                        | Autenticado               | Registra venda (exige caixa aberto) |
| GET    | `/vendas/minhas`                 | Autenticado               | Vendas do próprio operador |
| GET    | `/vendas?data_inicio&data_fim`   | Admin                      | Todas as vendas, com operador e itens, com filtro opcional por período |
| GET    | `/vendas/{id}`                   | Dono da venda / Admin      | Detalhe de uma venda |
| POST   | `/vendas/{id}/cancelar`          | Admin                      | Cancela uma venda concluída e devolve o estoque |

## Estrutura de pastas
```
projeto-integrador-pdv/
├── api/                     → FastAPI + SQLAlchemy (MySQL) + JWT (bcrypt + PyJWT)
├── web/                     → Flask + Jinja2, consome a API via HTTP
├── tests/                   → Pytest (cobertura da camada de API)
└── DOCUMENTACAO_TECNICA.md  → documentação técnica completa do projeto
```

## Documentação técnica

Veja **`DOCUMENTACAO_TECNICA.md`** para uma explicação detalhada, arquivo
por arquivo, de cada camada do sistema (models, schemas, routers, rotas
Flask, templates, testes) e das decisões de arquitetura tomadas.
