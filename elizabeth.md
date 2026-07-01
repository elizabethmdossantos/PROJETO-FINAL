# 📝 Documentação do Sistema de Gestão Comercial
Esta documentação descreve a estrutura, rotas e o funcionamento do **Sistema de Gestão Comercial**, um sistema focado no controle de estoque, finanças e geração de relatórios.

# 🏛️ 1. Arquitetura Geral do Sistema
O sistema utiliza uma arquitetura baseada em **Microsserviços/Cliente-Servidor**, dividida em duas camadas principais:

**Front-end (Client/BFF):** Desenvolvido em Flask, roda por padrão na porta 5001. Ele é responsável por renderizar os templates HTML e fazer requisições HTTP para a API de dados.

**Back-end (API Core):** Desenvolvido em FastAPI, roda por padrão na porta 8000. Ele gerencia as regras de negócio, validações de dados (Pydantic) e a persistência no banco de dados MySQL.

# 💻 2. Camada Front-end (Flask)
O servidor Flask faz o papel de intermediário entre o usuário final (navegador) e o Back-end. Todas as requisições para o backend possuem um tempo limite (timeout) configurado para evitar travamentos.

## 📌 Rotas e Integrações

| Rota Flask | Método | Template HTML | Endpoint consumido no Back-end | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| /dashboard | GET | dashboard_admin.html | /api/resumo-diario | Carrega os indicadores do dia (faturamento, vendas e status do caixa). |
| /cadastro | GET | cadastro_produto.html | — | Renderiza o formulário de cadastro. |
| /cadastro | POST | — | /api/produtos | Envia os dados do formulário para salvar um novo produto na API. |
| /estoque | GET | estoque.html | /api/produtos e /api/movimentacoes | Lista os produtos atuais e o histórico consolidado de entradas e saídas. |
| /financeiro | GET | financeiro.html | /api/financeiro-resumo | Exibe o resumo financeiro (contas a pagar, a receber e saldo). |
| /relatorios | GET | relatorios.html | — | Tela com opções de exportação de dados. |
| /relatorios/faturamento | POST | — | /api/relatorios/exportar | Solicita à API o download do relatório de faturamento em PDF. |
| /relatorios/vendas | POST | — | /api/relatorios/exportar | Solicita à API o download do relatório de vendas em Excel (.xlsx). |

# ⚙️ 3. Camada Back-end (FastAPI)A API centraliza o acesso ao banco de dados e valida rigorosamente as informações de entrada usando modelos Pydantic.

## 🔒 Validação de Dados (Pydantic Model)
O modelo ProdutoCadastro garante a integridade dos dados antes de qualquer inserção no banco:

**nome:** Texto obrigatório (2 a 100 caracteres).
**codigo:** Código identificador (1 a 50 caracteres). Deve ser único.preco_custo / 
**preco_venda:** Valores numéricos decimais (float), obrigatoriamente maiores ou iguais a $0.00$.
**categoria:** Texto obrigatório (2 a 50 caracteres).
**quantidade:** Valor inteiro (int), obrigatoriamente maior ou igual a $0$.

## 🛣️ Endpoints da API

``POST /api/produtos``<br>
**Objetivo:** Cadastrar um produto e gerar a movimentação inicial de estoque.<br>
**Lógica:** Executa duas operações dentro de uma transação SQL (commit/rollback). Primeiro insere o produto na tabela produtos, captura o ID gerado e, em seguida, insere um registro do tipo 'compra' na tabela movimentacoes_estoque.<br>
**Tratamento de Erro:** Caso o código do produto já exista, retorna Status 400 (Bad Request).

``GET /api/produtos``<br>
**Objetivo:** Retornar a lista de produtos ordenada alfabeticamente.<br>
**Query SQL:** SELECT nome, quantidade FROM produtos ORDER BY nome ASC (Nota: Há um pequeno erro de digitação no seu código original: ASCE em vez de ASC, que deve ser corrigido para evitar falha de sintaxe no banco).

``GET /api/movimentacoes``<br>
**Objetivo:** Retornar o consolidado de entradas e saídas por produto para a tela de estoque.<br>
**Lógica:** Utiliza um JOIN entre as tabelas de movimentação e produtos combinando as funções SUM e CASE WHEN para agrupar as quantidades vendidas e compradas.

``GET /api/resumo-diario``<br>
**Objetivo:** Alimentar os cards do Dashboard com dados do dia atual (CURDATE()).<br>
**Fallback:** Caso as tabelas ainda não existam ou estejam vazias, captura a exceção e retorna valores zerados mockados, impedindo que a tela do usuário trave.

``GET /api/financeiro-resumo``<br>
**Objetivo:** Calcular valores de contas_receber e contas_pagar com status 'pendente'.<br>
**Lógica:** Retorna o saldo consolidado subtraindo as contas a pagar das contas a receber. Também possui fallback para retornar valores zerados caso as tabelas não estejam criadas.

``GET /api/relatorios/exportar``<br>
**Objetivo:** Exportar arquivos de relatórios dinamicamente.<br>
**Parâmetros:** tipo_relatorio (faturamento/itens_vendidos) e formato (pdf/xlsx).<br>
**Status Atual:** Em desenvolvimento. Se o arquivo físico não for encontrado no servidor, retorna um erro controlado com Status 511 para avisar o Front-end.

# 🗄️ 4. Banco de Dados (MySQL)
A conexão é gerenciada pelo módulo obter_conexao(), que utiliza a biblioteca mysql.connector.

# 📐 Estrutura de Tabelas Inferida
Com base nas queries executadas no código, o banco de dados sistema_gestao_empresa possui a seguinte estrutura de tabelas:

**produtos:** Armazena os dados cadastrais (id, nome, codigo, preco_custo, preco_venda, categoria, quantidade).<br>
**movimentacoes_estoque:** Histórico de entradas e saídas (id, produto_id, tipo ['compra', 'venda'], quantidade, data_criacao).<br>
**contas_receber:** Fluxo de caixa de entrada futuro/pendente (valor, status).<br>
**contas_pagar:** Fluxo de caixa de saída futuro/pendente (valor, status).