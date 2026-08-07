#!/usr/bin/env python3
"""Render static previews of loja templates using Jinja2 and sample data.
Generates files under web/previews/.
"""
import os
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
TEMPLATES_DIR = os.path.join(ROOT, "web", "app", "templates")
OUT_DIR = os.path.join(ROOT, "web", "previews")

os.makedirs(OUT_DIR, exist_ok=True)

env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)

# Provide minimal Flask-like helpers used by the templates
def _url_for(endpoint, **kwargs):
    if endpoint == 'static':
        filename = kwargs.get('filename', '')
        # return a file:// absolute path to allow local preview loading
        static_path = os.path.join(ROOT, 'web', 'app', 'static', filename)
        # return a path relative to the previews output folder so browsers can load assets
        rel = os.path.relpath(static_path, OUT_DIR).replace('\\', '/')
        return rel
    # simple fallback
    return f"/{endpoint}"

def _get_flashed_messages(with_categories=False):
    return []

env.globals['url_for'] = _url_for
env.globals['get_flashed_messages'] = _get_flashed_messages

sample_produtos = [
    {"id": 1, "codigo": "A001", "nome": "Arroz 5kg", "preco": 25.9, "disponibilidade": "disponivel"},
    {"id": 2, "codigo": "B002", "nome": "Feijão 1kg", "preco": 8.5, "disponibilidade": "poucas_unidades"},
    {"id": 3, "codigo": "C003", "nome": "Leite 1L", "preco": 4.75, "disponibilidade": "indisponivel"},
]

sample_itens = [
    {"produto_id": 1, "nome": "Arroz 5kg", "preco": 25.9, "quantidade": 1, "subtotal": 25.9},
    {"produto_id": 2, "nome": "Feijão 1kg", "preco": 8.5, "quantidade": 2, "subtotal": 17.0},
]

subtotal = sum(i["subtotal"] for i in sample_itens)
taxa_servico = round(subtotal * 0.08, 2)
total = round(subtotal + taxa_servico, 2)

pedido = {
    "numero_pedido": "F260802A1B2C",
    "nome_cliente": "Maria Silva",
    "status": "aguardando_retirada",
    "subtotal": subtotal,
    "taxa_servico_valor": taxa_servico,
    "valor_total": total,
    "itens": [
        {"nome_produto": it["nome"], "quantidade": it["quantidade"], "preco_unitario": it["preco"], "subtotal": it["subtotal"]}
        for it in sample_itens
    ],
    "taxa_cancelamento_percentual": 15,
    "taxa_cancelamento_valor": round(total * 0.15, 2),
    "valor_reembolsado": round(total - round(total * 0.15, 2), 2),
}

contexts = {
    "catalogo.html": {"produtos": sample_produtos, "busca": "", "quantidade_no_carrinho": 3},
    "carrinho.html": {"itens": sample_itens, "subtotal": subtotal, "taxa_servico": taxa_servico, "total": total},
    "checkout.html": {"itens": sample_itens, "subtotal": subtotal, "taxa_servico": taxa_servico, "total": total},
    "comprovante.html": {"pedido": pedido, "telefone": "82999990000"},
    "consultar.html": {},
}

templates_to_render = [
    ("loja/catalogo.html", "catalogo.html"),
    ("loja/carrinho.html", "carrinho.html"),
    ("loja/checkout.html", "checkout.html"),
    ("loja/comprovante.html", "comprovante.html"),
    ("loja/consultar.html", "consultar.html"),
]

def render_all():
    for tpl_path, out_name in templates_to_render:
        try:
            tpl = env.get_template(tpl_path)
        except Exception as e:
            print(f"Template not found: {tpl_path}", e)
            continue
        ctx = contexts.get(out_name, {})
        html = tpl.render(**ctx)
        # keep the HTML as rendered with relative asset links (works with file://)
        out_path = os.path.join(OUT_DIR, out_name)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Wrote: {out_path}")
        # Also produce a dark-mode version by swapping the stylesheet reference
        try:
            dark_html = html
            # replace occurrences of loja.css with loja-dark.css when present
            if 'loja.css' in dark_html:
                dark_html = dark_html.replace('loja.css', 'loja-dark.css')
            # ensure body has class="dark" so CSS selectors can target it
            if '<body' in dark_html and 'class="dark"' not in dark_html:
                dark_html = dark_html.replace('<body', '<body class="dark"', 1)
            dark_out = os.path.join(OUT_DIR, out_name.replace('.html', '_dark.html'))
            with open(dark_out, 'w', encoding='utf-8') as f2:
                f2.write(dark_html)
            print(f"Wrote (dark): {dark_out}")
        except Exception as ex:
            print("Failed to write dark preview:", ex)

if __name__ == "__main__":
    render_all()
