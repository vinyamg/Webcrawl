from colorama import Fore
import re
from tqdm import tqdm
from urllib.parse import urlparse, urlunparse, parse_qs
from typing import Set

from .config import codigo_regexs, SECRET_PATTERNS, STRING_LITERAL_PATTERNS, ENTRADAS_USUARIO, SINKS_PERIGOSOS

MODIFICADORES_TUDO = ("tudo", "all", "completo")


def arquivoTipo(conn, extensao, mostrar_tudo=False):
    extensao = extensao.strip().lower()
    if not extensao:
        print("Uso: ext <extensão>  (ex: ext .js)")
        return
    query = """
        SELECT href AS url FROM links
        UNION ALL
        SELECT href AS url FROM css
        UNION ALL
        SELECT src AS url FROM scripts_externos
    """
    encontrados = set()
    for (url,) in conn.execute(query).fetchall():
        parsed = urlparse(url)
        sem_query = urlunparse(parsed._replace(query=""))
        if sem_query.lower().endswith(extensao):
            encontrados.add(sem_query)

    if not encontrados:
        print(f"\n{Fore.GREEN}[+] Nenhuma URL encontrada com a extensão '{extensao}'.{Fore.RESET}")
        return

    secao(f"URLs com extensão '{extensao}'", len(encontrados))
    imprimir_limitado(sorted(encontrados), lambda u: f"  → {colorir(u)}", mostrar_tudo=mostrar_tudo)


def social(conn, mostrar_tudo=False) -> None:
    REDES_PATTERNS = {
        "Redes sociais": [
            "facebook.com", "pinterest.com", "twitter.com", "x.com",
            "linkedin.com", "instagram.com", "tiktok.com", "reddit.com", "threads.net",
        ],
        "Vídeo/streaming": ["youtube.com", "youtu.be", "vimeo.com", "twitch.tv"],
        "Mensageria": [
            "wa.me", "whatsapp.com", "t.me", "telegram.me", "discord.gg", "discord.com",
        ],
    }
    encontrados_por_categoria = {}
    emails: Set[str] = set()
    telefones: Set[str] = set()

    for (link,) in conn.execute("SELECT DISTINCT href FROM links").fetchall():
        link_lower = link.lower()

        if link_lower.startswith("mailto:"):
            emails.add(link[7:].split("?")[0])
            continue
        if link_lower.startswith("tel:"):
            telefones.add(link[4:])
            continue

        for categoria, padroes in REDES_PATTERNS.items():
            if any(p in link_lower for p in padroes):
                encontrados_por_categoria.setdefault(categoria, set()).add(link)
                break

    total_redes = sum(len(v) for v in encontrados_por_categoria.values())
    if total_redes == 0 and not emails and not telefones:
        print(f"\n{Fore.GREEN}[+] Nada encontrado (redes, e-mails ou telefones).{Fore.RESET}")
        return

    if encontrados_por_categoria:
        secao("Redes/plataformas encontradas", total_redes)
        for categoria, links in sorted(encontrados_por_categoria.items(), key=lambda item: -len(item[1])):
            print(f"\n{Fore.YELLOW}[{categoria}]{Fore.RESET} — {len(links)} link(s)")
            imprimir_limitado(sorted(links), lambda link: f"  → {link}", mostrar_tudo=mostrar_tudo)

    if emails:
        secao("E-mails encontrados", len(emails))
        imprimir_limitado(sorted(emails), lambda e: f"  → {e}", mostrar_tudo=mostrar_tudo)

    if telefones:
        secao("Telefones encontrados", len(telefones))
        imprimir_limitado(sorted(telefones), lambda t: f"  → {t}", mostrar_tudo=mostrar_tudo)


