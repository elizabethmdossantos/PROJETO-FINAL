# 📋 Sistema de Gestão Comercial (ERP)

O **Sistema de Gestão Comercial** é uma solução ERP unificada projetada para otimizar operações comerciais, desde o atendimento de ponta no balcão até o controle gerencial estratégico de retaguarda. 

O sistema adota uma arquitetura desacoplada, dividindo-se em um front-end administrativo/operacional dinâmico e um back-end robusto focado em regras de negócio complexas e persistência de dados.

---

## 🏗️ Arquitetura e Tecnologias

* **Front-end (Administrativo & Operacional):** Flask (Python) + HTML5/CSS3/JavaScript
* **Back-end (API & Regras de Negócio):** FastAPI (Python)
* **Banco de Dados:** Banco de Dados Relacional (SQL)
* **Controle de Versão:** Git & GitHub

---

## 🚀 Módulos do Sistema e Divisão de Escopo

### 🎨 1. Identidade Visual (Responsável: Levi)
* Interface profissional, ergonômica e intuitiva focada na experiência do operador do dia a dia.
* Guia de estilos unificado (cores, logotipos, tipografia e componentes customizados).

### 🔒 2. Autenticação e Segurança (Responsáveis: Guilherme e Vitor)
* Controle de acesso restrito através de telas dedicadas de Login e Cadastro de Usuários.
* Validação de permissões para operadores e administradores.

### 🛒 3. Módulo PDV - Frente de Caixa (Responsável: Gustavo)
* **Tela de Vendas:** Campo de pesquisa multifuncional (código de barras, código interno ou nome), grid de itens em tempo real e painel lateral de alta visibilidade com o Total Geral.
* **Atalhos Teclado:** Fechamento rápido mapeado para Dinheiro, Cartão ou PIX.
* **Fluxo de Caixa:** Abertura com saldo inicial (troco), controle de Sangrias/Suprimentos e painel de fechamento para conciliação física vs. esperada.

### 📊 4. Módulos de Retaguarda (Responsável: Elizabeth)
* **Dashboard Gerencial:** Interface para monitoramento do faturamento e volume de vendas. Conta com arquitetura de *fallback* resiliente, que evita a quebra da tela caso ocorram oscilações no banco de dados.
* **Gestão de Estoque:** Telas para cadastro e listagem de produtos com gatilho de movimentação para o fluxo de 'compra'.
* **Resumo Financeiro:** Motor de cálculo dinâmico para consolidar o saldo previsto da empresa com base em contas a pagar e a receber pendentes.

---

## 🛠️ Como Executar o Projeto (Em Desenvolvimento)

### Pré-requisitos
* Python 3.10+
* Pip (Gerenciador de pacotes do Python)

### 1. Clonar o Repositório
```bash
git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
cd seu-repositorio
