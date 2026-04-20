from colorama import Fore
import re
from tqdm import tqdm
from urllib.parse import urlparse, urlunparse
from typing import Dict, List, Set

class codigo_regexs:
    ajax = r"\$\.ajax\(\{\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\)"
    ajaxGetPost = r"\$\.(get|post)\(\{\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\)"
    #ajax = r"\$\.ajax\(\{\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\)"
    fetch = r'fetch\s*\(.*?\)'
    axios = r"axios\.\w+\(.*?\)"
    webSocket = r"new\s*WebSocket\(.*?\)"
    xmlHttpRequest = r"\.open\(['`\"](GET|POST|PUT|DELETE|PATCH)['`\"]\,.*?\)"
    http_request = r'this\.\w+\.\w+\(.*\s.*\s.*\s.*\s.*\s.*\s.*\s.*\)'
    pattern = [ajax, fetch, http_request, ajaxGetPost, axios, webSocket, xmlHttpRequest]

    variaveis = r".*=.*"
    palavrasChavesVetores = r"\b(admin|role|Cookies.set|Cookies.get|Cookies.remove|userRole)\b"
    palavrasChavesBaixo = r"\b(userId)\b"

class sensive:
    tokens_header = r'token:.*'
    token_json = r'"token":"[^"]+"'
    token_acess = r'"access_token": "[^"]+"'
    authorization = r'Authorization:.*'
    twitter_token = r'[1-9][0-9]+-[0-9a-zA-Z]{40}'
    facebook_token = r'EAACEdEose0cBA[0-9A-Za-z]+'
    google_api = r'AIza[0-9A-Za-z-_]{35}'
    google_oauth = r'[0-9a-zA-Z-_]{24}'
    github_token = r'^ghp_[a-zA-Z0-9]{36}$'
    github_oauth = r'^gho_[a-zA-Z0-9]{36}$'
    github_server_acess_token = r'^ghu_[a-zA-Z0-9]{36}$'
    stripe_key_standart = r'sk_live_[0-9a-zA-Z]{24}'
    stripe_key_private = r'rk_live_[0-9a-zA-Z]{99}'
    openai_user_api = r'sk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}'
    paypal = r'access_token,production$[0-9a-z]{161[0-9a,]{32}'
    patterns = {
        #"token_header": r'token:.*',
        "token_json": r'"token":"[^"]+"',
        "access_token": r'"access_token": "[^"]+"',
        #"authorization": r'Authorization:.*',
        "twitter_token": r'[1-9][0-9]+-[0-9a-zA-Z]{40}',
        "facebook_token": r'EAACEdEose0cBA[0-9A-Za-z]+',
        "google_api": r'AIza[0-9A-Za-z-_]{35}',
        "google_oauth": r'([A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,})',
        "github_token": r'^ghp_[a-zA-Z0-9]{36}$',
        "github_oauth": r'^gho_[a-zA-Z0-9]{36}$',
        "github_server_access_token": r'^ghu_[a-zA-Z0-9]{36}$',
        "stripe_key_standard": r'sk_live_[0-9a-zA-Z]{24}',
        "stripe_key_private": r'rk_live_[0-9a-zA-Z]{99}',
        "openai_api_key": r'sk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}',
        "paypal_token": r'access_token,production\$[0-9a-z]{161}[0-9a-z]{32}'
    }


def arquivoTipo(chaves, dados, comando):
    for url in chaves:
        if url not in dados or not isinstance(dados[url], dict):
            continue
        links = dados[url]["links"]
        for urlLink in links:
            parsed = urlparse(urlLink)
            urlsParametros = urlunparse(parsed._replace(query=""))
            extensao = comando[4:]
            if urlsParametros.endswith(extensao):
                print(f"[+] {urlsParametros}")
def social(chaves: List[str], dados: Dict) -> None:
    REDES_PATTERNS = {
        "social": [
            "facebook.com", "pinterest.com", "youtube.com",
            "twitter.com", "x.com", "linkedin.com",
            "instagram.com", "tiktok.com", "reddit.com", "threads.net"
        ],
        "media": [
            "youtu.be", "vimeo.com", "twitch.tv"
        ],
        "mensageria": [
            "wa.me", "whatsapp.com", "t.me",
            "telegram.me", "discord.gg", "discord.com"
        ]
    }
    encontrados: Set[str] = set()
    emails: Set[str] = set()

    for url in chaves:
        if url not in dados or not isinstance(dados[url], dict):
            continue

        if url.endswith((".js", ".mjs")):
            continue

        links = dados[url].get("links", [])

        for link in links:
            link_lower = link.lower()

            if link_lower.startswith("mailto:"):
                email = link[7:]
                emails.add(email)
                continue

            for categoria, padroes in REDES_PATTERNS.items():
                if any(p in link_lower for p in padroes):
                    encontrados.add(link)
                    break

    print("\n[+] Redes encontradas:")
    for i in sorted(encontrados):
        print(f"  → {i}")

    print("\n[+] Emails encontrados:")
    for e in sorted(emails):
        print(f"  → {e}")