def subdomain(conn, dominio, mostrar_tudo=False):
    encontrados = {}

    query_html = """
        SELECT href AS url FROM links
        UNION ALL
        SELECT href AS url FROM css
        UNION ALL
        SELECT src AS url FROM scripts_externos
    """
    for (href,) in conn.execute(query_html).fetchall():
        parsed = urlparse(href)
        if parsed.netloc and re.search(rf"\.{re.escape(dominio)}$", parsed.netloc, re.IGNORECASE):
            base = f"{parsed.scheme}://{parsed.netloc}"
            encontrados.setdefault(base, set()).add("link/tag HTML")

    for origem, codigo in codigo_por_pagina(conn):
        for valor in extrair_strings(codigo):
            v = limpar_interpolacao(valor) if "${" in valor else valor
            if v.startswith("//"):
                v = "https:" + v
            elif not v.startswith(ESQUEMAS_URL):
                continue
            parsed = urlparse(v)
            if parsed.netloc and re.search(rf"\.{re.escape(dominio)}$", parsed.netloc, re.IGNORECASE):
                base = f"{parsed.scheme}://{parsed.netloc}"
                encontrados.setdefault(base, set()).add(origem)

    if not encontrados:
        print(f"\n{Fore.GREEN}[+] Nenhum subdomínio encontrado.{Fore.RESET}")
        return

    secao("Subdomínios encontrados", len(encontrados))

    def formatar(item):
        base, origens = item
        onde = next(iter(origens)) if len(origens) == 1 else f"{len(origens)} fonte(s)"
        return f"  → {base}\n    {Fore.CYAN}(via {onde}){Fore.RESET}"

    imprimir_limitado(sorted(encontrados.items()), formatar, mostrar_tudo=mostrar_tudo)


def gets(conn, alvo, mostrar_tudo=False):
    candidatos = [
        href for (href,) in conn.execute("SELECT DISTINCT href FROM links WHERE href LIKE '%?%'").fetchall()
        if href.startswith(alvo)
    ]

    if not candidatos:
        print(f"\n{Fore.GREEN}[+] Nenhum endpoint com parâmetro GET encontrado.{Fore.RESET}")
        return

    secao("Endpoints com parâmetro GET", len(candidatos))
    imprimir_limitado(sorted(candidatos), lambda h: f"  → {colorir(h)}", mostrar_tudo=mostrar_tudo)

    contagem_parametros = {}
    for href in candidatos:
        for nome in parse_qs(urlparse(href).query).keys():
            contagem_parametros[nome] = contagem_parametros.get(nome, 0) + 1

    if contagem_parametros:
        print(f"\n{Fore.CYAN}── Parâmetros GET mais comuns ──{Fore.RESET}")
        for nome, qtd in sorted(contagem_parametros.items(), key=lambda item: -item[1])[:15]:
            print(f"  {qtd:>3}  {colorir(nome)}")


def posts(conn, mostrar_tudo=False):
    linhas = conn.execute(
        """
        SELECT url_origem, GROUP_CONCAT(nome, ',')
        FROM post_params
        GROUP BY url_origem
        """
    ).fetchall()

    if not linhas:
        print(f"\n{Fore.GREEN}[+] Nenhum formulário com campos POST encontrado.{Fore.RESET}")
        return

    secao("Formulários encontrados", len(linhas))

    def formatar(item):
        url, nomes_str = item
        nomes = sorted({n.strip() for n in nomes_str.split(",") if n.strip()})
        nomes_coloridos = ", ".join(colorir(n) for n in nomes)
        return f"  → {url}\n    campos: [{nomes_coloridos}]"

    imprimir_limitado(linhas, formatar, mostrar_tudo=mostrar_tudo)

    contagem_nomes = {}
    for _, nomes_str in linhas:
        for nome in {n.strip() for n in nomes_str.split(",") if n.strip()}:
            contagem_nomes[nome] = contagem_nomes.get(nome, 0) + 1

    if contagem_nomes:
        print(f"\n{Fore.CYAN}── Campos mais comuns entre os formulários ──{Fore.RESET}")
        for nome, qtd in sorted(contagem_nomes.items(), key=lambda item: -item[1])[:15]:
            print(f"  {qtd:>3}  {colorir(nome)}")


