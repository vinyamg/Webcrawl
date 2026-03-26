# 🕷️ WebCrawler Enumeration Pentest

Ferramenta de **enumeração automatizada** para coleta e análise de recursos web, focada na identificação de **endpoints, parâmetros, e possíveis vetores de ataque** em aplicações web.

Projetada como apoio para atividades de **pentest** e **bug bounty**.

---

## 🚀 Funcionalidades

- 🔎 **Crawling completo do alvo**
  - Descobre endpoints, URLs, paths e arquivos relevantes
  - Coleta conteúdos HTML e JavaScript

- 📦 **Análise de código JavaScript**
  - Extração de endpoints
  - Identificação de tokens e possíveis credenciais
  - Detecção de requisições internas (APIs)

- 🧠 **Enumeração inteligente**
  - Identificação de parâmetros GET e POST, subdomínios, links de redes sociais
  - Classificação de informações coletadas
  - Organização dos dados para análise posterior

- 💻 **Shell interativa**
  - Interface para explorar os dados coletados
  - Comandos disponíveis:
    - `gets` → lista endpoints com parâmetros GET
    - `js` → analisa código JavaScript
    - `social` → Busca redes sociais
    - `posts` → lista endpoints com parâmetros POST
    - `subdomains` → lista subdomínios
    - *(em expansão)*

---

## 🛠️ Modo de uso

### 🔹 Exibir ajuda
```bash
python webcrawl.py -h
```
### 🔹 Executar enumeração
```bash
python webcrawl.py --url <alvo>
```
### 🔹 Executar análise
```bash
python webcrawl.py --analyze
```

## ⚠️ Aviso Legal

Esta ferramenta foi desenvolvida exclusivamente para fins educacionais e de segurança ofensiva autorizada.

O uso em alvos sem permissão explícita é ilegal.
O autor não se responsabiliza por qualquer uso indevido.
