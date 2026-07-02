document.addEventListener("DOMContentLoaded", () => {
    console.log("Interface do Sistema Comercial carregada com sucesso.");

    // Executa funções cosméticas ou de validação visual leve na interface
    configurarAlertas();

    // Inicializa o PDV caso o usuário esteja na tela de vendas
    if (document.getElementById("tabela-carrinho")) {
        inicializarPDV();
    }
});

/**
 * Esconde o formulário de login e exibe a tela de cadastro.
 */
function showRegister() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    if (loginForm && registerForm) {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
    }
}

/**
 * Esconde o formulário de cadastro e exibe a tela de login.
 */
function showLogin() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    if (loginForm && registerForm) {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
    }
}

/**
 * Faz com que as mensagens de alerta (Flash Messages) do Flask sumam 
 * suavemente após alguns segundos, melhorando a experiência do usuário.
 */
function configurarAlertas() {
    const alertas = document.querySelectorAll(".alert");
    
    alertas.forEach(alerta => {
        setTimeout(() => {
            alerta.style.transition = "opacity 0.5s ease";
            alerta.style.opacity = "0";
            
            setTimeout(() => {
                alerta.remove();
            }, 500);
        }, 4000);
    });
}

// =========================================================================
// MÓDULO DO FRENTE DE CAIXA (PDV) - NOVO
// =========================================================================

// Variável global para armazenar os itens que estão no carrinho do PDV
let carrinho = [];

function inicializarPDV() {
    const btnAdicionar = document.getElementById("btn-adicionar-item");
    const btnFinalizar = document.getElementById("btn-finalizar-venda");

    if (btnAdicionar) {
        btnAdicionar.addEventListener("click", adicionarItemAoCarrinho);
    }

    if (btnFinalizar) {
        btnFinalizar.addEventListener("click", finalizarVendaPDV);
    }
}

/**
 * Captura o produto selecionado no select do HTML e o joga para o carrinho
 */
function adicionarItemAoCarrinho() {
    const selectProduto = document.getElementById("select-produto");
    const inputQuantidade = document.getElementById("input-quantidade");

    if (!selectProduto || !inputQuantidade) return;

    const produtoId = parseInt(selectProduto.value);
    const quantidade = parseInt(inputQuantidade.value);

    if (isNaN(produtoId) || isNaN(quantidade) || quantidade <= 0) {
        alert("Selecione um produto válido e informe uma quantidade maior que zero.");
        return;
    }

    // Captura metadados do option selecionado (usando atributos data-* do HTML)
    const optionSelecionado = selectProduto.options[selectProduto.selectedIndex];
    const nomeProduto = optionSelecionado.text;
    const precoVenda = parseFloat(optionSelecionado.getAttribute("data-preco") || 0);

    // Verifica se o item já existe no carrinho para apenas somar a quantidade
    const itemExistente = carrinho.find(item => item.produto_id === produtoId);

    if (itemExistente) {
        itemExistente.quantidade += quantidade;
    } else {
        carrinho.push({
            produto_id: produtoId,
            nome: nomeProduto,
            preco_unitario: precoVenda,
            quantidade: quantidade
        });
    }

    // Limpa o campo de quantidade e atualiza a tabela na tela
    inputQuantidade.value = 1;
    atualizarGradePDV();
}

/**
 * Renderiza as linhas da tabela do carrinho e calcula o valor total geral
 */
function atualizarGradePDV() {
    const tabelaCorpo = document.getElementById("tabela-carrinho");
    const textoTotal = document.getElementById("total-venda");
    
    if (!tabelaCorpo) return;

    tabelaCorpo.innerHTML = "";
    let totalGeral = 0;

    carrinho.forEach((item, index) => {
        const subtotal = item.preco_unitario * item.quantidade;
        totalGeral += subtotal;

        const linha = document.createElement("tr");
        linha.className = "border-b hover:bg-gray-50"; // Tailwind styling
        linha.innerHTML = `
            <td class="p-3">${item.nome}</td>
            <td class="p-3 text-center">${item.quantidade}</td>
            <td class="p-3 text-right">R$ ${item.preco_unitario.toFixed(2)}</td>
            <td class="p-3 text-right font-medium">R$ ${subtotal.toFixed(2)}</td>
            <td class="p-3 text-center">
                <button onclick="removerItemPDV(${index})" class="text-red-500 hover:text-red-700 font-bold">✕</button>
            </td>
        `;
        tabelaCorpo.appendChild(linha);
    });

    if (textoTotal) {
        textoTotal.innerText = `R$ ${totalGeral.toFixed(2)}`;
    }
}