def help():
    print("Comandos válidos:\n")
    print("gets - Mostra todos os endpoints com parametros GET")
    print("Posts - Mostra todos os endpoints com parametros POST")
    print("subdomains - Mostra todos os subdominios descobertos")
    print("social - Mostra todas as redes sociais encontradas")
    print("ext <extensão> - Mostra urls com a determinada extensão\n  .jpg, .js, .json, etc")
    print("js <comando> - Função de analise de código JavaScript\n  - search\n  - reverse")
    print()
def subdomain(chaves, dados, dominio):
    encontrados = set()

    for url in chaves:
        if not (url.endswith(".js") or url.endswith(".mjs")):
            continue
        if url not in dados or not isinstance(dados[url], dict):
            continue

        links = dados[url]["links"]

        for subdominio in links:
            parsed = urlparse(subdominio)
            base = f"{parsed.scheme}://{parsed.netloc}"

            if re.search(fr"\.{dominio}$", parsed.netloc):
                encontrados.add(base)

    for item in encontrados:
        print(f"  → {item}")
def gets(chaves, dados, alvo):
    validos = set()
    for url in chaves:
        if url not in dados or not isinstance(dados[url], dict):
            continue
        if not (url.endswith(".js") or url.endswith(".mjs")):
            links = dados[url]["links"]
            for parametros in links:
                if parametros and "?" in parametros and parametros.startswith(alvo):
                    validos.add(parametros)
    for i in validos:
        print(f"  → {i}")
def posts(chaves, dados):
    for url in chaves:
        if url not in dados or not isinstance(dados[url], dict):
            continue
        if not (url.endswith(".js") or url.endswith(".mjs")):
            parametros = dados[url]["post"]
            if parametros:
                print(url)
                print(f"  → {parametros}\n")

