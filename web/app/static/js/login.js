document.addEventListener("DOMContentLoaded", function () {
  const chave = document.getElementById("e_admin");
  const campoAdmin = document.getElementById("campo-senha-admin");
  const inputSenhaAdmin = document.getElementById("senha_admin");
  const form = document.getElementById("form-login");
  const relogio = document.getElementById("relogio-recibo");

  function atualizarModo() {
    const ehAdmin = chave.checked;
    campoAdmin.classList.toggle("aberto", ehAdmin);
    form.classList.toggle("modo-admin", ehAdmin);
    inputSenhaAdmin.required = ehAdmin;
    if (!ehAdmin) {
      inputSenhaAdmin.value = "";
    }
  }

  chave.addEventListener("change", atualizarModo);
  atualizarModo();

  function atualizarRelogio() {
    if (!relogio) return;
    const agora = new Date();
    const hh = String(agora.getHours()).padStart(2, "0");
    const mm = String(agora.getMinutes()).padStart(2, "0");
    const ss = String(agora.getSeconds()).padStart(2, "0");
    relogio.textContent = `${hh}:${mm}:${ss}`;
  }

  atualizarRelogio();
  setInterval(atualizarRelogio, 1000);
});