def help():
    print("Comandos válidos:\n")
    print("gets - Mostra todos os endpoints com parametros GET")
    print("posts - Mostra todos os endpoints com parametros POST")
    print("subdomains - Mostra todos os subdominios descobertos (HTML e código JS)")
    print("social - Mostra todas as redes sociais, e-mails e telefones encontrados")
    print("ext <extensão> - Mostra urls com a determinada extensão\n  .jpg, .js, .json, etc")
    print(
        "js <comando> - Função de analise de código JavaScript\n"
        "  - search (shell própria: stats, endpoints, tokens, grep)\n"
        "  - reverse (requests, variaveis, value, entradas, sinks, fluxo)"
    )
    print("\nAdicione 'tudo' no final de qualquer comando acima para ver todas as")
    print("ocorrências sem limite (ex: 'gets tudo', 'ext .js tudo').")
    print()


def codigo_por_pagina(conn):
    resultado = []

    for url, codigo in conn.execute("SELECT url, js_codigo FROM paginas WHERE tipo = 'js'").fetchall():
        resultado.append((url, codigo or ""))

    query_inline = """
        SELECT p.url, GROUP_CONCAT(si.codigo, char(10))
        FROM paginas p
        JOIN scripts_inline si ON si.url_origem = p.url
        WHERE p.tipo = 'html'
        GROUP BY p.url
    """
    for url, codigo in conn.execute(query_inline).fetchall():
        resultado.append((url, codigo or ""))

    return resultado


def no_escopo(url_str: str, dominio: str) -> bool:
    host = urlparse(url_str).netloc.lower()
    dominio = dominio.lower()
    return host == dominio or host.endswith("." + dominio)


def extrair_strings(codigo: str) -> set:
    valores = set()
    for padrao in STRING_LITERAL_PATTERNS:
        for bruta in re.findall(padrao, codigo, re.DOTALL):
            valores.add(bruta[1:-1])  # remove as aspas externas
    return valores


ESQUEMAS_URL = ("http://", "https://", "ws://", "wss://", "ftp://")


def limpar_interpolacao(valor: str) -> str:
    return re.sub(r"\$\{[^}]*\}", "", valor)


def classificar_endpoints(valores):
    urls, paths = set(), set()
    for bruto in valores:
        if not isinstance(bruto, str) or not bruto:
            continue

        v = limpar_interpolacao(bruto) if "${" in bruto else bruto
        if not v:
            continue

        if v.startswith(ESQUEMAS_URL):
            # em vez de um comprimento mínimo arbitrário, valida que existe
            # um host de verdade depois do esquema
            if urlparse(v).netloc:
                urls.add(v)
        elif v.startswith("//") and len(v) > 4:
            urls.add("https:" + v)
        elif (
            (v.startswith("/") or v.startswith("./") or v.startswith("../") or v.startswith("?"))
            and len(v) > 3
            and not any(c in v for c in (":", ";", "{", "}", "!", " ", ")", "(", '"', "\\"))
        ):
            paths.add(v)
    return urls, paths


PADROES_COR = {
    "sensivel": ["api", "admin", "account", "login", "supabase.co", "firebase", "firestore", "amazonaws.com"],
    "parametro": ["?", "googleapis.com"],
    "interessante": ["auth", "token", "key", "secret", "private", "webhook", "callback", "session", "config"],
}


def colorir(valor: str) -> str:
    valor_lower = valor.lower()
    if any(p in valor_lower for p in PADROES_COR["sensivel"]):
        return Fore.YELLOW + valor + Fore.RESET
    if any(p in valor_lower for p in PADROES_COR["parametro"]):
        return Fore.BLUE + valor + Fore.RESET
    if any(p in valor_lower for p in PADROES_COR["interessante"]):
        return Fore.YELLOW + valor + Fore.RESET
    return valor


def legenda():
    print(
        f"\n{Fore.WHITE}Branco{Fore.RESET} = informação geral   "
        f"{Fore.BLUE}Azul{Fore.RESET} = informação baixa   "
        f"{Fore.YELLOW}Amarelo{Fore.RESET} = superfície de ataque   "
        f"{Fore.RED}Vermelho{Fore.RESET} = informação grave\n"
    )


def secao(titulo: str, quantidade: int, cor=Fore.CYAN):
    print(f"\n{cor}══ {titulo} ({quantidade}) ══{Fore.RESET}")