/**
 * Remove um item específico do carrinho através do índice do array
 */
function removerItemPDV(index) {
    carrinho.splice(index, 1);
    atualizarGradePDV();
}

/**
 * Envia o payload final do carrinho em formato JSON para o backend do Flask
 */
function finalizarVendaPDV() {
    if (carrinho.length === 0) {
        alert("Não é possível finalizar uma venda com o carrinho vazio.");
        return;
    }

    // Mapeia o carrinho para bater exatamente com o schema 'VendaCadastro' esperado pela API
    const payload = {
        itens: carrinho.map(item => ({
            produto_id: item.produto_id,
            quantidade: item.quantidade
        }))
    };

    const btnFinalizar = document.getElementById("btn-finalizar-venda");
    btnFinalizar.disabled = true;
    btnFinalizar.innerText = "Processando...";

    fetch('/pdv/confirmar-venda', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(async response => {
        const dados = await response.json();
        if (response.ok) {
            alert("✓ Venda efetuada com sucesso! Estoque atualizado.");
            carrinho = [];
            atualizarGradePDV();
            // Recarrega a página após 1s para atualizar os estoques visuais do select
            setTimeout(() => window.location.reload(), 1000);
        } else {
            alert(`Falha ao concluir venda: ${dados.mensagem || "Erro interno."}`);
            btnFinalizar.disabled = false;
            btnFinalizar.innerText = "Confirmar Venda (F2)";
        }
    })
    .catch(error => {
        console.error("Erro na requisição HTTP:", error);
        alert("Erro de comunicação: O servidor Flask ou a API estão indisponíveis.");
        btnFinalizar.disabled = false;
        btnFinalizar.innerText = "Confirmar Venda (F2)";
    });
}

// =========================================================================
// INTERCEPTAÇÃO E ENVIO REAL DO FORMULÁRIO DE CADASTRO DE USUÁRIOS
// =========================================================================

document.addEventListener("DOMContentLoaded", () => {
    // Localiza o formulário de cadastro dentro da interface de login
    const formRegistro = document.querySelector("#registerForm form") || document.getElementById("form-registro");

    if (formRegistro) {
        formRegistro.addEventListener("submit", async (e) => {
            e.preventDefault(); // Impede o HTML de atualizar a página antes do tempo

            // Captura os dados inseridos pelos inputs do seu HTML
            // Nota: Se os IDs forem levemente diferentes no seu HTML, ajuste-os aqui!
            const inputUsername = document.getElementById("reg-username") || document.querySelector("input[type='text']");
            const inputPassword = document.getElementById("reg-password") || document.querySelector("input[type='password']");
            const selectPerfil = document.getElementById("reg-perfil") || document.querySelector("select");

            if (!inputUsername || !inputPassword) {
                alert("Erro ao ler os campos do formulário. Verifique os IDs no HTML.");
                return;
            }

            const username = inputUsername.value.trim();
            const password = inputPassword.value;
            const perfil = selectPerfil ? selectPerfil.value : "vendedor";

            if (!username || !password) {
                alert("Por favor, preencha todos os campos obrigatórios.");
                return;
            }

            try {
                // Dispara a requisição para a ponte /registrar do Flask
                const response = await fetch("/registrar", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ username, password, perfil })
                });

                const dados = await response.json();

                if (response.ok) {
                    alert("✓ Usuário cadastrado com sucesso!");
                    
                    // Limpa o formulário
                    formRegistro.reset();
                    
                    // Executa a sua função cosmética existente para voltar à tela de login
                    if (typeof showLogin === "function") {
                        showLogin();
                    } else {
                        window.location.reload();
                    }
                } else {
                    // Mostra o erro retornado da sua FastAPI (ex: "Este nome de usuário já está em uso.")
                    alert(`Falha no cadastro: ${dados.message || "Erro desconhecido."}`);
                }
            } catch (error) {
                console.error("Erro na comunicação com o servidor:", error);
                alert("Erro de rede: O servidor Flask ou a API central estão indisponíveis.");
            }
        });
    }
});