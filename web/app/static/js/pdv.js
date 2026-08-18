(function () {
  const inputCodigo = document.getElementById("codigo-produto");
  const mensagemScanner = document.getElementById("mensagem-scanner");
  const corpoCarrinho = document.getElementById("corpo-carrinho");
  const valorTotalEl = document.getElementById("valor-total");
  const botaoFinalizar = document.getElementById("botao-finalizar");
  const mensagemVenda = document.getElementById("mensagem-venda");
  const botoesPagamento = document.querySelectorAll(".opcao-pagamento");

  const buscaProdutoMenu = document.getElementById("busca-produto-menu");
  const listaMenuProdutos = document.getElementById("lista-menu-produtos");

  const modalQuantidade = document.getElementById("modal-quantidade");
  const modalQuantidadeTitulo = document.getElementById("modal-quantidade-titulo");
  const modalQuantidadeProduto = document.getElementById("modal-quantidade-produto");
  const modalQuantidadeInput = document.getElementById("modal-quantidade-input");
  const modalQuantidadeCancelar = document.getElementById("modal-quantidade-cancelar");
  const modalQuantidadeConfirmar = document.getElementById("modal-quantidade-confirmar");

  if (!inputCodigo) return;

  let carrinho = [];
  let formaPagamento = null;
  let produtoPendente = null; // produto aguardando confirmação de quantidade no modal

  function formatarMoeda(valor) {
    return "R$ " + valor.toFixed(2).replace(".", ",");
  }

  function totalCarrinho() {
    return carrinho.reduce((soma, item) => soma + item.preco * item.quantidade, 0);
  }

  function atualizarBotaoFinalizar() {
    botaoFinalizar.disabled = !(carrinho.length > 0 && formaPagamento);
  }

  function renderizarCarrinho() {
    if (carrinho.length === 0) {
      corpoCarrinho.innerHTML =
        '<tr id="linha-vazia"><td colspan="6" class="carrinho-vazio">Nenhum item ainda — digite um código acima.</td></tr>';
    } else {
      corpoCarrinho.innerHTML = carrinho
        .map(
          (item, indice) => `
        <tr>
          <td><span class="codigo-mono">${item.codigo}</span></td>
          <td>${item.nome}</td>
          <td>${item.quantidade}</td>
          <td>${formatarMoeda(item.preco)}</td>
          <td>${formatarMoeda(item.preco * item.quantidade)}</td>
          <td><button type="button" class="botao-remover" data-indice="${indice}">Remover</button></td>
        </tr>`
        )
        .join("");
    }
    valorTotalEl.textContent = formatarMoeda(totalCarrinho());
    atualizarBotaoFinalizar();
  }

  function mostrarMensagemScanner(texto, tipo) {
    mensagemScanner.textContent = texto;
    mensagemScanner.className = "mensagem-scanner " + (tipo || "");
  }

  async function buscarProduto(codigo) {
    const resposta = await fetch("/pdv/terminal/buscar-produto", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codigo: codigo }),
    });
    const dados = await resposta.json();
    if (!resposta.ok) {
      throw new Error(dados.detail || "Produto não encontrado.");
    }
    return dados;
  }

  // ---------------------------------------------------------------------
  // Modal de quantidade — abre sempre antes de um produto entrar no
  // carrinho, seja vindo do campo de código, seja do menu lateral.
  // ---------------------------------------------------------------------

  function abrirModalQuantidade(produto) {
    produtoPendente = produto;
    modalQuantidadeTitulo.textContent = "Quantas unidades?";
    modalQuantidadeProduto.textContent = `${produto.nome} — ${formatarMoeda(produto.preco)} cada`;
    modalQuantidadeInput.value = "1";
    modalQuantidade.classList.remove("modal-oculto");
    setTimeout(() => {
      modalQuantidadeInput.focus();
      modalQuantidadeInput.select();
    }, 0);
  }

  function fecharModalQuantidade() {
    produtoPendente = null;
    modalQuantidade.classList.add("modal-oculto");
    inputCodigo.focus();
  }

  function adicionarAoCarrinho(produto, quantidade) {
    const existente = carrinho.find((item) => item.codigo === produto.codigo);
    if (existente) {
      existente.quantidade += quantidade;
    } else {
      carrinho.push({
        codigo: produto.codigo,
        nome: produto.nome,
        preco: parseFloat(produto.preco),
        quantidade: quantidade,
      });
    }
    mostrarMensagemScanner(`Adicionado: ${quantidade}x ${produto.nome}`, "sucesso");
    renderizarCarrinho();
  }

  function confirmarModalQuantidade() {
    if (!produtoPendente) return;
    const quantidade = parseInt(modalQuantidadeInput.value, 10);
    if (!quantidade || quantidade < 1) {
      modalQuantidadeInput.focus();
      return;
    }
    adicionarAoCarrinho(produtoPendente, quantidade);
    fecharModalQuantidade();
  }

  modalQuantidadeConfirmar.addEventListener("click", confirmarModalQuantidade);
  modalQuantidadeCancelar.addEventListener("click", fecharModalQuantidade);
  modalQuantidadeInput.addEventListener("keydown", (evento) => {
    if (evento.key === "Enter") {
      evento.preventDefault();
      confirmarModalQuantidade();
    } else if (evento.key === "Escape") {
      evento.preventDefault();
      fecharModalQuantidade();
    }
  });
  modalQuantidade.addEventListener("click", (evento) => {
    if (evento.target === modalQuantidade) fecharModalQuantidade();
  });

  // ---------------------------------------------------------------------
  // Campo de código — busca o produto e abre o modal de quantidade.
  // ---------------------------------------------------------------------

  inputCodigo.addEventListener("keydown", async (evento) => {
    if (evento.key !== "Enter") return;
    evento.preventDefault();

    const codigo = inputCodigo.value.trim();
    if (!codigo) return;

    try {
      const produto = await buscarProduto(codigo);
      abrirModalQuantidade(produto);
      mostrarMensagemScanner("", "");
    } catch (erro) {
      mostrarMensagemScanner(erro.message, "erro");
    }

    inputCodigo.value = "";
  });

  corpoCarrinho.addEventListener("click", (evento) => {
    const botao = evento.target.closest(".botao-remover");
    if (!botao) return;
    const indice = parseInt(botao.dataset.indice, 10);
    carrinho.splice(indice, 1);
    renderizarCarrinho();
  });

  // ---------------------------------------------------------------------
  // Menu lateral de produtos cadastrados — evita ter que decorar códigos.
  // Clicar num item abre o mesmo modal de quantidade.
  // ---------------------------------------------------------------------

  if (listaMenuProdutos) {
    listaMenuProdutos.addEventListener("click", (evento) => {
      const item = evento.target.closest(".item-menu-produto");
      if (!item) return;
      abrirModalQuantidade({
        codigo: item.dataset.codigo,
        nome: item.dataset.nome,
        preco: parseFloat(item.dataset.preco),
      });
    });
  }

  if (buscaProdutoMenu) {
    buscaProdutoMenu.addEventListener("input", () => {
      const termo = buscaProdutoMenu.value.trim().toLowerCase();
      const itens = listaMenuProdutos.querySelectorAll(".item-menu-produto");
      itens.forEach((item) => {
        const combina = !termo || item.dataset.busca.includes(termo);
        item.style.display = combina ? "" : "none";
      });
    });
  }

  // ---------------------------------------------------------------------
  // Forma de pagamento e finalização da venda.
  // ---------------------------------------------------------------------

  botoesPagamento.forEach((botao) => {
    botao.addEventListener("click", () => {
      formaPagamento = botao.dataset.forma;
      botoesPagamento.forEach((b) => b.classList.remove("selecionada"));
      botao.classList.add("selecionada");
      atualizarBotaoFinalizar();
    });
  });

  botaoFinalizar.addEventListener("click", async () => {
    botaoFinalizar.disabled = true;
    mensagemVenda.textContent = "";
    mensagemVenda.className = "mensagem-scanner";

    const payload = {
      forma_pagamento: formaPagamento,
      itens: carrinho.map((item) => ({
        codigo_produto: item.codigo,
        quantidade: item.quantidade,
      })),
    };

    try {
      const resposta = await fetch("/pdv/terminal/finalizar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const dados = await resposta.json();
      if (!resposta.ok) {
        throw new Error(dados.detail || "Não foi possível finalizar a venda.");
      }

      mensagemVenda.textContent = `Venda #${dados.id} registrada com sucesso!`;
      mensagemVenda.className = "mensagem-scanner sucesso";

      carrinho = [];
      formaPagamento = null;
      botoesPagamento.forEach((b) => b.classList.remove("selecionada"));
      renderizarCarrinho();
    } catch (erro) {
      mensagemVenda.textContent = erro.message;
      mensagemVenda.className = "mensagem-scanner erro";
    } finally {
      atualizarBotaoFinalizar();
      inputCodigo.focus();
    }
  });

  renderizarCarrinho();
})();