def imprimir_limitado(itens, formatter, limite=30, mostrar_tudo=False):
    itens = list(itens)
    limite_efetivo = None if mostrar_tudo else limite

    for item in itens[:limite_efetivo]:
        print(formatter(item))

    if limite_efetivo is not None:
        restante = len(itens) - limite_efetivo
        if restante > 0:
            print(f"  {Fore.CYAN}… e mais {restante} ocorrência(s) — digite o comando + 'tudo' para ver todas{Fore.RESET}")


def extrair_modificador_tudo(partes):
    if partes and partes[-1].lower() in MODIFICADORES_TUDO:
        return partes[:-1], True
    return partes, False

def stats_search(paginas_com_codigo, todos_valores, urls, paths, tokens_encontrados):
    tokens_por_tipo = {}
    for nome, valor, origem in tokens_encontrados:
        tokens_por_tipo.setdefault(nome, set()).add(valor)
    total_tokens = sum(len(v) for v in tokens_por_tipo.values())

    secao("Resumo geral", len(paginas_com_codigo), cor=Fore.MAGENTA)
    print(f"  Páginas/arquivos analisados : {len(paginas_com_codigo)}")
    print(f"  Strings únicas extraídas    : {len(todos_valores)}")
    print(f"  URLs classificadas          : {len(urls)}")
    print(f"  Caminhos relativos          : {len(paths)}")
    print(f"  Tipos de token encontrados  : {len(tokens_por_tipo)}")
    print(f"  Valores de token (únicos)   : {total_tokens}")

    if tokens_por_tipo:
        print(f"\n{Fore.YELLOW}Por tipo de token:{Fore.RESET}")
        for nome, valores in sorted(tokens_por_tipo.items(), key=lambda item: -len(item[1])):
            print(f"  {len(valores):>3}  {nome}")


def grep_strings(todos_valores, tokens_encontrados, termo, mostrar_tudo=False):
    termo_lower = termo.lower()

    achados_strings = sorted(v for v in todos_valores if termo_lower in v.lower())
    achados_tokens = [
        (nome, valor, origem)
        for nome, valor, origem in tokens_encontrados
        if termo_lower in valor.lower() or termo_lower in nome.lower()
    ]

    if not achados_strings and not achados_tokens:
        print(f"\n{Fore.GREEN}[+] Nada encontrado contendo '{termo}'.{Fore.RESET}")
        return

    if achados_strings:
        secao(f"Strings contendo '{termo}'", len(achados_strings))
        imprimir_limitado(achados_strings, lambda v: f"  → {colorir(v)}", mostrar_tudo=mostrar_tudo)

    if achados_tokens:
        secao(f"Tokens contendo '{termo}'", len(achados_tokens), cor=Fore.RED)
        imprimir_limitado(
            achados_tokens,
            lambda item: f"  → [{item[0]}] {item[1]}\n    {Fore.CYAN}(em {item[2]}){Fore.RESET}",
            mostrar_tudo=mostrar_tudo,
        )


def js_search(paginas_com_codigo, dominio):
    todos_valores = set()
    tokens_encontrados = []

    for origem, codigo in tqdm(paginas_com_codigo, desc="Analisando código JS"):
        todos_valores |= extrair_strings(codigo)
        for nome_padrao, regex in SECRET_PATTERNS.items():
            for match in set(re.findall(regex, codigo)):
                tokens_encontrados.append((nome_padrao, match, origem))

    urls, paths = classificar_endpoints(todos_valores)

    legenda()
    print(
        f"[+] {len(paginas_com_codigo)} página(s)/arquivo(s) analisados — "
        f"{len(todos_valores)} string(s) única(s) extraída(s)\n"
    )
    print("Digite 'help' para ver os comandos, 'exit' para sair.\n")

    while True:
        comando_bruto = input(r"Search\$> ").strip()
        partes = comando_bruto.split()
        partes, mostrar_tudo = extrair_modificador_tudo(partes)
        comando = partes[0].lower() if partes else ""

        if comando == "exit":
            break
        if comando == "help":
            print(
                "\nComandos:\n"
                "  stats           → resumo geral (contagens por categoria)\n"
                "  endpoints       → URLs e caminhos encontrados, por escopo\n"
                "  tokens          → tokens/segredos encontrados, agrupados por tipo\n"
                "  grep <termo>    → procura <termo> nas strings brutas e nos tokens\n"
                "\n"
                "  Adicione 'tudo' no final de qualquer comando para ver todas as\n"
                "  ocorrências sem limite (ex: 'endpoints tudo', 'grep token tudo').\n"
            )
            continue
        if comando == "stats":
            stats_search(paginas_com_codigo, todos_valores, urls, paths, tokens_encontrados)
        elif comando == "endpoints":
            mostrar_endpoints(urls, paths, dominio, mostrar_tudo)
        elif comando == "tokens":
            mostrar_tokens(tokens_encontrados, mostrar_tudo)
        elif comando == "grep":
            termo = " ".join(partes[1:]).strip()
            if not termo:
                print("Uso: grep <termo> [tudo]")
            else:
                grep_strings(todos_valores, tokens_encontrados, termo, mostrar_tudo)
        else:
            print("Comando inválido. Digite 'help' para ver as opções.")


