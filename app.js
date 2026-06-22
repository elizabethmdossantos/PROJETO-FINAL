// ==========================================
// "BANCO DE DADOS" EM LOCALSTORAGE
// ==========================================
const BD = {
    obter(chave, padrao = []) {
        const dados = localStorage.getItem(chave);
        return dados ? JSON.parse(dados) : padrao;
    },
    salvar(chave, dados) {
        localStorage.setItem(chave, JSON.stringify(dados));
    }
};

// Inicialização do caixa se não existir
if (!localStorage.getItem('caixa')) {
    BD.salvar('caixa', { faturamento: 0, vendas_count: 0, status: 'Aberto' });
}

// ==========================================
// ROTEAMENTO DE FUNÇÕES POR PÁGINA
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
    const path = window.location.pathname;

    if (path.includes("cadastro.html")) {
        inicializarCadastro();
    } else if (path.includes("estoque.html")) {
        inicializarEstoque();
    } else if (path.includes("index.html") || path.endsWith("/")) {
        inicializarDashboard();
    }
});

// ==========================================
// 1. LÓGICA DA PÁGINA DE CADASTRO
// ==========================================
function inicializarCadastro() {
    const form = document.querySelector("form");
    if (!form) return;

    form.addEventListener("submit", (e) => {
        e.preventDefault();

        // Captura os dados do formulário
        const novoProduto = {
            id: Date.now(), // ID único baseado no timestamp
            nome: document.getElementById("nome-produto").value,
            codigo: document.getElementById("codigo-produto").value,
            precoCusto: parseFloat(document.getElementById("preco-custo").value),
            precoVenda: parseFloat(document.getElementById("preco-venda").value),
            categoria: document.getElementById("categoria").value,
            quantidade: parseInt(document.getElementById("quantidade").value)
        };

        // Salva o produto no "Banco de Dados"
        const produtos = BD.obter("produtos");
        produtos.push(novoProduto);
        BD.salvar("produtos", produtos);

        // Registra a movimentação inicial de compra/entrada
        const movimentacoes = BD.obter("movimentacoes");
        movimentacoes.push({
            id: Date.now() + 1,
            produtoNome: novoProduto.nome,
            tipo: "compra",
            quantidade: novoProduto.quantidade,
            data: new Date().toLocaleDateString('pt-BR')
        });
        BD.salvar("movimentacoes", movimentacoes);

        alert("Produto cadastrado com sucesso!");
        form.reset();
    });
}

// ==========================================
// 2. LÓGICA DA PÁGINA DE ESTOQUE
// ==========================================
function inicializarEstoque() {
    const produtos = BD.obter("produtos");
    const movimentacoes = BD.obter("movimentacoes");

    // Seleciona as listas no HTML pelo índice/posição
    const listas = document.querySelectorAll(".lista-custom");
    if (listas.length < 2) return;

    const listaProdutos = listas[0];
    const listaMovimentacoes = listas[1];

    // Renderiza Produtos
    listaProdutos.innerHTML = "";
    if (produtos.length === 0) {
        listaProdutos.innerHTML = "<li>Nenhum produto cadastrado.</li>";
    } else {
        produtos.forEach(p => {
            listaProdutos.innerHTML += `<li>${p.nome} (Cód: ${p.codigo}) - <b>${p.quantidade} un.</b></li>`;
        });
    }

    // Renderiza Movimentações
    listaMovimentacoes.innerHTML = "";
    if (movimentacoes.length === 0) {
        listaMovimentacoes.innerHTML = "<li>Nenhuma movimentação registrada.</li>";
    } else {
        // Exibe as últimas 5 movimentações
        movimentacoes.slice(-5).reverse().forEach(m => {
            const cor = m.tipo === "compra" ? "var(--success)" : "#ef4444";
            const sinal = m.tipo === "compra" ? "+" : "-";
            listaMovimentacoes.innerHTML += `
                <li>${m.produtoNome}: <span style="color: ${cor}">${sinal}${m.quantidade} (${m.tipo})</span> <small style="color:var(--text-muted); float:right">${m.data}</small></li>
            `;
        });
    }
}

// ==========================================
// 3. LÓGICA DO DASHBOARD (INDEX)
// ==========================================
function inicializarDashboard() {
    const caixa = BD.obter("caixa", { faturamento: 0, vendas_count: 0, status: 'Aberto' });
    
    // Captura os elementos de texto nos cards
    const cards = document.querySelectorAll(".item p");
    if (cards.length < 3) return;

    // Atualiza os valores na tela dinamicamente
    cards[0].innerText = `R$ ${caixa.faturamento.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
    cards[1].innerText = caixa.vendas_count;
    cards[2].innerText = caixa.status;
    cards[2].className = caixa.status === "Aberto" ? "status-aberto" : "";
}