def js(chaves, dados, dominio, comando, alvo):
    instrucoes = {
        "branco": "Branco: Informação",
        "azul": Fore.BLUE + "Azul: Informação baixa" + Fore.RESET,
        "amarelo": Fore.YELLOW + "Amarelo: Superficie de ataque" + Fore.RESET,
        "vermelho": Fore.RED + "Vermelho: informação grave!!" + Fore.RESET
    }
    def codigo_js() -> str:
        codigo_final = ""
        for url in tqdm(chaves, desc="Especionando código"):
            if url.endswith(".js") or url.endswith(".mjs"):
                codigo_final += dados[url] + "\n"
            else:
                codigo_final += "".join(i + "\n" for i in dados[url]["scripts_inline"])
        return codigo_final

    def endpoints(valores):
        urls = []
        paths = []
        for i in valores:
            if (i.startswith("https://") or i.startswith("http://")) and len(i) > 10:
                urls.append(i)
            elif (i.startswith("/") or i.startswith("//") or i.startswith("./") or i.startswith("\\") or i.startswith("../") or i.startswith("/..")) and len(i) > 3 and not i.startswith(r"\u"):
                if ":" in i or ";" in i or "{" in i or "}" in i or "!" in i or " " in i or ")" in i or "(" in i or '"' in i:
                    pass
                else:
                    paths.append(i)
            else:
                pass
        return list(set(urls)), list(set(paths))
    def tokens(valores):
        for dados in tqdm(valores, desc="Analisando em busca de tokens"):
            for nome, regex in sensive.patterns.items():
                matches = re.findall(regex, dados)
                if matches:
                    for m in matches:
                        print(f"[+] {nome}: {m}")
    def reverse(origem, codigo, comando):
        def classificacao(valor):
            if re.search(codigo_regexs.palavrasChavesVetores, valor, re.IGNORECASE):
                return Fore.YELLOW + valor + Fore.RESET
            elif re.search(codigo_regexs.palavrasChavesBaixo, valor, re.IGNORECASE) and not re.search(r"</.*?>", valor):
                return Fore.BLUE + valor + Fore.RESET
            else:
                return False

        if comando == "requests":
            for regexs in codigo_regexs.pattern:
                procurar = re.findall(regexs, codigo)
                if procurar:
                    for i in procurar:
                        print(Fore.GREEN + f"\n[+] Achado['{origem}']:" + Fore.RESET + f"\n\n{i}")
        elif comando == "variaveis":
            variaveis = re.findall(codigo_regexs.variaveis, codigo)
            if variaveis:
                for i in variaveis:
                    verificacao = classificacao(i)
                    if verificacao:
                        print(f"\n[+] Achado['{origem}']:\n\n{verificacao}")
        elif comando.startswith("value"):
            nome = comando[6:]
            procura = re.search(fr"{nome}\s*=\s.*", codigo, re.IGNORECASE)
            if procura:
                print(f"\n[+] Achado['{origem}']:\n\n{procura.group(0)}")
        else:
            pass

    def mostrarDados(info, tipo):
        PADROES = {
            "sensivel": [
                "api", "admin", "account", "login",
                "supabase.co", "firebase", "firestore", "amazonaws.com"
            ],
            "parametro": [
                "?", "googleapis.com"
            ],
            "interessante": [
                "auth", "token", "key", "secret", "private",
                "webhook", "callback", "session", "config"
            ]
        }

        def tipos(valor: str) -> str:
            valor_lower = valor.lower()

            if any(p in valor_lower for p in PADROES["sensivel"]):
                return Fore.YELLOW + valor + Fore.RESET

            if any(p in valor_lower for p in PADROES["parametro"]):
                return Fore.BLUE + valor + Fore.RESET

            if any(p in valor_lower for p in PADROES["interessante"]):
                return Fore.YELLOW + valor + Fore.RESET

            return valor

        fora_escopo = []
        escopo = []

        print(instrucoes["branco"] + "\n" + instrucoes["azul"] + "\n" + instrucoes["amarelo"] + "\n" + instrucoes[
            "vermelho"] + "\n")
        if tipo == 1:  # tipo 1 = Urls
            for i in info:
                if dominio in i:
                    tipo = tipos(i)
                    escopo.append(tipo)
                else:
                    tipo = tipos(i)
                    fora_escopo.append(tipo)
            print("No escopo:\n")
            for i in escopo:
                print(f"[+] {i}")
            print("\nFora do escopo:\n")
            for i in fora_escopo:
                print(f"[+] {i}")
        else:
            for i in info:
                tipo = tipos(i)
                print(f"[+] {tipo}")

    codigo_strings = codigo_js()
    acao = comando[3:]
    if acao == "search":
        regex = r'"(.*?)"'
        regex2 = r"'(.*?)'"
        regex3 = r"`(.*?)`"
        valoresAspasDuplas = re.findall(regex, codigo_strings)
        valoresAspasSimples = re.findall(regex2, codigo_strings)
        valoresApostrofos = re.findall(regex3, codigo_strings)
        print("1. Endpoints 2. Tokens\n99. Sair")
        while True:
            procura = int(input("O que você deseja procurar?: "))
            match (procura):
                case 1:
                    urls, paths = endpoints(valoresAspasDuplas)
                    urls2, paths2 = endpoints(valoresAspasSimples)
                    urls3, paths3 = endpoints(valoresApostrofos)
                    print("Caminhos encontrados:\n")
                    mostrarDados(paths, 2)
                    mostrarDados(paths2, 2)
                    mostrarDados(paths3, 2)
                    print("\nurls encontradas:\n")
                    mostrarDados(urls, 1)
                    mostrarDados(urls2, 1)
                    mostrarDados(urls3, 1)
                case 2:
                    tokens(valoresAspasSimples)
                    tokens(valoresAspasDuplas)
                case 99:
                    print("Saindo...")
                    break
                case _:
                    print("Opção inválida")
    elif acao == "reverse":
        print(instrucoes["branco"] + "\n" + instrucoes["azul"] + "\n" + instrucoes["amarelo"] + "\n" + instrucoes[
            "vermelho"] + "\n")
        print("\nDigite 'help' para obter ajuda")
        while True:
            comando = input(r"Reverse\$> ").lower()
            if comando == "exit":
                break
            if comando == "help":
                print("\nComandos:\n - requests > Mostra requisições fetch, ajax, axios, etc\n - variaveis > Mostra variaveis com valores uteis\n - value <nomeVariavel> > Descubra o valor de uma variavel")
            for url in chaves:
                if url not in dados or not isinstance(dados[url], dict):
                    continue
                if not (url.endswith(".js") or url.endswith(".mjs")):
                    codigoEm_Html = dados[url]["scripts_inline"]
                    codigoFinal = ""
                    for i in codigoEm_Html:
                        codigoFinal += i + "\n"
                    reverse(url, codigoFinal, comando)
                else:
                    codigoPuro = dados[url]
                    reverse(url, codigoPuro, comando)
    else:
        print("Comando inválido...")