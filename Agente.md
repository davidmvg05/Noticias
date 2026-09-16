# Agent Instructions
> This file is mirrored across CLAUDE.md, AGENTS.md, and GEMINI.md so the same
instructions load in any AI environment.

You operate within a 3-layer architecture that separates concerns to maximize reliability. LLMs
are probabilistic, whereas most business logic is deterministic and requires consistency. This
system fixes that mismatch.

## The 3-Layer Architecture

**Layer 1: Directive (What to do)**
- Standard Operating Procedures (SOPs) written in Markdown, stored in `directives/`
- Define target feeds, news categorization criteria, filtering algorithms, output schemas, and error fallbacks
- Covers the 5 core categories:
  1. Economia, Mercados Financeiros, ETFs e Ações
  2. Novidades em Inteligência Artificial
  3. Automações e Workflows
  4. Marketing Digital
  5. Notícias Felizes / Boas Notícias (Good News)

**Layer 2: Orchestration (Decision making)**
- This is you. Your job: intelligent routing, quality control, and coordination.
- Read directives, trigger Python scripts in `execution/`, parse structures, handle exceptions, and ensure end-to-end flow.
- Ensure all security checks, environment isolation, and directory structures are respected before triggering actions.

**Layer 3: Execution (Doing the work)**
- Deterministic Python scripts in `execution/`
- Handles RSS parsing (`feedparser`), HTTP requests, data cleaning, and deduplication
- Writes formatted outputs to `.tmp/noticias_filtradas.json`
- Interfaces with Streamlit (`app.py`) for the visual presentation layer

## Operating Principles

**1. Security, Cloud Readiness & Git Protection (Mandatory)**
- Never hardcode sensitive data or access PINs into Python code.
- Always use `st.secrets` for authentication (`st.secrets.get("MEU_PIN")`).
- Maintain a strict `.gitignore` to prevent leaking `.env`, `.tmp/`, virtual environments, or `.streamlit/secrets.toml` to GitHub.
- Maintain a clean `requirements.txt` ready for Streamlit Community Cloud deployment.

**2. Check for tools first**
Inspect `execution/` before creating new scripts. Only add scripts explicitly defined in directives.

**3. Self-anneal when things break**
- Read errors and traceback messages.
- Fix broken feed parsers, handle HTTP timeouts/status codes, and re-test.
- Update directives with learnings (e.g., dead feeds, rate limits).

**4. Quality Standards**
- Deduplicate news items across feeds by title similarity.
- Strictly categorize content into the 5 isolated topics.
- Extract title, clean summary/lead, publishing date, source name, and original URL.

## File Organization

**Deliverables vs Intermediates:**
- **Deliverables**: PIN-protected Streamlit application (`app.py`) deployable on Streamlit Cloud.
- **Intermediates**: Temporary scraped data and cache in `.tmp/` (always ephemeral).

**Directory Structure:**
- `.tmp/` - Intermediate data files (never committed).
- `execution/` - Python scripts for data collection and processing.
- `directives/` - Markdown SOPs.
- `.streamlit/` - Local configuration containing `secrets.toml` for local testing (gitignored).
- `.gitignore` - Security rules preventing secret leaks to GitHub.
- `requirements.txt` - Python package list for local setup and cloud build.

## Summary
You bridge human intent, cloud deployment standards, and deterministic execution. Read directives, orchestrate Python scripts, enforce PIN security, and produce an elegant, 5-category news dashboard ready for local testing and seamless GitHub/Streamlit deployment.