def mostrar_endpoints(urls, paths, dominio, mostrar_tudo=False):
    legenda()

    escopo = sorted(u for u in urls if no_escopo(u, dominio))
    fora_escopo = sorted(u for u in urls if not no_escopo(u, dominio))
    paths_ordenados = sorted(paths)

    secao("Caminhos relativos", len(paths_ordenados))
    imprimir_limitado(paths_ordenados, lambda p: f"  → {colorir(p)}", mostrar_tudo=mostrar_tudo)

    secao("URLs no escopo", len(escopo))
    imprimir_limitado(escopo, lambda u: f"  → {colorir(u)}", mostrar_tudo=mostrar_tudo)

    secao("URLs fora do escopo", len(fora_escopo))
    imprimir_limitado(fora_escopo, lambda u: f"  → {colorir(u)}", mostrar_tudo=mostrar_tudo)


def mostrar_tokens(tokens_encontrados, mostrar_tudo=False):
    if not tokens_encontrados:
        print(f"\n{Fore.GREEN}[+] Nenhum token ou segredo encontrado.{Fore.RESET}")
        return

    agrupado = {}
    for nome, valor, origem in tokens_encontrados:
        agrupado.setdefault(nome, {}).setdefault(valor, set()).add(origem)

    total = sum(len(valores) for valores in agrupado.values())
    secao("Tokens/segredos encontrados", total, cor=Fore.RED)

    for nome, valores in sorted(agrupado.items()):
        print(f"\n{Fore.YELLOW}[{nome}]{Fore.RESET} — {len(valores)} valor(es) único(s)")

        def formatar(par):
            valor, origens = par
            onde = next(iter(origens)) if len(origens) == 1 else f"{len(origens)} arquivos"
            return f"  → {valor}\n    {Fore.CYAN}(em {onde}){Fore.RESET}"

        imprimir_limitado(list(valores.items()), formatar, mostrar_tudo=mostrar_tudo)

def reverse_requests(paginas_com_codigo, mostrar_tudo=False):
    achados_por_tipo = {}
    for origem, codigo in paginas_com_codigo:
        for nome_tipo, regex in codigo_regexs.padroes_requisicao.items():
            for match in set(re.findall(regex, codigo, re.DOTALL)):
                achados_por_tipo.setdefault(nome_tipo, []).append((match, origem))

    total = sum(len(v) for v in achados_por_tipo.values())
    if total == 0:
        print(f"\n{Fore.GREEN}[+] Nenhuma chamada de rede encontrada.{Fore.RESET}")
        return

    secao("Chamadas de rede encontradas", total)
    for tipo, achados in achados_por_tipo.items():
        print(f"\n{Fore.YELLOW}[{tipo}]{Fore.RESET} — {len(achados)} ocorrência(s)")

        def formatar(item):
            trecho, origem = item
            trecho_limpo = " ".join(trecho.split())
            if len(trecho_limpo) > 160:
                trecho_limpo = trecho_limpo[:160] + "..."
            return f"  {Fore.GREEN}→{Fore.RESET} {trecho_limpo}\n    {Fore.CYAN}(em {origem}){Fore.RESET}"

        imprimir_limitado(achados, formatar, limite=15, mostrar_tudo=mostrar_tudo)


