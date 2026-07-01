document.addEventListener("DOMContentLoaded", () => {
    console.log("Interface do Sistema Comercial carregada com sucesso.");

    // Executa funções cosméticas ou de validação visual leve na interface
    configurarAlertas();
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
        // Define que após 4 segundos o alerta vai começar a desaparecer
        setTimeout(() => {
            alerta.style.transition = "opacity 0.5s ease";
            alerta.style.opacity = "0";
            
            // Remove o elemento do HTML após o término da animação
            setTimeout(() => {
                alerta.remove();
            }, 500);
        }, 4000);
    });
}