# 🎓 ERP (Enterprise Resource Planning) - Sistema de Gestão Integrado

## Login - Responsáveis: Vitor e Guilherme
## Identidade Visual - Responsável: Levi

## 1. Módulo PDV (Frente de Caixa) - Responsável: Gustavo

Esta área deve ser limpa, rápida e preferencialmente operável por teclado.

### Tela de Venda (PDV):

Campo de busca rápida de produto (por nome, código ou leitor de código de barras).

Lista de itens da venda atual (com quantidade, valor unitário e subtotal).

Painel lateral com o Total Geral em destaque.

Atalhos para fechar a venda (Dinheiro, Cartão, Pix, etc.).

Automação: Ao finalizar a venda, o sistema dispara a baixa automática no estoque e lança o valor no caixa do dia.

### Fluxo de Caixa (Abertura/Fechamento):

Tela simples para informar o saldo inicial (fundo de caixa).

Tela de Fechamento de Caixa mostrando o esperado (vendas do dia) vs. o real em dinheiro/cartão, com campo para registrar sangrias (retiradas) ou suprimentos (entradas).

## 2. Módulo Administrativo (Backoffice)

### 📊 Painel Geral (Dashboard)
Resumo do dia: faturamento, quantidade de vendas e status do caixa (aberto/fechado).

Alertas rápidos: produtos com estoque crítico (mínimo) e contas que vencem hoje.

### 📦 Cadastro e Estoque
Produtos: Listagem e formulário de cadastro (Nome, código de barras, preço de custo, preço de venda, categoria e estoque atual/mínimo).

Movimentação de Estoque: Histórico de entradas (compras/ajustes) e saídas (vendas/perdas), para auditoria caso algo destoe da baixa automática.

### 💰 Financeiro
Contas a Receber: Lançamentos vindos automaticamente do PDV (especialmente vendas a prazo ou cartões) e cadastros manuais.

Contas a Pagar: Registro de despesas fixas (aluguel, luz) e variáveis (compras de fornecedores).

Fluxo de Caixa Consolidado: Visão geral de entradas e saídas financeiras.

### 📈 Relatórios
Relatório de Faturamento por Período: Filtro por data (hoje, 7 dias, 30 dias ou personalizado) mostrando o total faturado, lucratividade bruta e métodos de pagamento mais utilizados.

Relatório de Itens Vendidos: Ranking dos produtos mais vendidos (curva ABC) para ajudar nas compras.
