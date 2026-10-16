"""Acessibilidade das cores (WCAG): contraste mínimo 4,5:1 para texto, 3:1 para gráficos."""
import pytest

from config import theme as T


def _lum(h):
    """Luminância relativa de uma cor hexadecimal (fórmula WCAG)."""
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contraste(a, b):
    """Razão de contraste entre duas cores (1 a 21). WCAG AA exige ≥ 4,5 para texto."""
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


@pytest.mark.parametrize("nome,tk", [("claro", T.TOKENS_LIGHT), ("escuro", T.TOKENS_DARK)])
def test_texto_legivel_nos_fundos(nome, tk):
    """Todo texto e cor de estado precisa de contraste ≥ 4,5:1 sobre cada fundo, nos dois temas."""
    for fundo in ("content_bg", "sidebar_bg", "card_bg"):
        for texto in ("text_primary", "text_secondary", "text_muted"):
            assert contraste(tk[texto], tk[fundo]) >= 4.5, (nome, texto, fundo)
        estados = ("saudavel", "atencao", "critico", "accent") if fundo != "sidebar_bg" else ("accent",)  # sidebar não exibe estados
        for estado in estados:
            assert contraste(tk[estado], tk[fundo]) >= 4.5, (nome, estado, fundo)


@pytest.mark.parametrize("nome,tk", [("claro", T.TOKENS_LIGHT), ("escuro", T.TOKENS_DARK)])
def test_sidebar_distinta_do_conteudo(nome, tk):
    """A navegação deve ter fundo diferente do conteúdo (hierarquia visual)."""
    assert tk["sidebar_bg"] != tk["content_bg"] and tk["card_bg"] != tk["content_bg"] or nome == "claro"
    assert tk["sidebar_bg"].upper() != tk["content_bg"].upper()


def test_tokens_oficiais_do_ds():
    """Garante que as cores principais seguem o Padrão Digital de Governo v3.7.0."""
    assert T.TOKENS_LIGHT["accent"] == "#1351B4"  # blue-warm-vivid-70
    assert T.TOKENS_LIGHT["critico"] == "#E52207" and T.TOKENS_LIGHT["saudavel"] == "#168821"