def reverse_variaveis(paginas_com_codigo, mostrar_tudo=False):
    vetores, baixos = [], []
    for origem, codigo in paginas_com_codigo:
        for match in re.findall(codigo_regexs.variaveis, codigo):
            match_limpo = " ".join(match.split())
            if re.search(codigo_regexs.palavras_chaves_vetores, match_limpo, re.IGNORECASE):
                vetores.append((match_limpo, origem))
            elif re.search(codigo_regexs.palavras_chaves_baixo, match_limpo, re.IGNORECASE) and not re.search(r"</.*?>", match_limpo):
                baixos.append((match_limpo, origem))

    if not vetores and not baixos:
        print(f"\n{Fore.GREEN}[+] Nenhuma variável sensível encontrada.{Fore.RESET}")
        return

    def formatar(item):
        valor, origem = item
        return f"  → {valor}\n    {Fore.CYAN}(em {origem}){Fore.RESET}"

    secao("Superfície de ataque", len(vetores), cor=Fore.YELLOW)
    imprimir_limitado(vetores, formatar, mostrar_tudo=mostrar_tudo)

    secao("Informação baixa", len(baixos), cor=Fore.BLUE)
    imprimir_limitado(baixos, formatar, mostrar_tudo=mostrar_tudo)


def reverse_value(paginas_com_codigo, nome, mostrar_tudo=False):
    encontrados = []
    for origem, codigo in paginas_com_codigo:
        match = re.search(rf"\b{re.escape(nome)}\s*=\s*.*", codigo, re.IGNORECASE)
        if match:
            encontrados.append((" ".join(match.group(0).split()), origem))

    if not encontrados:
        print(f"\n{Fore.GREEN}[+] Variável '{nome}' não encontrada.{Fore.RESET}")
        return

    secao(f"Ocorrências de '{nome}'", len(encontrados))
    imprimir_limitado(
        encontrados,
        lambda item: f"  → {item[0]}\n    {Fore.CYAN}(em {item[1]}){Fore.RESET}",
        mostrar_tudo=mostrar_tudo,
    )


def reverse_entradas(paginas_com_codigo, mostrar_tudo=False):
    achados_por_categoria = {}

    for origem, codigo in tqdm(paginas_com_codigo, desc="Procurando fontes de entrada"):
        for categoria, regexes in ENTRADAS_USUARIO.items():
            vistos_na_pagina = set()
            for regex in regexes:
                for match in re.findall(regex, codigo, re.DOTALL):
                    if match in vistos_na_pagina:
                        continue
                    vistos_na_pagina.add(match)
                    achados_por_categoria.setdefault(categoria, []).append((match, origem))

    total = sum(len(v) for v in achados_por_categoria.values())
    if total == 0:
        print(f"\n{Fore.GREEN}[+] Nenhuma fonte de entrada de usuário encontrada.{Fore.RESET}")
        return

    secao("Fontes de entrada de usuário", total, cor=Fore.MAGENTA)
    print(
        f"{Fore.CYAN}(pontos onde o JS lê dado potencialmente controlado pelo usuário — "
        f"úteis para procurar DOM XSS, open redirect, prototype pollution, etc){Fore.RESET}"
    )

    for categoria, achados in sorted(achados_por_categoria.items(), key=lambda item: -len(item[1])):
        print(f"\n{Fore.YELLOW}[{categoria}]{Fore.RESET} — {len(achados)} ocorrência(s)")

        def formatar(item):
            trecho, origem = item
            trecho_limpo = " ".join(trecho.split())
            if len(trecho_limpo) > 140:
                trecho_limpo = trecho_limpo[:140] + "..."
            return f"  {Fore.GREEN}→{Fore.RESET} {trecho_limpo}\n    {Fore.CYAN}(em {origem}){Fore.RESET}"

        imprimir_limitado(achados, formatar, limite=15, mostrar_tudo=mostrar_tudo)
    contagem_por_pagina = {}
    for achados in achados_por_categoria.values():
        for _, origem in achados:
            contagem_por_pagina[origem] = contagem_por_pagina.get(origem, 0) + 1

    top_paginas = sorted(contagem_por_pagina.items(), key=lambda item: -item[1])[:5]
    print(f"\n{Fore.CYAN}── Páginas com mais fontes de entrada (top {len(top_paginas)}) ──{Fore.RESET}")
    for origem, qtd in top_paginas:
        print(f"  {qtd:>3}  {origem}")


