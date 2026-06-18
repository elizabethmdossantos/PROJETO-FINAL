# 🎓 Sistema de Gestão Acadêmica com RBAC

Projeto Integrador desenvolvido para o **Módulo III do curso de Informática para Internet (Ano 2026)**. A aplicação consiste em um sistema de gestão escolar utilizando uma arquitetura distribuída com controle de acesso baseado em perfis (**RBAC**).

---

## 📐 Arquitetura Técnica Obrigatória

O projeto segue estritamente a separação de responsabilidades exigida:
* **Front-end:** HTML5, CSS3 (Bootstrap/Tailwind) e JavaScript Responsivo.
* **Aplicação Web (Flask):** Camada de interação com o usuário, consumindo a API via requisições HTTP e renderizando as telas dinamicamente com **Jinja2**.
* **API REST (FastAPI):** Núcleo do sistema. Concentra as regras de negócio, validação de dados com **Pydantic**, persistência de dados e autenticação por token **JWT**.
* **Banco de Dados (MySQL):** Banco relacional normalizado com chaves estrangeiras e relacionamentos N:N (ex: Alunos ⇄ Disciplinas).
* **Testes Automatizados (Pytest):** Suíte de testes com cobertura mínima de 70% na camada da API, utilizando fixtures e mocks.
