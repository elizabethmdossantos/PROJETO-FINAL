(function () {
  const inputCodigo = document.getElementById("codigo-produto");
  const mensagemScanner = document.getElementById("mensagem-scanner");
  const corpoCarrinho = document.getElementById("corpo-carrinho");
  const valorTotalEl = document.getElementById("valor-total");
  const botaoFinalizar = document.getElementById("botao-finalizar");
  const mensagemVenda = document.getElementById("mensagem-venda");
  const botoesPagamento = document.querySelectorAll(".opcao-pagamento");

  if (!inputCodigo) return;

  let carrinho = [];
  let formaPagamento = null;

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

  inputCodigo.addEventListener("keydown", async (evento) => {
    if (evento.key !== "Enter") return;
    evento.preventDefault();

    const codigo = inputCodigo.value.trim();
    if (!codigo) return;

    try {
      const produto = await buscarProduto(codigo);
      const existente = carrinho.find((item) => item.codigo === produto.codigo);
      if (existente) {
        existente.quantidade += 1;
      } else {
        carrinho.push({
          codigo: produto.codigo,
          nome: produto.nome,
          preco: parseFloat(produto.preco),
          quantidade: 1,
        });
      }
      mostrarMensagemScanner(`Adicionado: ${produto.nome}`, "sucesso");
      renderizarCarrinho();
    } catch (erro) {
      mostrarMensagemScanner(erro.message, "erro");
    }

    inputCodigo.value = "";
    inputCodigo.focus();
  });

  corpoCarrinho.addEventListener("click", (evento) => {
    const botao = evento.target.closest(".botao-remover");
    if (!botao) return;
    const indice = parseInt(botao.dataset.indice, 10);
    carrinho.splice(indice, 1);
    renderizarCarrinho();
  });

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