def reverse_sinks(paginas_com_codigo, mostrar_tudo=False):
    achados_por_categoria = {}

    for origem, codigo in tqdm(paginas_com_codigo, desc="Procurando sinks perigosos"):
        for categoria, regexes in SINKS_PERIGOSOS.items():
            vistos_na_pagina = set()
            for regex in regexes:
                for match in re.findall(regex, codigo, re.DOTALL):
                    if match in vistos_na_pagina:
                        continue
                    vistos_na_pagina.add(match)
                    achados_por_categoria.setdefault(categoria, []).append((match, origem))

    total = sum(len(v) for v in achados_por_categoria.values())
    if total == 0:
        print(f"\n{Fore.GREEN}[+] Nenhum sink perigoso encontrado.{Fore.RESET}")
        return

    secao("Sinks (destinos perigosos) encontrados", total, cor=Fore.RED)
    print(
        f"{Fore.CYAN}(pontos onde dado chega e é usado de forma perigosa — HTML, execução de "
        f"código, redirecionamento, etc. Não confirma exploração, só indica onde revisar se o "
        f"dado que chega ali é controlado pelo usuário){Fore.RESET}"
    )

    for categoria, achados in sorted(achados_por_categoria.items(), key=lambda item: -len(item[1])):
        print(f"\n{Fore.YELLOW}[{categoria}]{Fore.RESET} — {len(achados)} ocorrência(s)")

        def formatar(item):
            trecho, origem = item
            trecho_limpo = " ".join(trecho.split())
            if len(trecho_limpo) > 140:
                trecho_limpo = trecho_limpo[:140] + "..."
            return f"  {Fore.RED}→{Fore.RESET} {trecho_limpo}\n    {Fore.CYAN}(em {origem}){Fore.RESET}"

        imprimir_limitado(achados, formatar, limite=15, mostrar_tudo=mostrar_tudo)

    contagem_por_pagina = {}
    for achados in achados_por_categoria.values():
        for _, origem in achados:
            contagem_por_pagina[origem] = contagem_por_pagina.get(origem, 0) + 1

    top_paginas = sorted(contagem_por_pagina.items(), key=lambda item: -item[1])[:5]
    print(f"\n{Fore.CYAN}── Páginas com mais sinks (top {len(top_paginas)}) ──{Fore.RESET}")
    for origem, qtd in top_paginas:
        print(f"  {qtd:>3}  {origem}")


REGEX_ATRIBUICAO = re.compile(r"^\s*(?:var|let|const)?\s*([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*=\s*(?!=)")


def variavel_atribuida(linha: str):
    m = REGEX_ATRIBUICAO.match(linha)
    return m.group(1) if m else None


