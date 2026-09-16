# 📰 Radar de Notícias | Dashboard Inteligente & Automatizado

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Feeds RSS](https://img.shields.io/badge/Feeds-RSS%20Abertos-orange.svg?logo=rss&logoColor=white)](#-as-5-categorias-curadas)
[![Design](https://img.shields.io/badge/UI%20Design-%230051ff-0051ff.svg)](#-design-e-experiência-do-utilizador)

Um painel web moderno, determinístico e em tempo real para curadoria, agregação e leitura de notícias internacionais e nacionais. Desenvolvido com **Streamlit** e uma robusta **arquitetura de 3 camadas**, o projeto conta com autenticação por PIN, interface com acentos visuais `#0051ff`, tradução automática para Português de Portugal e resiliência total no carregamento de imagens.

---

## 🌟 Principais Funcionalidades

- 🔐 **Acesso Restrito por PIN**: Modal de autenticação elegante com proteção de segredos via `st.secrets` (`MEU_PIN`), sem exposição em código ou commits do Git.
- 🎨 **Design Visual de Alto Nível**: Estilização refinada com a cor `#0051ff`, pills de categoria ergonómicas, cartões verticais uniformes, botões sem fundo com hover sutil na sidebar e compatibilidade integral com Light e Dark Mode.
- 🌐 **Tradução Automática para Português**: Integração direta com o Google Tradutor no cabeçalho, com pré-seleção automática de Português (`pt`), permitindo ler feeds globais em inglês já em português.
- 🖼️ **Resiliência Total de Imagens**: Extração inteligente de tags RSS e Open Graph (`og:image`), proteção contra bloqueios de hotlinking com `referrerpolicy="no-referrer"` e substituição automática (`onerror`) por imagens panorâmicas de alta resolução (800px) para que nenhum cartão fique sem imagem.
- ⚡ **Pipeline Determinístico**: Desduplicação inteligente por similaridade de títulos (Jaccard > 75%), limpeza de parâmetros de tracking (`utm_*`, `ref`), normalização de datas e leads informativos.

---

## 📂 As 5 Categorias Curadas

O agregador recolhe e classifica notícias através de feeds RSS de referência mundial:

| # | Categoria | Fontes de Dados Principais | Foco Editorial |
|---|---|---|---|
| 1 | **Economia & Mercados** | *Jornal de Negócios*, *InfoMoney*, *CNBC Finance*, *Yahoo Finance* | Mercados de capitais, ações, ETFs, bancos centrais e conjuntura económica. |
| 2 | **Inteligência Artificial** | *TechCrunch AI*, *VentureBeat AI*, *MIT Technology Review*, *The Verge* | Modelos de linguagem (LLMs), robótica, agentes de IA e avanços tecnológicos. |
| 3 | **Automações** | *Make Blog*, *Zapier Blog*, *n8n Blog*, *Hacker News Automation* | Workflows inteligentes, integração de sistemas, produtividade e scripts no-code/code. |
| 4 | **Marketing Digital** | *Search Engine Journal*, *Search Engine Land*, *Marketing Dive*, *HubSpot* | SEO, campanhas de tráfego, social media, copywriting e estratégias de conversão. |
| 5 | **Notícias Felizes** | *Good News Network*, *Positive News*, *Reasons to be Cheerful*, *Só Notícia Boa* | Boas ações, sustentabilidade, descobertas médicas e eventos inspiradores pelo mundo. |

---

## 🏛️ Arquitetura em 3 Camadas

O projeto adota o princípio de separação de responsabilidades para garantir estabilidade, auditabilidade e manutenção simples:

```
┌─────────────────────────────────────────────────────────────┐
│  Camada 1: Diretivas (directives/)                          │
│  - Especificações e Procedimentos Operacionais (SOPs em MD) │
│  - Critérios de desduplicação, esquemas JSON e regras RSS   │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  Camada 2: Orquestração (AI Agent / Routing)                │
│  - Coordenação inteligente entre diretivas e scripts        │
│  - Gestão de ambientes, auditoria de código e testes        │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  Camada 3: Execução (execution/ & app.py)                   │
│  - fetch_feeds.py: Coleta, desduplicação e extração og:img  │
│  - app.py: Apresentação Streamlit, PIN e Google Tradutor    │
│  - .tmp/noticias_filtradas.json: Cache de dados estruturado │
└─────────────────────────────────────────────────────────────┘
```

1. **Camada 1: Diretivas (`directives/`)**:
   - Manuais e procedimentos padrão (`coleta_noticias.md`) que documentam regras de negócio, URLs dos feeds, limites de caracteres e algoritmos de filtragem.
2. **Camada 2: Orquestração**:
   - Ponto de tomada de decisão e fluxo lógico guiado por diretrizes claras (`Agente.md`), garantindo isolamento de segredos e execução sem efeitos secundários inesperados.
3. **Camada 3: Execução (`execution/` e `app.py`)**:
   - Código Python puro e determinístico para raspagem HTTP com timeouts, paralelização via `ThreadPoolExecutor` e renderização reativa com Streamlit.

---

## 📁 Estrutura do Repositório

```bash
Noticias/
├── .gitignore                     # Proteção estrita de segredos e caches
├── .streamlit/
│   ├── config.toml                # Configurações do servidor e telemetria
│   └── secrets.toml               # PIN local para testes (ignorado pelo Git)
├── directives/
│   └── coleta_noticias.md         # Diretiva formal de coleta e tratamento RSS
├── execution/
│   ├── fetch_feeds.py             # Script de coleta, desduplicação e cache
│   └── translator.py              # Módulo auxiliar e utilitários de tradução
├── .tmp/                          # Dados temporários em JSON (ignorado pelo Git)
│   └── noticias_filtradas.json
├── Agente.md                      # Princípios operacionais e arquitetura do agente
├── app.py                         # Aplicação principal do Dashboard Streamlit
├── requirements.txt               # Dependências do ecossistema Python
└── README.md                      # Documentação oficial do projeto
```

---

## 🚀 Como Executar Localmente

### 1. Pré-requisitos
- Python 3.10 ou superior instalado.
- Gestor de pacotes `pip` e Git configurados.

### 2. Clonar o Repositório
```bash
git clone https://github.com/davidmvg05/Noticias.git
cd Noticias
```

### 3. Instalar as Dependências
Recomenda-se a utilização de um ambiente virtual:
```bash
python -m venv venv
# No Windows:
venv\Scripts\activate
# No Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Configurar o PIN de Acesso
Crie o ficheiro de segredos locais em `.streamlit/secrets.toml`:
```toml
# .streamlit/secrets.toml
MEU_PIN = "1234"
```
*(Nota: Este ficheiro encontra-se no `.gitignore` e nunca será enviado para o repositório).*

### 5. Iniciar o Painel
```bash
streamlit run app.py
```
O navegador abrirá automaticamente em `http://localhost:8501`. Introduza o PIN definido e explore as notícias em tempo real!

---

## ☁️ Implantação no Streamlit Community Cloud

Para publicar o painel gratuitamente online:

1. Faça o fork ou envie o seu repositório para o **GitHub**.
2. Aceda a [share.streamlit.io](https://share.streamlit.io/) e conecte a sua conta.
3. Selecione o repositório `Noticias`, a branch `main` e o ficheiro `app.py`.
4. Na secção **Advanced settings > Secrets**, adicione o seu PIN:
   ```toml
   MEU_PIN = "SeuPinSeguroAqui"
   ```
5. Clique em **Deploy**. O seu painel de notícias estará online e protegido em poucos minutos!

---

## 📄 Licença

Este projeto está sob a licença [MIT](LICENSE). Sinta-se à vontade para utilizar, estudar e adaptar para os seus próprios fluxos de informação.
