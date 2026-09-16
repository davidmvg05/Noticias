"""
Dashboard de Notícias Inteligente com Streamlit
Design moderno com acentos na cor #0051ff, autenticação por PIN,
Google Tradutor com seleção automática de Português e resiliência de imagens.
"""

import os

# 1. Garantir que a pasta temporária existe imediatamente no arranque do servidor
os.makedirs(".tmp", exist_ok=True)

import json
import html
from pathlib import Path
from datetime import datetime
import hashlib

import streamlit as st

from execution.fetch_feeds import run_collection, OUTPUT_FILE
from execution.translator import get_article_translation

# Configuração da Página
st.set_page_config(
    page_title="Radar de Notícias | Dashboard",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Imagens temáticas curadas de alta resolução 800px (fallback para notícias sem imagem de origem)
CATEGORY_IMAGES = {
    "economia": [
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=800&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&auto=format&fit=crop&q=80"
    ],
    "ia": [
        "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=800&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&auto=format&fit=crop&q=80"
    ],
    "automacoes": [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&auto=format&fit=crop&q=80"
    ],
    "marketing_digital": [
        "https://images.unsplash.com/photo-1533750516457-a7f992034fec?w=800&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=800&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1432888498266-38ffec3eaf0a?w=800&auto=format&fit=crop&q=80"
    ],
    "noticias_felizes": [
        "https://images.unsplash.com/photo-1499209974431-9dddcece7f88?w=800&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1518495973542-4542c06a5843?w=800&auto=format&fit=crop&q=80"
    ]
}

def get_category_fallback_image(item: dict, categoria: str) -> str:
    """Retorna fallback temático de alta resolução para a categoria."""
    imgs = CATEGORY_IMAGES.get(categoria, CATEGORY_IMAGES["economia"])
    hash_val = int(hashlib.md5(item.get("id", item.get("titulo", "")).encode("utf-8")).hexdigest(), 16)
    return imgs[hash_val % len(imgs)]


def get_article_image(item: dict, categoria: str) -> str:
    """Retorna imagem real do artigo em alta resolução ou fallback panorâmico."""
    img = item.get("imagem")
    if img and img.startswith("http"):
        if "100x100" in img:
            return img.replace("100x100", "800x450")
        return img
    return get_category_fallback_image(item, categoria)


# Injeção Limpa de Estilos e FontAwesome via st.html
st.html(
    """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" />
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* 1. Ocultar completamente âncoras de títulos e botões de cabeçalho */
    [data-testid="stHeaderAnchor"],
    .stHeadingAnchor,
    a.anchor-link,
    [data-testid="stHeaderActionElements"] {
        display: none !important;
    }

    /* 2. Ocultar barra de decoração superior do Streamlit */
    [data-testid="stDecoration"] {
        display: none !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 2rem !important;
    }

    /* 3. Puxar conteúdo mais para cima */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1250px !important;
    }

    /* 4. Cabeçalho Centralizado e Compacto */
    .header-section {
        text-align: center;
        margin-top: 0 !important;
        margin-bottom: 1.5rem !important;
    }

    .main-title {
        font-size: 2.3rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.025em !important;
        margin: 0 0 0.4rem 0 !important;
        color: inherit;
    }

    .main-subtitle {
        font-size: 1rem !important;
        color: #64748b !important;
        margin: 0 !important;
        font-weight: 400;
    }

    /* 5. Categorias: BORDAS E FUNDO COM COR #0051ff */
    div[data-testid="stButtonGroup"],
    .stButtonGroup,
    .st-key-category_pills,
    .st-key-category_pills div[data-testid="stButtonGroup"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 0.8rem auto 2.2rem auto !important;
        width: 100% !important;
    }

    div[data-testid="stButtonGroup"] > div,
    .stButtonGroup > div {
        display: flex !important;
        justify-content: center !important;
        gap: 12px !important;
        flex-wrap: wrap !important;
    }

    /* TODAS as pills inativas: bordas #0051ff e fundo azul suave */
    div[data-testid="stButtonGroup"] button,
    .stButtonGroup button,
    .st-key-category_pills button,
    [data-testid="stButtonGroup"] [data-testid="baseButton-secondary"] {
        border-radius: 9999px !important;
        border: 1.5px solid #0051ff !important;
        color: #0051ff !important;
        background-color: rgba(0, 81, 255, 0.08) !important;
        padding: 8px 22px !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        box-shadow: none !important;
        transform: none !important;
        transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease !important;
    }

    div[data-testid="stButtonGroup"] button:hover,
    .stButtonGroup button:hover,
    .st-key-category_pills button:hover {
        background-color: rgba(0, 81, 255, 0.16) !important;
        border-color: #0051ff !important;
        color: #003ecb !important;
        box-shadow: none !important;
        transform: none !important;
    }

    /* Pill Ativa: azul #0051ff preenchido com texto branco */
    div[data-testid="stButtonGroup"] button[aria-pressed="true"],
    div[data-testid="stButtonGroup"] button[aria-checked="true"],
    div[data-testid="stButtonGroup"] button[data-state="active"],
    div[data-testid="stButtonGroup"] button[data-selected="true"],
    .stButtonGroup button[aria-pressed="true"],
    .st-key-category_pills button[aria-pressed="true"] {
        background-color: #0051ff !important;
        color: #ffffff !important;
        border: 1.5px solid #0051ff !important;
        box-shadow: none !important;
        transform: none !important;
    }

    div[data-testid="stButtonGroup"] button[aria-pressed="true"] *,
    div[data-testid="stButtonGroup"] button[aria-checked="true"] * {
        color: #ffffff !important;
    }

    /* 6. Sidebar: Botões sem fundo, borda #0051ff e hover cinzento sutil */
    [data-testid="stSidebar"] [data-testid="stButton"] button {
        background: transparent !important;
        background-color: transparent !important;
        border: 1.5px solid #0051ff !important;
        color: inherit !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        box-shadow: none !important;
        transform: none !important;
        transition: background-color 0.15s ease, border-color 0.15s ease !important;
    }

    [data-testid="stSidebar"] [data-testid="stButton"] button:hover {
        background-color: rgba(128, 128, 128, 0.15) !important;
        border-color: #0051ff !important;
        color: inherit !important;
        box-shadow: none !important;
        transform: none !important;
    }

    [data-testid="stSidebarCollapseButton"] button *,
    [data-testid="stSidebarCollapsedControl"] button * {
        display: none !important;
        visibility: hidden !important;
        font-size: 0 !important;
        width: 0 !important;
        height: 0 !important;
        opacity: 0 !important;
    }

    /* Sidebar FECHADA: ícone hambúrguer SEMPRE visível */
    [data-testid="stSidebarCollapsedControl"] {
        display: block !important;
        visibility: visible !important;
        z-index: 99999 !important;
    }
    [data-testid="stSidebarCollapsedControl"] button {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 40px !important;
        height: 40px !important;
        border-radius: 8px !important;
        background: rgba(255, 255, 255, 0.07) !important;
        border: 1px solid rgba(128, 128, 128, 0.22) !important;
        box-shadow: none !important;
        transform: none !important;
    }
    [data-testid="stSidebarCollapsedControl"] button::after {
        content: "\\f0c9" !important;
        font-family: "Font Awesome 6 Free" !important;
        font-weight: 900 !important;
        font-size: 1.25rem !important;
        color: inherit !important;
        display: block !important;
    }

    /* Sidebar ABERTA: Ocultar dupla seta e hover azul no botão X */
    [data-testid="stSidebarCollapseButton"] button {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 38px !important;
        height: 38px !important;
        border-radius: 8px !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        background: rgba(255, 255, 255, 0.05) !important;
        color: #64748b !important;
        position: relative !important;
        box-shadow: none !important;
        transform: none !important;
        transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease !important;
    }
    [data-testid="stSidebarCollapseButton"] button::after {
        content: "✕" !important;
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        color: inherit !important;
        display: block !important;
        line-height: 1 !important;
    }
    [data-testid="stSidebarCollapseButton"] button:hover {
        background: rgba(0, 81, 255, 0.1) !important;
        border-color: rgba(0, 81, 255, 0.4) !important;
        color: #0051ff !important;
        box-shadow: none !important;
        transform: none !important;
    }
    [data-testid="stSidebarCollapseButton"] button:hover::after {
        color: #0051ff !important;
    }

    /* Elementos da Sidebar */
    .sidebar-header-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
    }

    .sidebar-brand {
        font-size: 1.15rem;
        font-weight: 700;
        color: inherit;
        white-space: nowrap;
    }

    .session-active-badge {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 9999px;
        white-space: nowrap;
    }

    .sidebar-stat-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 12px;
    }

    .sidebar-stat-title {
        font-size: 0.78rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .sidebar-stat-value {
        font-size: 0.95rem;
        font-weight: 600;
        color: inherit;
        white-space: normal;
        word-break: break-word;
        line-height: 1.4;
    }

    .sidebar-stat-count {
        font-size: 1.5rem;
        font-weight: 800;
        color: #0051ff;
    }

    /* 7. Cartões de Notícias Verticais */
    .news-card-vertical {
        height: 520px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        background: rgba(255, 255, 255, 0.035);
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 14px;
        overflow: hidden;
        margin-bottom: 24px;
        box-shadow: none !important;
        transform: none !important;
        transition: border-color 0.15s ease !important;
    }

    .news-card-vertical:hover {
        transform: none !important;
        box-shadow: none !important;
        border-color: #0051ff !important;
    }

    .card-img-wrapper {
        position: relative !important;
        width: 100% !important;
        height: 215px !important;
        min-height: 215px !important;
        max-height: 215px !important;
        flex-shrink: 0 !important;
        overflow: hidden !important;
        background: #0f172a !important;
    }

    .card-img-top {
        display: block !important;
        width: 100% !important;
        height: 100% !important;
        min-width: 100% !important;
        min-height: 100% !important;
        max-width: 100% !important;
        max-height: 100% !important;
        object-fit: cover !important;
        object-position: center !important;
    }

    /* Tag de fonte no canto superior esquerdo da imagem com cor #0051ff */
    .source-badge-floating {
        position: absolute !important;
        top: 12px !important;
        left: 12px !important;
        z-index: 5 !important;
        background: #0051ff !important;
        color: #ffffff !important;
        font-size: 0.76rem !important;
        font-weight: 700 !important;
        padding: 4px 12px !important;
        border-radius: 9999px !important;
        letter-spacing: 0.02em !important;
        box-shadow: none !important;
        transform: none !important;
    }

    .card-body-content {
        padding: 18px 20px 16px 20px;
        display: flex;
        flex-direction: column;
        flex-grow: 1;
        overflow: hidden;
    }

    .date-text-clean {
        font-size: 0.82rem;
        color: #94a3b8;
        margin-bottom: 8px;
        font-weight: 500;
        flex-shrink: 0;
    }

    /* Clamping uniforme de título (2 linhas) */
    .card-news-title {
        font-size: 1.1rem;
        font-weight: 700;
        line-height: 1.4;
        margin: 0 0 8px 0;
        color: inherit;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        height: 2.8em;
        flex-shrink: 0;
    }

    /* Clamping uniforme do lead (3 linhas) */
    .card-news-lead {
        font-size: 0.9rem;
        line-height: 1.55;
        color: #64748b;
        margin: 0 0 12px 0;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        height: 4.65em;
        flex-grow: 1;
    }

    .card-bottom-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        margin-top: auto;
        padding-top: 8px;
        flex-shrink: 0;
        flex-wrap: wrap;
    }

    /* Botão Traduzir Cartão (Individual PT-PT) */
    .btn-translate-card {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(0, 81, 255, 0.08) !important;
        color: #0051ff !important;
        border: 1.5px solid #0051ff !important;
        border-radius: 8px;
        font-size: 0.84rem;
        font-weight: 600;
        padding: 7px 14px;
        cursor: pointer;
        box-shadow: none !important;
        transform: none !important;
        transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease !important;
        white-space: nowrap;
        user-select: none;
        outline: none;
    }

    .btn-translate-card:hover {
        background: rgba(0, 81, 255, 0.16) !important;
        color: #003ecb !important;
        border-color: #003ecb !important;
    }

    .btn-translate-card.translated {
        background: #0051ff !important;
        color: #ffffff !important;
        border-color: #0051ff !important;
    }

    /* Botão firme e estável Ler o Artigo Original com #0051ff */
    .btn-read-article {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        background: #0051ff;
        color: #ffffff !important;
        text-decoration: none !important;
        font-size: 0.86rem;
        font-weight: 600;
        padding: 8px 18px;
        border-radius: 8px;
        box-shadow: none !important;
        transform: none !important;
        transition: background-color 0.15s ease !important;
        white-space: nowrap;
        margin-left: auto;
    }

    .btn-read-article:hover {
        background: #003ecb !important;
        box-shadow: none !important;
        transform: none !important;
    }

    /* 8. Pop-up do PIN: Customização visual do modal (Light e Dark Mode) */
    .st-emotion-cache-14scugc {
        background: rgb(255 255 255 / 25%) !important;
    }

    .st-emotion-cache-1vr7xu3,
    .st-emotion-cache-r76p4h {
        overflow: visible !important;
        border-radius: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
    }

    .st-emotion-cache-1bcyifm,
    .st-emotion-cache-zuyloh {
        border: none !important;
        border-radius: 0 !important;
    }

    div[data-testid="stDialog"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 100vh !important;
    }

    div[data-testid="stDialog"] > div[role="dialog"],
    div[role="dialog"],
    [data-testid="stDialogContent"],
    [data-testid="stModal"] {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        margin: auto !important;
        max-width: 440px !important;
        width: 92% !important;
    }

    /* Botão Desbloquear Painel (Submit Form): background e border #0051ff, hover azul mais forte */
    div[data-testid="stFormSubmitButton"] > button,
    div[data-testid="stFormSubmitButton"] button,
    .stFormSubmitButton > button,
    button[kind="primaryFormSubmit"] {
        background-color: #0051ff !important;
        background: #0051ff !important;
        border: 1.5px solid #0051ff !important;
        color: #ffffff !important;
        box-shadow: none !important;
        transform: none !important;
        font-weight: 600 !important;
        transition: background-color 0.15s ease, border-color 0.15s ease !important;
    }

    div[data-testid="stFormSubmitButton"] > button:hover,
    div[data-testid="stFormSubmitButton"] button:hover,
    .stFormSubmitButton > button:hover,
    button[kind="primaryFormSubmit"]:hover {
        background-color: #003ecb !important;
        background: #003ecb !important;
        border-color: #003ecb !important;
        color: #ffffff !important;
        box-shadow: none !important;
        transform: none !important;
    }

    /* No olho fica sem o fundo azul */
    div[data-testid="stTextInput"] button,
    div[data-testid="stTextInput"] button:hover,
    div[data-testid="stTextInput"] button:focus,
    div[data-testid="stTextInput"] button:active,
    div[data-testid="stTextInput"] [data-baseweb="button"],
    div[data-testid="stTextInput"] [data-baseweb="button"]:hover,
    div[data-testid="stTextInput"] [data-baseweb="button"]:focus,
    button[aria-label*="password" i],
    button[aria-label*="Password"],
    button[aria-label*="Show" i],
    button[aria-label*="Hide" i] {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        color: #64748b !important;
    }

    /* UMA ÚNICA BORDA AZUL no container externo */
    div[data-testid="stTextInput"] div[data-baseweb="input"] {
        border-radius: 8px !important;
        border: 1.5px solid rgba(128, 128, 128, 0.25) !important;
        background: transparent !important;
        background-color: transparent !important;
        transition: border-color 0.15s ease !important;
        outline: none !important;
        box-shadow: none !important;
    }

    /* No hover e foco a borda onde coloco o PIN é azul #0051ff */
    .st-emotion-cache-1rn0o2o:focus-within,
    .st-emotion-cache-1rn0o2o:hover,
    .st-emotion-cache-1rn0o2o:focus,
    div[data-testid="stTextInput"] div[data-baseweb="input"]:hover,
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
        border: 1.5px solid #0051ff !important;
        border-color: #0051ff !important;
        outline: none !important;
        box-shadow: none !important;
    }

    /* Quando carrego para colocar o PIN NÃO deve aparecer aquele fundo azul claro */
    .st-emotion-cache-1rn0o2o,
    .st-emotion-cache-1rn0o2o:hover,
    .st-emotion-cache-1rn0o2o:focus,
    .st-emotion-cache-1rn0o2o:focus-within,
    .st-emotion-cache-1rn0o2o:active,
    div[data-testid="stTextInput"] div[data-baseweb="input"],
    div[data-testid="stTextInput"] div[data-baseweb="base-input"],
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextInput"] div[data-baseweb="input"]:hover,
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus,
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
    div[data-testid="stTextInput"] div[data-baseweb="input"]:active,
    div[data-testid="stTextInput"] div[data-baseweb="base-input"]:hover,
    div[data-testid="stTextInput"] div[data-baseweb="base-input"]:focus,
    div[data-testid="stTextInput"] div[data-baseweb="base-input"]:focus-within,
    div[data-testid="stTextInput"] div[data-baseweb="base-input"]:active,
    div[data-testid="stTextInput"] input:hover,
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextInput"] input:focus-within,
    div[data-testid="stTextInput"] input:active,
    div[data-testid="stTextInput"] input:focus-visible {
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* Eliminar qualquer borda interna duplicada em base-input e input */
    div[data-testid="stTextInput"] div[data-baseweb="base-input"],
    div[data-baseweb="base-input"],
    div[data-testid="stTextInput"] input {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }

    div[data-testid="stTextInput"] div[data-baseweb="base-input"]:hover,
    div[data-testid="stTextInput"] div[data-baseweb="base-input"]:focus-within,
    div[data-testid="stTextInput"] input:hover,
    div[data-testid="stTextInput"] input:focus {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }

    /* Centralizar os símbolos **** (placeholder e texto) no centro geométrico */
    .st-emotion-cache-1rn0o2o input,
    .st-emotion-cache-1rn0o2o input::placeholder,
    .st-emotion-cache-1rn0o2o input::-webkit-input-placeholder,
    .st-emotion-cache-1rn0o2o input::-moz-placeholder,
    .st-emotion-cache-1rn0o2o input:-ms-input-placeholder,
    [data-testid="stTextInputField"],
    [data-testid="stTextInputField"]::placeholder,
    [data-testid="stTextInputField"]::-webkit-input-placeholder,
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextInput"] input::placeholder,
    div[data-testid="stTextInput"] input::-webkit-input-placeholder,
    div[data-testid="stTextInput"] input::-moz-placeholder,
    div[data-testid="stTextInput"] input:-ms-input-placeholder,
    div[data-baseweb="input"] input,
    div[data-baseweb="input"] input::placeholder,
    div[data-baseweb="input"] input::-webkit-input-placeholder,
    div[data-baseweb="base-input"] input,
    div[data-baseweb="base-input"] input::placeholder,
    div[data-baseweb="base-input"] input::-webkit-input-placeholder,
    input[type="password"],
    input[type="password"]::placeholder,
    input[type="password"]::-webkit-input-placeholder {
        text-align: center !important;
        text-align-last: center !important;
        letter-spacing: 0.35em !important;
        font-size: 1.25rem !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        margin: 0 auto !important;
        -webkit-text-security: disc !important;
    }

    /* Ocultar "Press Enter to submit form" */
    [data-testid="InputInstructions"], 
    .stInputInstructions, 
    div[data-testid="InputInstructions"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }

    /* Ocultar botão X de fechar o pop-up de autenticação */
    [data-testid="stDialog"] button[aria-label="Close"],
    div[role="dialog"] button[aria-label="Close"] {
        display: none !important;
    }

    /* Estilização do Google Tradutor */
    #google_translate_element {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 0.5rem auto 1.2rem auto !important;
    }

    .goog-te-gadget-simple {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1.5px solid #0051ff !important;
        border-radius: 9999px !important;
        padding: 5px 15px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.88rem !important;
        color: inherit !important;
        display: inline-flex !important;
        align-items: center !important;
        cursor: pointer !important;
        box-shadow: none !important;
    }

    .goog-te-gadget-simple .goog-te-menu-value {
        color: inherit !important;
        font-weight: 500 !important;
    }

    .goog-te-gadget-simple .goog-te-menu-value span {
        color: inherit !important;
    }

    .goog-te-banner-frame.skiptranslate,
    .goog-te-banner-frame {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }

    body {
        top: 0px !important;
    }
    </style>

    <script>
    // Configurar cookie do Google Tradutor para Português automático
    function setGoogleTranslateCookie() {
        var d = window.location.hostname;
        document.cookie = 'googtrans=/auto/pt; path=/;';
        document.cookie = 'googtrans=/auto/pt; path=/; domain=' + d;
        document.cookie = 'googtrans=/en/pt; path=/;';
        document.cookie = 'googtrans=/en/pt; path=/; domain=' + d;
    }
    setGoogleTranslateCookie();

    window.googleTranslateElementInit = function() {
        setGoogleTranslateCookie();
        new google.translate.TranslateElement({
            pageLanguage: 'auto',
            includedLanguages: 'pt,en,es,fr,de',
            layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
            autoDisplay: false
        }, 'google_translate_element');
    };

    // Desativar autocomplete do navegador e garantir centralização dos símbolos **** no PIN
    function disablePinAutocomplete() {
        var inputs = document.querySelectorAll('input');
        inputs.forEach(function(inp) {
            inp.setAttribute('autocomplete', 'new-password');
            inp.setAttribute('autocorrect', 'off');
            inp.setAttribute('autocapitalize', 'off');
            inp.setAttribute('spellcheck', 'false');
            inp.style.setProperty('text-align', 'center', 'important');
            inp.style.setProperty('text-align-last', 'center', 'important');
            inp.style.setProperty('letter-spacing', '0.35em', 'important');
        });
    }
    window.addEventListener('DOMContentLoaded', disablePinAutocomplete);
    setInterval(disablePinAutocomplete, 300);

    // Função de alternância da tradução do cartão individual (sem recarregar o Streamlit)
    function toggleCardTranslation(cardId, btn) {
        var card = document.getElementById(cardId);
        if (!card) return;
        var titleEl = card.querySelector('.card-news-title');
        var leadEl = card.querySelector('.card-news-lead');
        var btnText = btn.querySelector('.btn-text');
        var isTranslated = btn.getAttribute('data-translated') === 'true';

        if (isTranslated) {
            // Reverter para o texto original (EN)
            if (titleEl && titleEl.getAttribute('data-en')) {
                titleEl.textContent = titleEl.getAttribute('data-en');
            }
            if (leadEl && leadEl.getAttribute('data-en')) {
                leadEl.textContent = leadEl.getAttribute('data-en');
            }
            btn.setAttribute('data-translated', 'false');
            btn.classList.remove('translated');
            if (btnText) btnText.textContent = 'Traduzir (PT)';
        } else {
            // Alternar para o texto em Português de Portugal (pt-PT)
            if (titleEl && titleEl.getAttribute('data-pt')) {
                titleEl.textContent = titleEl.getAttribute('data-pt');
            }
            if (leadEl && leadEl.getAttribute('data-pt')) {
                leadEl.textContent = leadEl.getAttribute('data-pt');
            }
            btn.setAttribute('data-translated', 'true');
            btn.classList.add('translated');
            if (btnText) btnText.textContent = 'Ver Original (EN)';
        }
    }
    window.toggleCardTranslation = toggleCardTranslation;
    </script>

    <script type="text/javascript" src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>

    <img src="data:image/svg+xml;utf8,<svg></svg>" style="display:none;" onerror="
        var d = window.location.hostname;
        document.cookie = 'googtrans=/auto/pt; path=/;';
        document.cookie = 'googtrans=/auto/pt; path=/; domain=' + d;
        document.cookie = 'googtrans=/en/pt; path=/;';
        document.cookie = 'googtrans=/en/pt; path=/; domain=' + d;
        if (!window.googleTranslateElementInit) {
            window.googleTranslateElementInit = function() {
                new google.translate.TranslateElement({
                    pageLanguage: 'auto',
                    includedLanguages: 'pt,en,es,fr,de',
                    layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
                    autoDisplay: false
                }, 'google_translate_element');
            };
        }
        if (!document.getElementById('google-translate-script')) {
            var s = document.createElement('script');
            s.id = 'google-translate-script';
            s.type = 'text/javascript';
            s.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
            document.head.appendChild(s);
        }
    " />
    """
)


# ==============================================================================
# 1. ECRÃ DE AUTENTICAÇÃO POR PIN (BLINDADO E SEGURO)
# ==============================================================================

pin_correto = str(st.secrets.get("MEU_PIN", "")).strip()

if not pin_correto:
    st.error("PIN não configurado nos Secrets do servidor.")
    st.stop()

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    col_a, col_b, col_c = st.columns([1, 1.8, 1])
    with col_b:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 20px; margin-top: 30px;">
                <div style="display: flex; justify-content: center; margin-bottom: 12px;">
                    <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="#0051ff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2" fill="rgba(0, 81, 255, 0.08)"></rect>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                        <circle cx="12" cy="16" r="1.5" fill="#0051ff"></circle>
                    </svg>
                </div>
                <h2 style="text-align: center; margin: 0 0 6px 0; font-size: 1.6rem; font-weight: 800; color: inherit;">
                    Acesso Restrito
                </h2>
                <p style="color: #64748b; font-size: 0.94rem; margin: 0;">
                    Introduza o seu PIN de segurança para aceder ao painel.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.form("form_pin_auth", clear_on_submit=False):
            pin_digitado = st.text_input("Introduza o PIN:", type="password")
            submetido = st.form_submit_button(
                "Desbloquear Painel",
                use_container_width=True,
                type="primary"
            )

            if submetido:
                if pin_digitado.strip() == pin_correto:
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("❌ PIN incorreto. Verifique o código e tente novamente.")

    st.stop()


# ==============================================================================
# 2. CARREGAMENTO DE DADOS
# ==============================================================================

def load_news_data() -> dict:
    """Carrega as notícias de .tmp/noticias_filtradas.json com resiliência total contra FileNotFoundError."""
    os.makedirs(".tmp", exist_ok=True)
    if not OUTPUT_FILE.exists():
        try:
            with st.spinner("Inicializando primeira coleta de notícias RSS..."):
                return run_collection()
        except Exception as e:
            st.warning("⚠️ Não foi possível coletar as notícias automaticamente na inicialização.")
            return {"atualizado_em": "Pendente", "total_artigos": 0, "categorias": {}}

    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not data.get("categorias"):
                return run_collection()
            return data
    except Exception:
        try:
            with st.spinner("Recarregando feeds RSS após erro de leitura..."):
                return run_collection()
        except Exception:
            return {"atualizado_em": "Erro", "total_artigos": 0, "categorias": {}}


dados_noticias = load_news_data()


# ==============================================================================
# 3. BARRA LATERAL (SIDEBAR SEM ÍCONES 🚪🔄, BORDA #0051ff E HOVER CINZENTO)
# ==============================================================================

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-header-row">
            <span class="sidebar-brand"><i class="fa-solid fa-newspaper" style="color: #0051ff; margin-right: 6px;"></i> Radar de Notícias</span>
            <span class="session-active-badge"><i class="fa-solid fa-circle" style="font-size: 0.55rem; vertical-align: middle; margin-right: 4px;"></i> Sessão Ativa</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    atualizado_em = dados_noticias.get("atualizado_em", "Desconhecido")
    try:
        dt = datetime.fromisoformat(atualizado_em.replace("Z", "+00:00"))
        data_formatada = dt.strftime("%d/%m/%Y às %H:%M UTC")
    except Exception:
        data_formatada = atualizado_em

    st.markdown(
        f"""
        <div class="sidebar-stat-card">
            <div class="sidebar-stat-title"><i class="fa-regular fa-clock" style="color: #0051ff;"></i> Última Sincronização</div>
            <div class="sidebar-stat-value">{data_formatada}</div>
        </div>
        <div class="sidebar-stat-card">
            <div class="sidebar-stat-title"><i class="fa-solid fa-layer-group" style="color: #0051ff;"></i> Total de Artigos</div>
            <div class="sidebar-stat-count">{dados_noticias.get("total_artigos", 0)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    # Botão Atualizar Feeds Agora (sem ícone 🔄 e sem background sólido)
    if st.button("Atualizar Feeds Agora", use_container_width=True):
        with st.spinner("A recolher novidades dos feeds RSS..."):
            dados_noticias = run_collection()
            st.success("Feeds atualizados com sucesso!")
            st.rerun()

    st.write("")

    # Botão Terminar Sessão (sem ícone 🚪)
    if st.button("Terminar Sessão", use_container_width=True):
        st.session_state["autenticado"] = False
        st.rerun()


# ==============================================================================
# 4. TÍTULO E CATEGORIAS ESTILO PILLS COM BORDAS E FUNDO #0051ff
# ==============================================================================

st.markdown(
    """
    <div class="header-section">
        <h1 class="main-title">Radar de Notícias e Tendências</h1>
        <p class="main-subtitle">Curadoria determinística e em tempo real através de feeds RSS abertos.</p>
        <div id="google_translate_element"></div>
    </div>
    """,
    unsafe_allow_html=True
)

OPCOES_CATEGORIAS = [
    "Todos",
    "Economia & Mercados",
    "Inteligência Artificial",
    "Automações",
    "Marketing Digital",
    "Notícias Felizes"
]

categoria_selecionada = st.pills(
    label="Filtrar por Categoria",
    options=OPCOES_CATEGORIAS,
    default="Todos",
    label_visibility="collapsed",
    key="category_pills"
)

if not categoria_selecionada:
    categoria_selecionada = "Todos"


MAPA_CATEGORIAS = {
    "Economia & Mercados": ("economia", "Economia & Mercados"),
    "Inteligência Artificial": ("ia", "Inteligência Artificial"),
    "Automações": ("automacoes", "Automações"),
    "Marketing Digital": ("marketing_digital", "Marketing Digital"),
    "Notícias Felizes": ("noticias_felizes", "Notícias Felizes"),
}

categorias_dict = dados_noticias.get("categorias", {})

if categoria_selecionada == "Todos":
    artigos_exibicao = []
    for cat_key, _ in MAPA_CATEGORIAS.values():
        for art in categorias_dict.get(cat_key, []):
            art_com_cat = dict(art)
            art_com_cat["_cat_key"] = cat_key
            artigos_exibicao.append(art_com_cat)
    artigos_exibicao.sort(key=lambda x: x.get("data_publicacao", ""), reverse=True)
else:
    cat_key, _ = MAPA_CATEGORIAS.get(categoria_selecionada, ("economia", "Economia & Mercados"))
    artigos_exibicao = [
        dict(art, _cat_key=cat_key)
        for art in categorias_dict.get(cat_key, [])
    ]


# ==============================================================================
# 5. RENDERIZAÇÃO DOS CARTÕES VERTICAIS (SEM BOTÃO VER TRADUÇÃO)
# ==============================================================================

def render_article_card(item: dict) -> str:
    """Renderiza o HTML do cartão com suporte a tradução individual instantânea via JavaScript."""
    cat_key = item.get("_cat_key", "economia")
    img_url = get_article_image(item, cat_key)
    fallback_img = get_category_fallback_image(item, cat_key)
    
    raw_title = item.get("titulo", "")
    raw_lead = item.get("resumo", "Sem resumo disponível.")
    raw_source = item.get("fonte", "Fonte")
    raw_url = item.get("url", "#")
    raw_date = item.get("data_publicacao", "")
    
    card_id = f"news_card_{item.get('id', hashlib.md5(raw_title.encode('utf-8')).hexdigest())}"
    
    safe_title = html.escape(raw_title)
    safe_lead = html.escape(raw_lead)
    safe_source = html.escape(raw_source)
    safe_url = html.escape(raw_url, quote=True)
    safe_date = html.escape(raw_date)

    # Obter tradução (do item pré-calculado ou através do módulo com cache persistente)
    is_en = item.get("is_en")
    pt_title = item.get("titulo_pt")
    pt_lead = item.get("resumo_pt")
    if is_en is None or pt_title is None or pt_lead is None:
        is_en, pt_title, pt_lead = get_article_translation(raw_title, raw_lead, raw_source)

    if is_en and (pt_title != raw_title or pt_lead != raw_lead):
        safe_attr_title_en = html.escape(raw_title, quote=True)
        safe_attr_title_pt = html.escape(pt_title, quote=True)
        safe_attr_lead_en = html.escape(raw_lead, quote=True)
        safe_attr_lead_pt = html.escape(pt_lead, quote=True)

        title_html = f'<div class="card-news-title" data-en="{safe_attr_title_en}" data-pt="{safe_attr_title_pt}">{safe_title}</div>'
        lead_html = f'<div class="card-news-lead" data-en="{safe_attr_lead_en}" data-pt="{safe_attr_lead_pt}">{safe_lead}</div>'
        translate_btn_html = (
            f'<button type="button" class="btn-translate-card" onclick="toggleCardTranslation(\'{card_id}\', this)" data-translated="false" title="Traduzir para Português de Portugal">'
            f'<i class="fa-solid fa-language"></i> <span class="btn-text">Traduzir (PT)</span>'
            f'</button>'
        )
    else:
        title_html = f'<div class="card-news-title">{safe_title}</div>'
        lead_html = f'<div class="card-news-lead">{safe_lead}</div>'
        translate_btn_html = ""

    bottom_html = (
        f'<div class="card-bottom-row">'
        f'{translate_btn_html}'
        f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer" class="btn-read-article">'
        f'<i class="fa-solid fa-arrow-up-right-from-square"></i> Ler o Artigo Original'
        f'</a>'
        f'</div>'
    )

    # Construção plana do HTML sem espaços de indentação que acionem blocos de código Markdown
    return (
        f'<div class="news-card-vertical" id="{card_id}">'
        f'<div class="card-img-wrapper">'
        f'<span class="source-badge-floating">{safe_source}</span>'
        f'<img src="{img_url}" alt="{safe_title}" class="card-img-top" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null; this.src=\'{fallback_img}\';" />'
        f'</div>'
        f'<div class="card-body-content">'
        f'<div class="date-text-clean">{safe_date}</div>'
        f'{title_html}'
        f'{lead_html}'
        f'{bottom_html}'
        f'</div>'
        f'</div>'
    )


if not artigos_exibicao:
    st.info("Nenhuma notícia disponível para a categoria selecionada de momento.")
    if st.button("Buscar Notícias Agora", type="primary"):
        with st.spinner("A recolher novidades dos feeds RSS..."):
            run_collection()
            st.rerun()
else:
    for i in range(0, len(artigos_exibicao), 2):
        col1, col2 = st.columns(2)

        # Coluna 1
        with col1:
            st.markdown(render_article_card(artigos_exibicao[i]), unsafe_allow_html=True)

        # Coluna 2 (se existir)
        if i + 1 < len(artigos_exibicao):
            with col2:
                st.markdown(render_article_card(artigos_exibicao[i + 1]), unsafe_allow_html=True)