def reverse_fluxo(paginas_com_codigo, mostrar_tudo=False):
    suspeitas = []

    for origem, codigo in tqdm(paginas_com_codigo, desc="Cruzando fontes com sinks"):
        linhas = codigo.splitlines()

        variaveis_de_fontes = {}
        for idx, linha in enumerate(linhas):
            for categoria, regexes in ENTRADAS_USUARIO.items():
                if any(re.search(r, linha) for r in regexes):
                    var = variavel_atribuida(linha)
                    if var:
                        variaveis_de_fontes[var] = (categoria, idx)
                    break

        if not variaveis_de_fontes:
            continue

        for idx, linha in enumerate(linhas):
            for categoria_sink, regexes in SINKS_PERIGOSOS.items():
                if not any(re.search(r, linha) for r in regexes):
                    continue
                for var, (categoria_fonte, linha_fonte) in variaveis_de_fontes.items():
                    if linha_fonte != idx and re.search(rf"\b{re.escape(var)}\b", linha):
                        suspeitas.append(
                            {
                                "origem": origem,
                                "variavel": var,
                                "fonte": categoria_fonte,
                                "linha_fonte": linha_fonte + 1,
                                "sink": categoria_sink,
                                "linha_sink": idx + 1,
                                "trecho_fonte": linhas[linha_fonte].strip()[:120],
                                "trecho_sink": linha.strip()[:120],
                            }
                        )

    if not suspeitas:
        print(f"\n{Fore.GREEN}[+] Nenhum fluxo suspeito encontrado (heurística por variável, mesmo arquivo).{Fore.RESET}")
        return

    secao("Possíveis fluxos fonte → sink", len(suspeitas), cor=Fore.RED)
    print(
        f"{Fore.CYAN}(heurística: mesma variável atribuída a partir de uma fonte e depois usada "
        f"num sink, no mesmo arquivo — SEMPRE revise manualmente antes de considerar isso uma "
        f"vulnerabilidade confirmada){Fore.RESET}\n"
    )

    def formatar(item):
        return (
            f"  {Fore.RED}→{Fore.RESET} variável '{item['variavel']}'\n"
            f"    {Fore.YELLOW}[{item['fonte']}]{Fore.RESET} linha {item['linha_fonte']}: {item['trecho_fonte']}\n"
            f"    {Fore.YELLOW}[{item['sink']}]{Fore.RESET} linha {item['linha_sink']}: {item['trecho_sink']}\n"
            f"    {Fore.CYAN}(em {item['origem']}){Fore.RESET}"
        )

    imprimir_limitado(suspeitas, formatar, limite=15, mostrar_tudo=mostrar_tudo)


def js_reverse(paginas_com_codigo):
    legenda()
    print("Digite 'help' para ver os comandos, 'exit' para sair.\n")

    while True:
        comando_bruto = input(r"Reverse\$> ").strip()
        partes = comando_bruto.split()
        partes, mostrar_tudo = extrair_modificador_tudo(partes)
        comando = partes[0].lower() if partes else ""

        if comando == "exit":
            break
        if comando == "help":
            print(
                "\nComandos:\n"
                "  requests        → chamadas de rede (fetch, ajax, axios, websocket, etc)\n"
                "  variaveis       → atribuições de variáveis potencialmente sensíveis\n"
                "  value <nome>    → valor(es) atribuído(s) a uma variável específica\n"
                "  entradas        → fontes de entrada do usuário (URL, storage, cookies,\n"
                "                    formulários, postMessage, headers, etc)\n"
                "  sinks           → destinos perigosos (innerHTML, eval, redirecionamento,\n"
                "                    setAttribute de href/src, cookies, prototype pollution, etc)\n"
                "  fluxo           → cruza entradas x sinks (heurística: mesma variável, mesmo\n"
                "                    arquivo) para sugerir onde revisar primeiro\n"
                "\n"
                "  Adicione 'tudo' no final de qualquer comando acima para ver todas as\n"
                "  ocorrências sem limite (ex: 'sinks tudo', 'value token tudo').\n"
            )
            continue
        if comando == "requests":
            reverse_requests(paginas_com_codigo, mostrar_tudo)
        elif comando == "variaveis":
            reverse_variaveis(paginas_com_codigo, mostrar_tudo)
        elif comando in ("entradas", "input", "sources"):
            reverse_entradas(paginas_com_codigo, mostrar_tudo)
        elif comando in ("sinks", "destinos"):
            reverse_sinks(paginas_com_codigo, mostrar_tudo)
        elif comando in ("fluxo", "fluxos", "correlacao"):
            reverse_fluxo(paginas_com_codigo, mostrar_tudo)
        elif comando == "value":
            nome = " ".join(partes[1:]).strip()
            if not nome:
                print("Uso: value <nomeVariavel> [tudo]")
            else:
                reverse_value(paginas_com_codigo, nome, mostrar_tudo)
        else:
            print("Comando inválido. Digite 'help' para ver as opções.")


def js(conn, dominio, comando, alvo):
    paginas_com_codigo = codigo_por_pagina(conn)
    if not paginas_com_codigo:
        print("Nenhum código JavaScript foi coletado para esse alvo.")
        return

    acao = comando[3:].strip()
    if acao == "search":
        js_search(paginas_com_codigo, dominio)
    elif acao == "reverse":
        js_reverse(paginas_com_codigo)
    else:
        print("Comando inválido. Use 'js search' ou 'js reverse'.")